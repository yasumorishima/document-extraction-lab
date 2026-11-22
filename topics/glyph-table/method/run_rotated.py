"""Rotated text: what the glyph table does when the drawing is turned.

Each month's page (a self-made outline sample, one glyph per fill) is wrapped in
`q <rotation> cm ... Q`, i.e. the same drawing turned by an angle; nothing else
changes. Two tables are tried:
  same:    the table is built from the turned month 1 (the person confirms the
           turned glyphs; labels come from the upright month 1 fill by fill)
  upright: the table is built from the upright month 1, and turned pages are read
Months 2-12 are scored glyph by glyph: every fill is matched alone and its
answer compared with the confirmed character of the same fill, so reading
order does not matter. read()'s text is also scored order-free (score_text.bag)
and in order (score_text.score) to show what happens to the reading order.

Usage: python run_rotated.py <gen-dir> <prefix> <months> <out.json> [angles...]
       angles in degrees, counter-clockwise, default 0 1 3 90 180 270
"""
import json, math, sys, tempfile, time
from pathlib import Path
here = Path(__file__).parent
sys.path.insert(0, str(here)); sys.path.insert(0, str(here.parent / "tools"))
import glyphs, read_page, pick_threshold
from score_text import score, bag

W, H = 595, 842

def matrix(deg):
    if deg % 360 == 90:  return (0, 1, -1, 0, H, 0), (0, 0, H, W)
    if deg % 360 == 180: return (-1, 0, 0, -1, W, H), (0, 0, W, H)
    if deg % 360 == 270: return (0, -1, 1, 0, 0, W), (0, 0, H, W)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg)); cx, cy = W / 2, H / 2
    return (c, s, -s, c, cx - (c * cx - s * cy), cy - (s * cx + c * cy)), (0, 0, W, H)

def write_pdf(path, content, box):
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [%d %d %d %d] /Resources << >> /Contents 4 0 R >>" % box,
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"]
    out = bytearray(b"%PDF-1.4\n"); offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out); out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs: out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    path.write_bytes(bytes(out))

def turned(src, deg, dst):
    m, box = matrix(deg)
    cm = " ".join(f"{v:.6f}" for v in m).encode()
    write_pdf(dst, b"q " + cm + b" cm\n" + glyphs.page_content(src) + b"\nQ", box)
    return dst

def labels(pdf, truth, with_size=False):
    """The confirmed character of every fill, in fill order (upright page)."""
    gl, stray, per_fill = read_page.labelled_glyphs(pdf, truth, with_size)
    fills, _ = glyphs.page_fills(pdf)
    assert stray == 0 and len(gl) == len(fills) and set(per_fill) == {1}, "needs one glyph per fill"
    return [c for _, c in gl]

def labelled_turned(pdf_turned, lab):
    fills, _ = glyphs.page_fills(pdf_turned)
    assert len(fills) == len(lab)
    return [(glyphs.bitmap(f), c) for f, c in zip(fills, lab)]

def build_from(gl, th):
    t = read_page.Table()
    for b, c in gl: read_page.add(t, b, c, th)
    return t

def pick_from(gl_sized):
    """pick_threshold.pick on given labelled glyphs (labelled_glyphs swapped for the call)."""
    orig = read_page.labelled_glyphs
    read_page.labelled_glyphs = lambda *a, **k: (gl_sized, 0, [1])
    try: return pick_threshold.pick(None, None)
    finally: read_page.labelled_glyphs = orig

def per_glyph(table, pdf, lab, th):
    fills, _ = glyphs.page_fills(pdf)
    right = wrong = unk = 0; wrong_pairs = {}
    for f, c in zip(fills, lab):
        k, _ = read_page._match(table, glyphs.bitmap(f), th)
        if k < 0: unk += 1
        elif read_page.same_char(table[k][1], c): right += 1
        else:
            wrong += 1; p = f"{c}->{table[k][1]}"; wrong_pairs[p] = wrong_pairs.get(p, 0) + 1
    return right, wrong, unk, wrong_pairs

def main():
    gen, prefix, n, out = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), Path(sys.argv[4])
    angles = [float(a) for a in sys.argv[5:]] or [0, 1, 3, 90, 180, 270]
    months = [f"2026-{m:02d}" for m in range(1, n + 1)]
    pdf = lambda m: gen / f"{prefix}-statement-{m}.pdf"
    truth = lambda m: gen / f"{prefix}-truth-{m}.json"
    lab = {m: labels(pdf(m), truth(m)) for m in months}
    lab_sized = labels(pdf(months[0]), truth(months[0]), with_size=True)
    th_up, det_up = pick_threshold.pick(pdf(months[0]), truth(months[0])); tol_up = glyphs.SIZE_TOL
    table_up = read_page.build(pdf(months[0]), truth(months[0]), th_up)
    res = {"prefix": prefix, "months_read": months[1:], "upright_threshold": det_up}
    tmp = Path(tempfile.mkdtemp())
    for deg in angles:
        t0 = time.time()
        tp = {m: turned(pdf(m), deg, tmp / f"{prefix}-{deg:g}-{m}.pdf") for m in months}
        gl1 = labelled_turned(tp[months[0]], lab_sized)
        th, det = pick_from(gl1); tol = glyphs.SIZE_TOL
        table_same = build_from([(b, c[0]) for b, c in gl1], th)
        r = {"same_table": {"threshold": det, "groups": len(table_same),
                            "ambiguous_groups": [sorted(e[3]) for e in table_same if len(e[3]) > 1]},
             "upright_table": {"groups": len(table_up)}}
        for name, table, t, st in (("same_table", table_same, th, tol), ("upright_table", table_up, th_up, tol_up)):
            glyphs.SIZE_TOL = st
            share = []
            tot = [0, 0, 0]; pairs = {}; bg = {"short": 0, "over": 0, "unassigned": 0}; sq = {"correct": 0, "substituted": 0, "missing": 0, "extra": 0}
            for m in months[1:]:
                a, b, c, wp = per_glyph(table, tp[m], lab[m], t)
                tot[0] += a; tot[1] += b; tot[2] += c
                share.append(c / (a + b + c))
                for p, k in wp.items(): pairs[p] = pairs.get(p, 0) + k
                text, _ = read_page.read(tp[m], table, t, orient=False)   # the v5 measurement: no turning back
                g = bag(text, truth(m), nfkc=True)
                for k in bg: bg[k] += g[k]
                s = score(text, truth(m), nfkc=True)
                for k in sq: sq[k] += s["counts"].get(k, 0)
            r[name].update({"glyphs_right": tot[0], "glyphs_wrong": tot[1], "glyphs_unknown": tot[2],
                            "unknown_share_min_max": [round(min(share), 3), round(max(share), 3)],
                            "wrong_pairs": dict(sorted(pairs.items(), key=lambda kv: -kv[1])[:10]),
                            "text_order_free": bg, "text_in_order": sq})
        r["seconds"] = round(time.time() - t0, 1)
        res[f"{deg:g} deg"] = r
        print(f"{prefix} {deg:g}: same {r['same_table']['glyphs_right']}/{r['same_table']['glyphs_wrong']}/{r['same_table']['glyphs_unknown']}"
              f"  upright {r['upright_table']['glyphs_right']}/{r['upright_table']['glyphs_wrong']}/{r['upright_table']['glyphs_unknown']}"
              f"  ({r['seconds']}s)", file=sys.stderr, flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")

if __name__ == "__main__":
    main()
