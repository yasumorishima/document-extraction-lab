"""Read filled glyph shapes from a PDF page and turn each into a small bitmap.

Standard library only. One page, one uncompressed or Flate-compressed content
stream. Handles `q`/`Q`/`cm` (as Ghostscript writes), filled paths `f`/`f*`/`F`,
and paths that hold several glyphs: the subpaths of one fill are split into
glyphs by horizontal overlap (subpaths whose x-ranges overlap belong together,
so the dot of an "i" stays with its stem). Strokes (`S`) are ignored.
Not handled: glyphs that overlap horizontally inside one path (tight kerning),
characters made of side-by-side pieces in one path (such as a double quote),
text in Form XObjects, images.
"""
import re, zlib

NUM = rb"[-+]?(?:\d+\.?\d*|\.\d+)"
TOKEN = re.compile(rb"(%s)|([A-Za-z*'\"]+)" % NUM)   # "re", "f*", "B*" etc. are single tokens

def page_content(path):
    data = open(path, "rb").read()
    m = re.search(rb"/Contents\s+(\d+)\s+0\s+R", data)
    obj = re.search(rb"\n%s 0 obj\s*<<(.*?)>>\s*stream\r?\n" % m.group(1), data, re.S)
    lm = re.search(rb"/Length\s+(\d+)(\s+\d+\s+R)?", obj.group(1))
    if lm.group(2):                                   # indirect length: "/Length 7 0 R"
        lm2 = re.search(rb"\n%s 0 obj\s*(\d+)" % lm.group(1), data)
        length = int(lm2.group(1))
    else:
        length = int(lm.group(1))
    raw = data[obj.end():obj.end() + length]
    return zlib.decompress(raw) if b"FlateDecode" in obj.group(1) else raw

class Fill(list):
    """The subpaths of one filled path, with its fill rule (even-odd for `f*`)."""
    evenodd = False

def _mul(m, n):
    a, b, c, d, e, f = m; A, B, C, D, E, F = n
    return (a*A + b*C, a*B + b*D, c*A + d*C, c*B + d*D, e*A + f*C + E, e*B + f*D + F)

def filled_paths(content):
    """Yield glyphs: each filled path split by horizontal overlap (see split_glyphs)."""
    for fl in filled_paths_raw(content):
        for g in split_glyphs([s for s in fl if not is_rule(s)]):
            g = Fill(g); g.evenodd = fl.evenodd; yield g

def filled_paths_raw(content):
    """Yield each filled path as a list of subpaths; a subpath is a list of (x, y) in page space."""
    stack, subs, cur = [], [], []
    start = None                                     # start of the current subpath (in page space)
    ctm, saved = (1, 0, 0, 1, 0, 0), []
    def T(x, y):
        a, b, c, d, e, f = ctm
        return (a*x + c*y + e, b*x + d*y + f)
    def curve(p0, p1, p2, p3):
        for i in range(1, 9):                           # flatten the Bézier
            t = i / 8; u = 1 - t
            cur.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                        u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    for num, op in TOKEN.findall(content):
        if num:
            stack.append(float(num)); continue
        if op in (b"l", b"c", b"v", b"y") and not cur and start is not None:
            cur = [start]                               # after "h" the current point is the subpath's start
        if op == b"q": saved.append(ctm)
        elif op == b"Q": ctm = saved.pop() if saved else ctm
        elif op == b"cm" and len(stack) >= 6: ctm = _mul(tuple(stack[-6:]), ctm)
        elif op == b"m":
            if cur: subs.append(cur)
            start = T(stack[-2], stack[-1]); cur = [start]
        elif op == b"l" and cur:
            cur.append(T(stack[-2], stack[-1]))
        elif op == b"c" and cur:
            curve(cur[-1], T(*stack[-6:-4]), T(*stack[-4:-2]), T(*stack[-2:]))
        elif op == b"v" and cur:                        # first control point = current point
            curve(cur[-1], cur[-1], T(*stack[-4:-2]), T(*stack[-2:]))
        elif op == b"y" and cur:                        # second control point = end point
            p3 = T(*stack[-2:]); curve(cur[-1], T(*stack[-4:-2]), p3, p3)
        elif op == b"re" and len(stack) >= 4:
            if cur: subs.append(cur)
            x, y, w, h = stack[-4:]
            subs.append([T(x, y), T(x + w, y), T(x + w, y + h), T(x, y + h)]); cur = []; start = T(x, y)
        elif op == b"h":
            if cur: subs.append(cur); cur = []
        elif op in (b"f", b"F", b"f*"):
            if cur: subs.append(cur); cur = []
            if subs:
                fl = Fill(subs); fl.evenodd = op == b"f*"; yield fl
            subs = []; start = None
        elif op in (b"S", b"s", b"n", b"B", b"B*", b"b", b"b*"):
            subs, cur, start = [], [], None
        stack = []

def split_glyphs(subs):
    """Split one fill's subpaths into glyphs: subpaths whose x-ranges overlap stay together."""
    if not subs: return
    spans = sorted(((min(x for x, _ in s), max(x for x, _ in s), s) for s in subs), key=lambda t: t[0])
    group, right = [spans[0][2]], spans[0][1]
    for x0, x1, s in spans[1:]:
        if x0 < right - 1e-6: group.append(s); right = max(right, x1)
        else: yield group; group, right = [s], x1
    yield group

def bitmap(subs, scale=8.0, evenodd=None):
    """Rasterise with the non-zero rule (even-odd if `evenodd`, or if `subs` is a Fill
    from an `f*` path). Returns (x0, y0, x1, y1, width, height, rows)."""
    if evenodd is None: evenodd = getattr(subs, "evenodd", False)
    xs = [x for s in subs for x, _ in s]; ys = [y for s in subs for _, y in s]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    w = max(1, round((x1 - x0) * scale)); h = max(1, round((y1 - y0) * scale))
    edges = []
    for s in subs:
        for (ax, ay), (bx, by) in zip(s, s[1:] + s[:1]):
            if ay != by: edges.append((ax, ay, bx, by))
    rows = []
    for r in range(h):
        y = y1 - (r + 0.5) / scale
        xs_w = []
        for ax, ay, bx, by in edges:
            if (ay <= y < by) or (by <= y < ay):
                xs_w.append((ax + (y - ay) * (bx - ax) / (by - ay), 1 if by > ay else -1))
        xs_w.sort(); bits = 0; wind = 0; prev = None
        for x, d in xs_w:
            if (wind % 2 if evenodd else wind) != 0 and prev is not None:
                a = max(0, round((prev - x0) * scale)); b = min(w, round((x - x0) * scale))
                for c in range(a, b): bits |= 1 << c
            wind += d; prev = x
        rows.append(bits)
    return (x0, y0, x1, y1, w, h, rows)

SIZE_TOL = 1      # px: bigger width/height differences mean "not the same glyph" (set by the caller)

def _overlap(ra, rb, dx):
    if dx > 0: rb = [r << dx for r in rb]
    elif dx < 0: rb = [r >> -dx for r in rb]
    return sum(bin(p & q).count("1") for p, q in zip(ra, rb))

def dice(a, b):
    """Overlap of two glyph bitmaps (1.0 = identical).

    Glyphs whose width or height differ by more than SIZE_TOL px score 0.
    Otherwise the bitmaps are bottom-left aligned and also tried shifted by one
    pixel in each direction; the best overlap counts (rounding of positions moves
    a glyph's pixels by up to a pixel).
    """
    _, _, _, _, wa, ha, ra = a; _, _, _, _, wb, hb, rb = b
    if abs(wa - wb) > SIZE_TOL or abs(ha - hb) > SIZE_TOL: return 0.0
    tot = sum(bin(p).count("1") for p in ra) + sum(bin(q).count("1") for q in rb)
    if not tot: return 1.0
    H = max(ha, hb) + 2
    A = [0] * (H - ha) + ra
    best = 0
    for dy in (-1, 0, 1):
        B = [0] * (H - hb + dy) + rb + [0] * max(0, -dy)
        B = B[len(B) - H:] if len(B) > H else [0] * (H - len(B)) + B
        for dx in (-1, 0, 1):
            best = max(best, _overlap(A, B, dx))
    return 2 * best / tot

def is_rule(sub, long=20.0, thin=1.5):
    """A table rule drawn as a thin, long filled rectangle (not a glyph)."""
    xs = [x for x, _ in sub]; ys = [y for _, y in sub]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    return (w >= long and h <= thin) or (h >= long and w <= thin)

def page_fills(path):
    """Every filled path of the page as a list of subpaths, table rules removed.
    Returns (fills, number of rules removed)."""
    fills, rules = [], 0
    for fl in filled_paths_raw(page_content(path)):
        keep = Fill(s for s in fl if not is_rule(s)); keep.evenodd = fl.evenodd
        rules += len(fl) - len(keep)
        if keep: fills.append(keep)
    return fills, rules

def page_glyphs(path, scale=8.0):
    return [bitmap(s, scale) for s in filled_paths(page_content(path))]
