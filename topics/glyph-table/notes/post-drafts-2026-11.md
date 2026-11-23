# 投稿文の下書き（未投稿、2026-11-22 作成、2026-11-23 監査を受けて改訂）

関連 OSS に出す文面の下書き。**オーナーが文面を確認して OK を出すまで投稿しない。**
根拠は `oss-verification-2026-11.md` と `../results/oss-evaluation-2026-11.md`（どちらも実測）。

2026-11-23：Fable 5.2 による監査（読み取りのみ）を受けて改訂した。主な訂正：
- A：「278 個が完全に一致」は誤り（今のコードは ActualText をフォント名の目印で包むので、そのままでは 0 個。目印を外すと 279 個）。`IndexError` は実行によって `TomlDecodeError` にもなる。根拠のログが無い共有ストリームの文と、#5 の段落を削った。
- B：`5,583 → 5,983` は 1 月だけの例で、集計した 2〜12 月には無い。`ー→-` は向きが逆（正しくはハイフンが ー になる）。日本語で確認依頼が付かない理由として「照合の OCR が eng」と書いたのは、今回の実行（全体設定が `jpn+eng`）と合わない。表を使う方法の成績を、正解で代用したこと・順番を問わない数・「?」の多さが分かる書き方にした。
- B は 2 件に分けた：B1（図形のページの似た字の置き換え）と B2（OCRmyPDF のロックを上げる提案）。B2 の `#<B1 の番号>` は、B1 を投稿した後にその番号に置き換える。

投稿の直前にやること：
- 両方の HEAD と issue 一覧をもう一度確かめる（2026-11-23：pdf-glyph-mapping `7b4075b`、CUNY `8213721`。同じ内容の報告なし。CUNY の issue は #84〜#91、どれも別の話題）。
- CUNY には `CONTRIBUTING` も issue テンプレートも無い（2026-11-23 確認）。

---

## A. pdf-glyph-mapping — issue #10「Get this working again」へのコメント

**日本語の要約**：作者の issue #10 に、今の HEAD を手順どおりに動かすと 4 か所で止まることを、再現手順つきで報告する。うち 2 か所は 1 行ずつで直り、直すと作者自身の作業例の出力とほぼ一致したことを伝える（違いは目印と、後で直されたらしい 1 字形だけ）。残り 2 か所は「Python 側と Rust 側のどちらに合わせるか」を作者に聞く。PR を出してよいかも聞く。

```markdown
I tried the current HEAD (`7b4075b`) step by step (not through the Makefile) on two inputs: the example in `work/example/unabridged-page-201.pdf` with your maps in `work/maps/valid/`, and a small self-made English PDF whose embedded font has no ToUnicode, no cmap table and no glyph names. Environment: rustc 1.97.0, mutool 1.23.10, Python 3 with `toml` 0.10.2. In case it helps with this issue, here is where it stops.

1. **`src/sample-runs.py` cannot find the map.** It opens `font-<name>.toml`, but phase 1 writes `font-<name>-cmap.toml` (and only when the font has a ToUnicode). With the file renamed, `toml` 0.10.2 cannot parse the nested arrays phase 1 writes (I got `TomlDecodeError` or `IndexError` depending on the file), so the format differs too, not just the name.
2. **`.Tjs` files use Rust's debug format.** `text_state.rs` writes `format!("{:?} ", n)`, so the file contains `CharacterCode([0, 1])`, while `sample-runs.py` expects four hex digits (`0001`) and fails an assertion.
3. **Phase 2 ignores the validated maps.** `dump-tjs --phase phase2` reads only `*<font>-cmap.toml` in the phase 1 format (`mapped = [[[0, 5], ["ँ"]], ...]`). When it is given `maps/valid/` (as the Makefile does), the `[0005] replacement_text = "..."` files that `validate_maps.py` checks are never read, so every glyph becomes the `[glyph...]` placeholder.
4. **Phase 2 writes a corrupt PDF when the content stream is compressed.** `pdf_visit.rs` writes the edited content back with `set_content`, which keeps `/Filter /FlateDecode` on now-uncompressed data. `pdftotext` then reports `Unknown compression method in flate stream`. This happens with `unabridged-page-201.pdf` too.

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

With both changes, and your `valid/*.toml` maps converted to the phase 1 format, phase 2 on `unabridged-page-201.pdf` gives 284 `/ActualText` runs, the same number as the committed `unabridged.fixed-page-201.pdf`. The current code wraps each one in `[FontName]…[/FontName]` (and one slanted run in `[sl]…[/sl]`), which the committed file does not have. Ignoring those markers, 279 of the 284 are identical. The other 5 all contain glyph `01C2`, which the current map gives as `ों` and the committed output as `र्<CCprec>े`, so I assume the map was revised after that output was made. On my self-made PDF, all 82 lines matched the expected text.

I did not change (1) or (3), because each needs a choice of which side (Python or Rust) should define the file name and format. Which one would you prefer? I'm happy to open a PR with the two one-line fixes, or with (1) and (3) as well once the direction is clear.
```

---

## B1. CUNY AI Lab pdf-accessibility-app — 新しい issue（本体）

**日本語の要約**：
- 文字が図形で描かれたページはページ全体の OCR に回り、似た字（O/0、l/1、I/1）や数字が別の字になる。自作サンプルと公開の統計資料で測った。
- アプリ全体を生成 AI 込みで通しても（既定のモデルには届かないので Claude Haiku 5.5 で代用）、英語では文字の確認依頼が 1 件も付かず、読み上げの文字は OCR の誤りそのまま。公開の月報では 2 回通して 30 ページ・19 ページに止めない確認依頼が付いたが、依頼の付かないページにも誤りが残る。
- 参考：文字情報の無いフォントの処理（`ocr_unicode`）は英語で誤り 0 だった（2 行で触れるだけ）。
- 提案は 1 つ（図形のページでも、同じ形をまとめて投票し、決めきれない字は未確定のまま残す）。手伝えるかも聞く。

**タイトル案**：`Outline-only pages: full-page OCR replaces look-alike characters with no review task`

```markdown
I measured what happens to PDFs whose text is drawn as filled paths (no fonts), at `8213721`. Inputs: self-made samples (fictional monthly statements, English and Japanese, months 2–12) and a public government report, the Statistics Bureau of Japan's monthly "Population Estimates" (Public Data License 1.0, CC BY 4.0 compatible), pages 1–5 of 11 issues converted to outlines with Ghostscript `-dNoOutputFonts`. Every output was compared character by character with ground truth (for the public report, the text layer of the original PDF).

For context: `ocr_unicode` on fonts with no Unicode info did well. On two English fonts it made 0 wrong characters and left only O/0 and I/l/1 look-alikes unmapped.

**Outline-only pages.** `classify._vector_outline_pages` finds these pages, and they go through OCRmyPDF `--force-ocr`. I checked that your own `classify_pdf` → `run_ocr` gives output identical to running OCRmyPDF 17.4.0 directly with the same arguments (22 pages), and used the direct run for the larger set:

- Self-made English, 10 variants (fonts, rules, tight tracking, Ghostscript-converted, small coordinate jitter), 5,259 characters each (5,534 for one variant): **95–128 characters replaced** per variant. Mostly O→0, l→1, I→1, I↔l. A clearer font did not help (DejaVu Serif: 120). Digits change too: in five variants one digit was replaced in one month (e.g. 5→9, 5→0).
- Self-made Japanese (4,207 characters, OCR language set to `jpn+eng`): 249 replaced, including 0→9 12 times.
- The public report (153,247 characters, `jpn+eng`): 4,145 extra or wrong characters and 6,812 missing, counted without regard to order (so a lower bound). Examples: a hyphen/minus read as ー, 人→A, ＋→十, 月→4.

**Does anything after OCR catch them?** I ran the whole app with `scripts/corpus_benchmark.py --profile full` (sqlite, veraPDF 1.28.2). Your default model endpoint was not reachable from my machine, so the app's LLM calls went to Claude Haiku 5.5 through a small local OpenAI-compatible adapter. I also ran it once with an endpoint that always fails. Screen-reader text is from your `scripts/tagged_text.py`.

- English (11 documents): all `complete` / compliant. None of the 2,151 OCR lines triggers `suspicious_text_signals`, so no text review task was created, with or without the LLM. The only tasks were figure and alt-text checks. The screen-reader text carries the OCR substitutions: 116 in reading order, against 126 for the OCR alone (one table is read column by column). A screen-reader user gets wrong item codes (O-683 read as 0-683, and so on) with nothing to show they might be wrong.
- Japanese (11 documents, `jpn+eng`): 57 of 239 lines trigger "mixed scripts", yet no text review task was created. From the code, the second-opinion crop OCR uses the global `OCR_LANGUAGE` setting, not the job's language (`text_grounding.py:43`; it was `jpn+eng` in my run), and the comparison looks only at a-z0-9 (`page_intelligence.py:59-65`), so a kana/kanji swap on its own does not count as a difference. I did not trace further why no task was created.
- The public report (55 pages, `jpn+eng`), run twice: all `complete` / compliant / fidelity passed. A non-blocking "Verify readable text on flagged blocks" task appeared on 30 pages in one run and 19 in the other (the model's proposed readings are in the task; 2 and 0 blocks were applied as `/ActualText`). The pages without a task still had 1,330 and 1,925 extra or wrong characters. In both runs the glyphs in the output were exactly the OCR's.

These task counts come from Haiku; with your default model they may differ. The English result does not depend on the model.

**Suggestion.** On an outline page the same character is drawn as (almost) the same path every time, so the idea behind `ocr_unicode` could carry over: rasterise each filled path, group paths by shape similarity (not an exact hash, since coordinates are rounded differently each time), OCR all members of a group and vote with the same agreement rules, and leave groups without agreement as unknown. I tested a small stdlib-only version. With a glyph→character table filled in from ground truth (standing in for a human check) built from one month, the later months had 0 wrong characters in 16 of 17 self-made conditions; the exception was heavy coordinate jitter (±0.1 pt), where the table showed warning signs when it was built. On the public report an order-free count found 0 characters that were not in the truth, but about 10% came out as "unknown" (77% in the one issue where digit sizes changed). Reusing a checked map across documents with the same layout would be a natural next step.

Is this something you would want in the app? If so, I can share the scripts, samples and scoring (https://github.com/yasumorishima/document-extraction-lab/tree/main/topics/glyph-table; write-ups are in Japanese, scripts and raw outputs are language-neutral), or try a PR along the lines you prefer. If outline pages are out of scope for now, these numbers may still be useful as a known limitation.
```

---

## B2. CUNY AI Lab pdf-accessibility-app — 新しい issue（OCRmyPDF のロックを上げる提案）

**日本語の要約**：ロックの OCRmyPDF 17.4.0 では、日本語の OCR の文字（`Occulta` フォントで 1 字ずつ書かれる）を pdfium が読まず、`tagged_text.py` の読み上げの文字が欠ける。上流の OCRmyPDF 17.13.0 で直っている。ロックを上げた再実行で日本語は PDF の字と同じ数になり、英語は変わらなかった。CUNY のテスト 2,216 件は両方の版で全部通った。

**タイトル案**：`Bump OCRmyPDF in uv.lock to 17.13.0: pdfium does not read single-glyph Occulta text in 17.4.0`

```markdown
With the locked OCRmyPDF 17.4.0, OCR text in scripts that no installed font covers (Japanese in my case; your Docker image installs no CJK font) is written in OCRmyPDF's `Occulta` font, often one glyph per `Tj`. Occulta's glyphs in 17.4.0 have no extents, and pdfium (147.0.7713.0 via pypdfium2 5.6.0) drops a text object of zero width, so `scripts/tagged_text.py` returns fewer characters than the page draws. pdfminer and pdftotext read them.

This is fixed upstream in OCRmyPDF 17.13.0 (commit 56f7282, "Give Occulta's glyphs extents so pdfium can extract their text"). `pyproject.toml` already allows it (`ocrmypdf>=17.4.0`), so only `uv.lock` needs the bump; `uv lock --upgrade-package ocrmypdf` resolved to 17.13.0 for me.

I ran `scripts/corpus_benchmark.py --profile full` before and after the bump on the same inputs (LLM calls went to Claude Haiku 5.5 through a local adapter, as described in #<B1 の番号>):

| | 17.4.0 | 17.13.0 |
| --- | --- | --- |
| 11 self-made Japanese documents: characters read by pdfium / glyphs in the PDF | 3,984 / 4,193 | 4,193 / 4,193 |
| 55 pages of a public Japanese report: same | 143,348 / 150,968 | 150,962 / 150,968 |
| 11 self-made English documents | | glyphs and screen-reader text unchanged |

The glyphs themselves were identical in every output, and every job finished `complete` in both runs. OCR errors stay as they were; the fix only makes pdfium read what OCRmyPDF wrote. The backend test suite passes with both versions (2,216 passed; run with a dummy `LLM_API_KEY`).

A small script that shows the problem on any OCRmyPDF output: `tools/cuny-e2e/check_pdfium_single_glyph.py` in https://github.com/yasumorishima/document-extraction-lab. I only tested 17.13.0, and I did not check what Chrome's viewer reads (upstream's commit message says selection and copy work in Chromium after the fix).
```

---

## 文面について気をつけたこと
- 測っていないことは書かない。
- 生成 AI との比較は入れていない（どちらのプロジェクトの話題でもないため）。
- 実在の個人・会社の情報は入れていない。サンプルは自作か公開資料だけ。
