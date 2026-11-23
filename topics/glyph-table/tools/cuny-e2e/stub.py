import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
LOG = open(sys.argv[2], "a")
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps({"data":[{"id":"stub"}]}).encode())
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(n)
        try:
            d = json.loads(body); msgs = d.get("messages", [])
            imgs = sum(1 for m in msgs if isinstance(m.get("content"), list) for c in m["content"] if c.get("type") == "image_url")
            def txt(m):
                c = m.get("content")
                return c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            sysmsg = " | ".join(txt(m)[:150] for m in msgs)
        except Exception: d, imgs, sysmsg = {}, -1, ""
        LOG.write(json.dumps({"t": time.time(), "path": self.path, "bytes": n, "images": imgs, "system": sysmsg}) + "\n"); LOG.flush()
        self.send_response(500); self.end_headers(); self.wfile.write(b'{"error":"stub"}')
ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
