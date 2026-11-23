"""English figures for the glyph-table blog post (images/blog/*-en.png), for DEV.to.
Same numbers and layout as blog_figures.py. Numbers are copied from
topics/glyph-table/results/*.md and results/public/method-jinsui.json.

Usage: python3 blog_figures_en.py <out dir>
Text font: DejaVu Sans (Bitstream Vera licence, matplotlib's default). The look-alike
figure draws glyphs with Liberation Sans (OFL 1.1) and IPAGothic (IPA Font
License v1.0), the fonts of the self-made samples. Needs matplotlib."""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"

INK, MUTED, GRID = "#1f2933", "#5f6b7a", "#e3e6ea"
GRAY, BLUE, ORANGE = "#c9cdd6", "#2a78d6", "#d9822b"


def frame(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)


def titles(fig, title, sub):
    fig.text(0.03, 0.95, title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.03, 0.875, sub, fontsize=11, color=MUTED, va="top")


def hbar(ax, labels, values, texts, highlight, xmax, bh=0.62):
    y = range(len(labels))[::-1]
    for yi, v, t, h in zip(y, values, texts, highlight):
        ax.barh(yi, max(v, xmax * 0.004), height=bh, color=BLUE if h else GRAY)
        ax.text(max(v, 0) + xmax * 0.015, yi, t, va="center", fontsize=11.5, color=INK,
                fontweight="bold" if h else "normal")
    frame(ax)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=12, color=INK)
    ax.set_xlim(0, xmax * 1.28)
    ax.set_xticks([])


# 0. problem
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), dpi=150)
for ax, head, body, res, good in ((axes[0], "Normal PDF", "Inside: text data\nS a l e s   5 , 5 8 3", "Copy → \"Sales 5,583\"", True),
                                   (axes[1], "PDF with no text", "Inside: outlined shapes only\n(nothing says they are letters)", "Copy → nothing, or garbage", False)):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.85, boxstyle="round,pad=0.01,rounding_size=0.03",
                                fc="#f2f4f7", ec="#9aa3b0", lw=1))
    ax.text(0.5, 0.82, head, ha="center", fontsize=14, fontweight="bold", color=INK)
    ax.text(0.5, 0.58, "Sales 5,583", ha="center", va="center", fontsize=30, color=INK)
    ax.text(0.5, 0.36, body.split("\n")[0], ha="center", fontsize=11.5, color=MUTED)
    ax.text(0.5, 0.29, body.split("\n")[1] if not good else "", ha="center", fontsize=11, color=MUTED)
    ax.text(0.5, 0.13, res, ha="center", fontsize=12.5, color=BLUE if good else ORANGE, fontweight="bold")
fig.subplots_adjust(top=0.78, left=0.02, right=0.98, bottom=0.02, wspace=0.06)
titles(fig, "Same look, different inside", "A PDF like the one on the right reads fine on screen, but you cannot copy or extract its text")
fig.savefig(f"{OUT}/fig-problem-en.png", facecolor="white"); plt.close(fig)

# 1. flow
fig, ax = plt.subplots(figsize=(9, 7.2), dpi=150)
ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.axis("off")
def box(x, y, w, t, hl=False, h=0.9):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc="#fff4e5" if hl else "#f2f4f7", ec=ORANGE if hl else "#9aa3b0", lw=1.6 if hl else 1))
    ax.text(x, y, t, ha="center", va="center", fontsize=12.5, color=INK, fontweight="bold" if hl else "normal")
def arrow(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5, mutation_scale=16))
ax.text(0.2, 11.6, "First month only", fontsize=12, color=MUTED, fontweight="bold")
box(5, 10.8, 6, "Collect every glyph shape in the PDF")
arrow(5, 10.35, 5, 9.75)
box(5, 9.3, 6, "Group identical shapes")
arrow(5, 8.85, 5, 8.25)
box(5, 7.8, 6, "4 AI models name each group")
arrow(5, 7.35, 5, 6.75)
box(5, 6.3, 6, "A person checks only the disagreements", hl=True)
arrow(5, 5.85, 5, 5.25)
box(5, 4.8, 6, "Glyph table (shape → character) done")
ax.plot([0.2, 9.8], [4.0, 4.0], color=GRID, lw=1.2, ls="--")
ax.text(0.2, 3.55, "Every month after that", fontsize=12, color=MUTED, fontweight="bold")
box(5, 2.9, 7.4, "Look up the table (no AI, free, same result every time)")
arrow(4, 2.45, 2.6, 1.55); arrow(6, 2.45, 7.4, 1.55)
box(2.6, 1.1, 3.6, "Match → character")
box(7.4, 1.1, 3.6, "No match → \"?\"")
fig.savefig(f"{OUT}/fig-flow-en.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# 2. look-alikes (self-made sample fonts: Liberation Sans OFL, IPAGothic IPA licence)
LS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
IPA = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
pairs = [("I", "l", "1", LS, "I (capital i), l (small L), 1"), ("O", "0", None, LS, "O (letter), 0 (zero)"),
         ("カ", "力", None, IPA, "katakana ka, kanji 'power'"), ("ー", "一", None, IPA, "long-vowel mark, kanji 'one'"),
         ("エ", "工", None, IPA, "katakana e, kanji 'craft'"), ("ロ", "口", None, IPA, "katakana ro, kanji 'mouth'")]
fig, axes = plt.subplots(2, 3, figsize=(10, 5.6), dpi=150)
for ax, (a, b, c, f, cap) in zip(axes.flat, pairs):
    fp = fm.FontProperties(fname=f)
    chars = [ch for ch in (a, b, c) if ch]
    for i, ch in enumerate(chars):
        x = (i + 0.5) / len(chars)
        ax.text(x, 0.55, ch, fontproperties=fp, fontsize=54, ha="center", va="center", color=INK)
    ax.text(0.5, 0.07, cap, fontsize=11, ha="center", color=MUTED)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(GRID)
fig.subplots_adjust(top=0.78, hspace=0.12, wspace=0.08, left=0.03, right=0.97, bottom=0.03)
titles(fig, "Look-alikes that fool people and AI", "Glyphs from the fonts of the self-made samples. I and l differ in height by only about 5%")
fig.savefig(f"{OUT}/fig-lookalike-en.png", facecolor="white"); plt.close(fig)

# 3. self-made: silent errors over months 2-12 (3 runs: show the range, bar = largest)
rows = [("Glyph table", 0, 0, "0", "0", True),
        ("OCR (Tesseract)", 126, 249, "126", "249", False),
        ("AI Opus 5.5", 15, 203, "11–15", "192–203", False),
        ("AI Sonnet 5.5", 54, 222, "49–54", "210–222", False),
        ("AI Haiku 5.5", 13, 249, "6–13", "229–249", False),
        ("AI Fable 5.2", 18, 216, "13–18", "205–216", False)]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150, sharey=True)
for ax, col, tcol, head in ((axes[0], 1, 3, "English, 5,259 chars"), (axes[1], 2, 4, "Japanese, 4,207 chars")):
    hbar(ax, [r[0] for r in rows], [r[col] for r in rows], [r[tcol] for r in rows], [r[5] for r in rows], 250)
    ax.set_title(head, fontsize=12.5, color=INK, loc="left", pad=6)
fig.subplots_adjust(top=0.72, left=0.19, right=0.98, bottom=0.05, wspace=0.08)
titles(fig, "Self-made statements, 11 months: only the glyph table has 0 silent errors",
       "Silent error = a wrong character with no warning. AI: range over 3 runs")
fig.savefig(f"{OUT}/fig-selfmade-en.png", facecolor="white"); plt.close(fig)

# 4. public report
rows = [("Glyph table", 0, "0   (free)", True), ("AI Opus 5.5", 0, "0 / 0 (2 runs)   ~$0.07", False),
        ("AI Fable 5.2 *", 0, "0   ~$0.22", False), ("AI Sonnet 5.5", 7, "7   ~$0.03", False),
        ("AI Haiku 5.5", 371, "371   ~$0.002", False), ("OCR (Tesseract)", 4145, "4,145   (free)", False)]
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
hbar(ax, [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows], 4145)
fig.subplots_adjust(top=0.74, left=0.22, right=0.97, bottom=0.08)
titles(fig, "Public statistics report: 0 silent errors, but so did the top AI models",
       "Silent errors on 11 monthly issues of Japan's Population Estimates (~150k chars). Right: cost per page")
fig.text(0.03, 0.02, "* Fable 5.2: pages 1–2 only (68,747 chars)", fontsize=10, color=MUTED)
fig.savefig(f"{OUT}/fig-public-en.png", facecolor="white"); plt.close(fig)

# 5. monthly ? share (method-jinsui.json, first_only, pages 1-5)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
share = [2.9, 2.9, 3.4, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 77.1]
fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
ax.bar(range(11), share, width=0.62, color=[GRAY] * 10 + [ORANGE])
for i, v in enumerate(share):
    ax.text(i, v + 1.5, f"{v}%", ha="center", fontsize=10.5, color=INK, fontweight="bold" if i == 10 else "normal")
ax.set_xticks(range(11)); ax.set_xticklabels(months, fontsize=11, color=INK)
ax.set_yticks([]); ax.set_ylim(0, 90); frame(ax)
ax.annotate("Digit sizes in the tables changed slightly.\nNo misreads: they all came out as \"?\"",
            (10, 60), (4.4, 50), fontsize=11.5, color=INK,
            arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.2))
fig.subplots_adjust(top=0.74, left=0.03, right=0.98, bottom=0.1)
titles(fig, "When the layout changed, most characters became \"?\"",
       "Share of characters the glyph table marked \"?\" (unknown). Table built from the Dec 2025 issue only")
fig.savefig(f"{OUT}/fig-monthly-en.png", facecolor="white"); plt.close(fig)

# 6. draft check
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), dpi=150)
data = [("Self-made statements (English, 11 months)", [("Opus draft, unchecked", 210, "210", False),
                                     ("Person checks only the\n5 / 83 the models split on", 0, "0", True)], 210),
        ("Population Estimates (11 months)", [("Fable draft, unchecked", 200, "200", False),
                                  ("Person checks only the\n113 / 1,016 the models split on", 0, "0", True)], 210)]
for ax, (head, rs, xm) in zip(axes, data):
    hbar(ax, [r[0] for r in rs], [r[1] for r in rs], [r[2] for r in rs], [r[3] for r in rs], xm, bh=0.45)
    ax.set_ylim(-0.7, 1.7)
    ax.set_title(head, fontsize=12.5, color=INK, loc="left", pad=6)
    ax.tick_params(axis="y", labelsize=11)
fig.subplots_adjust(top=0.7, left=0.2, right=0.98, bottom=0.05, wspace=0.75)
titles(fig, "An unchecked AI draft repeats its mistakes every month",
       "Silent errors. Left: one wrong table entry (l answered as I) became 210 errors over 11 months")
fig.savefig(f"{OUT}/fig-draft-en.png", facecolor="white"); plt.close(fig)
print("ok")
