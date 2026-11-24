"""Self-made sample: three monthly statements in one fixed layout, in two variants.
Font: Liberation Sans Regular (SIL OFL 1.1). Every character, name and number is invented.
Usage: python make_sample.py <out-dir> [mode] [months] [jitter]
  outline: every character is a filled path; no font, no text in the PDF.
  outline-merged: the same shapes, but all glyphs of one printed line are a single path.
  outline-jitter: like outline, with seeded noise of +/- `jitter` pt added to every point
           (a stand-in for generators that round or wobble coordinates).
  font:    an embedded TrueType subset with every Unicode clue removed
           (no ToUnicode, no cmap table, no glyph names, codes in first-use order).
Options (after the positional arguments, all off by default):
  --font=PATH      another TrueType font (record its licence in LICENSES.md)
  --lang=ja        a Japanese statement (needs a font with Japanese glyphs)
  --tracking=PT    extra space after every character; negative = tighter than the font
  --rules=separate horizontal rules under every row, touching the descenders, as their own paths
  --rules=merged   the same rules inside the row's first text path (use with outline-merged)
  --quotes         add a line with straight quotes (" and ') to every month
  --prefix=NAME    file name prefix instead of the mode
  --vertical       (outline modes, Japanese) vertical writing: the same table turned so that
                   rows become columns (right to left), characters top to bottom, the font's
                   'vert' forms for ー、。「」（） etc. Half-width digits stay upright, one per cell.
  --tounicode-shift=N  (font mode) add a ToUnicode CMap that maps every glyph to the character N code
                   points above the right one ("the" -> "wkh" for N=3): a broken text layer that looks like text.
                   N=0 writes a correct ToUnicode (a normal, extractable text layer)
  --notes=N        (English) N lines of fixed self-made English sentences under the total (a longer page)
  --stable-codes   (font mode) keep each glyph's code from month to month; by default
                   every file numbers its glyphs afresh in first-use order, as print drivers do
Writes <out>/<prefix>-statement-2026-MM.pdf and <out>/<prefix>-truth-2026-MM.json (text and position of every character)."""
import json, random, sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

OPTS = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in sys.argv[1:] if a.startswith("--"))
sys.argv = [a for a in sys.argv if not a.startswith("--")]
FONT = OPTS.get("font", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
LANG = OPTS.get("lang", "en")
TRACKING = float(OPTS.get("tracking", 0))
RULES = OPTS.get("rules", "none")
QUOTES = "quotes" in OPTS
OUT = Path(sys.argv[1]); MODE = sys.argv[2] if len(sys.argv) > 2 else "outline"
PREFIX = OPTS.get("prefix", MODE)
MONTHS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
JITTER = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
NOISE = random.Random(7)
tt = TTFont(FONT); gs = tt.getGlyphSet(); cmap = tt.getBestCmap(); UPM = tt["head"].unitsPerEm
VERTICAL = "vertical" in OPTS
VERT = {}                       # glyph -> its vertical form (GSUB 'vert')
if VERTICAL:
    for fr in tt["GSUB"].table.FeatureList.FeatureRecord:
        if fr.FeatureTag == "vert":
            for li in fr.Feature.LookupListIndex:
                for st in tt["GSUB"].table.LookupList.Lookup[li].SubTable:
                    VERT.update(getattr(st, "mapping", None) or {})

class PdfPen(BasePen):
    def __init__(self, gs, s, x, y):
        super().__init__(gs); self.o = []; self.s, self.x, self.y = s, x, y; self.cur = None
    def p(self, pt):
        dx = NOISE.uniform(-JITTER, JITTER) if JITTER else 0.0
        dy = NOISE.uniform(-JITTER, JITTER) if JITTER else 0.0
        return f"{self.x + pt[0]*self.s + dx:.3f} {self.y + pt[1]*self.s + dy:.3f}"
    def _moveTo(self, pt): self.o.append(self.p(pt) + " m"); self.cur = pt
    def _lineTo(self, pt): self.o.append(self.p(pt) + " l"); self.cur = pt
    def _curveToOne(self, a, b, c): self.o.append(f"{self.p(a)} {self.p(b)} {self.p(c)} c"); self.cur = c
    def _qCurveToOne(self, a, b):  # exact quadratic -> cubic
        p0 = self.cur
        c1 = (p0[0] + 2/3*(a[0]-p0[0]), p0[1] + 2/3*(a[1]-p0[1]))
        c2 = (b[0] + 2/3*(a[0]-b[0]), b[1] + 2/3*(a[1]-b[1]))
        self._curveToOne(c1, c2, b)
    def _closePath(self): self.o.append("h")

USED = {}  # glyph name -> CID, in first-use order (like a print driver)
def draw_text(ops, truth, text, x, y, size):
    if MODE == "font":
        cids = []
        for ch in text:
            g = cmap[ord(ch)]
            cids.append(USED.setdefault(g, len(USED) + 1))
        ops.append(f"BT /F1 {size} Tf {x} {y} Td <" + "".join(f"{c:04X}" for c in cids) + "> Tj ET")
        truth.append({"text": text, "x": round(x, 2), "y": round(y, 2), "size": size, "chars": char_boxes(text, x, y, size)}); return
    global PENDING_RULE
    if VERTICAL: return draw_vertical(ops, truth, text, x, y, size)
    s = size / UPM; x0 = x; merged = []
    if PENDING_RULE: merged.append(PENDING_RULE); PENDING_RULE = None
    for ch in text:
        g = cmap[ord(ch)]
        if ch != " ":
            pen = PdfPen(gs, s, x, y); gs[g].draw(pen)
            if pen.o:
                if MODE == "outline-merged": merged += pen.o
                else: ops.append(" ".join(pen.o) + " f")
        x += tt["hmtx"][g][0] * s + TRACKING
    if merged: ops.append(" ".join(merged) + " f")
    truth.append({"text": text, "x": round(x0, 2), "y": round(y, 2), "size": size, "chars": char_boxes(text, x0, y, size)})
    return x

def draw_vertical(ops, truth, text, x, y, size):
    """The horizontal layout turned: row y becomes a column (right to left), x runs down the page."""
    s = size / UPM; cx, top = 555 - (790 - y), 800 - (x - 50); merged = []; chars = []
    for ch in text:
        g = cmap[ord(ch)]; g = VERT.get(g, g)
        adv = tt["hmtx"][g][0] * s; step = tt["vmtx"][g][0] * s
        if ch != " ":
            ox, base = cx - adv / 2, top - 0.88 * size
            pen = PdfPen(gs, s, ox, base); gs[g].draw(pen)
            if pen.o:
                if MODE == "outline-merged": merged += pen.o
                else: ops.append(" ".join(pen.o) + " f")
            chars.append([ch, round(ox, 3), round(adv, 3), round(base, 3), size])
        top -= step + TRACKING
    if merged: ops.append(" ".join(merged) + " f")
    truth.append({"text": text, "x": round(cx, 2), "y": round(800 - (x - 50), 2), "size": size, "chars": chars, "vertical": True})

def char_boxes(text, x, y, size):
    """[char, origin x, advance, baseline y, size] for every non-space character."""
    s = size / UPM; out = []
    for ch in text:
        adv = tt["hmtx"][cmap[ord(ch)]][0] * s
        if ch != " ": out.append([ch, round(x, 3), round(adv, 3), y, size])
        x += adv + TRACKING
    return out

PENDING_RULE = None
def rule(ops, y, x0=50, x1=545, t=0.6):
    """A horizontal rule drawn as a filled rectangle path (not `re`), at y..y+t."""
    global PENDING_RULE
    path = f"{x0} {y} m {x1} {y} l {x1} {y + t} l {x0} {y + t} l h"
    if RULES == "merged": PENDING_RULE = path
    elif RULES == "separate": ops.append(path + " f")

ITEMS = ["Paper A4 box", "Toner black", "Cable 2m", "Desk lamp", "Folder blue", "Stapler",
         "Ink red", "USB hub", "Chair mat", "Label roll", "Whiteboard", "Marker set"]
def code(r):  # look-alikes on purpose: 0/O, 1/l/I
    return "".join(r.choice("0O1lI") for _ in range(2)) + "-" + str(r.randint(100, 999))

def page(year, month, r, extra):
    ops, truth = [], []
    W, H = 595, 842
    draw_text(ops, truth, "MONTHLY STATEMENT (SAMPLE)", 50, 790, 16)
    draw_text(ops, truth, f"Period {year}-{month:02d}", 50, 765, 10)
    draw_text(ops, truth, "Account 4471-0098", 400, 765, 10)
    ops.append("0.5 w 50 740 m 545 740 l S")
    cols = [50, 120, 200, 420, 480]
    for cx, h in zip(cols, ["Date", "Code", "Item", "Qty", "Amount"]):
        draw_text(ops, truth, h, cx, 725, 9)
    y, total = 705, 0
    for i in range(14):
        qty = r.randint(1, 12); price = r.randint(80, 4800); amt = qty * price; total += amt
        row = [f"{month:02d}/{r.randint(1, 28):02d}", code(r), r.choice(ITEMS), str(qty), f"{amt:,}"]
        if RULES != "none": rule(ops, y - 1.6)
        for cx, t in zip(cols, row): draw_text(ops, truth, t, cx, y, 9)
        y -= 18
    for t in extra:  # characters seen rarely or only this month
        draw_text(ops, truth, t, 50, y, 9); y -= 18
    ops.append(f"0.5 w 50 {y+8} m 545 {y+8} l S")
    draw_text(ops, truth, "Total", 420, y - 8, 10); draw_text(ops, truth, f"{total:,}", 480, y - 8, 10)
    y -= 34
    for t in NOTES[:int(OPTS.get("notes", 0))]:
        draw_text(ops, truth, t, 50, y, 9); y -= 13
    return "\n".join(ops).encode(), truth

NOTES = ["Please check every line of this statement and tell us about any mistake within thirty days.",
         "Prices include the sales tax that applied on the date of delivery shown in the first column.",
         "Returned items are credited on the next statement once the warehouse has received them.",
         "Orders placed after five in the afternoon are packed and shipped on the following working day.",
         "Payment is due at the end of the month after the month in which the goods were delivered.",
         "We keep a copy of this statement for seven years and can send it again if you need it later.",
         "For questions about an item code, quote the code and the date exactly as they appear above.",
         "Thank you for your order; this sample statement was made by hand and lists no real business."]

ITEMS_JA = ["コピー用紙Ａ４", "トナー黒", "ケーブル２ｍ", "デスクライト", "ファイル青", "ホッチキス",
            "インク赤", "ＵＳＢハブ", "チェアマット", "ラベル", "ホワイトボード", "マーカー"]
LOOK_JA = "カ力ロ口ニ二エ工ハ八タ夕"          # katakana and the kanji that look like them
def code_ja(r):
    return "".join(r.choice(LOOK_JA) for _ in range(2)) + r.choice("ー一") + str(r.randint(100, 999))

def page_ja(year, month, r, extra):
    ops, truth = [], []
    draw_text(ops, truth, "月次明細書（サンプル）", 50, 790, 16)
    draw_text(ops, truth, f"期間 {year}年{month:02d}月", 50, 765, 10)
    draw_text(ops, truth, "口座 4471-0098", 400, 765, 10)
    ops.append("0.5 w 50 740 m 545 740 l S")
    cols = [50, 120, 200, 420, 480]
    for cx, h in zip(cols, ["日付", "品番", "品名", "数量", "金額"]):
        draw_text(ops, truth, h, cx, 725, 9)
    y, total = 705, 0
    for i in range(14):
        qty = r.randint(1, 12); price = r.randint(80, 4800); amt = qty * price; total += amt
        row = [f"{month:02d}/{r.randint(1, 28):02d}", code_ja(r), r.choice(ITEMS_JA), str(qty), f"{amt:,}"]
        if RULES != "none": rule(ops, y - 1.6)
        for cx, t in zip(cols, row): draw_text(ops, truth, t, cx, y, 9)
        y -= 18
    for t in extra:
        draw_text(ops, truth, t, 50, y, 9); y -= 18
    ops.append(f"0.5 w 50 {y+8} m 545 {y+8} l S")
    draw_text(ops, truth, "合計", 420, y - 8, 10); draw_text(ops, truth, f"{total:,}", 480, y - 8, 10)
    return "\n".join(ops).encode(), truth

EXTRA_JA = {m: ["備考：税込（８％）"] for m in range(1, 13)}
EXTRA_JA[1] = []
EXTRA_JA[3] = ["備考：税込（８％）", "参照 ＃Ｑ７（新しい品番）"]
EXTRA_JA[7] = ["備考：税込（１０％）", "振込 銀行（参照 Ｊ－２０２６）"]
EXTRA_JA[9] = ["備考：税込（１０％）", "返品 －１，２００（返品分）"]
EXTRA_JA[11] = ["備考：税込（１０％）", "次回訪問 １２月３日"]

def font_objs():
    import io
    from fontTools import subset
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    order = [".notdef"] + sorted(USED, key=USED.get)          # CID n -> glyph order[n]
    f = TTFont(FONT)
    opt = subset.Options(); opt.glyph_names = False; opt.notdef_outline = True
    opt.name_IDs = []; opt.layout_features = []; opt.hinting = False
    sub = subset.Subsetter(opt); sub.populate(glyphs=order); sub.subset(f)
    f.setGlyphOrder([g for g in f.getGlyphOrder()])
    # reorder glyphs so GID == CID, then strip every clue to the characters
    glyf = f["glyf"]; hmtx = f["hmtx"]
    new = {f"g{i}": (glyf[g], hmtx[g]) for i, g in enumerate(order)}
    names = list(new)
    f.setGlyphOrder(names); glyf.glyphOrder = names
    glyf.glyphs = {n: v[0] for n, v in new.items()}; hmtx.metrics = {n: v[1] for n, v in new.items()}
    f["maxp"].numGlyphs = len(names); f["hhea"].numberOfHMetrics = len(names)
    f["post"].formatType = 3.0
    keep = {"head", "hhea", "maxp", "hmtx", "glyf", "loca", "post", "name", "OS/2"}   # drawing only: no cmap,
    for t in [t for t in f.keys() if t not in keep and t != "GlyphOrder"]:              # no layout, no vertical
        del f[t]
    buf = io.BytesIO(); f.save(buf); data = buf.getvalue()
    widths = " ".join(str(round(tt["hmtx"][g][0] * 1000 / UPM)) for g in order[1:])
    shift = int(OPTS.get("tounicode-shift", 0))
    has_tu = "tounicode-shift" in OPTS
    tu = b" /ToUnicode 9 0 R" if has_tu else b""
    objs = [b"<< /Type /Font /Subtype /Type0 /BaseFont /ABCDEF+Sample /Encoding /Identity-H /DescendantFonts [6 0 R]" + tu + b" >>",
            b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /ABCDEF+Sample /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor 7 0 R /CIDToGIDMap /Identity /DW 500 /W [1 [" + widths.encode() + b"]] >>",
            b"<< /Type /FontDescriptor /FontName /ABCDEF+Sample /Flags 32 /FontBBox [-200 -300 1200 1000] /ItalicAngle 0 /Ascent 905 /Descent -212 /CapHeight 716 /StemV 80 /FontFile2 8 0 R >>",
            b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream"]
    if has_tu:
        rev = {}
        for u, g in cmap.items(): rev.setdefault(g, u)
        pairs = "".join(f"<{cid:04X}> <{rev[g] + shift:04X}>\n" for g, cid in sorted(USED.items(), key=lambda kv: kv[1]))
        cm = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CMapName /Shifted def /CMapType 2 def\n"
              "1 begincodespacerange <0000> <FFFF> endcodespacerange\n"
              f"{len(USED)} beginbfchar\n{pairs}endbfchar endcmap CMapName currentdict /CMap defineresource pop end end").encode()
        objs.append(b"<< /Length %d >>\nstream\n" % len(cm) + cm + b"\nendstream")
    return objs

def write_pdf(path, content):
    res = b"<< /Font << /F1 5 0 R >> >>" if MODE == "font" else b"<< >>"
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources " + res + b" /Contents 4 0 R >>",
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"]
    if MODE == "font": objs += font_objs()
    out = bytearray(b"%PDF-1.4\n"); offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out); out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs: out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    path.write_bytes(bytes(out))

OUT.mkdir(parents=True, exist_ok=True)
EXTRA = {1: [], 2: ["Note: rate 8% applies"], 3: ["Note: rate 8% applies", "Ref #Q7 (new code)"]}
# months 4-12: mostly the same notes, a few new characters now and then
for m in range(4, 13): EXTRA[m] = ["Note: rate 8% applies"]
EXTRA[5] = ["Note: rate 8% applies", "Ref #Q7 (new code)"]
EXTRA[7] = ["Note: rate 10% applies", "Paid via Bank (ref J-2026)"]
EXTRA[9] = ["Note: rate 10% applies", "Credit: -1,200 (returned item)"]
EXTRA[11] = ["Note: rate 10% applies", "Ref #Q7; next visit Dec. 3rd"]
QUOTE_LINE = 'Item "Desk lamp" isn\'t listed' if LANG == "en" else "品名「デスクライト」は'未掲載'"
for m in range(1, MONTHS + 1):
    r = random.Random(2026 * 100 + m)
    if "stable-codes" not in OPTS: USED.clear()
    extra = (EXTRA_JA if LANG == "ja" else EXTRA)[m] + ([QUOTE_LINE] if QUOTES else [])
    content, truth = (page_ja if LANG == "ja" else page)(2026, m, r, extra)
    if VERTICAL:   # the horizontal layout's stroked rules would cut across the columns
        content = b"\n".join(l for l in content.split(b"\n") if not l.endswith(b" S"))
    write_pdf(OUT / f"{PREFIX}-statement-2026-{m:02d}.pdf", content)
    meta = {"self_made": True, "mode": MODE, "font": "Liberation Sans Regular (SIL OFL 1.1)" if "font" not in OPTS else Path(FONT).name}
    if len(OPTS): meta["options"] = OPTS
    (OUT / f"{PREFIX}-truth-2026-{m:02d}.json").write_text(json.dumps({**meta, "lines": truth}, indent=1, ensure_ascii=False))
print("ok")
