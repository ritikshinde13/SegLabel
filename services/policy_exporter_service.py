from typing import Dict, Any, List
from database.db import get_db_connection

class PolicyExporterService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_policies_and_destinations(self):
        conn = get_db_connection(self.db_path)
        try:
            policies = [dict(r) for r in conn.execute("SELECT * FROM policies ORDER BY source_identity, destination").fetchall()]
            destinations = [dict(r) for r in conn.execute("SELECT * FROM destinations ORDER BY name").fetchall()]
            return policies, destinations
        finally:
            conn.close()

    def export_cilium_manifest(self) -> str:
        """Generates a production-ready CiliumNetworkPolicy (CNP) YAML definition."""
        policies, destinations = self._get_policies_and_destinations()
        
        # Group allows by source identity
        allows_by_source: Dict[str, List[str]] = {}
        for p in policies:
            if p["action"] == "ALLOW":
                allows_by_source.setdefault(p["source_identity"], []).append(p["destination"])

        manifest_sections = []
        for src, dests in allows_by_source.items():
            to_endpoints_yaml = []
            for d in dests:
                to_endpoints_yaml.append(f"""    - toEndpoints:
      - matchLabels:
          k8s:io.kubernetes.pod.namespace: production
          app.kubernetes.io/name: {d}
          security.seglabel.io/identity-state: confirmed""")

            to_endpoints_str = "\n".join(to_endpoints_yaml)

            section = f"""apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: seglabel-{src}-microsegmentation
  namespace: production
  labels:
    security.seglabel.io/managed-by: seglabel-engine
    security.seglabel.io/zero-trust: "true"
spec:
  description: "Enforces Zero Trust for {src}. Egress allowed only to confirmed destinations."
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: {src}
      security.seglabel.io/identity-state: confirmed
  egress:
{to_endpoints_str}
  # Global fail-closed: drops all traffic from unconfirmed/ambiguous pods
  ingress:
    - fromEndpoints:
      - matchLabels:
          security.seglabel.io/identity-state: confirmed
---"""
            manifest_sections.append(section)

        if not manifest_sections:
            return "# No active ALLOW policies found in SegLabel policy matrix.\n"

        return "\n".join(manifest_sections)

    def export_k8s_network_policy(self) -> str:
        """Generates standard Kubernetes NetworkPolicy YAML with strict Default Deny."""
        policies, _ = self._get_policies_and_destinations()
        
        allows_by_source: Dict[str, List[str]] = {}
        for p in policies:
            if p["action"] == "ALLOW":
                allows_by_source.setdefault(p["source_identity"], []).append(p["destination"])

        manifests = [
"""# ==========================================================
# SegLabel K8s Baseline: Default Deny Ingress & Egress
# ==========================================================
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: seglabel-default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---"""
        ]

        for src, dests in allows_by_source.items():
            egress_rules = []
            for d in dests:
                egress_rules.append(f"""    - to:
      - podSelector:
          matchLabels:
            app: {d}
            identity-status: confirmed""")
            
            rules_str = "\n".join(egress_rules)
            manifest = f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: seglabel-allow-{src}
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: {src}
      identity-status: confirmed
  policyTypes:
  - Egress
  egress:
{rules_str}
---"""
            manifests.append(manifest)

        return "\n".join(manifests)

    def export_ebpf_sock_ops_snippet(self) -> str:
        """Generates an eBPF C program snippet illustrating socket-level ambiguity drops."""
        return """/*
 * SegLabel eBPF Socket Filter (Kernel BPF_PROG_TYPE_SOCK_OPS)
 * Enforces Zero Trust Ambiguity Window packet drops directly in Linux TCP/IP stack.
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

#define STATUS_STARTING    1
#define STATUS_AMBIGUOUS   2
#define STATUS_CONFIRMED   3
#define STATUS_QUARANTINED 4
#define STATUS_REVOKED     5

/* Map storing active workload identity status keyed by socket cookie / container cgroup */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u64);    /* cgroup_id */
    __type(value, __u32);  /* identity_status */
    __uint(max_entries, 65536);
} workload_identity_map SEC(".maps");

SEC("sockops")
int seglabel_sock_ops_enforce(struct bpf_sock_ops *skops) {
    __u32 op = skops->op;

    /* Intercept outbound active TCP connect & established events */
    if (op == BPF_SOCK_OPS_ACTIVE_ESTABLISHED_CB || op == BPF_SOCK_OPS_TCP_CONNECT_CB) {
        __u64 cgroup_id = bpf_get_current_cgroup_id();
        __u32 *status = bpf_map_lookup_elem(&workload_identity_map, &cgroup_id);

        if (!status) {
            /* Unknown identity -> Fail-closed drop */
            bpf_printk("[SEGLABEL-eBPF] DROP: Workload cgroup %llu has unknown identity\\n", cgroup_id);
            return -1;
        }

        /* Enforce Ambiguity Window Drop */
        if (*status == STATUS_STARTING || *status == STATUS_AMBIGUOUS) {
            bpf_printk("[SEGLABEL-eBPF] ZERO TRUST DROP: Ambiguity window active (status=%u) for cgroup %llu\\n",
                       *status, cgroup_id);
            return -1; /* Reset / drop connection */
        }

        if (*status == STATUS_QUARANTINED || *status == STATUS_REVOKED) {
            bpf_printk("[SEGLABEL-eBPF] CONTAINMENT DROP: Workload is quarantined or revoked (status=%u)\\n",
                       *status);
            return -1;
        }

        /* CONFIRMED status -> packet permitted through kernel */
    }

    return 0;
}

char _license[] SEC("license") = "GPL";
"""
