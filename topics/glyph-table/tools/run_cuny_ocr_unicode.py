"""Run only the OCR->ToUnicode lane of CUNY AI Lab's pdf-accessibility-app on one PDF.

Usage: python run_cuny_ocr_unicode.py <path-to-pdf-accessibility-app> <in.pdf> <out.pdf> [tesseract languages, default eng]
Needs Tesseract and, in the venv, the versions pinned in that repo's backend/uv.lock:
pikepdf, pypdfium2, pdfminer.six, fonttools, pydantic, pydantic-settings.
Set LLM_BASE_URL=http://localhost:1/v1 so the settings check does not ask for an
LLM key; this lane never calls an LLM.
"""
import json, sys
from pathlib import Path
repo, src, out = sys.argv[1:4]
langs = sys.argv[4] if len(sys.argv) > 4 else "eng"
sys.path.insert(0, str(Path(repo) / "backend"))
import app  # noqa: F401  installs the PDFium guard first, as the repo's AGENTS.md requires
from app.pipeline.fonts.ocr_unicode import _recover_sync
ok, msg, stats = _recover_sync(Path(src), Path(out), langs, 300)
print(json.dumps({"ok": ok, "msg": msg, "stats": stats}, indent=1, default=str))
