# docling runs: key to the folders

docling 2.152.0, docling-parse 7.27.1, Tesseract 5.3.4, Claude Code cloud (x86_64), 2026-11-24.
Each run folder has `run.json` (options, package versions, sha256 of every input PDF, per-page `parse_score`, where 0.0 = the text layer was judged broken, the auto OCR engine log, and any errors) and the exported text (`*.txt`), except where noted.
Scored totals are in `summary.json` of each round; keys ending in `(strip)` are scored with Markdown table rules removed (the pre-registered scoring from round 2 on).
Samples are self-made by `../../../samples/make_sample.py` (12 months; months 2–12 are scored against the generator's truth files). Scoring: `../../../tools/score_text.py`, `../../../tools/summarize_docling.py`. Runner: `../../../tools/run_docling.py`.
Pre-registrations: `../../preregistration-docling-2026-11.md`, `../../preregistration-docling2-2026-11.md`, `../../preregistration-docling3-2026-11.md`. Full write-up (Japanese): `../../docling-2026-11.md`.

## Samples
| Name | Font / text layer |
| --- | --- |
| `font-statement-*` (EN), `ja-font-statement-*` (JA) | Type0 / Identity-H, no ToUnicode, embedded TrueType without cmap table or glyph names; one page (table only) |
| `shift3-font-*` | as EN, plus a ToUnicode mapping every glyph 3 code points too high, the space included (space → `#`) |
| `shift3ks-font-*` | as `shift3-font`, but the space stays a space (added after pre-registration) |
| `long-none-*`, `long-good-*`, `long-shift3-*`, `long-shift3ks-*` | EN with 8 more lines of English sentences under the table; no ToUnicode / correct ToUnicode / shifted incl. space / shifted, space kept (the last added after pre-registration) |
| `mixed-*` | two pages: `long-good` then `long-none` |

## Round 1 (this folder's top level; `summary.json` here is round 1)
- `default-en`, `default-ja`: `DocumentConverter()` with no options.
- `fullocr-{en,ja}-r{1,2}`: `force_full_page_ocr=True` with Tesseract (the workaround given in docling #2963).
- `glyph-table/`: this repository's own method on the same PDFs after Ghostscript `-dNoOutputFonts` (for comparison).

## Round 2 (`round2/`)
- `replace-auto-*`: `OcrAutoOptions(lang=[...], replace_broken_text_layer=True)`; the engine picked was RapidOCR (torch). `replace-auto-ja-r1`: errors only (no engine for `ja`).
- `replace-tess-*`: `TesseractCliOcrOptions(lang=[eng|jpn], replace_broken_text_layer=True)`, scale 3.0 unless the name ends in `-s2.0` / `-s4.0`.
- `-en`, `-ja`: short EN / JA samples; `-shift`: `shift3-font`; `-r1`, `-r2`: two runs.
- `control-auto`, `control-tess`: original Statistics Bureau "Population Estimates" monthly PDFs, Jan–Nov 2026 (good text layer); only `run.json` kept; pages 1–5 counted.

## Round 3 (`round3/`)
- `D-*`: default engine (as `replace-auto`); `T-*`: Tesseract scale 3.0 (as `replace-tess`).
- `D-long-*`, `T-long-*`, `D-mixed`, `T-mixed`: the long and mixed samples above.
- `D-en-public`: docling's own `tests/data/pdf/sources/*.pdf` at commit `311b683` (17 files, right-to-left ones left out; mixed languages); only `run.json` kept.
- `E-en`, `E-ja`: default engine in a copy of the environment with `easyocr` installed (it picks EasyOCR).
- `X-*`: the space-kept shifted samples (added after pre-registration); `X-long-shiftks-tess` with Tesseract.
