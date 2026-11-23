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
