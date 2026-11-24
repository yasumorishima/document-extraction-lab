# Pre-registration, round 2: docling's broken-text-layer replacement (2026-11-24)

Written and committed before any round-2 run. Frozen once committed; results go in `results/docling-2026-11.md`.

## What round 1 missed (owner asked "was the evaluation complete?")
1. Round 1 called the sample font "a simple TrueType font". Wrong: `make_sample.py` `font` mode writes a Type0 font, CIDFontType2, `/Encoding /Identity-H`, `/CIDToGIDMap /Identity`, no ToUnicode, and an embedded TrueType with no cmap table and no glyph names. That is the font class of docling #2963. Corrected in the round-1 write-up and the draft.
2. docling 2.152.0 already has the feature #2963 asks for: `OcrOptions.replace_broken_text_layer` (opt-in, off by default; PR #4654, merged 2026-10-27/28). A page whose text layer `utils/text_quality.is_broken_text_layer` judges broken is read with full-page OCR. Round 1 did not test it.
3. Round 1 only used Tesseract. The default engine (`OcrAutoOptions`) was not tested.
4. Round 1 recorded `images_scale=2.0` as if it set the OCR resolution. It does not: OCR renders at `ocr_options.scale` (default 3.0 = 216 dpi). Round 1 therefore ran Tesseract at scale 3.0.
5. The glyph table was compared on other PDFs (EN only), not the same ones.
6. Markdown table rules were removed from "extra" after seeing the output.

## Samples (self-made)
- EN-font, JA-font: as round 1 (`font` mode, 12 months, months 2–12 scored; same files, same sha256).
- EN-shift (new): `font` mode plus a ToUnicode CMap that maps every glyph to the character 3 code points above the right one ("the" → "wkh"), the "Caesar-shifted" case reported in #2963 by tseaver. Months 2–12. Added to `make_sample.py` as `--tounicode-shift=N`.
- Control (public): the original "Population Estimates" monthly PDFs (good text layer), pages 1–5 of the Jan–Nov 2026 issues, 55 pages, downloaded by `public/prepare.sh`. Used only to count pages judged broken.

## Arms (docling 2.152.0, docling-parse 7.27.1)
Every arm also records, per page, whether the page was judged broken (`parse_score == 0` with the option on).
- R1 `replace_broken_text_layer=True`, default engine (`OcrAutoOptions`, lang `en` / `ja`), everything else default. The engine the auto option picks is recorded.
- R2 `replace_broken_text_layer=True` with `TesseractCliOcrOptions` (lang `eng` / `jpn`), `scale` 3.0 (default).
- R3 as R2 with `scale` 2.0 and 4.0 (EN-font and JA-font only).
- R4 (control) R1 and R2 settings on the 55 public pages: count of pages judged broken only.
- G glyph table on the same font PDFs after Ghostscript `-dNoOutputFonts` (the way to give it shapes), table from month 1, months 2–12 read with the month-1 table (`method/run_method.py`, `first_only`). EN-font and JA-font. EN-shift has the same glyphs as EN-font, so it is not run separately.
- Round-1 arms are kept as they are (A1 default, A2 forced full-page Tesseract).

## Scoring (decided now)
`tools/score_text.py`, EN strict, JA `--nfkc`. Before scoring, docling text gets Markdown table rules removed (lines made only of `|`, `-`, `:` and spaces) and other `|` turned into spaces, for every docling arm; raw numbers are kept in the JSON too. Main number: substituted characters (silent errors), with extra and missing beside it, and substitutions split into digits, Latin, kana, kanji, punctuation. R1 and R2 are run twice; a difference between the two runs is reported.

## What would count as a finding
- F3: with the option on, all 22 font pages (EN-font + JA-font, months 2–12) are judged broken. If fewer, report how many.
- F4: with the option on, EN-font output still has more than 0 substituted characters including a look-alike pair (O/0, I/l/1) — for R1, R2, or both, reported separately.
- F5: the option judges 0 of the 55 control pages broken.
- F6: EN-shift: report whether its 11 pages are judged broken (no threshold; #2963 reports this case unflagged in an older version).
- F7: the glyph table has 0 substituted characters on EN-font and JA-font. If not 0, report it as is.
- The draft comment is rewritten only after these are in; nothing is posted without the owner's OK.
