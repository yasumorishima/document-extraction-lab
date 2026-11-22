"""Ask Claude to transcribe a rendered page image; save every raw response.

Usage: python run_claude_vision.py <pdf> <out-dir> <run-id> [dpi] [prompt]
  prompt: "plain" (default), "lookalike" (adds a warning about 0/O and 1/l/I)
          or "lookalike-ja" (the Japanese look-alikes used in the Japanese sample)
Key: SCOREBOOK_API_KEY (or ANTHROPIC_API_KEY). Replies already on disk are skipped.
The page is rendered with `pdftoppm -r 150` (1240 x 1754 px for A4).
"""
import base64, json, os, subprocess, sys, tempfile, time
from pathlib import Path
import anthropic
sys.path.insert(0, str(Path(__file__).parent))

MODEL = "claude-opus-5-5"
from run_claude_vision_prompts import PROMPTS

pdf, out, run = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 150
pname = sys.argv[5] if len(sys.argv) > 5 else "plain"
PROMPT = PROMPTS[pname]
out.mkdir(parents=True, exist_ok=True)
tag = "" if (dpi, pname) == (150, "plain") else f".{dpi}dpi-{pname}"
dest = out / f"{pdf.stem}{tag}.run{run}.json"
if dest.exists(): print("skip", dest); sys.exit()
with tempfile.TemporaryDirectory() as td:
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", str(pdf), f"{td}/p"], check=True)
    img = base64.standard_b64encode(open(f"{td}/p.png", "rb").read()).decode()
client = anthropic.Anthropic(api_key=os.environ.get("SCOREBOOK_API_KEY") or os.environ["ANTHROPIC_API_KEY"])
t0 = time.time()
r = client.beta.messages.create(
    model=MODEL, max_tokens=16000,
    thinking={"type": "adaptive"}, output_config={"effort": "high"},
    betas=["server-side-fallback-2026-07-01"], fallbacks="default",
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
        {"type": "text", "text": PROMPT}]}],
)
sec = round(time.time() - t0, 1)
text = "".join(b.text for b in r.content if b.type == "text")
u = r.usage
cost = (u.input_tokens * 4 + u.output_tokens * 20) / 1e6   # USD, Opus 5.5 list price
rec = {"dpi": dpi, "prompt_variant": pname, "model_requested": MODEL, "model_served": r.model, "stop_reason": r.stop_reason,
       "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
       "usd_estimate": round(cost, 4), "seconds": sec, "prompt": PROMPT, "text": text}
dest.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rec.items() if k not in ("prompt", "text")}))
