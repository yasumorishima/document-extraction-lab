"""Glyph-table method end to end, scored with tools/score_text.py.

Month 1 builds the table (characters confirmed by a person = truth by position).
The threshold is picked from month 1 alone (pick_threshold.py) unless given.
first_only: every later month is read with the month-1 table.
cumulative: after each month, the shapes it reported as new ("?") are confirmed
            by a person and added before the next month.
Usage: python run_method.py <gen-dir> <pdf-prefix> <months> <out-dir> [threshold] [--vertical]
       --vertical: the pages are written vertically (read columns right to left)
       pdf-prefix e.g. "outline", "outline-merged", "gs-outline"; truth files are <prefix>-truth-YYYY-MM.json
"""
import json, sys, time
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here)); sys.path.insert(0, str(here.parent / "tools"))
import read_page, glyphs, pick_threshold
from score_text import score

VERTICAL = "--vertical" in sys.argv; sys.argv = [a for a in sys.argv if a != "--vertical"]
gen, prefix, n, out = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
months = [f"2026-{m:02d}" for m in range(1, n + 1)]
pdf = lambda m: gen / f"{prefix}-statement-{m}.pdf"
truth = lambda m: gen / f"{prefix}-truth-{m}.json"
res = {"prefix": prefix}
th, detail = pick_threshold.pick(pdf(months[0]), truth(months[0])); res["threshold"] = detail
if len(sys.argv) > 5: th = float(sys.argv[5]); res["threshold"]["given"] = th
t0 = time.time(); table = read_page.build(pdf(months[0]), truth(months[0]), th)
res["table"] = {"groups": len(table), "thin_groups(<3)": sum(e[2] < 3 for e in table),
                "one_glyph_per_fill": table.one_per_fill, "stray_subpaths": table.stray,
                "ambiguous_groups": [sorted(e[3]) for e in table if len(e[3]) > 1], "build_seconds": round(time.time() - t0, 2)}
for mode in ("first_only", "cumulative"):
    tab = read_page.copy(table)
    for m in months[1:]:
        info = {}
        t0 = time.time(); text, thin = read_page.read(pdf(m), tab, th, vertical=VERTICAL, info=info); sec = round(time.time() - t0, 2)
        (out / f"{prefix}-{mode}-{m}.txt").write_text(text + "\n")
        sc = score(text, truth(m))
        res[f"{mode} {m}"] = {**sc, "page": info, "flagged_thin": len(thin), "read_seconds": sec, "groups_in_table": len(tab)}
        if mode == "cumulative":
            gl, _, _ = read_page.labelled_glyphs(pdf(m), truth(m))
            for b, c in gl:
                s, k = read_page.nearest(tab, b)
                if k < 0 or not read_page.accepts(tab[k], s, th) or tab[k][1] == "?":
                    read_page.add(tab, b, c, th)   # the person confirms the shapes reported as "?"
                else:
                    tab[k][2] += 1
print(json.dumps(res, ensure_ascii=False, indent=1))
