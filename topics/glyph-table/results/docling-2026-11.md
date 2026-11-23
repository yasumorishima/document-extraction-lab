# 評価：docling の「ページ全体を OCR し直す」回避策（2026-11-24）

事前登録：`results/preregistration-docling-2026-11.md`（実行前に main に入れた）。実行場所：Claude Code クラウド（x86_64）。
出力と設定：`results/oss/docling/`（各 `run.json` に版・設定・入力 PDF の sha256・時間）、集計 `results/oss/docling/summary.json`（`tools/summarize_docling.py`）。

## 何を確かめたか
docling issue #2963（未解決、2026-11-24 時点でメンテナーの返事なし）と、関連する #2170・#3081・#3582。
文字の対応表（ToUnicode）がないフォントの PDF は、docling の既定では文字化けする。issue で示された回避策は、Tesseract でページ全体を OCR し直すこと（`force_full_page_ocr=True`）で、コメントでも「これしか道がない」とされている。
その回避策で、似た字が黙って置き換わるかを測った。

- サンプル：自作の明細（`samples/make_sample.py` の `font` モード。埋め込み TrueType で、ToUnicode・cmap 表・グリフ名なし）。英語（Liberation Sans）と日本語（IPAゴシック）、各 12 か月のうち 2〜12 月を採点。
- issue のフォントは Type0/CID（Identity-H）で、こちらは単純な TrueType。どちらも Unicode の手がかりがない点は同じ。
- 版：docling 2.152.0、docling-parse 7.27.1、docling-core 2.108.0、docling-ibm-models 4.0.4、Tesseract 5.3.4（eng・jpn）。
- 回避策の設定は issue のとおり：`do_ocr=True`、`TesseractCliOcrOptions(force_full_page_ocr=True, lang=[eng|jpn])`、`images_scale=2.0`、`do_table_structure=False`。2 回実行した。

## 結果（2〜12 月）
| 方法 | 英語 5,259 字：誤り（置き換え）／余分／足りない | 日本語 4,207 字：同 |
| --- | --- | --- |
| 何も出さない（採点の確認用） | 0 ／ 0 ／ 5,259 | 0 ／ 0 ／ 4,207 |
| docling 既定 | 3 ／ 4,974 ／ 5,115（ほぼ文字化け） | 50 ／ 4,378 ／ 3,939 |
| **docling 回避策（全ページ OCR）1 回目** | **137** ／ 12 ／ 18 | **330** ／ 36 ／ 62 |
| docling 回避策 2 回目 | 1 回目と全く同じ出力 | 同左 |
| 参考：帳簿方式（Ghostscript で図形にした同じフォントの PDF、`evaluation-2026-11.md`） | 0 | — |
| 参考：OCRmyPDF + Tesseract（図形の PDF、`evaluation-2026-11.md`） | 126 ／ 4 | 249 |

「余分」は、docling が表を Markdown で書く区切り線（`|---|`）を除いた数。この除き方は出力を見てから決めた（事前登録には無い）。除かない数は `summary.json` にある（英語 606、日本語 7,108。ほぼ全部が区切り線の `-`）。置き換えの数はどちらでも同じ。

**置き換えの中身**
- 英語 137 字：O→0 43、l→1 33、I→1 30、I→l 15、l→I 8、0→O 4 など。例：2 月号では品番 `0I-979` が `Ol-979`、`OO-821` が `00-821` に。英字が 132、数字が 5。
- 日本語 330 字：0→9 89、一→ー 82、力→カ 27、二→ニ 24、工→エ 23、夕→タ 22、0→6 21、口→ロ 20、八→ハ 13 など。漢字 213、数字 110。日付・品番・金額の 0 が 9 や 6 になる（2 月号では金額 `10,908` が `19,908` に）。

## 事前登録との照合
- **F1（成立）**：回避策は英語 2〜12 月で 137 字を黙って置き換え、その中に似た字の組（O/0、I/l/1）がある。
- **F2（成立）**：既定の出力は英語・日本語とも文字として使えない（足りない字が 9 割以上）。issue の確認で、新しい主張ではない。
- 2 回の実行は全く同じ出力だった（回避策は毎回同じ間違いをする）。

## 言えること・言えないこと
- issue の回避策で文字化けは消えるが、代わりに似た字の置き換えが黙って入る。全体の字数に対して英語 2.6%、日本語 7.8%。出力には印が無いので、使う人は気づけない。
- これは Tesseract の性質で、OCRmyPDF 経由で測った数（英語 126、日本語 249）と同じ傾向。
- 自作サンプル 1 種類だけ。issue の CID フォントの実物、docling の他の OCR エンジン（EasyOCR、RapidOCR など）は測っていない。
- 帳簿方式との比較は、帳簿方式を Ghostscript で図形にした PDF で測った数。docling の中で帳簿方式を動かしたわけではない。
