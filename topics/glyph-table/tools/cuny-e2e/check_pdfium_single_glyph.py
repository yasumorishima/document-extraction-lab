"""Does pdfium read a text-show operator that draws exactly one glyph?

For an OCRmyPDF output page: count non-space characters as pdfium reads them and as pdfminer reads them,
then, for each font of the OCR text layer, put one glyph alone (and two glyphs together) into the layer
and see what pdfium reads. Usage: python check_pdfium_single_glyph.py <ocrmypdf-output.pdf> [page]
Needs pikepdf, pypdfium2, pdfminer.six."""
import io, sys
import pikepdf, pypdfium2 as pdfium
from pdfminer.high_level import extract_text
path = sys.argv[1]; page = int(sys.argv[2]) if len(sys.argv) > 2 else 0
dense = lambda s: "".join(c for c in s if not c.isspace())
print("pypdfium2", pdfium.version.PYPDFIUM_INFO, "pdfium", pdfium.version.PDFIUM_INFO)
print("page chars  pdfium:", len(dense(pdfium.PdfDocument(path)[page].get_textpage().get_text_range())),
      " pdfminer:", len(dense(extract_text(path, page_numbers=[page]))))
def layer(pdf):
    pg = pdf.pages[page]
    for operands, op in pikepdf.parse_content_stream(pg):
        if str(op) == "Do":
            x = pg.Resources.XObject[str(operands[0])]
            if x.Subtype == "/Form" and "/Font" in x.get("/Resources", {}): return pg, x, str(operands[0])
    raise SystemExit("no form XObject with fonts on this page")
def read(body):
    pdf = pikepdf.open(path); pg, x, name = layer(pdf)
    x.write(body.encode()); pg.Contents = pdf.make_stream(f"q {name} Do Q".encode())
    b = io.BytesIO(); pdf.save(b); return pdfium.PdfDocument(b.getvalue())[0].get_textpage().get_text_range()
pdf = pikepdf.open(path); _, x, _ = layer(pdf)
for fname, font in x.Resources.Font.items():
    print(f"font {fname} {font.get('/BaseFont')}")
    for show in ("<0001> Tj", "<0001> Tj 10 0 Td <0002> Tj", "<00010002> Tj"):
        print(f"   {show:32s} -> pdfium reads {read(f'BT 3 Tr {fname} 8 Tf 100 100 Td {show} ET')!r}")
