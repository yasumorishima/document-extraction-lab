"""Glyph-table method on a multi-page document series (e.g. a monthly report).

The first month's pages build the table (characters confirmed by a person =
truth by position); every later month's pages are read with it.
Threshold and size tolerance are picked from the first month's pages together.
Usage: python run_pages.py <dir> <months, comma-separated> <out-dir> [pages, default all] [--draft=<draft.json>] [--first-only]
  --draft: replace every group's character with an AI draft's answer (no human check),
           then read the later months with that table (first_only only).
Files: <dir>/<YYYYMM>-p<K>-outline.pdf and <dir>/<YYYYMM>-p<K>-truth.json
Modes as in run_method.py: first_only and cumulative.
"""
import glob, json, re, sys, time
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here)); sys.path.insert(0, str(here.parent / "tools"))
import glyphs, read_page
from score_text import score

d, months, out = Path(sys.argv[1]), sys.argv[2].split(","), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
DRAFT = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--draft=")), None)
args = [a for a in sys.argv if not a.startswith("--")]
want = set(args[4].split(",")) if len(args) > 4 else None
def pages(ym):
    ps = sorted(glob.glob(str(d / f"{ym}-p*-outline.pdf")), key=lambda p: int(re.search(r"-p(\d+)-", p)[1]))
    return [(p, p.replace("-outline.pdf", "-truth.json")) for p in ps if want is None or re.search(r"-p(\d+)-", p)[1] in want]

# threshold and size tolerance from the first month (as pick_threshold.py, over all its pages)
glyphs.SIZE_TOL = 99
reps = {}
for pdf, tr in pages(months[0]):
    gl, _, _ = read_page.labelled_glyphs(pdf, tr, with_size=True)
    for b, key in gl: reps.setdefault(key, []).append(b)
tol = max(max(abs(b[4] - bs[0][4]), abs(b[5] - bs[0][5])) for bs in reps.values() for b in bs[1:])
glyphs.SIZE_TOL = tol
same = min((glyphs.dice(bs[0], b), k) for k, bs in reps.items() for b in bs[1:])
keys = list(reps)
diff = max((glyphs.dice(reps[a][0], reps[b][0]), a, b) for i, a in enumerate(keys) for b in keys[i+1:] if not read_page.same_char(a[0], b[0]))
th = (same[0] + diff[0]) / 2 if same[0] > diff[0] else same[0] - 0.005
res = {"threshold": {"value": round(th, 4), "gap": same[0] > diff[0], "size_tol_px": tol,
                     "same_char_least_similar": [round(same[0], 4), same[1]], "different_chars_most_similar": [round(diff[0], 4), diff[1], diff[2]]}}
t0 = time.time(); table = None
for pdf, tr in pages(months[0]): table = read_page.build(pdf, tr, th, table)
if DRAFT:
    ans = json.load(open(DRAFT))["answer"]; changed = 0
    for i, e in enumerate(table):
        if e[1] == "?": continue
        a = ans.get(str(i), "?")
        if not read_page.same_char(a, e[1]): changed += 1
        e[1] = a
    res["draft"] = {"file": DRAFT, "entries_changed": changed}
res["table"] = {"groups": len(table), "thin(<3)": sum(e[2] < 3 for e in table), "ambiguous": [sorted(e[3]) for e in table if len(e[3]) > 1],
                "one_glyph_per_fill": table.one_per_fill, "build_seconds": round(time.time() - t0, 1)}
for mode in (("first_only",) if DRAFT or "--first-only" in sys.argv else ("first_only", "cumulative")):
    tab = read_page.copy(table)
    for ym in months[1:]:
        for pdf, tr in pages(ym):
            info = {}
            t0 = time.time(); text, flags = read_page.read(pdf, tab, th, info=info); sec = round(time.time() - t0, 2)
            name = Path(pdf).name.replace("-outline.pdf", "")
            (out / f"{name}-{mode}.txt").write_text(text + "\n")
            s = score(text, tr, nfkc=True)
            res[f"{mode} {name}"] = {**s, "page": info, "flagged": len(flags), "seconds": sec, "groups_in_table": len(tab)}
            if mode == "cumulative":
                gl, _, _ = read_page.labelled_glyphs(pdf, tr)
                for b, c in gl:
                    s2, k = read_page.nearest(tab, b)
                    if k < 0 or not read_page.accepts(tab[k], s2, th) or tab[k][1] == "?": read_page.add(tab, b, c, th)
                    else: tab[k][2] += 1
print(json.dumps(res, ensure_ascii=False, indent=1))
