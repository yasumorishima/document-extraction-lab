"""Score plain text against the truth with one yardstick for every method.

Truth rows = lines that share a baseline, cells joined left to right. Spaces
are ignored; empty lines are dropped. The whole page is aligned at once, so a
method that reads rows in the right order but splits or joins them differently
is not punished. "?" in the text means "left unassigned on purpose".
"moved" counts characters that appear both as missing and as extra (read in
another order); they are included in "missing" and "extra" too.

With nfkc=True both sides are NFKC-normalised first, so full-width and
half-width forms (２ and 2, （ and () count as the same character.
With loose=True (implies nfkc) the comparison also ignores the table bars "|"
some readers add, treats the dash family (- − ‐ ‑ – — ―) as one character,
the wave dash 〜 as ~, and "•" as "・". The long-vowel mark ー stays a character of its own.

Usage (module): score(text, truth_path, nfkc=False) -> dict
Usage (CLI):    python score_text.py <text-file> <truth.json> [--nfkc] [--loose]
"""
import json, sys, unicodedata
from collections import Counter
from difflib import SequenceMatcher

LOOSE = str.maketrans({"|": " ", "−": "-", "‐": "-", "‑": "-", "–": "-", "—": "-", "―": "-", "•": "・", "〜": "~", "～": "~"})

def _prep(t, nfkc, loose):
    if nfkc or loose: t = unicodedata.normalize("NFKC", t)
    if loose: t = t.translate(LOOSE)
    return t

def truth_text(path, nfkc=False, loose=False):
    rows = {}
    lines = json.load(open(path))["lines"]
    if lines and lines[0].get("vertical"):        # vertical writing: columns right to left, top to bottom
        for l in lines:
            rows.setdefault(-l["x"], []).append((-l["y"], _prep(l["text"], nfkc, loose).replace(" ", "")))
        return "\n".join("".join(t for _, t in sorted(rows[x])) for x in sorted(rows))
    for l in lines:
        l = {**l, "text": _prep(l["text"], nfkc, loose)}
        rows.setdefault(l["y"], []).append((l["x"], l["text"].replace(" ", "")))
    return "\n".join("".join(t for _, t in sorted(rows[y])) for y in sorted(rows, reverse=True))

def norm(text):
    return "\n".join(l.replace(" ", "").replace("\t", "") for l in text.splitlines() if l.strip())

def score(text, truth_path, nfkc=False, loose=False):
    w = truth_text(truth_path, nfkc, loose)
    g = norm(_prep(text, nfkc, loose))
    r = Counter(); subs = Counter(); miss = Counter(); extra = Counter()
    for op, a1, a2, b1, b2 in SequenceMatcher(None, w, g, autojunk=False).get_opcodes():
        A, B = w[a1:a2].replace("\n", ""), g[b1:b2].replace("\n", "")
        if op == "equal": r["correct"] += len(A); continue
        if op == "replace" and len(A) == len(B):
            for a, b in zip(A, B):
                if b == "?": r["unassigned"] += 1; miss[a + "(?)"] += 1
                else: r["substituted"] += 1; subs[a + "->" + b] += 1
            continue
        for a in A: r["missing"] += 1; miss[a] += 1
        for b in B:
            if b == "?": r["unassigned"] += 1
            else: r["extra"] += 1; extra[b] += 1
    # "moved": characters that are both missing in one place and extra in another
    # (the same characters read in a different order); missing/extra still include them.
    r["moved"] = sum(min(n, extra.get(c, 0)) for c, n in miss.items() if not c.endswith("(?)"))
    r["truth_chars"] = len(w.replace("\n", ""))
    return {"counts": dict(r), "substituted": dict(subs.most_common()),
            "missing": dict(miss.most_common()), "extra": dict(extra.most_common())}

def bag(text, truth_path, nfkc=False, loose=False):
    """Order-free comparison: how often each character occurs on the page.
    A misread shows up as one "short" (a truth character not found) and one "over"
    (a character the truth does not have); reading cells in another order changes
    nothing. Two misreads elsewhere can cancel out, so this is a lower bound on errors.
    "?" (left unassigned on purpose) is counted on its own and not as "over"."""
    w = Counter(truth_text(truth_path, nfkc, loose).replace("\n", ""))
    g = Counter(norm(_prep(text, nfkc, loose)).replace("\n", ""))
    q = g.pop("?", 0)
    matched = sum(min(n, g.get(c, 0)) for c, n in w.items())
    return {"truth_chars": sum(w.values()), "matched": matched, "short": sum(w.values()) - matched,
            "over": sum(g.values()) - matched, "unassigned": q}

if __name__ == "__main__":
    print(json.dumps(score(open(sys.argv[1]).read(), sys.argv[2], "--nfkc" in sys.argv, "--loose" in sys.argv), ensure_ascii=False, indent=1))
