"""Transcribe many pages with Claude models in parallel; one JSON per reply.

Jobs come from a JSON list: [{"pdf": ..., "out": ..., "model": ..., "prompt": ..., "dpi": 150, "run": 1}, ...]
Replies already on disk are skipped, so the batch can be re-run after a failure.
Usage: python ai_batch.py <jobs.json> [workers]
Key: SCOREBOOK_API_KEY (or ANTHROPIC_API_KEY).
"""
import base64, json, os, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import anthropic
sys.path.insert(0, str(Path(__file__).parent))
from run_claude_vision_prompts import PROMPTS

PRICE = {"claude-opus-5-5": (4, 20), "claude-sonnet-5-5": (2, 10), "claude-haiku-5-5": (0.10, 0.50),
         "claude-fable-5-2": (8, 40)}                       # USD per 1M tokens (input, output), list price
client = anthropic.Anthropic(api_key=os.environ.get("SCOREBOOK_API_KEY") or os.environ["ANTHROPIC_API_KEY"], max_retries=6)

def dest_of(job):
    pdf = Path(job["pdf"]); m = job["model"].replace("claude-", "")
    return Path(job["out"]) / f"{pdf.stem}.{m}.{job.get('dpi', 150)}dpi-{job['prompt']}.run{job.get('run', 1)}.json"

def image(pdf, dpi):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", str(pdf), f"{td}/p"], check=True)
        return base64.standard_b64encode(open(f"{td}/p.png", "rb").read()).decode()

def run(job):
    dest = dest_of(job)
    if dest.exists(): return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    model, dpi, prompt = job["model"], job.get("dpi", 150), PROMPTS[job["prompt"]]
    kw = dict(model=model, max_tokens=16000, output_config={"effort": "high"},
              messages=[{"role": "user", "content": [
                  {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image(job["pdf"], dpi)}},
                  {"type": "text", "text": prompt}]}])
    if model != "claude-fable-5-2": kw["thinking"] = {"type": "adaptive"}       # Fable: thinking is always on
    if model != "claude-haiku-5-5":                                             # Haiku has no server-side fallback
        kw["betas"] = ["server-side-fallback-2026-07-01"]; kw["fallbacks"] = "default"
    t0 = time.time()
    r = client.beta.messages.create(**kw) if "betas" in kw else client.messages.create(**kw)
    text = "".join(b.text for b in r.content if b.type == "text")
    u = r.usage; pi, po = PRICE[model]
    rec = {"dpi": dpi, "prompt_variant": job["prompt"], "model_requested": model, "model_served": r.model,
           "stop_reason": r.stop_reason, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
           "usd_estimate": round((u.input_tokens * pi + u.output_tokens * po) / 1e6, 4),
           "seconds": round(time.time() - t0, 1), "prompt": prompt, "text": text}
    dest.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    return f"{rec['usd_estimate']}"

def safe(job):
    try: return job, run(job), None
    except Exception as e: return job, None, f"{type(e).__name__}: {e}"

if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1])); workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    done = skipped = 0; cost = 0.0; errors = []
    with ThreadPoolExecutor(workers) as ex:
        for job, res, err in ex.map(safe, jobs):
            if err: errors.append((str(dest_of(job)), err))
            elif res == "skip": skipped += 1
            else: done += 1; cost += float(res)
    print(json.dumps({"jobs": len(jobs), "done": done, "skipped": skipped, "usd_this_batch": round(cost, 3), "errors": errors[:10], "n_errors": len(errors)}, indent=1))
