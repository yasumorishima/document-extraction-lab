"""Truth file (same format as the self-made samples) from a PDF page that still has its text.

Every character with its position comes from the PDF's own text information
(pdfminer.six): origin x, advance, baseline y (from the text matrix), size and font name
(with "/slantN" added when the text matrix slants the glyphs, as synthetic italics do).
Rows are characters sharing a baseline (rounded to 0.5 pt), cut into separate
"lines" where the gap to the previous character is larger than one em.
Usage: python truth_from_text.py <text-page.pdf> <truth.json>
"""
import json, sys
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar

def chars(o):
    if isinstance(o, LTChar): yield o
    elif hasattr(o, "__iter__"):
        for c in o: yield from chars(c)

pdf, dest = sys.argv[1:3]
cs = []
for p in extract_pages(pdf, laparams=None):
    for c in chars(p):
        t = c.get_text()
        if not t.strip() or len(t) != 1: continue
        size = round(c.size, 2); base = round(c.matrix[5] * 2) / 2
        font = c.fontname.split("+")[-1]
        a, b, cc, d, e, f = c.matrix
        if d and abs(cc / d) > 0.01: font += f"/slant{cc / d:.2f}"     # synthetic italic: a different shape
        cs.append((base, c.x0, t, round(c.x1 - c.x0, 3), size, font))
rows = {}
for base, x, t, adv, size, font in cs: rows.setdefault(base, []).append((x, t, adv, size, font))
lines = []
for base in sorted(rows, reverse=True):
    cur = None
    for x, t, adv, size, font in sorted(rows[base]):
        if cur is None or x - (cur["chars"][-1][1] + cur["chars"][-1][2]) > size:
            cur = {"text": "", "x": round(x, 2), "y": base, "size": size, "chars": []}; lines.append(cur)
        cur["text"] += t; cur["chars"].append([t, round(x, 3), adv, base, size, font])
json.dump({"source": "text layer of the original PDF", "lines": lines}, open(dest, "w"), ensure_ascii=False, indent=1)
print(dest, sum(len(l["chars"]) for l in lines), "chars")
