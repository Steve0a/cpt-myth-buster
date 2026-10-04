"""Tiny API for the grounded Gemini fallback (item 3). Standard library only.
Run: GEMINI_API_KEY=... python backend/server.py   (port 8787)
"""
import json, os, time, collections
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from gemini_core import ask

KEY = os.environ.get("GEMINI_API_KEY")  # optional when a proxy injects the key
HITS = collections.defaultdict(list)
LIMIT = 20  # questions per IP per hour

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_OPTIONS(self): self._send(204, {})
    def do_GET(self): self._send(200, {"ok": True})

    def do_POST(self):
        if self.path.rstrip("/") != "/api/ask":
            return self._send(404, {"error": "not found"})
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0]
        now = time.time(); HITS[ip] = [t for t in HITS[ip] if now - t < 3600]
        if len(HITS[ip]) >= LIMIT:
            return self._send(429, {"status": "rate_limited"})
        HITS[ip].append(now)
        try:
            q = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}").get("question", "").strip()[:500]
            if len(q) < 3:
                return self._send(400, {"status": "bad_request"})
            self._send(200, ask(q, KEY))
        except Exception as e:
            self._send(500, {"status": "error", "detail": str(e)[:200]})

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8787))), H).serve_forever()
