/**
 * ============================================================================
 * PROJECT: NEURO SIGN - Paralysis Patient Assistance System
 * DEVELOPED BY: Rudra Attri Pandey
 * MODULE: Client-Side Dashboard Controller & Real-Time Telemetry Engine
 * ============================================================================
 */

// Global State
let ws = null;
let isConnected = false;
let tremorHistory = new Array(80).fill(0);
let lastGestureId = 0;

// DOM Elements
const wsDot = document.getElementById('wsDot');
const wsText = document.getElementById('wsText');
const emergencyBanner = document.getElementById('emergencyBanner');
const emergencyTitle = document.getElementById('emergencyTitle');

// Initialize on Window Load
window.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    initCanvas();
    startWaveformLoop();
});

// --- WEBSOCKET CONNECTION ---
function initWebSocket() {
    const host = window.location.hostname || '192.168.4.1';
    const wsUrl = `ws://${host}:81/`;

    console.log(`[NEURO SIGN] Connecting to WebSocket Hub at ${wsUrl}...`);

    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            isConnected = true;
            wsDot.style.background = '#00f298';
            wsDot.style.boxShadow = '0 0 10px #00f298';
            wsText.innerText = 'HUB ONLINE (192.168.4.1)';
            wsText.style.color = '#00f298';
            addLogEntry('WebSocket Connected to Neuro Sign Hub', '100%', 'READY', 'Live Stream Active');
        };

        ws.onclose = () => {
            isConnected = false;
            wsDot.style.background = '#ff3366';
            wsDot.style.boxShadow = '0 0 10px #ff3366';
            wsText.innerText = 'DISCONNECTED (RECONNECTING...)';
            wsText.style.color = '#ff3366';
            // Reconnect after 2 seconds
            setTimeout(initWebSocket, 2000);
        };

        ws.onerror = (err) => {
            console.warn('[NEURO SIGN] WebSocket error, starting simulation fallback mode:', err);
            startSimulationMode();
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                updateTelemetryUI(data);
            } catch (e) {
                console.error('JSON parse error:', e);
            }
        };
    } catch (e) {
        startSimulationMode();
    }
}

// --- TELEMETRY UI DISPATCHER ---
function updateTelemetryUI(data) {
    // 1. RF Link & Signal Quality
    const rfConnected = data.rfConnected;
    const rfQuality = data.rfSignalQuality || 0;
    const rfStatusEl = document.getElementById('rfLinkStatus');
    const rfQualityEl = document.getElementById('rfQualityText');

    if (rfConnected) {
        rfStatusEl.innerText = 'CONNECTED';
        rfStatusEl.className = 'm-val online';
        rfQualityEl.innerText = `${rfQuality}%`;
    } else {
        rfStatusEl.innerText = 'SEARCHING';
        rfStatusEl.className = 'm-val alert';
        rfQualityEl.innerText = '0%';
    }

    // Signal Bars
    updateSignalBars(rfQuality, rfConnected);

    // Battery & Packet Counters
    document.getElementById('gloveBattery').innerText = `${data.battery || 0}%`;
    document.getElementById('pktCount').innerText = data.packetsReceived || 0;
    
    const total = (data.packetsReceived || 0) + (data.packetsDropped || 0);
    const lossPct = total > 0 ? Math.round(((data.packetsDropped || 0) / total) * 100) : 0;
    document.getElementById('pktLoss').innerText = `${lossPct}%`;

    // 2. Flex Sensors
    const f1 = data.flex ? data.flex[0] : 0;
    const f2 = data.flex ? data.flex[1] : 0;
    const f3 = data.flex ? data.flex[2] : 0;

    document.getElementById('f1Val').innerText = `${f1}%`;
    document.getElementById('f1Fill').style.width = `${f1}%`;

    document.getElementById('f2Val').innerText = `${f2}%`;
    document.getElementById('f2Fill').style.width = `${f2}%`;

    document.getElementById('f3Val').innerText = `${f3}%`;
    document.getElementById('f3Fill').style.width = `${f3}%`;

    // 3. Orientation & Tremor
    document.getElementById('pitchVal').innerText = `${data.pitch || 0}°`;
    document.getElementById('rollVal').innerText = `${data.roll || 0}°`;
    document.getElementById('tremorVal').innerText = `${data.tremor || 0}%`;

    // Update Tremor History Buffer for Canvas Plot
    tremorHistory.push(data.tremor || 0);
    tremorHistory.shift();

    // 4. Neuro AI Gesture Classification
    const gestureName = data.gestureName || 'NEUTRAL / RESTING';
    const gestureId = data.gestureId || 0;
    const confidence = Math.round((data.gestureConfidence || 0.95) * 100);

    document.getElementById('aiGestureName').innerText = gestureName;
    document.getElementById('aiConfFill').style.width = `${confidence}%`;
    document.getElementById('aiConfText').innerText = `Confidence: ${confidence}%`;

    highlightLegend(gestureId);

    // Track state change & log
    if (gestureId !== lastGestureId && gestureId !== 0) {
        lastGestureId = gestureId;
        handleGestureTrigger(gestureId, gestureName, confidence);
    } else if (gestureId === 0) {
        lastGestureId = 0;
    }

    // 5. Environmental Sensors
    document.getElementById('envTemp').innerText = `${(data.temperatureC || 25.0).toFixed(1)} °C`;
    document.getElementById('envHum').innerText = `${(data.humidityPercent || 50.0).toFixed(1)} %`;
    document.getElementById('envPress').innerText = `${(data.pressureHpa || 1013.2).toFixed(1)} hPa`;
    
    const voc = data.vocIndex || 100;
    const vocEl = document.getElementById('envVoc');
    if (voc < 150) {
        vocEl.innerText = `${voc} (Clean)`;
        vocEl.className = 'env-val good';
    } else if (voc < 280) {
        vocEl.innerText = `${voc} (Moderate)`;
        vocEl.className = 'env-val highlight';
    } else {
        vocEl.innerText = `${voc} (Poor/Polluted)`;
        vocEl.className = 'env-val alert';
    }

    document.getElementById('envAlt').innerText = `${(data.altitudeMeters || 45.0).toFixed(1)} m`;

    // 6. Home Automation Relay States
    if (data.relayState) {
        for (let i = 0; i < 4; i++) {
            const btn = document.getElementById(`btnRelay${i}`);
            if (btn) {
                if (data.relayState[i]) {
                    btn.classList.add('on');
                    btn.innerText = 'ON';
                } else {
                    btn.classList.remove('on');
                    btn.innerText = 'OFF';
                }
            }
        }
    }

    // 7. Electrical INA219
    document.getElementById('pwrVolt').innerText = `${(data.busVoltageV || 5.0).toFixed(2)} V`;
    document.getElementById('pwrCurr').innerText = `${(data.currentMA || 145.0).toFixed(1)} mA`;
    document.getElementById('pwrWatts').innerText = `${(data.powerMW || 725.0).toFixed(1)} mW`;

    // 8. Spasm / Emergency Alarm Banner
    if (data.spasmAlertActive || gestureId === 1 || gestureId === 99) {
        emergencyBanner.style.display = 'flex';
        emergencyTitle.innerText = gestureId === 99 ? 'PATIENT MUSCLE SPASM DETECTED!' : 'EMERGENCY HELP REQUESTED!';
    }
}

// --- SIGNAL BARS ---
function updateSignalBars(quality, connected) {
    const bars = [
        document.getElementById('bar1'),
        document.getElementById('bar2'),
        document.getElementById('bar3'),
        document.getElementById('bar4')
    ];

    bars.forEach(b => b.classList.remove('active'));
    if (!connected) return;

    if (quality > 15) bars[0].classList.add('active');
    if (quality > 40) bars[1].classList.add('active');
    if (quality > 65) bars[2].classList.add('active');
    if (quality > 85) bars[3].classList.add('active');
}

// --- LEGEND HIGHLIGHT ---
function highlightLegend(gestureId) {
    const validIds = [1, 2, 3, 4, 11, 12, 13, 21, 22, 23];
    validIds.forEach(id => {
        const item = document.getElementById(`leg${id}`);
        if (item) {
            if (id === gestureId) item.classList.add('active');
            else item.classList.remove('active');
        }
    });
}

// --- EVENT & GESTURE TRIGGER HANDLER ---
function handleGestureTrigger(gestureId, name, conf) {
    let action = 'Speech Cue Broadcast';
    let tag = 'CALL';

    if (gestureId === 4 || gestureId === 99) {
        tag = 'ALARM';
        action = 'Alarm Siren & Relay 4 Fired';
    } else if (gestureId === 11) {
        action = 'Relay 1 (Light 1) Toggled';
    } else if (gestureId === 12) {
        action = 'Relay 2 (Fan) Toggled';
    } else if (gestureId === 13) {
        action = 'Relay 3 (Bed Position) Toggled';
    } else if (gestureId === 21) {
        action = 'Nurse Call Chime Broadcast';
    } else if (gestureId === 22) {
        tag = 'ALARM';
        action = 'Pain Warning Alert Broadcast';
    } else if (gestureId === 23) {
        action = 'All Appliances Switched OFF (Sleep)';
    }

    addLogEntry(name, `${conf}%`, tag, action);
}

function addLogEntry(event, confidence, statusTag, action) {
    const tbody = document.getElementById('logTableBody');
    const now = new Date().toTimeString().split(' ')[0];

    let tagClass = 'tag-ready';
    if (statusTag === 'CALL') tagClass = 'tag-call';
    if (statusTag === 'ALARM') tagClass = 'tag-alarm';

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${now}</td>
        <td><strong>${event}</strong></td>
        <td>${confidence}</td>
        <td><span class="log-tag ${tagClass}">${statusTag}</span></td>
        <td>${action}</td>
    `;

    tbody.insertBefore(tr, tbody.firstChild);

    // Limit to 20 entries
    if (tbody.children.length > 20) {
        tbody.removeChild(tbody.lastChild);
    }
}

function clearEventLog() {
    document.getElementById('logTableBody').innerHTML = '';
}

// --- CONTROLS & ACTIONS ---
function toggleRelay(index) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'toggle_relay', index: index }));
    } else {
        // Fallback fetch REST
        fetch('/api/relay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index: index })
        }).catch(err => console.log('Relay POST fallback'));

        // Toggle locally for instant UI feedback
        const btn = document.getElementById(`btnRelay${index}`);
        btn.classList.toggle('on');
        btn.innerText = btn.classList.contains('on') ? 'ON' : 'OFF';
    }
}

function playVoicePrompt(alertId) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'play_sound', id: alertId }));
    } else {
        fetch('/api/alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: alertId })
        }).catch(err => console.log('Alert POST fallback'));
    }
}

function dismissAlarm() {
    emergencyBanner.style.display = 'none';
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'reset_alarm' }));
    }
    const r4 = document.getElementById('btnRelay3');
    if (r4) {
        r4.classList.remove('on');
        r4.innerText = 'OFF';
    }
}

// --- CANVAS TREMOR WAVEFORM ---
let canvas, ctx;
function initCanvas() {
    canvas = document.getElementById('tremorWaveCanvas');
    if (canvas) {
        ctx = canvas.getContext('2d');
    }
}

function startWaveformLoop() {
    function draw() {
        if (ctx && canvas) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw grid lines
            ctx.strokeStyle = 'rgba(0, 242, 254, 0.08)';
            ctx.lineWidth = 1;
            for (let y = 15; y < canvas.height; y += 20) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }

            // Draw Tremor Spline
            ctx.beginPath();
            ctx.strokeStyle = '#00f2fe';
            ctx.lineWidth = 2;
            ctx.shadowColor = '#00f2fe';
            ctx.shadowBlur = 8;

            const step = canvas.width / (tremorHistory.length - 1);
            for (let i = 0; i < tremorHistory.length; i++) {
                const val = tremorHistory[i];
                const y = canvas.height - (val / 100) * (canvas.height - 12) - 6;
                const x = i * step;

                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
            ctx.shadowBlur = 0; // Reset
        }
        requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
}

// --- SIMULATION FALLBACK MODE (If running in browser without ESP32 hardware) ---
function startSimulationMode() {
    wsText.innerText = 'SIMULATION DEMO MODE';
    wsText.style.color = '#ffaa00';
    wsDot.style.background = '#ffaa00';

    let simTick = 0;
    setInterval(() => {
        simTick++;
        const gestures = [
            { id: 0, name: 'NEUTRAL / RESTING', conf: 0.95 },
            { id: 2, name: 'Need Water (Index Point)', conf: 0.98 },
            { id: 3, name: 'Need Food (Peace Sign)', conf: 0.96 },
            { id: 4, name: 'Toggle Light (Palm Up)', conf: 0.94 },
            { id: 0, name: 'NEUTRAL / RESTING', conf: 0.95 },
        ];
        const gIdx = Math.floor(simTick / 60) % gestures.length;
        const activeG = gestures[gIdx];

        const simData = {
            rfConnected: true,
            rfSignalQuality: 92 + Math.floor(Math.sin(simTick * 0.1) * 8),
            packetsReceived: simTick * 14,
            packetsDropped: Math.floor(simTick * 0.05),
            flex: [
                activeG.id === 0 ? 12 : (activeG.id === 2 ? 8 : 85),
                activeG.id === 0 ? 15 : (activeG.id === 2 ? 78 : 12),
                activeG.id === 0 ? 10 : 82
            ],
            pitch: Math.floor(Math.sin(simTick * 0.05) * 20),
            roll: Math.floor(Math.cos(simTick * 0.05) * 15),
            tremor: 8 + Math.floor(Math.random() * 12),
            battery: 88,
            gestureId: activeG.id,
            gestureName: activeG.name,
            gestureConfidence: activeG.conf,
            temperatureC: 25.2 + (Math.sin(simTick * 0.02) * 0.5),
            humidityPercent: 54.5 + (Math.cos(simTick * 0.02) * 1.5),
            pressureHpa: 1013.4,
            altitudeMeters: 42.8,
            vocIndex: 98,
            busVoltageV: 5.05,
            currentMA: 146.2 + (Math.random() * 4),
            powerMW: 738.0,
            relayState: [false, false, false, false],
            spasmAlertActive: false
        };

        updateTelemetryUI(simData);
    }, 100);
}
