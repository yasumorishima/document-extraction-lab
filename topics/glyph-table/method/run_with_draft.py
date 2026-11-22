"""What happens if the AI's table draft is used without a human check.

Builds the month-1 table exactly as draft_table_with_claude.py does (same
groups, same order), replaces every group's character with the draft's answer,
and reads months 2..N with it.
Usage: python run_with_draft.py <gen-dir> <prefix> <months> <draft.json>
"""
import json, sys
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here)); sys.path.insert(0, str(here.parent / "tools"))
import read_page, pick_threshold
from score_text import score
gen, prefix, n, draft = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), json.load(open(sys.argv[4]))
pdf = lambda m: gen / f"{prefix}-statement-2026-{m:02d}.pdf"
truth = lambda m: gen / f"{prefix}-truth-2026-{m:02d}.json"
th, _ = pick_threshold.pick(pdf(1), truth(1))
table = read_page.build(pdf(1), truth(1), th)
assert len(table) == draft["groups"], (len(table), draft["groups"])
changed = 0
for i, e in enumerate(table):
    a = draft["answer"].get(str(i), "?")
    if e[1] != "?" and a != e[1]: changed += 1
    e[1] = a if e[1] != "?" else "?"
tot = {"correct": 0, "substituted": 0, "unassigned": 0, "truth_chars": 0}; subs = {}
for m in range(2, n + 1):
    text, _ = read_page.read(pdf(m), table, th)
    s = score(text, truth(m), nfkc=prefix.startswith("ja"))
    for k in tot: tot[k] += s["counts"].get(k, 0)
    for k, v in s["substituted"].items(): subs[k] = subs.get(k, 0) + v
print(json.dumps({"draft": sys.argv[4], "table_entries_wrong": changed, "months_2_to_n": tot, "substitutions": subs}, ensure_ascii=False))
