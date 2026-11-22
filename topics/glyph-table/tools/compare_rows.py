"""Compare a repaired PDF with the truth, row by row (rows = truth baselines, cells joined in x order).

Usage: python compare_rows.py <repaired.pdf> <truth.json>   (needs pdfminer.six)
Spaces are ignored. "?" = a glyph still without Unicode."""
import json, sys
from collections import Counter, defaultdict
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar
def chars(o):
    if isinstance(o, LTChar): yield o
    elif hasattr(o, "__iter__"):
        for c in o: yield from chars(c)
fixed, truth = sys.argv[1:3]
lines = json.load(open(truth))["lines"]
want = defaultdict(list)
for l in lines: want[l["y"]].append((l["x"], l["text"].replace(" ", "")))
cs = [c for p in extract_pages(fixed, laparams=None) for c in chars(p) if c.get_text() != " "]
got = defaultdict(list)
for c in cs:
    y = min(want, key=lambda b: abs(b - c.y0))
    got[y].append((c.x0, c.get_text()))
res = Counter(); diffs = []
for y in sorted(want, reverse=True):
    w = [ch for _, t in sorted(want[y]) for ch in t]
    g = [t if len(t) == 1 else "?" for _, t in sorted(got[y])]
    if len(w) != len(g): diffs.append(("LENGTH", "".join(w), "".join(g))); continue
    for a, b in zip(w, g):
        res["correct" if a == b else ("unmapped (?)" if b == "?" else "WRONG")] += 1
        if a != b: diffs.append((a, b))
print(dict(res)); print(Counter(diffs))
