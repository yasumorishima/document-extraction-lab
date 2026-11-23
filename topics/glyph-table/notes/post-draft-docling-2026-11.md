# Draft: comment on docling-project/docling#2963 (not posted; needs the owner's OK on the exact text)

Target: https://github.com/docling-project/docling/issues/2963 (open, no maintainer reply as of 2026-11-24).
Measured in `results/docling-2026-11.md`; pre-registration `results/preregistration-docling-2026-11.md`.

---

A data point on the workaround in this issue (`force_full_page_ocr=True` with Tesseract), since it is the route every comment here ends up recommending.

It removes the garbage, but Tesseract then swaps look-alike characters, with no flag in the output. I measured it on self-made monthly statements whose embedded font has no ToUnicode, no cmap table and no glyph names (a simple TrueType font rather than the Type0/Identity-H fonts in this issue, but with the same lack of any Unicode clue). Eleven months were scored against the generator's own text:

| | English, 5,259 chars | Japanese, 4,207 chars |
| --- | --- | --- |
| default conversion | unusable (5,115 missing) | unusable (3,939 missing) |
| `force_full_page_ocr` + Tesseract (`eng` / `jpn`) | **137 substituted** | **330 substituted** |

- English: O→0 (43), l→1 (33), I→1 (30), I→l (15), l→I (8), mostly in item codes (`0I-979` came out as `Ol-979`).
- Japanese: 0→9 (89), 一→ー (82), 力→カ (27), 0→6 (21) and other kanji→katakana pairs; one amount went from `10,908` to `19,908`.
- Two runs gave byte-identical output, so the same characters are swapped every time.

So a detector for broken text layers (as proposed above) would help, but the fallback it switches to is not error-free on this kind of document: codes and numbers can change silently. It may be worth saying so in the troubleshooting docs requested in this issue.

Setup: docling 2.152.0, docling-parse 7.27.1, Tesseract 5.3.4, `images_scale=2.0`, `do_table_structure=False`. Sample generator, outputs, settings and scoring script: https://github.com/yasumorishima/document-extraction-lab/blob/main/topics/glyph-table/results/docling-2026-11.md
