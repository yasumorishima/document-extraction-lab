#!/bin/sh
# Build every sample variant used by the evaluation (12 months each) into $1.
# Needs: python3 + fonttools, Ghostscript (gs).
set -e
OUT=${1:-samples/variants}
HERE=$(dirname "$0")
python3 -I "$HERE/make_sample.py" "$OUT" outline 12
python3 -I "$HERE/make_sample.py" "$OUT" outline-merged 12
for j in 0.02 0.05 0.1; do
  python3 -I "$HERE/make_sample.py" "$OUT" outline-jitter 12 "$j" --prefix=jitter$j
done
python3 -I "$HERE/make_sample.py" "$OUT" font 12 2>/dev/null
# A real converter: Ghostscript turns the font text into outlines (-dNoOutputFonts).
for f in "$OUT"/font-statement-2026-*.pdf; do
  m=$(basename "$f" .pdf | sed 's/font-statement-//')
  gs -q -dBATCH -dNOPAUSE -dSAFER -sDEVICE=pdfwrite -dNoOutputFonts -sOutputFile="$OUT/gs-outline-statement-$m.pdf" "$f"
  cp "$OUT/font-truth-$m.json" "$OUT/gs-outline-truth-$m.json"
done
# Round 2: other fonts, Japanese, rules touching glyphs, tight tracking, straight quotes.
F=/usr/share/fonts/truetype
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --font=$F/dejavu/DejaVuSerif.ttf --prefix=dejavu-serif
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --font=$F/liberation/LiberationMono-Regular.ttf --prefix=liberation-mono
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --font=$F/liberation/LiberationSerif-Regular.ttf --prefix=liberation-serif
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --font=/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf --lang=ja --prefix=ja
python3 -I "$HERE/make_sample.py" "$OUT" outline-merged 12 --font=/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf --lang=ja --prefix=ja-merged
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --rules=separate --prefix=rules-separate
python3 -I "$HERE/make_sample.py" "$OUT" outline-merged 12 --rules=merged --prefix=rules-merged
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --tracking=-0.6 --prefix=tight
python3 -I "$HERE/make_sample.py" "$OUT" outline-merged 12 --tracking=-0.6 --prefix=tight-merged
python3 -I "$HERE/make_sample.py" "$OUT" outline 12 --quotes --prefix=quotes
python3 -I "$HERE/make_sample.py" "$OUT" outline-merged 12 --quotes --prefix=quotes-merged
