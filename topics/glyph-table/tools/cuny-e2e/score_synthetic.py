"""Score the screen-reader text (the app's scripts/tagged_text.py) of full-app runs on the self-made outline samples.
Usage: E2E=<work-dir> python score_synthetic.py <EN corpus dir name> <JA corpus dir name> <tag>
Expects $E2E/samples/{outline,ja}-truth-YYYY-MM.json (make_sample.py) and writes $E2E/runs/sr-<tag>-*.txt."""
import glob, json, os, re, sqlite3, subprocess, sys, collections
import os; S=os.environ["E2E"]; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),".."))
from score_text import score
def run(dirname, prefix, nfkc, ocrdir):
    D=f"{S}/cuny/backend/data/benchmarks/{dirname}"; tot=collections.Counter(); rep=collections.Counter(); sub=collections.Counter(); per=[]
    for pdf in sorted(glob.glob(f"{D}/tagged_outputs/*/*_workflow_output.pdf")):
        m=re.search(r"(\d{4}-\d{2})_workflow", pdf)[1]
        txt=subprocess.run([f"{S}/cuny/backend/.venv/bin/python","scripts/tagged_text.py",pdf],cwd=f"{S}/cuny/backend",capture_output=True,text=True).stdout
        out=f"{S}/runs/sr-{_tag}-{prefix}-{m}.txt"; open(out,"w").write(txt)
        truth=f"{S}/samples/{prefix}-truth-{m}.json"
        a=score(txt,truth,nfkc); b=score(open(f"{ocrdir}/{prefix}-{m[5:]}.txt").read(),truth,nfkc)
        tot.update(a["counts"]); rep.update(b["counts"]); sub.update(a["substituted"]); per.append((m,a["counts"]["substituted"],b["counts"]["substituted"]))
    tasks=collections.Counter()
    for f in glob.glob(f"{D}/*.sqlite3"):
        for r in sqlite3.connect(f).execute("select task_type,title,blocking from review_tasks"): tasks[r]+=1
    print(prefix, "app:",dict(tot)); print(prefix, "replica OCR:",dict(rep)); print("per month (app, replica):",per)
    print("top substitutions:",sub.most_common(8)); print("review tasks:",dict(tasks)); print()
_tag=__import__("sys").argv[3]
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","results")
import sys as _s
run(_s.argv[1],"outline",False,R+"/ocrmypdf-12m")
run(_s.argv[2],"ja",True,R+"/ocrmypdf-ja")
