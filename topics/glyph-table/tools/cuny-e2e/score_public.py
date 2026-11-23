"""Score screen-reader text of the CUNY full-app run on the public report vs the replica OCR.
Uses the app's own screen-reader text (scripts/tagged_text.py, read with pdfium).
Usage: E2E=<work-dir> python score_public.py <corpus-dir>... > json ; truth in $E2E/jinsui/ (public/prepare.sh)."""
import glob, json, re, sqlite3, subprocess, sys, collections
import os; S=os.environ["E2E"]; G=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..")
sys.path.insert(0,G+"/tools"); from score_text import score, bag
app=collections.Counter(); rep=collections.Counter(); subs=collections.Counter(); tasks=collections.Counter(); pages=[]
for D in sys.argv[1:]:
    for pdf in sorted(glob.glob(f"{D}/tagged_outputs/*/*_workflow_output.pdf")):
        m=re.search(r"(\d{6})-p(\d)-outline", pdf); ym,k=m[1],m[2]
        txt=subprocess.run([f"{S}/cuny/backend/.venv/bin/python","scripts/tagged_text.py",pdf],cwd=f"{S}/cuny/backend",capture_output=True,text=True).stdout
        open(f"{S}/runs/sr-haiku-pub-{ym}-p{k}.txt","w").write(txt)
        t=f"{S}/jinsui/{ym}-p{k}-truth.json"; ocr=open(f"{G}/results/public/ocr/{ym}-p{k}.txt").read()
        for name,c,src in (("app",app,txt),("replica",rep,ocr)):
            s=score(src,t,nfkc=True,loose=True); c.update({"seq_"+a:b for a,b in s["counts"].items()})
            c.update({"bag_"+a:b for a,b in bag(src,t,nfkc=True,loose=True).items() if a!="truth_chars"})
            if name=="app": subs.update(s["substituted"])
        pages.append(f"{ym}-p{k}")
    for f in glob.glob(f"{D}/*.sqlite3"):
        for r in sqlite3.connect(f).execute("select task_type,title,blocking from review_tasks"): tasks[f"{r[0]} | {re.sub(r'[0-9]+','N',r[1])} | blocking={r[2]}"]+=1
print(json.dumps({"pages":len(pages),"app":dict(app),"replica_ocr":dict(rep),"app_substituted_top":dict(subs.most_common(15)),"review_tasks":dict(tasks)},ensure_ascii=False,indent=1))
