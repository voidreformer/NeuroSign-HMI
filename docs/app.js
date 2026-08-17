/**
 * NeuroSign-HMI: Interactive Edge AI & Hardware Simulation Engine
 * Simulates 60 FPS Hand Skeleton, 1D-LSTM Inference, Web Speech TTS,
 * 8x13 LED Matrix Glyphs, and STM32 Actuation in the browser.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── 1. Gesture Configurations & Hand Landmark Geometries ────────────────
    const GESTURES = {
        water: {
            name: "Water Please",
            speech: "I need a glass of water, please.",
            conf: 98.4,
            latency: "9.2 ms",
            relay1: false,
            relay2: false,
            pan: 95,
            tilt: 88,
            gsm: "Standby",
            matrixType: "check",
            joints: getHandPoseWater()
        },
        light_on: {
            name: "Turn On Room Light",
            speech: "Turning on room light.",
            conf: 99.1,
            latency: "8.9 ms",
            relay1: true,
            relay2: false,
            pan: 110,
            tilt: 92,
            gsm: "Standby",
            matrixType: "relay_on",
            joints: getHandPoseOpenPalm()
        },
        light_off: {
            name: "Turn Off Room Light",
            speech: "Turning off room light.",
            conf: 97.8,
            latency: "9.5 ms",
            relay1: false,
            relay2: false,
            pan: 80,
            tilt: 90,
            gsm: "Standby",
            matrixType: "idle",
            joints: getHandPoseFist()
        },
        thanks: {
            name: "Thank You",
            speech: "Thank you very much.",
            conf: 99.4,
            latency: "9.1 ms",
            relay1: false,
            relay2: false,
            pan: 90,
            tilt: 85,
            gsm: "Standby",
            matrixType: "check",
            joints: getHandPoseThanks()
        },
        yes: {
            name: "Yes / Understood",
            speech: "Yes, understood.",
            conf: 98.7,
            latency: "8.8 ms",
            relay1: false,
            relay2: false,
            pan: 92,
            tilt: 94,
            gsm: "Standby",
            matrixType: "check",
            joints: getHandPoseThumbsUp()
        },
        sos: {
            name: "EMERGENCY - NEED HELP!",
            speech: "Emergency alert triggered! Sending SOS dispatch!",
            conf: 99.8,
            latency: "9.4 ms",
            relay1: true,
            relay2: true,
            pan: 90,
            tilt: 105,
            gsm: "SMS SENT: +919876543210",
            matrixType: "sos",
            joints: getHandPoseSOS()
        }
    };

    let currentGestureKey = 'water';
    let targetJoints = GESTURES[currentGestureKey].joints;
    let currentJoints = JSON.parse(JSON.stringify(targetJoints));

    // MediaPipe Hand Connection Graph (21 Landmarks)
    const HAND_CONNECTIONS = [
        [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
        [0, 5], [5, 6], [6, 7], [7, 8],       // Index
        [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
        [9, 13], [13, 14], [14, 15], [15, 16],// Ring
        [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
        [0, 17]                               // Palm base
    ];

    // ── 2. Canvas 60 FPS Hand Renderer ──────────────────────────────────────
    const canvas = document.getElementById('handCanvas');
    const ctx = canvas.getContext('2d');

    function animateCanvas() {
        ctx.fillStyle = '#05070d';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw Subtle Video Grid & Face/Body Silhouette Guide
        drawCameraViewportGrid(ctx, canvas.width, canvas.height);

        // Interpolate Joints smoothly toward target pose
        const time = Date.now() * 0.003;
        for (let i = 0; i < 21; i++) {
            const jitterX = Math.sin(time + i) * 0.8;
            const jitterY = Math.cos(time + i * 1.5) * 0.8;
            currentJoints[i].x += (targetJoints[i].x + jitterX - currentJoints[i].x) * 0.15;
            currentJoints[i].y += (targetJoints[i].y + jitterY - currentJoints[i].y) * 0.15;
        }

        // Draw Hand Skeleton Bones
        ctx.lineWidth = 3;
        const isSOS = (currentGestureKey === 'sos');
        ctx.strokeStyle = isSOS ? 'rgba(255, 51, 102, 0.85)' : 'rgba(0, 240, 255, 0.85)';
        ctx.shadowBlur = 12;
        ctx.shadowColor = isSOS ? '#ff3366' : '#00f0ff';

        HAND_CONNECTIONS.forEach(([start, end]) => {
            const p1 = currentJoints[start];
            const p2 = currentJoints[end];
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        });

        // Draw 21 Hand Landmark Points
        ctx.shadowBlur = 10;
        for (let i = 0; i < 21; i++) {
            const pt = currentJoints[i];
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, (i === 0 || i === 4 || i === 8 || i === 12 || i === 16 || i === 20) ? 5 : 3.5, 0, Math.PI * 2);
            ctx.fillStyle = (i === 0) ? '#ffb800' : (isSOS ? '#ffffff' : '#00ff88');
            ctx.shadowColor = (i === 0) ? '#ffb800' : (isSOS ? '#ff3366' : '#00ff88');
            ctx.fill();
        }

        // Reset Shadow for overlay
        ctx.shadowBlur = 0;

        // Bounding Box Simulation
        let minX = 999, maxX = 0, minY = 999, maxY = 0;
        currentJoints.forEach(p => {
            minX = Math.min(minX, p.x);
            maxX = Math.max(maxX, p.x);
            minY = Math.min(minY, p.y);
            maxY = Math.max(maxY, p.y);
        });
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(minX - 15, minY - 15, (maxX - minX) + 30, (maxY - minY) + 30);
        ctx.setLineDash([]);

        requestAnimationFrame(animateCanvas);
    }

    function drawCameraViewportGrid(ctx, w, h) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
        ctx.lineWidth = 1;
        // Crosshair center
        ctx.beginPath();
        ctx.moveTo(w / 2 - 20, h / 2); ctx.lineTo(w / 2 + 20, h / 2);
        ctx.moveTo(w / 2, h / 2 - 20); ctx.lineTo(w / 2, h / 2 + 20);
        ctx.stroke();
    }

    // ── 3. 8x13 LED Matrix Renderer ─────────────────────────────────────────
    const matrixGrid = document.getElementById('ledMatrix');
    const MATRIX_ROWS = 8;
    const MATRIX_COLS = 12;

    // Create 96 pixels
    matrixGrid.innerHTML = '';
    const matrixPixels = [];
    for (let r = 0; r < MATRIX_ROWS; r++) {
        for (let c = 0; c < MATRIX_COLS; c++) {
            const pixel = document.createElement('div');
            pixel.className = 'matrix-pixel';
            matrixGrid.appendChild(pixel);
            matrixPixels.push(pixel);
        }
    }

    function renderMatrixGlyph(type) {
        matrixPixels.forEach(p => p.className = 'matrix-pixel');
        if (type === 'check') {
            // Checkmark pattern
            const checkBits = [
                [4, 4], [5, 5], [6, 6], [7, 7], [6, 8], [5, 9], [4, 10], [3, 11]
            ];
            checkBits.forEach(([r, c]) => {
                if (r < MATRIX_ROWS && c < MATRIX_COLS) {
                    matrixPixels[r * MATRIX_COLS + c].classList.add('lit');
                }
            });
        } else if (type === 'relay_on') {
            // Center filled box
            for (let r = 2; r < 6; r++) {
                for (let c = 4; c < 8; c++) {
                    matrixPixels[r * MATRIX_COLS + c].classList.add('lit');
                }
            }
        } else if (type === 'sos') {
            // All border flash red
            matrixPixels.forEach(p => p.classList.add('lit-red'));
        } else {
            // Idle center dot
            matrixPixels[3 * MATRIX_COLS + 5].classList.add('lit');
            matrixPixels[3 * MATRIX_COLS + 6].classList.add('lit');
            matrixPixels[4 * MATRIX_COLS + 5].classList.add('lit');
            matrixPixels[4 * MATRIX_COLS + 6].classList.add('lit');
        }
    }

    // ── 4. Web Speech API (Voice Synthesis) ──────────────────────────────────
    function speakText(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Stop ongoing speech
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }

    // ── 5. Trigger Gesture Flow ─────────────────────────────────────────────
    function triggerGesture(key) {
        currentGestureKey = key;
        const g = GESTURES[key];
        targetJoints = g.joints;

        // UI updates
        document.getElementById('subtitleText').textContent = `"${g.speech}"`;
        document.getElementById('subtitleConf').textContent = `${g.conf}%`;
        document.getElementById('hudLatency').textContent = g.latency;

        // Hardware actuators
        const r1 = document.getElementById('relay1Status');
        r1.textContent = g.relay1 ? "ON (Energized)" : "OFF";
        r1.className = `act-val ${g.relay1 ? 'on' : 'off'}`;

        const r2 = document.getElementById('relay2Status');
        r2.textContent = g.relay2 ? "STROBE ALARM ON" : "OFF";
        r2.className = `act-val ${g.relay2 ? 'sos' : 'off'}`;

        document.getElementById('servoStatus').textContent = `Pan: ${g.pan}° | Tilt: ${g.tilt}°`;
        
        const gsmEl = document.getElementById('gsmStatus');
        gsmEl.textContent = g.gsm;
        gsmEl.className = `act-val ${key === 'sos' ? 'sos' : ''}`;

        // Matrix glyph
        renderMatrixGlyph(g.matrixType);

        // Voice output
        speakText(g.speech);
    }

    // ── 6. Event Listeners for Gesture Buttons ───────────────────────────────
    const buttons = document.querySelectorAll('.btn-gesture');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const gKey = btn.getAttribute('data-gesture');
            triggerGesture(gKey);
        });
    });

    // ── 7. Simulated Sensor Telemetry Jitter ─────────────────────────────────
    setInterval(() => {
        const voc = Math.floor(105 + Math.random() * 15);
        document.getElementById('valVoc').innerHTML = `${voc} <small>Index</small>`;

        const v = (5.02 + Math.random() * 0.06).toFixed(2);
        const ma = Math.floor(410 + Math.random() * 30);
        document.getElementById('valPower').innerHTML = `${v} <small>V</small> | ${ma} <small>mA</small>`;

        const t = (26.2 + Math.random() * 0.4).toFixed(1);
        const h = Math.floor(51 + Math.random() * 3);
        document.getElementById('valDht').innerHTML = `${t} <small>°C</small> | ${h} <small>%</small>`;
    }, 2000);

    // Initial setup
    renderMatrixGlyph('check');
    animateCanvas();

    // ── Hand Geometry Templates ─────────────────────────────────────────────
    function getHandPoseWater() {
        return [
            {x: 240, y: 280}, // 0: Wrist
            {x: 200, y: 260}, {x: 180, y: 220}, {x: 175, y: 190}, {x: 180, y: 165}, // Thumb
            {x: 220, y: 190}, {x: 215, y: 140}, {x: 215, y: 105}, {x: 215, y: 80},  // Index (Extended)
            {x: 240, y: 190}, {x: 240, y: 135}, {x: 240, y: 100}, {x: 240, y: 75},  // Middle (Extended)
            {x: 260, y: 195}, {x: 265, y: 145}, {x: 265, y: 115}, {x: 265, y: 90},  // Ring (Extended)
            {x: 280, y: 210}, {x: 285, y: 195}, {x: 280, y: 210}, {x: 275, y: 225}  // Pinky (Curled)
        ];
    }

    function getHandPoseOpenPalm() {
        return [
            {x: 240, y: 280},
            {x: 190, y: 250}, {x: 160, y: 215}, {x: 145, y: 180}, {x: 135, y: 155},
            {x: 210, y: 185}, {x: 200, y: 135}, {x: 195, y: 95},  {x: 190, y: 65},
            {x: 240, y: 180}, {x: 240, y: 125}, {x: 240, y: 85},  {x: 240, y: 55},
            {x: 270, y: 185}, {x: 275, y: 135}, {x: 280, y: 95},  {x: 285, y: 65},
            {x: 295, y: 200}, {x: 305, y: 160}, {x: 315, y: 125}, {x: 325, y: 95}
        ];
    }

    function getHandPoseFist() {
        return [
            {x: 240, y: 280},
            {x: 210, y: 255}, {x: 195, y: 235}, {x: 210, y: 220}, {x: 230, y: 225},
            {x: 220, y: 220}, {x: 215, y: 190}, {x: 230, y: 195}, {x: 230, y: 215},
            {x: 240, y: 220}, {x: 240, y: 190}, {x: 245, y: 195}, {x: 245, y: 215},
            {x: 260, y: 220}, {x: 265, y: 190}, {x: 260, y: 195}, {x: 255, y: 215},
            {x: 280, y: 230}, {x: 285, y: 205}, {x: 275, y: 205}, {x: 265, y: 220}
        ];
    }

    function getHandPoseThanks() {
        return [
            {x: 240, y: 290},
            {x: 215, y: 255}, {x: 205, y: 225}, {x: 210, y: 195}, {x: 220, y: 175},
            {x: 230, y: 200}, {x: 230, y: 150}, {x: 230, y: 110}, {x: 230, y: 75},
            {x: 245, y: 200}, {x: 245, y: 150}, {x: 245, y: 110}, {x: 245, y: 75},
            {x: 260, y: 205}, {x: 260, y: 155}, {x: 260, y: 115}, {x: 260, y: 80},
            {x: 275, y: 215}, {x: 275, y: 170}, {x: 275, y: 135}, {x: 275, y: 105}
        ];
    }

    function getHandPoseThumbsUp() {
        return [
            {x: 240, y: 280},
            {x: 210, y: 250}, {x: 200, y: 210}, {x: 200, y: 160}, {x: 200, y: 115}, // Thumb Straight UP
            {x: 230, y: 230}, {x: 245, y: 215}, {x: 250, y: 230}, {x: 240, y: 240}, // Curled fingers
            {x: 245, y: 230}, {x: 255, y: 215}, {x: 260, y: 230}, {x: 250, y: 240},
            {x: 260, y: 235}, {x: 265, y: 220}, {x: 270, y: 235}, {x: 260, y: 245},
            {x: 275, y: 240}, {x: 275, y: 230}, {x: 280, y: 240}, {x: 270, y: 250}
        ];
    }

    function getHandPoseSOS() {
        return [
            {x: 240, y: 270},
            {x: 210, y: 240}, {x: 180, y: 200}, {x: 165, y: 170}, {x: 150, y: 145},
            {x: 220, y: 190}, {x: 210, y: 140}, {x: 205, y: 95},  {x: 200, y: 60},
            {x: 245, y: 185}, {x: 245, y: 130}, {x: 245, y: 85},  {x: 245, y: 50},
            {x: 270, y: 190}, {x: 275, y: 140}, {x: 280, y: 95},  {x: 285, y: 60},
            {x: 295, y: 210}, {x: 310, y: 175}, {x: 320, y: 140}, {x: 330, y: 110}
        ];
    }
});
