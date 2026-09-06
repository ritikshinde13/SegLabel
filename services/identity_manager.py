from datetime import datetime, timezone
import sqlite3
from typing import Optional, List, Dict, Any
from database.db import get_db_connection
from models.workload import Workload, IdentityEvent, IdentityStatus

class IdentityManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def check_identity_reuse(self, signal: str, exclude_workload_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Checks if an identity signal has previously belonged to another workload."""
        conn = get_db_connection(self.db_path)
        try:
            query = """
                SELECT id, name, status, confirmed_identity, initial_identity_signal
                FROM workloads
                WHERE (initial_identity_signal = ? OR current_identity = ? OR confirmed_identity = ?)
            """
            params = [signal, signal, signal]
            if exclude_workload_id:
                query += " AND id != ?"
                params.append(exclude_workload_id)
            query += " ORDER BY created_at ASC LIMIT 1"
            
            row = conn.execute(query, params).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def create_workload(
        self,
        workload_id: str,
        name: str,
        initial_identity_signal: str,
        status: Optional[str] = None,
        confirmed_identity: Optional[str] = None,
        started_at: Optional[str] = None
    ) -> Workload:
        now_iso = datetime.now(timezone.utc).isoformat()
        started_time = started_at or now_iso

        reused = self.check_identity_reuse(initial_identity_signal, exclude_workload_id=workload_id)
        
        status_reason = None
        confirmed_time = None

        if status:
            final_status = status
            if final_status == IdentityStatus.CONFIRMED.value:
                confirmed_identity = confirmed_identity or initial_identity_signal
                confirmed_time = now_iso
                status_reason = "Pre-provisioned confirmed workload"
        elif reused:
            final_status = IdentityStatus.AMBIGUOUS.value
            status_reason = f"Identity signal reused by another workload (previous owner: {reused['id']})"
        else:
            final_status = IdentityStatus.STARTING.value
            status_reason = "Initial startup phase; identity verification pending"

        current_id = confirmed_identity if (final_status == IdentityStatus.CONFIRMED.value and confirmed_identity) else initial_identity_signal

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO workloads (
                        id, name, initial_identity_signal, current_identity,
                        confirmed_identity, status, status_reason, started_at, confirmed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workload_id,
                        name,
                        initial_identity_signal,
                        current_id,
                        confirmed_identity,
                        final_status,
                        status_reason,
                        started_time,
                        confirmed_time
                    )
                )

                # Log lifecycle event
                conn.execute(
                    """
                    INSERT INTO identity_events (
                        workload_id, event_type, old_status, new_status, identity_signal, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workload_id,
                        "WORKLOAD_STARTED",
                        None,
                        final_status,
                        initial_identity_signal,
                        f"Workload initialized with status {final_status}. {status_reason or ''}".strip(),
                        now_iso
                    )
                )

                if reused and final_status == IdentityStatus.AMBIGUOUS.value:
                    conn.execute(
                        """
                        INSERT INTO identity_events (
                            workload_id, event_type, old_status, new_status, identity_signal, details, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            workload_id,
                            "AMBIGUITY_DETECTED",
                            IdentityStatus.STARTING.value,
                            IdentityStatus.AMBIGUOUS.value,
                            initial_identity_signal,
                            f"Identity collision: '{initial_identity_signal}' was already claimed by {reused['id']}",
                            now_iso
                        )
                    )

            return self.get_workload(workload_id)
        finally:
            conn.close()

    def get_workload(self, workload_id: str) -> Optional[Workload]:
        conn = get_db_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM workloads WHERE id = ?", (workload_id,)).fetchone()
            if not row:
                return None
            return Workload(
                id=row["id"],
                name=row["name"],
                initial_identity_signal=row["initial_identity_signal"],
                current_identity=row["current_identity"],
                confirmed_identity=row["confirmed_identity"],
                status=row["status"],
                status_reason=row["status_reason"],
                started_at=row["started_at"],
                confirmed_at=row["confirmed_at"],
                created_at=row["created_at"]
            )
        finally:
            conn.close()

    def list_workloads(self) -> List[Workload]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM workloads ORDER BY created_at DESC").fetchall()
            return [
                Workload(
                    id=row["id"],
                    name=row["name"],
                    initial_identity_signal=row["initial_identity_signal"],
                    current_identity=row["current_identity"],
                    confirmed_identity=row["confirmed_identity"],
                    status=row["status"],
                    status_reason=row["status_reason"],
                    started_at=row["started_at"],
                    confirmed_at=row["confirmed_at"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    def confirm_identity(self, workload_id: str, confirmed_identity: str) -> Workload:
        workload = self.get_workload(workload_id)
        if not workload:
            raise ValueError(f"Workload {workload_id} not found")

        # Immutability check
        if workload.status == IdentityStatus.CONFIRMED.value:
            if workload.confirmed_identity and workload.confirmed_identity != confirmed_identity:
                raise ValueError(
                    f"Workload identity is cryptographically immutable once confirmed. "
                    f"Existing: '{workload.confirmed_identity}', Requested: '{confirmed_identity}'"
                )
            return workload

        if workload.status in (IdentityStatus.QUARANTINED.value, IdentityStatus.REVOKED.value):
            raise ValueError(
                f"Cannot confirm workload {workload_id} in {workload.status} state. Workload must be re-provisioned."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        old_status = workload.status

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE workloads
                    SET confirmed_identity = ?,
                        current_identity = ?,
                        status = ?,
                        status_reason = ?,
                        confirmed_at = ?
                    WHERE id = ?
                    """,
                    (
                        confirmed_identity,
                        confirmed_identity,
                        IdentityStatus.CONFIRMED.value,
                        "Identity cryptographically verified and attested",
                        now_iso,
                        workload_id
                    )
                )

                conn.execute(
                    """
                    INSERT INTO identity_events (
                        workload_id, event_type, old_status, new_status, identity_signal, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workload_id,
                        "IDENTITY_CONFIRMED",
                        old_status,
                        IdentityStatus.CONFIRMED.value,
                        confirmed_identity,
                        f"Identity confirmed as '{confirmed_identity}'. Ambiguity window closed at {now_iso}.",
                        now_iso
                    )
                )

            return self.get_workload(workload_id)
        finally:
            conn.close()

    def quarantine_workload(self, workload_id: str, reason: str = "Administrative or security quarantine") -> Workload:
        workload = self.get_workload(workload_id)
        if not workload:
            raise ValueError(f"Workload {workload_id} not found")
        
        now_iso = datetime.now(timezone.utc).isoformat()
        old_status = workload.status

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE workloads
                    SET status = ?,
                        status_reason = ?
                    WHERE id = ?
                    """,
                    (IdentityStatus.QUARANTINED.value, reason, workload_id)
                )
                conn.execute(
                    """
                    INSERT INTO identity_events (
                        workload_id, event_type, old_status, new_status, identity_signal, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workload_id,
                        "WORKLOAD_QUARANTINED",
                        old_status,
                        IdentityStatus.QUARANTINED.value,
                        workload.current_identity,
                        reason,
                        now_iso
                    )
                )
            return self.get_workload(workload_id)
        finally:
            conn.close()

    def revoke_workload(self, workload_id: str, reason: str = "Cryptographic identity revoked / runtime compromise detected") -> Workload:
        workload = self.get_workload(workload_id)
        if not workload:
            raise ValueError(f"Workload {workload_id} not found")
        
        now_iso = datetime.now(timezone.utc).isoformat()
        old_status = workload.status

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE workloads
                    SET status = ?,
                        status_reason = ?
                    WHERE id = ?
                    """,
                    (IdentityStatus.REVOKED.value, reason, workload_id)
                )
                conn.execute(
                    """
                    INSERT INTO identity_events (
                        workload_id, event_type, old_status, new_status, identity_signal, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workload_id,
                        "WORKLOAD_REVOKED",
                        old_status,
                        IdentityStatus.REVOKED.value,
                        workload.current_identity,
                        reason,
                        now_iso
                    )
                )
            return self.get_workload(workload_id)
        finally:
            conn.close()

    def check_attestation_timeouts(self, ttl_seconds: float = 60.0) -> List[Dict[str, Any]]:
        """Scans active workloads and quarantines any starting/ambiguous workloads that exceeded attestation TTL."""
        now = datetime.now(timezone.utc)
        quarantined = []
        workloads = self.list_workloads()
        for w in workloads:
            if w.status in (IdentityStatus.STARTING.value, IdentityStatus.AMBIGUOUS.value):
                try:
                    started_dt = datetime.fromisoformat(w.started_at)
                    if started_dt.tzinfo is None:
                        started_dt = started_dt.replace(tzinfo=timezone.utc)
                    elapsed = (now - started_dt).total_seconds()
                    if elapsed > ttl_seconds:
                        reason = f"Attestation TTL expired: pending for {elapsed:.1f}s (limit: {ttl_seconds}s)"
                        self.quarantine_workload(w.id, reason=reason)
                        quarantined.append({"workload_id": w.id, "elapsed_seconds": elapsed, "reason": reason})
                except Exception:
                    pass
        return quarantined

    def get_identity_events(self, workload_id: str) -> List[IdentityEvent]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM identity_events WHERE workload_id = ? ORDER BY timestamp ASC",
                (workload_id,)
            ).fetchall()
            return [
                IdentityEvent(
                    id=row["id"],
                    workload_id=row["workload_id"],
                    event_type=row["event_type"],
                    old_status=row["old_status"],
                    new_status=row["new_status"],
                    identity_signal=row["identity_signal"],
                    details=row["details"],
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    def list_all_identity_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT ie.*, w.name as workload_name
                FROM identity_events ie
                LEFT JOIN workloads w ON ie.workload_id = w.id
                ORDER BY ie.timestamp DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "workload_id": row["workload_id"],
                    "workload_name": row["workload_name"],
                    "event_type": row["event_type"],
                    "old_status": row["old_status"],
                    "new_status": row["new_status"],
                    "identity_signal": row["identity_signal"],
                    "details": row["details"],
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]
        finally:
            conn.close()

