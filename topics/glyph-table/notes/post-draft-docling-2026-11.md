# Draft: comment on docling-project/docling#2963 (not posted; needs the owner's OK on the exact text)

Target: https://github.com/docling-project/docling/issues/2963 (open, no maintainer reply as of 2026-11-24).
Measured in `results/docling-2026-11.md` (round 2); pre-registrations `results/preregistration-docling-2026-11.md` and `results/preregistration-docling2-2026-11.md`.
Round-1 draft (superseded: wrong font description, missed `replace_broken_text_layer`) is in git history.

---

For anyone landing here: what this issue asks for has shipped as an opt-in option. It was added in #4654 and is in 2.152.0: `ocr_options.replace_broken_text_layer=True` checks each page's text layer and re-reads only the pages judged broken with full-page OCR.

I measured it on docling 2.152.0 with self-made monthly statements whose font is Type0 / Identity-H with no ToUnicode (and no cmap table or glyph names in the embedded TrueType), English and Japanese, 11 months each, scored against the generator's text:

**Detection**
- Pages with no ToUnicode: 22 of 22 judged broken.
- Real PDFs with a good text layer (Japan's Statistics Bureau monthly report, 55 pages): 0 judged broken.
- A ToUnicode that maps every glyph 3 code points too high (`the` → `wkh`, the Caesar-shift case described in an earlier comment): 0 of 11 judged broken, so the shifted text goes straight through.

**The OCR it falls back to** (characters silently replaced by a different one; no flag in the output)

| | English, 5,259 chars | Japanese, 4,207 chars |
| --- | --- | --- |
| default engine (`OcrAutoOptions` → RapidOCR, torch) | 113 | did not run: no installed engine for `ja` in a plain `pip install docling` |
| Tesseract (`eng` / `jpn`), scale 3.0 | 137 | 328 |
| Tesseract, scale 2.0 / 4.0 | 142 / 130 | 429 / 283 |

- English: l→I, O→0, I→1, l→1, 6→9; for example the item code `0I-979` came out as `Ol-979`.
- Japanese: 0→9 and 0→6 in dates and amounts (`10,908` became `19,908`), and kanji read as look-alike katakana such as 一→ー and 力→カ.
- Two runs of each setting gave identical output.

So the detection works well for missing mappings, and it did not fire on good pages here. Two things a user may want to know: the fallback OCR changes codes and numbers without any mark, and a wrong-but-plausible ToUnicode is not caught. Perhaps worth a line in the option's docs.

Setup, outputs and scoring script: https://github.com/yasumorishima/document-extraction-lab/blob/main/topics/glyph-table/results/docling-2026-11.md
