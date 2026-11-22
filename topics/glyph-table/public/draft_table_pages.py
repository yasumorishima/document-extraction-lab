"""AI draft of a large glyph table built from several pages (the public sample).

Builds the first month's table exactly as run_pages.py does, remembers which page
each group's representative came from, and asks a model to name the glyph of
every group, in sheets of SHEET groups (at most MAXSIDE px a side) shown in their printed line ("context"
style, as tools/draft_table_with_claude.py). Answers are compared with the
characters the table holds (NFKC: width forms count as the same).
Usage: python draft_table_pages.py <prepared-dir> <first-month YYYYMM> <model> <out.json>
"""
import base64, io, json, os, re, glob, subprocess, sys, tempfile, time, unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import anthropic
here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "method"))
import glyphs, read_page

SHEET = 45
STRIP_H = 90     # every strip is scaled to this height, so a big title glyph does not blow up a sheet
FONT = ImageFont.load_default(size=26)
MAXSIDE = 4000   # the API refuses images with a side over 8000 px; it downsizes large ones anyway
PRICE = {"claude-opus-5-5": (4, 20), "claude-sonnet-5-5": (2, 10), "claude-haiku-5-5": (0.10, 0.50), "claude-fable-5-2": (8, 40)}
d, ym, model, dest = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
pages = sorted(glob.glob(str(d / f"{ym}-p*-outline.pdf")), key=lambda p: int(re.search(r"-p(\d+)-", p)[1]))
res = json.load(open(here.parent / "results/public/method-jinsui.json"))
th = res["threshold"]["value"]; glyphs.SIZE_TOL = res["threshold"]["size_tol_px"]
table, origin = None, []
for pi, pdf in enumerate(pages):
    before = 0 if table is None else len(table)
    table = read_page.build(pdf, pdf.replace("-outline.pdf", "-truth.json"), th, table)
    origin += [pi] * (len(table) - before)
DPI = 300; k = DPI / 72
imgs, allg = [], []
with tempfile.TemporaryDirectory() as td:
    for pi, pdf in enumerate(pages):
        subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", pdf, f"{td}/p{pi}"], check=True)
        imgs.append(Image.open(f"{td}/p{pi}.png").convert("RGB")); allg.append(glyphs.page_glyphs(pdf))
def strip(i):
    b = table[i][0]; img = imgs[origin[i]]; H = img.height
    x0, y0, x1, y1 = b[:4]; yc = (y0 + y1) / 2
    row = [g for g in allg[origin[i]] if abs((g[1] + g[3]) / 2 - yc) < 4 or g[1] <= yc <= g[3]]
    top = max([g[3] for g in row] + [y1]) + 1; bot = min([g[1] for g in row] + [y0]) - 1
    hgt = top - bot; L = max(0, x0 - 2.5 * hgt); R = x1 + 2.5 * hgt
    c = img.crop((int(L * k), int(H - top * k), int(R * k), int(H - bot * k)))
    ImageDraw.Draw(c).rectangle((int((x0 - L) * k) - 3, int((top - y1) * k) - 3, int((x1 - L) * k) + 3, int((top - y0) * k) + 3), outline=(220, 0, 0), width=2)
    return c
client = anthropic.Anthropic(api_key=os.environ.get("SCOREBOOK_API_KEY") or os.environ["ANTHROPIC_API_KEY"], max_retries=6)
def ask(ids):
    crops = [strip(i) for i in ids]
    crops = [c.resize((max(1, int(c.width * STRIP_H / c.height)), STRIP_H), Image.LANCZOS) for c in crops]
    cw = max(c.width for c in crops) + 90; ch = STRIP_H + 16; cols = 3
    sheet = Image.new("RGB", (cols * cw, ((len(crops) + cols - 1) // cols) * ch), "white"); dr = ImageDraw.Draw(sheet)
    for n, (i, c) in enumerate(zip(ids, crops)):
        cx, cy = (n % cols) * cw, (n // cols) * ch
        dr.text((cx + 4, cy + (ch - 26) // 2), str(i), fill=(0, 0, 0), font=FONT); sheet.paste(c, (cx + 80, cy + 8))
        dr.rectangle((cx, cy, cx + cw - 1, cy + ch - 1), outline=(180, 180, 180))
    if max(sheet.size) > MAXSIDE:
        f = MAXSIDE / max(sheet.size); sheet = sheet.resize((int(sheet.width * f), int(sheet.height * f)), Image.LANCZOS)
    buf = io.BytesIO(); sheet.save(buf, "PNG")
    prompt = (f"This sheet shows {len(ids)} numbered strips cut from a Japanese government statistics report "
              "(Japanese, English and digits; Mincho and Gothic typefaces, some italic). Each strip is a piece of one printed "
              "line; the glyph to identify is inside the red box, with its neighbours for context. Judge only the glyph in the "
              "red box. Give the single character it is, keeping full-width and half-width forms as printed. "
              'If you cannot tell, give "?". Answer with JSON only: {"<number>": "<character>", ...}')
    kw = dict(model=model, max_tokens=16000, output_config={"effort": "high"}, messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.standard_b64encode(buf.getvalue()).decode()}},
        {"type": "text", "text": prompt}]}])
    if model != "claude-fable-5-2": kw["thinking"] = {"type": "adaptive"}
    if model != "claude-haiku-5-5": kw["betas"] = ["server-side-fallback-2026-07-01"]; kw["fallbacks"] = "default"
    t0 = time.time(); r = client.beta.messages.create(**kw) if "betas" in kw else client.messages.create(**kw)
    text = "".join(b.text for b in r.content if b.type == "text")
    try: ans = json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception: ans = {}
    u = r.usage
    return ans, (u.input_tokens * PRICE[model][0] + u.output_tokens * PRICE[model][1]) / 1e6, time.time() - t0
FAILED = []
def ask_safe(ids):
    for attempt in (1, 2):
        try: return ask(ids)
        except anthropic.BadRequestError as e:             # seen with one sheet on Opus: "Invalid request data"
            print(f"sheet {ids[0]}-{ids[-1]} attempt {attempt}: {e}", file=sys.stderr)
    FAILED.append([ids[0], ids[-1]]); return {}, 0.0, 0.0

def ask_checked(ids):
    """Ask for one sheet; if the reply cannot be read or misses numbers of the sheet, ask once more."""
    ask = ask_safe
    ans, c, s = ask(ids)
    if sum(str(i) in ans for i in ids) < len(ids):
        ans2, c2, s2 = ask(ids); c += c2; s += s2
        if sum(str(i) in ans2 for i in ids) > sum(str(i) in ans for i in ids): ans = ans2
    return {k: v for k, v in ans.items() if k in {str(i) for i in ids}}, c, s
ids = list(range(len(table))); chunks = [ids[i:i + SHEET] for i in range(0, len(ids), SHEET)]
answers, usd, secs = {}, 0.0, 0.0
with ThreadPoolExecutor(4) as ex:
    for ans, c, s in ex.map(ask_checked, chunks): answers.update(ans); usd += c; secs += s
nf = lambda x: unicodedata.normalize("NFKC", x)
truth = {str(i): e[1] for i, e in enumerate(table)}
wrong = {i: f"{truth[i]}->{answers.get(i)}" for i in truth if truth[i] != "?" and answers.get(i) not in (None, "?") and nf(answers[i]) != nf(truth[i])}
rec = {"model": model, "groups": len(table), "sheets": len(chunks), "failed_sheets": FAILED, "answered": sum(1 for i in truth if i in answers),
       "right": sum(1 for i in truth if i in answers and truth[i] != "?" and nf(answers[i]) == nf(truth[i])),
       "unsure": sum(1 for i in truth if answers.get(i) == "?"), "missing_answers": sum(1 for i in truth if i not in answers),
       "wrong": wrong, "usd_estimate": round(usd, 4), "seconds_total": round(secs, 1), "answer": answers}
dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in rec.items() if k not in ("answer", "wrong")} | {"n_wrong": len(wrong)}, ensure_ascii=False))
