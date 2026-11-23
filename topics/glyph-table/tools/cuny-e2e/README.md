# CUNY pdf-accessibility-app, end to end

How the numbers in `results/oss-evaluation-2026-11.md` section 2b were produced. Nothing here holds a key or private data.

1. Clone the app at `8213721` into `$E2E/cuny`, `uv sync` in `backend/`, install veraPDF at `/opt/verapdf/verapdf`.
2. Start an LLM endpoint the app can call:
   - `python stub.py <port> <log>`: always fails (no LLM).
   - `SCOREBOOK_API_KEY=... python adapter.py <port> claude-haiku-5-5 <log.jsonl> <cap-usd>`: forwards OpenAI-style chat calls to the Claude Messages API and refuses once the logged spend reaches the cap.
3. `E2E=... MODEL=claude-haiku-5-5 ./runbench.sh <port> <pdf-dir> <out-log> [jpn+eng]` runs the app's own `scripts/corpus_benchmark.py --profile full`.
4. Score:
   - `score_synthetic.py`: self-made samples, using the app's screen-reader text.
   - `score_public.py`: the public report, using the app's screen-reader text.
   - `score_public_pdfminer.py`: the public report, using the glyphs in the output, split by pages with a text review task.
5. `check_pdfium_single_glyph.py <ocrmypdf-output.pdf>` shows pdfium skipping one-glyph `Tj` operators in OCRmyPDF's `Occulta` font.
   - `results/oss/cuny-e2e/pdfium-single-glyph-ja-2026-02.txt`: OCRmyPDF 17.4.0 (CUNY's lock), pdfium 361 / pdfminer 377.
   - `results/oss/cuny-e2e/pdfium-single-glyph-ja-2026-02-ocrmypdf17.13.0.txt`: same check after `uv lock --upgrade-package ocrmypdf` (17.13.0), 377 / 377. The OCRmyPDF version is only in the file name; the script does not print it.
6. OCRmyPDF 17.13.0 rerun (2026-11-23): bump the lock as above, `uv sync --frozen --extra local-docling --extra dev`, then steps 3–4 again. Restore with the original `uv.lock` and the same `uv sync`.
