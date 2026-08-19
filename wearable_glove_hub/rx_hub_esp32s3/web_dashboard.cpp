#include "web_dashboard.h"
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>

static WebServer server(WEB_SERVER_PORT);
static WebSocketsServer webSocket(WEBSOCKET_PORT);
static DNSServer dnsServer;

static AudioEngine*     s_audioPtr = nullptr;
static RelayController* s_relayPtr = nullptr;

// Embedded Glassmorphic Web Application (HTML + CSS + JS)
static const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Neuro Sign - Paralysis Patient Assistance HUD</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#070b14;--card:rgba(14,22,39,0.85);--border:rgba(0,242,254,0.25);--cyan:#00f2fe;--blue:#4facfe;--green:#00f298;--red:#ff3366;--amber:#ffaa00;--text:#f0f6fc;--muted:#8b9bb4;--head:'Orbitron',sans-serif;--body:'Rajdhani',sans-serif;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:var(--body);min-height:100vh;padding:16px;}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px;background:var(--card);border:1px solid var(--border);border-radius:14px;margin-bottom:16px;}
.title h1{font-family:var(--head);font-size:22px;background:linear-gradient(90deg,#00f2fe,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.title p{font-size:12px;color:var(--muted);}
.badge{background:rgba(0,242,152,0.15);border:1px solid var(--green);color:var(--green);padding:6px 12px;border-radius:8px;font-family:var(--head);font-size:12px;}
.author{font-size:12px;color:var(--green);font-weight:700;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px;}
.card-head{display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:8px;margin-bottom:12px;font-family:var(--head);font-size:14px;color:var(--cyan);}
.pill-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;text-align:center;}
.pill{background:rgba(255,255,255,0.04);padding:6px;border-radius:6px;font-size:11px;}
.pill .v{font-family:var(--head);font-size:13px;color:var(--green);display:block;margin-top:2px;}
.flex-bar{margin-bottom:8px;}
.flex-info{display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;}
.flex-track{width:100%;height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden;}
.flex-fill{height:100%;background:linear-gradient(90deg,#00f2fe,#4facfe);border-radius:4px;width:0%;transition:width 0.1s;}
.gesture-box{text-align:center;background:rgba(0,0,0,0.3);border:1px solid var(--cyan);border-radius:10px;padding:14px;margin-bottom:12px;}
.g-name{font-family:var(--head);font-size:20px;color:var(--green);margin:6px 0;}
.env-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.env-item{background:rgba(255,255,255,0.04);padding:10px;border-radius:8px;}
.env-item span{display:block;font-size:11px;color:var(--muted);}
.env-item strong{font-family:var(--head);font-size:16px;color:var(--text);}
.relay-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.btn-relay{padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.05);color:#fff;font-family:var(--head);font-size:13px;cursor:pointer;width:100%;transition:all 0.2s;}
.btn-relay.on{background:var(--green);color:#070b14;border-color:var(--green);box-shadow:0 0 12px var(--green);}
.btn-relay.danger.on{background:var(--red);color:#fff;border-color:var(--red);box-shadow:0 0 15px var(--red);}
.audio-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;}
.btn-audio{padding:8px;background:rgba(255,255,255,0.05);border:1px solid var(--border);color:var(--text);border-radius:6px;font-size:12px;cursor:pointer;}
.emergency-bar{display:none;background:linear-gradient(90deg,#ff3366,#ff6600);padding:14px 20px;border-radius:10px;margin-bottom:16px;justify-content:space-between;align-items:center;font-family:var(--head);}
.btn-ack{background:#fff;color:#cc0033;border:none;padding:8px 16px;border-radius:6px;font-weight:700;cursor:pointer;}
#tremorCanvas{width:100%;height:60px;background:#050810;border-radius:6px;margin-top:10px;}
.footer{text-align:center;font-size:11px;color:var(--muted);margin-top:20px;}
</style>
</head>
<body>
<div class="header">
  <div class="title"><h1>NEURO SIGN</h1><p>Paralysis Patient Assist & Telemetry Base Hub</p></div>
  <div><span class="author">Dev: Rudra Attri Pandey</span><br><span class="badge" id="wsBadge">HUB ONLINE (192.168.4.1)</span></div>
</div>

<div class="emergency-bar" id="alarmBar">
  <div><strong id="alarmText">PATIENT EMERGENCY ALERT ACTIVE!</strong></div>
  <button class="btn-ack" onclick="ackAlarm()">ACKNOWLEDGE / SILENCE</button>
</div>

<div class="grid">
  <!-- GLOVE TELEMETRY -->
  <div class="card">
    <div class="card-head"><span>TX GLOVE (433MHz)</span><span id="rfQual">0%</span></div>
    <div class="pill-row">
      <div class="pill">STATUS<span class="v" id="rfStat">OFFLINE</span></div>
      <div class="pill">BATTERY<span class="v" id="gBat">--%</span></div>
      <div class="pill">PITCH<span class="v" id="pitch">0°</span></div>
      <div class="pill">ROLL<span class="v" id="roll">0°</span></div>
    </div>
    <div class="flex-bar"><div class="flex-info"><span>Thumb (F1)</span><span id="f1Txt">0%</span></div><div class="flex-track"><div class="flex-fill" id="f1"></div></div></div>
    <div class="flex-bar"><div class="flex-info"><span>Index (F2)</span><span id="f2Txt">0%</span></div><div class="flex-track"><div class="flex-fill" id="f2"></div></div></div>
    <div class="flex-bar"><div class="flex-info"><span>Middle (F3)</span><span id="f3Txt">0%</span></div><div class="flex-track"><div class="flex-fill" id="f3"></div></div></div>
  </div>

  <!-- AI GESTURE -->
  <div class="card">
    <div class="card-head"><span>NEURO AI CLASSIFIER</span><span>TinyML</span></div>
    <div class="gesture-box">
      <div style="font-size:11px;color:var(--muted);">ACTIVE INTENTION</div>
      <div class="g-name" id="gName">NEUTRAL / RESTING</div>
      <div style="font-size:12px;color:var(--muted);" id="conf">Confidence: 95%</div>
    </div>
    <div style="font-size:12px;color:var(--muted);">Live Tremor Spectrum: <span id="trmVal" style="color:var(--amber);">0%</span></div>
    <canvas id="tremorCanvas" width="300" height="60"></canvas>
  </div>

  <!-- ROOM VITALS -->
  <div class="card">
    <div class="card-head"><span>ROOM VITALS & POWER</span><span>INA219 • SGP40</span></div>
    <div class="env-grid">
      <div class="env-item"><span>Temperature</span><strong id="temp">25.4 °C</strong></div>
      <div class="env-item"><span>Humidity</span><strong id="hum">54 %</strong></div>
      <div class="env-item"><span>Pressure</span><strong id="press">1013 hPa</strong></div>
      <div class="env-item"><span>VOC Air Quality</span><strong id="voc" style="color:var(--green);">95 (Clean)</strong></div>
      <div class="env-item"><span>Supply Voltage</span><strong id="vBus">5.04 V</strong></div>
      <div class="env-item"><span>Power Draw</span><strong id="pwr">740 mW</strong></div>
    </div>
  </div>

  <!-- RELAYS -->
  <div class="card">
    <div class="card-head"><span>HOME AUTOMATION</span><span>4-CH Relays</span></div>
    <div class="relay-grid">
      <button class="btn-relay" id="r0" onclick="toggleRelay(0)">💡 Light 1: OFF</button>
      <button class="btn-relay" id="r1" onclick="toggleRelay(1)">🌀 Fan: OFF</button>
      <button class="btn-relay" id="r2" onclick="toggleRelay(2)">🛏️ Bed Adjust: OFF</button>
      <button class="btn-relay danger" id="r3" onclick="toggleRelay(3)">🚨 Alarm: OFF</button>
    </div>
  </div>

  <!-- VOICE PROMPTS -->
  <div class="card">
    <div class="card-head"><span>MAX98357A I2S AUDIO</span><span>Voice E    <div class="audio-grid">
      <button class="btn-audio" onclick="playSound(3)">💧 Need Water</button>
      <button class="btn-audio" onclick="playSound(4)">🍲 Need Food</button>
      <button class="btn-audio" onclick="playSound(5)">💊 Need Medicine</button>
      <button class="btn-audio" onclick="playSound(10)">👩‍⚕️ Call Nurse</button>
      <button class="btn-audio" onclick="playSound(6)">🚨 Emergency</button>
      <button class="btn-audio" onclick="playSound(7)">💡 Light Tone</button>
      <button class="btn-audio" onclick="playSound(8)">🌀 Fan Tone</button>
      <button class="btn-audio" onclick="playSound(11)">⚠️ Pain Alert</button>
      <button class="btn-audio" onclick="playSound(12)">🌙 All Off</button>
    </div>
  </div>
</div>

<div class="footer"><p>Neuro Sign • Developed by Rudra Attri Pandey • Static IP: 192.168.4.1</p></div>

<script>
let ws, tremorBuf=new Array(50).fill(0);
function init(){
  ws=new WebSocket('ws://'+(location.hostname||'192.168.4.1')+':81/');
  ws.onmessage=(e)=>{
    try{
      let d=JSON.parse(e.data);
      document.getElementById('rfStat').innerText=d.rfConnected?'ONLINE':'OFFLINE';
      document.getElementById('rfStat').style.color=d.rfConnected?'#00f298':'#ff3366';
      document.getElementById('rfQual').innerText=(d.rfSignalQuality||0)+'%';
      document.getElementById('gBat').innerText=(d.battery||0)+'%';
      document.getElementById('pitch').innerText=(d.pitch||0)+'°';
      document.getElementById('roll').innerText=(d.roll||0)+'°';
      if(d.flex){
        document.getElementById('f1').style.width=d.flex[0]+'%'; document.getElementById('f1Txt').innerText=d.flex[0]+'%';
        document.getElementById('f2').style.width=d.flex[1]+'%'; document.getElementById('f2Txt').innerText=d.flex[1]+'%';
        document.getElementById('f3').style.width=d.flex[2]+'%'; document.getElementById('f3Txt').innerText=d.flex[2]+'%';
      }
      document.getElementById('gName').innerText=d.gestureName||'NEUTRAL';
      document.getElementById('conf').innerText='Confidence: '+Math.round((d.gestureConfidence||0.95)*100)+'%';
      document.getElementById('trmVal').innerText=(d.tremor||0)+'%';
      tremorBuf.push(d.tremor||0); tremorBuf.shift();
      drawTremor();
      document.getElementById('temp').innerText=(d.temperatureC||25).toFixed(1)+' °C';
      document.getElementById('hum').innerText=(d.humidityPercent||50).toFixed(0)+' %';
      document.getElementById('press').innerText=(d.pressureHpa||1013).toFixed(0)+' hPa';
      document.getElementById('voc').innerText=(d.vocIndex||100)+' ('+(d.vocIndex<150?'Clean':'Elevated')+')';
      document.getElementById('vBus').innerText=(d.busVoltageV||5.0).toFixed(2)+' V';
      document.getElementById('pwr').innerText=(d.powerMW||740).toFixed(0)+' mW';
      if(d.relayState){
        const names=['💡 Light 1','🌀 Fan','🛏️ Bed Adjust','🚨 Alarm'];
        for(let i=0;i<4;i++){
          let b=document.getElementById('r'+i);
          if(d.relayState[i]){b.classList.add('on'); b.innerText=names[i]+': ON';}
          else{b.classList.remove('on'); b.innerText=names[i]+': OFF';}
        }
      }
      let ab=document.getElementById('alarmBar');
      if(d.spasmAlertActive||d.gestureId===4||d.gestureId===99||d.gestureId===22){
        ab.style.display='flex';
        document.getElementById('alarmText').innerText=d.gestureId===99?'PATIENT MUSCLE SPASM DETECTED!':(d.gestureId===22?'PATIENT PAIN ALERT!':'PATIENT EMERGENCY HELP REQUESTED!');
      }
    }catch(err){}
  };
  ws.onclose=()=>setTimeout(init,2000);
}
function drawTremor(){
  let c=document.getElementById('tremorCanvas'),ctx=c.getContext('2d');
  ctx.clearRect(0,0,c.width,c.height);
  ctx.strokeStyle='#00f2fe'; ctx.lineWidth=2; ctx.beginPath();
  let step=c.width/(tremorBuf.length-1);
  for(let i=0;i<tremorBuf.length;i++){
    let y=c.height-(tremorBuf[i]/100)*(c.height-8)-4;
    if(i===0)ctx.moveTo(0,y); else ctx.lineTo(i*step,y);
  }
  ctx.stroke();
}
function toggleRelay(i){ if(ws&&ws.readyState===1) ws.send(JSON.stringify({action:'toggle_relay',index:i})); }
function playSound(id){ if(ws&&ws.readyState===1) ws.send(JSON.stringify({action:'play_sound',id:id})); }
function ackAlarm(){
  document.getElementById('alarmBar').style.display='none';
  if(ws&&ws.readyState===1) ws.send(JSON.stringify({action:'reset_alarm'}));
}
window.onload=init;
</script>
</body>
</html>
)rawliteral";

// WebSockets Event Handler
static void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    if (type == WStype_TEXT) {
        StaticJsonDocument<256> doc;
        DeserializationError err = deserializeJson(doc, payload, length);
        if (!err) {
            const char* action = doc["action"];
            if (action) {
                if (strcmp(action, "toggle_relay") == 0) {
                    uint8_t idx = doc["index"] | 0;
                    if (s_relayPtr) s_relayPtr->toggleRelay(idx);
                } else if (strcmp(action, "play_sound") == 0) {
                    uint8_t soundId = doc["id"] | 0;
                    if (s_audioPtr) s_audioPtr->playAlert((SoundAlertId)soundId);
                } else if (strcmp(action, "reset_alarm") == 0) {
                    if (s_relayPtr) s_relayPtr->triggerEmergencyAlarm(false);
                }
            }
        }
    }
}

WebDashboard::WebDashboard() :
    _audio(nullptr),
    _relays(nullptr),
    _lastWsBroadcast(0)
{
}

bool WebDashboard::begin(AudioEngine *audio, RelayController *relays) {
    _audio = audio;
    _relays = relays;
    s_audioPtr = audio;
    s_relayPtr = relays;

    setupSoftAP();
    setupHttpRoutes();

    webSocket.begin();
    webSocket.onEvent(webSocketEvent);

    return true;
}

void WebDashboard::setupSoftAP() {
    IPAddress local_ip(STATIC_IP_ADDR);
    IPAddress gateway(STATIC_IP_GATEWAY);
    IPAddress subnet(STATIC_IP_SUBNET);

    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(local_ip, gateway, subnet);
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS);

    // Setup DNS Server for Captive Portal (Redirect * to 192.168.4.1)
    dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
    dnsServer.start(53, "*", local_ip);
}

void WebDashboard::setupHttpRoutes() {
    // Root Dashboard
    server.on("/", HTTP_GET, []() {
        server.send_P(200, "text/html", INDEX_HTML);
    });

    // Captive portal redirects
    server.on("/generate_204", HTTP_GET, []() { server.send_P(200, "text/html", INDEX_HTML); });
    server.on("/hotspot-detect.html", HTTP_GET, []() { server.send_P(200, "text/html", INDEX_HTML); });
    server.on("/canonical.html", HTTP_GET, []() { server.send_P(200, "text/html", INDEX_HTML); });

    // REST API Endpoints
    server.on("/api/relay", HTTP_POST, [this]() {
        if (server.hasArg("plain")) {
            StaticJsonDocument<128> doc;
            deserializeJson(doc, server.arg("plain"));
            uint8_t idx = doc["index"] | 0;
            if (_relays) _relays->toggleRelay(idx);
            server.send(200, "application/json", "{\"status\":\"ok\"}");
        } else {
            server.send(400, "application/json", "{\"error\":\"bad_request\"}");
        }
    });

    server.on("/api/alert", HTTP_POST, [this]() {
        if (server.hasArg("plain")) {
            StaticJsonDocument<128> doc;
            deserializeJson(doc, server.arg("plain"));
            uint8_t soundId = doc["id"] | 0;
            if (_audio) _audio->playAlert((SoundAlertId)soundId);
            server.send(200, "application/json", "{\"status\":\"ok\"}");
        } else {
            server.send(400, "application/json", "{\"error\":\"bad_request\"}");
        }
    });

    server.onNotFound([]() {
        server.send_P(200, "text/html", INDEX_HTML);
    });

    server.begin();
}

void WebDashboard::broadcastTelemetry(const SystemTelemetry &telemetry) {
    StaticJsonDocument<512> doc;
    doc["rfConnected"]       = telemetry.rfConnected;
    doc["rfSignalQuality"]   = telemetry.rfSignalQuality;
    doc["packetsReceived"]   = telemetry.packetsReceived;
    doc["packetsDropped"]    = telemetry.packetsDropped;

    JsonArray flexArr = doc.createNestedArray("flex");
    flexArr.add(telemetry.flex[0]);
    flexArr.add(telemetry.flex[1]);
    flexArr.add(telemetry.flex[2]);

    doc["pitch"]             = telemetry.pitch;
    doc["roll"]              = telemetry.roll;
    doc["tremor"]            = telemetry.tremor;
    doc["battery"]           = telemetry.battery;
    doc["gestureId"]         = telemetry.gestureId;
    doc["gestureName"]       = telemetry.gestureName;
    doc["gestureConfidence"] = telemetry.gestureConfidence;

    doc["temperatureC"]      = telemetry.temperatureC;
    doc["humidityPercent"]   = telemetry.humidityPercent;
    doc["pressureHpa"]       = telemetry.pressureHpa;
    doc["vocIndex"]          = telemetry.vocIndex;

    doc["busVoltageV"]       = telemetry.busVoltageV;
    doc["currentMA"]         = telemetry.currentMA;
    doc["powerMW"]           = telemetry.powerMW;

    JsonArray relayArr = doc.createNestedArray("relayState");
    for (int i = 0; i < 4; i++) {
        relayArr.add(telemetry.relayState[i]);
    }

    doc["spasmAlertActive"]  = telemetry.spasmAlertActive;

    String jsonString;
    serializeJson(doc, jsonString);
    webSocket.broadcastTXT(jsonString);
}

void WebDashboard::update(const SystemTelemetry &telemetry) {
    dnsServer.processNextRequest();
    server.handleClient();
    webSocket.loop();

    uint32_t now = millis();
    if (now - _lastWsBroadcast >= WS_BROADCAST_RATE_MS) {
        _lastWsBroadcast = now;
        broadcastTelemetry(telemetry);
    }
}

void WebDashboard::handleClient() {
    dnsServer.processNextRequest();
    server.handleClient();
    webSocket.loop();
}
