"""Evaluate pdf-glyph-mapping's last step (dump-tjs --phase phase2) on the font variants.

The tool maps each glyph *code* of a font to text with a hand-written table and
writes /ActualText into a copy of the PDF. Here the table is written from the
truth (as a careful person would), in the tool's phase-2 format
(`*<BaseFont>-cmap.toml`, `mapped = [[[0, code], ["char"]], ...]`).

Modes (codes are known because make_sample.py numbers glyphs in first-use order):
  own       each month gets its own correct table
  january   the January table is used for every month
Usage: python run_pdf_glyph_mapping.py <bin-dir> <gen-dir> <prefix> <months> <mode> <out-dir> [--stable]
  --stable: the PDFs keep glyph codes across months (made with --stable-codes)
Writes <out-dir>/<prefix>-<mode>-2026-MM.txt (one text run per line, "?" = code without mapping).
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

bin_dir, gen, prefix, n, mode, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3], int(sys.argv[4]), sys.argv[5], Path(sys.argv[6])
stable = "--stable" in sys.argv
out.mkdir(parents=True, exist_ok=True)

def codes(months):
    """char -> code, in first-use order over the given months (one month unless --stable)."""
    m = {}
    for mm in months:
        for l in json.load(open(gen / f"{prefix}-truth-2026-{mm:02d}.json"))["lines"]:
            for ch in l["text"]: m.setdefault(ch, len(m) + 1)
    return m

def table_for(month):
    if mode == "own": return codes(range(1, month + 1) if stable else [month])
    return codes([1])

for month in range(1, n + 1):
    t = table_for(month)
    with tempfile.TemporaryDirectory() as td:
        rows = ",\n".join(f"  [[{c >> 8}, {c & 255}], [{json.dumps(ch, ensure_ascii=False)}]]" for ch, c in t.items())
        (Path(td) / "font-x-ABCDEF+Sample-cmap.toml").write_text("mapped = [\n" + rows + "\n]\n")
        fixed = Path(td) / "fixed.pdf"
        subprocess.run([f"{bin_dir}/dump-tjs", str(gen / f"{prefix}-statement-2026-{month:02d}.pdf"), td, str(fixed), "--phase", "phase2"],
                       capture_output=True, check=True)
        txt = subprocess.run(["pdftotext", "-raw", str(fixed), "-"], capture_output=True, text=True).stdout
    runs = re.findall(r"\[ABCDEF\+Sample\](.*?)\[/ABCDEF\+Sample\]", txt, re.S)
    runs = [re.sub(r"\[glyph\[[^\]]*\]\]", "?", r) for r in runs]       # codes the table does not have
    (out / f"{prefix}-{mode}{'-stable' if stable else ''}-2026-{month:02d}.txt").write_text("\n".join(runs) + "\n")
print("ok", prefix, mode, "stable" if stable else "")
