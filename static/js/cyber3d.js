/**
 * ============================================================================
 * SegLabel Cyber3D — Interactive 3D Cyber Topology Mesh Engine
 * Zero Trust eBPF Microsegmentation & Identity Ambiguity Visualizer
 * ============================================================================
 */

(function (window) {
    "use strict";

    let scene, camera, renderer, container;
    let animationFrameId = null;
    let isInitialized = false;
    let isAutoRotating = true;
    let nodes = {};
    let conduits = [];
    let particleStreams = [];
    let active3DPackets = [];
    let shockwaves = [];
    let raycaster, mouse;
    let hoveredNode = null;
    let tooltipEl = null;

    // Camera Orbit State
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let cameraTheta = Math.PI / 4;  // horizontal angle
    let cameraPhi = Math.PI / 3.2;   // vertical angle
    let cameraDistance = 14.5;
    const targetLookAt = new THREE.Vector3(0, 0.5, 0);

    // Color Palette
    const CYBER_COLORS = {
        cyan: 0x06b6d4,
        blue: 0x3b82f6,
        emerald: 0x10b981,
        amber: 0xf59e0b,
        rose: 0xf43f5e,
        purple: 0xa855f7,
        darkGrid: 0x1e293b,
        brightGrid: 0x334155,
        bg: 0x070d19
    };

    /**
     * Initialize the 3D Cyber Mesh inside the specified container.
     */
    function initCyber3D(containerElementId) {
        container = document.getElementById(containerElementId);
        if (!container || typeof THREE === "undefined") {
            console.warn("[Cyber3D] Container or THREE.js not available.");
            return;
        }

        if (isInitialized) {
            onWindowResize();
            return;
        }

        const width = container.clientWidth || 900;
        const height = container.clientHeight || 500;

        // 1. Scene
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(CYBER_COLORS.bg, 0.035);

        // 2. Camera
        camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        updateCameraPosition();

        // 3. Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.25;

        // Clear any old canvas and append
        container.innerHTML = "";
        container.appendChild(renderer.domElement);

        // Tooltip element
        tooltipEl = document.createElement("div");
        tooltipEl.className = "hud-3d-tooltip";
        tooltipEl.id = "hud3DTooltip";
        tooltipEl.style.display = "none";
        container.appendChild(tooltipEl);

        // Raycasting
        raycaster = new THREE.Raycaster();
        mouse = new THREE.Vector2();

        // 4. Lighting
        setupLighting();

        // 5. Grid and Environment
        setupEnvironment();

        // 6. 3D Nodes
        buildTopologyNodes();

        // 7. 3D Conduits and Particle Beams
        buildConduits();

        // 8. Event Listeners
        setupEventListeners();

        isInitialized = true;
        animate();
    }

    function setupLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        scene.add(ambientLight);

        // Cyan Key Light
        const cyanLight = new THREE.PointLight(CYBER_COLORS.cyan, 3.5, 30);
        cyanLight.position.set(0, 8, 5);
        scene.add(cyanLight);

        // Emerald Fill Light
        const greenLight = new THREE.PointLight(CYBER_COLORS.emerald, 2.0, 25);
        greenLight.position.set(6, -2, -4);
        scene.add(greenLight);

        // Rose Back Light
        const roseLight = new THREE.PointLight(CYBER_COLORS.rose, 2.0, 25);
        roseLight.position.set(-6, -2, -4);
        scene.add(roseLight);
    }

    function setupEnvironment() {
        // Futuristic Cyber Grid Floor
        const gridHelper = new THREE.GridHelper(24, 24, CYBER_COLORS.cyan, CYBER_COLORS.darkGrid);
        gridHelper.position.y = -3.5;
        gridHelper.material.opacity = 0.45;
        gridHelper.material.transparent = true;
        scene.add(gridHelper);

        // Holographic Scanner Ring on floor
        const ringGeo = new THREE.RingGeometry(5.5, 5.65, 64);
        const ringMat = new THREE.MeshBasicMaterial({
            color: CYBER_COLORS.cyan,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.3
        });
        const scannerRing = new THREE.Mesh(ringGeo, ringMat);
        scannerRing.rotation.x = Math.PI / 2;
        scannerRing.position.y = -3.48;
        scene.add(scannerRing);
        nodes.scannerRing = scannerRing;

        // Subtle ambient dust particles
        const particleCount = 200;
        const particleGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        for (let i = 0; i < particleCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 20;
            positions[i + 1] = (Math.random() - 0.5) * 12;
            positions[i + 2] = (Math.random() - 0.5) * 20;
        }
        particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        const particleMat = new THREE.PointsMaterial({
            color: CYBER_COLORS.cyan,
            size: 0.08,
            transparent: true,
            opacity: 0.4,
            blending: THREE.AdditiveBlending
        });
        const dustParticles = new THREE.Points(particleGeo, particleMat);
        scene.add(dustParticles);
        nodes.dustParticles = dustParticles;
    }

    /**
     * Create floating 3D text/label sprites
     */
    function createLabelSprite(text, subtext, colorHex) {
        const canvas = document.createElement("canvas");
        canvas.width = 256;
        canvas.height = 128;
        const ctx = canvas.getContext("2d");

        // Background card
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.strokeStyle = colorHex;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.roundRect(10, 10, 236, 108, 14);
        ctx.fill();
        ctx.stroke();

        // Title
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 24px 'Space Grotesk', system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(text, 128, 54);

        // Subtext
        ctx.fillStyle = colorHex;
        ctx.font = "16px 'JetBrains Mono', monospace";
        ctx.fillText(subtext, 128, 88);

        const texture = new THREE.CanvasTexture(canvas);
        texture.minFilter = THREE.LinearFilter;
        const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.set(2.4, 1.2, 1);
        return sprite;
    }

    function buildTopologyNodes() {
        // ----------------------------------------------------
        // 1. Identity Authority (Top Center)
        // ----------------------------------------------------
        const authGroup = new THREE.Group();
        authGroup.position.set(0, 3.8, 0);

        // Core Octahedron
        const authCoreGeo = new THREE.OctahedronGeometry(0.75, 0);
        const authCoreMat = new THREE.MeshStandardMaterial({
            color: CYBER_COLORS.cyan,
            emissive: CYBER_COLORS.cyan,
            emissiveIntensity: 0.6,
            roughness: 0.2,
            metalness: 0.8
        });
        const authCore = new THREE.Mesh(authCoreGeo, authCoreMat);
        authGroup.add(authCore);

        // Wireframe cage
        const authCageGeo = new THREE.IcosahedronGeometry(1.15, 1);
        const authCageMat = new THREE.MeshBasicMaterial({
            color: CYBER_COLORS.cyan,
            wireframe: true,
            transparent: true,
            opacity: 0.4
        });
        const authCage = new THREE.Mesh(authCageGeo, authCageMat);
        authGroup.add(authCage);

        // Label sprite
        const authLabel = createLabelSprite("IDENTITY AUTH", "SPIFFE / PKI", "#06B6D4");
        authLabel.position.set(0, 1.4, 0);
        authGroup.add(authLabel);

        authGroup.userData = {
            id: "authority",
            name: "Identity Authority",
            ip: "10.0.0.1 (Control Plane)",
            role: "Root Cryptographic Attestor",
            status: "ACTIVE • ENFORCING",
            clickable: false
        };

        scene.add(authGroup);
        nodes.authority = { group: authGroup, core: authCore, cage: authCage };

        // ----------------------------------------------------
        // 2. Target Workload Pod (Center)
        // ----------------------------------------------------
        const workloadGroup = new THREE.Group();
        workloadGroup.position.set(0, 0.6, 0);

        // Core Sphere
        const workCoreGeo = new THREE.SphereGeometry(0.85, 32, 32);
        const workCoreMat = new THREE.MeshStandardMaterial({
            color: CYBER_COLORS.amber,
            emissive: CYBER_COLORS.amber,
            emissiveIntensity: 0.7,
            roughness: 0.15,
            metalness: 0.6
        });
        const workCore = new THREE.Mesh(workCoreGeo, workCoreMat);
        workloadGroup.add(workCore);

        // Rotating Orbital Ring 1
        const ring1Geo = new THREE.TorusGeometry(1.35, 0.035, 16, 64);
        const ring1Mat = new THREE.MeshBasicMaterial({ color: CYBER_COLORS.cyan, transparent: true, opacity: 0.8 });
        const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
        ring1.rotation.x = Math.PI / 3;
        workloadGroup.add(ring1);

        // Rotating Orbital Ring 2
        const ring2Geo = new THREE.TorusGeometry(1.5, 0.03, 16, 64);
        const ring2Mat = new THREE.MeshBasicMaterial({ color: CYBER_COLORS.amber, transparent: true, opacity: 0.7 });
        const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
        ring2.rotation.y = Math.PI / 4;
        workloadGroup.add(ring2);

        // Status Pulse Glow Halo
        const haloGeo = new THREE.SphereGeometry(1.65, 16, 16);
        const haloMat = new THREE.MeshBasicMaterial({
            color: CYBER_COLORS.amber,
            wireframe: true,
            transparent: true,
            opacity: 0.25
        });
        const halo = new THREE.Mesh(haloGeo, haloMat);
        workloadGroup.add(halo);

        // Label sprite
        const workLabel = createLabelSprite("WORKLOAD W-NEW", "Signal: payment [AMBIGUOUS]", "#F59E0B");
        workLabel.position.set(0, 1.8, 0);
        workloadGroup.add(workLabel);

        workloadGroup.userData = {
            id: "workload",
            name: "Workload Pod (W-NEW)",
            ip: "10.0.4.12 (Recycled IP)",
            role: "Ingressing Container",
            status: "AMBIGUOUS • FAIL-CLOSED",
            clickable: true
        };

        scene.add(workloadGroup);
        nodes.workload = { group: workloadGroup, core: workCore, ring1, ring2, halo, label: workLabel };

        // ----------------------------------------------------
        // 3. Destination Enclaves (Bottom Row)
        // ----------------------------------------------------
        // A. Database
        const dbGroup = buildEnclaveNode("database", -4.8, -2.0, 0.8, "DATABASE", "Port 5432 • Tier 1", CYBER_COLORS.rose, "cylinder");
        scene.add(dbGroup);
        nodes.database = dbGroup;

        // B. Payment API
        const payGroup = buildEnclaveNode("payment-api", 0.0, -2.1, -1.8, "PAYMENT API", "Port 443 • PCI-DSS", CYBER_COLORS.purple, "octahedron");
        scene.add(payGroup);
        nodes.paymentApi = payGroup;

        // C. Student API
        const stuGroup = buildEnclaveNode("student-api", 4.8, -2.0, 0.8, "STUDENT API", "Port 8080 • Scoped", CYBER_COLORS.emerald, "box");
        scene.add(stuGroup);
        nodes.studentApi = stuGroup;
    }

    function buildEnclaveNode(id, x, y, z, title, subtitle, colorHex, shapeType) {
        const group = new THREE.Group();
        group.position.set(x, y, z);

        let geo;
        if (shapeType === "cylinder") {
            geo = new THREE.CylinderGeometry(0.7, 0.7, 1.1, 24);
        } else if (shapeType === "octahedron") {
            geo = new THREE.OctahedronGeometry(0.8, 0);
        } else {
            geo = new THREE.BoxGeometry(1.1, 1.1, 1.1);
        }

        const mat = new THREE.MeshStandardMaterial({
            color: colorHex,
            emissive: colorHex,
            emissiveIntensity: 0.45,
            roughness: 0.25,
            metalness: 0.7
        });
        const mesh = new THREE.Mesh(geo, mat);
        group.add(mesh);

        // Shield wireframe
        const cageGeo = new THREE.SphereGeometry(1.1, 12, 12);
        const cageMat = new THREE.MeshBasicMaterial({
            color: colorHex,
            wireframe: true,
            transparent: true,
            opacity: 0.35
        });
        const cage = new THREE.Mesh(cageGeo, cageMat);
        group.add(cage);

        // Label sprite
        const label = createLabelSprite(title, subtitle, "#" + colorHex.toString(16).padStart(6, "0"));
        label.position.set(0, 1.35, 0);
        group.add(label);

        group.userData = {
            id: id,
            name: title,
            role: "Protected Service Enclave",
            policy: id === "student-api" ? "ALLOWED (Post-Attest)" : "BLOCKED (Fail-Closed)",
            clickable: true
        };

        return { group, mesh, cage, label, id };
    }

    /**
     * Build dynamic 3D conduits linking nodes
     */
    function buildConduits() {
        // Authority -> Workload
        createConduitSpline(
            new THREE.Vector3(0, 3.8, 0),
            new THREE.Vector3(0, 0.6, 0),
            CYBER_COLORS.cyan
        );

        // Workload -> Database
        createConduitSpline(
            new THREE.Vector3(0, 0.6, 0),
            new THREE.Vector3(-4.8, -2.0, 0.8),
            CYBER_COLORS.rose,
            "database"
        );

        // Workload -> Payment API
        createConduitSpline(
            new THREE.Vector3(0, 0.6, 0),
            new THREE.Vector3(0.0, -2.1, -1.8),
            CYBER_COLORS.purple,
            "payment-api"
        );

        // Workload -> Student API
        createConduitSpline(
            new THREE.Vector3(0, 0.6, 0),
            new THREE.Vector3(4.8, -2.0, 0.8),
            CYBER_COLORS.emerald,
            "student-api"
        );
    }

    function createConduitSpline(start, end, colorHex, targetId = null) {
        // Create smooth 3D curved path
        const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
        midPoint.y += 0.35; // gentle upward arc

        const curve = new THREE.CatmullRomCurve3([start, midPoint, end]);
        const tubeGeo = new THREE.TubeGeometry(curve, 32, 0.035, 8, false);
        const tubeMat = new THREE.MeshBasicMaterial({
            color: colorHex,
            transparent: true,
            opacity: 0.35
        });
        const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
        scene.add(tubeMesh);

        // Ambient flowing photons along the curve
        const photonCount = 6;
        const photons = [];
        for (let i = 0; i < photonCount; i++) {
            const pGeo = new THREE.SphereGeometry(0.065, 8, 8);
            const pMat = new THREE.MeshBasicMaterial({
                color: colorHex,
                transparent: true,
                opacity: 0.85
            });
            const pMesh = new THREE.Mesh(pGeo, pMat);
            scene.add(pMesh);
            photons.push({ mesh: pMesh, progress: (i / photonCount) });
        }

        particleStreams.push({ curve, photons, targetId });
        conduits.push({ curve, tubeMesh, targetId });
    }

    /**
     * Shoot a 3D animated packet towards a destination enclave.
     */
    function shoot3DPacket(targetId, decision) {
        const conduit = conduits.find(c => c.targetId === targetId);
        if (!conduit) return;

        const isDenied = (decision === "DENY" || decision === "BLOCKED");
        const packetColor = isDenied ? CYBER_COLORS.rose : CYBER_COLORS.emerald;

        // Glowing packet sphere
        const pGeo = new THREE.SphereGeometry(0.18, 16, 16);
        const pMat = new THREE.MeshStandardMaterial({
            color: packetColor,
            emissive: packetColor,
            emissiveIntensity: 2.0,
            roughness: 0.1
        });
        const packetMesh = new THREE.Mesh(pGeo, pMat);
        scene.add(packetMesh);

        // Light attached to packet
        const packetLight = new THREE.PointLight(packetColor, 2.5, 4);
        packetMesh.add(packetLight);

        active3DPackets.push({
            mesh: packetMesh,
            curve: conduit.curve,
            progress: 0,
            speed: 0.016,
            isDenied: isDenied,
            interceptTriggered: false,
            targetId: targetId
        });
    }

    /**
     * Trigger 3D eBPF Intercept shockwave when a packet is denied.
     */
    function trigger3DInterceptShockwave(position) {
        const ringGeo = new THREE.RingGeometry(0.2, 0.35, 32);
        const ringMat = new THREE.MeshBasicMaterial({
            color: CYBER_COLORS.rose,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 1.0
        });
        const shockwave = new THREE.Mesh(ringGeo, ringMat);
        shockwave.position.copy(position);
        shockwave.lookAt(camera.position);
        scene.add(shockwave);

        // 3D Lock Shield Hologram
        const lockGeo = new THREE.PlaneGeometry(0.65, 0.65);
        const canvas = document.createElement("canvas");
        canvas.width = 128;
        canvas.height = 128;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "rgba(244, 63, 94, 0.9)";
        ctx.font = "bold 64px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("🔒", 64, 64);
        const lockTex = new THREE.CanvasTexture(canvas);
        const lockMat = new THREE.MeshBasicMaterial({ map: lockTex, transparent: true, depthWrite: false });
        const lockMesh = new THREE.Mesh(lockGeo, lockMat);
        lockMesh.position.copy(position);
        lockMesh.position.y += 0.35;
        lockMesh.lookAt(camera.position);
        scene.add(lockMesh);

        shockwaves.push({ mesh: shockwave, lock: lockMesh, scale: 1.0, opacity: 1.0 });
    }

    /**
     * Update Workload status (AMBIGUOUS, CONFIRMED, STARTING)
     */
    function update3DStatus(status) {
        if (!nodes.workload) return;
        const core = nodes.workload.core;
        const halo = nodes.workload.halo;
        const ring2 = nodes.workload.ring2;

        let color = CYBER_COLORS.amber;
        let labelText = "Signal: payment [AMBIGUOUS]";
        let labelColor = "#F59E0B";

        if (status === "CONFIRMED") {
            color = CYBER_COLORS.emerald;
            labelText = "Signal: student [CONFIRMED]";
            labelColor = "#10B981";
        } else if (status === "STARTING") {
            color = CYBER_COLORS.blue;
            labelText = "Signal: payment [STARTING]";
            labelColor = "#3B82F6";
        }

        core.material.color.setHex(color);
        core.material.emissive.setHex(color);
        halo.material.color.setHex(color);
        ring2.material.color.setHex(color);

        // Update workload label sprite
        if (nodes.workload.label) {
            nodes.workload.group.remove(nodes.workload.label);
            const newLabel = createLabelSprite("WORKLOAD W-NEW", labelText, labelColor);
            newLabel.position.set(0, 1.8, 0);
            nodes.workload.group.add(newLabel);
            nodes.workload.label = newLabel;
        }

        nodes.workload.group.userData.status = status;
    }

    /**
     * Setup Interactive Camera Orbit Controls
     */
    function setupEventListeners() {
        const dom = renderer.domElement;

        dom.addEventListener("mousedown", (e) => {
            isDragging = true;
            previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        window.addEventListener("mouseup", () => {
            isDragging = false;
        });

        window.addEventListener("mousemove", (e) => {
            const rect = dom.getBoundingClientRect();
            if (e.clientX >= rect.left && e.clientX <= rect.right &&
                e.clientY >= rect.top && e.clientY <= rect.bottom) {

                mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

                if (isDragging) {
                    const deltaX = e.clientX - previousMousePosition.x;
                    const deltaY = e.clientY - previousMousePosition.y;

                    cameraTheta -= deltaX * 0.007;
                    cameraPhi -= deltaY * 0.007;

                    // Clamp vertical angle to prevent flipping
                    cameraPhi = Math.max(0.2, Math.min(Math.PI / 2.05, cameraPhi));
                    updateCameraPosition();
                    previousMousePosition = { x: e.clientX, y: e.clientY };
                }

                // Raycast for hover tooltips
                checkRaycasting(e.clientX, e.clientY);
            }
        });

        // Mouse Wheel Zoom
        dom.addEventListener("wheel", (e) => {
            e.preventDefault();
            cameraDistance += e.deltaY * 0.012;
            cameraDistance = Math.max(7.5, Math.min(24.0, cameraDistance));
            updateCameraPosition();
        }, { passive: false });

        // Click to interact
        dom.addEventListener("click", () => {
            if (hoveredNode && hoveredNode.userData && hoveredNode.userData.clickable) {
                const id = hoveredNode.userData.id;
                if (id === "database" || id === "payment-api" || id === "student-api") {
                    triggerEgressSimulationFrom3D(id);
                }
            }
        });

        window.addEventListener("resize", onWindowResize);
    }

    function updateCameraPosition() {
        camera.position.x = cameraDistance * Math.sin(cameraPhi) * Math.sin(cameraTheta);
        camera.position.y = cameraDistance * Math.cos(cameraPhi);
        camera.position.z = cameraDistance * Math.sin(cameraPhi) * Math.cos(cameraTheta);
        camera.lookAt(targetLookAt);
    }

    function checkRaycasting(screenX, screenY) {
        raycaster.setFromCamera(mouse, camera);

        // Collect meshes to test
        const testObjects = [];
        if (nodes.authority) testObjects.push(nodes.authority.core);
        if (nodes.workload) testObjects.push(nodes.workload.core);
        if (nodes.database) testObjects.push(nodes.database.mesh);
        if (nodes.paymentApi) testObjects.push(nodes.paymentApi.mesh);
        if (nodes.studentApi) testObjects.push(nodes.studentApi.mesh);

        const intersects = raycaster.intersectObjects(testObjects, false);

        if (intersects.length > 0) {
            const hitMesh = intersects[0].object;
            const parentGroup = hitMesh.parent;
            hoveredNode = parentGroup;

            // Show Tooltip
            if (tooltipEl && parentGroup.userData) {
                const u = parentGroup.userData;
                tooltipEl.innerHTML = `
                    <div class="hud-tip-header">${u.name}</div>
                    <div class="hud-tip-role">${u.role || ""}</div>
                    ${u.ip ? `<div class="hud-tip-row"><span>IP Address:</span> <strong>${u.ip}</strong></div>` : ""}
                    ${u.status ? `<div class="hud-tip-row"><span>State:</span> <strong class="hud-tip-status">${u.status}</strong></div>` : ""}
                    ${u.policy ? `<div class="hud-tip-row"><span>Policy:</span> <strong>${u.policy}</strong></div>` : ""}
                    ${u.clickable ? `<div class="hud-tip-action">⚡ Click node to test traffic</div>` : ""}
                `;
                tooltipEl.style.display = "block";
                tooltipEl.style.left = (screenX + 15) + "px";
                tooltipEl.style.top = (screenY - 20) + "px";
            }
            renderer.domElement.style.cursor = "pointer";
        } else {
            hoveredNode = null;
            if (tooltipEl) tooltipEl.style.display = "none";
            renderer.domElement.style.cursor = isDragging ? "grabbing" : "grab";
        }
    }

    function triggerEgressSimulationFrom3D(targetId) {
        if (targetId === "database" && typeof window.simulateVisEgressDb === "function") {
            window.simulateVisEgressDb();
        } else if (targetId === "payment-api" && typeof window.simulateVisEgressApi === "function") {
            window.simulateVisEgressApi();
        } else if (targetId === "student-api" && typeof window.simulateVisEgressStudent === "function") {
            window.simulateVisEgressStudent();
        }
    }

    function onWindowResize() {
        if (!container || !renderer || !camera) return;
        const width = container.clientWidth || 900;
        const height = container.clientHeight || 500;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    }

    /**
     * Animation Render Loop
     */
    function animate() {
        animationFrameId = requestAnimationFrame(animate);

        // Auto rotation
        if (isAutoRotating && !isDragging) {
            cameraTheta += 0.0025;
            updateCameraPosition();
        }

        // Rotate Authority Cage & Core
        if (nodes.authority) {
            nodes.authority.cage.rotation.y += 0.008;
            nodes.authority.cage.rotation.x += 0.004;
            nodes.authority.core.rotation.y -= 0.01;
        }

        // Rotate Workload Orbital Rings
        if (nodes.workload) {
            nodes.workload.ring1.rotation.z += 0.015;
            nodes.workload.ring2.rotation.z -= 0.012;
            nodes.workload.core.rotation.y += 0.008;
        }

        // Rotate Destination Cages
        if (nodes.database) nodes.database.cage.rotation.y += 0.005;
        if (nodes.paymentApi) nodes.paymentApi.cage.rotation.y -= 0.006;
        if (nodes.studentApi) nodes.studentApi.cage.rotation.y += 0.005;

        // Flow Ambient Photons along conduits
        particleStreams.forEach(stream => {
            stream.photons.forEach(p => {
                p.progress += 0.006;
                if (p.progress > 1.0) p.progress = 0;
                const pos = stream.curve.getPoint(p.progress);
                p.mesh.position.copy(pos);
            });
        });

        // Animate Active 3D Packets
        for (let i = active3DPackets.length - 1; i >= 0; i--) {
            const pkt = active3DPackets[i];
            pkt.progress += pkt.speed;

            if (pkt.isDenied && pkt.progress >= 0.52 && !pkt.interceptTriggered) {
                // Intercept mid-air!
                pkt.interceptTriggered = true;
                trigger3DInterceptShockwave(pkt.mesh.position);
                // Destroy packet with visual flash
                scene.remove(pkt.mesh);
                active3DPackets.splice(i, 1);
                continue;
            }

            if (pkt.progress >= 1.0) {
                // Destination reached (ALLOWED)
                scene.remove(pkt.mesh);
                active3DPackets.splice(i, 1);
                continue;
            }

            const currentPos = pkt.curve.getPoint(pkt.progress);
            pkt.mesh.position.copy(currentPos);
        }

        // Animate Shockwaves
        for (let i = shockwaves.length - 1; i >= 0; i--) {
            const sw = shockwaves[i];
            sw.scale += 0.08;
            sw.opacity -= 0.025;
            sw.mesh.scale.set(sw.scale, sw.scale, sw.scale);
            sw.mesh.material.opacity = sw.opacity;

            if (sw.lock) {
                sw.lock.position.y += 0.008;
                sw.lock.material.opacity = sw.opacity;
            }

            if (sw.opacity <= 0) {
                scene.remove(sw.mesh);
                if (sw.lock) scene.remove(sw.lock);
                shockwaves.splice(i, 1);
            }
        }

        renderer.render(scene, camera);
    }

    /**
     * Controls API
     */
    function resetCamera() {
        cameraTheta = Math.PI / 4;
        cameraPhi = Math.PI / 3.2;
        cameraDistance = 14.5;
        updateCameraPosition();
    }

    function toggleAutoRotate() {
        isAutoRotating = !isAutoRotating;
        return isAutoRotating;
    }

    // Expose Global Cyber3D API
    window.Cyber3D = {
        init: initCyber3D,
        shootPacket: shoot3DPacket,
        updateStatus: update3DStatus,
        resetCamera: resetCamera,
        toggleAutoRotate: toggleAutoRotate,
        resize: onWindowResize
    };

})(window);
