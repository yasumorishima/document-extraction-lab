# 投稿文の下書き（未投稿、2026-11-22）

関連 OSS 2 件に出す文面の下書き。**オーナーが文面を確認して OK を出すまで投稿しない。**
根拠は `oss-verification-2026-11.md` と `../results/oss-evaluation-2026-11.md`（どちらも実測）。

投稿の直前にやること：
- 両方の HEAD と issue 一覧をもう一度確かめる（2026-11-22 時点：pdf-glyph-mapping `7b4075b`、CUNY `8213721`。同じ内容の報告なし）。
- このリポジトリを公開するなら、文中の「(link)」を実際の URL に置き換える。非公開のままなら、その行を消す。
- CUNY は投稿前に `CONTRIBUTING`・issue テンプレートの有無を確かめ、あればそれに合わせる。

---

## A. pdf-glyph-mapping — issue #10「Get this working again」へのコメント

**日本語の要約**：作者の issue #10 に、今の HEAD を手順どおりに動かすと 4 か所で止まることを、再現手順つきで報告する。うち 2 か所は 1 行ずつで直り、直すと作者自身の作業例の出力と一致したことを伝える。残り 2 か所は「Python 側と Rust 側のどちらに合わせるか」を作者に聞く。PR を出してよいかも聞く。

```markdown
I tried the current HEAD (`7b4075b`) step by step (not through the Makefile) on two inputs: the example in `work/example/unabridged-page-201.pdf` with your maps in `work/maps/valid/`, and a small self-made English PDF whose embedded font has no ToUnicode, no cmap table and no glyph names. Environment: rustc 1.97.0, mutool 1.23.10, Python 3.12, `toml` 0.10.2. In case it helps with this issue, here is where it stops.

1. **`src/sample-runs.py` cannot find the map.** It opens `font-<name>.toml`, but phase 1 writes `font-<name>-cmap.toml` (and only when the font has a ToUnicode). With the file renamed, `toml` 0.10.2 raises `IndexError` on the nested arrays phase 1 writes, so the format differs too, not just the name.
2. **`.Tjs` files use Rust's debug format.** `text_state.rs` writes `format!("{:?} ", n)`, so the file contains `CharacterCode([0, 1])`, while `sample-runs.py` expects four hex digits (`0001`) and fails an assertion.
3. **Phase 2 ignores the validated maps.** `dump-tjs --phase phase2` reads only `*<font>-cmap.toml` in the phase 1 format (`mapped = [[[0, 5], ["ँ"]], ...]`). The `[0005] replacement_text = "..."` files that `validate_maps.py` checks are never read, so every glyph becomes the `[glyph...]` placeholder.
4. **Phase 2 writes a corrupt PDF when the content stream is compressed.** `pdf_visit.rs` writes the edited content back with `set_content`, which keeps `/Filter /FlateDecode` on now-uncompressed data. `pdftotext` then reports `Unknown compression method in flate stream`. This happens with `unabridged-page-201.pdf` too. If all pages share one compressed content stream, only the first page gets `/ActualText`.

(2) and (4) are one-line changes:

    // text_state.rs
    -        let glyph_hexes: Vec<String> = glyph_ids.iter().map(|n| format!("{:?} ", n)).collect();
    +        let glyph_hexes: Vec<String> = glyph_ids
    +            .iter()
    +            .map(|n| n.0.iter().map(|b| format!("{:02X}", b)).collect::<String>() + " ")
    +            .collect();

    // pdf_visit.rs
    -        .set_content(ok!(content.encode()));
    +        .set_plain_content(ok!(content.encode()));

With both changes, and your `valid/*.toml` maps converted to the phase 1 format, phase 2 on `unabridged-page-201.pdf` gives 284 `/ActualText` runs. 278 of them match `unabridged.fixed-page-201.pdf` in the repo exactly. Of the other 6, one is an artefact of my comparison script. The remaining 5 all contain glyph `01C2`, which the current map gives as `ों` and the committed output as `र्<CCprec>े`, so I think the map was revised after that output was made. On my self-made PDF, all 82 lines matched the expected text.

I did not change (1) or (3), because each needs a choice of which side (Python or Rust) should define the file name and format. Which one would you prefer? I'm happy to open a PR with the two one-line fixes, or with (1) and (3) as well once the direction is clear.

Unrelated to the breaks: I could not reproduce #5 with a 12,000-page PDF (my self-made page repeated). Phase 1 finished three times each with and without the fixes. That PDF is not yours, though, so it says little about #5.
```

---

## B. CUNY AI Lab pdf-accessibility-app — 新しい issue

**日本語の要約**：
- 文字情報の無いフォントの字形を OCR の多数決で決める処理（PR #82）は、英語で誤り 0 だったこと（決めきれない字は未確定のまま残す）。
- 一方、文字が図形で描かれたページはページ全体の OCR に回り、そこでは似た字（O/0、l/1、I/1）や金額の数字が**印なしで別の字になる**こと。自作サンプルと、公開されている実在の統計資料の両方で測った。
- 提案は 2 つ（図形のページでも「同じ形をまとめて投票し、決めきれない字は未確定のまま残す」ようにする。確認済みの対応表を文書をまたいで使えるようにする）。手伝えるかも聞く。

**タイトル案**：`Outline-only pages go to full-page OCR, which silently swaps look-alike characters (measurements + a suggestion)`

```markdown
I measured two parts of the pipeline on PDFs whose text cannot be extracted, at `8213721`. The inputs were self-made samples (fictional monthly statements, 12 months, English and Japanese) and a public government report: the Statistics Bureau of Japan's monthly "Population Estimates", Public Data License 1.0 (CC BY 4.0 compatible). Every output was compared character by character with ground truth.

**1. `ocr_unicode` (fonts with no Unicode info) works well.**
I called `_recover_sync` directly with Tesseract 5.3.4, at the lockfile versions. Over months 2–12 (11 documents; 5,259 characters in total for English, 4,207 for Japanese):

| Font | Wrong | Left unmapped |
| --- | --- | --- |
| Liberation Sans | **0** | 147 |
| DejaVu Serif | **0** | 297 |
| IPAGothic (Japanese, `jpn+eng`) | 76 | 495 |

Leaving undecided glyphs unmapped instead of guessing worked: every English case it could not settle was a look-alike (O/0, I/l/1). In Japanese the errors are kanji/katakana pairs that look the same (工→エ, 力→カ, 夕→タ, 二→ニ, 一→ー), plus a few kanji read as Latin letters (座→E, 参→B).

**2. Outline-only pages go to full-page OCR, which substitutes without any flag.**
`classify._vector_outline_pages` finds pages whose characters are drawn as filled paths, and those pages go through OCRmyPDF `--force-ocr`. I ran your own `classify_pdf` → `run_ocr` on 22 such pages. The output was identical to running OCRmyPDF 17.4.0 directly with the same arguments, so I used the direct run for the larger set:

- Self-made English, 10 variants (fonts, rules, tight tracking, Ghostscript-converted, small coordinate jitter), months 2–12 (about 5,250 characters per variant): **95–128 characters silently replaced** in each variant. Mostly O→0, l→1, I→1, I↔l. A clearer font did not help (DejaVu Serif still had 120). In one month an amount changed from `5,583` to `5,983`.
- Self-made Japanese (4,207 characters): 249 replaced, including a digit (0→9).
- The public report (pages 1–5 of 11 monthly issues, 153,247 characters, outlined with Ghostscript `-dNoOutputFonts`): 4,145 extra or wrong characters and 6,812 missing. Examples: ー→-, 人→A, ＋→十, 月→4.

For a screen-reader user, these are wrong words and wrong numbers with nothing to show they might be wrong.

**Suggestion.**
On an outline page, the same character is drawn as (almost) the same path every time, so the idea behind `ocr_unicode` can carry over:

- Rasterise each filled path.
- Group them by shape similarity, not an exact hash, because coordinates are rounded slightly differently each time.
- OCR all members of a group and vote with the same agreement rules.
- Leave groups that do not reach agreement as unknown instead of picking a character.

I built a small stdlib-only version of the grouping and lookup to test the idea. With a checked glyph→character table built once from one month, the later months had 0 silent errors in 16 of 17 self-made conditions and on the public report. The rest came out as "unknown". The one condition with errors was heavy coordinate jitter (±0.1 pt), and there the table showed warning signs when it was built.

A second, smaller idea: for documents that come out in the same layout every month, being able to reuse a glyph map that someone has checked would remove most of the "unmapped" cases above. Each document is currently decided on its own.

Is either of these something you would want in the app? If so, I can share the scripts, samples and scoring (link), or try a PR along the lines you prefer. If outline pages are out of scope for now, these numbers may still be useful as a known limitation.
```

---

## 文面について気をつけたこと
- 測っていないことは書かない（CUNY の 2 つ目の提案は「未確定がなくなるはず」とは書かず「most of」に留めた。根拠は帳簿方式の測定）。
- 生成 AI との比較は入れていない（どちらのプロジェクトの話題でもないため）。
- 実在の個人・会社の情報は入れていない。サンプルは自作か公開資料だけ。
