# Draft: comment on docling-project/docling#2963 (not posted; needs the owner's OK on the exact text)

Target: https://github.com/docling-project/docling/issues/2963 (open, no maintainer reply as of 2026-11-24).
Measured in `results/docling-2026-11.md` (round 2); pre-registrations `results/preregistration-docling-2026-11.md` and `results/preregistration-docling2-2026-11.md`.
Round-1 draft (superseded: wrong font description, missed `replace_broken_text_layer`) is in git history.

---

For anyone landing here: what this issue asks for has shipped as an opt-in option. It was added in #4654 and is in 2.152.0: with `do_ocr` on, `ocr_options.replace_broken_text_layer=True` checks the visible text layer of each page and re-reads only the pages judged broken with full-page OCR.

I measured it on docling 2.152.0, mostly with self-made monthly statements whose font is Type0 / Identity-H with no ToUnicode (and no cmap table or glyph names in the embedded TrueType), English and Japanese, 11 one-page months each, scored against the generator's text.

**Detection**
- Pages with no ToUnicode: all judged broken (short pages 22/22, longer English pages 11/11).
- Two-page documents with a good page 1 and a no-ToUnicode page 2: in all 11, only page 2 was re-read.
- Good text layers: 0 judged broken among 55 Japanese pages (Japan's Statistics Bureau monthly report), 95 English pages from docling's own `tests/data/pdf/sources` and 11 self-made English pages. The only test-data pages judged broken (`redp5110_sampled` p3, and the same page of `skipped_1page` / `skipped_2pages`, which are Korean) also show many `(cid:N)` in pdfminer, so they look really broken.
- A ToUnicode that maps every glyph 3 code points too high (`Period` came out as `Shulrg`):
  - spaces kept as spaces: caught on the longer pages (11/11), missed on the short ones (0/11). The vowel-share check from #4654 needs at least 200 letters in 3–20-letter words; the short pages have about 160–180.
  - spaces shifted as well (space → `#`): missed on both (0/11 each), because the words run together into tokens longer than 20 letters, which the check skips.

**The OCR it falls back to** (characters silently replaced by a different one, with no flag in the output; Markdown table rules removed before scoring; short pages)

| | English, 5,259 chars | Japanese, 4,207 chars |
| --- | --- | --- |
| default engine in a plain install (`OcrAutoOptions` → RapidOCR, torch) | 113 | did not run: no engine for `ja` (`OcrAutoOptions` does not consider Tesseract), `OcrLanguageNotSupportedError` |
| default engine with `easyocr` installed (it picks EasyOCR) | 157 | 149 (and 501 characters missing) |
| Tesseract (`eng` / `jpn`), scale 3.0 | 137 | 328 |
| Tesseract, scale 2.0 / 4.0 | 142 / 130 | 429 / 283 |

- English: O→0, l→1, I→1, l→I with every engine; for example Tesseract read the item code `0I-979` as `Ol-979`.
- Japanese: 0→9 and 0→6 in dates and amounts with Tesseract (`10,908` was read as `19, 908`), and kanji read as look-alike katakana such as 一→ー and 力→カ with both Tesseract and EasyOCR.
- An order-free count (how often each character occurs on the page, a lower bound on misreads) gives the same picture.
- Settings that were run twice gave identical output.

So the per-page detection works well for missing mappings and kept every good page here. Two things a user may want to know: the fallback OCR changes codes and numbers without any mark, whichever engine is used, and a shifted ToUnicode is missed on short pages or when the space is shifted too. Perhaps worth a line in the option's docs.

Setup, outputs and scoring script (write-up in Japanese; raw outputs, settings and `summary.json` are language-neutral): https://github.com/yasumorishima/document-extraction-lab/tree/main/topics/glyph-table/results/oss/docling
