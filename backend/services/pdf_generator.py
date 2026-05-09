"""
PDF Report Generator for KMU-Comply compliance reports.
Uses fpdf (not fpdf2). Public entry point: generate_pdf(report) -> bytes.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from fpdf import FPDF, XPos, YPos

from models.compliance_report import ComplianceReport
from models.enums import ComplianceStatus, Priority

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo-dark-bg.png"

REG_LABELS: dict[str, str] = {
    "gdpr_dsgvo": "GDPR / DSGVO",
    "bdsg":       "BDSG",
    "lksg":       "LkSG",
    "enefg":      "EnEfG",
    "csrd":       "CSRD",
    "nis2":       "NIS2",
    "eu_ai_act":  "EU AI Act",
    "hinschg":    "HinSchG",
    "arbschg":    "ArbSchG",
    "agg":        "AGG",
    "milog":      "MiLoG",
}

# Colour palette
NAVY        = (15,  33,  69)
NAVY_LIGHT  = (25,  55, 110)
WHITE       = (255, 255, 255)
LIGHT_GREY  = (245, 246, 248)
MID_GREY    = (180, 185, 195)
DARK_GREY   = (80,  90, 105)
BLACK       = (30,  30,  30)

# Status colours (R, G, B)
STATUS_COLOURS: dict[ComplianceStatus, tuple[int, int, int]] = {
    ComplianceStatus.COMPLIANT:           (39,  174,  96),   # green
    ComplianceStatus.PARTIALLY_COMPLIANT: (230, 162,   0),   # amber
    ComplianceStatus.NON_COMPLIANT:       (192,  57,  43),   # red
    ComplianceStatus.CANNOT_ASSESS:       (127, 140, 148),   # grey
}

STATUS_LABELS: dict[ComplianceStatus, str] = {
    ComplianceStatus.COMPLIANT:           "Compliant",
    ComplianceStatus.PARTIALLY_COMPLIANT: "Partial",
    ComplianceStatus.NON_COMPLIANT:       "Non-Compliant",
    ComplianceStatus.CANNOT_ASSESS:       "Cannot Assess",
}

PRIORITY_COLOURS: dict[Priority, tuple[int, int, int]] = {
    Priority.CRITICAL: (192,  57,  43),  # red
    Priority.HIGH:     (211, 105,  26),  # orange
    Priority.MEDIUM:   (230, 162,   0),  # amber
    Priority.LOW:      (39,  174,  96),  # green
}

PAGE_W    = 210   # A4 mm
PAGE_H    = 297
MARGIN    = 18
CONTENT_W = PAGE_W - 2 * MARGIN


# ---------------------------------------------------------------------------
# Text sanitiser
# ---------------------------------------------------------------------------

def _s(text: Optional[str]) -> str:
    """Sanitise arbitrary text for safe output in latin-1 fpdf cells."""
    if text is None:
        return ""
    text = str(text)
    # Unicode dashes -> hyphen
    text = text.replace("—", "-")   # em dash
    text = text.replace("–", "-")   # en dash
    # Curly / smart quotes -> straight
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    # Ellipsis character
    text = text.replace("…", "...")
    # German umlauts -> ASCII digraphs
    text = (text
            .replace("\xe4", "ae").replace("\xc4", "Ae")
            .replace("\xf6", "oe").replace("\xd6", "Oe")
            .replace("\xfc", "ue").replace("\xdc", "Ue")
            .replace("\xdf", "ss"))
    # Encode to latin-1, replacing anything still unrepresentable
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _reg_label(reg_value: str) -> str:
    return REG_LABELS.get(reg_value, reg_value.upper())


def _score_colour(score: float) -> tuple[int, int, int]:
    if score >= 75:
        return (39, 174, 96)    # green
    if score >= 40:
        return (230, 162, 0)    # amber
    return (192, 57, 43)        # red


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------

class KMUPdf(FPDF):
    """Custom FPDF subclass with branded header/footer and shared layout helpers."""

    def __init__(self, company_name: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.company_name = company_name
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self._is_cover = False

    # ------------------------------------------------------------------
    # Header / footer overrides
    # ------------------------------------------------------------------

    def header(self):
        if self._is_cover:
            return
        # Thin navy running header bar
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PAGE_W, 14, style="F")
        # Logo (small, ~7 mm height)
        if LOGO_PATH.exists():
            try:
                self.image(str(LOGO_PATH), x=MARGIN, y=3.5, h=7)
            except Exception:
                pass
        # Company name right-aligned in header
        self.set_xy(0, 3)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        self.cell(PAGE_W - MARGIN, 8, _s(self.company_name), align="R")
        self.set_text_color(*BLACK)
        # Push content below the header bar
        self.set_y(16)

    def footer(self):
        if self._is_cover:
            return
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MID_GREY)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")
        self.set_text_color(*BLACK)

    # ------------------------------------------------------------------
    # Reusable layout helpers
    # ------------------------------------------------------------------

    def section_title(self, title: str):
        """Bold navy section heading with underline rule."""
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*NAVY)
        self.cell(CONTENT_W, 8, _s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Underline rule
        self.set_draw_color(*NAVY_LIGHT)
        self.set_line_width(0.5)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.set_text_color(*BLACK)
        self.ln(3)

    def sub_title(self, title: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*NAVY_LIGHT)
        self.cell(CONTENT_W, 6, _s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*BLACK)
        self.ln(1)

    def body_text(self, text: str, indent: float = 0):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK_GREY)
        self.set_x(MARGIN + indent)
        self.multi_cell(CONTENT_W - indent, 5, _s(text))
        self.set_text_color(*BLACK)

    def label_value_row(self, label: str, value: str, label_w: float = 42, indent: float = 0):
        """Print a bold label followed by wrapped value text."""
        x0 = MARGIN + indent
        y0 = self.get_y()
        self.set_x(x0)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK_GREY)
        self.cell(label_w, 5, _s(label + ":"))
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.set_xy(x0 + label_w, y0)
        self.multi_cell(CONTENT_W - indent - label_w, 5, _s(value))

    def reg_subheading(self, reg_key: str):
        """Full-width navy sub-heading bar for a regulation section."""
        self.ln(3)
        self.set_fill_color(*NAVY_LIGHT)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.set_x(MARGIN)
        self.cell(CONTENT_W, 8, _s(_reg_label(reg_key)), fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*BLACK)
        self.ln(2)

    def separator_line(self):
        self.set_draw_color(*MID_GREY)
        self.set_line_width(0.2)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.set_draw_color(0, 0, 0)
        self.ln(2)

    def ensure_space(self, mm: float = 40):
        """Add a new page if less than mm space remains."""
        if self.get_y() > PAGE_H - mm:
            self.add_page()
            self.ln(2)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_cover(pdf: KMUPdf, report: ComplianceReport):
    """
    Cover page: dark navy top block (~120 mm) with logo placed directly
    on the dark background (no white box). White lower area with stats.
    """
    pdf._is_cover = True
    pdf.add_page()

    COVER_TOP = 122  # height of dark block in mm

    # --- Dark navy top block ---
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PAGE_W, COVER_TOP, style="F")

    # Logo directly on dark background
    if LOGO_PATH.exists():
        try:
            pdf.image(str(LOGO_PATH), x=MARGIN, y=10, h=18)
        except Exception:
            pass

    # "KMU-Comply" text (shown regardless of logo, acts as fallback label)
    pdf.set_xy(MARGIN, 11)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*WHITE)
    pdf.cell(80, 8, "KMU-Comply")

    # Report type label
    pdf.set_xy(MARGIN, 34)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(160, 185, 220)
    pdf.cell(CONTENT_W, 6, "COMPLIANCE ASSESSMENT REPORT")

    # Company name (large)
    pdf.set_xy(MARGIN, 44)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*WHITE)
    pdf.multi_cell(CONTENT_W - 42, 11, _s(report.company_name))

    # Generated date
    date_str = report.generated_at[:10] if report.generated_at else ""
    pdf.set_xy(MARGIN, 72)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(160, 185, 220)
    pdf.cell(CONTENT_W, 5, _s(f"Generated: {date_str}"))

    # --- Score badge (top-right of dark block) ---
    score    = report.overall_score_percent
    sc       = _score_colour(score)
    badge_x  = PAGE_W - MARGIN - 38
    badge_y  = 42
    badge_w  = 38
    badge_h  = 28

    pdf.set_fill_color(*sc)
    pdf.rect(badge_x, badge_y, badge_w, badge_h, style="F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(badge_x, badge_y + 4)
    pdf.cell(badge_w, 12, f"{score:.0f}%", align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(badge_x, badge_y + 17)
    pdf.cell(badge_w, 6, "Overall Score", align="C")

    # --- Stats row (bottom of dark block) ---
    n_applicable = sum(1 for r in report.applicable_regulations if r.applies)
    n_gaps       = len(report.gap_analysis)
    n_actions    = len(report.action_plan)
    n_critical   = sum(1 for a in report.action_plan if a.priority == Priority.CRITICAL)

    stats = [
        (str(n_applicable), "Regulations"),
        (str(n_gaps),        "Gaps Found"),
        (str(n_actions),     "Actions"),
        (str(n_critical),    "Critical"),
    ]
    stat_w = CONTENT_W / len(stats)
    stat_y = 82

    for i, (val, lbl) in enumerate(stats):
        sx = MARGIN + i * stat_w
        pdf.set_fill_color(*NAVY_LIGHT)
        pdf.rect(sx, stat_y, stat_w - 2, 16, style="F")
        pdf.set_xy(sx, stat_y + 1)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*WHITE)
        pdf.cell(stat_w - 2, 8, val, align="C")
        pdf.set_xy(sx, stat_y + 9)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(160, 185, 220)
        pdf.cell(stat_w - 2, 5, lbl, align="C")

    pdf.set_text_color(*BLACK)

    # --- White lower area ---

    # "Applicable Regulations" label
    pdf.set_xy(MARGIN, COVER_TOP + 8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(CONTENT_W, 6, "Applicable Regulations")
    pdf.ln(8)

    applicable = [r for r in report.applicable_regulations if r.applies]
    col_w = CONTENT_W / 3

    for i, reg_app in enumerate(applicable):
        col = i % 3
        row = i // 3
        rx = MARGIN + col * col_w
        ry = COVER_TOP + 18 + row * 8
        label = _reg_label(reg_app.regulation.value)
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.rect(rx, ry, col_w - 2, 6, style="F")
        pdf.set_xy(rx, ry)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*NAVY_LIGHT)
        pdf.cell(col_w - 2, 6, _s(label), align="C")

    # --- Disclaimer at bottom of cover ---
    pdf.set_xy(MARGIN, PAGE_H - 22)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*MID_GREY)
    pdf.multi_cell(
        CONTENT_W, 4,
        "This report is generated by an AI system and does not constitute legal advice. "
        "Consult a qualified legal professional before making compliance decisions."
    )

    pdf._is_cover = False


def _build_executive_summary(pdf: KMUPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_title("1. Executive Summary")

    if report.executive_summary:
        pdf.body_text(report.executive_summary)
    else:
        pdf.body_text("No executive summary available.")

    if report.inferred_characteristics:
        pdf.ln(4)
        pdf.sub_title("Inferred Company Characteristics")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_GREY)
        for ch in report.inferred_characteristics:
            pdf.set_x(MARGIN + 4)
            pdf.multi_cell(CONTENT_W - 4, 5, _s("- " + ch))
        pdf.set_text_color(*BLACK)

    if report.validation_warnings:
        pdf.ln(4)
        pdf.sub_title("Validation Warnings")
        pdf.set_font("Helvetica", "", 9)
        for w in report.validation_warnings:
            pdf.set_text_color(192, 57, 43)
            pdf.set_x(MARGIN + 4)
            pdf.multi_cell(CONTENT_W - 4, 5, _s("! " + w))
        pdf.set_text_color(*BLACK)

    if report.requires_manual_review:
        pdf.ln(4)
        pdf.sub_title("Sections Requiring Manual Review")
        pdf.set_font("Helvetica", "", 9)
        for item in report.requires_manual_review:
            pdf.set_text_color(211, 105, 26)
            pdf.set_x(MARGIN + 4)
            pdf.multi_cell(CONTENT_W - 4, 5, _s("- " + item))
        pdf.set_text_color(*BLACK)


def _build_regulation_applicability(pdf: KMUPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_title("2. Regulation Applicability")

    pdf.body_text(
        "The table below summarises which regulations apply to your organisation "
        "based on the submitted company profile."
    )
    pdf.ln(4)

    # Column widths
    col_reg    = 48
    col_app    = 22
    col_reason = CONTENT_W - col_reg - col_app

    # Header row
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(MARGIN)
    pdf.cell(col_reg,    7, "Regulation", fill=True)
    pdf.cell(col_app,    7, "Applies",    fill=True, align="C")
    pdf.cell(col_reason, 7, "Reason",     fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8.5)
    for idx, reg_app in enumerate(report.applicable_regulations):
        fill = LIGHT_GREY if idx % 2 == 0 else WHITE
        label        = _reg_label(reg_app.regulation.value)
        applies_str  = "Yes" if reg_app.applies else "No"
        applies_col  = (39, 174, 96) if reg_app.applies else MID_GREY
        reason_text  = _s(reg_app.reason)

        row_y = pdf.get_y()

        # Regulation name
        pdf.set_fill_color(*fill)
        pdf.set_text_color(*DARK_GREY)
        pdf.set_x(MARGIN)
        pdf.cell(col_reg, 6, _s(label), fill=True)

        # Applies badge
        pdf.set_fill_color(*applies_col)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_app, 6, applies_str, fill=True, align="C")

        # Reason - multi_cell resets x; use set_xy after
        reason_x = MARGIN + col_reg + col_app
        pdf.set_fill_color(*fill)
        pdf.set_text_color(*DARK_GREY)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(reason_x, row_y)
        pdf.multi_cell(col_reason, 6, reason_text, fill=True)

        # Ensure cursor is below the tallest cell in this row
        new_y = max(pdf.get_y(), row_y + 6)
        pdf.set_xy(MARGIN, new_y)
        pdf.set_font("Helvetica", "", 8.5)

    pdf.set_text_color(*BLACK)


def _build_score_breakdown(pdf: KMUPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_title("3. Score Breakdown")

    # --- Overall score ---
    score = report.overall_score_percent
    sc    = _score_colour(score)

    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*sc)
    pdf.cell(CONTENT_W, 16, f"{score:.1f}%", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_GREY)
    pdf.cell(CONTENT_W, 5, "Overall Compliance Score", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*BLACK)
    pdf.ln(5)

    if not report.regulation_scores:
        pdf.body_text("No regulation scores available.")
        return

    # Column widths
    col_reg  = 40
    col_pct  = 18
    col_bar  = 52
    col_stat = 12
    col_tot  = 16

    # Header
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(MARGIN)
    pdf.cell(col_reg,  6, "Regulation",  fill=True)
    pdf.cell(col_pct,  6, "Score",       fill=True, align="C")
    pdf.cell(col_bar,  6, "Progress",    fill=True)
    pdf.cell(col_stat, 6, "C",           fill=True, align="C")
    pdf.cell(col_stat, 6, "Part.",       fill=True, align="C")
    pdf.cell(col_stat, 6, "NC",          fill=True, align="C")
    pdf.cell(col_stat, 6, "N/A",         fill=True, align="C")
    pdf.cell(col_tot,  6, "Total",       fill=True, align="C")
    pdf.ln()

    row_h = 7

    for idx, rs in enumerate(report.regulation_scores):
        fill       = LIGHT_GREY if idx % 2 == 0 else WHITE
        bar_colour = _score_colour(rs.score_percent)
        label      = _reg_label(rs.regulation.value)
        row_y      = pdf.get_y()

        pdf.set_fill_color(*fill)
        pdf.set_text_color(*DARK_GREY)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_x(MARGIN)
        pdf.cell(col_reg, row_h, _s(label), fill=True)

        # Score % in bar colour
        pdf.set_text_color(*bar_colour)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_pct, row_h, f"{rs.score_percent:.0f}%", fill=True, align="C")

        # Progress bar drawn at absolute coordinates
        bar_x = MARGIN + col_reg + col_pct
        bar_y = row_y + 1.5
        bar_h = 4.0
        # Track
        pdf.set_fill_color(*LIGHT_GREY)
        pdf.rect(bar_x, bar_y, col_bar, bar_h, style="F")
        # Fill
        filled_w = col_bar * (max(0.0, min(100.0, rs.score_percent)) / 100.0)
        if filled_w > 0:
            pdf.set_fill_color(*bar_colour)
            pdf.rect(bar_x, bar_y, filled_w, bar_h, style="F")

        # Restore fill & continue cells after bar
        pdf.set_fill_color(*fill)
        pdf.set_text_color(*DARK_GREY)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(bar_x + col_bar, row_y)
        pdf.cell(col_stat, row_h, str(rs.compliant),           fill=True, align="C")
        pdf.cell(col_stat, row_h, str(rs.partially_compliant), fill=True, align="C")
        pdf.cell(col_stat, row_h, str(rs.non_compliant),        fill=True, align="C")
        pdf.cell(col_stat, row_h, str(rs.cannot_assess),        fill=True, align="C")
        pdf.cell(col_tot,  row_h, str(rs.total_requirements),   fill=True, align="C")
        pdf.ln()

    pdf.set_text_color(*BLACK)
    pdf.ln(3)

    # Legend
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*DARK_GREY)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 5,
             "C = Compliant   Part. = Partially Compliant   NC = Non-Compliant   N/A = Cannot Assess")
    pdf.ln()
    pdf.set_text_color(*BLACK)


def _build_gap_analysis(pdf: KMUPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_title("4. Gap Analysis")

    pdf.body_text(
        "This section details every assessed requirement. Full evidence and deficiency "
        "descriptions are provided for each finding. No text is truncated."
    )

    # Group gaps by regulation
    gaps_by_reg: dict[str, list] = {}
    for gap in report.gap_analysis:
        gaps_by_reg.setdefault(gap.regulation.value, []).append(gap)

    for reg_key, gaps in gaps_by_reg.items():
        pdf.reg_subheading(reg_key)

        for gap in gaps:
            pdf.ensure_space(42)

            status_colour = STATUS_COLOURS.get(gap.status, MID_GREY)
            status_label  = STATUS_LABELS.get(gap.status, str(gap.status))

            # --- Article heading row ---
            row_y   = pdf.get_y()
            art_str = f"Art. {_s(gap.article_number)} - {_s(gap.article_title)}"

            pdf.set_fill_color(*LIGHT_GREY)
            pdf.rect(MARGIN, row_y, CONTENT_W, 7, style="F")

            # Article text (leave 36 mm on right for badge)
            pdf.set_xy(MARGIN + 2, row_y)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*NAVY_LIGHT)
            pdf.cell(CONTENT_W - 36, 7, _s(art_str))

            # Status badge
            badge_x = MARGIN + CONTENT_W - 34
            pdf.set_fill_color(*status_colour)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 7)
            pdf.rect(badge_x, row_y + 1, 34, 5, style="F")
            pdf.set_xy(badge_x, row_y + 1)
            pdf.cell(34, 5, _s(status_label), align="C")

            pdf.set_xy(MARGIN, row_y + 8)
            pdf.set_text_color(*BLACK)

            # --- Evidence (full, no truncation) ---
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*DARK_GREY)
            pdf.cell(22, 5, "Evidence:")
            pdf.ln()
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(CONTENT_W - 3, 5, _s(gap.evidence))

            # --- Deficiency (full, no truncation) ---
            if gap.deficiency_description:
                pdf.set_x(MARGIN + 3)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(192, 57, 43)
                pdf.cell(30, 5, "Deficiency:")
                pdf.ln()
                pdf.set_x(MARGIN + 3)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*DARK_GREY)
                pdf.multi_cell(CONTENT_W - 3, 5, _s(gap.deficiency_description))

            pdf.set_text_color(*BLACK)
            pdf.ln(2)
            pdf.separator_line()


def _build_action_plan(pdf: KMUPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_title("5. Action Plan")

    pdf.body_text(
        "The following actions are recommended to address identified compliance gaps. "
        "Priority and effort are indicated for each item. Full action text is shown."
    )
    pdf.ln(3)

    if not report.action_plan:
        pdf.body_text("No remediation actions required.")
        return

    # Group by regulation
    actions_by_reg: dict[str, list] = {}
    for action in report.action_plan:
        actions_by_reg.setdefault(action.regulation.value, []).append(action)

    for reg_key, actions in actions_by_reg.items():
        pdf.reg_subheading(reg_key)

        for act in actions:
            pdf.ensure_space(45)

            priority_colour = PRIORITY_COLOURS.get(act.priority, MID_GREY)
            row_y           = pdf.get_y()
            badge_w         = 24

            # Priority badge
            pdf.set_fill_color(*priority_colour)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 8)
            pdf.rect(MARGIN, row_y, badge_w, 6, style="F")
            pdf.set_xy(MARGIN, row_y)
            pdf.cell(badge_w, 6, _s(act.priority.value), align="C")

            # Article reference
            pdf.set_text_color(*NAVY_LIGHT)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(MARGIN + badge_w + 2, row_y)
            pdf.cell(CONTENT_W - badge_w - 2, 6, _s(f"Art. {act.article_number}"))
            pdf.ln()

            # Full action text (no truncation)
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK_GREY)
            pdf.multi_cell(CONTENT_W - 3, 5, _s(act.action))

            # Effort & Deadline
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*DARK_GREY)
            pdf.cell(22, 5, "Effort:")
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(52, 5, _s(act.estimated_effort))

            if act.deadline:
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(22, 5, "Deadline:")
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(0, 5, _s(act.deadline))
            pdf.ln()

            # Dependencies
            if act.dependencies:
                pdf.set_x(MARGIN + 3)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*DARK_GREY)
                pdf.cell(30, 5, "Dependencies:")
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(CONTENT_W - 33, 5, _s(", ".join(act.dependencies)))

            pdf.set_text_color(*BLACK)
            pdf.ln(2)
            pdf.separator_line()


def _build_closing(pdf: KMUPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_title("6. Closing & Disclaimer")

    pdf.ln(2)
    pdf.sub_title("Recommended Next Steps")

    next_steps = [
        "Review each gap finding with your legal or compliance team.",
        "Prioritise Critical and High priority action items immediately.",
        "Establish a compliance calendar with realistic deadlines from the Action Plan.",
        "Re-run this assessment after implementing changes to track your progress.",
        "Consult a qualified legal counsel for binding compliance decisions.",
    ]
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DARK_GREY)
    for step in next_steps:
        pdf.set_x(MARGIN + 4)
        pdf.multi_cell(CONTENT_W - 4, 5, _s(f"- {step}"))
    pdf.set_text_color(*BLACK)

    pdf.ln(6)
    pdf.sub_title("Legal Disclaimer")

    # Shaded disclaimer box
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*DARK_GREY)
    disc_y = pdf.get_y()
    # First pass: render to measure height
    pdf.set_x(MARGIN + 3)
    pdf.multi_cell(CONTENT_W - 6, 5, _s(report.disclaimer))
    disc_end_y = pdf.get_y()
    box_h = disc_end_y - disc_y + 4

    # Draw background rect then re-render text on top
    pdf.set_fill_color(*LIGHT_GREY)
    pdf.rect(MARGIN, disc_y - 2, CONTENT_W, box_h, style="F")
    pdf.set_xy(MARGIN + 3, disc_y)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*DARK_GREY)
    pdf.multi_cell(CONTENT_W - 6, 5, _s(report.disclaimer))

    pdf.set_text_color(*BLACK)
    pdf.ln(10)

    # Branding footer block
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(CONTENT_W, 6, "KMU-Comply - AI-Powered Compliance for German SMEs",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MID_GREY)
    pdf.cell(CONTENT_W, 5,
             "This report was generated automatically and is not a substitute for legal advice.",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*BLACK)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf(report: ComplianceReport) -> bytes:
    """
    Generate a professional compliance PDF report and return raw bytes.

    Args:
        report: A fully populated ComplianceReport instance.

    Returns:
        PDF file contents as bytes, suitable for HTTP streaming or writing to disk.
    """
    pdf = KMUPdf(company_name=report.company_name)

    _build_cover(pdf, report)
    _build_executive_summary(pdf, report)
    _build_regulation_applicability(pdf, report)
    _build_score_breakdown(pdf, report)
    _build_gap_analysis(pdf, report)
    _build_action_plan(pdf, report)
    _build_closing(pdf, report)

    raw = pdf.output()
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    # fpdf may return a string in older builds
    buf = io.BytesIO()
    buf.write(raw if isinstance(raw, bytes) else raw.encode("latin-1"))
    return buf.getvalue()
