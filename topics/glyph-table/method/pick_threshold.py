"""Pick the grouping threshold from the table-building month only (no peeking).

Within that month's labelled glyphs: the least similar pair of copies of one
character (same size), and the most similar pair of different characters.
If the first is above the second there is a gap, and its midpoint is used.

Module: pick(pdf, truth_path) -> (threshold or None, details)
CLI:    python pick_threshold.py <pdf> <truth.json>
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import glyphs, read_page

def pick(pdf, truth_path):
    glyphs.SIZE_TOL = 99                       # measure without the size gate first
    gl, _, _ = read_page.labelled_glyphs(pdf, truth_path, with_size=True)
    reps = {}
    for b, key in gl: reps.setdefault(key, []).append(b)      # key = (character, size)
    # copies of one character at one size: the least similar copy against the first one
    tol = max(max(abs(b[4] - bs[0][4]), abs(b[5] - bs[0][5])) for bs in reps.values() for b in bs[1:])
    glyphs.SIZE_TOL = tol
    same = [(glyphs.dice(bs[0], b), k) for k, bs in reps.items() for b in bs[1:]]
    same_min = min(same)
    keys = list(reps)
    diff_max = max((glyphs.dice(reps[a][0], reps[b][0]), a, b) for i, a in enumerate(keys) for b in keys[i+1:] if not read_page.same_char(a[0], b[0]))
    # tol = the largest width/height difference between copies of one character (size gate)
    if same_min[0] > diff_max[0]:
        th, how = (same_min[0] + diff_max[0]) / 2, "gap: midpoint"
    else:
        # no gap: keep every copy of a character together; look-alikes that fall in with
        # them are marked ambiguous by the table ("?"), never silently read as one of them
        th, how = same_min[0] - 0.005, "no gap: just below the least similar copies"
    return th, {"how": how, "size_tol_px": tol,"same_char_least_similar": [round(same_min[0], 4), same_min[1]],
                "different_chars_most_similar": [round(diff_max[0], 4), diff_max[1], diff_max[2]],
                "threshold": round(th, 4)}

if __name__ == "__main__":
    print(pick(sys.argv[1], sys.argv[2])[1])
