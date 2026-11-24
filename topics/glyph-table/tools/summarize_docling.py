"""Score the docling runs of results/preregistration-docling-2026-11.md with tools/score_text.py.

Usage: python summarize_docling.py <runs-dir> <samples-dir> <out.json>
<runs-dir> holds one folder per arm (default-en, default-ja, fullocr-en-r1, ...), each with
<stem>.txt and run.json from run_docling.py. Months 2-12 only. Also scores A0 (empty text)
and runs a scorer self-check (known substitutions injected into the truth text).
EN is scored strict, JA with nfkc, as in the main evaluation.
Each arm is scored twice: as written ("raw"), and with Markdown table rules removed ("strip":
lines made only of | - : and spaces dropped, other "|" turned into spaces). The strip variant
was added after seeing the output (docling writes tables as Markdown), not pre-registered.
"""
import json, re, sys, unicodedata
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from score_text import score, truth_text

runs, samples, outp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
MONTHS = [f"2026-{m:02d}" for m in range(2, 13)]

def cls(c):
    if c.isdigit(): return "digit"
    n = unicodedata.name(c, "")
    if "HIRAGANA" in n or "KATAKANA" in n or c == "ー": return "kana"
    if "CJK UNIFIED" in n: return "kanji"
    if c.isascii() and c.isalpha(): return "latin"
    return "punct/other"

def stems(lang, pre=None):
    pre = pre or ("font" if lang == "en" else "ja-font")
    return [(f"{pre}-statement-{m}", samples / f"{pre}-truth-{m}.json") for m in MONTHS]

SEP = re.compile(r"^\s*\|?[\s|:\-]+\|?\s*$")
def strip_md(t):
    return "\n".join(l for l in t.splitlines() if not SEP.match(l)).replace("|", " ")

def total(arm_dir, lang, empty=False, strip=False, pre=None):
    nfkc = lang == "ja"
    c = Counter(); subs = Counter(); flags = []
    for stem, truth in stems(lang, pre):
        f = arm_dir / f"{stem}.txt" if arm_dir else None
        if empty: text = ""
        elif not f.exists(): flags.append(stem); continue
        else: text = f.read_text(encoding="utf-8")
        if strip: text = strip_md(text)
        r = score(text, truth, nfkc=nfkc)
        c.update(r["counts"]); subs.update(r["substituted"])
    by_cls = Counter()
    for pair, n in subs.items(): by_cls[cls(pair.split("->")[0])] += n
    return {"counts": dict(c), "substituted_by_truth_class": dict(by_cls),
            "top_substitutions": dict(subs.most_common(25)), "flagged_missing_output": flags}

def self_check():
    """Swap 5 characters of one truth text and score it: expect exactly 5 substituted."""
    truth = samples / "font-truth-2026-02.json"
    t = truth_text(truth); chars = list(t); idx = [i for i, ch in enumerate(chars) if ch.isalnum()][:50:10]
    for i in idx: chars[i] = "Z" if chars[i] != "Z" else "Y"
    r = score("".join(chars), truth)["counts"]
    return {"injected_substitutions": len(idx), "scored": r.get("substituted", 0),
            "extra": r.get("extra", 0), "missing": r.get("missing", 0), "ok": r.get("substituted", 0) == len(idx)}

out = {"self_check": self_check(),
       "A0-empty-en": total(None, "en", empty=True), "A0-empty-ja": total(None, "ja", empty=True)}
for d in sorted(p for p in runs.iterdir() if p.is_dir() and p.name != "test"):
    lang = "ja" if d.name.endswith("-ja") or "-ja-" in d.name else "en"
    pre = "shift3-font" if "-shift" in d.name else None
    for key, p in (("-long-shift", "long-shift3"), ("-long-good", "long-good"),   # round 3
                   ("-long-none", "long-none"), ("-mixed", "mixed")):
        if key in d.name: pre = p
    if d.name.endswith("-en-public"):     # detection only: no truth
        d_name_detect_only = True
    else:
        d_name_detect_only = False
    rj = d / "run.json"
    run = json.loads(rj.read_text()) if rj.exists() else None
    if not d.name.startswith("control") and not d_name_detect_only:
        out[d.name] = total(d, lang, pre=pre)
        out[d.name + " (strip)"] = total(d, lang, strip=True, pre=pre)
    else:
        out[d.name] = {"counts": {}, "substituted_by_truth_class": {}}
    if run:
        pages = [(f["pdf"], pg, sc) for f in run["files"] for pg, sc in (f.get("parse_score") or {}).items()]
        if d.name.startswith("control"):   # pages 1-5 of each monthly report (round 2)
            pages = [x for x in pages if int(x[1]) <= 5]
        out[d.name]["run"] = {"versions": run["versions"], "options": run["options"], "date": run["date"],
                              "auto_ocr_log": run.get("auto_ocr_log"),
                              "flags": [f for f in run["files"] if f.get("flag")],
                              "pages": len(pages), "pages_judged_broken": sum(sc == 0.0 for _, _, sc in pages),
                              "seconds_total": round(sum(f["seconds"] for f in run["files"]), 1)}
outp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in out.items():
    if k == "self_check": print(k, v); continue
    c = v["counts"]
    if "run" in v and "pages" in v["run"]:
        print(f"{k:24} pages={v['run']['pages']} judged_broken={v['run']['pages_judged_broken']} flags={len(v['run']['flags'])}")
    print(f"{k:16} substituted={c.get('substituted',0):5} extra={c.get('extra',0):5} missing={c.get('missing',0):5} "
          f"correct={c.get('correct',0):5} truth={c.get('truth_chars',0)} by_class={v['substituted_by_truth_class']}")
