// ==========================================================================
// SEGLabel — Cybersecurity SaaS Command Center JavaScript Controller
// Identity-Aware Microsegmentation with Workload Ambiguity Window Protection
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    setupNavigation();
    setupModals();
    setupGlobalActions();
    animatePageEntrance();
    animateSidebarBeacon();

    // Context-dependent page initializers
    if (document.getElementById("statTotalWorkloads")) {
        loadDashboardStats();
        initHeroVisualizer();
        loadLiveEventStream();
        populateSimulatorSelectors();
    }

    if (document.getElementById("workloadCardsGrid") || document.getElementById("workloadsTableBody")) {
        loadWorkloadsFleet();
    }

    if (document.getElementById("identityEventsTimeline")) {
        loadIdentityEventsPage();
    }

    if (document.getElementById("trafficFlowStream") || document.getElementById("btnSimulateTraffic")) {
        populateSimulatorSelectors();
        animateStaticFlowBeams();
    }

    if (document.getElementById("verificationHeroStage")) {
        initVerificationPage();
    }

    if (document.getElementById("policiesTableBody")) {
        loadPoliciesTable();
    }

    if (document.getElementById("auditTableBody")) {
        loadAuditTable();
    }
}

// ================= PAGE ENTRANCE ANIMATION =================
function animatePageEntrance() {
    if (typeof anime === "undefined") return;

    // Stagger-reveal all cyber-cards on page load
    anime({
        targets: [".cyber-card", ".metric-module", ".hero-command-banner", ".hero-visualizer-card", ".explainer-banner"],
        opacity: [0, 1],
        translateY: [24, 0],
        scale: [0.98, 1],
        delay: anime.stagger(55, { start: 80 }),
        duration: 550,
        easing: "easeOutCubic"
    });

    // Stagger the topbar elements in
    anime({
        targets: ".topbar-left > *, .topbar-actions > *",
        opacity: [0, 1],
        translateY: [-10, 0],
        delay: anime.stagger(60, { start: 120 }),
        duration: 400,
        easing: "easeOutQuad"
    });

    // Sidebar nav links cascade
    anime({
        targets: ".sidebar-link",
        opacity: [0, 1],
        translateX: [-14, 0],
        delay: anime.stagger(45, { start: 200 }),
        duration: 380,
        easing: "easeOutCubic"
    });
}

// ================= SIDEBAR ACTIVE BEACON =================
function animateSidebarBeacon() {
    if (typeof anime === "undefined") return;

    // Continuously pulse the active nav icon
    const activeLink = document.querySelector(".sidebar-link.active .nav-icon");
    if (activeLink) {
        anime({
            targets: activeLink,
            opacity: [1, 0.45, 1],
            color: ["var(--accent-cyan)", "rgba(0, 229, 255, 0.55)", "var(--accent-cyan)"],
            duration: 2200,
            easing: "easeInOutSine",
            loop: true
        });
    }

    // Brand emblem rotation on hover
    const brand = document.querySelector(".brand-emblem");
    if (brand) {
        brand.addEventListener("mouseenter", () => {
            anime({
                targets: brand,
                rotate: [0, 12, -8, 0],
                scale: [1, 1.08, 1],
                duration: 600,
                easing: "easeOutElastic(1, .6)"
            });
        });
    }
}

// ================= STATIC FLOW BEAM PARTICLE ANIMATION =================
function animateStaticFlowBeams() {
    if (typeof anime === "undefined") return;

    // Add a traveling particle to each static flow beam
    document.querySelectorAll(".flow-beam-denied, .flow-beam-allowed").forEach((beam, i) => {
        if (beam.querySelector(".flow-beam-particle")) return;
        const particle = document.createElement("div");
        particle.className = "flow-beam-particle";
        particle.style.cssText = `
            position: absolute;
            top: -3px;
            left: 0;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            pointer-events: none;
            z-index: 4;
        `;
        const isAllowed = beam.classList.contains("flow-beam-allowed");
        particle.style.background = isAllowed ? "#10B981" : "#EF4444";
        particle.style.boxShadow = isAllowed ? "0 0 10px #10B981" : "0 0 10px #EF4444";
        beam.appendChild(particle);

        const trackWidth = beam.offsetWidth > 20 ? (beam.offsetWidth - 12) : 180;
        anime({
            targets: particle,
            translateX: [0, trackWidth],
            opacity: [0, 1, 1, 0],
            duration: 1800,
            delay: i * 300,
            easing: "easeInOutQuad",
            loop: true
        });
    });
}

// ================= NAVIGATION & SIDEBAR =================
function setupNavigation() {
    const toggleBtn = document.getElementById("btnToggleSidebar");
    const sidebar = document.getElementById("cyberSidebar");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("mobile-open");
        });
    }
}

// ================= GLOBAL ACTIONS =================
function setupGlobalActions() {
    // Run Security Demo buttons (navbar and hero)
    const demoBtns = document.querySelectorAll(".btn-run-demo");
    demoBtns.forEach(btn => {
        btn.addEventListener("click", () => triggerSecurityDemo());
    });

    // Reset Database button
    const resetBtn = document.getElementById("btnResetSystem");
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            if (confirm("Reset database to clean seed state? All dynamic workloads and simulation logs will be reset.")) {
                try {
                    const res = await fetch("/api/reset", { method: "POST" });
                    const data = await res.json();
                    alert(data.message || "Database successfully reset.");
                    window.location.reload();
                } catch (err) {
                    console.error("Reset error:", err);
                }
            }
        });
    }

    // Modal submit buttons
    const btnSubmitConfirm = document.getElementById("btnSubmitConfirmIdentity");
    if (btnSubmitConfirm) {
        btnSubmitConfirm.addEventListener("click", submitConfirmIdentity);
    }

    const btnSubmitRegister = document.getElementById("btnSubmitRegisterWorkload");
    if (btnSubmitRegister) {
        btnSubmitRegister.addEventListener("click", submitRegisterWorkload);
    }

    const btnSimTraffic = document.getElementById("btnSimulateTraffic");
    if (btnSimTraffic) {
        btnSimTraffic.addEventListener("click", executeSimulation);
    }

    const btnAddPolicy = document.getElementById("btnSubmitAddPolicy");
    if (btnAddPolicy) {
        btnAddPolicy.addEventListener("click", submitAddPolicy);
    }
}

// ================= MODAL CONTROLLER =================
function setupModals() {
    // Close modal on backdrop click
    document.querySelectorAll(".modal-backdrop-cyber").forEach(backdrop => {
        backdrop.addEventListener("click", (e) => {
            if (e.target === backdrop) {
                closeAllModals();
            }
        });
    });

    // Close on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeAllModals();
        }
    });
}

function closeAllModals() {
    document.querySelectorAll(".modal-backdrop-cyber").forEach(m => m.classList.remove("open"));
    if (demoPlayerTimer) {
        clearInterval(demoPlayerTimer);
        demoPlayerTimer = null;
    }
    refreshCurrentPageData();
}

function refreshCurrentPageData() {
    if (document.getElementById("statTotalWorkloads")) loadDashboardStats();
    if (document.getElementById("liveEventStream")) loadLiveEventStream();
    if (document.getElementById("workloadCardsGrid") || document.getElementById("workloadsTableBody")) loadWorkloadsFleet();
    if (document.getElementById("identityEventsTimeline")) loadIdentityEventsPage();
    if (document.getElementById("trafficFlowStream") || document.getElementById("btnSimulateTraffic")) populateSimulatorSelectors();
    if (document.getElementById("verificationHeroStage")) {
        if (typeof runRetroactiveVerification === "function") runRetroactiveVerification();
        if (typeof loadVerificationHistory === "function") loadVerificationHistory();
    }
    if (document.getElementById("policiesTableBody")) loadPoliciesTable();
    if (document.getElementById("auditTableBody")) loadAuditTable();
}

// ================= STATS & NUMBER COUNT-UP =================
async function loadDashboardStats() {
    try {
        const res = await fetch("/api/stats");
        const stats = await res.json();

        animateCounter("statTotalWorkloads", stats.total_workloads);
        animateCounter("statAmbiguousWorkloads", stats.ambiguous_workloads);
        animateCounter("statDeniedRequests", stats.denied_requests);

        // Verification score percentage
        const totalVerifs = stats.verification_passes + stats.verification_failures;
        const verifScore = totalVerifs > 0 ? Math.round((stats.verification_passes / totalVerifs) * 100) : 100;
        const scoreEl = document.getElementById("statVerifScore");
        if (scoreEl) {
            scoreEl.innerText = `${verifScore}%`;
            scoreEl.style.color = verifScore === 100 ? "var(--status-confirmed)" : "var(--status-violation)";
        }

        // Topbar ambient alert if any workloads are ambiguous
        const topbarAlert = document.getElementById("topbarAmbiguityAlert");
        const topbarCount = document.getElementById("topbarAmbiguousCount");
        if (topbarAlert && topbarCount) {
            if (stats.ambiguous_workloads > 0) {
                topbarCount.innerText = stats.ambiguous_workloads;
                topbarAlert.style.display = "inline-flex";

                // Start attention-grabbing loop animation if not already running
                if (!topbarAlert._animeLoop && typeof anime !== "undefined") {
                    topbarAlert._animeLoop = anime({
                        targets: topbarAlert,
                        translateX: [0, -4, 4, -3, 3, 0],
                        duration: 550,
                        easing: "easeInOutQuad",
                        loop: true,
                        loopDelay: 3500
                    });
                }
            } else {
                topbarAlert.style.display = "none";
                if (topbarAlert._animeLoop) {
                    topbarAlert._animeLoop.pause();
                    topbarAlert._animeLoop = null;
                }
            }
        }

        // Animate sparklines with Anime.js
        if (typeof anime !== "undefined") {
            anime({
                targets: ".spark-bar",
                scaleY: [0.1, 1],
                transformOrigin: "bottom center",
                delay: anime.stagger(25),
                duration: 500,
                easing: "easeOutCubic"
            });
        }
    } catch (err) {
        console.error("Error loading stats:", err);
    }
}

function animateCounter(elemId, targetVal, duration = 1000) {
    const el = document.getElementById(elemId);
    if (!el) return;
    const startVal = parseInt(el.innerText.replace(/[^0-9]/g, "")) || 0;
    const target = parseInt(targetVal) || 0;
    if (startVal === target) {
        el.innerText = target;
        return;
    }

    if (typeof anime !== "undefined") {
        const counterObj = { val: startVal };
        anime({
            targets: counterObj,
            val: target,
            round: 1,
            easing: "easeOutExpo",
            duration: duration,
            update: () => {
                el.innerText = counterObj.val;
            }
        });
    } else {
        const startTime = performance.now();
        function updateVal(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.round(startVal + (target - startVal) * progress);
            el.innerText = current;
            if (progress < 1) {
                requestAnimationFrame(updateVal);
            } else {
                el.innerText = target;
            }
        }
        requestAnimationFrame(updateVal);
    }
}

// ================= HERO SECURITY VISUALIZATION (ANIME.JS POWERED) =================
let heroPacketsAnimTimeline = null;

// ================= ADVANCED CANVAS & TOPOLOGY VISUALIZER ENGINE =================
let visCanvasCtx = null;
let visCanvasAnimId = null;
let visCanvasParticles = [];
let visCanvasSparks = [];
let visCurrentStatus = "AMBIGUOUS";
let visRadarAngle = 0;
let visShieldPulse = 0;

function initVisualizerCanvas() {
    const stage = document.getElementById("nodeGraphStage");
    const canvas = document.getElementById("visCanvasOverlay");
    if (!stage || !canvas) return;

    visCanvasCtx = canvas.getContext("2d");
    if (!visCanvasCtx) return;

    function resizeCanvas() {
        const rect = stage.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        canvas.style.width = `${rect.width}px`;
        canvas.style.height = `${rect.height}px`;
        visCanvasCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Populate ambient particles
    visCanvasParticles = [];
    for (let i = 0; i < 28; i++) {
        visCanvasParticles.push({
            x: Math.random() * stage.offsetWidth,
            y: Math.random() * stage.offsetHeight,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            size: 1 + Math.random() * 2,
            alpha: 0.2 + Math.random() * 0.4,
            color: Math.random() > 0.5 ? "#00E5FF" : "#38BDF8"
        });
    }

    if (visCanvasAnimId) cancelAnimationFrame(visCanvasAnimId);
    animateVisualizerCanvas();
}

function getNodeCenter(el, stage) {
    if (!el || !stage) return { x: 0, y: 0 };
    const rEl = el.getBoundingClientRect();
    const rStage = stage.getBoundingClientRect();
    return {
        x: (rEl.left - rStage.left) + rEl.width / 2,
        y: (rEl.top - rStage.top) + rEl.height / 2,
        w: rEl.width,
        h: rEl.height
    };
}

function spawnDeflectionSparks(x, y, color = "#EF4444") {
    for (let i = 0; i < 16; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 1.5 + Math.random() * 3.5;
        visCanvasSparks.push({
            x: x,
            y: y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            life: 1.0,
            decay: 0.02 + Math.random() * 0.03,
            color: color,
            size: 2 + Math.random() * 2.5
        });
    }
}

function animateVisualizerCanvas() {
    const stage = document.getElementById("nodeGraphStage");
    const canvas = document.getElementById("visCanvasOverlay");
    if (!stage || !canvas || !visCanvasCtx) return;

    const ctx = visCanvasCtx;
    const width = stage.offsetWidth;
    const height = stage.offsetHeight;

    ctx.clearRect(0, 0, width, height);

    const isAmbiguous = (visCurrentStatus === "AMBIGUOUS" || visCurrentStatus === "STARTING");
    const nodeAuthority = document.querySelector(".node-engine");
    const nodeWorkload = document.getElementById("graphNodeWorkload");
    const nodeDb = document.getElementById("targetNodeDb");
    const nodeApi = document.getElementById("targetNodeApi");
    const nodeStudent = document.getElementById("targetNodeStudent");

    const pAuth = getNodeCenter(nodeAuthority, stage);
    const pWl = getNodeCenter(nodeWorkload, stage);
    const pDb = getNodeCenter(nodeDb, stage);
    const pApi = getNodeCenter(nodeApi, stage);
    const pStudent = getNodeCenter(nodeStudent, stage);

    // 1. Draw Ambient Background Cyber Grid
    ctx.strokeStyle = "rgba(56, 189, 248, 0.03)";
    ctx.lineWidth = 1;
    const gridSize = 32;
    for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // 2. Draw Subtle Radar Sweep from Workload Center
    visRadarAngle += 0.015;
    ctx.save();
    ctx.translate(pWl.x, pWl.y);
    const radarGrad = ctx.createRadialGradient(0, 0, 10, 0, 0, 140);
    radarGrad.addColorStop(0, isAmbiguous ? "rgba(245, 158, 11, 0.12)" : "rgba(16, 185, 129, 0.12)");
    radarGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = radarGrad;
    ctx.beginPath();
    ctx.arc(0, 0, 140, visRadarAngle, visRadarAngle + Math.PI / 3);
    ctx.lineTo(0, 0);
    ctx.fill();
    ctx.restore();

    // 3. Draw Dynamic Energy Conduits
    function drawConduit(from, to, statusType) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        const midY = (from.y + to.y) / 2;
        ctx.bezierCurveTo(from.x, midY, to.x, midY, to.x, to.y);

        if (statusType === "amber") {
            ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
            ctx.shadowColor = "#F59E0B";
            ctx.shadowBlur = 6;
        } else if (statusType === "green") {
            ctx.strokeStyle = "rgba(16, 185, 129, 0.5)";
            ctx.shadowColor = "#10B981";
            ctx.shadowBlur = 8;
        } else if (statusType === "red") {
            ctx.strokeStyle = "rgba(239, 68, 68, 0.35)";
            ctx.shadowColor = "#EF4444";
            ctx.shadowBlur = 6;
        } else {
            ctx.strokeStyle = "rgba(0, 229, 255, 0.4)";
            ctx.shadowColor = "#00E5FF";
            ctx.shadowBlur = 6;
        }
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 6]);
        ctx.lineDashOffset = -visRadarAngle * 25;
        ctx.stroke();
        ctx.restore();
    }

    drawConduit(pAuth, pWl, isAmbiguous ? "amber" : "cyan");
    drawConduit(pWl, pDb, isAmbiguous ? "red" : (visCurrentStatus === "CONFIRMED_PAYMENT" ? "green" : "red"));
    drawConduit(pWl, pApi, isAmbiguous ? "red" : (visCurrentStatus === "CONFIRMED_PAYMENT" ? "green" : "red"));
    if (pStudent.x > 0) {
        drawConduit(pWl, pStudent, isAmbiguous ? "red" : "green");
    }

    // 4. Draw Rotating Hexagonal Quarantine Shield around Workload
    visShieldPulse += 0.03;
    const shieldRadius = Math.max(pWl.w, pWl.h) / 2 + 18;
    ctx.save();
    ctx.translate(pWl.x, pWl.y);
    ctx.rotate(visRadarAngle * 0.4);

    if (isAmbiguous) {
        ctx.strokeStyle = `rgba(245, 158, 11, ${0.4 + Math.sin(visShieldPulse) * 0.25})`;
        ctx.shadowColor = "#F59E0B";
        ctx.shadowBlur = 12 + Math.sin(visShieldPulse) * 6;
    } else {
        ctx.strokeStyle = `rgba(16, 185, 129, ${0.4 + Math.sin(visShieldPulse) * 0.25})`;
        ctx.shadowColor = "#10B981";
        ctx.shadowBlur = 12;
    }
    ctx.lineWidth = 2;

    // Draw 6-sided hexagon
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        const a = (i * Math.PI) / 3;
        const hx = Math.cos(a) * shieldRadius;
        const hy = Math.sin(a) * shieldRadius;
        if (i === 0) ctx.moveTo(hx, hy);
        else ctx.lineTo(hx, hy);
    }
    ctx.closePath();
    ctx.stroke();

    // Outer faint pulse ring
    ctx.beginPath();
    ctx.arc(0, 0, shieldRadius + 8 + Math.sin(visShieldPulse) * 4, 0, Math.PI * 2);
    ctx.strokeStyle = isAmbiguous ? "rgba(239, 68, 68, 0.2)" : "rgba(0, 229, 255, 0.2)";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 4]);
    ctx.stroke();
    ctx.restore();

    // 5. Render Ambient Floating Particles
    visCanvasParticles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
    });
    ctx.globalAlpha = 1.0;

    // 6. Render Deflection Spark Bursts
    for (let i = visCanvasSparks.length - 1; i >= 0; i--) {
        const s = visCanvasSparks[i];
        s.x += s.vx;
        s.y += s.vy;
        s.life -= s.decay;

        if (s.life <= 0) {
            visCanvasSparks.splice(i, 1);
            continue;
        }

        ctx.save();
        ctx.fillStyle = s.color;
        ctx.shadowColor = s.color;
        ctx.shadowBlur = 8;
        ctx.globalAlpha = s.life;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size * s.life, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    visCanvasAnimId = requestAnimationFrame(animateVisualizerCanvas);
}

function showVisualizerBanner(message, type = "denied") {
    const banner = document.getElementById("visLiveBanner");
    const icon = document.getElementById("visBannerIcon");
    const text = document.getElementById("visBannerText");
    if (!banner || !text) return;

    banner.className = `vis-live-intercept-banner active ${type}`;
    if (icon) {
        icon.innerText = type === "denied" ? "🔒" : "✓";
    }
    text.innerText = message;

    clearTimeout(banner._timer);
    banner._timer = setTimeout(() => {
        banner.className = "vis-live-intercept-banner";
    }, 4500);
}

function startHeroPacketLoop(isAmbiguous = true) {
    if (typeof anime === "undefined") return;

    const pathEngine = document.getElementById("pathEngineToWorkload");
    const pathDb = document.getElementById("pathWorkloadToDb");
    const pathApi = document.getElementById("pathWorkloadToApi");
    const pathStudent = document.getElementById("pathWorkloadToStudent");
    const pktEngine = document.getElementById("animPacketEngine");
    const pktDb = document.getElementById("animPacketDb");
    const pktApi = document.getElementById("animPacketApi");
    const pktStudent = document.getElementById("animPacketStudent");

    if (!pathEngine || !pathDb || !pathApi || !pktEngine || !pktDb || !pktApi) return;

    try {
        const pEngine = anime.path(pathEngine);
        const pDb = anime.path(pathDb);
        const pApi = anime.path(pathApi);
        const pStudent = pathStudent ? anime.path(pathStudent) : null;

        // Authority Engine -> Workload packet
        anime({
            targets: pktEngine,
            translateX: pEngine("x"),
            translateY: pEngine("y"),
            easing: "linear",
            duration: 1600,
            loop: true
        });

        if (isAmbiguous) {
            pktDb.setAttribute("fill", "#EF4444");
            pktApi.setAttribute("fill", "#EF4444");
            if (pktStudent) pktStudent.setAttribute("fill", "#EF4444");

            // DB packet blocked by Fail-Closed
            anime({
                targets: pktDb,
                translateX: [
                    { value: pDb("x"), duration: 1100, easing: "easeOutQuad" },
                    { value: 450, duration: 350, easing: "easeInQuad" }
                ],
                translateY: [
                    { value: pDb("y"), duration: 1100, easing: "easeOutQuad" },
                    { value: 185, duration: 350, easing: "easeInQuad" }
                ],
                scale: [
                    { value: 1.4, duration: 200 },
                    { value: 1, duration: 900 },
                    { value: 0, duration: 350 }
                ],
                loop: true
            });

            // API packet blocked by Fail-Closed
            anime({
                targets: pktApi,
                translateX: [
                    { value: pApi("x"), duration: 1100, easing: "easeOutQuad" },
                    { value: 450, duration: 350, easing: "easeInQuad" }
                ],
                translateY: [
                    { value: pApi("y"), duration: 1100, easing: "easeOutQuad" },
                    { value: 185, duration: 350, easing: "easeInQuad" }
                ],
                scale: [
                    { value: 1.4, duration: 200 },
                    { value: 1, duration: 900 },
                    { value: 0, duration: 350 }
                ],
                loop: true
            });

            if (pktStudent && pStudent) {
                anime({
                    targets: pktStudent,
                    translateX: [
                        { value: pStudent("x"), duration: 1100, easing: "easeOutQuad" },
                        { value: 450, duration: 350, easing: "easeInQuad" }
                    ],
                    translateY: [
                        { value: pStudent("y"), duration: 1100, easing: "easeOutQuad" },
                        { value: 185, duration: 350, easing: "easeInQuad" }
                    ],
                    scale: [
                        { value: 1.4, duration: 200 },
                        { value: 1, duration: 900 },
                        { value: 0, duration: 350 }
                    ],
                    loop: true
                });
            }
        } else {
            // Confirmed state
            pktDb.setAttribute("fill", "#10B981");
            pktApi.setAttribute("fill", "#10B981");
            if (pktStudent) pktStudent.setAttribute("fill", "#10B981");

            anime({
                targets: pktDb,
                translateX: pDb("x"),
                translateY: pDb("y"),
                scale: 1,
                easing: "linear",
                duration: 1800,
                loop: true
            });

            anime({
                targets: pktApi,
                translateX: pApi("x"),
                translateY: pApi("y"),
                scale: 1,
                easing: "linear",
                duration: 1800,
                loop: true
            });

            if (pktStudent && pStudent) {
                anime({
                    targets: pktStudent,
                    translateX: pStudent("x"),
                    translateY: pStudent("y"),
                    scale: 1,
                    easing: "linear",
                    duration: 1800,
                    loop: true
                });
            }
        }
    } catch (e) {
        console.warn("Hero packet animation error:", e);
    }
}

function initHeroVisualizer() {
    const selector = document.getElementById("visWorkloadSelector");
    if (!selector) return;

    // Initialize Canvas dynamics
    initVisualizerCanvas();

    // Load available workloads into selector
    fetch("/api/workloads")
        .then(res => res.json())
        .then(workloads => {
            if (workloads.length > 0) {
                selector.innerHTML = workloads.map(w => {
                    return `<option value="${escapeHtml(w.id)}">${escapeHtml(w.id)} (${escapeHtml(w.status)})</option>`;
                }).join("");
            }
            updateHeroVisualizerState(selector.value);
        });

    selector.addEventListener("change", () => {
        updateHeroVisualizerState(selector.value);
    });

    // Wire up Direct Simulation Action Buttons
    const btnDb = document.getElementById("btnVisSimDb");
    const btnApi = document.getElementById("btnVisSimApi");
    const btnStudent = document.getElementById("btnVisSimStudent");
    const btnConfirm = document.getElementById("btnVisConfirmIdentity");
    const btnReset = document.getElementById("btnVisResetWindow");

    if (btnDb) {
        btnDb.addEventListener("click", () => simulateVisualizerPacket("database"));
    }
    if (btnApi) {
        btnApi.addEventListener("click", () => simulateVisualizerPacket("payment-api"));
    }
    if (btnStudent) {
        btnStudent.addEventListener("click", () => simulateVisualizerPacket("student-api"));
    }
    if (btnConfirm) {
        btnConfirm.addEventListener("click", () => confirmVisualizerWorkload());
    }
    if (btnReset) {
        btnReset.addEventListener("click", () => resetVisualizerDemo());
    }
}

async function simulateVisualizerPacket(destination) {
    const selector = document.getElementById("visWorkloadSelector");
    const workloadId = selector ? selector.value : "W-NEW";
    const stage = document.getElementById("nodeGraphStage");
    const nodeWorkload = document.getElementById("graphNodeWorkload");

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(workloadId)}/communication`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ destination })
        });
        const data = await res.json();

        // Spawn graphic deflection shockwave
        if (stage && nodeWorkload) {
            const pWl = getNodeCenter(nodeWorkload, stage);
            if (data.decision === "DENY") {
                spawnDeflectionSparks(pWl.x, pWl.y + pWl.h / 2 + 10, "#EF4444");
                showVisualizerBanner(`🚨 FAIL-CLOSED INTERCEPT: Request to '${destination}' BLOCKED (${data.reason})`, "denied");
                
                if (typeof anime !== "undefined") {
                    anime({
                        targets: "#graphNodeWorkload",
                        translateX: [-8, 8, -5, 5, 0],
                        duration: 350,
                        easing: "easeInOutQuad"
                    });
                }
            } else {
                spawnDeflectionSparks(pWl.x, pWl.y + pWl.h / 2 + 10, "#10B981");
                showVisualizerBanner(`✓ AUTHORIZED ACCESS: Request to '${destination}' ALLOWED (${data.reason})`, "allowed");

                if (typeof anime !== "undefined") {
                    anime({
                        targets: "#graphNodeWorkload",
                        scale: [1, 1.06, 1],
                        duration: 400,
                        easing: "easeOutElastic(1, .6)"
                    });
                }
            }
        }

        // Refresh fleet stats and live event feed
        if (typeof loadDashboardStats === "function") loadDashboardStats();
        if (typeof loadLiveEventStream === "function") loadLiveEventStream();
        updateHeroVisualizerState(workloadId);
    } catch (err) {
        console.error("Simulation error:", err);
    }
}

async function confirmVisualizerWorkload() {
    const selector = document.getElementById("visWorkloadSelector");
    const workloadId = selector ? selector.value : "W-NEW";
    const stage = document.getElementById("nodeGraphStage");
    const nodeWorkload = document.getElementById("graphNodeWorkload");

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(workloadId)}/confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirmed_identity: "student" })
        });
        const data = await res.json();

        if (stage && nodeWorkload) {
            const pWl = getNodeCenter(nodeWorkload, stage);
            spawnDeflectionSparks(pWl.x, pWl.y, "#10B981");
        }

        showVisualizerBanner(`🛡️ IDENTITY CRYPTOGRAPHICALLY CONFIRMED as 'student' • Ambiguity Window Closed`, "allowed");
        
        if (typeof showCyberToast === "function") {
            showCyberToast("Attestation Complete", "Workload identity confirmed. Retroactive verification executed with 0 breaches.", "success");
        }

        // Refresh stats, event stream, and visualizer
        if (typeof loadDashboardStats === "function") loadDashboardStats();
        if (typeof loadLiveEventStream === "function") loadLiveEventStream();
        updateHeroVisualizerState(workloadId);
    } catch (err) {
        console.error("Attestation error:", err);
    }
}

async function resetVisualizerDemo() {
    try {
        await fetch("/api/reset", { method: "POST" });
        showVisualizerBanner("↺ Demo Environment Reset to Initial Seed State", "allowed");
        if (typeof showCyberToast === "function") {
            showCyberToast("System Reset", "Database restored to initial seed state. W-NEW restored to Ambiguous.", "info");
        }
        setTimeout(() => window.location.reload(), 600);
    } catch (err) {
        console.error("Reset error:", err);
    }
}

async function updateHeroVisualizerState(workloadId) {
    const nodeWorkload = document.getElementById("graphNodeWorkload");
    const idEl = document.getElementById("visWorkloadId");
    const signalEl = document.getElementById("visWorkloadSignal");
    const badgeEl = document.getElementById("visWorkloadStateBadge");
    const meterEl = document.getElementById("visAttestationMeter");
    const pathEngine = document.getElementById("pathEngineToWorkload");
    const pathDb = document.getElementById("pathWorkloadToDb");
    const pathApi = document.getElementById("pathWorkloadToApi");
    const pathStudent = document.getElementById("pathWorkloadToStudent");
    const targetDb = document.getElementById("targetNodeDb");
    const targetApi = document.getElementById("targetNodeApi");
    const targetStudent = document.getElementById("targetNodeStudent");
    const lockDb = document.getElementById("lockBadgeDb");
    const lockApi = document.getElementById("lockBadgeApi");
    const lockStudent = document.getElementById("lockBadgeStudent");
    const decDb = document.getElementById("decisionBadgeDb");
    const decApi = document.getElementById("decisionBadgeApi");
    const decStudent = document.getElementById("decisionBadgeStudent");

    if (!nodeWorkload) return;

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(workloadId)}`);
        const data = await res.json();
        const w = data.workload;

        if (idEl) idEl.innerText = w.id;
        if (signalEl) signalEl.innerText = w.current_identity || w.initial_identity_signal || "unknown";

        const isAmbiguous = (w.status === "AMBIGUOUS" || w.status === "STARTING");
        visCurrentStatus = isAmbiguous ? "AMBIGUOUS" : (w.confirmed_identity === "payment" ? "CONFIRMED_PAYMENT" : "CONFIRMED_STUDENT");

        if (isAmbiguous) {
            // Ambiguous State: Amber glow, Fail-Closed blocking
            nodeWorkload.className = "graph-node node-workload cyber-glass-pod";
            if (badgeEl) {
                badgeEl.className = "node-badge badge-cyber badge-ambiguous";
                badgeEl.innerText = `⚠ ${w.status}`;
            }

            if (pathEngine) pathEngine.className = "flow-path active-amber";
            if (pathDb) pathDb.className = "flow-path blocked-red";
            if (pathApi) pathApi.className = "flow-path blocked-red";
            if (pathStudent) pathStudent.className = "flow-path blocked-red";

            if (targetDb) targetDb.className = "graph-node node-target denied cyber-glass-pod";
            if (targetApi) targetApi.className = "graph-node node-target denied cyber-glass-pod";
            if (targetStudent) targetStudent.className = "graph-node node-target denied cyber-glass-pod";

            if (lockDb) lockDb.innerText = "🔒";
            if (lockApi) lockApi.innerText = "🔒";
            if (lockStudent) lockStudent.innerText = "🔒";

            if (decDb) decDb.innerText = "DENY (FAIL-CLOSED)";
            if (decApi) decApi.innerText = "DENY (FAIL-CLOSED)";
            if (decStudent) decStudent.innerText = "DENY (FAIL-CLOSED)";
        } else {
            // Confirmed State: Green glow, evaluated policy
            nodeWorkload.className = "graph-node node-workload confirmed cyber-glass-pod";
            if (badgeEl) {
                badgeEl.className = "node-badge badge-cyber badge-confirmed";
                badgeEl.innerText = `✓ CONFIRMED (${escapeHtml(w.confirmed_identity || w.current_identity)})`;
            }

            if (pathEngine) pathEngine.className = "flow-path active-green";

            const ident = (w.confirmed_identity || w.current_identity || "").toLowerCase();
            if (ident === "payment") {
                if (pathDb) pathDb.className = "flow-path active-green";
                if (pathApi) pathApi.className = "flow-path active-green";
                if (pathStudent) pathStudent.className = "flow-path blocked-red";

                if (targetDb) targetDb.className = "graph-node node-target allowed cyber-glass-pod";
                if (targetApi) targetApi.className = "graph-node node-target allowed cyber-glass-pod";
                if (targetStudent) targetStudent.className = "graph-node node-target denied cyber-glass-pod";

                if (lockDb) lockDb.innerText = "✓";
                if (lockApi) lockApi.innerText = "✓";
                if (lockStudent) lockStudent.innerText = "🔒";

                if (decDb) decDb.innerText = "ALLOW (POLICY)";
                if (decApi) decApi.innerText = "ALLOW (POLICY)";
                if (decStudent) decStudent.innerText = "DENY (NO POLICY)";
            } else {
                // student identity
                if (pathDb) pathDb.className = "flow-path blocked-red";
                if (pathApi) pathApi.className = "flow-path blocked-red";
                if (pathStudent) pathStudent.className = "flow-path active-green";

                if (targetDb) targetDb.className = "graph-node node-target denied cyber-glass-pod";
                if (targetApi) targetApi.className = "graph-node node-target denied cyber-glass-pod";
                if (targetStudent) targetStudent.className = "graph-node node-target allowed cyber-glass-pod";

                if (lockDb) lockDb.innerText = "🔒";
                if (lockApi) lockApi.innerText = "🔒";
                if (lockStudent) lockStudent.innerText = "✓";

                if (decDb) decDb.innerText = "DENY (POLICY)";
                if (decApi) decApi.innerText = "DENY (POLICY)";
                if (decStudent) decStudent.innerText = "ALLOW (STUDENT API)";
            }
        }

        // Trigger Anime.js loop & state pulse
        startHeroPacketLoop(isAmbiguous);

        if (typeof anime !== "undefined") {
            anime({
                targets: "#graphNodeWorkload",
                scale: [0.94, 1.05, 1],
                duration: 600,
                easing: "easeOutElastic(1, .7)"
            });

            if (isAmbiguous) {
                anime({
                    targets: ["#targetNodeDb", "#targetNodeApi", "#targetNodeStudent"],
                    translateX: [-5, 5, -2, 2, 0],
                    duration: 400,
                    easing: "easeInOutQuad"
                });
            }
        }
    } catch (err) {
        console.error("Error updating hero visualizer:", err);
    }
}


// ================= LIVE EVENT STREAM =================
async function loadLiveEventStream() {
    const streamContainer = document.getElementById("liveEventStream");
    if (!streamContainer) return;

    try {
        const res = await fetch("/api/audit?limit=6");
        const logs = await res.json();

        if (logs.length === 0) {
            return;
        }

        streamContainer.innerHTML = logs.map(l => {
            const isDenied = l.decision === "DENY";
            const itemClass = isDenied ? "denied" : "confirmed";
            const badgeClass = isDenied ? "badge-denied" : "badge-allowed";
            const icon = isDenied ? "🔒" : "✓";

            return `
                <div class="event-feed-item ${itemClass}">
                    <div class="event-time-workload">
                        <span class="event-timestamp">${formatTime(l.timestamp)}</span>
                        <span class="event-workload-id">${escapeHtml(l.workload_id)}</span>
                    </div>
                    <div class="event-action-desc">
                        Request to <strong>${escapeHtml(l.destination)}</strong>: ${escapeHtml(l.reason)}
                    </div>
                    <div class="event-badge-cell">
                        <span class="badge-cyber ${badgeClass}">${icon} ${escapeHtml(l.decision)}</span>
                    </div>
                </div>
            `;
        }).join("");

        if (typeof anime !== "undefined") {
            anime({
                targets: "#liveEventStream .event-feed-item",
                opacity: [0, 1],
                translateX: [-15, 0],
                delay: anime.stagger(35),
                duration: 350,
                easing: "easeOutCubic"
            });
        }
    } catch (err) {
        console.error("Error loading event stream:", err);
    }
}

// ================= WORKLOAD FLEET EXPLORER =================
let allWorkloadsCache = [];
let currentFleetFilter = 'ALL';

function filterWorkloadFleet(status, btn) {
    currentFleetFilter = status;
    document.querySelectorAll(".filter-pills-bar .filter-pill").forEach(p => p.classList.remove("active"));
    if (btn) btn.classList.add("active");
    const input = document.getElementById("workloadSearchInput");
    loadWorkloadsFleet(input ? input.value : "");
}

function searchWorkloadFleet(query) {
    loadWorkloadsFleet(query);
}

function switchFleetView(view) {
    const cardsGrid = document.getElementById("workloadCardsGrid");
    const tableView = document.getElementById("workloadTableView");
    const btnCards = document.getElementById("btnViewCards");
    const btnTable = document.getElementById("btnViewTable");

    if (view === "cards") {
        if (cardsGrid) {
            cardsGrid.style.display = "grid";
            if (typeof anime !== "undefined") {
                anime({
                    targets: cardsGrid,
                    opacity: [0, 1],
                    translateY: [10, 0],
                    duration: 300,
                    easing: "easeOutQuad"
                });
            }
        }
        if (tableView) tableView.style.display = "none";
        if (btnCards) {
            btnCards.style.background = "rgba(0, 229, 255, 0.15)";
            btnCards.style.color = "var(--accent-cyan)";
        }
        if (btnTable) {
            btnTable.style.background = "transparent";
            btnTable.style.color = "var(--text-muted)";
        }
    } else {
        if (cardsGrid) cardsGrid.style.display = "none";
        if (tableView) {
            tableView.style.display = "block";
            if (typeof anime !== "undefined") {
                anime({
                    targets: tableView,
                    opacity: [0, 1],
                    translateY: [10, 0],
                    duration: 300,
                    easing: "easeOutQuad"
                });
            }
        }
        if (btnCards) {
            btnCards.style.background = "transparent";
            btnCards.style.color = "var(--text-muted)";
        }
        if (btnTable) {
            btnTable.style.background = "rgba(0, 229, 255, 0.15)";
            btnTable.style.color = "var(--accent-cyan)";
        }
    }
}

function openRegisterModal() {
    const modal = document.getElementById("registerWorkloadModal");
    if (modal) {
        modal.classList.add("open");
        if (typeof anime !== "undefined") {
            anime({
                targets: modal.querySelector(".modal-dialog-cyber"),
                scale: [0.92, 1],
                opacity: [0, 1],
                duration: 250,
                easing: "easeOutCubic"
            });
        }
    }
}

async function loadWorkloadsFleet(searchQuery = "") {
    const cardsGrid = document.getElementById("workloadCardsGrid");
    const tableBody = document.getElementById("workloadsTableBody");

    try {
        const res = await fetch("/api/workloads");
        const workloads = await res.json();
        allWorkloadsCache = workloads;

        let filtered = workloads;
        if (currentFleetFilter && currentFleetFilter !== 'ALL') {
            filtered = filtered.filter(w => w.status === currentFleetFilter);
        }

        if (searchQuery) {
            const q = searchQuery.toLowerCase();
            filtered = filtered.filter(w => 
                w.id.toLowerCase().includes(q) ||
                w.name.toLowerCase().includes(q) ||
                (w.current_identity && w.current_identity.toLowerCase().includes(q))
            );
        }

        // 1. Render Cards
        if (cardsGrid) {
            if (filtered.length === 0) {
                cardsGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">No workloads matching filter.</div>`;
            } else {
                cardsGrid.innerHTML = filtered.map(w => {
                    const isAmbiguous = w.status === "AMBIGUOUS" || w.status === "STARTING";
                    const statusClass = isAmbiguous ? "ambiguous" : "confirmed";
                    const badge = isAmbiguous 
                        ? `<span class="badge-cyber badge-ambiguous">⚠ ${escapeHtml(w.status)}</span>`
                        : `<span class="badge-cyber badge-confirmed">✓ CONFIRMED</span>`;

                    return `
                        <div class="workload-card-cyber ${statusClass}">
                            <div class="workload-card-header">
                                <div>
                                    <div class="workload-card-id">
                                        <span class="pulse-dot ${isAmbiguous ? 'amber' : ''}"></span>
                                        ${escapeHtml(w.id)}
                                    </div>
                                    <div class="workload-card-name">${escapeHtml(w.name)}</div>
                                </div>
                                <div>${badge}</div>
                            </div>

                            <div class="workload-identity-box">
                                <div class="identity-row">
                                    <span class="identity-key">Reported Signal:</span>
                                    <span class="identity-val">${escapeHtml(w.initial_identity_signal)}</span>
                                </div>
                                <div class="identity-row">
                                    <span class="identity-key">Evaluated Identity:</span>
                                    <span class="identity-val" style="color: ${isAmbiguous ? 'var(--status-ambiguous)' : 'var(--status-confirmed)'};">
                                        ${escapeHtml(w.current_identity)}
                                    </span>
                                </div>
                                ${w.status_reason ? `
                                    <div style="font-size: 0.72rem; color: var(--status-ambiguous); margin-top: 0.35rem; line-height: 1.3;">
                                        ${escapeHtml(w.status_reason)}
                                    </div>
                                ` : ''}
                            </div>

                            <div class="workload-card-footer">
                                <div style="display: flex; gap: 0.4rem;">
                                    ${isAmbiguous ? `
                                        <button class="btn-cyber btn-cyber-primary btn-sm" onclick="openConfirmModal('${escapeHtml(w.id)}')">
                                            🔐 Attest Identity
                                        </button>
                                    ` : ''}
                                    <button class="btn-cyber btn-cyber-secondary btn-sm" onclick="openWorkloadDetail('${escapeHtml(w.id)}')">
                                        Open Workload →
                                    </button>
                                </div>
                                <div style="display: flex; gap: 0.3rem;">
                                    <button class="btn-cyber btn-cyber-secondary btn-sm" title="Simulate Traffic" onclick="quickSimulate('${escapeHtml(w.id)}')">
                                        ⚡
                                    </button>
                                    <button class="btn-cyber btn-cyber-secondary btn-sm" title="Retroactive Verify" onclick="quickVerify('${escapeHtml(w.id)}')">
                                        🛡
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }).join("");

                if (typeof anime !== "undefined") {
                    anime({
                        targets: "#workloadCardsGrid .workload-card-cyber",
                        opacity: [0, 1],
                        translateY: [20, 0],
                        scale: [0.97, 1],
                        delay: anime.stagger(40),
                        duration: 450,
                        easing: "easeOutCubic"
                    });
                }
            }
        }

        // 2. Render Table
        if (tableBody) {
            if (filtered.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No workloads found.</td></tr>`;
            } else {
                tableBody.innerHTML = filtered.map(w => {
                    const isConfirmed = w.status === "CONFIRMED";
                    const badge = isConfirmed 
                        ? `<span class="badge-cyber badge-confirmed">✓ CONFIRMED</span>`
                        : `<span class="badge-cyber badge-ambiguous">⚠ ${escapeHtml(w.status)}</span>`;

                    return `
                        <tr>
                            <td class="font-mono" style="font-weight: 700; color: var(--accent-cyan);">${escapeHtml(w.id)}</td>
                            <td><strong>${escapeHtml(w.name)}</strong></td>
                            <td class="font-mono">${escapeHtml(w.initial_identity_signal)}</td>
                            <td class="font-mono" style="color: ${isConfirmed ? 'var(--status-confirmed)' : 'var(--status-ambiguous)'};">
                                ${escapeHtml(w.current_identity)}
                            </td>
                            <td>${badge}</td>
                            <td style="font-size: 0.8rem; color: var(--text-muted);">
                                ${w.confirmed_at ? `<span style="color: var(--status-confirmed);">Closed (${getDuration(w.started_at, w.confirmed_at)})</span>` : `<span class="badge-cyber badge-starting">WINDOW OPEN</span>`}
                            </td>
                            <td>
                                <div style="display: flex; gap: 0.4rem;">
                                    ${!isConfirmed ? `
                                        <button class="btn-cyber btn-cyber-primary btn-sm" onclick="openConfirmModal('${escapeHtml(w.id)}')">
                                            Attest
                                        </button>
                                    ` : ''}
                                    <button class="btn-cyber btn-cyber-secondary btn-sm" onclick="openWorkloadDetail('${escapeHtml(w.id)}')">
                                        Detail
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join("");

                if (typeof anime !== "undefined") {
                    anime({
                        targets: "#workloadsTableBody tr",
                        opacity: [0, 1],
                        translateX: [-10, 0],
                        delay: anime.stagger(25),
                        duration: 350,
                        easing: "easeOutQuad"
                    });
                }
            }
        }
    } catch (err) {
        console.error("Error loading workloads:", err);
    }
}

// ================= WORKLOAD DETAIL & JOURNEY TIMELINE =================
async function openWorkloadDetail(workloadId) {
    const modal = document.getElementById("workloadDetailModal");
    const header = document.getElementById("detailWorkloadHeader");
    const identEl = document.getElementById("detailCurrentIdentity");
    const badgeEl = document.getElementById("detailStatusBadge");
    const timelineEl = document.getElementById("detailJourneyTimeline");
    const terminalEl = document.getElementById("detailAuditTerminal");

    if (!modal) return;
    modal.classList.add("open");

    if (header) header.innerText = `${workloadId} | Workload Telemetry`;
    if (timelineEl) timelineEl.innerHTML = `<div style="color: var(--text-muted);">Retrieving identity journey events...</div>`;

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(workloadId)}`);
        const data = await res.json();
        const w = data.workload;
        const events = data.events || [];
        const logs = data.audit_logs || [];

        if (identEl) identEl.innerText = `${w.current_identity} (Claimed: ${w.initial_identity_signal})`;
        if (badgeEl) {
            badgeEl.innerHTML = w.status === "CONFIRMED"
                ? `<span class="badge-cyber badge-confirmed">✓ CONFIRMED</span>`
                : `<span class="badge-cyber badge-ambiguous">⚠ ${escapeHtml(w.status)}</span>`;
        }

        // Build Animated Identity Journey Timeline
        const journeySteps = [
            {
                title: "1. STARTED",
                desc: `Workload container initialized at ${formatTime(w.started_at)}. Initial state: STARTING.`,
                status: "green"
            },
            {
                title: "2. SIGNAL RECEIVED",
                desc: `Identity signal '${w.initial_identity_signal}' received from container environment.`,
                status: "green"
            }
        ];

        if (w.status === "AMBIGUOUS" || w.confirmed_identity) {
            journeySteps.push({
                title: "3. REUSE DETECTED",
                desc: `Collision analysis matched signal '${w.initial_identity_signal}' to another existing workload.`,
                status: "amber"
            });
            journeySteps.push({
                title: "4. AMBIGUOUS",
                desc: `Fail-Closed protection activated. Workload marked AMBIGUOUS. Restrictive quarantine engaged.`,
                status: "amber"
            });
            journeySteps.push({
                title: "5. COMMUNICATION BLOCKED",
                desc: `All ingress/egress requests unconditionally denied (IDENTITY_AMBIGUOUS). Zero trust preserved.`,
                status: "red"
            });
        }

        if (w.status === "CONFIRMED") {
            journeySteps.push({
                title: "6. IDENTITY CONFIRMED",
                desc: `Cryptographic attestation received. Identity attested as '${w.confirmed_identity}' at ${formatTime(w.confirmed_at)}.`,
                status: "green"
            });
            journeySteps.push({
                title: "7. POLICY APPLIED",
                desc: `Ambiguity window closed. Segmentation policies for '${w.confirmed_identity}' now active.`,
                status: "green"
            });
            journeySteps.push({
                title: "8. VERIFICATION PASS",
                desc: `Retroactive audit confirmed 0 wrong-identity access violations during ambiguity window.`,
                status: "green"
            });
        }

        if (timelineEl) {
            timelineEl.innerHTML = journeySteps.map((step, idx) => {
                return `
                    <div class="timeline-step ${step.status}" style="animation: slideInDown ${0.2 + idx * 0.1}s ease-out;">
                        <div class="timeline-step-header">
                            <span class="timeline-step-title">${step.title}</span>
                            <span class="badge-cyber ${step.status === 'green' ? 'badge-confirmed' : (step.status === 'amber' ? 'badge-ambiguous' : 'badge-denied')}">
                                STEP ${idx + 1}
                            </span>
                        </div>
                        <div class="timeline-step-desc">${step.desc}</div>
                    </div>
                `;
            }).join("");
        }

        if (terminalEl) {
            if (logs.length === 0) {
                terminalEl.innerText = "No communication requests recorded for this workload.";
            } else {
                terminalEl.innerText = logs.map(l => 
                    `[${formatTime(l.timestamp)}] ${l.decision} -> ${l.destination} (${l.reason}) [Identity: ${l.source_identity}, InWindow: ${l.in_ambiguity_window}]`
                ).join("\n");
            }
        }
    } catch (err) {
        console.error("Error opening workload detail:", err);
    }
}

// ================= IDENTITY EVENTS PAGE =================
let allEventsCache = [];
let currentEventFilter = 'ALL';

async function loadIdentityEventsPage() {
    const timeline = document.getElementById("identityEventsTimeline");
    const countBadge = document.getElementById("eventsCountBadge");
    if (!timeline) return;

    try {
        const res = await fetch("/api/events?limit=100");
        const events = await res.json();
        allEventsCache = events;

        if (countBadge) countBadge.innerText = `${events.length} EVENTS RECORDED`;

        renderFilteredIdentityEvents();
    } catch (err) {
        console.error("Error loading events:", err);
    }
}

function filterIdentityEvents(filter, btn) {
    currentEventFilter = filter;
    document.querySelectorAll(".filter-pills-bar .filter-pill").forEach(p => p.classList.remove("active"));
    if (btn) btn.classList.add("active");
    renderFilteredIdentityEvents();
}

function renderFilteredIdentityEvents() {
    const timeline = document.getElementById("identityEventsTimeline");
    if (!timeline) return;

    let filtered = allEventsCache;
    if (currentEventFilter === 'COLLISION') {
        filtered = filtered.filter(e => e.event_type.includes("COLLISION") || e.new_status === "AMBIGUOUS");
    } else if (currentEventFilter === 'CONFIRMED') {
        filtered = filtered.filter(e => e.event_type.includes("CONFIRMED") || e.new_status === "CONFIRMED");
    } else if (currentEventFilter === 'STARTUP') {
        filtered = filtered.filter(e => e.event_type.includes("STARTUP") || e.new_status === "STARTING");
    }

    if (filtered.length === 0) {
        timeline.innerHTML = `<div style="color: var(--text-muted); text-align: center; padding: 2rem;">No matching identity events recorded.</div>`;
        return;
    }

    timeline.innerHTML = filtered.map(e => {
        const isAmber = e.new_status === "AMBIGUOUS" || e.event_type.includes("COLLISION");
        const isGreen = e.new_status === "CONFIRMED";
        const statusClass = isAmber ? "amber" : (isGreen ? "green" : "");

        return `
            <div class="timeline-step ${statusClass}">
                <div class="timeline-step-header">
                    <div>
                        <span style="font-family: var(--font-mono); color: var(--accent-cyan); font-weight: 700;">${escapeHtml(e.workload_id)}</span>
                        <span style="color: var(--text-muted); font-size: 0.75rem; margin-left: 0.5rem;">${formatTime(e.timestamp)}</span>
                    </div>
                    <span class="badge-cyber ${isAmber ? 'badge-ambiguous' : (isGreen ? 'badge-confirmed' : 'badge-starting')}">
                        ${escapeHtml(e.event_type)}
                    </span>
                </div>
                <div class="timeline-step-desc">
                    ${escapeHtml(e.details)}
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.4rem; font-family: var(--font-mono);">
                    Signal: <strong>${escapeHtml(e.identity_signal || 'N/A')}</strong> | Status Transition: ${escapeHtml(e.old_status || 'NONE')} ➔ ${escapeHtml(e.new_status)}
                </div>
            </div>
        `;
    }).join("");

    if (typeof anime !== "undefined") {
        anime({
            targets: "#identityEventsTimeline .timeline-step",
            opacity: [0, 1],
            translateX: [-16, 0],
            delay: anime.stagger(40),
            duration: 400,
            easing: "easeOutCubic"
        });
    }
}

// ================= TRAFFIC SIMULATOR & MONITOR =================
async function populateSimulatorSelectors() {
    const workloadSelect = document.getElementById("simWorkloadSelect");
    const destSelect = document.getElementById("simDestSelect");
    if (!workloadSelect) return;

    try {
        const [wRes, dRes] = await Promise.all([
            fetch("/api/workloads"),
            fetch("/api/destinations")
        ]);
        const workloads = await wRes.json();
        const dests = await dRes.json();

        workloadSelect.innerHTML = workloads.map(w => 
            `<option value="${escapeHtml(w.id)}">${escapeHtml(w.id)} (${escapeHtml(w.name)} — ${escapeHtml(w.status)})</option>`
        ).join("");

        if (destSelect) {
            destSelect.innerHTML = dests.map(d => 
                `<option value="${escapeHtml(d.name)}">${escapeHtml(d.name)} (${escapeHtml(d.description || d.category)})</option>`
            ).join("");
        }

        // Check URL parameter for prepopulated workload
        const urlParams = new URLSearchParams(window.location.search);
        const preselected = urlParams.get("workload_id");
        if (preselected && workloadSelect) {
            workloadSelect.value = preselected;
        }
    } catch (err) {
        console.error("Error populating simulator:", err);
    }
}

function useCustomDest() {
    const input = document.getElementById("customDestInput");
    const destSelect = document.getElementById("simDestSelect");
    if (input && input.value.trim() && destSelect) {
        const val = input.value.trim();
        const opt = document.createElement("option");
        opt.value = val;
        opt.text = `${val} (Custom)`;
        opt.selected = true;
        destSelect.appendChild(opt);
    }
}

function setPreset(workloadId, dest) {
    const workloadSelect = document.getElementById("simWorkloadSelect");
    const destSelect = document.getElementById("simDestSelect");
    if (workloadSelect) workloadSelect.value = workloadId;
    if (destSelect) destSelect.value = dest;
    executeSimulation();
}

async function executeSimulation() {
    const workloadSelect = document.getElementById("simWorkloadSelect");
    const destSelect = document.getElementById("simDestSelect");
    const resultBox = document.getElementById("simulationResult");

    if (!workloadSelect || !destSelect) return;
    const workloadId = workloadSelect.value;
    const destination = destSelect.value;

    if (!workloadId || !destination) {
        alert("Please select both a workload and a destination.");
        return;
    }

    if (resultBox) {
        resultBox.innerHTML = `<div style="text-align: center; padding: 1.5rem; color: var(--accent-cyan);">Evaluating Microsegmentation Decision...</div>`;
    }

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(workloadId)}/communication`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ destination })
        });
        const data = await res.json();

        const isAllow = data.decision === "ALLOW";
        const decColor = isAllow ? "var(--status-confirmed)" : "var(--status-violation)";
        const decIcon = isAllow ? "✓" : "🔒";

        // Trigger Anime.js visual packet transmission
        animateConduitPacket(data.workload_id, data.destination, isAllow);

        if (resultBox) {
            resultBox.innerHTML = `
                <div style="background: var(--bg-surface-elevated); border: 1px solid ${isAllow ? 'var(--status-confirmed-border)' : 'var(--status-violation-border)'}; border-radius: var(--radius-md); padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border-card); padding-bottom: 0.75rem;">
                        <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Evaluation Result</span>
                        <span class="badge-cyber ${isAllow ? 'badge-allowed' : 'badge-denied'}">
                            ${decIcon} ${escapeHtml(data.decision)}
                        </span>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 0.6rem; font-size: 0.88rem;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Source Workload:</span>
                            <span class="font-mono" style="font-weight: 700; color: #FFFFFF;">${escapeHtml(data.workload_id)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Identity State:</span>
                            <span class="badge-cyber ${data.current_identity_state === 'AMBIGUOUS' ? 'badge-ambiguous' : 'badge-confirmed'}">
                                ${escapeHtml(data.current_identity_state)}
                            </span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Evaluated Identity:</span>
                            <span class="font-mono" style="font-weight: 600; color: #FFFFFF;">${escapeHtml(data.evaluated_identity)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Destination:</span>
                            <span class="font-mono" style="font-weight: 600; color: var(--accent-cyan);">${escapeHtml(data.destination)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Enforcement Reason:</span>
                            <span class="font-mono" style="font-weight: 700; color: ${decColor};">${escapeHtml(data.reason)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Ambiguity Window:</span>
                            <span style="color: ${data.in_ambiguity_window ? 'var(--status-ambiguous)' : 'var(--text-secondary)'};">
                                ${data.in_ambiguity_window ? 'Active Window (Quarantine)' : 'Closed (Post-Attestation)'}
                            </span>
                        </div>
                    </div>
                </div>
            `;

            if (typeof anime !== "undefined") {
                anime({
                    targets: "#simulationResult > div",
                    opacity: [0, 1],
                    translateY: [16, 0],
                    duration: 400,
                    easing: "easeOutCubic"
                });
            }
        }

        // Add to flow monitor if present
        appendTrafficFlowItem(data);

        // Refresh stats
        if (document.getElementById("statTotalWorkloads")) loadDashboardStats();
    } catch (err) {
        console.error("Simulation error:", err);
    }
}

function animateConduitPacket(sourceId, destName, isAllow) {
    const conduit = document.getElementById("simPacketConduit");
    const srcNode = document.getElementById("conduitSource");
    const destNode = document.getElementById("conduitDest");
    const packet = document.getElementById("conduitPacket");
    const shockwave = document.getElementById("conduitShockwave");
    const line = document.getElementById("conduitLine");

    if (!conduit || !packet) return;

    conduit.style.display = "block";
    if (srcNode) srcNode.innerText = sourceId;
    if (destNode) destNode.innerText = destName;

    if (typeof anime === "undefined") return;

    const lineWidth = line ? (line.offsetWidth - 20) : 320;
    const barrierX = Math.max(lineWidth * 0.55, 120);

    // Initial positioning
    anime.set(packet, { translateX: 0, opacity: 1, scale: 1 });
    anime.set(shockwave, { scale: 0, opacity: 0 });

    if (isAllow) {
        packet.style.backgroundColor = "#10B981";
        packet.style.boxShadow = "0 0 14px #10B981";

        anime.timeline()
            .add({
                targets: packet,
                translateX: [0, lineWidth],
                duration: 850,
                easing: "easeInOutQuad"
            })
            .add({
                targets: destNode,
                scale: [1, 1.08, 1],
                borderColor: ["rgba(56, 189, 248, 0.4)", "#10B981", "rgba(56, 189, 248, 0.4)"],
                duration: 400,
                easing: "easeOutQuad"
            }, "-=150");
    } else {
        packet.style.backgroundColor = "#00E5FF";
        packet.style.boxShadow = "0 0 14px #00E5FF";

        anime.timeline()
            .add({
                targets: packet,
                translateX: [0, barrierX],
                backgroundColor: ["#00E5FF", "#EF4444"],
                boxShadow: ["0 0 12px #00E5FF", "0 0 18px #EF4444"],
                duration: 650,
                easing: "easeInQuad"
            })
            .add({
                targets: shockwave,
                scale: [0.3, 3.2],
                opacity: [1, 0],
                duration: 450,
                easing: "easeOutQuad"
            }, "-=80")
            .add({
                targets: packet,
                translateX: [barrierX, barrierX - 35],
                opacity: [1, 0],
                duration: 300,
                easing: "easeOutQuad"
            }, "-=350");
    }
}

function appendTrafficFlowItem(data) {
    const stream = document.getElementById("trafficFlowStream");
    if (!stream) return;

    const isDenied = data.decision === "DENY";
    const flowRow = document.createElement("div");
    flowRow.className = `flow-row-cyber ${isDenied ? 'denied' : 'allowed'}`;
    flowRow.style.animation = "slideInDown 0.4s ease-out";

    flowRow.innerHTML = `
        <div class="flow-workload-node">
            <span class="pulse-dot ${data.current_identity_state === 'AMBIGUOUS' ? 'amber' : ''}"></span>
            <strong>${escapeHtml(data.workload_id)}</strong>
            <span class="badge-cyber ${data.current_identity_state === 'AMBIGUOUS' ? 'badge-ambiguous' : 'badge-confirmed'}" style="font-size: 0.65rem; padding: 0.1rem 0.4rem;">
                ${escapeHtml(data.current_identity_state)}
            </span>
        </div>
        <div class="flow-line-track">
            <div class="${isDenied ? 'flow-beam-denied' : 'flow-beam-allowed'}"></div>
            <div class="flow-status-pill badge-cyber ${isDenied ? 'badge-denied' : 'badge-allowed'}">
                ${isDenied ? '🔒 BLOCKED' : '✓ ALLOWED'}
            </div>
        </div>
        <div class="flow-dest-node">
            <strong>${escapeHtml(data.destination).toUpperCase()}</strong>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(data.reason)}</span>
        </div>
    `;

    stream.insertBefore(flowRow, stream.firstChild);

    if (typeof anime !== "undefined") {
        anime({
            targets: flowRow,
            opacity: [0, 1],
            translateY: [-14, 0],
            duration: 380,
            easing: "easeOutCubic"
        });
    }
    setTimeout(animateStaticFlowBeams, 60);
}

// ================= RETROACTIVE VERIFICATION =================
async function initVerificationPage() {
    const select = document.getElementById("verifyWorkloadSelect");
    const btnRun = document.getElementById("btnExecuteVerification");
    const btnTamper = document.getElementById("btnInjectTamper");

    if (select) {
        const res = await fetch("/api/workloads");
        const workloads = await res.json();
        select.innerHTML = workloads.map(w => 
            `<option value="${escapeHtml(w.id)}">${escapeHtml(w.id)} (${escapeHtml(w.name)} — ${escapeHtml(w.status)})</option>`
        ).join("");

        // Auto-run verification on selected workload
        if (select.value) {
            runRetroactiveVerification(select.value);
        }

        select.addEventListener("change", () => {
            runRetroactiveVerification(select.value);
        });
    }

    if (btnRun) {
        btnRun.addEventListener("click", () => {
            if (select) runRetroactiveVerification(select.value);
        });
    }

    if (btnTamper) {
        btnTamper.addEventListener("click", async () => {
            if (confirm("Inject synthetic breach into ambiguity window to test FAIL detection and violation animation?")) {
                const wid = select ? select.value : "W-NEW";
                try {
                    const res = await fetch("/api/demo/tamper", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ workload_id: wid, destination: "database" })
                    });
                    const data = await res.json();
                    alert(`Synthetic Breach Injected: Request ID #${data.request_id} forced to ALLOW inside ambiguity window.`);
                    runRetroactiveVerification(wid);
                } catch (err) {
                    console.error("Tamper error:", err);
                }
            }
        });
    }

    loadVerificationHistory();
}

async function runRetroactiveVerification(workloadId) {
    if (!workloadId) {
        const select = document.getElementById("verifyWorkloadSelect");
        if (select && select.value) {
            workloadId = select.value;
        } else {
            return;
        }
    }

    const circle = document.getElementById("gaugeFillCircle");
    const pctText = document.getElementById("gaugePercentText");
    const verdictText = document.getElementById("gaugeVerdictText");
    const banner = document.getElementById("verdictBanner");
    const bannerText = document.getElementById("verdictBannerText");
    const term = document.getElementById("verificationTerminal");

    const durEl = document.getElementById("verifDuration");
    const totalEl = document.getElementById("verifTotalInspected");
    const allowedEl = document.getElementById("verifAllowedDuringWindow");
    const wrongEl = document.getElementById("verifWrongIdentityAccess");
    const violEl = document.getElementById("verifViolationsCount");
    const cardWrong = document.getElementById("cardWrongAccess");
    const cardViol = document.getElementById("cardViolations");

    if (term) term.innerText = `Running retroactive audit on ${workloadId}...\nInspecting ambiguity window communication logs...`;

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(workloadId)}/verify`, {
            method: "POST"
        });
        const data = await res.json();

        // Animate SVG circle (Circumference ~ 565 for r=90)
        const isPass = data.result === "PASS";
        const targetOffset = isPass ? 0 : 280; // Full ring if PASS, partial if FAIL

        if (circle) {
            if (isPass) {
                circle.classList.remove("violation");
            } else {
                circle.classList.add("violation");
            }

            if (typeof anime !== "undefined") {
                anime({
                    targets: circle,
                    strokeDashoffset: [565, targetOffset],
                    duration: 1400,
                    easing: "easeOutElastic(1, .8)"
                });
            } else {
                circle.style.strokeDashoffset = targetOffset.toString();
            }
        }

        if (pctText) {
            if (typeof anime !== "undefined" && isPass) {
                const pObj = { p: 0 };
                anime({
                    targets: pObj,
                    p: 100,
                    round: 1,
                    duration: 1100,
                    easing: "easeOutExpo",
                    update: () => {
                        pctText.innerText = `${pObj.p}%`;
                    }
                });
            } else {
                pctText.innerText = isPass ? "100%" : "FAIL";
            }
        }

        if (verdictText) {
            verdictText.innerText = isPass ? "VERIFIED ✓" : "VIOLATION DETECTED ✗";
            verdictText.style.color = isPass ? "var(--status-confirmed)" : "var(--status-violation)";
        }

        if (banner && bannerText) {
            if (isPass) {
                banner.className = "verdict-banner-cyber";
                bannerText.innerText = "✓ VERIFICATION PASSED — No communication was permitted using an unverified identity.";
                if (typeof anime !== "undefined") {
                    anime({
                        targets: banner,
                        scale: [0.95, 1],
                        opacity: [0, 1],
                        duration: 400,
                        easing: "easeOutCubic"
                    });
                }
            } else {
                banner.className = "verdict-banner-cyber fail";
                bannerText.innerText = `⚠ SECURITY VIOLATION DETECTED — ${data.allowed_in_window} packet(s) permitted during ambiguity window!`;
                if (typeof anime !== "undefined") {
                    anime({
                        targets: "#verificationHeroStage",
                        translateX: [-12, 12, -8, 8, -4, 4, 0],
                        duration: 600,
                        easing: "easeInOutQuad"
                    });
                }
            }
        }

        // Metrics
        if (durEl) durEl.innerText = getDuration(data.window_start, data.window_end);
        if (totalEl) animateCounter("verifTotalInspected", data.total_attempts);
        if (allowedEl) animateCounter("verifAllowedDuringWindow", data.allowed_in_window);
        if (wrongEl) animateCounter("verifWrongIdentityAccess", data.wrong_identity_access);
        if (violEl) animateCounter("verifViolationsCount", data.allowed_in_window);

        if (cardWrong) {
            cardWrong.className = data.wrong_identity_access > 0 ? "verif-mini-card danger" : "verif-mini-card";
        }
        if (cardViol) {
            cardViol.className = data.allowed_in_window > 0 ? "verif-mini-card danger" : "verif-mini-card";
        }

        if (term) {
            term.innerText = data.summary;
            term.style.color = isPass ? "#34D399" : "#F87171";
            term.style.borderColor = isPass ? "var(--status-confirmed-border)" : "var(--status-violation-border)";
        }

        loadVerificationHistory();
    } catch (err) {
        console.error("Verification execution error:", err);
    }
}

async function loadVerificationHistory() {
    const body = document.getElementById("verificationHistoryBody");
    if (!body) return;

    try {
        const res = await fetch("/api/verifications");
        const list = await res.json();

        if (list.length === 0) {
            body.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No verifications recorded yet.</td></tr>`;
            return;
        }

        body.innerHTML = list.map(v => {
            const isPass = v.result === "PASS";
            const badge = isPass
                ? `<span class="badge-cyber badge-pass">✓ PASS</span>`
                : `<span class="badge-cyber badge-fail">✗ FAIL</span>`;

            return `
                <tr>
                    <td class="font-mono" style="font-weight: 700; color: var(--accent-cyan);">${escapeHtml(v.workload_id)}</td>
                    <td>${badge}</td>
                    <td class="font-mono">${v.total_attempts}</td>
                    <td class="font-mono" style="color: ${v.allowed_in_window > 0 ? 'var(--status-violation)' : 'var(--text-secondary)'};">
                        ${v.allowed_in_window}
                    </td>
                    <td style="font-size: 0.8rem; color: var(--text-muted);">${formatTime(v.verified_at)}</td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        console.error("Error loading verification history:", err);
    }
}

// ================= POLICY MATRIX =================
async function loadPoliciesTable() {
    const tbody = document.getElementById("policiesTableBody");
    if (!tbody) return;

    try {
        const res = await fetch("/api/policies");
        const policies = await res.json();

        if (policies.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No policies configured.</td></tr>`;
            return;
        }

        tbody.innerHTML = policies.map(p => {
            const isAllow = p.action === "ALLOW";
            const badge = isAllow
                ? `<span class="badge-cyber badge-allowed">✓ ALLOW</span>`
                : `<span class="badge-cyber badge-denied">✕ DENY</span>`;

            return `
                <tr>
                    <td class="font-mono" style="font-weight: 700; color: var(--accent-cyan);">${escapeHtml(p.source_identity)}</td>
                    <td class="font-mono" style="color: #FFFFFF;">${escapeHtml(p.destination)}</td>
                    <td>${badge}</td>
                    <td style="color: var(--text-secondary);">${escapeHtml(p.description || '-')}</td>
                    <td>
                        <button class="btn-cyber btn-cyber-danger btn-sm" onclick="deletePolicy(${p.id})">
                            Delete
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        if (typeof anime !== "undefined") {
            anime({
                targets: "#policiesTableBody tr",
                opacity: [0, 1],
                translateY: [10, 0],
                delay: anime.stagger(25),
                duration: 350,
                easing: "easeOutQuad"
            });
            anime({
                targets: ".matrix-cell",
                opacity: [0, 1],
                scale: [0.85, 1],
                delay: anime.stagger(20, { from: "center" }),
                duration: 400,
                easing: "easeOutBack"
            });
        }
    } catch (err) {
        console.error("Error loading policies:", err);
    }
}

async function submitAddPolicy() {
    const src = document.getElementById("policySourceInput").value;
    const dest = document.getElementById("policyDestInput").value;
    const action = document.getElementById("policyActionInput").value;
    const desc = document.getElementById("policyDescInput").value;

    if (!src || !dest || !action) {
        alert("Please specify Source Identity, Destination, and Action.");
        return;
    }

    try {
        const res = await fetch("/api/policies", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source_identity: src, destination: dest, action, description: desc })
        });
        const data = await res.json();

        closeAllModals();
        loadPoliciesTable();
        alert("Policy rule saved successfully!");
    } catch (err) {
        console.error("Error saving policy:", err);
    }
}

async function deletePolicy(policyId) {
    if (confirm("Delete this microsegmentation policy rule?")) {
        try {
            await fetch(`/api/policies/${policyId}`, { method: "DELETE" });
            loadPoliciesTable();
        } catch (err) {
            console.error("Delete policy error:", err);
        }
    }
}

function openAddPolicyModal() {
    const modal = document.getElementById("addPolicyModal");
    if (modal) {
        modal.classList.add("open");
        if (typeof anime !== "undefined") {
            anime({
                targets: modal.querySelector(".modal-dialog-cyber"),
                scale: [0.92, 1],
                opacity: [0, 1],
                duration: 250,
                easing: "easeOutCubic"
            });
        }
    }
}

function inspectMatrixRule(src, dst, action) {
    if (typeof anime !== "undefined" && window.event && window.event.currentTarget) {
        anime({
            targets: window.event.currentTarget,
            scale: [1, 1.25, 1],
            duration: 350,
            easing: "easeInOutQuad"
        });
    }
    const modal = document.getElementById("addPolicyModal");
    if (modal) {
        const srcInput = document.getElementById("policySourceInput");
        const dstInput = document.getElementById("policyDestInput");
        const actionInput = document.getElementById("policyActionInput");
        const descInput = document.getElementById("policyDescInput");
        if (srcInput) srcInput.value = src;
        if (dstInput) dstInput.value = dst;
        if (actionInput) actionInput.value = action;
        if (descInput) descInput.value = `Access rule: ${src} -> ${dst} (${action})`;
        openAddPolicyModal();
    }
}

function filterPoliciesTable(query) {
    const q = (query || "").toLowerCase();
    const rows = document.querySelectorAll("#policiesTableBody tr");
    rows.forEach(r => {
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(q) ? "" : "none";
    });
}

// ================= AUDIT LOGS =================
let currentAuditFilter = 'ALL';

function filterAuditLogs(filter, btn) {
    currentAuditFilter = filter;
    document.querySelectorAll(".filter-pills-bar .filter-pill").forEach(p => p.classList.remove("active"));
    if (btn) btn.classList.add("active");
    loadAuditTable();
}

function filterAuditBySearch(query) {
    const q = (query || "").toLowerCase();
    const rows = document.querySelectorAll("#auditTableBody tr");
    rows.forEach(r => {
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(q) ? "" : "none";
    });
}

async function exportAuditJson() {
    try {
        const res = await fetch("/api/audit?limit=1000");
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `seglabel-audit-trail-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Failed to export audit JSON:", err);
    }
}

async function loadAuditTable() {
    const tbody = document.getElementById("auditTableBody");
    const countBadge = document.getElementById("auditTotalCountBadge");
    if (!tbody) return;

    try {
        let url = "/api/audit?limit=200";
        if (currentAuditFilter === 'DENIED') url += "&decision=DENY";
        if (currentAuditFilter === 'ALLOWED') url += "&decision=ALLOW";
        if (currentAuditFilter === 'AMBIGUOUS') url += "&in_ambiguity_window=true";

        const res = await fetch(url);
        let logs = await res.json();

        if (currentAuditFilter === 'VIOLATIONS') {
            logs = logs.filter(l => l.in_ambiguity_window && l.decision === "ALLOW");
        }

        if (countBadge) countBadge.innerText = `${logs.length} EVENTS RECORDED`;

        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No audit logs match filter criteria.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => {
            const isDeny = l.decision === "DENY";
            const badge = isDeny
                ? `<span class="badge-cyber badge-denied">🔒 DENIED</span>`
                : `<span class="badge-cyber badge-allowed">✓ ALLOWED</span>`;

            return `
                <tr>
                    <td class="font-mono" style="font-size: 0.8rem; color: var(--text-muted);">${formatTime(l.timestamp)}</td>
                    <td class="font-mono" style="font-weight: 700; color: var(--accent-cyan);">${escapeHtml(l.workload_id)}</td>
                    <td class="font-mono">${escapeHtml(l.source_identity)}</td>
                    <td class="font-mono" style="color: #FFFFFF;">${escapeHtml(l.destination)}</td>
                    <td>${badge}</td>
                    <td class="font-mono" style="font-size: 0.82rem; color: ${isDeny ? 'var(--status-violation)' : 'var(--status-confirmed)'};">
                        ${escapeHtml(l.reason)}
                        ${l.in_ambiguity_window ? `<span class="badge-cyber badge-ambiguous" style="margin-left: 0.4rem; font-size: 0.65rem;">WINDOW</span>` : ''}
                    </td>
                </tr>
            `;
        }).join("");

        if (typeof anime !== "undefined") {
            anime({
                targets: "#auditTableBody tr",
                opacity: [0, 1],
                translateY: [8, 0],
                delay: anime.stagger(18),
                duration: 300,
                easing: "easeOutCubic"
            });
        }
    } catch (err) {
        console.error("Error loading audit table:", err);
    }
}

// ================= WORKLOAD REGISTRATION & CONFIRMATION =================
async function submitRegisterWorkload() {
    const id = document.getElementById("newWorkloadId").value;
    const name = document.getElementById("newWorkloadName").value;
    const signal = document.getElementById("newWorkloadSignal").value;
    const status = document.getElementById("newWorkloadStatus").value;

    if (!id || !name || !signal) {
        alert("Please enter Workload ID, Name, and Initial Identity Signal.");
        return;
    }

    try {
        const body = { id: id.trim(), name: name.trim(), initial_identity_signal: signal.trim() };
        if (status) body.status = status;

        const res = await fetch("/api/workloads", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();

        if (res.status >= 400) {
            alert(data.error || "Failed to register workload");
            return;
        }

        closeAllModals();
        loadWorkloadsFleet();
        alert(`Workload '${id}' registered! Assigned Status: ${data.status}`);
    } catch (err) {
        console.error("Registration error:", err);
    }
}

function openConfirmModal(workloadId) {
    const modal = document.getElementById("confirmModal");
    const idField = document.getElementById("confirmWorkloadId");
    const inputField = document.getElementById("confirmedIdentityInput");

    if (modal && idField && inputField) {
        idField.value = workloadId;
        inputField.value = "student";
        modal.classList.add("open");
    }
}

async function submitConfirmIdentity() {
    const id = document.getElementById("confirmWorkloadId").value;
    const confirmed = document.getElementById("confirmedIdentityInput").value;

    if (!id || !confirmed) {
        alert("Please enter the confirmed identity.");
        return;
    }

    try {
        const res = await fetch(`/api/workloads/${encodeURIComponent(id)}/confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirmed_identity: confirmed.trim() })
        });
        const data = await res.json();

        closeAllModals();
        alert(`Identity confirmed for ${id}! Ambiguity window closed. Retroactive verification executed: ${data.auto_verification.result} ✓`);

        loadWorkloadsFleet();
        if (document.getElementById("statTotalWorkloads")) loadDashboardStats();
    } catch (err) {
        console.error("Confirmation error:", err);
    }
}

function quickSimulate(workloadId) {
    window.location.href = `/simulator?workload_id=${encodeURIComponent(workloadId)}`;
}

function quickVerify(workloadId) {
    window.location.href = `/verification?workload_id=${encodeURIComponent(workloadId)}`;
}

// ================= CINEMATIC 10-SCENE SECURITY DEMO PLAYER =================
let demoScenes = [];
let demoCurrentSceneIdx = 0;
let demoPlayerTimer = null;
let demoIsPlaying = false;
let demoFinalVerificationData = null;

async function triggerSecurityDemo() {
    const modal = document.getElementById("demoModal");
    const terminal = document.getElementById("demoTerminal");

    if (modal) modal.classList.add("open");
    if (terminal) terminal.innerText = "Executing Official Microsegmentation Ambiguity Window scenario on backend...";

    try {
        const res = await fetch("/api/demo/run", { method: "POST" });
        const demo = await res.json();

        if (!demo.success) {
            alert(`Demo failed: ${demo.error}`);
            return;
        }

        demoFinalVerificationData = demo.final_verification;

        // Build 10 cinematic scenes from backend steps
        demoScenes = [
            {
                scene: 1,
                badge: "SCENE 1 / 10",
                title: "WORKLOAD STARTING: W-NEW",
                desc: "Workload W-NEW starts up in cluster. Memory address space and initial environment configured.",
                badgeHtml: '<span class="badge-cyber badge-starting">⚡ STARTING</span>'
            },
            {
                scene: 2,
                badge: "SCENE 2 / 10",
                title: "IDENTITY SIGNAL RECEIVED: 'payment'",
                desc: "W-NEW announces initial identity signal 'payment' (e.g. from recycled container or reused IP).",
                badgeHtml: '<span class="badge-cyber badge-starting">SIGNAL: payment</span>'
            },
            {
                scene: 3,
                badge: "SCENE 3 / 10",
                title: "⚠ REUSED SIGNAL DETECTED — COLLISION",
                desc: "SegLabel engine identifies that 'payment' was already claimed by confirmed workload W-OLD! Identity is genuinely ambiguous.",
                badgeHtml: '<span class="badge-cyber badge-ambiguous">⚠ IDENTITY_AMBIGUOUS</span>'
            },
            {
                scene: 4,
                badge: "SCENE 4 / 10",
                title: "SECURITY POLICY: DEFAULT DENY ACTIVATED",
                desc: "Fail-Closed Invariant engaged: All ingress/egress is strictly denied during ambiguity window.",
                badgeHtml: '<span class="badge-cyber badge-denied">🔒 FAIL-CLOSED ACTIVE</span>'
            },
            {
                scene: 5,
                badge: "SCENE 5 / 10",
                title: "W-NEW ➔ DATABASE [🔒 BLOCKED]",
                desc: "Workload attempts database query. Blocked immediately under IDENTITY_AMBIGUOUS fail-closed rule.",
                badgeHtml: '<span class="badge-cyber badge-denied">🔒 DENY IDENTITY_AMBIGUOUS</span>'
            },
            {
                scene: 6,
                badge: "SCENE 6 / 10",
                title: "W-NEW ➔ PAYMENT API [🔒 BLOCKED]",
                desc: "CRITICAL PROOF: Even though 'payment' normally has ALLOW access to payment-api, communication is BLOCKED because identity is unconfirmed!",
                badgeHtml: '<span class="badge-cyber badge-denied">🔒 DENY IDENTITY_AMBIGUOUS</span>'
            },
            {
                scene: 7,
                badge: "SCENE 7 / 10",
                title: "IDENTITY ATTESTATION: CONFIRMED AS 'student'",
                desc: "Attestation token verified: W-NEW is actually a 'student' analytics process, not a payment worker!",
                badgeHtml: '<span class="badge-cyber badge-confirmed">✓ ATTESTED: student</span>'
            },
            {
                scene: 8,
                badge: "SCENE 8 / 10",
                title: "AMBIGUITY WINDOW CLOSED: CORRECT POLICY ENGAGED",
                desc: "Window formally closes. Standard microsegmentation policy matrix for 'student' now governs traffic.",
                badgeHtml: '<span class="badge-cyber badge-confirmed">✓ POLICY ACTIVE</span>'
            },
            {
                scene: 9,
                badge: "SCENE 9 / 10",
                title: "student ➔ student-api [✓ ALLOWED]",
                desc: "Verified student process allowed access to student-api according to configured microsegmentation rules.",
                badgeHtml: '<span class="badge-cyber badge-allowed">✓ ALLOW POLICY_ALLOW</span>'
            },
            {
                scene: 10,
                badge: "SCENE 10 / 10",
                title: "RETROACTIVE VERIFICATION: PASSED ✓",
                desc: "Auditor scans entire [t_start, t_confirm] ambiguity window: 0 wrong-identity access allowed! Invariant 100% satisfied.",
                badgeHtml: '<span class="badge-cyber badge-pass">✓ VERIFICATION PASSED (0 VIOLATIONS)</span>'
            }
        ];

        demoCurrentSceneIdx = 0;
        demoRenderCurrentScene();
        demoStartPlay();

        // Refresh all active tab/page data dynamically
        refreshCurrentPageData();
    } catch (err) {
        console.error("Demo run error:", err);
    }
}

function demoRenderCurrentScene() {
    if (!demoScenes.length) return;
    const s = demoScenes[demoCurrentSceneIdx];

    const badge = document.getElementById("demoSceneBadge");
    const title = document.getElementById("demoSceneTitle");
    const desc = document.getElementById("demoSceneDesc");
    const statusBadge = document.getElementById("demoSceneStatusBadge");
    const terminal = document.getElementById("demoTerminal");

    if (badge) badge.innerText = s.badge;
    if (title) title.innerText = s.title;
    if (desc) desc.innerText = s.desc;
    if (statusBadge) statusBadge.innerHTML = s.badgeHtml;

    // Update Stepper Dots
    document.querySelectorAll("#demoStepperDots .demo-dot").forEach((dot, idx) => {
        dot.className = "demo-dot";
        if (idx === demoCurrentSceneIdx) {
            dot.classList.add("active");
        } else if (idx < demoCurrentSceneIdx) {
            dot.classList.add("passed");
        }
    });

    if (terminal) {
        const isLastScene = demoCurrentSceneIdx === 9 && demoFinalVerificationData;
        const rawText = isLastScene
            ? demoFinalVerificationData.summary
            : `[Scene ${demoCurrentSceneIdx + 1}/10] ${s.title}\n${s.desc}\nEnforcement State: ACTIVE`;
        terminal.style.color = isLastScene ? "#34D399" : "#38BDF8";
        typewriterTerminal(terminal, rawText, 12);
    }

    if (typeof anime !== "undefined") {
        anime({
            targets: "#demoSceneDisplay",
            opacity: [0.4, 1],
            translateY: [-6, 0],
            duration: 320,
            easing: "easeOutCubic"
        });
        anime({
            targets: "#demoStepperDots .demo-dot.active",
            scale: [0.8, 1.35, 1],
            duration: 450,
            easing: "easeOutElastic(1, .6)"
        });
    }
}

function demoStartPlay() {
    demoIsPlaying = true;
    const btn = document.getElementById("demoBtnPlayPause");
    if (btn) btn.innerText = "⏸ Pause";

    if (demoPlayerTimer) clearInterval(demoPlayerTimer);
    demoPlayerTimer = setInterval(() => {
        if (demoCurrentSceneIdx < demoScenes.length - 1) {
            demoCurrentSceneIdx++;
            demoRenderCurrentScene();
        } else {
            demoPausePlay();
        }
    }, 2400);
}

function demoPausePlay() {
    demoIsPlaying = false;
    const btn = document.getElementById("demoBtnPlayPause");
    if (btn) btn.innerText = "▶ Play";
    if (demoPlayerTimer) {
        clearInterval(demoPlayerTimer);
        demoPlayerTimer = null;
    }
}

function demoTogglePlay() {
    if (demoIsPlaying) {
        demoPausePlay();
    } else {
        if (demoCurrentSceneIdx >= demoScenes.length - 1) {
            demoCurrentSceneIdx = 0;
        }
        demoStartPlay();
    }
}

function demoNextScene() {
    demoPausePlay();
    if (demoCurrentSceneIdx < demoScenes.length - 1) {
        demoCurrentSceneIdx++;
        demoRenderCurrentScene();
    }
}

function demoPrevScene() {
    demoPausePlay();
    if (demoCurrentSceneIdx > 0) {
        demoCurrentSceneIdx--;
        demoRenderCurrentScene();
    }
}

function demoGoToScene(stepNum) {
    demoPausePlay();
    demoCurrentSceneIdx = Math.max(0, Math.min(demoScenes.length - 1, stepNum - 1));
    demoRenderCurrentScene();
}

function demoReplay() {
    demoCurrentSceneIdx = 0;
    demoRenderCurrentScene();
    demoStartPlay();
}

function demoSkipToEnd() {
    demoPausePlay();
    demoCurrentSceneIdx = demoScenes.length - 1;
    demoRenderCurrentScene();
}

// ================= TYPEWRITER TERMINAL EFFECT =================
function typewriterTerminal(el, text, speed = 14) {
    if (!el) return;
    el.innerText = "";
    let i = 0;
    function tick() {
        if (i < text.length) {
            el.innerText += text[i];
            i++;
            // Auto-scroll terminal
            el.scrollTop = el.scrollHeight;
            setTimeout(tick, speed);
        }
    }
    tick();
}

// ================= HELPERS & FORMATTING =================
function formatTime(isoStr) {
    if (!isoStr) return "-";
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function getDuration(start, end) {
    if (!start) return "0s";
    const s = new Date(start).getTime();
    const e = end ? new Date(end).getTime() : Date.now();
    const sec = Math.max(0, Math.round((e - s) / 1000));
    return `${sec}s`;
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
