"""Check that copies of one blog post have the same title and body.

Usage: python check_post_copies.py <source.md> <copy.md> [<copy.md> ...]
Each file starts with a front-matter block between two "---" lines (Zenn or Qiita style).
The body is everything after it, with leading/trailing blank lines dropped.
Fails (exit 1) if any body is empty, or a copy's title or body differs from the source.
Front-matter fields other than the title (published, tags, ...) are not compared.
Only same-language copies: the English DEV.to version is a translation and is not checked here.
"""
import re, sys
from pathlib import Path

def split(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not m: sys.exit(f"{path}: no front matter")
    t = re.search(r"^title:\s*(.*)$", m.group(1), re.M)
    title = t.group(1).strip().strip('"') if t else None
    return title, m.group(2).strip("\n")

src, copies = sys.argv[1], sys.argv[2:]
if not copies: sys.exit(__doc__)
st, sb = split(src)
ok = True
for p, (t, b) in [(src, (st, sb))] + [(c, split(c)) for c in copies]:
    if not b.strip(): print(f"EMPTY BODY  {p}"); ok = False
    if p == src: continue
    if t != st: print(f"TITLE DIFF  {p}: {t!r} vs {st!r}"); ok = False
    if b != sb:
        bl, sl = b.splitlines(), sb.splitlines()
        i = next((k for k in range(min(len(bl), len(sl))) if bl[k] != sl[k]), min(len(bl), len(sl)))
        print(f"BODY DIFF   {p}: first differing body line {i + 1} "
              f"({len(sl)} lines in source, {len(bl)} in copy)")
        ok = False
    else: print(f"same        {p} ({len(b.splitlines())} body lines)")
sys.exit(0 if ok else 1)
