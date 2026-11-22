# サンプルについて

- **すべて自作**。実在の帳票ではない。会社名・人名・口座番号・金額はすべて架空（乱数）。
- フォント：**Liberation Sans Regular**（Debian パッケージ `fonts-liberation`）、**SIL Open Font License 1.1**。
  - 図形版（`outline-*`）はフォントの字形の輪郭を図形として描いたもの。フォント自体は入っていない。
  - フォント版（`font-*`）はフォントの一部（使った字形だけ）を埋め込み、文字コードの情報を取り除いたもの。
  - OFL 1.1 は「フォントを使って作った文書」には及ばない（文書への埋め込みも許されている）。
- 生成スクリプト・正解 JSON・生成済み PDF は、このリポジトリの LICENSE（MIT）に従う。

## 評価用の追加サンプル（`make_variants.sh` で作る。PDF はリポジトリに入れていない）
- DejaVu Serif（Debian `fonts-dejavu-core`、Bitstream Vera Fonts License）
- Liberation Serif / Liberation Mono（`fonts-liberation`、SIL OFL 1.1）
- IPAゴシック（`fonts-ipafont-gothic`、IPA Font License v1.0。第 2 条 2〜3 項で、フォントを使って作った文書の複製・配布が認められている）
- Ghostscript 10.02.1 で図形に変換した版は、上の Liberation Sans 版から作る。
