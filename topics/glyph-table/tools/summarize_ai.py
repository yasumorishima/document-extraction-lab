"""Summarise generative-AI transcriptions against the truth (months 2-12 unless told otherwise).

Usage: python summarize_ai.py <results-dir> <truth-dir> [--from=2] > summary.json
Groups replies by (condition, model, prompt, dpi); per group: totals over runs,
pages with at least one silent error, and whether the runs agree page by page.
Japanese conditions (prefix "ja") are scored with NFKC (full/half width equal).
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from score_text import score

res_dir, truth_dir = Path(sys.argv[1]), Path(sys.argv[2])
first = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--from=")), 2))
pat = re.compile(r"(?P<cond>.+)-statement-2026-(?P<m>\d\d)\.(?P<model>[a-z0-9-]+)\.(?P<dpi>\d+)dpi-(?P<prompt>[a-z-]+)\.run(?P<run>\d+)\.json")
groups = defaultdict(lambda: defaultdict(dict))
for f in sorted(res_dir.rglob("*.json")):
    mt = pat.fullmatch(f.name)
    if not mt or int(mt["m"]) < first: continue
    g = (mt["cond"], mt["model"], mt["prompt"], mt["dpi"])
    groups[g][int(mt["m"])][int(mt["run"])] = json.load(open(f))
out = {}
for (cond, model, prompt, dpi), months in sorted(groups.items()):
    nfkc = cond.startswith("ja")
    runs = sorted({r for m in months.values() for r in m})
    tot = {r: defaultdict(int) for r in runs}; subs = defaultdict(int); bad_pages = {r: 0 for r in runs}
    usd = secs = calls = 0; agree = 0; pages = 0; stops = defaultdict(int)
    for m, byrun in months.items():
        texts = []
        for r, rec in byrun.items():
            s = score(rec["text"], truth_dir / f"{cond}-truth-2026-{m:02d}.json", nfkc)
            for k, v in s["counts"].items(): tot[r][k] += v
            for k, v in s["substituted"].items(): subs[k] += v
            if s["counts"].get("substituted", 0) or s["counts"].get("extra", 0): bad_pages[r] += 1
            usd += rec["usd_estimate"]; secs += rec["seconds"]; calls += 1; stops[rec["stop_reason"]] += 1
            texts.append(rec["text"].strip())
        pages += 1; agree += len(set(texts)) == 1
    key = f"{cond} | {model} | {prompt} | {dpi}dpi"
    out[key] = {"runs": len(runs), "months": len(months),
                "per_run": {r: {k: tot[r][k] for k in ("truth_chars", "correct", "substituted", "unassigned", "missing", "extra")} for r in runs},
                "pages_with_silent_error_per_run": bad_pages,
                "pages_where_all_runs_identical": f"{agree}/{pages}" if len(runs) > 1 else None,
                "top_substitutions_all_runs": dict(sorted(subs.items(), key=lambda x: -x[1])[:10]),
                "usd": round(usd, 3), "usd_per_page": round(usd / calls, 4), "seconds_per_page": round(secs / calls, 1),
                "stop_reasons": dict(stops), "nfkc": nfkc}
print(json.dumps(out, ensure_ascii=False, indent=1))
