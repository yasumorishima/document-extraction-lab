"""Judge H5-H8 of results/preregistration-skew-2026-11.md from the runs.

Usage: python check_skew.py <public-prepared-dir> <out-1.5-dir> <json-1.5> <out-178-dir> <json-178> <json-upright>
Reads results/method/skew/*.json (this run), results/method/orientation/*.json (the previous
pre-registration's 0-degree results), results/public/method-text/ (upright public record) and
results/public/method-jinsui-orient-check.json (previous upright public run).
"""
import glob, json, re, sys
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "tools"))
from score_text import bag

R = here.parent / "results"
P = Path(sys.argv[1]); runs = {"1.5": (Path(sys.argv[2]), Path(sys.argv[3])), "178": (Path(sys.argv[4]), Path(sys.argv[5]))}
UP = Path(sys.argv[6])
JITTER = {"jitter0.02", "jitter0.05", "jitter0.1"}
near = lambda a, b: abs(a - b) <= 0.01 * b
err = lambda t: t.get("substituted", 0) + t.get("extra", 0)
out = {"H5": {}, "H6": {}, "H7": {}, "H8": {}}; ok = dict.fromkeys(out, True)

for f in sorted(glob.glob(str(R / "method" / "skew" / "*.json"))):
    d = json.load(open(f)); c = d["prefix"]; z = d["0 deg"]
    prev = json.load(open(R / "method" / "orientation" / f"{c}.json"))["0 deg"]
    h8 = z["counts"] == prev["counts"] and z["held_pages"] == prev["held_pages"]
    out["H8"][c] = {"pass": h8}; ok["H8"] &= h8
    for k, v in d.items():
        if not k.endswith(" deg") or k == "0 deg": continue
        fe = err(v["errors_on_pages_not_held"])
        out["H5"][f"{c} {k}"] = {"not_held_errors": fe, "held": len(v["held_pages"])}
        ok["H5"] &= fe == 0
        if c not in JITTER:
            t, b = v["counts"], z["counts"]
            h6 = err(t) == err(b) and near(t.get("unassigned", 0), b.get("unassigned", 0)) and near(t.get("correct", 0), b.get("correct", 0))
            out["H6"][f"{c} {k}"] = {"errors": [err(t), err(b)], "unknown": [t.get("unassigned", 0), b.get("unassigned", 0)],
                                    "correct": [t.get("correct", 0), b.get("correct", 0)], "turns": v["turn_chosen"], "pass": h6}
            ok["H6"] &= h6

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
    skews = sorted({v["page"]["skew"] for k, v in j.items() if k.startswith("first_only")}, key=lambda x: (x is None, x))
    turns = {}
    for k, v in j.items():
        if k.startswith("first_only"): turns[v["page"]["turn"]] = turns.get(v["page"]["turn"], 0) + 1
    h7 = t["over"] == 0 and near(t["unassigned"], rec["unassigned"]) and held == [f"202611-p{i}" for i in range(1, 6)]
    out["H7"][name] = {"turned": t, "upright_record": rec, "held_pages_1_5": held, "turns": turns,
                       "skew_min_max": [skews[0], skews[-1]] if skews else None, "pass": h7}
    ok["H7"] &= h7

prev = json.load(open(R / "public" / "method-jinsui-orient-check.json")); now = json.load(open(UP))
diff = [k for k, v in now.items() if k.startswith("first_only") and (v["counts"] != prev[k]["counts"] or v["page"]["held"] != prev[k]["page"]["held"])]
out["H8"]["public"] = {"pages_differing": diff, "pass": not diff}; ok["H8"] &= not diff
out["verdict"] = ok
print(json.dumps(out, ensure_ascii=False, indent=1))
