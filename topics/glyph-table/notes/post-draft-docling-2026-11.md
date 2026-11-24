# Draft: comment on docling-project/docling#2963 (not posted; needs the owner's OK on the exact text)

Target: https://github.com/docling-project/docling/issues/2963 (open, no maintainer reply as of 2026-11-24).
Measured in `results/docling-2026-11.md` (rounds 2 and 3); pre-registrations `results/preregistration-docling-2026-11.md`, `results/preregistration-docling2-2026-11.md` and `results/preregistration-docling3-2026-11.md`. Two independent read-only audits were applied.
Round-1 draft (superseded: wrong font description, missed `replace_broken_text_layer`) is in git history.

---

For anyone landing here: what this issue asks for has shipped as an opt-in option. It was added in #4654 and is in 2.152.0: with `do_ocr` on, `ocr_options.replace_broken_text_layer=True` checks the visible text layer of each page and re-reads only the pages judged broken with full-page OCR.

I measured it on docling 2.152.0, mostly with self-made monthly statements whose font is Type0 / Identity-H with no ToUnicode (and no cmap table or glyph names in the embedded TrueType), English and Japanese, 11 one-page months each, scored against the generator's text.

**Detection**
- Pages with no ToUnicode: all judged broken (short pages 22/22, longer English pages 11/11).
- Two-page documents with a good page 1 and a no-ToUnicode page 2: in all 11, only page 2 was re-read.
- Good text layers: 0 judged broken among 55 Japanese pages (Japan's Statistics Bureau monthly report) and 11 self-made English pages.
- docling's own `tests/data/pdf/sources` (17 files, 102 pages; mostly English, also 3 Korean files, 1 German, some Lorem ipsum; right-to-left files left out): 3 pages judged broken, `redp5110_sampled` p3 and one Korean page that appears in both `skipped_1page` (p2) and `skipped_2pages` (p3). All three also show many `(cid:N)` in pdfminer (278, 47, 47), so they look really broken. One page that pdfminer cannot map well (`2206.01062` p1, 617 `(cid:N)`) was not flagged; I did not check whether docling-parse maps it correctly.
- A ToUnicode that maps every glyph 3 code points too high (`Period` came out as `Shulrg`):
  - spaces kept as spaces: caught on the longer pages (11/11), missed on the short ones (0/11). The vowel-share check from #4654 needs at least 200 letters in 3–20-letter words; the short pages have 156–179.
  - spaces shifted as well (space → `#`): missed on both (0/11 each), because the words run together into tokens longer than 20 letters, which the check skips.
  - (The spaces-kept variant was added after I pre-registered the spaces-shifted one, once I saw why that one was missed.)

**The OCR it falls back to** (characters replaced by a different one; there is no per-character mark in the exported text, only the page's `parse_score` set to 0; Markdown table rules removed before scoring; short pages)

| | English, 5,259 chars | Japanese, 4,207 chars |
| --- | --- | --- |
| default engine in a plain install (`OcrAutoOptions` → RapidOCR, torch) | 113 | did not run: no engine for `ja` (`OcrAutoOptions` does not consider Tesseract), `OcrLanguageNotSupportedError` |
| default engine with `easyocr` installed (it picks EasyOCR) | 157 | 149 (and 501 characters missing) |
| Tesseract (`eng` / `jpn`), scale 3.0 | 137 | 328 |
| Tesseract, scale 2.0 / 4.0 | 142 / 130 | 429 / 283 |

- English: O→0, l→1, I→1, l→I with every engine; for example Tesseract read the item code `OO-821` as `00-821`, and RapidOCR and EasyOCR read `0I-979` as `01-979`.
- Japanese: 0→9 and 0→6 in dates and amounts with Tesseract (`10,908` was read as `19, 908`), and kanji read as look-alike katakana such as 一→ー and 力→カ with both Tesseract and EasyOCR.
- The short-page settings with the default engine and with Tesseract at scale 3.0 were run twice and gave identical output; the other settings were run once.

So the per-page detection works well for missing mappings and kept every good page I could check. Two things a user may want to know: the fallback OCR changes codes and numbers with no mark in the text, whichever engine is used, and a shifted ToUnicode is missed on short pages or when the space is shifted too. Perhaps worth a line in the option's docs.

Outputs, settings and an English key to the run names: https://github.com/yasumorishima/document-extraction-lab/tree/main/topics/glyph-table/results/oss/docling (sample generator `samples/make_sample.py`, scoring `tools/score_text.py` and `tools/summarize_docling.py` in the same topic folder; the full write-up is in Japanese).
