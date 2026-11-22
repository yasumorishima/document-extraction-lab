"""Build a glyph table and read pages with it.

A page is a list of filled paths ("fills"); table rules are removed first.
One fill can be one glyph (most generators) or a whole line of glyphs.

build(pdf, truth, th, table=None)
  The characters are what a person would confirm; here they come from the
  truth file by position: every subpath goes to the character box that holds
  its centre, so the pieces of one character (the dot of "i", the two halves
  of "明") are put together. Each new group takes the character of its first
  glyph, as a person labelling one representative would. If a later glyph
  joins a group but is confirmed as a different character, the group is
  marked ambiguous: it reads as "?" from then on.
  The table also learns whether this producer draws one glyph per fill.
  Entry: [bitmap, char, count, set of chars seen, lowest member similarity].

read(pdf, table, th, thin=3, vertical=False, orient=True, info=None) -> (text, flags)
  The page is first straightened (its tilt measured by `skew` and turned back; table rules are removed
  again afterwards; a page tilted more than SKEW_HOLD_DEG is held), then turned by 0/90/180/270 degrees to the orientation in which the
  table accepts the most glyphs. A page with more than HOLD "?" is marked held.
  Each fill is first matched whole. If that fails and the producer draws
  several glyphs per fill, the fill's pieces are split in the way that best
  fits the table (pieces ordered left to right; a glyph is 1-40 pieces and at
  most MAXWIDTH times as wide as the fill's tallest piece).
  Anything no group accepts is written "?". Rows come from glyph positions
  (vertical=True: columns right to left, each read top to bottom).
  flags: glyphs to check by eye (see `risky`).
"""
import json, math, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import glyphs

MARGIN = 0.02   # how far below a group's own lowest member similarity a new glyph may be
NEAR = 0.10     # a thin group's glyph is flagged when another character's group is this close
MAXPIECES = 40   # a many-stroke kanji can have 20+ pieces
MAXWIDTH = 1.6   # a glyph is at most this many times as wide as the tallest piece in its fill

class Table(list):
    """The glyph table, with an index by bitmap width and height: glyphs.dice() scores 0
    whenever the sizes differ by more than glyphs.SIZE_TOL, so only nearby sizes are compared."""
    one_per_fill = True
    def __init__(self, *a):
        super().__init__(*a); self.index = {}
        for i, e in enumerate(self): self.index.setdefault((e[0][4], e[0][5]), []).append(i)
    def append(self, e):
        super().append(e); self.index.setdefault((e[0][4], e[0][5]), []).append(len(self) - 1)
    def candidates(self, b):
        t = glyphs.SIZE_TOL; w, h = b[4], b[5]
        for dw in range(-t, t + 1):
            for dh in range(-t, t + 1):
                yield from self.index.get((w + dw, h + dh), ())

def copy(table):
    t = Table([[e[0], e[1], e[2], set(e[3]), e[4]] for e in table]); t.one_per_fill = table.one_per_fill
    return t

def nearest(table, b):
    idx = table.candidates(b) if isinstance(table, Table) else range(len(table))
    return max(((glyphs.dice(table[i][0], b), i) for i in idx), default=(0.0, -1))

def accepts(entry, s, th):
    """A glyph joins a group only if it is at least as close as the group's own
    members were (minus MARGIN), and never below the global threshold. A group
    seen once has no members to learn from and uses the global threshold."""
    return s >= th and (entry[2] < 2 or s >= entry[4] - MARGIN)

def _center(sub):
    xs = [x for x, _ in sub]; ys = [y for _, y in sub]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

def labelled_glyphs(pdf, truth_path, with_size=False):
    """Glyphs of a page with the confirmed character of each (from the truth by position).
    Returns (list of (bitmap, char or (char, size[, font])), stray subpaths, glyphs per fill).
    The font name is there only when the truth file records it (public samples)."""
    lines = json.load(open(truth_path))["lines"]
    boxes = [c for l in lines for c in l["chars"]]
    # how far a character's box reaches below / above its baseline, in sizes. Vertical writing
    # stacks characters one size apart, so its boxes are exactly one em (the font's em box
    # sits 0.12 below the baseline at 0.88 ascent, as make_sample.py draws it)
    reach = [(0.12, 0.88) if l.get("vertical") else (0.35, 1.0) for l in lines for _ in l["chars"]]
    fills, _ = glyphs.page_fills(pdf)
    out, stray, per_fill = [], 0, []
    def box_of(cx, cy, w, h):
        hit = [i for i, (ch, x, adv, y, size, *_) in enumerate(boxes)
               if x <= cx <= x + adv and y - reach[i][0] * size <= cy <= y + reach[i][1] * size and w <= 1.5 * max(adv, size) and h <= 1.5 * size]
        return hit[0] if len(hit) == 1 else None
    for subs in fills:
        groups = {}
        # a whole fill that fits one character box is that character (slanted glyphs reach
        # outside their box, so their pieces must not be sent to the neighbours one by one)
        xs = [x for s in subs for x, _ in s]; ys = [y for s in subs for _, y in s]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        whole = box_of((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0)
        if whole is not None and any(j != whole and x0 < bx + badv / 2 < x1 and y0 < by + 0.3 * bsize < y1
                                     for j, (_, bx, badv, by, bsize, *_) in enumerate(boxes)):
            whole = None                       # the fill also covers another character: not one glyph
        if whole is not None:
            per_fill.append(1)
            ch, x, adv, y, size, *font = boxes[whole]
            out.append((glyphs.bitmap(subs, evenodd=subs.evenodd), (ch, size, *font) if with_size else ch))
            continue
        for s in subs:
            cx, cy = _center(s)
            xs = [x for x, _ in s]; ys = [y for _, y in s]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            # the subpath's centre must lie in the character's box, and the subpath must not be
            # much bigger than the character (table frames and other drawings are not glyphs)
            i = box_of(cx, cy, w, h)
            if i is not None: groups.setdefault(i, []).append(s)
            else: stray += 1
        per_fill.append(len(groups))
        for i, ss in groups.items():
            ch, x, adv, y, size, *font = boxes[i]
            out.append((glyphs.bitmap(ss, evenodd=subs.evenodd), (ch, size, *font) if with_size else ch))
    return out, stray, per_fill

def same_char(a, b):
    """Characters that differ only in width form (： and :, ２ and 2) count as the same,
    as the scoring does."""
    return unicodedata.normalize("NFKC", a) == unicodedata.normalize("NFKC", b)

def add(table, b, c, th):
    s, k = nearest(table, b)
    if k >= 0 and s >= th:                                 # building: grouping uses the global threshold
        e = table[k]; e[2] += 1; e[3].add(c); e[4] = min(e[4], s)
        if len({unicodedata.normalize("NFKC", x) for x in e[3]}) > 1:
            e[1] = "?"                                     # look-alikes the table cannot tell apart
    else:
        table.append([b, c, 1, {c}, 1.0])

def build(pdf, truth_path, th, table=None):
    table = Table() if table is None else table
    gl, stray, per_fill = labelled_glyphs(pdf, truth_path)
    if per_fill and max(per_fill) > 1: table.one_per_fill = False
    for b, c in gl: add(table, b, c, th)
    table.stray = stray
    return table

def risky(table, b, k, s, thin):
    """Thin data that matters: the group was seen fewer than `thin` times AND some
    group of a different character is almost as similar (within NEAR)."""
    if table[k][2] >= thin: return False
    idx = table.candidates(b) if isinstance(table, Table) else range(len(table))
    other = max((glyphs.dice(table[i][0], b) for i in idx if not same_char(table[i][1], table[k][1])), default=0.0)
    return s - other < NEAR

def _match(table, b, th):
    s, k = nearest(table, b)
    return (k, s) if k >= 0 and accepts(table[k], s, th) and table[k][1] != "?" else (-1, s)

def _split(table, subs, th):
    """Best split of a fill's pieces into glyphs: maximise the width covered by
    accepted matches. Returns [(bitmap, k)] with k = -1 for unmatched pieces."""
    units = sorted(subs, key=lambda s: _center(s)[0]); n = len(units)
    span = [(min(x for x, _ in u), max(x for x, _ in u)) for u in units]
    tallest = max(max(y for _, y in u) - min(y for _, y in u) for u in units)
    best = [(0.0, [])] + [None] * n
    for j in range(1, n + 1):
        for i in range(j - 1, max(0, j - MAXPIECES) - 1, -1):
            if j - i > 1 and max(r for _, r in span[i:j]) - min(l for l, _ in span[i:j]) > MAXWIDTH * tallest: break
            b = glyphs.bitmap(units[i:j], evenodd=getattr(subs, "evenodd", False)); k, s = _match(table, b, th)
            gain = (b[2] - b[0]) if k >= 0 else 0.0
            if j - i > 1 and k < 0: continue          # unmatched pieces are reported one by one
            cand = (best[i][0] + gain, best[i][1] + [(b, k)])
            if best[j] is None or cand[0] > best[j][0] + 1e-9 or (abs(cand[0] - best[j][0]) <= 1e-9 and len(cand[1]) < len(best[j][1])):
                best[j] = cand
    out = []
    for b, k in best[n][1]:                           # merge neighbouring unmatched pieces that overlap in x
        if k < 0 and out and out[-1][1] < 0 and b[0] < out[-1][0][2]:
            prev = out[-1][0]; out[-1] = ((min(prev[0], b[0]), min(prev[1], b[1]), max(prev[2], b[2]), max(prev[3], b[3]), 0, 0, []), -1)
        else: out.append((b, k))
    return out

HOLD = 0.30      # a page with more than this share of "?" glyphs is held for a person (fixed in
                 # results/preregistration-orientation-2026-11.md before it was tested)
TURNS = (0, 90, 180, 270)
SAMPLE = 400     # at most this many glyphs are tried per orientation

def turn(fills, deg):
    """The fills turned clockwise by `deg` (a multiple of 90): undoes a page turned counter-clockwise."""
    f = {0: lambda x, y: (x, y), 90: lambda x, y: (y, -x), 180: lambda x, y: (-x, -y), 270: lambda x, y: (-y, x)}[deg]
    out = []
    for fl in fills:
        g = glyphs.Fill([f(x, y) for x, y in s] for s in fl); g.evenodd = fl.evenodd; out.append(g)
    return out

SKEW_SIZE = 0.10   # two contours pair up only if width and height differ by at most this share
SKEW_MIN_PAIRS = 20
SKEW_MIN_DEG = 0.05
SKEW_HOLD_DEG = 10.0   # a page tilted more than this is held for a person (the tilt is measured less precisely)
SKEW_SAMPLE = 3000
SKEW_CELL = 20.0   # pt: neighbours are looked for in the 3x3 grid cells around a contour

def skew(fills):
    """The page's tilt in degrees, in (-45, 45]: the median angle between each contour's centre and
    the centre of the nearest contour of about the same size, folded by 90 degrees (text lines and
    columns both give 0 on an upright page). None if fewer than SKEW_MIN_PAIRS pairs."""
    subs = [s for fl in fills for s in fl]
    step = max(1, len(subs) // SKEW_SAMPLE); boxes = []
    for s in subs[::step]:
        xs = [x for x, _ in s]; ys = [y for _, y in s]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if max(w, h) < 1.0: continue
        boxes.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, w, h))
    grid = {}
    for i, (cx, cy, _, _) in enumerate(boxes):
        grid.setdefault((int(cx // SKEW_CELL), int(cy // SKEW_CELL)), []).append(i)
    angles = []
    for i, (cx, cy, w, h) in enumerate(boxes):
        gx, gy = int(cx // SKEW_CELL), int(cy // SKEW_CELL); best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    if j == i: continue
                    x2, y2, w2, h2 = boxes[j]
                    if abs(w2 - w) > SKEW_SIZE * max(w, w2) or abs(h2 - h) > SKEW_SIZE * max(h, h2): continue
                    d = (x2 - cx) ** 2 + (y2 - cy) ** 2
                    if d > 1e-6 and (best is None or d < best[0]): best = (d, x2 - cx, y2 - cy)
        if best:
            a = math.degrees(math.atan2(best[2], best[1]))
            angles.append(-((-a + 45) % 90 - 45))        # fold into (-45, 45]
    if len(angles) < SKEW_MIN_PAIRS: return None
    angles.sort(); n = len(angles)
    return angles[n // 2] if n % 2 else (angles[n // 2 - 1] + angles[n // 2]) / 2

def rotate(fills, deg):
    """The fills turned counter-clockwise by `deg` (any angle) about the origin."""
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg)); out = []
    for fl in fills:
        g = glyphs.Fill([(c * x - s_ * y, s_ * x + c * y) for x, y in sub] for sub in fl); g.evenodd = fl.evenodd; out.append(g)
    return out

def orientation(table, fills, th):
    """The turn (0/90/180/270) under which the table accepts the most glyphs. A fill counts
    once if it matches whole, otherwise each of its x-overlap groups that matches counts."""
    step = max(1, len(fills) // SAMPLE); sample = fills[::step]
    best = None
    for deg in TURNS:
        n = 0
        for fl in turn(sample, deg):
            if _match(table, glyphs.bitmap(fl), th)[0] >= 0: n += 1; continue
            if len(fl) > 1:
                n += sum(_match(table, glyphs.bitmap(glyphs.Fill(g), evenodd=fl.evenodd), th)[0] >= 0
                         for g in glyphs.split_glyphs(list(fl)))
        if best is None or n > best[1]: best = (deg, n)
    return best[0]

def read(pdf, table, th, thin=3, vertical=False, orient=True, info=None):
    """info, if a dict, receives: turn (degrees the page was turned back), unknown_share, held."""
    fills, _ = glyphs.page_fills(pdf)
    tilt = skew(fills) if orient else None
    if tilt is not None and abs(tilt) > SKEW_MIN_DEG: fills = rotate(fills, -tilt)
    deg = orientation(table, fills, th) if orient else 0
    if deg: fills = turn(fills, deg)
    if tilt is not None and abs(tilt) > SKEW_MIN_DEG:   # rules that were tilted are straight now
        kept = []
        for fl in fills:
            g = glyphs.Fill(sub for sub in fl if not glyphs.is_rule(sub)); g.evenodd = fl.evenodd
            if g: kept.append(g)
        fills = kept
    items = []
    for subs in fills:
        whole = glyphs.bitmap(subs); k, s = _match(table, whole, th)
        if k >= 0 or table.one_per_fill or len(subs) == 1:
            parts = [(whole, k)]
        else:
            parts = _split(table, subs, th)
        for b, k in parts:
            flag = False
            if k >= 0:
                s = glyphs.dice(table[k][0], b); flag = risky(table, b, k, s, thin)
            items.append((b, k, flag))
    # rows top to bottom, each left to right; vertical writing: columns right to left, each top to bottom
    across = (lambda b: -(b[0] + b[2]) / 2) if vertical else (lambda b: -(b[1] + b[3]) / 2)
    along = (lambda b: -b[3]) if vertical else (lambda b: b[0])
    items.sort(key=lambda t: across(t[0]))
    rows, top = [], None
    for b, k, flag in items:
        c = across(b)
        if top is None or c - top > 6: rows.append([]); top = c
        rows[-1].append((b, k, flag))
    if info is not None:
        unknown = sum(k < 0 for _, k, _ in items) / max(1, len(items))
        big = tilt is not None and abs(tilt) > SKEW_HOLD_DEG
        info.update(skew=None if tilt is None else round(tilt, 3), turn=deg, unknown_share=round(unknown, 4),
                    held=unknown > HOLD or big)
    lines, flags = [], []
    for row in rows:
        line = ""
        for b, k, flag in sorted(row, key=lambda t: along(t[0])):
            line += "?" if k < 0 else table[k][1]
            if flag: flags.append(table[k][1])
        lines.append(line)
    return "\n".join(lines), flags
