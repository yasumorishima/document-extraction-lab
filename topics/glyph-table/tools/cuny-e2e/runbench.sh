#!/bin/sh
# Run the CUNY app's own corpus benchmark (full pipeline, sqlite) on a folder of PDFs, with the app's LLM pointed at a local endpoint.
# usage: E2E=<work-dir with cuny/ clone> runbench.sh <port> <pdf-dir> <out-log> [ocr-language]
# MODEL=<model id> is passed as LLM_MODEL (only a label for the adapter). veraPDF is expected at /opt/verapdf/verapdf.
cd "$E2E/cuny/backend" || exit 1
export PATH=/opt/verapdf:$PATH LLM_BASE_URL=http://127.0.0.1:$1/v1 LLM_API_KEY=stub LLM_MODEL=${MODEL:-stub} VERAPDF_PATH=/opt/verapdf/verapdf OMP_THREAD_LIMIT=1
[ -n "$4" ] && export OCR_LANGUAGE=$4
.venv/bin/python scripts/corpus_benchmark.py --profile full --no-default-roots --root "$2" > "$3" 2>&1
