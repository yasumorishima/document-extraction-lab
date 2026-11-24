# Pre-registration, round 3: what the round-2 comment still leaves open (2026-11-24)

Written and committed before any round-3 run. Frozen once committed; results go in `results/docling-2026-11.md` ("第 3 回").
Same docling install as round 2 (docling 2.152.0, docling-parse 7.27.1), except arm E, which adds EasyOCR to a copy of it.

## Why
The owner asked whether the evaluation is exhaustive. The round-2 draft claims four things that were not tested:
1. A shifted ToUnicode is missed "on a short page"; a long page was never tried. docling's vowel-share check (`utils/text_quality.py`) needs at least 200 letters in words.
2. "0 good pages judged broken" covered only Japanese pages; the Latin-only checks never saw good English text.
3. Japanese failed with the default engine in a plain install; an install with an extra engine was not tried.
4. Documents that mix broken and good pages were not tried, although the option works page by page.

## Samples
- L-shift: `font` mode, English, `--tounicode-shift=3`, plus `--notes=8`: eight lines of self-written English sentences under the table, so that a page has well over 200 letters in words. 12 months, months 2–12 used.
- L-good: the same as L-shift but with a correct ToUnicode (`--tounicode-shift=0`). Months 2–12.
- L-none: the same long page with no ToUnicode (`font` mode, `--notes=8`). Months 2–12.
- EN-public: English PDFs with a good text layer from docling's own test data (`tests/data/pdf/` in docling-project/docling at a recorded commit; repository licence MIT), every page, PDFs not committed. If a file fails to load it is listed and skipped.
- Mixed: for each month 2–12, a two-page PDF made by putting the L-good page first and the L-none page second (page objects copied with pypdf; nothing re-encoded). 11 documents, 22 pages.
- New generator options: `--notes=N` (N lines of fixed self-made English text after the total) and `--tounicode-shift=0` (writes a correct ToUnicode). Existing outputs without these options must stay byte-identical except for the font's creation timestamp.

## Arms
- D (detection only, all samples above): `replace_broken_text_layer=True`, `OcrAutoOptions(lang=[en])`; record per-page `parse_score`.
- T (Tesseract `eng`, scale 3.0, `replace_broken_text_layer=True`) on L-shift, L-none and Mixed, scored.
- E: a copy of the round-2 environment plus `easyocr`; `replace_broken_text_layer=True`, `OcrAutoOptions` with lang `ja` on JA-font (round-2 sample, months 2–12) and lang `en` on EN-font, scored; the engine actually picked is recorded. If EasyOCR cannot be installed or its models cannot be downloaded here, E is reported as not run, with the error.

## Scoring (as round 2)
`tools/score_text.py` after removing Markdown table rules (EN strict, JA `--nfkc`), order-free `bag()` beside it. Mixed documents: truth = page 1 truth then page 2 truth.

## What would count as a finding
- F8: L-shift pages judged broken (count of 11). The round-2 sentence "a shifted ToUnicode on a short page is not caught" stays only if F8 is high; if L-shift is also mostly missed, the sentence becomes "a shifted ToUnicode is not caught" with both lengths given.
- F9: L-good, L-none and EN-public: L-none should be 11/11 broken; L-good and EN-public 0 broken. Any good page judged broken is reported with its page.
- F10: E: whether the auto option picks an engine for Japanese once EasyOCR is installed, and its substitutions on JA-font and EN-font.
- F11: Mixed: page 1 kept (not judged broken) and page 2 replaced, in how many of 11 documents; substitutions in the whole document.
- The draft comment is changed only to match these results; nothing is posted without the owner's OK.
