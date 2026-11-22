"""Compare any PDF's extracted text with the truth, row by row, allowing for
missing or extra characters (for OCR output, whose glyph count can differ).

Usage: python compare_text.py <pdf> <truth.json>   (needs pdfminer.six)
Rows are the truth baselines; spaces are ignored. Counts per character:
correct / substituted (a wrong character) / missing / extra (not in the truth).
"""
import json, sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar

def chars(o):
    if isinstance(o, LTChar): yield o
    elif hasattr(o, "__iter__"):
        for c in o: yield from chars(c)

pdf, truth = sys.argv[1:3]
lines = json.load(open(truth))["lines"]
want = defaultdict(list)
for l in lines: want[l["y"]].append((l["x"], l["text"].replace(" ", "")))
got = defaultdict(list)
for p in extract_pages(pdf, laparams=None):
    for c in chars(p):
        t = c.get_text()
        if t.isspace(): continue
        mid = (c.y0 + c.y1) / 2 - 3          # roughly the baseline for 9-10 pt text
        y = min(want, key=lambda b: abs(b - mid))
        got[y].append((c.x0, t if len(t) == 1 else "?"))
res = Counter(); subs = Counter(); miss = Counter(); extra = Counter()
for y in sorted(want, reverse=True):
    w = "".join(t for _, t in sorted(want[y]))
    g = "".join(t for _, t in sorted(got[y]))
    for op, a1, a2, b1, b2 in SequenceMatcher(None, w, g, autojunk=False).get_opcodes():
        if op == "equal": res["correct"] += a2 - a1
        elif op == "replace" and a2 - a1 == b2 - b1:
            for a, b in zip(w[a1:a2], g[b1:b2]): res["substituted"] += 1; subs[(a, b)] += 1
        else:
            for a in w[a1:a2]: res["missing"] += 1; miss[a] += 1
            for b in g[b1:b2]: res["extra"] += 1; extra[b] += 1
print(dict(res))
print("substituted:", dict(subs.most_common()))
print("missing:", dict(miss.most_common()), " extra:", dict(extra.most_common()))
