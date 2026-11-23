"""Local OpenAI-style /v1/chat/completions endpoint that forwards to the Claude Messages API.
Usage: adapter.py <port> <model> <log.jsonl> <cap-usd> [effort]
Key from SCOREBOOK_API_KEY (never printed). Stops answering (HTTP 503) once the logged spend reaches the cap.
"""
import json, os, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import anthropic
PORT, MODEL, LOG, CAP = int(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4])
EFFORT = sys.argv[5] if len(sys.argv) > 5 else None
PRICE = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0)}[MODEL]
client = anthropic.Anthropic(api_key=os.environ["SCOREBOOK_API_KEY"], max_retries=3)
lock = threading.Lock()
spent = sum(json.loads(l).get("usd", 0) for l in open(LOG)) if os.path.exists(LOG) else 0.0

def block(c):
    t = c.get("type")
    if t == "text": return {"type": "text", "text": c.get("text", "")}
    if t == "image_url":
        url = c["image_url"]["url"]; head, data = url.split(",", 1)
        return {"type": "image", "source": {"type": "base64", "media_type": head[5:].split(";")[0], "data": data}}
    raise ValueError(f"unsupported content type {t}")

def convert(msgs):
    system, out = [], []
    for m in msgs:
        c = m.get("content"); parts = [{"type": "text", "text": c}] if isinstance(c, str) else [block(x) for x in c]
        if m["role"] == "system": system += [p["text"] for p in parts if p["type"] == "text"]; continue
        if out and out[-1]["role"] == m["role"]: out[-1]["content"] += parts
        else: out.append({"role": m["role"], "content": parts})
    return "\n\n".join(system), out

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self): self.reply(200, {"data": [{"id": MODEL}]})
    def do_POST(self):
        global spent
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        with lock:
            if spent >= CAP: return self.reply(503, {"error": {"message": "budget cap reached"}})
        system, msgs = convert(d["messages"])
        kw = dict(model=MODEL, max_tokens=int(d.get("max_tokens") or 4096), messages=msgs)
        if system: kw["system"] = system
        if EFFORT: kw["output_config"] = {"effort": EFFORT}
        t0 = time.time()
        try: r = client.messages.create(**kw)
        except anthropic.APIStatusError as e: return self.reply(e.status_code, {"error": {"message": str(e)[:300]}})
        u = r.usage; cin = (u.input_tokens + 1.25 * (u.cache_creation_input_tokens or 0) + 0.1 * (u.cache_read_input_tokens or 0))
        usd = (cin * PRICE[0] + u.output_tokens * PRICE[1]) / 1e6
        text = "".join(b.text for b in r.content if b.type == "text")
        prompt_head = " | ".join((p["text"] if p["type"] == "text" else "[img]")[:100] for m in msgs for p in m["content"])[:400]
        with lock:
            spent += usd
            open(LOG, "a").write(json.dumps({"t": t0, "sec": round(time.time() - t0, 1), "model": MODEL, "in": u.input_tokens, "out": u.output_tokens,
                "cache_w": u.cache_creation_input_tokens, "cache_r": u.cache_read_input_tokens, "usd": usd, "stop": r.stop_reason,
                "prompt": prompt_head, "answer": text[:2000]}, ensure_ascii=False) + "\n")
        fin = {"end_turn": "stop", "max_tokens": "length"}.get(r.stop_reason, "stop")
        self.reply(200, {"id": r.id, "object": "chat.completion", "model": MODEL,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": fin}],
            "usage": {"prompt_tokens": u.input_tokens, "completion_tokens": u.output_tokens, "total_tokens": u.input_tokens + u.output_tokens}})
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
