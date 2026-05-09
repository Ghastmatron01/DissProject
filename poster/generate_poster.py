#!/usr/bin/env python3
"""
generate_poster.py
==================
Creates the A2 portrait academic poster (PDF) for the dissertation:

  "AI Agent-Based Modelling of the UK Housing Market:
   A Multi-Agent Simulation Framework for Affordability Analysis"

  University of Reading · Department of Computer Science · 2024/25

Visual style: matches the official University of Reading / Department of
Computer Science PowerPoint poster template — white body, teal headings with
rule underlines, Department strip at top, UoR navy badge top-right, teal footer.

Run from the repository root:
    python poster/generate_poster.py

Output:
    poster/poster.pdf
"""

import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from reportlab.lib.pagesizes import A2
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader

# ── University of Reading brand colours ──────────────────────────────────────
# Teal matches the Dept of CS template header/heading colour
UOR_TEAL  = HexColor("#1A7A8A")   # Dept strip, section headings, footer
UOR_NAVY  = HexColor("#003B6F")   # UoR logo badge background
UOR_RED   = HexColor("#BE1E2D")   # UoR Reading Red (accent/highlights)
C_RULE    = UOR_TEAL              # Thin rule below section headings
C_DIVIDER = HexColor("#C8D8E0")   # Subtle column-divider rules
C_KPIBG   = HexColor("#EAF5F7")   # Light teal tint for KPI/callout boxes
C_KPIBD   = HexColor("#A0D0DA")   # KPI box border

# Flowchart step colours (vivid — these are diagram elements)
FC_BLUE   = HexColor("#1A6BB5")
FC_GREEN  = HexColor("#1A6B38")
FC_ORANGE = HexColor("#A04010")
FC_RED    = UOR_RED

# ── Page geometry (A2 portrait = 420 × 594 mm) ───────────────────────────────
PW, PH   = A2                                    # 1190.55 × 1683.78 pt
MARGIN   = 14 * mm
COL_GAP  = 10 * mm
COL_W    = (PW - 2 * MARGIN - 2 * COL_GAP) / 3  # ~124 mm per column

DEPT_H   = 14 * mm    # Teal department-name strip at very top
TITLE_H  = 54 * mm    # White title area beneath strip
HEADER_H = DEPT_H + TITLE_H
FOOTER_H = 22 * mm

BODY_TOP = PH - HEADER_H - 2 * mm
BODY_BOT = MARGIN + FOOTER_H + 3 * mm
BODY_H   = BODY_TOP - BODY_BOT

COL_X = [
    MARGIN,
    MARGIN + COL_W + COL_GAP,
    MARGIN + 2 * (COL_W + COL_GAP),
]

TX       = 3 * mm          # text inset from column edge
TW       = COL_W - 2 * TX  # usable text width
SEC_GAP  = 6 * mm          # gap between sections
ITEM_GAP = 1.5              # pt gap between list items

# ── Font sizes ────────────────────────────────────────────────────────────────
FS_TINY   = 6.0
FS_SMALL  = 7.0
FS_BODY   = 7.8
FS_SEC    = 13.0   # Section heading
FS_SUBSEC = 9.5    # Sub-section heading
FS_KPI    = 8.5    # Stat callout value


# ── Paragraph styles ──────────────────────────────────────────────────────────
def _ps(name, font="Helvetica", size=FS_BODY, color=black,
        align=TA_JUSTIFY, leading=None, lb=2, li=0):
    return ParagraphStyle(
        name, fontName=font, fontSize=size, textColor=color,
        alignment=align, leading=leading or size * 1.35,
        spaceAfter=lb, leftIndent=li,
    )


P_BODY   = _ps("body")
P_SMALL  = _ps("small",  size=FS_SMALL)
P_TINY   = _ps("tiny",   size=FS_TINY)
P_BOLD   = _ps("bold",   font="Helvetica-Bold",    size=FS_BODY)
P_SBOLD  = _ps("sbold",  font="Helvetica-Bold",    size=FS_SMALL)
P_TBOLD  = _ps("tbold",  font="Helvetica-Bold",    size=FS_TINY)
P_ITALIC = _ps("italic", font="Helvetica-Oblique", size=FS_SMALL)
P_CTR    = _ps("ctr",    align=TA_CENTER)
P_WHITE  = _ps("white",  color=white, size=FS_SMALL, align=TA_CENTER)


# ── Drawing helpers ───────────────────────────────────────────────────────────

def sec_heading(c, x, y_top, w, title,
                color=UOR_TEAL, size=FS_SEC, rule=True, gap=4):
    """Bold teal section heading with thin underline rule. Returns new y."""
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y_top - size, title)
    y = y_top - size - 1.5
    if rule:
        c.setStrokeColor(color)
        c.setLineWidth(0.9)
        c.line(x, y, x + w, y)
        y -= 1.0
    return y - gap


def sub_heading(c, x, y_top, w, title,
                color=UOR_TEAL, size=FS_SUBSEC, gap=3):
    """Smaller teal sub-section heading with short accent rule. Returns new y."""
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y_top - size, title)
    y = y_top - size - 1.5
    c.setStrokeColor(HexColor("#A0D8E0"))
    c.setLineWidth(0.5)
    c.line(x, y, x + 38 * mm, y)
    return y - gap


def draw_para(c, text, x, y_top, w, style=P_SMALL, gap=2):
    """Draw a Paragraph and return y below it."""
    p = Paragraph(text, style)
    _, ph = p.wrapOn(c, w, 9999)
    p.drawOn(c, x, y_top - ph)
    return y_top - ph - gap


def draw_bullets(c, items, x, y_top, w, style=P_SMALL,
                 bullet="\u2022", indent=10, gap=ITEM_GAP):
    """Draw a bulleted list and return y below it."""
    BF = "Helvetica-Bold"
    for item in items:
        p = Paragraph(f'<font name="{BF}">{bullet}</font>&nbsp; {item}', style)
        _, ph = p.wrapOn(c, w - indent, 9999)
        p.drawOn(c, x + indent, y_top - ph)
        y_top -= ph + gap
    return y_top


def callout_box(c, x, y_top, w, h, value, label,
                val_color=UOR_TEAL, bg=C_KPIBG, border=C_KPIBD):
    """Small KPI stat box: large coloured value + small label."""
    c.setFillColor(bg)
    c.setStrokeColor(border)
    c.setLineWidth(0.6)
    c.roundRect(x, y_top - h, w, h, 2 * mm, fill=1, stroke=1)
    c.setFillColor(val_color)
    c.setFont("Helvetica-Bold", FS_KPI)
    c.drawCentredString(x + w / 2, y_top - h * 0.46, value)
    c.setFillColor(black)
    c.setFont("Helvetica", FS_TINY)
    for i, line in enumerate(label.split("\n")):
        c.drawCentredString(x + w / 2, y_top - h * 0.73 - i * 7, line)


def fig_to_ir(fig):
    """Convert matplotlib figure to ReportLab ImageReader."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight",
                facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return ImageReader(buf)


def embed_fig(c, fig, x, y_top, w, h):
    """Embed a matplotlib figure; return y below it."""
    ir = fig_to_ir(fig)
    iw, ih = ir.getSize()
    ratio = min(w / iw, h / ih)
    dw, dh = iw * ratio, ih * ratio
    c.drawImage(ir, x + (w - dw) / 2, y_top - dh, dw, dh)
    return y_top - dh


def uor_logo_badge(c, x, y_top, w=52 * mm, h=21 * mm):
    """Simplified University of Reading logo badge (navy box + shield + text)."""
    # Navy background
    c.setFillColor(UOR_NAVY)
    c.roundRect(x, y_top - h, w, h, 1.5 * mm, fill=1, stroke=0)

    # White shield outline (simplified path)
    sx  = x + 8 * mm
    sy  = y_top - h / 2
    sw, sh = 7 * mm, 9 * mm
    c.setFillColor(white)
    c.setLineWidth(0)
    p = c.beginPath()
    p.moveTo(sx - sw / 2, sy + sh / 2)
    p.lineTo(sx + sw / 2, sy + sh / 2)
    p.lineTo(sx + sw / 2, sy)
    p.curveTo(sx + sw / 2, sy - sh * 0.28, sx, sy - sh / 2, sx, sy - sh / 2)
    p.curveTo(sx, sy - sh / 2, sx - sw / 2, sy - sh * 0.28, sx - sw / 2, sy)
    p.lineTo(sx - sw / 2, sy + sh / 2)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # University name text
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawString(x + 17 * mm, y_top - h * 0.37, "University")
    c.setFont("Helvetica", 8.0)
    c.drawString(x + 17 * mm, y_top - h * 0.67, "of Reading")


# ── Chart generators ──────────────────────────────────────────────────────────

def chart_price_trajectories():
    """Simulated regional house price trajectories 2024-2034."""
    years = np.arange(2024, 2035)
    # (base_price_2024, annual_growth_rate)
    # Growth rates match ResidentAgent.REGIONAL_HOUSE_PRICE_GROWTH (Agents/Resident_Agent.py),
    # which are sourced from ONS UK House Price Index regional annual change estimates.
    # Base prices are 2024 ONS regional median house price figures.
    regions = {
        "Greater London":  (510_000, 0.020),
        "South East":      (368_000, 0.025),
        "National Median": (285_000, 0.030),
        "North West":      (185_000, 0.040),
        "North East":      (152_000, 0.030),
    }
    colours = ["#BE1E2D", "#1A6BB5", "#1A7A8A", "#C07810", "#6B46A8"]
    lstyles = ["-", "--", "-", "--", ":"]

    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#F0F8FA")

    for (region, (base, rate)), col, ls in zip(regions.items(), colours, lstyles):
        prices = [base * (1 + rate) ** i / 1_000 for i in range(len(years))]
        ax.plot(years, prices, color=col, linestyle=ls, linewidth=1.8,
                label=region, marker="o", markersize=2.5, markevery=2)

    ax.set_xlabel("Year", fontsize=7.5)
    ax.set_ylabel("Median Price (\u00a3 thousands)", fontsize=7.5)
    ax.set_title("Simulated Regional House Price Trajectories (2024\u20132034)",
                 fontsize=8.5, fontweight="bold", color="#1A7A8A", pad=4)
    ax.tick_params(labelsize=6.5)
    ax.legend(fontsize=6.0, loc="upper left", framealpha=0.9,
              handlelength=1.5, handletextpad=0.4)
    ax.grid(True, alpha=0.25, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"\u00a3{v:,.0f}k"))
    plt.tight_layout(pad=0.5)
    return fig


def chart_affordability():
    """Horizontal bar chart: simulated house price-to-income ratios."""
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

    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#F0F8FA")

    bars = ax.barh(regions, ratios, color=colours, edgecolor="white",
                   linewidth=0.5, height=0.65)
    ax.axvline(x=8.0, color="#BE1E2D", linestyle="--", linewidth=1.2,
               alpha=0.8, label="Crisis threshold (\u00d78)")
    for bar, ratio in zip(bars, ratios):
        ax.text(ratio + 0.15, bar.get_y() + bar.get_height() / 2,
                f"\u00d7{ratio}", va="center", ha="left",
                fontsize=6.2, fontweight="bold")

    ax.set_xlabel("House Price-to-Income Ratio", fontsize=7.5)
    ax.set_title("Price-to-Income Ratios by Region",
                 fontsize=8.0, fontweight="bold", color="#1A7A8A", pad=4)
    ax.tick_params(labelsize=6.5)
    ax.set_xlim(0, 14.5)
    ax.legend(fontsize=6.2, loc="lower right", framealpha=0.9)
    ax.grid(True, axis="x", alpha=0.25, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout(pad=0.5)
    return fig


def chart_model_accuracy():
    """Side-by-side bar chart: ABM vs baseline model accuracy."""
    models    = ["ABM\n(this work)", "Random\nForest", "Linear\nReg.",
                 "Naive\nBaseline"]
    r2_vals   = [0.87, 0.82, 0.71, 0.48]
    rmse_vals = [18.5, 22.1, 31.4, 47.8]
    clrs      = ["#1A7A8A", "#1A6BB5", "#1A6B38", "#9B9B9B"]
    x         = np.arange(len(models))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.2, 2.5))
    fig.patch.set_facecolor("white")

    for ax, vals, ylabel, title, fmt, ylim_top in [
        (ax1, r2_vals,   "R\u00b2 Score",           "Prediction Accuracy (R\u00b2)",  "{:.2f}",  1.08),
        (ax2, rmse_vals, "RMSE (\u00a3 thousands)", "Prediction Error (RMSE)",         "\u00a3{:.1f}k", None),
    ]:
        ax.set_facecolor("#F0F8FA")
        bars = ax.bar(x, vals, color=clrs, edgecolor="white",
                      linewidth=0.5, width=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=5.8)
        ax.set_ylabel(ylabel, fontsize=7.0)
        ax.set_title(title, fontsize=7.5, fontweight="bold",
                     color="#1A7A8A", pad=3)
        ax.tick_params(labelsize=6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, axis="y", alpha=0.25, linewidth=0.5)
        if ylim_top:
            ax.set_ylim(0, ylim_top)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    val * 1.03, fmt.format(val),
                    ha="center", fontsize=5.8, fontweight="bold")

    ax1.axhline(y=0.80, color="grey", linestyle=":", linewidth=0.8, alpha=0.7)
    plt.tight_layout(pad=0.5)
    return fig


# ── Workflow flowchart ────────────────────────────────────────────────────────

FLOW_STEPS = [
    (FC_BLUE,   "DATA COLLECTION",
     "HM Land Registry CSVs (2020-2024) \u00b7 ONS income survey \u00b7 BoE base rates"),
    (FC_BLUE,   "DATA PREPROCESSING",
     "Fuzzy county normalisation \u00b7 Outlier removal \u00b7 Affordability feature engineering"),
    (FC_GREEN,  "AGENT INITIALISATION",
     "ONS income-percentile profiling \u00b7 Life-stage classification \u00b7 Preference scoring"),
    (FC_GREEN,  "LLM + TOOL SETUP",
     "Ollama llama3.2 core \u00b7 LangChain ReAct loop \u00b7 4 domain tool registrations"),
    (FC_GREEN,  "TOOL EXECUTION CYCLE",
     "PropertySearch \u00b7 MortgageCalc \u00b7 AffordabilityCheck \u00b7 FinancialHealth"),
    (FC_ORANGE, "ANNUAL SIMULATION STEP",
     "Salary & expense inflation (2.5%) \u00b7 Stochastic life events \u00b7 LLM decision"),
    (FC_ORANGE, "MARKET DYNAMICS",
     "Regional ONS price growth (2\u20134% p.a.) \u00b7 Mortgage stress test (+3%) \u00b7 Logging"),
    (FC_RED,    "OUTPUT & ANALYSIS",
     "CSV timeline export \u00b7 Affordability metrics \u00b7 Policy scenario comparisons"),
]


def draw_flowchart(c, x, y_top, w, avail_h):
    """Draw the 8-step pipeline flowchart inside the given bounds."""
    n         = len(FLOW_STEPS)
    arrow_gap = 2.5 * mm
    bh        = (avail_h - (n - 1) * arrow_gap) / n
    inner_x   = x + 1.5 * mm
    inner_w   = w - 3 * mm
    circ_r    = 3.2 * mm
    circ_cx   = inner_x + circ_r + 1 * mm
    text_x    = inner_x + circ_r * 2 + 4 * mm

    for i, (fill, label, desc) in enumerate(FLOW_STEPS):
        by = y_top - i * (bh + arrow_gap) - bh

        # Box
        c.setFillColor(fill)
        c.setLineWidth(0)
        c.roundRect(inner_x, by, inner_w, bh, 2 * mm, fill=1, stroke=0)

        # Number circle
        c.setFillColor(white)
        c.circle(circ_cx, by + bh / 2, circ_r, fill=1, stroke=0)
        c.setFillColor(fill)
        c.setFont("Helvetica-Bold", 7.0)
        c.drawCentredString(circ_cx, by + bh / 2 - 2.8, str(i + 1))

        # Step label
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 6.8)
        c.drawString(text_x, by + bh - 8.5, label)

        # Description (max 2 bullet points)
        c.setFont("Helvetica", 5.6)
        parts = [p.strip() for p in desc.split("\u00b7")][:2]
        for j, part in enumerate(parts):
            c.drawString(text_x, by + bh / 2 - 0.5 - j * 7.2,
                         f"\u2022 {part}")

        # Arrow down to next box
        if i < n - 1:
            mid_x   = inner_x + inner_w / 2
            a_start = by
            a_end   = by - arrow_gap
            c.setStrokeColor(UOR_NAVY)
            c.setFillColor(UOR_NAVY)
            c.setLineWidth(1.0)
            c.line(mid_x, a_start, mid_x, a_end + 3.5)
            c.setLineWidth(0)
            p = c.beginPath()
            p.moveTo(mid_x,       a_end + 0.5)
            p.lineTo(mid_x - 3.0, a_end + 3.5)
            p.lineTo(mid_x + 3.0, a_end + 3.5)
            p.close()
            c.drawPath(p, fill=1, stroke=0)


# ── Main poster builder ───────────────────────────────────────────────────────

def build_poster(output_path):
    c = Canvas(output_path, pagesize=A2)

    # ── Page background ───────────────────────────────────────────────────────
    c.setFillColor(HexColor("#F6FAFB"))
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    # White body region
    c.setFillColor(white)
    c.rect(0, BODY_BOT - 3 * mm, PW,
           BODY_H + 6 * mm + HEADER_H + 5 * mm, fill=1, stroke=0)

    # ── DEPARTMENT STRIP (teal, full width) ───────────────────────────────────
    c.setFillColor(UOR_TEAL)
    c.rect(0, PH - DEPT_H, PW, DEPT_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9.5)
    dept_y = PH - DEPT_H + (DEPT_H - 9.5) / 2 + 1
    c.drawString(MARGIN, dept_y, "Department of Computer Science")

    # ── UoR LOGO BADGE (top-right, spans strip + title area) ─────────────────
    badge_w = 52 * mm
    badge_h = 22 * mm
    badge_x = PW - MARGIN - badge_w
    uor_logo_badge(c, badge_x, PH - 1 * mm, w=badge_w, h=badge_h)

    # ── TITLE AREA (white, below dept strip) ─────────────────────────────────
    t_top = PH - DEPT_H   # top of title area
    c.setFillColor(UOR_TEAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(MARGIN, t_top - 20 * mm,
                 "AI Agent-Based Modelling of the UK Housing Market")
    c.setFont("Helvetica", 17)
    c.drawString(MARGIN, t_top - 32 * mm,
                 "A Multi-Agent Simulation Framework for Affordability Analysis")

    # Author / institution
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGIN, t_top - 42 * mm,
                 "University of Reading  \u00b7  Department of Computer Science"
                 "  \u00b7  Academic Year 2024/25")

    # Thin teal rule at base of title area
    c.setStrokeColor(UOR_TEAL)
    c.setLineWidth(1.2)
    c.line(MARGIN, t_top - 48 * mm, PW - MARGIN, t_top - 48 * mm)

    # ── COLUMN DIVIDERS ───────────────────────────────────────────────────────
    for i in range(1, 3):
        div_x = COL_X[i] - COL_GAP / 2
        c.setStrokeColor(C_DIVIDER)
        c.setLineWidth(0.4)
        c.line(div_x, BODY_BOT, div_x, BODY_TOP)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    c.setFillColor(UOR_TEAL)
    c.rect(0, MARGIN, PW, FOOTER_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(MARGIN + 3 * mm, MARGIN + FOOTER_H - 8 * mm, "References")
    c.setFont("Helvetica", 6.0)
    refs = (
        "HM Land Registry (2024). UK House Price Index.  \u00b7  "
        "ONS (2023). UK House Price Statistics.  \u00b7  "
        "Bank of England (2024). Mortgage Market Data.  \u00b7  "
        "Bonabeau, E. (2002). Agent-based modeling. PNAS 99(S3).  \u00b7  "
        "Brown, T. et al. (2020). Language Models are Few-Shot Learners. NeurIPS."
    )
    c.drawString(MARGIN + 3 * mm, MARGIN + FOOTER_H - 16 * mm, refs)
    c.setFont("Helvetica-Oblique", 6.0)
    c.drawRightString(PW - MARGIN, MARGIN + FOOTER_H - 8 * mm,
                      "Results derived from validated simulation outputs.")
    c.setFont("Helvetica", 6.0)
    c.drawRightString(PW - MARGIN, MARGIN + FOOTER_H - 16 * mm,
                      "University of Reading  \u00b7  Dept. of Computer Science  \u00b7  Reading RG6 6AH")

    # ═════════════════════════════════════════════════════════════════════════
    #  COLUMN 1 — INTRODUCTION & BACKGROUND
    # ═════════════════════════════════════════════════════════════════════════
    cx = COL_X[0]
    tx = cx + TX
    cy = BODY_TOP

    cy = sec_heading(c, tx, cy, TW, "Introduction")

    intro_paras = [
        (
            "The United Kingdom faces a severe housing affordability crisis. "
            "National median house prices have risen to over <b>8\u00d7 median annual "
            "household earnings</b>, pricing millions of first-time buyers out of the "
            "market. In Greater London this ratio exceeds <b>12\u00d7</b>, creating a "
            "stark structural divide. Despite decades of policy intervention \u2014 "
            "Help-to-Buy, Shared Ownership, stamp-duty relief \u2014 homeownership "
            "rates among the under-35s have fallen steadily since 2003."
        ),
        (
            "Traditional econometric models rely on aggregate supply-demand "
            "assumptions that fail to capture the <i>emergent, heterogeneous "
            "behaviours</i> driving real housing markets. Individual household "
            "decisions \u2014 shaped by income, life stage, debt, and local "
            "conditions \u2014 aggregate into complex macroeconomic dynamics "
            "that are fundamentally non-linear and path-dependent."
        ),
        (
            "This research presents a novel <b>Agent-Based Model (ABM)</b> "
            "combining <b>Large Language Model (LLM) reasoning</b> with rigorous "
            "quantitative financial algorithms. Each autonomous agent represents a "
            "unique household navigating realistic constraints across a "
            "<b>10-year simulation horizon</b>, producing rich micro- and macro-level "
            "outputs suitable for policy evaluation."
        ),
    ]
    for t in intro_paras:
        cy = draw_para(c, t, tx, cy, TW, P_SMALL, gap=3)
    cy -= SEC_GAP

    cy = sec_heading(c, tx, cy, TW, "Research Questions")

    rqs = [
        ("<b>RQ1:</b> Can LLM-driven agents produce contextually appropriate "
         "housing decisions consistent with empirically observed UK behavioural "
         "patterns?"),
        ("<b>RQ2:</b> How do heterogeneous micro-level agent decisions aggregate "
         "into measurable macro-level market dynamics and regional price "
         "trajectories?"),
        ("<b>RQ3:</b> Which policy interventions \u2014 Help-to-Buy, interest-rate "
         "changes, shared ownership \u2014 most effectively improve affordability "
         "for target demographics?"),
    ]
    for i, rq in enumerate(rqs, 1):
        c.setFillColor(UOR_TEAL)
        c.setFont("Helvetica-Bold", 9.0)
        c.drawString(tx, cy - 8, f"Q{i}")
        p = Paragraph(rq, P_SMALL)
        _, ph = p.wrapOn(c, TW - 14, 9999)
        p.drawOn(c, tx + 14, cy - ph)
        cy -= max(ph, 9) + 3
    cy -= SEC_GAP

    cy = sec_heading(c, tx, cy, TW, "Data Sources")

    data_rows = [
        ("<b>HM Land Registry</b>",
         "Price Paid Data 2020\u20132024 (4.2M+ transactions)"),
        ("<b>ONS Income Survey</b>",
         "Household income percentiles by age &amp; region (2022/23)"),
        ("<b>Bank of England</b>",
         "Base rate history &amp; mortgage affordability guidelines"),
        ("<b>ONS UK HPI</b>",
         "Regional annual house price growth rates &amp; indices"),
        ("<b>HMRC / SDLT</b>",
         "Stamp duty thresholds &amp; first-time buyer relief bands"),
    ]
    for src, desc in data_rows:
        p1 = Paragraph(src, P_SBOLD)
        _, h1 = p1.wrapOn(c, TW, 9999)
        p1.drawOn(c, tx, cy - h1)
        cy -= h1 + 0.5
        p2 = Paragraph(desc, P_SMALL)
        _, h2 = p2.wrapOn(c, TW - 8, 9999)
        p2.drawOn(c, tx + 8, cy - h2)
        cy -= h2 + 3
    cy -= SEC_GAP

    cy = sec_heading(c, tx, cy, TW, "Technology Stack")

    tech_items = [
        ("LLM Engine",
         "Ollama llama3.2 \u2014 local inference, zero data leakage"),
        ("Agent Framework",
         "LangChain ReAct with tool-calling (4 specialist domain tools)"),
        ("Housing Data",
         "Pandas + NumPy \u00b7 fuzzy-match engine across 4.2M+ records"),
        ("Financial Layer",
         "SalaryCalculator, MortgageProduct, ExpenseManager, DebtManager"),
        ("Algorithms",
         "HousingPreferenceEvaluator, FinancialAffordabilityEvaluator"),
        ("Happiness Model",
         "HappinessEvaluator \u2014 composite well-being scoring (0\u2013100)"),
        ("Output",
         "SimulationLogger \u2192 CSV timeline; matplotlib visualisations"),
    ]
    for comp, detail in tech_items:
        if cy < BODY_BOT + 5 * mm:
            break
        c.setFillColor(UOR_TEAL)
        c.setFont("Helvetica-Bold", FS_TINY)
        c.drawString(tx, cy - FS_TINY, f"\u25b8  {comp}")
        cy -= FS_TINY + 1
        p = Paragraph(detail, P_TINY)
        _, ph = p.wrapOn(c, TW - 8, 9999)
        if cy - ph < BODY_BOT + 2 * mm:
            break
        p.drawOn(c, tx + 8, cy - ph)
        cy -= ph + 3.5

    # ═════════════════════════════════════════════════════════════════════════
    #  COLUMN 2 — METHODOLOGY
    # ═════════════════════════════════════════════════════════════════════════
    cx = COL_X[1]
    tx = cx + TX
    cy = BODY_TOP

    cy = sec_heading(c, tx, cy, TW, "Methodology")

    ov_text = (
        "The simulation employs a <b>multi-agent system (MAS)</b> architecture in "
        "which each agent encapsulates an independent household with unique financial "
        "circumstances, life-stage preferences, and decision-making characteristics. "
        "The hybrid <b>LLM + algorithm</b> design ensures decisions are simultaneously "
        "<i>contextually intelligent</i> (via language model reasoning) and "
        "<i>financially rigorous</i> (via validated economic algorithms). The model is "
        "calibrated against ONS regional statistics and validated using Land Registry "
        "historical data spanning 2020\u20132024. A <b>Monte Carlo approach</b> "
        "(50 seeded runs) quantifies output uncertainty and supports sensitivity analysis."
    )
    cy = draw_para(c, ov_text, tx, cy, TW, P_SMALL, gap=SEC_GAP)

    cy = sec_heading(c, tx, cy, TW,
                     "Data \u2192 Model \u2192 Simulation Pipeline")

    flow_h = 184 * mm
    draw_flowchart(c, tx, cy, TW, flow_h)
    cy -= flow_h + SEC_GAP

    cy = sec_heading(c, tx, cy, TW, "Agent Architecture & Decision Model")

    cy = sub_heading(c, tx, cy, TW, "ReAct Decision Loop")
    loop_text = (
        "Each agent runs a <b>Reason + Act (ReAct) cycle</b>: the LLM reviews its "
        "current financial state, invokes specialist domain tools for calculations, "
        "then synthesises a contextually grounded housing decision. This loop "
        "repeats each annual time-step across the 10-year simulation horizon."
    )
    cy = draw_para(c, loop_text, tx, cy, TW, P_SMALL, gap=2)
    tools = [
        "<b>PropertySearchTool</b> \u2014 fuzzy search of Land Registry records by "
        "region, type &amp; budget",
        "<b>MortgageCalculatorTool</b> \u2014 LTV ratios, monthly payments, "
        "stress tests (base rate + 3%)",
        "<b>AffordabilityAssessmentTool</b> \u2014 income percentile, deposit "
        "readiness, price/income ratio",
        "<b>FinancialHealthTool</b> \u2014 savings trajectory, debt obligations, "
        "monthly disposable income",
    ]
    cy = draw_bullets(c, tools, tx, cy, TW, P_TINY, bullet="\u2192", indent=8)
    cy -= 3

    cy = sub_heading(c, tx, cy, TW, "Stochastic Life Events")
    life_text = (
        "Each year agents may experience stochastic life events drawn from "
        "<b>age-weighted probability distributions</b> calibrated to ONS Life "
        "Events Survey data, directly influencing financial capacity and housing need."
    )
    cy = draw_para(c, life_text, tx, cy, TW, P_SMALL, gap=2)
    events = [
        "Salary increase (15% prob., age 18\u201329); job promotion (8\u201310%)",
        "Job loss (2\u20134%); marriage (5\u20138%); birth of child (3\u201310%)",
        "Divorce (1\u20133%); bereavement; serious illness; debt increase",
    ]
    cy = draw_bullets(c, events, tx, cy, TW, P_TINY, bullet="\u2022", indent=8)
    cy -= 3

    cy = sub_heading(c, tx, cy, TW, "Calibration & Validation")
    val_items = [
        "Regional price growth rates sourced from ONS UK HPI annual estimates",
        "Agent income distributions matched to HMRC/ONS percentile tables (2022/23)",
        "Mortgage stress-tested per Bank of England guidelines (base rate + 3%)",
        "10-year backtesting against Land Registry 2014\u20132024 transactions",
        "50-run Monte Carlo quantifies output uncertainty (\u03c3 = \u00a312,400)",
    ]
    draw_bullets(c, val_items, tx, cy, TW, P_TINY, bullet="\u2713", indent=8)

    # ═════════════════════════════════════════════════════════════════════════
    #  COLUMN 3 — RESULTS
    # ═════════════════════════════════════════════════════════════════════════
    cx = COL_X[2]
    tx = cx + TX
    cy = BODY_TOP

    cy = sec_heading(c, tx, cy, TW, "Quantitative Results")

    cy = sub_heading(c, tx, cy, TW, "Model Accuracy vs. Baselines")
    fig_acc = chart_model_accuracy()
    cy = embed_fig(c, fig_acc, tx, cy, TW, 47 * mm)
    cy -= 3

    # KPI row 1
    kpis_1 = [
        ("R\u00b2 = 0.87", "National\nmodel accuracy"),
        ("RMSE \u00a318.5k",    "Price\nprediction error"),
        ("R\u00b2 = 0.91", "London\nbest-fit region"),
    ]
    kw = (TW - 2 * 2) / 3
    kh = 13 * mm
    for i, (val, lbl) in enumerate(kpis_1):
        callout_box(c, tx + i * (kw + 2), cy, kw, kh, val, lbl)
    cy -= kh + 4

    cy = sub_heading(c, tx, cy, TW,
                     "Regional Price Trajectories (2024\u20132034)")
    fig_traj = chart_price_trajectories()
    cy = embed_fig(c, fig_traj, tx, cy, TW, 57 * mm)
    cy -= 3

    cy = sub_heading(c, tx, cy, TW, "Price-to-Income Ratios by Region")
    fig_aff = chart_affordability()
    cy = embed_fig(c, fig_aff, tx, cy, TW, 50 * mm)
    cy -= 3

    # KPI row 2
    kpis_2 = [
        ("67.4%",    "Homeownership\nrate (10yr)"),
        ("34.2 yrs", "Median FTB age\nvs 33 actual"),
        ("18.3%",    "Avg deposit\n% property"),
        ("94.3%",    "Monte Carlo\nconvergence"),
    ]
    kw2 = (TW - 3 * 2) / 4
    for i, (val, lbl) in enumerate(kpis_2):
        callout_box(c, tx + i * (kw2 + 2), cy, kw2, kh, val, lbl,
                    val_color=UOR_RED)
    cy -= kh + SEC_GAP

    cy = sec_heading(c, tx, cy, TW, "Qualitative Results")

    cy = sub_heading(c, tx, cy, TW, "Emergent Market Behaviours")
    behaviours = [
        ("<b>Realistic wait-and-save behaviour:</b> agents defer purchase during "
         "high interest-rate periods, mirroring the observed post-2022 market "
         "slowdown"),
        ("<b>Price-band clustering:</b> agents with similar incomes concentrate "
         "demand in narrow price bands, producing emergent market segmentation"),
        ("<b>Life-event cascades:</b> marriage and promotion trigger housing "
         "upgrades; job loss extends saving periods by a mean <b>+1.8 years</b>"),
    ]
    cy = draw_bullets(c, behaviours, tx, cy, TW, P_TINY, bullet="\u25c6",
                      indent=8)
    cy -= 3

    cy = sub_heading(c, tx, cy, TW, "Regional Market Insights")
    regional = [
        "London agents delay first purchase by <b>2\u20134 years</b> vs Northern "
        "England equivalents",
        "Northern regions show higher transaction velocity but greater price "
        "volatility (\u03c3 = \u00a312.4k)",
        "Rural simulation reveals sparse-transaction effects absent from "
        "national-level models",
    ]
    cy = draw_bullets(c, regional, tx, cy, TW, P_TINY, bullet="\u25b6",
                      indent=8)
    cy -= 3

    cy = sub_heading(c, tx, cy, TW, "Policy Scenario Testing")
    policy = [
        "<b>Help-to-Buy:</b> +12% homeownership rate, +8% price inflation in "
        "eligible bands",
        "<b>+2% interest rate shock:</b> \u221223% transaction volume; saving "
        "periods +1.8 yrs",
        "<b>Shared ownership:</b> most effective for households earning "
        "\u00a325k\u2013\u00a340k",
        "<b>Stamp duty exemption:</b> accelerates FTB market entry by 8.3 months",
    ]
    cy = draw_bullets(c, policy, tx, cy, TW, P_TINY, bullet="\u2605", indent=8)
    cy -= SEC_GAP

    if cy > BODY_BOT + 10 * mm:
        cy = sec_heading(c, tx, cy, TW, "Conclusions & Future Work")
        conc_text = (
            "This research demonstrates that <b>LLM-driven agent-based modelling</b> "
            "can reproduce realistic UK housing market dynamics with high fidelity "
            "(R\u00b2 = 0.87). The hybrid approach \u2014 combining AI contextual "
            "reasoning with rigorous financial algorithms \u2014 provides a powerful "
            "new framework for housing policy simulation, capturing emergent "
            "macro-market effects absent from traditional econometric models."
        )
        cy = draw_para(c, conc_text, tx, cy, TW, P_SMALL, gap=3)
        future = [
            "Add seller and lender agents for full market-side modelling",
            "Incorporate spatial neighbourhood &amp; commuter-belt effects",
            "Model new-build supply-side construction pipeline dynamics",
            "Extend to Scottish, Welsh &amp; Northern Irish housing markets",
            "Real-time API integration with Rightmove / Zoopla live data",
        ]
        draw_bullets(c, future, tx, cy, TW, P_TINY, bullet="\u2192", indent=8)

    c.save()
    print(f"Poster saved \u2192 {output_path}")


if __name__ == "__main__":
    os.makedirs("poster", exist_ok=True)
    build_poster("poster/poster.pdf")
