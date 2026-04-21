#!/usr/bin/env python3
"""
generate_poster_pptx.py
=======================
Generates an A2 portrait academic poster as a PowerPoint (.pptx) file,
styled to match the University of Reading Department of Computer Science
poster template:
  - Teal department strip at the top
  - Large bold navy title + teal subtitle + author line
  - Two-column body layout
  - Section headers: filled teal rounded rectangles with white bold text
  - Methodology pipeline: coloured label cells + light content cells
  - Charts embedded from matplotlib
  - KPI callout boxes
  - Teal footer with references

Run from the repository root:
    python poster/generate_poster_pptx.py

Output:
    poster/poster.pptx
"""

import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from pptx import Presentation
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE as MSO

# ── Brand colours ─────────────────────────────────────────────────────────────
TEAL  = RGBColor(0x1A, 0x7A, 0x8A)
NAVY  = RGBColor(0x00, 0x3B, 0x6F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x22, 0x22, 0x22)
LGREY = RGBColor(0xEA, 0xF5, 0xF7)   # light teal tint for pipeline / KPI bg
DGREY = RGBColor(0xA0, 0xD0, 0xDA)   # border colour
RED   = RGBColor(0xBE, 0x1E, 0x2D)
BLUE  = RGBColor(0x1A, 0x6B, 0xB5)
ORNG  = RGBColor(0xA0, 0x40, 0x10)

# ── Slide geometry (A2 portrait: 42 × 59.4 cm) ───────────────────────────────
SW, SH   = 42.0, 59.4   # slide width / height in cm
MLR      = 1.2           # left & right margin
HDRH     = 1.5           # teal department strip height
TTH      = 5.8           # title text area height (below strip)
FTRH     = 1.8           # footer height
CGAP     = 0.8           # gap between the two body columns

BODY_TOP = HDRH + TTH + 0.4    # y where body columns begin (~7.7 cm)
BODY_BOT = SH - FTRH - 0.3    # y where body columns end  (~57.3 cm)

COL_W  = (SW - 2 * MLR - CGAP) / 2   # ~19.4 cm per column
COL1X  = MLR
COL2X  = MLR + COL_W + CGAP

# ── Font sizes (points) ───────────────────────────────────────────────────────
FS_TITLE  = 26
FS_STITLE = 14
FS_AUTH   = 8.5
FS_SEC    = 8.5    # section header (inside teal box)
FS_SSEC   = 7.5    # sub-section heading
FS_BODY   = 7.0
FS_SMALL  = 6.5
FS_TINY   = 6.0


# ══════════════════════════════════════════════════════════════════════════════
# LOW-LEVEL PPTX HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _tf(shape, ml=0.12, mr=0.12, mt=0.08, mb=0.08):
    """Configure and return a shape's text frame with tight internal margins."""
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left   = Cm(ml)
    tf.margin_right  = Cm(mr)
    tf.margin_top    = Cm(mt)
    tf.margin_bottom = Cm(mb)
    return tf


def _run(para, text, size, bold=False, italic=False, color=None):
    """Add a formatted run to a paragraph and return it."""
    r = para.add_run()
    r.text = text
    r.font.size  = Pt(size)
    r.font.bold  = bold
    r.font.italic = italic
    if color:
        r.font.color.rgb = color
    return r


def _solid(shape, color):
    """Fill a shape with a solid colour."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


def _no_line(shape):
    """Remove the shape outline."""
    shape.line.fill.background()


def _rect(slide, x, y, w, h, color=None, line_color=None, line_pt=0.5):
    """Add a plain rectangle; optionally filled and/or outlined."""
    shp = slide.shapes.add_shape(1, Cm(x), Cm(y), Cm(w), Cm(h))
    if color:
        _solid(shp, color)
    else:
        shp.fill.background()
    if line_color:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(line_pt)
    else:
        _no_line(shp)
    return shp


def _rrect(slide, x, y, w, h, color=None, line_color=None, line_pt=0.5, adj=0.3):
    """Add a rounded rectangle; adj controls corner radius (0–0.5)."""
    shp = slide.shapes.add_shape(MSO.ROUNDED_RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(h))
    shp.adjustments[0] = adj
    if color:
        _solid(shp, color)
    else:
        shp.fill.background()
    if line_color:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(line_pt)
    else:
        _no_line(shp)
    return shp


# ══════════════════════════════════════════════════════════════════════════════
# SECTION / TEXT COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def sec_hdr(slide, label, x, y, w, h=0.68, gap=0.2):
    """
    Teal filled rounded-rectangle section header with white bold text.
    Returns the y coordinate immediately below the header.
    """
    shp = _rrect(slide, x, y, w, h, color=TEAL, adj=0.3)
    tf = _tf(shp, ml=0.22, mt=0.08, mb=0.08)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    _run(p, label.upper(), FS_SEC, bold=True, color=WHITE)
    return y + h + gap


def ssec_hdr(slide, label, x, y, w, gap=0.12):
    """
    Small bold teal sub-section heading (no box).
    Returns the y coordinate immediately below.
    """
    txb = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(0.45))
    tf = txb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    _run(p, label, FS_SSEC, bold=True, color=TEAL)
    return y + 0.45 + gap


def text_box(slide, paras, x, y, w, h, size=FS_BODY, para_gap=4):
    """
    Multiple paragraphs in one text box.

    paras: list of str  OR  (text, bold, italic) tuples.
    Returns y + h.
    """
    txb = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    tf = txb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Cm(0)

    for i, item in enumerate(paras):
        if isinstance(item, str):
            text, bold, italic = item, False, False
        elif len(item) == 2:
            text, bold = item; italic = False
        else:
            text, bold, italic = item

        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(para_gap)
        _run(p, text, size, bold=bold, italic=italic, color=BLACK)

    return y + h


def bullet_box(slide, items, x, y, w, h, size=FS_SMALL,
               bchar="•", bcolor=None, gap=1.5):
    """
    Bulleted list in a single text box.

    items: list of str  OR  (str, bold_flag) tuples.
    Returns y + h.
    """
    bc = bcolor or TEAL
    txb = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    tf = txb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Cm(0)

    for i, item in enumerate(items):
        text, bold = (item, False) if isinstance(item, str) else item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        _run(p, bchar + "  ", size, bold=True, color=bc)
        _run(p, text, size, bold=bold, color=BLACK)

    return y + h


# ══════════════════════════════════════════════════════════════════════════════
# METHODOLOGY PIPELINE TABLE
# ══════════════════════════════════════════════════════════════════════════════

_PIPE_STEPS = [
    ("DATA\nCOLLECTION",  BLUE, ["HM Land Registry CSVs (2020–2024)",
                                   "ONS income survey · BoE base rates"]),
    ("DATA\nPREP",         BLUE, ["Fuzzy county normalisation · Outlier removal",
                                   "Affordability feature engineering"]),
    ("AGENT\nSETUP",       TEAL, ["ONS income-percentile profiling",
                                   "Life-stage classification · Preference scoring"]),
    ("LLM +\nTOOLS",       TEAL, ["Ollama llama3.2 · LangChain ReAct loop",
                                   "4 domain tool registrations"]),
    ("TOOL\nEXECUTION",    TEAL, ["PropertySearch · MortgageCalc",
                                   "AffordabilityCheck · FinancialHealth"]),
    ("ANNUAL\nSTEP",       ORNG, ["Salary & expense inflation (2.5%)",
                                   "Stochastic life events · LLM decision"]),
    ("MARKET\nDYNAMICS",   ORNG, ["Regional ONS price growth (2–4% p.a.)",
                                   "Mortgage stress test (+3%) · Logging"]),
    ("OUTPUT\n& ANALYSIS", RED,  ["CSV timeline export",
                                   "Affordability metrics · Policy comparisons"]),
]


def pipeline_table(slide, x, y, w, row_h=1.22, gap=0.04):
    """
    Draw the 8-step methodology pipeline as a two-column table.
    Left cell: coloured background with white step label.
    Right cell: light background with bullet content.
    Returns y position after the last row.
    """
    lw = 4.5          # label cell width
    rw = w - lw - gap  # content cell width

    for label, col, lines in _PIPE_STEPS:
        # ── Label cell ────────────────────────────────────────────────────
        ls = _rect(slide, x, y, lw, row_h, color=col)
        ls.line.color.rgb = WHITE
        ls.line.width = Pt(0.5)
        ltf = _tf(ls, ml=0.12, mr=0.08, mt=0.1, mb=0.1)
        lp = ltf.paragraphs[0]
        lp.alignment = PP_ALIGN.CENTER
        _run(lp, label, 6.0, bold=True, color=WHITE)

        # ── Content cell ──────────────────────────────────────────────────
        rs = _rect(slide, x + lw + gap, y, rw, row_h, color=LGREY)
        rs.line.color.rgb = DGREY
        rs.line.width = Pt(0.5)
        rtf = _tf(rs, ml=0.18, mr=0.1, mt=0.1, mb=0.1)
        for j, line in enumerate(lines):
            rp = rtf.paragraphs[0] if j == 0 else rtf.add_paragraph()
            rp.space_after = Pt(1)
            _run(rp, "• " + line, 6.0, color=BLACK)

        y += row_h + gap

    return y


# ══════════════════════════════════════════════════════════════════════════════
# KPI CALLOUT BOXES
# ══════════════════════════════════════════════════════════════════════════════

def kpi_row(slide, kpis, x, y, w, h=1.4, vcolor=TEAL):
    """
    Horizontal row of KPI stat boxes.

    kpis: list of (value_string, label_string).
    Returns y position below the row.
    """
    n  = len(kpis)
    bw = (w - (n - 1) * 0.12) / n

    for i, (val, lbl) in enumerate(kpis):
        bx  = x + i * (bw + 0.12)
        shp = _rrect(slide, bx, y, bw, h, color=LGREY,
                     line_color=DGREY, line_pt=0.8, adj=0.2)
        tf  = _tf(shp, mt=0.12, mb=0.08)
        p1  = tf.paragraphs[0]
        p1.alignment = PP_ALIGN.CENTER
        _run(p1, val, FS_BODY + 1, bold=True, color=vcolor)
        p2  = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        p2.space_before = Pt(2)
        _run(p2, lbl, FS_TINY, color=BLACK)

    return y + h + 0.15


# ══════════════════════════════════════════════════════════════════════════════
# CHART GENERATORS (matplotlib → embedded images)
# ══════════════════════════════════════════════════════════════════════════════

def _embed(slide, fig, x, y, w_cm, h_cm=None):
    """
    Embed a matplotlib figure into the slide at the given position.
    If h_cm is None the height is auto-computed from the image aspect ratio.
    Returns the y position immediately below the embedded image.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    buf.seek(0)
    if h_cm:
        pic = slide.shapes.add_picture(buf, Cm(x), Cm(y), Cm(w_cm), Cm(h_cm))
    else:
        pic = slide.shapes.add_picture(buf, Cm(x), Cm(y), width=Cm(w_cm))
    return y + pic.height.cm + 0.15


def _chart_trajectories():
    """Line chart: simulated regional house price trajectories 2024–2034."""
    years   = np.arange(2024, 2035)
    regions = {
        "Greater London":  (510_000, 0.020),
        "South East":      (368_000, 0.025),
        "National Median": (285_000, 0.030),
        "North West":      (185_000, 0.040),
        "North East":      (152_000, 0.030),
    }
    colours = ["#BE1E2D", "#1A6BB5", "#1A7A8A", "#C07810", "#6B46A8"]
    lstyles = ["-", "--", "-", "--", ":"]

    fig, ax = plt.subplots(figsize=(5.0, 3.1))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#F0F8FA")

    for (region, (base, rate)), col, ls in zip(regions.items(), colours, lstyles):
        prices = [base * (1 + rate) ** i / 1_000 for i in range(len(years))]
        ax.plot(years, prices, color=col, linestyle=ls, linewidth=1.8,
                label=region, marker="o", markersize=2.5, markevery=2)

    ax.set_xlabel("Year", fontsize=7)
    ax.set_ylabel("Median Price (£ thousands)", fontsize=7)
    ax.set_title("Regional House Price Trajectories (2024–2034)",
                 fontsize=8, fontweight="bold", color="#1A7A8A", pad=4)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.5, loc="upper left", framealpha=0.9,
              handlelength=1.4, handletextpad=0.4)
    ax.grid(True, alpha=0.25, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}k"))
    plt.tight_layout(pad=0.4)
    return fig


def _chart_affordability():
    """Horizontal bar chart: house price-to-income ratios by region."""
    regions = [
        "North East", "Yorkshire", "North West",
        "East Midlands", "West Midlands",
        "South West", "East of England",
        "South East", "Greater London",
    ]
    ratios  = [5.1, 5.8, 6.3, 6.9, 7.4, 8.8, 9.1, 10.2, 12.1]
    colours = [
        "#1A6B38" if r < 7.0 else "#C07810" if r < 9.5 else "#BE1E2D"
        for r in ratios
    ]

    fig, ax = plt.subplots(figsize=(5.0, 2.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#F0F8FA")

    bars = ax.barh(regions, ratios, color=colours, edgecolor="white",
                   linewidth=0.5, height=0.65)
    ax.axvline(x=8.0, color="#BE1E2D", linestyle="--", linewidth=1.2,
               alpha=0.8, label="Crisis threshold (×8)")
    for bar, ratio in zip(bars, ratios):
        ax.text(ratio + 0.15, bar.get_y() + bar.get_height() / 2,
                f"×{ratio}", va="center", ha="left",
                fontsize=5.8, fontweight="bold")

    ax.set_xlabel("Price-to-Income Ratio", fontsize=7)
    ax.set_title("Price-to-Income Ratios by Region",
                 fontsize=8, fontweight="bold", color="#1A7A8A", pad=4)
    ax.tick_params(labelsize=6)
    ax.set_xlim(0, 14.5)
    ax.legend(fontsize=5.5, loc="lower right", framealpha=0.9)
    ax.grid(True, axis="x", alpha=0.25, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout(pad=0.4)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CHROME — HEADER & FOOTER
# ══════════════════════════════════════════════════════════════════════════════

def _build_header(slide):
    """Draw the teal department strip, title area, author line, and UoR badge."""

    # ── Teal department strip (full width, top of slide) ──────────────────
    strip = _rect(slide, 0, 0, SW, HDRH, color=TEAL)
    tf = _tf(strip, ml=MLR, mr=0.5, mt=0.2, mb=0.1)
    p  = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    _run(p, "Department of Computer Science", 9.5, bold=True, color=WHITE)

    # ── University of Reading badge (navy rounded rect, top-right) ────────
    bw, bh = 5.2, 2.1
    badge  = _rrect(slide, SW - 0.5 - bw, 0.05, bw, bh,
                    color=NAVY, adj=0.15)
    btf    = _tf(badge, ml=0.15, mr=0.15, mt=0.18, mb=0.1)
    bp1    = btf.paragraphs[0]
    bp1.alignment = PP_ALIGN.CENTER
    _run(bp1, "University", 9.5, bold=True, color=WHITE)
    bp2 = btf.add_paragraph()
    bp2.alignment = PP_ALIGN.CENTER
    _run(bp2, "of Reading", 9.5, color=WHITE)

    # ── Main title ────────────────────────────────────────────────────────
    title_w = SW - 2 * MLR - bw - 0.8
    tx  = slide.shapes.add_textbox(Cm(MLR), Cm(HDRH + 0.3), Cm(title_w), Cm(2.9))
    ttf = tx.text_frame
    ttf.word_wrap = True
    _run(ttf.paragraphs[0],
         "AI Agent-Based Modelling of the UK Housing Market",
         FS_TITLE, bold=True, color=NAVY)

    # ── Subtitle ──────────────────────────────────────────────────────────
    tx2 = slide.shapes.add_textbox(Cm(MLR), Cm(HDRH + 3.3), Cm(SW - 2 * MLR), Cm(1.1))
    _run(tx2.text_frame.paragraphs[0],
         "An LLM-Driven Simulation of UK Housing Affordability",
         FS_STITLE, color=TEAL)

    # ── Author / institution line ─────────────────────────────────────────
    tx3 = slide.shapes.add_textbox(Cm(MLR), Cm(HDRH + 4.5), Cm(SW - 2 * MLR), Cm(0.65))
    _run(tx3.text_frame.paragraphs[0],
         "Kieran Thompson  |  University of Reading  ·  "
         "Department of Computer Science  ·  2024/25",
         FS_AUTH, color=BLACK)

    # ── Thin teal rule at base of title area ──────────────────────────────
    _rect(slide, MLR, HDRH + TTH - 0.18, SW - 2 * MLR, 0.07, color=TEAL)


def _build_footer(slide):
    """Draw the teal footer strip with references and degree programme."""
    fy = SH - FTRH
    _rect(slide, 0, fy, SW, FTRH, color=TEAL)

    # References (left side)
    txb = slide.shapes.add_textbox(Cm(MLR), Cm(fy + 0.12),
                                   Cm(SW * 0.62), Cm(FTRH - 0.2))
    tf  = txb.text_frame
    tf.word_wrap = True
    p1  = tf.paragraphs[0]
    _run(p1, "References", FS_SMALL, bold=True, color=WHITE)
    for ref in [
        "HM Land Registry (2024). UK House Price Index.   "
        "ONS (2023). UK House Price Statistics.   "
        "Bank of England (2024). Mortgage Market Data.",
        "Bonabeau, E. (2002). Agent-based modeling. PNAS 99(S3).   "
        "Brown, T. et al. (2020). Language Models are Few-Shot Learners. NeurIPS.",
    ]:
        p = tf.add_paragraph()
        _run(p, ref, FS_TINY, color=WHITE)

    # Degree programme (right side)
    dp   = slide.shapes.add_textbox(Cm(SW * 0.62), Cm(fy + 0.12),
                                    Cm(SW * 0.38 - MLR), Cm(FTRH - 0.2))
    dptf = dp.text_frame
    dp1  = dptf.paragraphs[0]
    dp1.alignment = PP_ALIGN.RIGHT
    _run(dp1, "Degree Programme", FS_SMALL, bold=True, color=WHITE)
    dp2 = dptf.add_paragraph()
    dp2.alignment = PP_ALIGN.RIGHT
    _run(dp2, "BSc Computer Science  ·  University of Reading", FS_TINY, color=WHITE)


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN 1 — INTRODUCTION, RESEARCH QUESTIONS, METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════

def _build_col1(slide):
    x, w = COL1X, COL_W
    y    = BODY_TOP

    # ── INTRODUCTION ──────────────────────────────────────────────────────────
    y = sec_hdr(slide, "Introduction", x, y, w)
    y = text_box(slide, [
        "The United Kingdom faces a severe housing affordability crisis. "
        "National median house prices have risen to over 8× median annual "
        "household earnings, pricing millions of first-time buyers out of the "
        "market. In Greater London this ratio exceeds 12×, creating a stark "
        "structural divide. Despite decades of policy intervention — Help-to-Buy, "
        "Shared Ownership, stamp-duty relief — homeownership rates among the "
        "under-35s have fallen steadily since 2003.",

        "Traditional econometric models rely on aggregate supply-demand "
        "assumptions that fail to capture the emergent, heterogeneous behaviours "
        "driving real housing markets. Individual household decisions — shaped by "
        "income, life stage, debt, and local conditions — aggregate into complex "
        "dynamics that are fundamentally non-linear and path-dependent.",

        "This research presents a novel Agent-Based Model (ABM) combining "
        "Large Language Model (LLM) reasoning with rigorous quantitative financial "
        "algorithms. Each agent represents a unique household navigating realistic "
        "constraints across a 10-year simulation horizon, producing outputs "
        "suitable for policy evaluation.",
    ], x, y, w, 5.3, size=FS_BODY, para_gap=4)
    y += 0.35

    # ── RESEARCH QUESTIONS ────────────────────────────────────────────────────
    y = sec_hdr(slide, "Research Questions", x, y, w)
    y = bullet_box(slide, [
        "Can LLM-driven agents produce contextually appropriate housing "
        "decisions consistent with empirically observed UK behavioural patterns?",
        "How do heterogeneous agent decisions compare across income groups, ages, "
        "and regions over a 10-year simulation horizon?",
        "Which policy interventions — Help-to-Buy, interest-rate changes, "
        "shared ownership — most effectively improve affordability for target "
        "demographics?",
    ], x, y, w, 3.2, size=FS_SMALL, bchar="▶", bcolor=TEAL, gap=3)
    y += 0.35

    # ── METHODOLOGY ───────────────────────────────────────────────────────────
    y = sec_hdr(slide, "Methodology", x, y, w)
    y = text_box(slide, [
        "Each agent encapsulates a household with unique financial circumstances, "
        "life-stage preferences, and decision-making characteristics. The hybrid "
        "LLM + algorithm design ensures decisions are simultaneously contextually "
        "intelligent (via language model reasoning) and financially rigorous "
        "(via validated economic algorithms).",
    ], x, y, w, 1.7, size=FS_SMALL, para_gap=2)
    y += 0.25

    # Pipeline table
    y = pipeline_table(slide, x, y, w)
    y += 0.4

    # ── DATA SOURCES ──────────────────────────────────────────────────────────
    y = sec_hdr(slide, "Data Sources", x, y, w)
    y = bullet_box(slide, [
        ("HM Land Registry  —  Price Paid Data 2020–2024 (4.2M+ transactions)",   True),
        ("ONS Income Survey  —  Household income percentiles, age & region (2022/23)", False),
        ("Bank of England  —  Base rate history & mortgage affordability guidelines", False),
        ("ONS UK HPI  —  Regional annual house price growth rates & indices",      False),
        ("HMRC / SDLT  —  Stamp duty thresholds & first-time buyer relief bands",  False),
    ], x, y, w, 3.3, size=FS_SMALL, bchar="▸", bcolor=TEAL, gap=2)
    y += 0.35

    # ── TECHNOLOGY STACK ──────────────────────────────────────────────────────
    y = sec_hdr(slide, "Technology Stack", x, y, w)
    bullet_box(slide, [
        ("LLM Engine  —  Ollama llama3.2 (local inference, zero data leakage)",   False),
        ("Agent Framework  —  LangChain ReAct with 4 specialist domain tools",    False),
        ("Housing Data  —  Pandas + NumPy · fuzzy-match over 4.2M+ records",      False),
        ("Financial Layer  —  SalaryCalculator, MortgageProduct, ExpenseManager", False),
        ("Algorithms  —  HousingPreferenceEvaluator, FinancialAffordabilityEvaluator", False),
        ("Well-being  —  HappinessEvaluator (composite scoring 0–100)",           False),
        ("Output  —  SimulationLogger → CSV timeline; matplotlib charts",         False),
    ], x, y, w, 4.0, size=FS_SMALL, bchar="▸", bcolor=TEAL, gap=2)


# ══════════════════════════════════════════════════════════════════════════════
# COLUMN 2 — AGENT ARCHITECTURE, RESULTS, QUALITATIVE RESULTS, CONCLUSIONS
# ══════════════════════════════════════════════════════════════════════════════

def _build_col2(slide):
    x, w = COL2X, COL_W
    y    = BODY_TOP

    # ── AGENT ARCHITECTURE & DECISION MODEL ───────────────────────────────────
    y = sec_hdr(slide, "Agent Architecture & Decision Model", x, y, w)

    y = ssec_hdr(slide, "ReAct Decision Loop", x, y, w)
    y = text_box(slide, [
        "Each agent runs a Reason + Act (ReAct) cycle: the LLM reviews its "
        "current financial state, invokes specialist domain tools for calculations, "
        "then synthesises a contextually grounded housing decision. This loop "
        "repeats each annual time-step across the 10-year simulation horizon.",
    ], x, y, w, 1.4, size=FS_SMALL, para_gap=2)
    y += 0.1

    y = bullet_box(slide, [
        "PropertySearchTool — fuzzy search of Land Registry records by region, type & budget",
        "MortgageCalculatorTool — LTV ratios, monthly payments, stress tests (base rate + 3%)",
        "AffordabilityAssessmentTool — income percentile, deposit readiness, price/income ratio",
        "FinancialHealthTool — savings trajectory, debt obligations, monthly disposable income",
    ], x, y, w, 2.6, size=FS_SMALL, bchar="→", bcolor=TEAL, gap=2)
    y += 0.35

    # ── STOCHASTIC LIFE EVENTS ────────────────────────────────────────────────
    y = ssec_hdr(slide, "Stochastic Life Events", x, y, w)
    y = text_box(slide, [
        "Each year agents may experience life events drawn from age-weighted "
        "probability distributions, directly influencing financial capacity "
        "and housing need.",
    ], x, y, w, 1.0, size=FS_SMALL, para_gap=2)
    y = bullet_box(slide, [
        "Salary increase (15% prob., age 18–29);  job promotion (8–10%)",
        "Job loss (2–4%);  marriage (5–8%);  birth of child (3–10%)",
        "Divorce (1–3%);  bereavement;  serious illness;  debt increase",
    ], x, y, w, 1.8, size=FS_SMALL, bchar="•", bcolor=TEAL, gap=2)
    y += 0.4

    # ── RESULTS ───────────────────────────────────────────────────────────────
    y = sec_hdr(slide, "Results", x, y, w)

    # Two charts side by side
    cw = (w - 0.25) / 2
    fig_traj = _chart_trajectories()
    fig_aff  = _chart_affordability()

    buf1 = io.BytesIO()
    fig_traj.savefig(buf1, format="png", dpi=150, bbox_inches="tight",
                     facecolor="white")
    plt.close(fig_traj)
    buf1.seek(0)
    pic1 = slide.shapes.add_picture(buf1, Cm(x), Cm(y), Cm(cw))

    buf2 = io.BytesIO()
    fig_aff.savefig(buf2, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white")
    plt.close(fig_aff)
    buf2.seek(0)
    pic2 = slide.shapes.add_picture(buf2, Cm(x + cw + 0.25), Cm(y), Cm(cw))

    chart_h = max(pic1.height.cm, pic2.height.cm)
    y += chart_h + 0.2

    # KPI row
    y = kpi_row(slide, [
        ("67.4%",    "Homeownership\nrate (10 yr)"),
        ("34.2 yrs", "Median FTB\nage"),
        ("18.3%",    "Avg deposit\n% of price"),
        ("3.0%",     "Avg annual\nprice growth"),
    ], x, y, w, h=1.35, vcolor=TEAL)
    y += 0.3

    # ── QUALITATIVE RESULTS ───────────────────────────────────────────────────
    y = sec_hdr(slide, "Qualitative Results", x, y, w)

    y = ssec_hdr(slide, "Emergent Behaviours", x, y, w, gap=0.1)
    y = bullet_box(slide, [
        "Realistic wait-and-save behaviour: agents defer purchase during "
        "high interest-rate periods, mirroring the observed post-2022 slowdown",
        "Life-event cascades: marriage and promotion trigger housing upgrades; "
        "job loss extends saving periods by a mean +1.8 years",
        "London agents delay first purchase by 2–4 years vs Northern England "
        "equivalents on equivalent salaries",
    ], x, y, w, 2.6, size=FS_SMALL, bchar="◆", bcolor=TEAL, gap=2)
    y += 0.15

    y = ssec_hdr(slide, "Policy Scenario Testing", x, y, w, gap=0.1)
    y = bullet_box(slide, [
        "Help-to-Buy: accelerates homeownership for households earning £25k–£45k",
        "+2% interest rate shock: reduces transaction volume; extends saving "
        "periods by ~1.8 years",
        "Shared ownership: most effective for households earning £25k–£40k",
        "Stamp duty exemption: accelerates first-time buyer market entry",
    ], x, y, w, 2.6, size=FS_SMALL, bchar="★", bcolor=TEAL, gap=2)
    y += 0.35

    # ── CONCLUSIONS & FUTURE WORK ─────────────────────────────────────────────
    y = sec_hdr(slide, "Conclusions & Future Work", x, y, w)
    y = text_box(slide, [
        "This research demonstrates that LLM-driven agent-based modelling "
        "can reproduce realistic UK housing affordability dynamics. The hybrid "
        "approach — combining AI contextual reasoning with rigorous financial "
        "algorithms — provides a powerful new framework for housing policy "
        "simulation, capturing individual-level decision patterns absent from "
        "traditional econometric models.",
    ], x, y, w, 1.9, size=FS_SMALL, para_gap=2)
    y += 0.15

    bullet_box(slide, [
        "Add seller and lender agents for full market-side modelling",
        "Incorporate spatial neighbourhood & commuter-belt effects",
        "Model new-build supply-side construction pipeline dynamics",
        "Extend to Scottish, Welsh & Northern Irish housing markets",
        "Real-time API integration with Rightmove / Zoopla live data",
    ], x, y, w, 2.8, size=FS_SMALL, bchar="→", bcolor=TEAL, gap=2)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_poster(output_path: str = "poster/poster.pptx"):
    """
    Assemble and save the complete A2 poster as a PowerPoint file.

    :param output_path: Destination path for the .pptx file.
    """
    prs = Presentation()

    # Set slide dimensions to A2 portrait (42 × 59.4 cm)
    prs.slide_width  = Cm(SW)
    prs.slide_height = Cm(SH)

    # Add a blank slide (layout index 6 = blank in default template)
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # White slide background
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    # Build all poster regions
    _build_header(slide)
    _build_footer(slide)
    _build_col1(slide)
    _build_col2(slide)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    prs.save(output_path)
    print(f"Poster saved → {output_path}")


if __name__ == "__main__":
    build_poster("poster/poster.pptx")
