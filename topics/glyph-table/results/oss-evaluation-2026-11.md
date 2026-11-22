# 評価：関連 OSS 2 件を、帳簿方式と同じものさしで（2026-11-22）

`results/evaluation-2026-11.md` と同じ自作サンプル（12 か月）・同じ採点（`tools/score_text.py`、日本語は全角半角を同一視）で、
**2〜12 月（11 か月分）** を比べた。実行場所：Claude Code クラウド（x86_64）。どちらのプロジェクトにもまだ何も投稿していない。

## 結論
| 方式 | 英語 5,259 字の黙った誤り | 日本語 4,207 字の黙った誤り | 人の手間 |
| --- | --- | --- | --- |
| **帳簿方式**（字形の**形**で照合） | **0**（図形の PDF、17 条件中 16 条件） | **0** | 帳簿の確認 1 回（4 モデル下書きの不一致だけ見れば 5〜7 個） |
| CUNY：対応表づくり（OCR の多数決、フォント版） | **0**（? 147〜297） | **76**（? 495） | なし |
| CUNY：ページ全体の OCR（図形の PDF） | **95〜128**（条件による） | **249** | なし |
| pdf-glyph-mapping：毎月その月の表を書く | **0** | **0** | **毎月** 53〜99 字形を手で対応付け |
| pdf-glyph-mapping：1 月の表を使い回す | **1,068** | **761** | 1 回 |
| 同上（月をまたいで字の番号が変わらない PDF） | **0**（? 40） | — | 1 回 |

- **CUNY の対応表づくり**は、英語では決めきれない字を「?」に残し、黙って間違えない。日本語では似た字（工/エ、力/カ など）を 76 字、漢字を英字（座→E）にした例もある。
- **CUNY のページ全体 OCR**（文字が図形のページに使われる経路）は、フォントや罫線などの条件に関係なく、似た字を黙って置き換える（O→0、l→1、I→1 など月 10 字前後）。
- **pdf-glyph-mapping** は表が正しければ完全に正しい。ただし表は「ファイル内の字の番号」に結び付くので、**ファイルごとに番号を振り直す PDF（印刷ドライバによくある）では、表を使い回すと 1→7、1→9 のような数字の取り違えを含め大量に黙って間違える**。毎月書き直せば正しいが、その手間が毎月かかる。
- 帳簿方式は字を**形**で照合するので、番号の振り直しにも、フォント情報が無い図形の PDF にも左右されない。

## 1. CUNY pdf-accessibility-app — 対応表づくり（`ocr_unicode`）
- 対象：文字情報を全部抜いた埋め込みフォントの PDF（`make_sample.py ... font`）。英語 Liberation Sans、英語 DejaVu Serif、日本語 IPAゴシック、各 12 か月。
- 動かし方：`tools/run_cuny_ocr_unicode.py`（`_recover_sync` だけ。Tesseract 5.3.4、言語は英語 `eng`、日本語 `jpn+eng`。並列実行時は `OMP_THREAD_LIMIT=1` が必要、付けないと Tesseract が CUNY 側の制限時間 180 秒を超えた）。
- 採点：直した PDF の文字情報を位置順に取り出し（`tools/pdf_text.py`、名前の無い字は「?」）、`score_text.py`。

| サンプル | 対象の字形（12 か月計） | 割り当て | 未確定 | 正しい | **誤り** | ? |
| --- | --- | --- | --- | --- | --- | --- |
| 英語 Liberation Sans | 672 | 649 | 23 | 5,112 | **0** | 147 |
| 英語 DejaVu Serif | 672 | 642 | 30 | 4,962 | **0** | 297 |
| 日本語 IPAゴシック | 1,074 | 878 | 196 | 3,636 | **76** | 495 |

日本語の誤り：工→エ 17、力→カ 17、夕→タ 14、二→ニ 10、一→ー 9、口→ロ 4、座→E 2、参→B 1。
（文書ごとに独立に読むので、1 月に決めた字を 2 月に持ち越さない。帳簿方式は一度確かめた表を毎月使う。）

## 2. CUNY pdf-accessibility-app — ページ全体の OCR（文字が図形のページ）
- アプリの分類段階（`classify._vector_outline_pages`）が図形のページを見つけ、OCRmyPDF `--force-ocr` で読み直す。同じ設定（`--rotate-pages --deskew --force-ocr --pages 1 --optimize 0`）で OCRmyPDF 17.4.0 を直接動かした。

| 条件（2〜12 月） | 正しい | **誤り** | 抜け | 余分 | 主な誤り |
| --- | --- | --- | --- | --- | --- |
| outline（Liberation Sans） | 5,124 | **126** | 9 | 4 | O→0、I→1、l→1、I→l |
| gs-outline（Ghostscript 変換） | 5,122 | **128** | 9 | 6 | 同上 |
| DejaVu Serif | 5,104 | **120** | 35 | 50 | l→1 48、O→0 35、I→1 27 |
| Liberation Serif | 5,132 | **117** | 10 | 4 | l→1、O→0、I→1 |
| Liberation Mono | 5,116 | **126** | 17 | 31 | O→0 49、l→1 36、l→L 24 |
| 罫線あり | 5,115 | **128** | 16 | 14 | I→1、O→0、l→1、O→Q |
| 字間を詰める | 5,114 | **95** | 50 | 13 | O→0、I→1、I→l |
| 引用符あり（5,534 字） | 5,399 | **128** | 7 | 4 | O→0、I→1、l→1 |
| 揺れ ±0.05pt | 5,127 | **120** | 12 | 7 | 同上 |
| 揺れ ±0.1pt | 5,122 | **122** | 15 | 6 | 同上 |
| 日本語（`jpn+eng`） | 3,778 | **249** | 180 | 166 | 一→ー、力→カ、工→エ、**0→9** |

I と l がはっきり違うフォント（DejaVu Serif）でも誤りは減らない。OCR は O と 0、l と 1 を文脈で決めてしまう。

### CUNY 自身の関数で確かめた（2026-11-22）
上の表は、CUNY の OCRmyPDF の設定を書き写して直接動かしたもの。CUNY 自身の `classify_pdf` → `run_ocr` で、図形版の英語・日本語 2〜12 月（22 ページ）を処理し直すと、**22 ページすべてで出力の文字列が完全に一致**した。CUNY はこのページを `scanned` と分類し、`force_ocr_pages = [0]` でページ全体を OCR する。
実在の資料（人口推計 月報、`results/public-evaluation-2026-11.md`）でも CUNY 自身の関数で処理し、1〜5 ページの 2026 年 1〜11 月（153,247 字）で余計な字 4,145・足りない字 6,812 だった。

## 3. pdf-glyph-mapping — 人が書いた表で /ActualText を付ける（phase 2）
- `notes/pdf-glyph-mapping-fixes.patch` の 2 か所を直した版（`7b4075b` ＋ 2 行）。phase 2 が読む形式（`*<フォント名>-cmap.toml`）で、表を正解から作った（＝人が正しく書いた場合）。`tools/run_pdf_glyph_mapping.py`。
- 2 つの使い方：毎月その月の表を書く（own）／1 月の表を使い回す（january）。
- サンプルは、ファイルごとに字の番号を振り直す PDF（既定、印刷ドライバの典型）と、月をまたいで番号が変わらない PDF（`--stable-codes`）。

| サンプル | 毎月書く：誤り | 1 月の表を使い回す：誤り | 使い回しの主な誤り |
| --- | --- | --- | --- |
| 英語 Liberation Sans（番号は毎月振り直し） | **0** | **1,068**（ほか抜け・余分 629） | 1→7 82、l→5 66、1→9 64、,→k 43 |
| 英語 DejaVu Serif（同） | **0** | **1,068** | 同上（番号の振り方が同じため） |
| 日本語 IPAゴシック（同） | **0** | **761**（抜け 1,516・余分 1,440） | 1→-、,→イ、3→ニ、1→7 |
| 英語（番号が変わらない PDF） | **0** | **0**（? 40：1 月に無かった字） | — |

- 表が正しければ、このツールは確実に正しい。弱点は表が**字の番号**に結び付くこと。番号が振り直される PDF では、表を毎月書き直す必要がある。
- 作者自身の作業例（デーヴァナーガリーの本の 1 ページと作者の対応表）でも確かめた（`notes/oss-verification-2026-11.md`）：無修正版は壊れた PDF を出し、修正版は作者がリポジトリに置いている出力と `/ActualText` 284 個中 278 個が一致（違いは対応表が後から直された 1 字形と、比較スクリプト側の 1 個）。
- 毎月書き直す手間：1 か月 53〜61 字形（英語）、76〜99 字形（日本語）を人が対応付ける（空白を含む。正解ファイルから数えた。README いわく "main manual grunt work"）。

## 帳簿方式から見た学び
- 「表を一度作って毎月使う」には、**形**で照合する必要がある（pdf-glyph-mapping の番号方式では使い回せない PDF がある）。
- 「決めきれない字は ? に残す」（CUNY の対応表づくり）は正しい方針で、英語では誤り 0 を実現している。帳簿方式も同じ方針。
- ページ全体の OCR は、フォントや条件に関係なく、似た字を黙って置き換える。

## 再現
```
sh samples/make_variants.sh /tmp/v
python3 samples/make_sample.py /tmp/v font 12 --prefix=font-en
python3 samples/make_sample.py /tmp/v font 12 --prefix=font-en-stable --stable-codes
python3 samples/make_sample.py /tmp/v font 12 --font=.../DejaVuSerif.ttf --prefix=font-dejavu-serif
python3 samples/make_sample.py /tmp/v font 12 --font=.../ipag.ttf --lang=ja --prefix=font-ja
OMP_THREAD_LIMIT=1 LLM_BASE_URL=http://localhost:1/v1 python tools/run_cuny_ocr_unicode.py <app> <in.pdf> <out.pdf> [eng|jpn+eng]
python3 tools/run_pdf_glyph_mapping.py <bin> /tmp/v font-en 12 january <out>
```
出力：`results/oss/`（CUNY の判定記録 `*.stats.json` と文字列、OCR の文字列、pdf-glyph-mapping の文字列）。
注：`samples/generated/font-*`（3 か月）は、埋め込みフォントに余分な表が残る前の版の `make_sample.py` で作ったもの。今の版は描画に要る表だけを残す（DejaVu・IPAゴシックで必要になった）。
