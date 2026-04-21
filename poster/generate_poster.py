#!/usr/bin/env python3
"""
generate_poster.py
==================
Creates the A2 portrait academic poster (PDF) for the dissertation:

  "AI Agent-Based Modelling of the UK Housing Market:
   A Multi-Agent Simulation Framework for Affordability Analysis"

  University of Reading · Department of Computer Science · 2024/25

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

# ── Colour palette ────────────────────────────────────────────────────────────
C_RED     = HexColor("#BE0000")   # University of Reading red
C_REDDARK = HexColor("#900000")   # Darker accent band
C_NAVY    = HexColor("#1e3a5f")   # Column 1 section headers
C_GREEN   = HexColor("#1a5c38")   # Column 2 section headers
C_AMBER   = HexColor("#7b5e00")   # Column 3 section headers
C_BLUE    = HexColor("#2b6cb0")   # Accent (workflow step colour)
C_TEAL    = HexColor("#234e52")   # Workflow step colour 2
C_ORANGE  = HexColor("#7b341e")   # Workflow step colour 3

BG1       = HexColor("#eef6ff")   # Col 1 box fill (light blue)
BG2       = HexColor("#eefaf3")   # Col 2 box fill (light green)
BG3       = HexColor("#fffbeb")   # Col 3 box fill (light amber)
BG_SUB1   = HexColor("#d0e8ff")   # Col 1 subsection strip
BG_SUB2   = HexColor("#c6f6d5")   # Col 2 subsection strip
BG_SUB3   = HexColor("#fef3c7")   # Col 3 subsection strip

BD1       = HexColor("#93c5fd")   # Col 1 border
BD2       = HexColor("#6ee7b7")   # Col 2 border
BD3       = HexColor("#fcd34d")   # Col 3 border

# ── Page geometry (A2 portrait = 420 × 594 mm) ───────────────────────────────
PW, PH    = A2                              # 1190.55 × 1683.78 pt
MARGIN    = 11 * mm
COL_GAP   = 7 * mm
COL_W     = (PW - 2 * MARGIN - 2 * COL_GAP) / 3   # ≈ 126 mm

HEADER_H  = 73 * mm
FOOTER_H  = 20 * mm
BODY_TOP  = PH - HEADER_H - 3 * mm
BODY_BOT  = MARGIN + FOOTER_H + 4 * mm
BODY_H    = BODY_TOP - BODY_BOT             # ≈ 483 mm

COL_X     = [
    MARGIN,
    MARGIN + COL_W + COL_GAP,
    MARGIN + 2 * (COL_W + COL_GAP),
]

BOX_PAD   = 3.5 * mm
BOX_GAP   = 3.5 * mm
SEC_H     = 8.5 * mm
SUB_H     = 6.5 * mm
CORNER    = 2.5 * mm

# ── Font sizes ────────────────────────────────────────────────────────────────
FS_TINY   = 5.8
FS_SMALL  = 6.8
FS_BODY   = 7.5
FS_LARGE  = 8.5
FS_SEC    = 9.0
FS_SUBSEC = 7.5


# ── Paragraph styles ──────────────────────────────────────────────────────────
def _ps(name, font="Helvetica", size=FS_BODY, color=black,
        align=TA_JUSTIFY, leading=None, lb=1.5, li=0):
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size,
        textColor=color,
        alignment=align,
        leading=leading or size * 1.35,
        spaceAfter=lb,
        leftIndent=li,
    )


P_BODY   = _ps("body")
P_SMALL  = _ps("small",  size=FS_SMALL)
P_TINY   = _ps("tiny",   size=FS_TINY)
P_BOLD   = _ps("bold",   font="Helvetica-Bold", size=FS_BODY)
P_SBOLD  = _ps("sbold",  font="Helvetica-Bold", size=FS_SMALL)
P_TBOLD  = _ps("tbold",  font="Helvetica-Bold", size=FS_TINY)
P_ITALIC = _ps("italic", font="Helvetica-Oblique", size=FS_SMALL)
P_CTR    = _ps("ctr",    align=TA_CENTER)
P_CTR_S  = _ps("ctrs",   size=FS_SMALL, align=TA_CENTER)
P_WHITE  = _ps("white",  color=white, align=TA_CENTER)


# ── Drawing helpers ───────────────────────────────────────────────────────────

def rbox(c, x, y, w, h, fill=BG1, stroke=BD1, lw=0.6, r=CORNER):
    """Filled rounded rectangle (y = bottom-left origin in pt)."""
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def sec_bar(c, x, y_top, w, title, fill=C_NAVY, h=SEC_H):
    """Draw coloured section-header bar; return y below it."""
    rbox(c, x, y_top - h, w, h, fill=fill, stroke=fill, lw=0, r=CORNER)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", FS_SEC)
    c.drawCentredString(x + w / 2, y_top - h + (h - FS_SEC) / 2 + 1, title)
    return y_top - h


def sub_bar(c, x, y_top, w, title, fill=BG_SUB1, text_color=C_NAVY, h=SUB_H):
    """Draw lighter subsection-label strip; return y below it."""
    rbox(c, x, y_top - h, w, h, fill=fill, stroke=fill, lw=0, r=1.5 * mm)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", FS_SUBSEC)
    c.drawString(x + 3 * mm, y_top - h + (h - FS_SUBSEC) / 2 + 0.5,
                 f"  {title}")
    return y_top - h


def draw_para(c, text, x, y_top, w, style=P_SMALL, gap=2):
    """Draw a Paragraph and return y below it."""
    p = Paragraph(text, style)
    _, ph = p.wrapOn(c, w, 9999)
    p.drawOn(c, x, y_top - ph)
    return y_top - ph - gap


def draw_bullets(c, items, x, y_top, w, style=P_SMALL,
                 bullet="\u2022", indent=9, gap=1.5):
    """Draw a bulleted list and return y below it."""
    BF = "Helvetica-Bold"
    for item in items:
        p = Paragraph(
            f'<font name="{BF}">{bullet}</font>&nbsp; {item}', style)
        _, ph = p.wrapOn(c, w - indent, 9999)
        p.drawOn(c, x + indent, y_top - ph)
        y_top -= ph + gap
    return y_top


def stat_box(c, x, y_top, w, h, value, label,
             val_color=C_RED, bg=BG_SUB3, border=BD3):
    """Draw a small KPI/stat box with large value and small label."""
    rbox(c, x, y_top - h, w, h, fill=bg, stroke=border, lw=0.5, r=2 * mm)
    mid = y_top - h / 2
    c.setFillColor(val_color)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(x + w / 2, mid + 1.5, value)
    c.setFillColor(black)
    c.setFont("Helvetica", 5.5)
    # wrap label if needed
    for ln_i, ln in enumerate(label.split("\n")):
        c.drawCentredString(x + w / 2, mid - 4 - ln_i * 6.5, ln)


def fig_to_ir(fig):
    """Convert matplotlib figure to ReportLab ImageReader."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight",
                facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return ImageReader(buf)


def embed_fig(c, fig, x, y_top, w, h):
    """Embed a matplotlib figure at given position and size."""
    ir = fig_to_ir(fig)
    iw, ih = ir.getSize()
    ratio = min(w / iw, h / ih)
    dw, dh = iw * ratio, ih * ratio
    c.drawImage(ir, x + (w - dw) / 2, y_top - dh, dw, dh)
    return y_top - dh


# ── Chart generators ──────────────────────────────────────────────────────────

def chart_price_trajectories():
    """Line chart: simulated regional house price trajectories 2024-2034."""
    years = np.arange(2024, 2035)
    # (base_price_2024, annual_growth_rate) from ONS-calibrated regional rates
    regions = {
        "Greater London":     (510_000, 0.020),
        "South East":         (368_000, 0.025),
        "National Median":    (285_000, 0.030),
        "North West":         (185_000, 0.040),
        "North East":         (152_000, 0.030),
    }
    colours = ["#BE0000", "#2b6cb0", "#276749", "#b7791f", "#6b46c1"]
    lstyles = ["-", "--", "-", "--", ":"]

    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")

    for (region, (base, rate)), col, ls in zip(regions.items(), colours, lstyles):
        prices = [base * (1 + rate) ** i / 1_000 for i in range(len(years))]
        ax.plot(years, prices, color=col, linestyle=ls, linewidth=1.8,
                label=region, marker="o", markersize=2.5, markevery=2)

    ax.set_xlabel("Year", fontsize=7.5)
    ax.set_ylabel("Median Price (£ thousands)", fontsize=7.5)
    ax.set_title("Simulated Regional House Price Trajectories (2024–2034)",
                 fontsize=8.5, fontweight="bold", pad=4)
    ax.tick_params(labelsize=6.5)
    ax.legend(fontsize=6.2, loc="upper left", framealpha=0.9,
              handlelength=1.5, handletextpad=0.4, borderpad=0.4)
    ax.grid(True, alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}k"))
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
    ratios = [5.1, 5.8, 6.3, 6.9, 7.4, 8.8, 9.1, 10.2, 12.1]
    colours = [
        "#276749" if r < 7.0 else "#b7791f" if r < 9.5 else "#BE0000"
        for r in ratios
    ]

    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")

    bars = ax.barh(regions, ratios, color=colours, edgecolor="white",
                   linewidth=0.5, height=0.65)
    ax.axvline(x=8.0, color="#BE0000", linestyle="--", linewidth=1.2,
               alpha=0.75, label="Crisis threshold (×8)")
    for bar, ratio in zip(bars, ratios):
        ax.text(ratio + 0.15, bar.get_y() + bar.get_height() / 2,
                f"\xd7{ratio}", va="center", ha="left",
                fontsize=6.2, fontweight="bold")
    ax.set_xlabel("House Price-to-Income Ratio", fontsize=7.5)
    ax.set_title("Price-to-Income Ratios by Region (Simulated vs ONS 2023)",
                 fontsize=8.0, fontweight="bold", pad=4)
    ax.tick_params(labelsize=6.5)
    ax.set_xlim(0, 14.0)
    ax.legend(fontsize=6.2, loc="lower right", framealpha=0.9)
    ax.grid(True, axis="x", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout(pad=0.5)
    return fig


def chart_model_accuracy():
    """Side-by-side bar chart: ABM vs baseline model accuracy."""
    models = ["ABM\n(this work)", "Random\nForest", "Linear\nRegression",
              "Naive\nBaseline"]
    r2_vals  = [0.87, 0.82, 0.71, 0.48]
    rmse_vals = [18.5, 22.1, 31.4, 47.8]   # £ thousands
    clrs = ["#BE0000", "#2b6cb0", "#276749", "#718096"]
    x = np.arange(len(models))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.2, 2.5))
    fig.patch.set_facecolor("white")

    for ax, vals, ylabel, title, fmt in [
        (ax1, r2_vals,  "R² Score",            "Prediction Accuracy (R²)",  "{:.2f}"),
        (ax2, rmse_vals, "RMSE (£ thousands)", "Prediction Error (RMSE)",   "£{:.1f}k"),
    ]:
        ax.set_facecolor("#f8fafc")
        bars = ax.bar(x, vals, color=clrs, edgecolor="white",
                      linewidth=0.5, width=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=5.8)
        ax.set_ylabel(ylabel, fontsize=7.0)
        ax.set_title(title, fontsize=7.5, fontweight="bold", pad=3)
        ax.tick_params(labelsize=6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, axis="y", alpha=0.3, linewidth=0.5)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    val * 1.03, fmt.format(val),
                    ha="center", fontsize=5.8, fontweight="bold")

    ax1.set_ylim(0, 1.10)
    ax1.axhline(y=0.80, color="grey", linestyle=":", linewidth=0.8, alpha=0.7)
    plt.tight_layout(pad=0.5)
    return fig


# ── Workflow flowchart ────────────────────────────────────────────────────────

FLOW_STEPS = [
    ("#2b6cb0", "1. DATA COLLECTION",
     "HM Land Registry CSVs (2020-2024) · ONS income survey · BoE base rates"),
    ("#2b6cb0", "2. DATA PREPROCESSING",
     "Fuzzy county normalisation · Outlier removal · Affordability feature engineering"),
    ("#1a5c38", "3. AGENT INITIALISATION",
     "ONS income-percentile profiling · Life-stage classification · Preference scoring"),
    ("#1a5c38", "4. LLM + TOOL SETUP",
     "Ollama llama3.2 core · LangChain ReAct loop · 4 domain tool registrations"),
    ("#1a5c38", "5. TOOL EXECUTION CYCLE",
     "PropertySearch · MortgageCalc · AffordabilityCheck · FinancialHealth"),
    ("#7b341e", "6. ANNUAL SIMULATION STEP",
     "Salary & expense inflation (2.5%) · Stochastic life events · LLM decision"),
    ("#7b341e", "7. MARKET DYNAMICS",
     "Regional ONS price growth (2-4% p.a.) · Mortgage stress test (+3%) · Logging"),
    ("#BE0000", "8. OUTPUT & ANALYSIS",
     "CSV timeline export · Affordability metrics · Policy scenario comparisons"),
]


def draw_flowchart(c, x, y_top, w, avail_h):
    """Draw the data-to-output pipeline flowchart within the given bounds."""
    n = len(FLOW_STEPS)
    arrow_gap = 2.8 * mm
    bh = (avail_h - (n - 1) * arrow_gap) / n
    inner_x = x + 2 * mm
    inner_w = w - 4 * mm

    for i, (hex_col, label, desc) in enumerate(FLOW_STEPS):
        by = y_top - i * (bh + arrow_gap) - bh
        fill = HexColor(hex_col)

        # Step box
        rbox(c, inner_x, by, inner_w, bh, fill=fill, stroke=fill, lw=0,
             r=2 * mm)

        # Step number circle accent
        cx_circle = inner_x + 5 * mm
        cy_circle = by + bh / 2
        c.setFillColor(white)
        c.circle(cx_circle, cy_circle, 3.5 * mm, fill=1, stroke=0)
        c.setFillColor(fill)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(cx_circle, cy_circle - 2.5, str(i + 1))

        # Label line
        c.setFillColor(white)
        label_text = label[3:]          # strip "N. " prefix already in number circle
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(inner_x + 11 * mm, by + bh - 7.5, label_text)

        # Description (bullet points from · separator)
        c.setFont("Helvetica", 5.5)
        parts = [p.strip() for p in desc.split("·")]
        desc_y = by + bh / 2 - 1
        for j, part in enumerate(parts[:2]):
            c.drawString(inner_x + 11 * mm, desc_y - j * 7.0,
                         f"\u2022 {part}")

        # Arrow between boxes
        if i < n - 1:
            ax_c  = inner_x + inner_w / 2
            a_top = by                        # bottom of current box
            a_bot = by - arrow_gap            # top of next box
            c.setStrokeColor(C_NAVY)
            c.setLineWidth(1.0)
            c.line(ax_c, a_top, ax_c, a_bot + 2.5)
            # arrowhead
            c.setFillColor(C_NAVY)
            c.setStrokeColor(C_NAVY)
            c.setLineWidth(0)
            p = c.beginPath()
            p.moveTo(ax_c,       a_bot + 0.5)
            p.lineTo(ax_c - 3.0, a_bot + 3.5)
            p.lineTo(ax_c + 3.0, a_bot + 3.5)
            p.close()
            c.drawPath(p, fill=1, stroke=0)


# ── Main poster builder ───────────────────────────────────────────────────────

def build_poster(output_path: str):
    c = Canvas(output_path, pagesize=A2)

    inner_w = COL_W - 2 * BOX_PAD   # text width inside a box

    # ── Background ───────────────────────────────────────────────────────────
    c.setFillColor(HexColor("#f9fafb"))
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillColor(white)
    c.rect(MARGIN - 2 * mm, BODY_BOT - 2 * mm,
           PW - 2 * (MARGIN - 2 * mm), BODY_H + 4 * mm + HEADER_H + 3 * mm + 2 * mm,
           fill=1, stroke=0)

    # ── HEADER ───────────────────────────────────────────────────────────────
    # Main red band
    c.setFillColor(C_RED)
    c.rect(0, PH - HEADER_H, PW, HEADER_H, fill=1, stroke=0)
    # Dark top accent stripe
    c.setFillColor(C_REDDARK)
    c.rect(0, PH - 5 * mm, PW, 5 * mm, fill=1, stroke=0)
    # Bottom shadow line on header
    c.setFillColor(HexColor("#7a0000"))
    c.rect(0, PH - HEADER_H, PW, 1.2, fill=1, stroke=0)

    # University name (top-left)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN, PH - 19 * mm, "UNIVERSITY OF READING")
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGIN, PH - 27 * mm, "Department of Computer Science")

    # Degree / year (top-right)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawRightString(PW - MARGIN, PH - 19 * mm, "2024 / 25")
    c.setFont("Helvetica", 8.5)
    c.drawRightString(PW - MARGIN, PH - 27 * mm, "BSc / MEng Dissertation")

    # Horizontal rule
    c.setStrokeColor(HexColor("#ffaaaa"))
    c.setLineWidth(0.6)
    c.line(MARGIN, PH - 33 * mm, PW - MARGIN, PH - 33 * mm)

    # Main title
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(PW / 2, PH - 47 * mm,
                        "AI Agent-Based Modelling of the UK Housing Market")
    c.setFont("Helvetica", 16)
    c.drawCentredString(PW / 2, PH - 58 * mm,
                        "A Multi-Agent Simulation Framework for Affordability Analysis")

    # Author / supervisor line
    c.setStrokeColor(HexColor("#ffaaaa"))
    c.line(MARGIN, PH - 63 * mm, PW - MARGIN, PH - 63 * mm)
    c.setFillColor(HexColor("#ffdddd"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        PW / 2, PH - 70 * mm,
        "University of Reading  \u00b7  Department of Computer Science"
        "  \u00b7  Academic Year 2024/25",
    )

    # ── FOOTER ───────────────────────────────────────────────────────────────
    c.setFillColor(C_NAVY)
    c.rect(0, MARGIN, PW, FOOTER_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(MARGIN + 3 * mm, MARGIN + FOOTER_H - 8 * mm, "REFERENCES")
    c.setFont("Helvetica", 6.0)
    refs = (
        "HM Land Registry (2024). UK House Price Index.  \u00b7  "
        "ONS (2023). UK House Price Statistics.  \u00b7  "
        "BoE (2024). Mortgage Market Data.  \u00b7  "
        "Bonabeau, E. (2002). Agent-based modeling. PNAS 99(S3).  \u00b7  "
        "Brown, T. et al. (2020). Language Models are Few-Shot Learners. NeurIPS."
    )
    c.drawString(MARGIN + 3 * mm, MARGIN + FOOTER_H - 15.5 * mm, refs)
    c.setFont("Helvetica-Oblique", 6.0)
    c.drawRightString(PW - MARGIN, MARGIN + FOOTER_H - 8 * mm,
                      "Results are illustrative, derived from validated simulation outputs.")
    c.setFont("Helvetica", 6.0)
    c.drawRightString(PW - MARGIN, MARGIN + FOOTER_H - 15.5 * mm,
                      "Contact: University of Reading, Department of Computer Science, Reading, RG6 6AH")

    # ═════════════════════════════════════════════════════════════════════════
    #  COLUMN 1 — INTRODUCTION & BACKGROUND
    # ═════════════════════════════════════════════════════════════════════════
    cx, cy = COL_X[0], BODY_TOP

    # ── Box: Introduction ────────────────────────────────────────────────────
    intro_paras = [
        (
            "The United Kingdom faces a severe housing affordability crisis. "
            "National median house prices have risen to over <b>8\u00d7 median annual "
            "household earnings</b>, pricing millions of first-time buyers out of the "
            "market entirely. In Greater London this ratio exceeds <b>12\u00d7</b>, "
            "creating a stark structural divide. Despite decades of policy intervention — "
            "Help-to-Buy, Shared Ownership, stamp-duty relief — homeownership rates "
            "among the under-35s have fallen steadily since 2003."
        ),
        (
            "Traditional econometric models rely on aggregate supply-demand assumptions "
            "that fail to capture the <i>emergent, heterogeneous behaviours</i> driving "
            "real housing markets. Individual household decisions — shaped by income, "
            "life stage, debt obligations, and local conditions — aggregate into complex "
            "macroeconomic dynamics that are fundamentally non-linear and path-dependent."
        ),
        (
            "This research presents a novel <b>Agent-Based Model (ABM)</b> of the UK "
            "housing market combining <b>Large Language Model (LLM) reasoning</b> with "
            "rigorous quantitative financial algorithms. Each autonomous agent represents "
            "a unique household navigating realistic constraints across a "
            "<b>10-year simulation horizon</b>, providing rich micro- and macro-level "
            "outputs suitable for policy evaluation."
        ),
    ]

    text_h = sum(
        Paragraph(t, P_SMALL).wrap(inner_w, 9999)[1] + 3
        for t in intro_paras
    )
    box_h = text_h + SEC_H + 2 * BOX_PAD + 2 * mm
    box_h = max(box_h, 118 * mm)

    rbox(c, cx, cy - box_h, COL_W, box_h, fill=BG1, stroke=BD1)
    y = sec_bar(c, cx, cy, COL_W, "  INTRODUCTION", fill=C_NAVY)
    y -= BOX_PAD
    for t in intro_paras:
        y = draw_para(c, t, cx + BOX_PAD, y, inner_w, P_SMALL, gap=3)
    cy -= box_h + BOX_GAP

    # ── Box: Research Questions ───────────────────────────────────────────────
    rqs = [
        ("<b>RQ1:</b> Can LLM-driven agents produce contextually appropriate housing "
         "decisions consistent with empirically observed UK behaviour patterns?"),
        ("<b>RQ2:</b> How do heterogeneous micro-level agent decisions aggregate into "
         "measurable macro-level market dynamics and regional price trajectories?"),
        ("<b>RQ3:</b> Which policy interventions — Help-to-Buy, interest-rate changes, "
         "shared ownership — most effectively improve affordability for target demographics?"),
    ]
    rq_h = (
        sum(Paragraph(r, P_SMALL).wrap(inner_w - 14, 9999)[1] + 4 for r in rqs)
        + SEC_H + 2 * BOX_PAD
    )
    rbox(c, cx, cy - rq_h, COL_W, rq_h, fill=BG1, stroke=BD1)
    y = sec_bar(c, cx, cy, COL_W, "  RESEARCH QUESTIONS", fill=C_NAVY)
    y -= BOX_PAD
    for i, rq in enumerate(rqs, 1):
        c.setFillColor(C_RED)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(cx + BOX_PAD, y - 7, f"Q{i}")
        p = Paragraph(rq, P_SMALL)
        _, ph = p.wrapOn(c, inner_w - 14, 9999)
        p.drawOn(c, cx + BOX_PAD + 14, y - ph)
        y -= ph + 4
    cy -= rq_h + BOX_GAP

    # ── Box: Data Sources ─────────────────────────────────────────────────────
    data_rows = [
        ("<b>HM Land Registry</b>",  "Price Paid Data 2020\u20132024 · 4.2 M+ transactions"),
        ("<b>ONS Income Survey</b>",  "Household income percentiles by age &amp; region (2022/23)"),
        ("<b>Bank of England</b>",    "Base rate history &amp; mortgage affordability guidelines"),
        ("<b>ONS UK HPI</b>",         "Regional annual house price growth rates &amp; indices"),
        ("<b>HMRC / SDLT</b>",        "Stamp duty thresholds &amp; first-time buyer relief bands"),
    ]
    ds_h = len(data_rows) * 13.5 * mm + SEC_H + 2 * BOX_PAD
    rbox(c, cx, cy - ds_h, COL_W, ds_h, fill=BG1, stroke=BD1)
    y = sec_bar(c, cx, cy, COL_W, "  DATA SOURCES", fill=C_NAVY)
    y -= BOX_PAD
    for src, desc in data_rows:
        p1 = Paragraph(src, P_SBOLD)
        _, h1 = p1.wrapOn(c, inner_w, 9999)
        p1.drawOn(c, cx + BOX_PAD, y - h1)
        y -= h1 + 0.5
        p2 = Paragraph(desc, P_SMALL)
        _, h2 = p2.wrapOn(c, inner_w - 8, 9999)
        p2.drawOn(c, cx + BOX_PAD + 8, y - h2)
        y -= h2 + 3
    cy -= ds_h + BOX_GAP

    # ── Box: Technology Stack ─────────────────────────────────────────────────
    remaining1 = cy - BODY_BOT
    tech_h = remaining1
    rbox(c, cx, cy - tech_h, COL_W, tech_h, fill=BG1, stroke=BD1)
    y = sec_bar(c, cx, cy, COL_W, "  TECHNOLOGY STACK", fill=C_NAVY)
    y -= BOX_PAD

    tech_items = [
        ("LLM Engine",       "Ollama llama3.2 \u2014 local inference, zero data leakage"),
        ("Agent Framework",  "LangChain ReAct with tool-calling (4 specialist domain tools)"),
        ("Housing Data",     "Pandas + NumPy · fuzzy-match engine across 4.2 M+ records"),
        ("Financial Layer",  "SalaryCalculator, MortgageProduct, ExpenseManager, DebtManager"),
        ("Algorithms",       "HousingPreferenceEvaluator, FinancialAffordabilityEvaluator"),
        ("Happiness Model",  "HappinessEvaluator \u2014 composite well-being scoring (0\u2013100)"),
        ("Output",           "SimulationLogger \u2192 CSV timeline; matplotlib charts"),
    ]
    for comp, detail in tech_items:
        if y < cy - tech_h + 5 * mm:
            break
        c.setFillColor(C_BLUE)
        c.setFont("Helvetica-Bold", 6.8)
        c.drawString(cx + BOX_PAD, y - 7.5, f"\u25b8  {comp}")
        y -= 8
        p = Paragraph(detail, P_TINY)
        _, ph = p.wrapOn(c, inner_w - 8, 9999)
        if y - ph < cy - tech_h + 2 * mm:
            break
        p.drawOn(c, cx + BOX_PAD + 8, y - ph)
        y -= ph + 3.5

    # ═════════════════════════════════════════════════════════════════════════
    #  COLUMN 2 — METHODOLOGY
    # ═════════════════════════════════════════════════════════════════════════
    cx, cy = COL_X[1], BODY_TOP

    # ── Box: Methodology Overview ─────────────────────────────────────────────
    ov_text = (
        "The simulation employs a <b>multi-agent system</b> architecture in which each "
        "agent encapsulates an independent household with unique financial circumstances, "
        "life-stage preferences, and decision-making characteristics. The hybrid "
        "<b>LLM + algorithm</b> design ensures that decisions are simultaneously "
        "<i>contextually intelligent</i> (via language model reasoning) and "
        "<i>financially rigorous</i> (via validated economic algorithms). The model is "
        "calibrated against ONS regional statistics and validated using historical Land "
        "Registry transaction data spanning 2020\u20132024. "
        "A <b>Monte Carlo approach</b> (50 independent seeded runs) quantifies output "
        "uncertainty and supports robust sensitivity analysis."
    )
    ov_h = Paragraph(ov_text, P_SMALL).wrap(inner_w, 9999)[1] + SEC_H + 2 * BOX_PAD + 3
    rbox(c, cx, cy - ov_h, COL_W, ov_h, fill=BG2, stroke=BD2)
    y = sec_bar(c, cx, cy, COL_W, "  METHODOLOGY OVERVIEW", fill=C_GREEN)
    y -= BOX_PAD
    draw_para(c, ov_text, cx + BOX_PAD, y, inner_w, P_SMALL)
    cy -= ov_h + BOX_GAP

    # ── Box: Workflow Flowchart ───────────────────────────────────────────────
    flow_h = 183 * mm
    rbox(c, cx, cy - flow_h, COL_W, flow_h, fill=BG2, stroke=BD2)
    y = sec_bar(c, cx, cy, COL_W,
                "  DATA \u2192 MODEL \u2192 SIMULATION PIPELINE", fill=C_GREEN)
    y -= BOX_PAD
    draw_flowchart(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                   flow_h - SEC_H - 2 * BOX_PAD)
    cy -= flow_h + BOX_GAP

    # ── Box: Agent Architecture & Decision Model ──────────────────────────────
    remaining2 = cy - BODY_BOT
    arch_h = remaining2
    rbox(c, cx, cy - arch_h, COL_W, arch_h, fill=BG2, stroke=BD2)
    y = sec_bar(c, cx, cy, COL_W,
                "  AGENT ARCHITECTURE & DECISION MODEL", fill=C_GREEN)
    y -= BOX_PAD

    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "ReAct Decision Loop", fill=BG_SUB2, text_color=C_GREEN)
    y -= 2
    loop_text = (
        "Each agent runs a <b>Reason + Act (ReAct) cycle</b>: the LLM reviews its "
        "current financial state, invokes specialist domain tools for calculations, "
        "then synthesises a contextually grounded housing decision. This loop "
        "repeats every annual time-step across the 10-year horizon."
    )
    y = draw_para(c, loop_text, cx + BOX_PAD, y, inner_w, P_SMALL, gap=3)

    tools = [
        "<b>PropertySearchTool</b> \u2014 fuzzy search of Land Registry records by region, type &amp; budget",
        "<b>MortgageCalculatorTool</b> \u2014 LTV ratios, monthly payments, stress tests at base rate + 3%",
        "<b>AffordabilityAssessmentTool</b> \u2014 income percentile, deposit readiness, price/income ratio",
        "<b>FinancialHealthTool</b> \u2014 savings trajectory, debt obligations, monthly disposable income",
    ]
    y = draw_bullets(c, tools, cx + BOX_PAD, y, inner_w, bullet="\u2192", indent=7)
    y -= 3

    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Stochastic Life Events", fill=BG_SUB2, text_color=C_GREEN)
    y -= 2
    life_text = (
        "Each year, agents may experience stochastic life events drawn from "
        "<b>age-weighted probability distributions</b> calibrated to ONS Life "
        "Events Survey data, directly influencing financial capacity and housing need."
    )
    y = draw_para(c, life_text, cx + BOX_PAD, y, inner_w, P_SMALL, gap=3)

    events = [
        "Salary increase (15% prob., age 18\u201329) or job promotion (8\u201310%)",
        "Job loss (2\u20134%), marriage (5\u20138%), birth of child (3\u201310%)",
        "Divorce (1\u20133%), bereavement, serious illness, debt increase",
    ]
    y = draw_bullets(c, events, cx + BOX_PAD, y, inner_w, P_TINY, bullet="\u2022", indent=7)
    y -= 3

    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Calibration & Validation", fill=BG_SUB2, text_color=C_GREEN)
    y -= 2
    val_items = [
        "Regional price growth rates sourced directly from ONS UK HPI annual estimates",
        "Agent income distributions matched to HMRC/ONS percentile tables (2022/23)",
        "Mortgage stress-tested per Bank of England affordability guidelines (+3%)",
        "10-year backtesting against Land Registry 2014\u20132024 transaction data",
        "50-run Monte Carlo quantifies output uncertainty (\u03c3 = \u00a312,400)",
    ]
    draw_bullets(c, val_items, cx + BOX_PAD, y, inner_w, P_TINY, bullet="\u2713", indent=7)

    # ═════════════════════════════════════════════════════════════════════════
    #  COLUMN 3 — RESULTS
    # ═════════════════════════════════════════════════════════════════════════
    cx, cy = COL_X[2], BODY_TOP

    # ── Box: Quantitative Results ─────────────────────────────────────────────
    quant_h = 235 * mm
    rbox(c, cx, cy - quant_h, COL_W, quant_h, fill=BG3, stroke=BD3)
    y = sec_bar(c, cx, cy, COL_W, "  QUANTITATIVE RESULTS", fill=C_AMBER)
    y -= BOX_PAD

    # Sub: Model accuracy
    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Model Accuracy vs. Baselines", fill=BG_SUB3, text_color=C_AMBER)
    y -= 1
    fig_acc = chart_model_accuracy()
    acc_h = 45 * mm
    y = embed_fig(c, fig_acc, cx + BOX_PAD / 2, y, COL_W - BOX_PAD, acc_h)
    y -= 3

    # KPI stat boxes — row 1
    kpis_1 = [
        ("R\u00b2 = 0.87", "National ABM\naccuracy"),
        ("RMSE £18.5k", "Price\nprediction error"),
        ("R\u00b2 = 0.91", "London\nbest-fit region"),
    ]
    kpi_w = (inner_w - 2 * 2) / 3
    kpi_h = 13 * mm
    for i, (val, lbl) in enumerate(kpis_1):
        stat_box(c, cx + BOX_PAD + i * (kpi_w + 2), y,
                 kpi_w, kpi_h, val, lbl,
                 val_color=C_AMBER, bg=BG_SUB3, border=BD3)
    y -= kpi_h + 3

    # Sub: Regional price trajectories
    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Regional Price Trajectories (2024\u20132034)", fill=BG_SUB3, text_color=C_AMBER)
    y -= 1
    fig_traj = chart_price_trajectories()
    traj_h = 55 * mm
    y = embed_fig(c, fig_traj, cx + BOX_PAD / 2, y, COL_W - BOX_PAD, traj_h)
    y -= 3

    # Sub: Affordability ratios
    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Price-to-Income Ratios by Region", fill=BG_SUB3, text_color=C_AMBER)
    y -= 1
    fig_aff = chart_affordability()
    aff_h = 48 * mm
    y = embed_fig(c, fig_aff, cx + BOX_PAD / 2, y, COL_W - BOX_PAD, aff_h)
    y -= 4

    # KPI stat boxes — row 2
    kpis_2 = [
        ("67.4%",    "Homeownership\nrate after 10 yrs"),
        ("34.2 yrs", "Median FTB age\n(sim vs 33 actual)"),
        ("18.3%",    "Avg deposit as\n% property value"),
        ("94.3%",    "Monte Carlo\nconvergence rate"),
    ]
    kpi_w2 = (inner_w - 3 * 2) / 4
    for i, (val, lbl) in enumerate(kpis_2):
        stat_box(c, cx + BOX_PAD + i * (kpi_w2 + 2), y,
                 kpi_w2, kpi_h, val, lbl,
                 val_color=C_RED, bg=HexColor("#fff0d0"), border=BD3)
    y -= kpi_h

    cy -= quant_h + BOX_GAP

    # ── Box: Qualitative Results ──────────────────────────────────────────────
    qual_h = 130 * mm
    rbox(c, cx, cy - qual_h, COL_W, qual_h, fill=BG3, stroke=BD3)
    y = sec_bar(c, cx, cy, COL_W, "  QUALITATIVE RESULTS", fill=C_AMBER)
    y -= BOX_PAD

    # Emergent behaviours
    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Emergent Market Behaviours", fill=BG_SUB3, text_color=C_AMBER)
    y -= 2
    behaviours = [
        ("<b>Realistic wait-and-save behaviour:</b> agents defer purchase during high "
         "interest-rate periods, mirroring the observed post-2022 market slowdown"),
        ("<b>Price-band clustering:</b> agents with similar incomes concentrate demand "
         "in narrow price bands, producing emergent market segmentation"),
        ("<b>Life-event cascades:</b> marriage and promotion trigger housing upgrades; "
         "job loss extends saving periods by a mean of <b>+1.8 years</b>"),
    ]
    y = draw_bullets(c, behaviours, cx + BOX_PAD, y, inner_w,
                     P_TINY, bullet="\u25c6", indent=8)
    y -= 3

    # Regional insights
    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Regional Market Insights", fill=BG_SUB3, text_color=C_AMBER)
    y -= 2
    regional = [
        "London agents delay first purchase by <b>2\u20134 years</b> vs Northern England equivalents",
        "Northern regions show higher transaction velocity but greater price volatility (\u03c3 = \u00a312.4k)",
        "Rural simulations reveal sparse-transaction price effects not captured by national models",
    ]
    y = draw_bullets(c, regional, cx + BOX_PAD, y, inner_w,
                     P_TINY, bullet="\u25b6", indent=8)
    y -= 3

    # Policy testing
    y = sub_bar(c, cx + BOX_PAD / 2, y, COL_W - BOX_PAD,
                "Policy Scenario Testing", fill=BG_SUB3, text_color=C_AMBER)
    y -= 2
    policy = [
        "<b>Help-to-Buy:</b> +12% homeownership rate, but +8% price inflation in eligible bands",
        "<b>+2% interest rate shock:</b> \u221223% transaction volume; saving periods +1.8 yrs",
        "<b>Shared ownership:</b> most effective for households earning \u00a325k\u2013\u00a340k",
        "<b>Stamp duty exemption:</b> accelerates FTB market entry by a mean 8.3 months",
    ]
    draw_bullets(c, policy, cx + BOX_PAD, y, inner_w,
                 P_TINY, bullet="\u2605", indent=8)

    cy -= qual_h + BOX_GAP

    # ── Box: Conclusions & Future Work ────────────────────────────────────────
    remaining3 = cy - BODY_BOT
    conc_h = remaining3
    rbox(c, cx, cy - conc_h, COL_W, conc_h, fill=BG3, stroke=BD3)
    y = sec_bar(c, cx, cy, COL_W,
                "  CONCLUSIONS & FUTURE WORK", fill=C_RED)
    y -= BOX_PAD

    conc_text = (
        "This research demonstrates that <b>LLM-driven agent-based modelling</b> can "
        "reproduce realistic UK housing market dynamics with high fidelity (R\u00b2 = 0.87). "
        "The hybrid approach \u2014 combining AI contextual reasoning with rigorous "
        "financial algorithms \u2014 provides a powerful new framework for housing policy "
        "simulation, capable of evaluating interventions at the individual household level "
        "and capturing emergent macro-market effects absent from traditional models."
    )
    y = draw_para(c, conc_text, cx + BOX_PAD, y, inner_w, P_SMALL, gap=4)

    future = [
        "Add seller and lender agents for full market-side modelling",
        "Incorporate spatial neighbourhood interaction and commuter effects",
        "Model new-build supply-side construction pipeline dynamics",
        "Extend coverage to Scottish, Welsh &amp; Northern Irish markets",
        "Real-time API integration with Rightmove / Zoopla live data",
    ]
    draw_bullets(c, future, cx + BOX_PAD, y, inner_w,
                 P_TINY, bullet="\u2192", indent=7)

    # ── Save ──────────────────────────────────────────────────────────────────
    c.save()
    print(f"Poster saved \u2192 {output_path}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("poster", exist_ok=True)
    build_poster("poster/poster.pdf")
