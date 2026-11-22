"""Prompt texts shared by run_claude_vision.py and ai_batch.py."""
PROMPTS = {"plain": (
    "Transcribe every piece of text on this page exactly as printed, top to bottom, "
    "one printed line per output line, left to right within a line. Copy each character "
    "as it appears; do not correct, normalise or complete anything. If you cannot tell "
    "which character it is, write ? for that character. Output only the transcription."
)}
PROMPTS["lookalike-ja"] = PROMPTS["plain"] + (
    " Be careful: this is a Japanese statement and the product codes mix katakana with "
    "kanji that look alike (カ/力, ロ/口, ニ/二, エ/工, ハ/八, タ/夕, and the long-vowel mark ー "
    "versus the kanji 一). Decide each one from its shape; if a shape could be either, write ?.")
PROMPTS["lookalike"] = PROMPTS["plain"] + (
    " Be careful: product codes mix look-alike characters (zero 0 and capital O; one 1, "
    "lowercase l and capital I). Decide each one from its shape; if a shape could be "
    "either, write ?.")
