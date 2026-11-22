"""Text of a PDF page as rows, for scoring with score_text.py (needs pdfminer.six).

Characters come from the PDF's own text information (font + ToUnicode), in
position order: rows by vertical position, left to right. A character the PDF
cannot name ("(cid:N)", control characters, U+FFFD) is written "?".
Usage: python pdf_text.py <pdf>   -> prints the rows
"""
import sys
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar

def chars(o):
    if isinstance(o, LTChar): yield o
    elif hasattr(o, "__iter__"):
        for c in o: yield from chars(c)

def page_rows(pdf):
    cs = []
    for p in extract_pages(pdf, laparams=None):
        for c in chars(p):
            t = c.get_text()
            if t.isspace(): continue
            if t.startswith("(cid:") or len(t) != 1 or ord(t) < 32 or t == "�": t = "?"
            cs.append(((c.y0 + c.y1) / 2, c.x0, t))
    cs.sort(key=lambda t: -t[0]); rows, top = [], None
    for y, x, t in cs:
        if top is None or top - y > 4: rows.append([]); top = y
        rows[-1].append((x, t))
    return "\n".join("".join(t for _, t in sorted(r)) for r in rows)

if __name__ == "__main__":
    print(page_rows(sys.argv[1]))
