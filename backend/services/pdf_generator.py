"""
PDF report generator - professional compliance screening report.
Uses fpdf2 to produce a clean, branded, multi-section document.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from fpdf import FPDF, XPos, YPos

from models.compliance_report import ComplianceReport
from models.enums import ComplianceStatus, Priority

# ── Assets ────────────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH  = ASSETS_DIR / "logo.png"

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY       = (10,  20,  50)
NAVY_MID   = (20,  40,  90)
WHITE      = (255, 255, 255)
LIGHT_BG   = (248, 250, 252)
BORDER_CLR = (226, 232, 240)
TEXT_MAIN  = (15,  23,  42)
TEXT_MID   = (100, 116, 139)
TEXT_LIGHT = (148, 163, 184)
BLUE_ACC   = (37,  99,  235)

GREEN  = (16,  185, 129)
AMBER  = (245, 158, 11)
RED    = (239, 68,  68)
GREY   = (148, 163, 184)

STATUS_META: dict[ComplianceStatus, tuple[tuple, str]] = {
    ComplianceStatus.COMPLIANT:           (GREEN, "COMPLIANT"),
    ComplianceStatus.PARTIALLY_COMPLIANT: (AMBER, "PARTIAL"),
    ComplianceStatus.NON_COMPLIANT:       (RED,   "NON-COMPLIANT"),
    ComplianceStatus.CANNOT_ASSESS:       (GREY,  "CANNOT ASSESS"),
}
PRIORITY_META: dict[Priority, tuple[tuple, str]] = {
    Priority.CRITICAL: (RED,   "CRITICAL"),
    Priority.HIGH:     ((249, 115, 22), "HIGH"),
    Priority.MEDIUM:   (AMBER, "MEDIUM"),
    Priority.LOW:      (GREEN, "LOW"),
}
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

PAGE_W  = 210
MARGIN  = 18
CONTENT = PAGE_W - 2 * MARGIN


# ── PDF class ─────────────────────────────────────────────────────────────────

class CompliancePDF(FPDF):
    def __init__(self, report: ComplianceReport) -> None:
        super().__init__()
        self.report = report
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(True, margin=22)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        # Thin navy top bar
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PAGE_W, 9, "F")
        self.set_y(1.5)
        self.set_font("Helvetica", "", 6.5)
        self.set_text_color(*TEXT_LIGHT)
        self.cell(MARGIN, 6, "")
        self.cell(
            0, 6,
            f"Complio  .  Preliminary Screening  .  {self.report.company_name}",
            align="L",
        )
        self.ln(11)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-13)
        self.set_draw_color(*BORDER_CLR)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TEXT_LIGHT)
        date_str = datetime.now().strftime("%d %b %Y")
        self.cell(0, 5, f"Page {self.page_no()}", align="L")
        self.set_y(self.get_y() - 5)
        self.cell(0, 5, "This report does not constitute legal advice", align="C")
        self.set_y(self.get_y() - 5)
        self.cell(0, 5, f"Complio  .  {date_str}", align="R")

    # ── Typography helpers ────────────────────────────────────────────────────

    def section_title(self, text: str) -> None:
        self.ln(5)
        self.set_fill_color(*LIGHT_BG)
        self.set_draw_color(*BORDER_CLR)
        self.rect(MARGIN, self.get_y(), CONTENT, 8, "FD")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*NAVY)
        self.cell(CONTENT, 8, _s(f"  {text}"), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str, size: int = 9) -> None:
        self.set_font("Helvetica", "", size)
        self.set_text_color(*TEXT_MID)
        self.multi_cell(0, 5, _s(text))
        self.set_text_color(0, 0, 0)

    def tag(self, label: str, color: tuple, w: int = 26, h: int = 5) -> None:
        r, g, b = color
        self.set_fill_color(min(255, r + 170), min(255, g + 170), min(255, b + 170))
        self.set_text_color(max(0, r - 30), max(0, g - 30), max(0, b - 30))
        self.set_font("Helvetica", "B", 6.5)
        self.cell(w, h, label, fill=True, align="C")
        self.set_fill_color(*WHITE)
        self.set_text_color(0, 0, 0)

    def score_bar(self, pct: float, w: float = 80) -> None:
        color = GREEN if pct >= 75 else AMBER if pct >= 50 else RED
        x, y = self.get_x(), self.get_y() + 1
        self.set_fill_color(*BORDER_CLR)
        self.rect(x, y, w, 4, "F")
        self.set_fill_color(*color)
        self.rect(x, y, max(1.0, w * pct / 100), 4, "F")
        self.set_fill_color(*WHITE)
        self.set_xy(x + w + 2, self.get_y())

    def divider(self, gap_before: float = 1, gap_after: float = 3) -> None:
        self.ln(gap_before)
        self.set_draw_color(*BORDER_CLR)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(gap_after)


# ── Public entry point ────────────────────────────────────────────────────────

def generate_pdf(report: ComplianceReport) -> bytes:
    # Deep-sanitise all string fields so Helvetica (latin-1) can render them
    report = _sanitise_report(report)
    pdf = CompliancePDF(report)
    pdf.add_page()
    _cover(pdf, report)
    _scores(pdf, report)
    _gap_analysis(pdf, report)
    _action_plan(pdf, report)
    _disclaimer(pdf, report)
    return bytes(pdf.output())


def _sanitise_report(r: ComplianceReport) -> ComplianceReport:
    """Return a shallow copy of the report with all strings sanitised for latin-1."""
    import copy
    r2 = copy.copy(r)
    r2.company_name       = _s(r.company_name)
    r2.executive_summary  = _s(r.executive_summary)
    r2.disclaimer         = _s(r.disclaimer)
    r2.gap_analysis = [
        _sanitise_gap(g) for g in r.gap_analysis
    ]
    r2.action_plan = [
        _sanitise_action(a) for a in r.action_plan
    ]
    r2.applicable_regulations = [
        _sanitise_reg_app(ra) for ra in r.applicable_regulations
    ]
    return r2


def _sanitise_gap(g):
    import copy
    g2 = copy.copy(g)
    g2.article_title          = _s(g.article_title)
    g2.evidence               = _s(g.evidence)
    g2.deficiency_description = _s(g.deficiency_description) if g.deficiency_description else None
    return g2


def _sanitise_action(a):
    import copy
    a2 = copy.copy(a)
    a2.action             = _s(a.action)
    a2.estimated_effort   = _s(a.estimated_effort)
    return a2


def _sanitise_reg_app(ra):
    import copy
    ra2 = copy.copy(ra)
    ra2.reason = _s(ra.reason)
    return ra2


# ── Cover page ────────────────────────────────────────────────────────────────

def _cover(pdf: CompliancePDF, r: ComplianceReport) -> None:
    # Full-width dark navy header band
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PAGE_W, 62, "F")

    # Complio logo (top-left of header)
    if LOGO_PATH.exists():
        # White background pill behind logo so it reads on dark
        pdf.set_fill_color(*WHITE)
        pdf.rect(MARGIN, 10, 52, 18, "F")
        pdf.image(str(LOGO_PATH), x=MARGIN + 1, y=11, h=16)
    else:
        # Fallback text logo
        pdf.set_xy(MARGIN, 12)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*WHITE)
        pdf.cell(0, 8, "COMPLIO")

    # Report type label
    pdf.set_xy(MARGIN, 32)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(147, 197, 253)   # blue-300
    pdf.cell(0, 5, "PRELIMINARY COMPLIANCE SCREENING REPORT")

    # Company name
    pdf.set_xy(MARGIN, 39)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*WHITE)
    pdf.cell(120, 10, _truncate(r.company_name, 40))

    # Date
    pdf.set_xy(MARGIN, 51)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*TEXT_LIGHT)
    date_str = datetime.fromisoformat(r.generated_at.replace("Z", "+00:00")).strftime("%d %B %Y")
    pdf.cell(0, 5, f"Generated on {date_str}")

    # Overall score badge (top-right of header)
    score  = r.overall_score_percent
    s_color = GREEN if score >= 75 else AMBER if score >= 50 else RED
    badge_x = PAGE_W - MARGIN - 38
    pdf.set_fill_color(*s_color)
    pdf.rect(badge_x, 10, 38, 22, "F")
    pdf.set_xy(badge_x, 12)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*WHITE)
    pdf.cell(38, 14, f"{score:.0f}%", align="C", new_x=XPos.LEFT, new_y=YPos.NEXT)
    pdf.set_xy(badge_x, 26)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*WHITE)
    pdf.cell(38, 6, "Overall Score", align="C")

    # Regulation count + action count strip below header
    applicable_count = sum(1 for a in r.applicable_regulations if a.applies)
    action_count     = len(r.action_plan)
    gap_count        = len(r.gap_analysis)
    critical_count   = sum(1 for a in r.action_plan if a.priority == Priority.CRITICAL)

    pdf.set_fill_color(*LIGHT_BG)
    pdf.rect(0, 62, PAGE_W, 13, "F")

    stats = [
        (f"{applicable_count} of {len(r.applicable_regulations)}", "regulations apply"),
        (str(gap_count), "requirements assessed"),
        (str(action_count), "action items"),
        (str(critical_count), "critical findings"),
    ]
    col_w = PAGE_W / len(stats)
    for i, (val, lbl) in enumerate(stats):
        x = i * col_w + col_w / 2 - 20
        pdf.set_xy(x, 63)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*NAVY)
        pdf.cell(40, 6, val, align="C", new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.set_xy(x, 69)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*TEXT_MID)
        pdf.cell(40, 5, lbl, align="C")

    pdf.set_y(80)
    pdf.set_text_color(0, 0, 0)

    # Executive summary
    pdf.section_title("Executive Summary")
    pdf.body_text(r.executive_summary or "No executive summary generated.")
    pdf.ln(4)

    # Applicability table
    pdf.section_title("Regulation Applicability")
    _applicability_table(pdf, r)


def _applicability_table(pdf: CompliancePDF, r: ComplianceReport) -> None:
    applicable     = [a for a in r.applicable_regulations if a.applies]
    not_applicable = [a for a in r.applicable_regulations if not a.applies]

    for reg in applicable:
        label = REG_LABELS.get(reg.regulation.value, reg.regulation.value)
        pdf.set_fill_color(*GREEN)
        pdf.cell(3, 6, "", fill=True)
        pdf.set_fill_color(*WHITE)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*NAVY)
        pdf.cell(28, 6, f"  {label}")
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*TEXT_MID)
        reason = _truncate(reg.reason, 100)
        pdf.cell(0, 6, reason, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if not_applicable:
        pdf.ln(2)
        labels = ", ".join(REG_LABELS.get(a.regulation.value, a.regulation.value) for a in not_applicable)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*TEXT_LIGHT)
        pdf.cell(0, 5, f"Not applicable: {labels}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(0, 0, 0)


# ── Score breakdown ───────────────────────────────────────────────────────────

def _scores(pdf: CompliancePDF, r: ComplianceReport) -> None:
    scored = [s for s in r.regulation_scores if s.total_requirements > 0]
    if not scored:
        return

    pdf.section_title(f"Compliance Score Breakdown")

    for s in scored:
        label = REG_LABELS.get(s.regulation.value, s.regulation.value)
        score_color = GREEN if s.score_percent >= 75 else AMBER if s.score_percent >= 50 else RED

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(36, 7, label)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*score_color)
        pdf.cell(14, 7, f"{s.score_percent:.0f}%")
        pdf.set_text_color(0, 0, 0)

        bar_start_x = pdf.get_x()
        bar_y = pdf.get_y() + 1.5
        pdf.set_fill_color(*BORDER_CLR)
        pdf.rect(bar_start_x, bar_y, 72, 4, "F")
        pdf.set_fill_color(*score_color)
        pdf.rect(bar_start_x, bar_y, max(1.0, 72 * s.score_percent / 100), 4, "F")
        pdf.set_fill_color(*WHITE)
        pdf.set_xy(bar_start_x + 74, pdf.get_y())

        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*TEXT_MID)
        parts = []
        if s.compliant:          parts.append(f"{s.compliant} compliant")
        if s.partially_compliant:parts.append(f"{s.partially_compliant} partial")
        if s.non_compliant:      parts.append(f"{s.non_compliant} non-compliant")
        if s.cannot_assess:      parts.append(f"{s.cannot_assess} unassessed")
        pdf.cell(0, 7, "  .  ".join(parts), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.divider(0, 1)

    pdf.set_text_color(0, 0, 0)


# ── Gap analysis ──────────────────────────────────────────────────────────────

def _gap_analysis(pdf: CompliancePDF, r: ComplianceReport) -> None:
    if not r.gap_analysis:
        return

    pdf.section_title(f"Gap Analysis  -  {len(r.gap_analysis)} requirements assessed")

    by_reg: dict[str, list] = {}
    for g in r.gap_analysis:
        by_reg.setdefault(g.regulation.value, []).append(g)

    for reg_key, gaps in by_reg.items():
        # Regulation sub-header
        pdf.set_fill_color(235, 241, 255)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*BLUE_ACC)
        pdf.cell(CONTENT, 6.5, f"  {REG_LABELS.get(reg_key, reg_key)}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

        for g in gaps:
            color, label = STATUS_META.get(g.status, (GREY, str(g.status)))
            self_x = pdf.l_margin

            # Status tag + article number + title
            pdf.tag(label, color, w=28)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*NAVY)
            pdf.set_x(self_x + 30)
            pdf.cell(22, 5, g.article_number)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*TEXT_MID)
            title = _truncate(g.article_title, 58)
            pdf.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Evidence
            if g.evidence:
                pdf.set_x(self_x + 4)
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(*TEXT_MID)
                pdf.multi_cell(CONTENT - 4, 4.5, _truncate(g.evidence, 250))

            # Deficiency
            if g.deficiency_description:
                pdf.set_x(self_x + 4)
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.set_text_color(*RED)
                pdf.multi_cell(CONTENT - 4, 4.5, _truncate(g.deficiency_description, 200))

            pdf.ln(1.5)

        pdf.ln(3)

    pdf.set_text_color(0, 0, 0)


# ── Action plan ───────────────────────────────────────────────────────────────

def _action_plan(pdf: CompliancePDF, r: ComplianceReport) -> None:
    if not r.action_plan:
        return

    prio_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
    actions = sorted(r.action_plan, key=lambda a: prio_order.get(a.priority, 4))

    pdf.section_title(f"Prioritised Action Plan  -  {len(actions)} items")

    for a in actions:
        color, label = PRIORITY_META.get(a.priority, (GREY, "LOW"))

        # Left accent bar by priority
        r_c, g_c, b_c = color
        pdf.set_fill_color(*color)
        pdf.rect(MARGIN, pdf.get_y(), 3, 18, "F")
        pdf.set_x(MARGIN + 5)

        # Priority tag + regulation
        pdf.tag(label, color, w=20)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*TEXT_MID)
        reg_label = REG_LABELS.get(a.regulation.value, a.regulation.value)
        pdf.set_x(MARGIN + 27)
        pdf.cell(0, 5, f"{reg_label}  .  {a.article_number}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Action text
        pdf.set_x(MARGIN + 5)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*TEXT_MAIN)
        pdf.multi_cell(CONTENT - 5, 5, a.action)

        # Meta
        meta = [f"Effort: {a.estimated_effort}"]
        if a.deadline:
            meta.append(f"Deadline: {a.deadline}")
        pdf.set_x(MARGIN + 5)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*TEXT_MID)
        pdf.cell(0, 4.5, "  .  ".join(meta), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    pdf.set_text_color(0, 0, 0)


# ── Disclaimer ────────────────────────────────────────────────────────────────

def _disclaimer(pdf: CompliancePDF, r: ComplianceReport) -> None:
    pdf.ln(4)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*BORDER_CLR)
    y0 = pdf.get_y()
    pdf.rect(MARGIN, y0, CONTENT, 30, "FD")
    pdf.set_xy(MARGIN + 3, y0 + 3)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, "Important notice - not legal advice")
    pdf.set_xy(MARGIN + 3, y0 + 10)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*TEXT_MID)
    pdf.multi_cell(CONTENT - 6, 4.5, r.disclaimer)
    pdf.set_text_color(0, 0, 0)


# ── Utilities ─────────────────────────────────────────────────────────────────

_REPLACEMENTS = [
    ("—", "-"), ("–", "-"), ("‒", "-"),
    ("‘", "'"), ("’", "'"),
    ("“", '"'), ("”", '"'),
    ("…", "..."), ("•", "*"), ("·", "."), (" ", " "),
    ("ä", "ae"), ("ö", "oe"), ("ü", "ue"),
    ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"),
    ("ß", "ss"), ("é", "e"), ("è", "e"),
    ("à", "a"), ("á", "a"), ("ó", "o"), ("ú", "u"), ("ñ", "n"),
]


def _s(text: str) -> str:
    if not text:
        return ""
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")

def _truncate(text: str, max_len: int) -> str:
    t = text if len(text) <= max_len else text[:max_len - 1] + "..."
    return _s(t)
