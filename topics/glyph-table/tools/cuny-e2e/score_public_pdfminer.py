"""Score the glyphs in the app's output PDFs read with pdfminer (every glyph the OCR layer draws),
split by pages that got a content_fidelity review task, against the replica OCR text.
Usage: E2E=<work-dir> python score_public_pdfminer.py <corpus-dir>... > json"""
import collections, glob, json, os, re, sqlite3, sys
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(G, "tools")); from score_text import score, bag
from pdfminer.high_level import extract_text
S = os.environ["E2E"]; D = sys.argv[1:]
flag = {}; lang = collections.Counter()
for d in D:
    c = sqlite3.connect(glob.glob(d + "/*.sqlite3")[0])
    jobs = {i: (fn, ol) for i, fn, ol in c.execute("select id,original_filename,ocr_language from jobs")}
    for fn, ol in jobs.values(): lang[ol] += 1
    for jid, md in c.execute("select job_id,metadata_json from review_tasks where task_type='content_fidelity'"):
        flag[re.search(r"(\d{6}-p\d)", jobs[jid][0])[1]] = len(json.loads(md)["flagged_blocks"])
tot = {"flagged": collections.Counter(), "not_flagged": collections.Counter()}; rep = collections.Counter(); subs = collections.Counter()
for d in D:
    for pdf in sorted(glob.glob(d + "/tagged_outputs/*/*_workflow_output.pdf")):
        p = re.search(r"(\d{6}-p\d)", pdf)[1]; t = f"{S}/jinsui/{p}-truth.json"; txt = extract_text(pdf)
        s = score(txt, t, nfkc=True, loose=True); b = bag(txt, t, nfkc=True, loose=True)
        k = "flagged" if p in flag else "not_flagged"; tot[k]["pages"] += 1
        tot[k].update({"seq_substituted": s["counts"]["substituted"], "bag_over": b["over"], "bag_short": b["short"]}); subs.update(s["substituted"])
        r = bag(open(f"{G}/results/public/ocr/{p}.txt").read(), t, nfkc=True, loose=True); rep.update({"bag_over": r["over"], "bag_short": r["short"]})
print(json.dumps({"ocr_language": dict(lang), "pages_with_content_fidelity_task": len(flag), "flagged_blocks": sum(flag.values()),
                  "app_output_pdfminer": {k: dict(v) for k, v in tot.items()}, "replica_ocr": dict(rep),
                  "substituted_top": dict(subs.most_common(12))}, ensure_ascii=False, indent=1))
