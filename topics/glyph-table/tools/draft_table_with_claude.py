"""Ask Claude to draft the glyph table: one sheet with every group's representative.

Each representative is cut from the page rendered at 300 dpi (same scale for all,
bottom-aligned in its cell, so relative heights stay visible), numbered, and
sent as one image. Claude answers {"id": "character"}; "?" if unsure.
Usage: python draft_table_with_claude.py <gen-dir> <out.json> [prefix] [language hint] [model] [sheet]
sheet: "cells" (default; each representative alone, bottom-aligned) or
       "context" (each representative in its printed line with its neighbours,
       inside a red box, so height on the line and the surrounding word show).
The threshold and size tolerance are picked from month 1 (method/pick_threshold.py), as in run_method.py.
"""
import base64, io, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image, ImageDraw
import anthropic
here = Path(__file__).parent; sys.path.insert(0, str(here.parent / "method"))
import read_page, glyphs

import pick_threshold
gen, dest = Path(sys.argv[1]), Path(sys.argv[2])
prefix = sys.argv[3] if len(sys.argv) > 3 else "outline"
hint = sys.argv[4] if len(sys.argv) > 4 else "an English business statement in one sans-serif typeface"
pdf = gen / f"{prefix}-statement-2026-01.pdf"
th, _ = pick_threshold.pick(pdf, gen / f"{prefix}-truth-2026-01.json")
MODEL = sys.argv[5] if len(sys.argv) > 5 else "claude-opus-5-5"
SHEET = sys.argv[6] if len(sys.argv) > 6 else "cells"
PRICE = {"claude-opus-5-5": (4, 20), "claude-sonnet-5-5": (2, 10), "claude-haiku-5-5": (0.10, 0.50), "claude-fable-5-2": (8, 40)}
table = read_page.build(pdf, gen / f"{prefix}-truth-2026-01.json", th)
DPI = 300; k = DPI / 72
with tempfile.TemporaryDirectory() as td:
    subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", str(pdf), f"{td}/p"], check=True)
    page = Image.open(f"{td}/p.png").convert("L")
H = page.height
crops = []
if SHEET == "context":
    # the line band of each representative: all glyphs of the page whose vertical centre is near its own
    allg = glyphs.page_glyphs(pdf)
    for b, *_ in table:
        x0, y0, x1, y1 = b[:4]; yc = (y0 + y1) / 2
        row = [g for g in allg if abs((g[1] + g[3]) / 2 - yc) < 6 or (g[1] <= yc <= g[3])]
        top = max(g[3] for g in row) + 1; bot = min(g[1] for g in row) - 1
        hgt = top - bot; L = max(0, x0 - 2.5 * hgt); R = x1 + 2.5 * hgt
        c = page.crop((int(L * k), int(H - top * k), int(R * k), int(H - bot * k))).convert("RGB")
        ImageDraw.Draw(c).rectangle((int((x0 - L) * k) - 3, int((top - y1) * k) - 3, int((x1 - L) * k) + 3, int((top - y0) * k) + 3), outline=(220, 0, 0), width=2)
        crops.append(c)
else:
    for b, *_ in table:
        x0, y0, x1, y1 = b[:4]
        crops.append(page.crop((int(x0 * k) - 2, int(H - y1 * k) - 2, int(x1 * k) + 3, int(H - y0 * k) + 3)))
cw = max(c.width for c in crops) + 20; ch = max(c.height for c in crops) + 40
cols = 10 if SHEET == "cells" else 4; rows = (len(crops) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cw, rows * ch), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for i, c in enumerate(crops):
    cx, cy = (i % cols) * cw, (i // cols) * ch
    d.text((cx + 4, cy + 2), str(i), fill=(0, 0, 0))
    sheet.paste(c, (cx + 10, cy + ch - c.height - 6))
    d.rectangle((cx, cy, cx + cw - 1, cy + ch - 1), outline=(180, 180, 180))
buf = io.BytesIO(); sheet.save(buf, "PNG"); sheet.save(dest.with_suffix(".png"))
prompt = ((f"This sheet shows {len(crops)} numbered glyphs cut from one printed page, all at the same scale "
          "and bottom-aligned in their cells (so relative size and height are meaningful). The page is ") if SHEET == "cells" else
          (f"This sheet shows {len(crops)} numbered strips cut from one printed page, all at the same scale. Each strip is "
           "a piece of one printed line; the glyph to identify is inside the red box, with its neighbours left and right "
           "for context. Judge only the glyph in the red box. The page is "))
prompt = (prompt + 
          f"{hint}; glyphs come in a few sizes. For each number, "
          "give the single character the glyph is. If you cannot tell, give \"?\". Answer with JSON only: "
          '{"0": "M", "1": "O", ...}')
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
t0 = time.time()
kw = dict(model=MODEL, max_tokens=16000, output_config={"effort": "high"},
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.standard_b64encode(buf.getvalue()).decode()}},
        {"type": "text", "text": prompt}]}])
if MODEL != "claude-fable-5-2": kw["thinking"] = {"type": "adaptive"}          # Fable: thinking is always on
if MODEL != "claude-haiku-5-5":                                                # Haiku has no server-side fallback
    kw["betas"] = ["server-side-fallback-2026-07-01"]; kw["fallbacks"] = "default"
r = client.beta.messages.create(**kw) if "betas" in kw else client.messages.create(**kw)
text = "".join(b.text for b in r.content if b.type == "text")
u = r.usage
ans = json.loads(text[text.find("{"): text.rfind("}") + 1])
truth = {str(i): e[1] for i, e in enumerate(table)}
right = [i for i in truth if ans.get(i) == truth[i]]
unsure = [i for i in truth if ans.get(i) == "?"]
wrong = {i: f"{truth[i]}->{ans.get(i)}" for i in truth if ans.get(i) not in (truth[i], "?")}
rec = {"model_requested": MODEL, "model_served": r.model, "stop_reason": r.stop_reason, "input_tokens": u.input_tokens,
       "output_tokens": u.output_tokens, "usd_estimate": round((u.input_tokens * PRICE[MODEL][0] + u.output_tokens * PRICE[MODEL][1]) / 1e6, 4),
       "seconds": round(time.time() - t0, 1), "groups": len(table), "right": len(right), "unsure": len(unsure),
       "wrong": wrong, "answer": ans, "prompt": prompt}
dest.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rec.items() if k not in ("answer", "prompt")}, ensure_ascii=False))
