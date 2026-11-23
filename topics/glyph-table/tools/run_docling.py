"""Run docling on PDFs and save plain text, for results/preregistration-docling-2026-11.md.

Usage: python run_docling.py <arm> <out-dir> <lang> <pdf>...
  arm  default : DocumentConverter() with no options
       fullocr : do_ocr, TesseractCliOcrOptions(force_full_page_ocr=True, lang=[lang]),
                 images_scale=2.0, do_table_structure=False (the workaround in docling #2963)
Writes <out-dir>/<pdf stem>.txt and <out-dir>/run.json (versions, options, sha256, errors).
A conversion that raises or returns empty text is recorded in run.json, never as an empty score.
"""
import hashlib, json, sys, time, platform
from importlib.metadata import version
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

arm, out, lang, pdfs = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4:]
out.mkdir(parents=True, exist_ok=True)

if arm == "default":
    conv = DocumentConverter()
    opts = {}
elif arm == "fullocr":
    po = PdfPipelineOptions()
    po.do_ocr = True
    po.do_table_structure = False
    po.images_scale = 2.0
    po.generate_page_images = True
    po.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True, lang=[lang])
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=po)})
    opts = {"do_ocr": True, "do_table_structure": False, "images_scale": 2.0,
            "ocr": "TesseractCliOcrOptions", "force_full_page_ocr": True, "lang": [lang]}
else:
    sys.exit("arm must be default or fullocr")

rec = {"arm": arm, "options": opts, "date": time.strftime("%Y-%m-%d %H:%M:%S"),
       "python": platform.python_version(), "versions": {}, "files": []}
for pkg in ("docling", "docling-core", "docling-parse", "docling-ibm-models"):
    try: rec["versions"][pkg] = version(pkg)
    except Exception: rec["versions"][pkg] = None
for p in map(Path, pdfs):
    item = {"pdf": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    t0 = time.time()
    try:
        text = conv.convert(str(p)).document.export_to_text()
        (out / (p.stem + ".txt")).write_text(text, encoding="utf-8")
        item["chars"] = len(text)
        if not text.strip(): item["flag"] = "empty"
    except Exception as e:
        item["flag"] = "error"; item["error"] = repr(e)[:500]
    item["seconds"] = round(time.time() - t0, 1)
    rec["files"].append(item)
    print(p.name, item.get("flag", "ok"), item.get("chars"), item["seconds"], flush=True)
(out / "run.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
