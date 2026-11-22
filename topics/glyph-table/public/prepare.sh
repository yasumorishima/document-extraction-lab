#!/bin/sh
# Public sample: "Population Estimates" monthly report (人口推計 月報), Statistics Bureau of Japan.
# Source: https://www.stat.go.jp/data/jinsui/new.html  (PDFs at /data/jinsui/pdf/YYYYMM.pdf)
# Licence: Public Data License 1.0 (PDL1.0, compatible with CC BY 4.0); the processed files are ours.
# The PDFs embed third-party fonts, so neither the PDFs nor the outlined copies are committed:
# this script downloads them and builds everything locally into $1.
#   <out>/YYYYMM.pdf                original
#   <out>/YYYYMM-pK-text.pdf        page K, text kept     -> truth (truth_from_text.py)
#   <out>/YYYYMM-pK-outline.pdf     page K, Ghostscript -dNoOutputFonts (no text, glyphs as shapes)
#   <out>/YYYYMM-pK-truth.json
# Needs: curl, Ghostscript, a Python with pdfminer.six (PY, default python3).
set -e
OUT=${1:-/tmp/jinsui}; PY=${PY:-python3}; HERE=$(dirname "$0")
MONTHS=${MONTHS:-"202512 202601 202602 202603 202604 202605 202606 202607 202608 202609 202610 202611"}
mkdir -p "$OUT"
for ym in $MONTHS; do
  [ -s "$OUT/$ym.pdf" ] || curl -sfL -A "Mozilla/5.0" -o "$OUT/$ym.pdf" "https://www.stat.go.jp/data/jinsui/pdf/$ym.pdf"
  n=$(gs -q -dNODISPLAY -dNOSAFER -c "($OUT/$ym.pdf) (r) file runpdfbegin pdfpagecount = quit")
  k=1
  while [ $k -le $n ]; do
    gs -q -dBATCH -dNOPAUSE -dSAFER -sDEVICE=pdfwrite -dFirstPage=$k -dLastPage=$k -sOutputFile="$OUT/$ym-p$k-text.pdf" "$OUT/$ym.pdf"
    gs -q -dBATCH -dNOPAUSE -dSAFER -sDEVICE=pdfwrite -dNoOutputFonts -dFirstPage=$k -dLastPage=$k -sOutputFile="$OUT/$ym-p$k-outline.pdf" "$OUT/$ym.pdf"
    $PY "$HERE/truth_from_text.py" "$OUT/$ym-p$k-text.pdf" "$OUT/$ym-p$k-truth.json" > /dev/null
    k=$((k + 1))
  done
done
echo "ok $OUT"
