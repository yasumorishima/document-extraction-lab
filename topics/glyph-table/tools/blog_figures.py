"""Figures for the glyph-table blog post (images/blog/). Numbers are copied from
topics/glyph-table/results/*.md and results/public/method-jinsui.json.

Usage: python3 blog_figures.py <out dir> <NotoSansJP-Regular.ttf>
The font is a static 400-weight instance of Noto Sans JP (OFL; google/fonts
ofl/notosansjp, made with fontTools.varLib.instancer wght=400 and wght=700;
the Bold file must sit next to it as NotoSansJP-Bold.ttf). The look-alike
figure draws glyphs with Liberation Sans (OFL 1.1) and IPAGothic (IPA Font
License v1.0), the fonts of the self-made samples. Needs matplotlib."""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

OUT = sys.argv[1]
FONT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
fm.fontManager.addfont(FONT)
fm.fontManager.addfont(FONT.replace("Regular", "Bold"))
plt.rcParams["font.family"] = fm.FontProperties(fname=FONT).get_name()

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
for ax, head, body, res, good in ((axes[0], "ふつうの PDF", "中身は「文字」のデータ\n売 上　5 , 5 8 3", "コピー → 「売上 5,583」", True),
                                   (axes[1], "文字が取れない PDF", "中身は「線で囲んだ形」の集まり\n（文字だという情報がない）", "コピー → 何も取れない／記号の羅列", False)):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.85, boxstyle="round,pad=0.01,rounding_size=0.03",
                                fc="#f2f4f7", ec="#9aa3b0", lw=1))
    ax.text(0.5, 0.82, head, ha="center", fontsize=14, fontweight="bold", color=INK)
    ax.text(0.5, 0.58, "売上 5,583", ha="center", va="center", fontsize=30, color=INK)
    ax.text(0.5, 0.36, body.split("\n")[0], ha="center", fontsize=11.5, color=MUTED)
    ax.text(0.5, 0.29, body.split("\n")[1] if not good else "", ha="center", fontsize=11, color=MUTED)
    ax.text(0.5, 0.13, res, ha="center", fontsize=12.5, color=BLUE if good else ORANGE, fontweight="bold")
fig.subplots_adjust(top=0.78, left=0.02, right=0.98, bottom=0.02, wspace=0.06)
titles(fig, "見た目は同じでも、中身が違う", "右のような PDF は、画面では読めるのにコピーやデータ抽出ができない")
fig.savefig(f"{OUT}/fig-problem.png", facecolor="white"); plt.close(fig)

# 1. flow
fig, ax = plt.subplots(figsize=(9, 7.2), dpi=150)
ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.axis("off")
def box(x, y, w, t, hl=False, h=0.9):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc="#fff4e5" if hl else "#f2f4f7", ec=ORANGE if hl else "#9aa3b0", lw=1.6 if hl else 1))
    ax.text(x, y, t, ha="center", va="center", fontsize=12.5, color=INK, fontweight="bold" if hl else "normal")
def arrow(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5, mutation_scale=16))
ax.text(0.2, 11.6, "最初の 1 か月だけ", fontsize=12, color=MUTED, fontweight="bold")
box(5, 10.8, 6, "PDF から字の「形」を全部集める")
arrow(5, 10.35, 5, 9.75)
box(5, 9.3, 6, "同じ形どうしを 1 つのグループに")
arrow(5, 8.85, 5, 8.25)
box(5, 7.8, 6, "4 種類の AI が「何の字か」を答える")
arrow(5, 7.35, 5, 6.75)
box(5, 6.3, 6, "答えが割れた所だけ人が確認", hl=True)
arrow(5, 5.85, 5, 5.25)
box(5, 4.8, 6, "帳簿（形 → 文字 の対応表）の完成")
ax.plot([0.2, 9.8], [4.0, 4.0], color=GRID, lw=1.2, ls="--")
ax.text(0.2, 3.55, "2 か月目から毎回", fontsize=12, color=MUTED, fontweight="bold")
box(5, 2.9, 6, "帳簿と見比べるだけ（AI なし・無料・毎回同じ）")
arrow(4, 2.45, 2.6, 1.55); arrow(6, 2.45, 7.4, 1.55)
box(2.6, 1.1, 3.6, "合う → 文字")
box(7.4, 1.1, 3.6, "どれとも合わない → 「?」")
fig.savefig(f"{OUT}/fig-flow.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# 2. look-alikes (self-made sample fonts: Liberation Sans OFL, IPAGothic IPA licence)
LS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
IPA = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
pairs = [("I", "l", "1", LS, "I（アイ）・l（エル）・1"), ("O", "0", None, LS, "O（オー）・0"),
         ("カ", "力", None, IPA, "カ（カタカナ）・力（ちから）"), ("ー", "一", None, IPA, "ー（長音）・一（いち）"),
         ("エ", "工", None, IPA, "エ・工"), ("ロ", "口", None, IPA, "ロ・口")]
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
titles(fig, "人にも AI にも紛らわしい「似た字」", "自作サンプルで使ったフォントの実物。I（アイ）と l（エル）は高さが約 5% 違うだけ")
fig.savefig(f"{OUT}/fig-lookalike.png", facecolor="white"); plt.close(fig)

# 3. self-made: silent errors over months 2-12 (3 runs: show the range, bar = largest)
rows = [("帳簿方式", 0, 0, "0", "0", True),
        ("文字認識ソフト（OCR）", 126, 249, "126", "249", False),
        ("AI Opus 5.5", 15, 203, "11〜15", "192〜203", False),
        ("AI Sonnet 5.5", 54, 222, "49〜54", "210〜222", False),
        ("AI Haiku 5.5", 13, 249, "6〜13", "229〜249", False),
        ("AI Fable 5.2", 18, 216, "13〜18", "205〜216", False)]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150, sharey=True)
for ax, col, tcol, head in ((axes[0], 1, 3, "英語 5,259 字"), (axes[1], 2, 4, "日本語 4,207 字")):
    hbar(ax, [r[0] for r in rows], [r[col] for r in rows], [r[tcol] for r in rows], [r[5] for r in rows], 250)
    ax.set_title(head, fontsize=12.5, color=INK, loc="left", pad=6)
fig.subplots_adjust(top=0.72, left=0.19, right=0.98, bottom=0.05, wspace=0.08)
titles(fig, "自作の明細 11 か月分：帳簿方式だけ「黙った誤り」0",
       "「黙った誤り」＝何の印もなく別の字に読み違えた数。AI は 3 回読ませた範囲")
fig.savefig(f"{OUT}/fig-selfmade.png", facecolor="white"); plt.close(fig)

# 4. public report
rows = [("帳簿方式", 0, "0　（0 円）", True), ("AI Opus 5.5", 0, "0 / 0（2 回）　約 0.07 ドル", False),
        ("AI Fable 5.2 ※", 0, "0　約 0.22 ドル", False), ("AI Sonnet 5.5", 7, "7　約 0.03 ドル", False),
        ("AI Haiku 5.5", 371, "371　約 0.002 ドル", False), ("文字認識ソフト（OCR）", 4145, "4,145　（0 円）", False)]
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
hbar(ax, [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows], 4145)
fig.subplots_adjust(top=0.74, left=0.22, right=0.97, bottom=0.08)
titles(fig, "公開の統計資料でも黙った誤り 0。ただし上位の AI も 0",
       "総務省統計局「人口推計」月報 11 か月分（約 15 万字）の黙った誤り。右は 1 ページを読む費用")
fig.text(0.03, 0.02, "※ Fable 5.2 は 1・2 ページ（68,747 字）のみ", fontsize=10, color=MUTED)
fig.savefig(f"{OUT}/fig-public.png", facecolor="white"); plt.close(fig)

# 5. monthly ? share (method-jinsui.json, first_only, pages 1-5)
months = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
share = [2.9, 2.9, 3.4, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 77.1]
fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
ax.bar(range(11), share, width=0.62, color=[GRAY] * 10 + [ORANGE])
for i, v in enumerate(share):
    ax.text(i, v + 1.5, f"{v}%", ha="center", fontsize=10.5, color=INK, fontweight="bold" if i == 10 else "normal")
ax.set_xticks(range(11)); ax.set_xticklabels([m + " 月" for m in months], fontsize=11, color=INK)
ax.set_yticks([]); ax.set_ylim(0, 90); frame(ax)
ax.annotate("表の数字の大きさがわずかに変わった。\n読み違えずに、すべて「?」で知らせた",
            (10, 60), (4.4, 50), fontsize=11.5, color=INK,
            arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.2))
fig.subplots_adjust(top=0.74, left=0.03, right=0.98, bottom=0.1)
titles(fig, "書式が変わった月は、ほとんどが「?」になる",
       "帳簿方式が「?」（分からない）とした字の割合。帳簿は 2025 年 12 月号だけで作った")
fig.savefig(f"{OUT}/fig-monthly.png", facecolor="white"); plt.close(fig)

# 6. draft check
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), dpi=150)
data = [("自作の明細（英語、11 か月）", [("Opus の下書きをそのまま", 210, "210", False),
                                     ("4 モデル × 3 回で割れた\n5 / 83 個だけ人が確認", 0, "0", True)], 210),
        ("人口推計 月報（11 か月）", [("Fable の下書きをそのまま", 200, "200", False),
                                  ("4 モデルで割れた\n113 / 1,016 個だけ人が確認", 0, "0", True)], 210)]
for ax, (head, rs, xm) in zip(axes, data):
    hbar(ax, [r[0] for r in rs], [r[1] for r in rs], [r[2] for r in rs], [r[3] for r in rs], xm, bh=0.45)
    ax.set_ylim(-0.7, 1.7)
    ax.set_title(head, fontsize=12.5, color=INK, loc="left", pad=6)
    ax.tick_params(axis="y", labelsize=11)
fig.subplots_adjust(top=0.7, left=0.2, right=0.98, bottom=0.05, wspace=0.75)
titles(fig, "AI の下書きは、確認なしだと同じ誤りを毎月繰り返す",
       "黙った誤りの数。左は、表の誤りたった 1 か所（l を I と答えた）が 11 か月で 210 字に増えた")
fig.savefig(f"{OUT}/fig-draft.png", facecolor="white"); plt.close(fig)
print("ok")
