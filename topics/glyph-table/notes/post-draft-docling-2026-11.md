# Draft: comment on docling-project/docling#2963 (not posted; needs the owner's OK on the exact text)

Target: https://github.com/docling-project/docling/issues/2963 (open, no maintainer reply as of 2026-11-24).
Measured in `results/docling-2026-11.md` (round 2); pre-registrations `results/preregistration-docling-2026-11.md` and `results/preregistration-docling2-2026-11.md`.
Round-1 draft (superseded: wrong font description, missed `replace_broken_text_layer`) is in git history.

---

For anyone landing here: what this issue asks for has shipped as an opt-in option. It was added in #4654 and is in 2.152.0: with `do_ocr` on, `ocr_options.replace_broken_text_layer=True` checks the visible text layer of each page and re-reads only the pages judged broken with full-page OCR.

I measured it on docling 2.152.0 with self-made monthly statements whose font is Type0 / Identity-H with no ToUnicode (and no cmap table or glyph names in the embedded TrueType), English and Japanese, 11 one-page months each, scored against the generator's text:

**Detection**
- Pages with no ToUnicode: 22 of 22 judged broken.
- Real PDFs with a good text layer (Japan's Statistics Bureau monthly report, 55 Japanese pages): 0 judged broken. Good English text was not part of this check.
- A ToUnicode that maps every glyph 3 code points too high (`Period` came out as `Shulrg`): 0 of 11 judged broken, so the shifted text goes straight through. The vowel-share check from #4654 is meant for this case, but it needs at least 200 letters in words and these short pages have 163–182, so it never ran; on 5 of the 11 pages the vowel share was below 0.25.

**The OCR it falls back to** (characters silently replaced by a different one; no flag in the output; Markdown table rules removed before scoring)

| | English, 5,259 chars | Japanese, 4,207 chars |
| --- | --- | --- |
| default engine (`OcrAutoOptions` → RapidOCR, torch) | 113 | did not run: in a plain install `OcrAutoOptions` has no engine for `ja` (it does not consider Tesseract) and raises `OcrLanguageNotSupportedError` |
| Tesseract (`eng` / `jpn`), scale 3.0 | 137 | 328 |
| Tesseract, scale 2.0 / 4.0 | 142 / 130 | 429 / 283 |

- English, RapidOCR: l→I, O→0, 6→9, I→1, l→1. English, Tesseract: O→0, l→1, I→1, I→l; for example the item code `0I-979` came out as `Ol-979`.
- Japanese, Tesseract: 0→9 and 0→6 in dates and amounts (`10,908` was read as `19, 908`), and kanji read as look-alike katakana such as 一→ー and 力→カ.
- The scale-3.0 settings were run twice and gave identical output; scales 2.0 and 4.0 were run once.
- An order-free count (how often each character occurs on the page, a lower bound on misreads) gives a similar picture: English 110 (RapidOCR) and 118 (Tesseract), Japanese 355.

So the detection works well for missing mappings, and it did not fire on the good pages tried here. Two things a user may want to know: the fallback OCR changes codes and numbers without any mark, and a shifted ToUnicode on a short page is not caught. Perhaps worth a line in the option's docs.

Setup, outputs and scoring script (write-up in Japanese; raw outputs, settings and `summary.json` are language-neutral): https://github.com/yasumorishima/document-extraction-lab/tree/main/topics/glyph-table/results/oss/docling/round2
