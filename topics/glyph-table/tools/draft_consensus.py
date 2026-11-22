"""Which table entries should a person check? Compare several AI drafts of the same table.

Usage: python draft_consensus.py <lang: en|ja> <glob of draft JSONs>...
A group goes to the person when the drafts do not all give the same character
(Japanese: full/half width counted as the same). Reports how many groups that is,
and whether every group whose majority answer is wrong was among them.
The right answers are read from the drafts' own scoring fields ("answer"/"wrong").
"""
import glob, json, sys, unicodedata as u
lang, pats = sys.argv[1], sys.argv[2:]
nf = (lambda a: u.normalize("NFKC", a)) if lang == "ja" else (lambda a: a)
rs = [json.load(open(f)) for p in pats for f in sorted(glob.glob(p))]
truth = dict(rs[0]["answer"]); truth.update({i: v.split("->")[0] for i, v in rs[0]["wrong"].items()})
check = [i for i in truth if len({nf(r["answer"].get(i, "?")) for r in rs}) > 1]
wrong, missed = [], []
for i in truth:
    a = [nf(r["answer"].get(i, "?")) for r in rs]; maj = max(set(a), key=a.count)
    if maj != nf(truth[i]):
        wrong.append(i)
        if i not in check: missed.append(f"{truth[i]}->{maj}")
print(json.dumps({"drafts": len(rs), "groups": len(truth), "to_check_by_a_person": len(check),
                  "majority_wrong": len(wrong), "majority_wrong_not_flagged": missed}, ensure_ascii=False))
