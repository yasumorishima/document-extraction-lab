# glyph-table：文字が取れない PDF を、字形の対応表で読む

*Reading PDFs whose text cannot be extracted, with a one-time, human-checked glyph→character table.*

**プログラムを書かない人向けの説明：[explainer-ja.md](explainer-ja.md)**

## 考え方
文字が「文字」として入っていない PDF がある。
- 文字が図形（塗りつぶしの輪郭）として描かれている
- フォントは入っているが、文字コードの情報（ToUnicode など）が抜けていて、コピーすると記号の羅列になる

どちらも、**同じ文字はいつも同じ形**で描かれる。そこで
1. 形が同じ字形をまとめる（プログラム）
2. まとまりごとに「これは A」と対応表を作る（生成 AI が下書きし、人が確認する。**1 回だけ**）
3. 以後は対応表を引くだけで読む（プログラム。API 呼び出しなし・無料・オフライン・毎回同じ結果）

対応表に無い形は「未確定」として残り、**文字をでっち上げない**。
ただし「間違えない」とは違う：対応表の誤りは毎回繰り返され、似た字（0/O、1/l/I）の取り違えは起こりうる。
まだ数回しか見ていない字は、それと分かるように知らせる。

## このフォルダにあるもの
| パス | 中身 |
| --- | --- |
| `samples/make_sample.py` | 自作サンプルの生成スクリプト |
| `samples/make_variants.sh` | 評価に使った 17 条件 × 12 か月を作る（フォント 4 種、日本語、Ghostscript、罫線、詰め組、引用符、揺れ 3 段階） |
| `samples/generated/` | 生成済みの PDF（2 種類 × 3 か月）と正解 JSON |
| `samples/LICENSES.md` | サンプルに使ったフォントのライセンス |
| `method/` | 帳簿方式の実装（標準ライブラリのみ） |
| `results/` | 各方式の出力と評価（`evaluation-2026-11.md`） |
| `tools/score_text.py` | 3 方式共通の採点 |
| `method/run_rotated.py` | 回転したページ（0・1・3・90・180・270 度）での照合の測定。縦書きは `make_sample.py --vertical` と `run_method.py --vertical` |
| `tools/run_claude_vision.py`、`tools/ai_batch.py`、`tools/summarize_ai.py` | 生成 AI の書き起こし（1 件／並列一括）と集計 |
| `tools/draft_table_with_claude.py`、`tools/draft_consensus.py`、`method/run_with_draft.py` | 帳簿の下書き、人が見るべき所の絞り込み、確認なしで使った場合の測定 |
| `tools/compare_rows.py` | 文字情報を直した PDF を、正解と 1 字ずつ比べる（字形の数が同じとき） |
| `tools/compare_text.py` | OCR の結果など、字数が変わりうる PDF を正解と比べる（置き換わり・抜け・余分を数える） |
| `tools/run_cuny_ocr_unicode.py` | CUNY pdf-accessibility-app の該当部分だけを動かす |
| `notes/oss-verification-2026-11.md` | 関連 OSS 2 件を自作サンプルで動かした記録（動作確認・不具合） |
| `public/`、`results/public/`、`results/public-evaluation-2026-11.md` | 実在の公開資料（人口推計 月報）での評価。PDF は置かず、取得・変換スクリプトと結果だけ |
| `results/oss-evaluation-2026-11.md` | 関連 OSS 2 件を同じものさしで評価（`tools/pdf_text.py`、`tools/run_pdf_glyph_mapping.py`） |
| `notes/pdf-glyph-mapping-fixes.patch` | pdf-glyph-mapping の 1 行修正 2 つ（手元で確認、未投稿） |

## これまでの結果（2026-11-21〜22、Claude Code クラウド x86_64 で実行）
- **関連 OSS の検証**（`notes/oss-verification-2026-11.md`）
  - CUNY pdf-accessibility-app
    - フォント版（Tesseract で読んで投票）：3 か月で**誤り 0**。未確定は似た字（O・I・l）だけ。
    - 図形版（ページ全体を OCRmyPDF で読み直す）：似た字が**黙って別の字に置き換わる**（月 9〜15 字）。金額も 1 か所変わった。
  - pdf-glyph-mapping（人が対応表を書く）：手順どおりに動かすと 4 か所で途切れる。うち 2 か所は 1 行ずつで直ることを確認。
    正しい対応表を渡せば、全 82 行が正解と一致した。
- **評価**（`results/evaluation-2026-11.md`、第 8 版）：図形化 PDF を 12 か月分、3 方式を同じものさしで比べた。2〜12 月：

  | 方式 | 英語 5,259 字の黙った誤り | 日本語 4,207 字の黙った誤り | 1 ページの費用 |
  | --- | --- | --- | --- |
  | 帳簿方式 | **0** | **0** | 0 円・0.3〜1.5 秒 |
  | ふつうの OCR（OCRmyPDF） | **126** | **249** | 0 円 |
  | 生成 AI（Claude 4 モデル × 3 回、似た字に注意） | **6〜54** | **192〜249** | 約 0.001〜0.19 ドル |

  帳簿方式は 17 条件中 16 条件で誤り 0（フォント 4 種、日本語、Ghostscript で変換した PDF、罫線、詰め組、引用符、小さな座標の揺れ）。
  極端な座標の揺れ（±0.1pt）だけ誤り 25 字（帳簿を作る時点で兆候が出る）。
  帳簿の下書きは生成 AI に作らせ、人が確認する。確認せずに使うと 1 か所の誤りが 11 か月で 210 字の誤りになる。
  4 モデル × 3 回の下書きで答えが割れた所だけ人が見れば、確認は 5〜7 個で済み、誤りの見逃しは 0 だった。

- **回転・縦書き・傾き**（同じ文書の後半。3 回の事前登録 `results/preregistration-*-2026-11.md`）
  - 縦書きは、横書きと同じ結果（誤り 0）。
  - 読む前にページの傾きを測って戻し、0°・90°・180°・270° のうち帳簿と一番よく合う向きに直す。
    - 判定用の角度（0.3°・-4°・9°・95° など）で、揺れの無い 15 条件は回さない時と同じ結果だった。
    - 揺れのある条件と実在の月報では、「?」がわずかに増えた（月報 +0.4%）。
  - 10° を超えて傾いたページと、「?」が 3 割を超えたページは、丸ごと人に回す（保留）。
  - 保留されなかったページの黙った誤りは 0。

- **関連 OSS の評価**（`results/oss-evaluation-2026-11.md`）：同じサンプル・同じ採点で 11 か月分。
  CUNY の対応表づくりは英語で誤り 0・日本語 76、ページ全体 OCR は条件によらず 95〜128（日本語 249）。
  pdf-glyph-mapping は毎月表を書けば誤り 0、1 月の表を使い回すと 1,068（英語）・761（日本語）。

- **実在の公開資料での評価**（`results/public-evaluation-2026-11.md`）：総務省統計局「人口推計」月報 12 か月（図形に変換、約 15 万字）。
  帳簿方式は黙った誤り 0（「?」約 3%、書式が変わった 11 月号は大半が「?」）。上位の生成 AI（Opus・Fable）も誤り 0、ふつうの OCR は 4,000 字以上の誤り。
  差が出るのは費用（生成 AI は 1 ページ約 0.07 ドルを毎回）と、毎回同じ結果・データを外に出さないこと。
  帳簿の下書きは 4 モデルの合議で割れた 11% だけ人が見れば誤り 0（下書きをそのまま使うと 200 字の誤り）。

## サンプルを作り直す
```
pip install fonttools==4.68.0
python samples/make_sample.py samples/generated outline
python samples/make_sample.py samples/generated font
```
Liberation Sans Regular（Debian/Ubuntu の `fonts-liberation`）が `/usr/share/fonts/truetype/liberation/` にある前提。
