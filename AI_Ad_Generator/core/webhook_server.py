import os
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from config import OUTPUTS_DIR


class WebhookReceiver:
    """A tiny local HTTP server (no extra dependencies) that receives
    completion callbacks from online providers (Pika / Luma ``webhook_url``)
    and downloads the resulting video into ``outputs/``.

    Usage:
        recv = WebhookReceiver(port=8000, log_callback=print)
        recv.start()                 # POST http://<host>:8000/
        ...
        recv.stop()
    """

    def __init__(self, port=8000, log_callback=None):
        self.port = port
        self.log_callback = log_callback
        self._httpd = None
        self._thread = None
        self.running = False

    # ------------------------------------------------------------------ #
    def _extract_video_url(self, data):
        if isinstance(data, dict):
            assets = data.get("assets")
            if isinstance(assets, dict) and assets.get("video"):
                return assets["video"]
            vid = data.get("video")
            if isinstance(vid, dict) and vid.get("url"):
                return vid["url"]
            if isinstance(vid, str):
                return vid
        return None

    def _handle(self, data):
        if self.log_callback:
            try:
                pretty = json.dumps(data)[:400]
            except Exception:
                pretty = str(data)[:400]
            self.log_callback(f"Webhook received: {pretty}")
        url = self._extract_video_url(data)
        if url:
            self._download(url)

    def _download(self, url):
        try:
            import requests
            ts = int(time.time())
            out = os.path.join(OUTPUTS_DIR, f"webhook_{ts}.mp4")
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(out, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            if self.log_callback:
                self.log_callback(f"Downloaded webhook video -> {out}")
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Webhook download error: {e}")

    # ------------------------------------------------------------------ #
    def _make_handler(self):
        receiver = self

        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0) or 0)
                body = self.rfile.read(length) if length else b"{}"
                try:
                    data = json.loads(body)
                except Exception:
                    data = {}
                receiver._handle(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"received"}')

            def log_message(self, *args):
                pass

        return _Handler

    def start(self):
        if self.running:
            return
        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer(("0.0.0.0", self.port), handler)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.running = True

    def stop(self):
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd = None
        self.running = False

    @property
    def url(self):
        return f"http://localhost:{self.port}/"
