"""Judge H1-H4 of results/preregistration-orientation-2026-11.md from the runs.

Usage: python check_orientation.py <variants-dir> <public-prepared-dir> <public-turned-out-dir> <public-upright-out-dir>
Reads results/method/orientation/*.json, results/method/*-12months.json (the earlier
records), results/public/method-jinsui.json, results/public/method-jinsui-orient-check.json,
results/public/method-text/ and the two public output dirs of run_pages.py.
"""
import glob, json, re, sys
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "tools"))
from score_text import bag

R = here.parent / "results"
V, P, P180, P0 = (Path(a) for a in sys.argv[1:5])
DEV = {"outline", "ja"}
out = {"H1": {}, "H2": {}, "H3": {}, "H4": {}}

def near(a, b):                      # same, or within 1% of the earlier value
    return abs(a - b) <= 0.01 * b

def earlier(c):
    f = R / "method" / f"{c}-12months.json"
    d = json.load(open(f)); tot = {}
    for k, v in d.items():
        if k.startswith("first_only"):
            for a, b in v["counts"].items(): tot[a] = tot.get(a, 0) + b
    return tot

ok = {"H1": True, "H2": True, "H3": True, "H4": True}
for f in sorted(glob.glob(str(R / "method" / "orientation" / "*.json"))):
    d = json.load(open(f)); c = d["prefix"]; base = earlier(c)
    err = lambda t: t.get("substituted", 0) + t.get("extra", 0)
    z = d["0 deg"]["counts"]
    # H4: 0 deg unchanged; held only for jitter0.1
    same0 = err(z) == err(base) and z.get("unassigned", 0) == base.get("unassigned", 0) and z.get("correct", 0) == base.get("correct", 0)
    held0 = d["0 deg"]["held_pages"]
    h4 = same0 and (bool(held0) == (c == "jitter0.1")) and (c != "jitter0.1" or len(held0) == 11)
    out["H4"][c] = {"errors": [err(z), err(base)], "unknown": [z.get("unassigned", 0), base.get("unassigned", 0)],
                    "correct": [z.get("correct", 0), base.get("correct", 0)], "held": len(held0), "pass": h4}
    ok["H4"] &= h4
    if c not in DEV:
        for a in ("90", "180", "270"):
            t = d[f"{a} deg"]["counts"]
            h1 = err(t) == err(base) and near(t.get("unassigned", 0), base.get("unassigned", 0)) and near(t.get("correct", 0), base.get("correct", 0))
            out["H1"][f"{c} {a}"] = {"errors": [err(t), err(base)], "unknown": [t.get("unassigned", 0), base.get("unassigned", 0)],
                                     "correct": [t.get("correct", 0), base.get("correct", 0)], "turns": d[f"{a} deg"]["turn_chosen"], "pass": h1}
            ok["H1"] &= h1
    for a in ("2", "45", "-1"):
        e = d[f"{a} deg"]; fe = e["errors_on_pages_not_held"]
        out["H2"][f"{c} {a}"] = {"held": len(e["held_pages"]), "not_held_errors": fe["substituted"] + fe["extra"],
                                 "in_17": c != "ja-vertical"}
        if c != "ja-vertical": ok["H2"] &= fe["substituted"] + fe["extra"] == 0

# H3: public, pages 1-5 of Jan-Nov 2026, turned 180, order-free scoring as the public write-up (NFKC, loose)
def public_tot(textdir, pattern):
    tot = {"over": 0, "short": 0, "unassigned": 0}
    for f in sorted(glob.glob(str(textdir / pattern))):
        m = re.search(r"(\d{6})-p(\d)-first_only\.txt$", f)
        if not m or m[2] not in "12345" or m[1] == "202512": continue
        b = bag(open(f).read(), P / f"{m[1]}-p{m[2]}-truth.json", nfkc=True, loose=True)
        for k in tot: tot[k] += b[k]
    return tot
t180 = public_tot(P180, "*-first_only.txt"); t0rec = public_tot(R / "public" / "method-text", "*-first_only.txt")
j180 = json.load(open(R / "public" / "method-jinsui-turned180.json"))
held180 = sorted(k.split()[1] for k, v in j180.items() if k.startswith("first_only") and v["page"]["held"] and re.search(r"-p[1-5]$", k))
turns = {}
for k, v in j180.items():
    if k.startswith("first_only"): turns[v["page"]["turn"]] = turns.get(v["page"]["turn"], 0) + 1
h3 = t180["over"] == 0 and all(h.startswith("202611") for h in held180) and len(held180) == 5 and near(t180["unassigned"], t0rec["unassigned"])
out["H3"] = {"turned_180": t180, "upright_record": t0rec, "held_pages_1_5": held180, "turns": turns, "pass": h3}
ok["H3"] = h3

# H4, public: upright run with orientation and hold on = the earlier record; held only Nov pages 1-5
strip = lambda c: {a: b for a, b in c.items() if a != "moved"}   # "moved" was added to the scorer later
j0 = json.load(open(R / "public" / "method-jinsui-orient-check.json")); rec = json.load(open(R / "public" / "method-jinsui.json"))
diff = [k for k, v in j0.items() if k.startswith("first_only") and strip(v["counts"]) != strip(rec[k]["counts"])]
held0 = sorted(k.split()[1] for k, v in j0.items() if k.startswith("first_only") and v["page"]["held"])
h4p = not diff and held0 == [f"202611-p{i}" for i in range(1, 6)]
out["H4"]["public"] = {"pages_differing_from_record": diff, "held": held0, "pass": h4p}
ok["H4"] &= h4p
out["verdict"] = ok
print(json.dumps(out, ensure_ascii=False, indent=1))
