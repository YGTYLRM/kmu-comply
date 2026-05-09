"""
PDF Report Generator for Complio compliance reports.
Public entry point: generate_pdf(report) -> bytes.
"""
from __future__ import annotations

import io
import re
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

# Palette
NAVY       = (12,  28,  64)
NAVY_MID   = (30,  58, 112)
WHITE      = (255, 255, 255)
LIGHT_BG   = (246, 248, 251)
BORDER     = (218, 223, 232)
TEXT_DARK  = (28,  36,  50)
TEXT_MID   = (86,  96, 112)
TEXT_LIGHT = (145, 155, 170)

STATUS_COLORS: dict[ComplianceStatus, tuple] = {
    ComplianceStatus.COMPLIANT:           (30,  150,  70),
    ComplianceStatus.PARTIALLY_COMPLIANT: (200, 120,   0),
    ComplianceStatus.NON_COMPLIANT:       (180,  35,  25),
    ComplianceStatus.CANNOT_ASSESS:       (115, 125, 140),
}
STATUS_LABELS: dict[ComplianceStatus, str] = {
    ComplianceStatus.COMPLIANT:           "Compliant",
    ComplianceStatus.PARTIALLY_COMPLIANT: "Partial",
    ComplianceStatus.NON_COMPLIANT:       "Non-Compliant",
    ComplianceStatus.CANNOT_ASSESS:       "Cannot Assess",
}
PRIORITY_COLORS: dict[Priority, tuple] = {
    Priority.CRITICAL: (180,  35,  25),
    Priority.HIGH:     (195,  85,  15),
    Priority.MEDIUM:   (200, 120,   0),
    Priority.LOW:      (30,  150,  70),
}

PAGE_W    = 210
PAGE_H    = 297
MARGIN    = 16
CONTENT_W = PAGE_W - 2 * MARGIN


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _s(text: Optional[str]) -> str:
    """Sanitise text for latin-1 fpdf output."""
    if text is None:
        return ""
    text = str(text)
    # Dashes
    text = text.replace("—", "-").replace("–", "-")
    # Smart quotes
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    # Ellipsis
    text = text.replace("…", "...")
    # Section sign
    text = text.replace("§", "§")
    # German umlauts -> ASCII digraphs
    text = (text
            .replace("ä", "ae").replace("Ä", "Ae")
            .replace("ö", "oe").replace("Ö", "Oe")
            .replace("ü", "ue").replace("Ü", "Ue")
            .replace("ß", "ss"))
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _clean_evidence(text: Optional[str]) -> str:
    """Remove raw field_name=value patterns from LLM evidence output."""
    if not text:
        return ""
    # Replace patterns like has_dpo=false, employee_count=62, etc.
    text = re.sub(r'\b\w+=(?:true|false|null|\d+(?:\.\d+)?)\b', '', text)
    # Clean up extra spaces left behind
    text = re.sub(r'  +', ' ', text).strip()
    # Remove leading/trailing punctuation artifacts
    text = re.sub(r'^[\s,;.]+', '', text)
    return text


def _reg_label(reg_value: str) -> str:
    return REG_LABELS.get(reg_value, reg_value.upper())


def _score_color(score: float) -> tuple:
    if score >= 75:
        return (30, 150, 70)
    if score >= 40:
        return (200, 120, 0)
    return (180, 35, 25)


# ---------------------------------------------------------------------------
# Row height helper
# ---------------------------------------------------------------------------

def _text_lines(pdf: FPDF, text: str, width: float, line_h: float) -> int:
    """Return the number of lines multi_cell would produce (dry run)."""
    lines = pdf.multi_cell(width, line_h, _s(text), dry_run=True, output="LINES")
    return max(1, len(lines))


def _row_h(pdf: FPDF, text: str, width: float, line_h: float = 5.0, pad: float = 3.0) -> float:
    return _text_lines(pdf, text, width, line_h) * line_h + pad


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------

class ComplioPdf(FPDF):
    def __init__(self, company_name: str, date_str: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.company_name = company_name
        self.date_str = date_str
        self._cover_page = True
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(MARGIN, MARGIN, MARGIN)

    def header(self):
        if self._cover_page:
            return
        # Thin top bar
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PAGE_W, 11, style="F")
        # Logo
        if LOGO_PATH.exists():
            try:
                self.image(str(LOGO_PATH), x=MARGIN, y=2.5, h=6)
            except Exception:
                self.set_xy(MARGIN, 2)
                self.set_font("Helvetica", "B", 9)
                self.set_text_color(*WHITE)
                self.cell(40, 7, "Complio")
        # Company name right-aligned
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*WHITE)
        self.set_xy(0, 2.5)
        self.cell(PAGE_W - MARGIN, 6, _s(self.company_name), align="R")
        self.set_text_color(*TEXT_DARK)
        self.set_y(14)

    def footer(self):
        if self._cover_page:
            return
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TEXT_LIGHT)
        self.cell(CONTENT_W // 2, 5, "Complio - Preliminary Compliance Screening")
        self.cell(CONTENT_W // 2, 5, f"Page {self.page_no()}", align="R")
        self.set_text_color(*TEXT_DARK)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def section_heading(self, title: str, top_pad: float = 6.0):
        self.ln(top_pad)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.set_x(MARGIN)
        self.cell(CONTENT_W, 8, _s(title), fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*TEXT_DARK)
        self.ln(2)

    def sub_heading(self, title: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*NAVY_MID)
        self.set_x(MARGIN)
        self.cell(CONTENT_W, 6, _s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.set_line_width(0.2)
        self.set_text_color(*TEXT_DARK)
        self.ln(2)

    def body(self, text: str, indent: float = 0):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_MID)
        self.set_x(MARGIN + indent)
        self.multi_cell(CONTENT_W - indent, 5, _s(text))
        self.set_text_color(*TEXT_DARK)

    def reg_banner(self, reg_key: str):
        """Full-width regulation sub-banner."""
        self.ln(4)
        self.set_fill_color(*NAVY_MID)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.set_x(MARGIN)
        self.cell(CONTENT_W, 7, _s(_reg_label(reg_key)),
                  fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*TEXT_DARK)
        self.ln(1)

    def ensure(self, mm: float = 35.0):
        if self.get_y() > PAGE_H - mm:
            self.add_page()


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _build_cover(pdf: ComplioPdf, report: ComplianceReport):
    pdf._cover_page = True
    pdf.add_page()

    DARK_H = 118  # height of dark block

    # Dark block
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PAGE_W, DARK_H, style="F")

    # Logo
    logo_y = 10
    if LOGO_PATH.exists():
        try:
            pdf.image(str(LOGO_PATH), x=MARGIN, y=logo_y, h=14)
        except Exception:
            pdf.set_xy(MARGIN, logo_y + 1)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(*WHITE)
            pdf.cell(60, 10, "Complio")

    # Report label
    pdf.set_xy(MARGIN, 30)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(130, 165, 215)
    pdf.cell(CONTENT_W, 5, "PRELIMINARY COMPLIANCE SCREENING REPORT")

    # Company name
    pdf.set_xy(MARGIN, 39)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*WHITE)
    pdf.multi_cell(CONTENT_W - 42, 13, _s(report.company_name))

    # Date
    pdf.set_xy(MARGIN, 76)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(130, 165, 215)
    date_str = report.generated_at[:10] if report.generated_at else ""
    pdf.cell(CONTENT_W, 5, f"Generated  {date_str}")

    # --- Score block (top-right, inside dark area) ---
    score  = report.overall_score_percent
    sc     = _score_color(score)
    bx     = PAGE_W - MARGIN - 36
    by     = 37
    bw     = 36
    bh     = 32

    pdf.set_fill_color(*sc)
    pdf.rect(bx, by, bw, bh, style="F")
    # Score number
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_xy(bx, by + 4)
    pdf.cell(bw, 14, f"{score:.0f}%", align="C")
    # Label
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_xy(bx, by + 20)
    pdf.cell(bw, 6, "Overall Score", align="C")

    # --- Stats strip (bottom of dark block) ---
    n_app      = sum(1 for r in report.applicable_regulations if r.applies)
    n_gaps     = len(report.gap_analysis)
    n_actions  = len(report.action_plan)
    n_critical = sum(1 for a in report.action_plan if a.priority == Priority.CRITICAL)
    stats = [(str(n_app), "Regulations"), (str(n_gaps), "Gaps"),
             (str(n_actions), "Actions"), (str(n_critical), "Critical")]

    sw = CONTENT_W / 4
    sy = 88
    for i, (val, lbl) in enumerate(stats):
        sx = MARGIN + i * sw
        if i > 0:
            pdf.set_draw_color(60, 90, 150)
            pdf.set_line_width(0.4)
            pdf.line(sx, sy + 2, sx, sy + 14)
            pdf.set_line_width(0.2)
        pdf.set_xy(sx, sy)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*WHITE)
        pdf.cell(sw, 10, val, align="C")
        pdf.set_xy(sx, sy + 10)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(130, 165, 215)
        pdf.cell(sw, 5, lbl, align="C")

    pdf.set_text_color(*TEXT_DARK)

    # --- White lower section ---
    # Applicable regulations chips
    pdf.set_xy(MARGIN, DARK_H + 8)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*NAVY)
    pdf.cell(CONTENT_W, 5, "Applicable Regulations")
    pdf.ln(7)

    applicable = [r for r in report.applicable_regulations if r.applies]
    chip_w = (CONTENT_W - 4) / 3
    for i, reg in enumerate(applicable):
        col = i % 3
        row = i // 3
        rx = MARGIN + col * (chip_w + 2)
        ry = DARK_H + 16 + row * 9
        pdf.set_fill_color(*LIGHT_BG)
        pdf.set_draw_color(*BORDER)
        pdf.rect(rx, ry, chip_w, 7, style="FD")
        pdf.set_xy(rx, ry + 0.5)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*NAVY_MID)
        pdf.cell(chip_w, 6, _s(_reg_label(reg.regulation.value)), align="C")

    # Disclaimer
    pdf.set_xy(MARGIN, PAGE_H - 22)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.multi_cell(CONTENT_W, 3.5,
        "This report is generated by an AI system and does not constitute legal advice. "
        "Consult a qualified legal professional before making compliance decisions. "
        "Complio is a preliminary screening tool only.")
    pdf.set_text_color(*TEXT_DARK)

    pdf._cover_page = False


# ---------------------------------------------------------------------------
# Executive summary  (no forced add_page — flows directly after cover)
# ---------------------------------------------------------------------------

def _build_summary(pdf: ComplioPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_heading("1. Executive Summary")

    if report.executive_summary:
        pdf.body(report.executive_summary)
    else:
        pdf.body("No executive summary generated.")

    if report.validation_warnings:
        pdf.ln(4)
        pdf.sub_heading("Validation Warnings")
        for w in report.validation_warnings:
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(180, 40, 30)
            pdf.multi_cell(CONTENT_W - 3, 5, _s("- " + w))
        pdf.set_text_color(*TEXT_DARK)

    # --- Applicability table on the same page (continue) ---
    pdf.ln(6)
    pdf.section_heading("2. Regulation Applicability")

    pdf.set_font("Helvetica", "", 8.5)
    pdf.body(
        "The table below shows which regulations apply to your organisation "
        "based on the submitted company profile."
    )
    pdf.ln(3)

    # Column widths
    cw_reg    = 38
    cw_app    = 20
    cw_reason = CONTENT_W - cw_reg - cw_app

    # Header
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(MARGIN)
    pdf.cell(cw_reg,    6, "Regulation", fill=True)
    pdf.cell(cw_app,    6, "Applies",    fill=True, align="C")
    pdf.cell(cw_reason, 6, "Reason",     fill=True)
    pdf.ln()
    pdf.set_text_color(*TEXT_DARK)

    LINE_H  = 4.5
    for idx, reg_app in enumerate(report.applicable_regulations):
        label   = _reg_label(reg_app.regulation.value)
        applies = reg_app.applies
        reason  = _s(reg_app.reason or "")

        # Pre-calculate row height from the reason column
        pdf.set_font("Helvetica", "", 8)
        rh = _row_h(pdf, reason, cw_reason, LINE_H, pad=2.0)
        rh = max(rh, 7.0)

        pdf.ensure(rh + 4)

        row_y = pdf.get_y()
        bg    = LIGHT_BG if idx % 2 == 0 else WHITE

        # Regulation name
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*TEXT_MID)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(MARGIN, row_y)
        pdf.cell(cw_reg, rh, _s(label), fill=True)

        # Applies badge
        badge_col = (30, 150, 70) if applies else (145, 155, 170)
        pdf.set_fill_color(*badge_col)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_xy(MARGIN + cw_reg, row_y)
        pdf.cell(cw_app, rh, "Yes" if applies else "No", fill=True, align="C")

        # Reason — multi_cell at absolute x
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*TEXT_MID)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(MARGIN + cw_reg + cw_app, row_y)
        pdf.multi_cell(cw_reason, LINE_H, reason, fill=True)

        # Move cursor to end of row
        pdf.set_xy(MARGIN, row_y + rh)

    pdf.set_text_color(*TEXT_DARK)


# ---------------------------------------------------------------------------
# Score breakdown
# ---------------------------------------------------------------------------

def _build_scores(pdf: ComplioPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_heading("3. Score Breakdown")

    if not report.regulation_scores:
        pdf.body("No regulation scores available.")
        return

    # Overall score banner
    score  = report.overall_score_percent
    sc     = _score_color(score)
    ban_y  = pdf.get_y()
    ban_h  = 20

    pdf.set_fill_color(*sc)
    pdf.rect(MARGIN, ban_y, CONTENT_W, ban_h, style="F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 30)
    pdf.set_xy(MARGIN, ban_y + 1)
    pdf.cell(CONTENT_W, 12, f"{score:.1f}%", align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(MARGIN, ban_y + 13)
    pdf.cell(CONTENT_W, 5, "Overall Compliance Score", align="C")
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_y(ban_y + ban_h + 6)

    # Per-regulation table
    cw_reg  = 38
    cw_pct  = 16
    cw_bar  = 50
    cw_stat = 11
    cw_tot  = 14

    # Header
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_x(MARGIN)
    pdf.cell(cw_reg,  6, "Regulation",  fill=True)
    pdf.cell(cw_pct,  6, "Score",       fill=True, align="C")
    pdf.cell(cw_bar,  6, "Progress",    fill=True)
    pdf.cell(cw_stat, 6, "C",           fill=True, align="C")
    pdf.cell(cw_stat, 6, "P",           fill=True, align="C")
    pdf.cell(cw_stat, 6, "NC",          fill=True, align="C")
    pdf.cell(cw_stat, 6, "?",           fill=True, align="C")
    pdf.cell(cw_tot,  6, "Total",       fill=True, align="C")
    pdf.ln()

    ROW_H = 7

    for idx, rs in enumerate(report.regulation_scores):
        bg        = LIGHT_BG if idx % 2 == 0 else WHITE
        bar_col   = _score_color(rs.score_percent)
        label     = _reg_label(rs.regulation.value)
        row_y     = pdf.get_y()

        pdf.ensure(ROW_H + 2)
        row_y = pdf.get_y()

        # Regulation name
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(MARGIN)
        pdf.cell(cw_reg, ROW_H, _s(label), fill=True)

        # Score %
        pdf.set_text_color(*bar_col)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(cw_pct, ROW_H, f"{rs.score_percent:.0f}%", fill=True, align="C")

        # Progress bar (drawn at absolute position)
        bx = MARGIN + cw_reg + cw_pct
        by = row_y + 1.8
        bh = 3.5
        pdf.set_fill_color(*BORDER)
        pdf.rect(bx, by, cw_bar, bh, style="F")
        filled = cw_bar * max(0.0, min(100.0, rs.score_percent)) / 100.0
        if filled > 0:
            pdf.set_fill_color(*bar_col)
            pdf.rect(bx, by, filled, bh, style="F")

        # Stats cells
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*TEXT_MID)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(bx + cw_bar, row_y)
        pdf.cell(cw_stat, ROW_H, str(rs.compliant),           fill=True, align="C")
        pdf.cell(cw_stat, ROW_H, str(rs.partially_compliant), fill=True, align="C")
        pdf.cell(cw_stat, ROW_H, str(rs.non_compliant),        fill=True, align="C")
        pdf.cell(cw_stat, ROW_H, str(rs.cannot_assess),        fill=True, align="C")
        pdf.cell(cw_tot,  ROW_H, str(rs.total_requirements),   fill=True, align="C")
        pdf.ln()

    pdf.set_text_color(*TEXT_DARK)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 5,
             "C = Compliant   P = Partial   NC = Non-Compliant   ? = Cannot Assess")
    pdf.set_text_color(*TEXT_DARK)


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

def _build_gaps(pdf: ComplioPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_heading("4. Gap Analysis")
    pdf.body(
        "Every assessed requirement is listed below, grouped by regulation. "
        "Evidence and gap descriptions are shown in full."
    )

    gaps_by_reg: dict[str, list] = {}
    for gap in report.gap_analysis:
        gaps_by_reg.setdefault(gap.regulation.value, []).append(gap)

    for reg_key, gaps in gaps_by_reg.items():
        pdf.reg_banner(reg_key)

        for gap in gaps:
            # Estimate space needed
            ev_text  = _clean_evidence(gap.evidence)
            def_text = _clean_evidence(gap.deficiency_description)

            pdf.set_font("Helvetica", "", 8.5)
            ev_lines  = _text_lines(pdf, ev_text,  CONTENT_W - 8, 4.8)
            def_lines = _text_lines(pdf, def_text, CONTENT_W - 8, 4.8) if def_text else 0
            needed = 10 + ev_lines * 4.8 + (def_lines * 4.8 + 6 if def_text else 0) + 6
            pdf.ensure(needed)

            status_col   = STATUS_COLORS.get(gap.status,  (120, 130, 145))
            status_label = STATUS_LABELS.get(gap.status, str(gap.status))
            art_str      = f"Art. {_s(gap.article_number)}  |  {_s(gap.article_title)}"
            row_y        = pdf.get_y()

            # Article header row
            pdf.set_fill_color(*LIGHT_BG)
            pdf.rect(MARGIN, row_y, CONTENT_W, 7, style="F")

            # Left: status colour strip
            pdf.set_fill_color(*status_col)
            pdf.rect(MARGIN, row_y, 3, 7, style="F")

            # Article text
            pdf.set_xy(MARGIN + 5, row_y + 0.5)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(CONTENT_W - 42, 6, _s(art_str))

            # Status badge
            badge_x = MARGIN + CONTENT_W - 36
            pdf.set_fill_color(*status_col)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 7)
            pdf.rect(badge_x, row_y + 1, 36, 5, style="F")
            pdf.set_xy(badge_x, row_y + 1)
            pdf.cell(36, 5, _s(status_label), align="C")

            pdf.set_xy(MARGIN, row_y + 8)
            pdf.set_text_color(*TEXT_DARK)

            # Evidence block
            if ev_text:
                pdf.set_x(MARGIN + 4)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(*TEXT_MID)
                pdf.cell(18, 4.5, "Evidence:")
                pdf.ln()
                pdf.set_x(MARGIN + 4)
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(*TEXT_DARK)
                pdf.multi_cell(CONTENT_W - 8, 4.8, _s(ev_text))

            # Deficiency block
            if def_text:
                pdf.ln(1)
                pdf.set_x(MARGIN + 4)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(175, 35, 25)
                pdf.cell(22, 4.5, "Gap:")
                pdf.ln()
                pdf.set_x(MARGIN + 4)
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(*TEXT_MID)
                pdf.multi_cell(CONTENT_W - 8, 4.8, _s(def_text))

            pdf.set_text_color(*TEXT_DARK)
            pdf.ln(2)
            # Separator
            pdf.set_draw_color(*BORDER)
            pdf.set_line_width(0.2)
            pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
            pdf.ln(2)


# ---------------------------------------------------------------------------
# Action plan
# ---------------------------------------------------------------------------

def _build_actions(pdf: ComplioPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_heading("5. Action Plan")
    pdf.body(
        "Recommended actions to address identified compliance gaps, "
        "ordered by priority."
    )
    pdf.ln(2)

    if not report.action_plan:
        pdf.body("No remediation actions required.")
        return

    actions_by_reg: dict[str, list] = {}
    for action in report.action_plan:
        actions_by_reg.setdefault(action.regulation.value, []).append(action)

    for reg_key, actions in actions_by_reg.items():
        pdf.reg_banner(reg_key)

        for act in actions:
            action_text = _s(act.action)
            pdf.set_font("Helvetica", "", 8.5)
            act_lines = _text_lines(pdf, action_text, CONTENT_W - 6, 5.0)
            needed    = act_lines * 5.0 + 20
            pdf.ensure(needed)

            prio_col = PRIORITY_COLORS.get(act.priority, (120, 130, 145))
            row_y    = pdf.get_y()

            # Priority badge
            badge_w = 22
            pdf.set_fill_color(*prio_col)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.rect(MARGIN, row_y, badge_w, 6, style="F")
            pdf.set_xy(MARGIN, row_y)
            pdf.cell(badge_w, 6, _s(act.priority.value), align="C")

            # Article ref
            pdf.set_text_color(*NAVY_MID)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(MARGIN + badge_w + 3, row_y)
            pdf.cell(CONTENT_W - badge_w - 3, 6, _s(f"Art. {act.article_number}"))
            pdf.ln()

            # Action text
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.multi_cell(CONTENT_W - 6, 5.0, action_text)

            # Effort + deadline row
            pdf.set_x(MARGIN + 3)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*TEXT_MID)
            pdf.cell(16, 5, "Effort:")
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(48, 5, _s(act.estimated_effort))
            if act.deadline:
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(*TEXT_MID)
                pdf.cell(18, 5, "Deadline:")
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(*TEXT_DARK)
                pdf.cell(0, 5, _s(act.deadline))
            pdf.ln()

            pdf.ln(2)
            pdf.set_draw_color(*BORDER)
            pdf.set_line_width(0.2)
            pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
            pdf.ln(2)

    pdf.set_text_color(*TEXT_DARK)


# ---------------------------------------------------------------------------
# Closing
# ---------------------------------------------------------------------------

def _build_closing(pdf: ComplioPdf, report: ComplianceReport):
    pdf.add_page()
    pdf.section_heading("6. Next Steps & Disclaimer")

    pdf.sub_heading("Recommended Next Steps")
    steps = [
        "Review each gap finding with your legal or compliance team.",
        "Prioritise Critical and High priority action items immediately.",
        "Establish a compliance calendar with realistic deadlines from the Action Plan.",
        "Re-run this screening after implementing changes to track progress.",
        "Engage a qualified legal counsel for binding compliance decisions.",
    ]
    for step in steps:
        pdf.set_x(MARGIN + 3)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_MID)
        pdf.multi_cell(CONTENT_W - 3, 5.5, _s(f"•  {step}"))
    pdf.set_text_color(*TEXT_DARK)

    pdf.ln(8)
    pdf.sub_heading("Legal Disclaimer")

    disc_y = pdf.get_y()
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*BORDER)
    pdf.set_line_width(0.3)

    # Draw background box (estimate height)
    disc_text = _s(report.disclaimer)
    pdf.set_font("Helvetica", "I", 8.5)
    lines = _text_lines(pdf, disc_text, CONTENT_W - 10, 5.0)
    box_h = lines * 5.0 + 10
    pdf.rect(MARGIN, disc_y, CONTENT_W, box_h, style="FD")

    pdf.set_xy(MARGIN + 5, disc_y + 5)
    pdf.set_text_color(*TEXT_MID)
    pdf.multi_cell(CONTENT_W - 10, 5.0, disc_text)
    pdf.set_text_color(*TEXT_DARK)

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 6, "Complio - Preliminary Compliance Screening for German SMEs",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 5,
             "This report was generated automatically and is not a substitute for legal advice.",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*TEXT_DARK)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf(report: ComplianceReport) -> bytes:
    date_str = report.generated_at[:10] if report.generated_at else ""
    pdf = ComplioPdf(company_name=report.company_name, date_str=date_str)

    _build_cover(pdf, report)
    _build_summary(pdf, report)
    _build_scores(pdf, report)
    _build_gaps(pdf, report)
    _build_actions(pdf, report)
    _build_closing(pdf, report)

    raw = pdf.output()
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    buf = io.BytesIO()
    buf.write(raw if isinstance(raw, bytes) else raw.encode("latin-1"))
    return buf.getvalue()
