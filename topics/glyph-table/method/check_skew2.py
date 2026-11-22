"""Judge H9-H13 of results/preregistration-skew2-2026-11.md from the runs.

Usage: python check_skew2.py <public-prepared-dir> <out--0.8-dir> <json--0.8> <out-93-dir> <json-93> <json-upright>
Reads results/method/skew2/*.json (this run), results/method/orientation/*.json (0-degree
results of the first pre-registration), results/public/method-text/ (upright public record)
and results/public/method-jinsui-orient-check.json (the earlier upright public run).
"""
import glob, json, re, sys
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "tools"))
from score_text import bag

R = here.parent / "results"
P = Path(sys.argv[1]); runs = {"-0.8": (Path(sys.argv[2]), Path(sys.argv[3])), "93": (Path(sys.argv[4]), Path(sys.argv[5]))}
UP = Path(sys.argv[6])
JITTER = {"jitter0.02", "jitter0.05", "jitter0.1"}
SMALL, BIG = ("0.3 deg", "-4 deg", "9 deg", "95 deg"), ("25 deg", "-60 deg")
near = lambda a, b: abs(a - b) <= 0.01 * b
err = lambda t: t.get("substituted", 0) + t.get("extra", 0)
out = {k: {} for k in ("H9", "H10", "H11", "H12", "H13")}; ok = dict.fromkeys(out, True)

for f in sorted(glob.glob(str(R / "method" / "skew2" / "*.json"))):
    d = json.load(open(f)); c = d["prefix"]; z = d["0 deg"]
    prev = json.load(open(R / "method" / "orientation" / f"{c}.json"))["0 deg"]
    h13 = z["counts"] == prev["counts"] and z["held_pages"] == prev["held_pages"]
    out["H13"][c] = {"pass": h13}; ok["H13"] &= h13
    for k, v in d.items():
        if not k.endswith(" deg") or k == "0 deg": continue
        fe = err(v["errors_on_pages_not_held"])
        out["H9"][f"{c} {k}"] = {"not_held_errors": fe, "held": len(v["held_pages"])}; ok["H9"] &= fe == 0
        if k in SMALL and c not in JITTER:
            t, b = v["counts"], z["counts"]
            h10 = err(t) == err(b) and near(t.get("unassigned", 0), b.get("unassigned", 0)) and near(t.get("correct", 0), b.get("correct", 0))
            out["H10"][f"{c} {k}"] = {"errors": [err(t), err(b)], "unknown": [t.get("unassigned", 0), b.get("unassigned", 0)],
                                     "correct": [t.get("correct", 0), b.get("correct", 0)], "turns": v["turn_chosen"], "pass": h10}
            ok["H10"] &= h10
        if k in BIG:
            h11 = len(v["held_pages"]) == len(d["months_read"])
            out["H11"][f"{c} {k}"] = {"held": len(v["held_pages"]), "pass": h11}; ok["H11"] &= h11

def public_tot(textdir):
    tot = {"over": 0, "short": 0, "unassigned": 0}
    for f in sorted(glob.glob(str(textdir / "*-first_only.txt"))):
        m = re.search(r"(\d{6})-p(\d)-first_only\.txt$", f)
        if not m or m[2] not in "12345" or m[1] == "202512": continue
        b = bag(open(f).read(), P / f"{m[1]}-p{m[2]}-truth.json", nfkc=True, loose=True)
        for k in tot: tot[k] += b[k]
    return tot
rec = public_tot(R / "public" / "method-text")
for name, (textdir, js) in runs.items():
    t = public_tot(textdir); j = json.load(open(js))
    held = sorted(k.split()[1] for k, v in j.items() if k.startswith("first_only") and v["page"]["held"] and re.search(r"-p[1-5]$", k))
    sk = [v["page"]["skew"] for k, v in j.items() if k.startswith("first_only") and v["page"]["skew"] is not None]
    turns = {}
    for k, v in j.items():
        if k.startswith("first_only"): turns[v["page"]["turn"]] = turns.get(v["page"]["turn"], 0) + 1
    h12 = t["over"] == 0 and near(t["unassigned"], rec["unassigned"]) and held == [f"202611-p{i}" for i in range(1, 6)]
    out["H12"][name] = {"turned": t, "upright_record": rec, "held_pages_1_5": held, "turns": turns,
                        "skew_min_max": [min(sk), max(sk)] if sk else None, "pass": h12}
    ok["H12"] &= h12

prev = json.load(open(R / "public" / "method-jinsui-orient-check.json")); now = json.load(open(UP))
diff = [k for k, v in now.items() if k.startswith("first_only") and (v["counts"] != prev[k]["counts"] or v["page"]["held"] != prev[k]["page"]["held"])]
out["H13"]["public"] = {"pages_differing": diff, "pass": not diff}; ok["H13"] &= not diff
out["verdict"] = ok
print(json.dumps(out, ensure_ascii=False, indent=1))
