# Pre-registration: docling on PDFs whose font has no Unicode information (2026-11-24)

Written and committed before any docling run. Frozen once committed; results go in a separate file.

## Why
docling issue #2963 (open, no maintainer reply as of 2026-11-24) and the related #2170, #3081 and #3582: PDFs whose fonts carry no ToUnicode map come out as garbage (`/31 /8 ...`, `GLYPH<...>`, shifted letters). The workaround given in the issue, and the only route named in its comments, is full-page OCR (`force_full_page_ocr=True` with Tesseract). Our earlier runs (`evaluation-2026-11.md`) show that Tesseract full-page OCR, through OCRmyPDF, silently swaps look-alikes (O→0, l→1). Not yet measured: whether docling's own full-page OCR does the same.

## Samples (self-made, `samples/make_sample.py`)
- EN: `font` mode, Liberation Sans, 12 months (an embedded TrueType subset with no ToUnicode, no cmap table, no glyph names). Months 2–12 are scored (5,259 characters, as in the main evaluation).
- JA: `font` mode with `--lang=ja --font=ipag.ttf --prefix=ja-font`, 12 months, months 2–12 scored.
- Difference from the issue: the issue's fonts are Type0/CID (Identity-H); ours is a simple TrueType font. Both have no Unicode clue. Stated as such in the write-up.

## Arms
- A0 do-nothing: empty text for every page (checks that the scorer counts it as all missing, 0 extra).
- A1 docling default conversion (no options), text = `export_to_text()`.
- A2 docling, the issue's workaround: `do_ocr=True`, `TesseractCliOcrOptions` with `force_full_page_ocr=True`, `images_scale=2.0`, `do_table_structure=False`, lang `eng` (EN) / `jpn` (JA). Run twice.
- Reference (already measured, not re-run): glyph table on the Ghostscript-outlined EN font PDFs (`gs-outline`, 0 silent errors months 2–12) and OCRmyPDF + Tesseract on the same (`results/ocrmypdf-12m/`).

## Measure
`tools/score_text.py` as in the main evaluation (EN strict; JA `--nfkc`). Main number: silent errors = extra/wrong characters. Beside it: missing characters, and the substitution pairs, split into digits, Latin letters, kana, kanji, punctuation. Settings recorded: docling, docling-parse and Tesseract versions, options, sha256 of each input PDF, tool commit, date. A run that errors or returns empty text is flagged and counted, not scored as 0.

## What would count as a finding (decided now)
- F1: A2 has more than 0 silent errors on EN months 2–12, with at least one look-alike pair among them (O/0, I/l/1, and so on). If A2 has 0, we report that docling's OCR route does not reproduce the OCRmyPDF result and post nothing about it.
- F2: A1 output is unusable as text (more than 50% of truth characters missing or wrong) on both EN and JA. This only confirms the issue; it is context, not a new claim.
- Whatever the result, nothing is posted without the owner's OK on the exact text.
