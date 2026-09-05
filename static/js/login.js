/**
 * SegLabel — Cybersecurity Login Interactions & Animation Choreography
 * Powered by Anime.js & HTML5 Canvas
 */

document.addEventListener("DOMContentLoaded", () => {
    initCyberMatrixCanvas();
    runLoginEntranceChoreography();
    setupPasswordToggle();
    setupQuickFill();
    setupLoginFormSubmission();
});

// ================= 1. CYBER MATRIX CANVAS BACKGROUND =================
function initCyberMatrixCanvas() {
    const canvas = document.getElementById("cyberMatrixCanvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        initNodes();
    });

    const nodeCount = Math.min(Math.floor((width * height) / 22000), 55);
    let nodes = [];

    function initNodes() {
        nodes = [];
        for (let i = 0; i < nodeCount; i++) {
            nodes.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.45,
                vy: (Math.random() - 0.5) * 0.45,
                radius: Math.random() * 1.6 + 1.2,
                alpha: Math.random() * 0.5 + 0.3
            });
        }
    }
    initNodes();

    function renderCanvas() {
        ctx.clearRect(0, 0, width, height);

        // Subtle grid lines
        ctx.strokeStyle = "rgba(0, 229, 255, 0.022)";
        ctx.lineWidth = 1;
        const gridSize = 64;
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

        // Draw connections between proximate nodes
        const maxDist = 130;
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[i].x - nodes[j].x;
                const dy = nodes[i].y - nodes[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < maxDist) {
                    const linkAlpha = (1 - dist / maxDist) * 0.18;
                    ctx.strokeStyle = `rgba(0, 229, 255, ${linkAlpha})`;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(nodes[i].x, nodes[i].y);
                    ctx.lineTo(nodes[j].x, nodes[j].y);
                    ctx.stroke();
                }
            }
        }

        // Update and draw nodes
        for (let i = 0; i < nodes.length; i++) {
            const n = nodes[i];
            n.x += n.vx;
            n.y += n.vy;

            if (n.x < 0 || n.x > width) n.vx *= -1;
            if (n.y < 0 || n.y > height) n.vy *= -1;

            ctx.fillStyle = `rgba(0, 229, 255, ${n.alpha})`;
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
            ctx.fill();
        }

        requestAnimationFrame(renderCanvas);
    }

    renderCanvas();
}

// ================= 2. ENTRANCE CHOREOGRAPHY =================
function runLoginEntranceChoreography() {
    if (typeof anime === "undefined") return;

    const timeline = anime.timeline({
        easing: "easeOutCubic"
    });

    // 1. Top system indicator drops in
    timeline.add({
        targets: "#topIndicator",
        opacity: [0, 1],
        translateY: [-24, 0],
        duration: 500
    }, 100);

    // 2. Main Login Card smoothly reveals
    timeline.add({
        targets: "#loginCard",
        opacity: [0, 1],
        translateY: [32, 0],
        scale: [0.96, 1],
        duration: 700
    }, 250);

    // 3. Brand Emblem scales and glows
    timeline.add({
        targets: "#brandEmblem",
        scale: [0.75, 1],
        opacity: [0, 1],
        rotate: [-15, 0],
        duration: 550,
        easing: "easeOutBack"
    }, 450);

    // 4. Security status capsule pop-in
    timeline.add({
        targets: "#securityStatus",
        opacity: [0, 1],
        scale: [0.85, 1],
        duration: 400
    }, 600);

    // 5. Form elements stagger into position
    timeline.add({
        targets: ".heading-group, .form-group-cyber, .form-options-row, #btnSignIn, .demo-credentials-pill, .login-card-footer",
        opacity: [0, 1],
        translateX: [-12, 0],
        delay: anime.stagger(60),
        duration: 450
    }, 650);
}

// ================= 3. PASSWORD VISIBILITY TOGGLE =================
function setupPasswordToggle() {
    const btn = document.getElementById("btnTogglePassword");
    const input = document.getElementById("passwordInput");
    const iconEye = document.getElementById("iconEye");
    const iconEyeOff = document.getElementById("iconEyeOff");

    if (!btn || !input) return;

    btn.addEventListener("click", () => {
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";

        if (iconEye && iconEyeOff) {
            iconEye.style.display = isPassword ? "none" : "block";
            iconEyeOff.style.display = isPassword ? "block" : "none";
        }

        btn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");

        if (typeof anime !== "undefined") {
            anime({
                targets: btn,
                scale: [0.8, 1],
                duration: 200,
                easing: "easeOutQuad"
            });
        }
    });
}

// ================= 4. QUICK FILL DEMO CREDENTIALS =================
function setupQuickFill() {
    const btn = document.getElementById("btnQuickFill");
    const userInp = document.getElementById("usernameInput");
    const passInp = document.getElementById("passwordInput");

    if (!btn || !userInp || !passInp) return;

    btn.addEventListener("click", () => {
        userInp.value = "admin";
        passInp.value = "SegLabel@2026!";

        if (typeof anime !== "undefined") {
            anime({
                targets: [userInp, passInp],
                backgroundColor: ["rgba(0, 229, 255, 0.2)", "rgba(15, 23, 42, 0.75)"],
                duration: 600,
                easing: "easeOutQuad"
            });
        }
    });
}

// ================= 5. FORM SUBMISSION & FEEDBACK =================
function setupLoginFormSubmission() {
    const form = document.getElementById("loginForm");
    const btn = document.getElementById("btnSignIn");
    const btnText = document.getElementById("btnSignInText");
    const spinner = document.getElementById("authSpinner");
    const banner = document.getElementById("authFeedbackBanner");
    const userInp = document.getElementById("usernameInput");
    const passInp = document.getElementById("passwordInput");
    const rememberMe = document.getElementById("rememberMe");

    if (!form || !btn) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = userInp.value.trim();
        const password = passInp.value;
        const remember = rememberMe ? rememberMe.checked : false;
        const nextUrl = form.querySelector("input[name='next']") ? form.querySelector("input[name='next']").value : "/";

        if (!username || !password) {
            showFeedback("Please enter both username and password.", "error");
            return;
        }

        // Set Loading State
        setButtonState("loading");
        clearFeedback();

        try {
            const res = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    remember_me: remember
                })
            });

            const data = await res.json();

            if (res.ok && data.status === "success") {
                // Success State
                setButtonState("success");
                showFeedback("ACCESS GRANTED — REDIRECTING TO COMMAND CENTER...", "success");

                // Smooth card pulse before transition
                if (typeof anime !== "undefined") {
                    anime({
                        targets: "#loginCard",
                        scale: [1, 1.02, 0.98, 1],
                        borderColor: ["rgba(0, 229, 255, 0.22)", "#10B981"],
                        duration: 600,
                        easing: "easeInOutQuad"
                    });
                }

                setTimeout(() => {
                    window.location.href = data.redirect || nextUrl || "/";
                }, 450);
            } else {
                // Denied State
                setButtonState("error");
                showFeedback(data.error || "ACCESS DENIED — INVALID CREDENTIALS", "error");
                shakeCard();

                setTimeout(() => {
                    setButtonState("idle");
                }, 1800);
            }
        } catch (err) {
            console.error("Authentication request error:", err);
            setButtonState("error");
            showFeedback("COMMUNICATION ERROR — UNABLE TO REACH AUTHENTICATION SERVICE", "error");
            shakeCard();

            setTimeout(() => {
                setButtonState("idle");
            }, 1800);
        }
    });

    function setButtonState(state) {
        if (!btn || !btnText) return;

        btn.classList.remove("success-state", "error-state");

        if (state === "loading") {
            btn.disabled = true;
            if (spinner) spinner.style.display = "inline-block";
            btnText.innerText = "AUTHENTICATING...";
        } else if (state === "success") {
            btn.disabled = true;
            btn.classList.add("success-state");
            if (spinner) spinner.style.display = "none";
            btnText.innerText = "ACCESS GRANTED ✓";
        } else if (state === "error") {
            btn.disabled = false;
            btn.classList.add("error-state");
            if (spinner) spinner.style.display = "none";
            btnText.innerText = "ACCESS DENIED ✕";
        } else {
            btn.disabled = false;
            if (spinner) spinner.style.display = "none";
            btnText.innerText = "Sign In →";
        }
    }

    function showFeedback(msg, type) {
        if (!banner) return;
        banner.className = `auth-feedback-banner ${type}`;
        banner.innerText = msg;
        banner.style.display = "block";

        if (typeof anime !== "undefined") {
            anime({
                targets: banner,
                opacity: [0, 1],
                translateY: [-6, 0],
                duration: 250,
                easing: "easeOutQuad"
            });
        }
    }

    function clearFeedback() {
        if (!banner) return;
        banner.style.display = "none";
        banner.innerText = "";
    }

    function shakeCard() {
        if (typeof anime !== "undefined") {
            anime({
                targets: "#loginCard",
                translateX: [-9, 9, -7, 7, -4, 4, 0],
                duration: 450,
                easing: "easeInOutSine"
            });
        }
    }
}
