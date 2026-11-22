"""Score every method on the public sample (months after the first, all pages).

Usage: python summarize_public.py <prepared-dir> <results/public> [--loose] [--pages=1,2,3] > summary.json
Sources: method-text/<YYYYMM>-p<K>-<mode>.txt, ocr/<YYYYMM>-p<K>.txt,
ai/<YYYYMM>-p<K>-outline.<model>.<dpi>dpi-<prompt>.run<N>.json. Scored with NFKC.
"""
import glob, json, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from score_text import score, bag

prep, res = Path(sys.argv[1]), Path(sys.argv[2])
LOOSE = "--loose" in sys.argv
PAGES = next((a.split("=")[1].split(",") for a in sys.argv if a.startswith("--pages=")), None)
truth = lambda ym, k: prep / f"{ym}-p{k}-truth.json"
groups = defaultdict(list)                                # name -> [(ym, k, text, extra)]
for f in glob.glob(str(res / "method-text" / "*.txt")):
    m = re.search(r"(\d{6})-p(\d)-(\w+)\.txt$", f); groups[f"glyph-table {m[3]}"].append((m[1], m[2], open(f).read(), {}))
for f in glob.glob(str(res / "ocr" / "*.txt")):
    m = re.search(r"(\d{6})-p(\d)\.txt$", f); groups["OCRmyPDF --force-ocr (CUNY)"].append((m[1], m[2], open(f).read(), {}))
for f in glob.glob(str(res / "ai" / "*.json")):
    m = re.search(r"(\d{6})-p(\d)-outline\.([a-z0-9-]+)\.(\d+)dpi-([a-z-]+)\.run(\d)\.json$", f)
    d = json.load(open(f)); groups[f"{m[3]} run{m[6]}"].append((m[1], m[2], d["text"], {"usd": d["usd_estimate"], "sec": d["seconds"]}))
out = {}
for name, items in sorted(groups.items()):
    tot = defaultdict(int); subs = defaultdict(int); per_page = defaultdict(lambda: defaultdict(int)); usd = sec = 0
    for ym, k, text, x in items:
        if PAGES and k not in PAGES: continue
        s = score(text, truth(ym, k), nfkc=True, loose=LOOSE)
        for a, b in s["counts"].items(): tot[a] += b; per_page[k][a] += b
        for a, b in bag(text, truth(ym, k), nfkc=True, loose=LOOSE).items():
            if a != "truth_chars": tot["bag_" + a] += b
        for a, b in s["substituted"].items(): subs[a] += b
        usd += x.get("usd", 0); sec += x.get("sec", 0)
    out[name] = {"pages": sum(1 for it in items if not PAGES or it[1] in PAGES), "counts": dict(tot), "substituted_top": dict(sorted(subs.items(), key=lambda t: -t[1])[:15]),
                 "by_page": {k: dict(v) for k, v in sorted(per_page.items())}, "usd": round(usd, 3), "seconds": round(sec, 1)}
print(json.dumps(out, ensure_ascii=False, indent=1))
