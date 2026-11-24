"""Run docling on PDFs and save plain text, for results/preregistration-docling-2026-11.md.

Usage: python run_docling.py <arm> <out-dir> <lang> <pdf>... [--scale=S]
  arm  default : DocumentConverter() with no options
       fullocr : do_ocr, TesseractCliOcrOptions(force_full_page_ocr=True, lang=[lang]),
                 images_scale=2.0, do_table_structure=False (the workaround in docling #2963)
       replace-auto : default pipeline, OcrAutoOptions(lang=[lang], replace_broken_text_layer=True)
       replace-tess : default pipeline, TesseractCliOcrOptions(lang=[lang], replace_broken_text_layer=True,
                      scale=S, default 3.0)
  lang: en/ja for replace-auto, eng/jpn for the Tesseract arms.
Per page, run.json records parse_score (0.0 = text layer judged broken when the option is on).
Writes <out-dir>/<pdf stem>.txt and <out-dir>/run.json (versions, options, sha256, errors).
A conversion that raises or returns empty text is recorded in run.json, never as an empty score.
"""
import hashlib, json, logging, sys, time, platform
from importlib.metadata import version
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions, OcrAutoOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

class _Keep(logging.Handler):   # keep the auto OCR model's choice of engine
    msgs = []
    def emit(self, r): self.msgs.append(r.getMessage())
_lg = logging.getLogger("docling.models.stages.ocr.auto_ocr_model"); _lg.setLevel(logging.INFO); _lg.addHandler(_Keep())

SCALE = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--scale=")), 3.0))
sys.argv = [a for a in sys.argv if not a.startswith("--scale=")]
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
elif arm in ("replace-auto", "replace-tess"):
    po = PdfPipelineOptions()
    if arm == "replace-auto":
        po.ocr_options = OcrAutoOptions(lang=[lang], replace_broken_text_layer=True)
    else:
        po.ocr_options = TesseractCliOcrOptions(lang=[lang], replace_broken_text_layer=True, scale=SCALE)
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=po)})
    opts = {"ocr": type(po.ocr_options).__name__, **po.ocr_options.model_dump(mode="json")}
else:
    sys.exit("arm must be default, fullocr, replace-auto or replace-tess")

rec = {"arm": arm, "options": opts, "date": time.strftime("%Y-%m-%d %H:%M:%S"),
       "python": platform.python_version(), "versions": {}, "files": []}
for pkg in ("docling", "docling-core", "docling-parse", "docling-ibm-models"):
    try: rec["versions"][pkg] = version(pkg)
    except Exception: rec["versions"][pkg] = None
for p in map(Path, pdfs):
    item = {"pdf": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    t0 = time.time()
    try:
        res = conv.convert(str(p))
        text = res.document.export_to_text()
        item["parse_score"] = {str(k): v.parse_score for k, v in res.confidence.pages.items()}
        (out / (p.stem + ".txt")).write_text(text, encoding="utf-8")
        item["chars"] = len(text)
        if not text.strip(): item["flag"] = "empty"
    except Exception as e:
        item["flag"] = "error"; item["error"] = repr(e)[:500]
    item["seconds"] = round(time.time() - t0, 1)
    rec["files"].append(item)
    print(p.name, item.get("flag", "ok"), item.get("chars"), item["seconds"], flush=True)
rec["auto_ocr_log"] = sorted(set(_Keep.msgs))
(out / "run.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
