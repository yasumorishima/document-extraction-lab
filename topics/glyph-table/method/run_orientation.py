"""Turned pages read with the upright table, with orientation detection and page hold
(results/preregistration-orientation-2026-11.md).

The table and threshold come from the upright month 1, exactly as run_method.py.
Months 2-12 are turned by each angle (run_rotated.turned: the drawing wrapped in a
rotation `cm`) and read with read_page.read (orientation detection on), first_only.
Scoring as run_method.py (tools/score_text.score, in reading order). A held page
goes to a person whole, so its errors are not silent: errors are also summed over
pages that were not held.

Usage: python run_orientation.py <gen-dir> <prefix> <months> <out.json> <angles...> [--vertical]
"""
import json, sys, tempfile, time
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here)); sys.path.insert(0, str(here.parent / "tools"))
import glyphs, read_page, pick_threshold
from run_rotated import turned
from score_text import score

VERTICAL = "--vertical" in sys.argv
args = [a for a in sys.argv if not a.startswith("--")]
gen, prefix, n, out = Path(args[1]), args[2], int(args[3]), Path(args[4])
angles = [float(a) for a in args[5:]]
months = [f"2026-{m:02d}" for m in range(1, n + 1)]
pdf = lambda m: gen / f"{prefix}-statement-{m}.pdf"
truth = lambda m: gen / f"{prefix}-truth-{m}.json"
th, det = pick_threshold.pick(pdf(months[0]), truth(months[0]))
table = read_page.build(pdf(months[0]), truth(months[0]), th)
res = {"prefix": prefix, "threshold": det, "hold_above": read_page.HOLD, "months_read": months[1:]}
tmp = Path(tempfile.mkdtemp())
KEYS = ("correct", "substituted", "extra", "missing", "unassigned")
for deg in angles:
    t0 = time.time()
    tot = dict.fromkeys(KEYS, 0); free = {"substituted": 0, "extra": 0}; held = []; turns = {}; shares = []
    for m in months[1:]:
        p = pdf(m) if deg == 0 else turned(pdf(m), deg, tmp / f"{prefix}-{deg:g}-{m}.pdf")
        info = {}
        text, _ = read_page.read(p, table, th, vertical=VERTICAL, info=info)
        c = score(text, truth(m))["counts"]
        for k in KEYS: tot[k] += c.get(k, 0)
        if info["held"]: held.append(m)
        else:
            for k in free: free[k] += c.get(k, 0)
        turns[info["turn"]] = turns.get(info["turn"], 0) + 1; shares.append(info["unknown_share"])
    res[f"{deg:g} deg"] = {"counts": tot, "errors_on_pages_not_held": free, "held_pages": held,
                           "turn_chosen": turns, "unknown_share_min_max": [min(shares), max(shares)],
                           "seconds": round(time.time() - t0, 1)}
    print(f"{prefix} {deg:g}: {tot} held {len(held)} not-held errors {free} turns {turns}", file=sys.stderr, flush=True)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
