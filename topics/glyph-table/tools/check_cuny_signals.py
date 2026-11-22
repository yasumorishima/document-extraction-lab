"""Run CUNY pdf-accessibility-app's own `suspicious_text_signals` over stored OCR outputs.

Usage: python check_cuny_signals.py <cuny-repo> <results-dir>
Needs regex, ftfy, rapidfuzz. Month 1 and the Dec 2025 issue are skipped (same months as the scores).
Each non-empty line of at least 6 characters is checked as one block, and each whole file as one block.
"""
import collections, glob, importlib.util as u, os, sys
s = u.spec_from_file_location("pi", os.path.join(sys.argv[1], "backend/app/services/page_intelligence.py"))
m = u.module_from_spec(s); s.loader.exec_module(m)
R = sys.argv[2]
sets = {"EN outline (ocrmypdf-12m)": "ocrmypdf-12m", "EN conditions (oss/ocrmypdf-conditions)": "oss/ocrmypdf-conditions",
        "JA (ocrmypdf-ja)": "ocrmypdf-ja", "public (public/ocr)": "public/ocr"}
for name, d in sets.items():
    fs = [f for f in sorted(glob.glob(os.path.join(R, d, "*.txt"))) if not f.endswith("-01.txt") and "202512" not in f]
    lines = flagged = files_flagged = 0; sig = collections.Counter()
    for f in fs:
        t = open(f).read()
        for l in t.splitlines():
            if len(m.normalize_visible_text(l)) < 6: continue
            lines += 1; x = m.suspicious_text_signals(l)
            if x: flagged += 1; sig.update(x)
        files_flagged += bool(m.suspicious_text_signals(t))
    print(f"{name}: files {len(fs)}, flagged as one block {files_flagged}; lines {lines}, flagged {flagged}", dict(sig))
