"""
PDF Report Generator for Complio compliance reports.
Uses WeasyPrint (HTML -> PDF) for professional output.
Public entry point: generate_pdf(report) -> bytes.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

from models.compliance_report import ComplianceReport
from models.enums import ComplianceStatus, Priority

# ---------------------------------------------------------------------------
# Assets & labels
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

STATUS_COLORS: dict[ComplianceStatus, str] = {
    ComplianceStatus.COMPLIANT:           "#1a9455",
    ComplianceStatus.PARTIALLY_COMPLIANT: "#c07800",
    ComplianceStatus.NON_COMPLIANT:       "#b52018",
    ComplianceStatus.CANNOT_ASSESS:       "#78828f",
}
STATUS_LABELS: dict[ComplianceStatus, str] = {
    ComplianceStatus.COMPLIANT:           "Compliant",
    ComplianceStatus.PARTIALLY_COMPLIANT: "Partial",
    ComplianceStatus.NON_COMPLIANT:       "Non-Compliant",
    ComplianceStatus.CANNOT_ASSESS:       "Cannot Assess",
}
PRIORITY_COLORS: dict[Priority, str] = {
    Priority.CRITICAL: "#b52018",
    Priority.HIGH:     "#c0560e",
    Priority.MEDIUM:   "#c07800",
    Priority.LOW:      "#1a9455",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reg_label(key: str) -> str:
    return REG_LABELS.get(key, key.upper())


def _score_color(score: float) -> str:
    if score >= 75:
        return "#1a9455"
    if score >= 40:
        return "#c07800"
    return "#b52018"


def _h(text: Optional[str]) -> str:
    """HTML-escape a string."""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _clean(text: Optional[str]) -> str:
    """Remove raw field_name=value patterns left by the LLM."""
    if not text:
        return ""
    text = re.sub(r'\b\w+=(?:true|false|null|\d+(?:\.\d+)?)\b', '', text)
    text = re.sub(r'  +', ' ', text).strip().lstrip('.,;')
    return text


def _logo_data_uri() -> str:
    if LOGO_PATH.exists():
        try:
            data = base64.b64encode(LOGO_PATH.read_bytes()).decode()
            return f"data:image/png;base64,{data}"
        except Exception:
            pass
    return ""


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
@page { size: A4; margin: 0; }

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    font-size: 9pt;
    color: #1c2233;
    line-height: 1.55;
    width: 210mm;
}

/* ---- Running header (injected per content section) ---- */
.page-header {
    display: table;
    width: 100%;
    border-bottom: 1px solid #dde2ea;
    padding: 5mm 15mm 4mm;
    background: #fff;
}
.page-header td { vertical-align: middle; }
.page-header .logo-cell { width: 32mm; }
.page-header .logo-cell img { height: 10pt; }
.page-header .co-name {
    font-size: 7.5pt;
    color: #5a6070;
    text-align: right;
}

/* ---- Content wrapper (padding for all non-cover pages) ---- */
.content-wrap {
    padding: 0 15mm 14mm;
}

/* ---- Cover ---- */
.cover {
    height: 297mm;
    display: table;
    width: 100%;
    page-break-after: always;
}
.cover-top {
    display: table-row;
    height: 120mm;
    background: #0c1c40;
}
.cover-top-inner {
    display: table-cell;
    padding: 12mm 14mm 10mm;
    vertical-align: top;
}
.cover-logo { height: 14pt; margin-bottom: 14mm; }
.cover-label {
    font-size: 7pt;
    letter-spacing: 1.5pt;
    color: #7ea8dc;
    text-transform: uppercase;
    margin-bottom: 6pt;
}
.cover-company {
    font-size: 26pt;
    font-weight: bold;
    color: #ffffff;
    line-height: 1.2;
    max-width: 120mm;
}
.cover-date {
    font-size: 8pt;
    color: #7ea8dc;
    margin-top: 8mm;
}

.cover-score-block {
    display: table-cell;
    width: 44mm;
    vertical-align: middle;
    padding-right: 14mm;
    text-align: center;
}
.score-circle {
    display: inline-block;
    width: 38mm;
    height: 38mm;
    border-radius: 50%;
    line-height: 38mm;
    text-align: center;
}
.score-number {
    font-size: 30pt;
    font-weight: bold;
    color: #ffffff;
    display: block;
    margin-top: 4mm;
    line-height: 1;
}
.score-sub {
    font-size: 7pt;
    color: rgba(255,255,255,0.75);
    margin-top: 3pt;
    display: block;
}

.cover-stats {
    display: table-row;
    height: 18mm;
    background: #172a5c;
}
.cover-stats-inner {
    display: table-cell;
    padding: 0 14mm;
    vertical-align: middle;
}
.stats-row {
    display: table;
    width: 100%;
}
.stat-cell {
    display: table-cell;
    text-align: center;
    border-right: 1px solid rgba(255,255,255,0.12);
}
.stat-cell:last-child { border-right: none; }
.stat-num {
    font-size: 18pt;
    font-weight: bold;
    color: #ffffff;
    display: block;
    line-height: 1.1;
}
.stat-label {
    font-size: 7pt;
    color: #7ea8dc;
}

.cover-bottom {
    display: table-row;
    background: #ffffff;
}
.cover-bottom-inner {
    display: table-cell;
    padding: 10mm 14mm;
    vertical-align: top;
}
.cover-regs-title {
    font-size: 8pt;
    font-weight: bold;
    color: #0c1c40;
    margin-bottom: 5mm;
}
.regs-grid {
    display: table;
    width: 100%;
}
.regs-row { display: table-row; }
.reg-chip-cell {
    display: table-cell;
    width: 33.3%;
    padding: 1.5mm 2mm 1.5mm 0;
}
.reg-chip {
    display: block;
    background: #f0f3f8;
    border: 1px solid #dde2ea;
    border-radius: 3pt;
    text-align: center;
    font-size: 7.5pt;
    font-weight: bold;
    color: #1a3066;
    padding: 2.5pt 4pt;
}
.cover-disclaimer {
    font-size: 7pt;
    color: #9ca3af;
    border-top: 1px solid #e5e7eb;
    padding-top: 4mm;
    margin-top: 5mm;
    line-height: 1.6;
}

/* ---- Section headings ---- */
.section-break { page-break-before: always; break-before: page; }

.section-title {
    font-size: 13pt;
    font-weight: bold;
    color: #0c1c40;
    margin-bottom: 6pt;
    padding-bottom: 4pt;
    border-bottom: 2pt solid #0c1c40;
}

.section-subtitle {
    font-size: 10pt;
    font-weight: bold;
    color: #1a3066;
    margin-top: 12pt;
    margin-bottom: 5pt;
    padding-bottom: 3pt;
    border-bottom: 1pt solid #dde2ea;
}

.body-text {
    font-size: 9pt;
    color: #3d4557;
    line-height: 1.6;
    margin-bottom: 8pt;
}

/* ---- Applicability table ---- */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 6pt;
    font-size: 8.5pt;
}
.data-table th {
    background: #0c1c40;
    color: #ffffff;
    font-size: 8pt;
    font-weight: bold;
    padding: 5pt 7pt;
    text-align: left;
}
.data-table td {
    padding: 5pt 7pt;
    vertical-align: top;
    border-bottom: 1pt solid #e5e7eb;
    color: #3d4557;
}
.data-table tr:nth-child(even) td { background: #f7f9fc; }
.data-table tr:last-child td { border-bottom: none; }

.badge {
    display: inline-block;
    padding: 2pt 6pt;
    border-radius: 10pt;
    font-size: 7.5pt;
    font-weight: bold;
    color: #ffffff;
    white-space: nowrap;
}
.badge-yes { background: #1a9455; }
.badge-no  { background: #9ca3af; }

/* ---- Score breakdown ---- */
.score-banner {
    border-radius: 4pt;
    padding: 10pt 14pt;
    margin-bottom: 12pt;
    text-align: center;
}
.score-banner-num {
    font-size: 36pt;
    font-weight: bold;
    color: #ffffff;
    display: block;
    line-height: 1;
}
.score-banner-label {
    font-size: 9pt;
    color: rgba(255,255,255,0.85);
    margin-top: 3pt;
}

.score-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
}
.score-table th {
    background: #0c1c40;
    color: #ffffff;
    font-size: 7.5pt;
    padding: 5pt 7pt;
    text-align: left;
}
.score-table th.center { text-align: center; }
.score-table td {
    padding: 5.5pt 7pt;
    border-bottom: 1pt solid #e5e7eb;
    vertical-align: middle;
}
.score-table tr:nth-child(even) td { background: #f7f9fc; }
.score-table tr:last-child td { border-bottom: none; }
.score-pct {
    font-weight: bold;
    font-size: 9pt;
    white-space: nowrap;
}
.bar-track {
    background: #e5e7eb;
    border-radius: 3pt;
    height: 6pt;
    width: 100%;
    overflow: hidden;
}
.bar-fill {
    height: 6pt;
    border-radius: 3pt;
}
.stat-num-cell {
    text-align: center;
    font-size: 8pt;
    color: #5a6070;
}
.score-legend {
    font-size: 7.5pt;
    color: #9ca3af;
    margin-top: 6pt;
}

/* ---- Regulation banner ---- */
.reg-banner {
    background: #1a3066;
    color: #ffffff;
    font-size: 9pt;
    font-weight: bold;
    padding: 5pt 8pt;
    margin-top: 10pt;
    margin-bottom: 4pt;
    border-radius: 2pt;
    page-break-after: avoid;
}

/* ---- Gap cards ---- */
.gap-card {
    border: 1pt solid #dde2ea;
    border-radius: 3pt;
    margin-bottom: 6pt;
    overflow: hidden;
    page-break-inside: avoid;
}
.gap-card-header {
    display: table;
    width: 100%;
    background: #f0f3f8;
    border-bottom: 1pt solid #dde2ea;
}
.gap-status-strip {
    display: table-cell;
    width: 4pt;
}
.gap-article {
    display: table-cell;
    padding: 5pt 8pt;
    font-size: 8.5pt;
    font-weight: bold;
    color: #1c2233;
    vertical-align: middle;
}
.gap-badge-cell {
    display: table-cell;
    width: 28mm;
    vertical-align: middle;
    padding-right: 7pt;
    text-align: right;
}
.gap-body { padding: 7pt 8pt 7pt 12pt; }
.gap-label {
    font-size: 7pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    color: #78828f;
    margin-bottom: 2pt;
}
.gap-text {
    font-size: 8.5pt;
    color: #3d4557;
    line-height: 1.55;
}
.gap-deficiency {
    margin-top: 6pt;
    padding: 5pt 8pt;
    background: #fef2f2;
    border-left: 3pt solid #b52018;
    border-radius: 0 2pt 2pt 0;
}
.gap-deficiency .gap-label { color: #b52018; }

/* ---- Action cards ---- */
.action-card {
    border: 1pt solid #dde2ea;
    border-radius: 3pt;
    margin-bottom: 6pt;
    overflow: hidden;
    page-break-inside: avoid;
}
.action-header {
    display: table;
    width: 100%;
}
.priority-badge-cell {
    display: table-cell;
    width: 22mm;
    vertical-align: middle;
    padding: 5pt 8pt;
}
.priority-badge {
    display: inline-block;
    padding: 2.5pt 8pt;
    border-radius: 10pt;
    font-size: 7.5pt;
    font-weight: bold;
    color: #ffffff;
}
.action-art {
    display: table-cell;
    font-size: 8pt;
    font-weight: bold;
    color: #1a3066;
    vertical-align: middle;
}
.action-body { padding: 5pt 10pt 7pt; border-top: 1pt solid #e5e7eb; }
.action-text {
    font-size: 8.5pt;
    color: #1c2233;
    line-height: 1.55;
    margin-bottom: 5pt;
}
.action-meta {
    font-size: 7.5pt;
    color: #78828f;
}
.action-meta strong { color: #3d4557; }

/* ---- Closing ---- */
.next-steps li {
    font-size: 9pt;
    color: #3d4557;
    margin-bottom: 5pt;
    margin-left: 14pt;
    line-height: 1.55;
}
.disclaimer-box {
    background: #f7f9fc;
    border: 1pt solid #dde2ea;
    border-radius: 4pt;
    padding: 10pt 12pt;
    font-size: 8pt;
    color: #5a6070;
    line-height: 1.65;
    margin-top: 8pt;
    font-style: italic;
}
.closing-brand {
    text-align: center;
    margin-top: 16pt;
    font-size: 8.5pt;
    color: #9ca3af;
}
"""


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------

def _cover(report: ComplianceReport, logo_uri: str) -> str:
    score  = report.overall_score_percent
    sc     = _score_color(score)
    date   = report.generated_at[:10] if report.generated_at else ""

    n_app      = sum(1 for r in report.applicable_regulations if r.applies)
    n_gaps     = len(report.gap_analysis)
    n_actions  = len(report.action_plan)
    n_critical = sum(1 for a in report.action_plan if a.priority == Priority.CRITICAL)

    logo_img = (f'<img src="{logo_uri}" class="cover-logo" alt="Complio">'
                if logo_uri else
                '<span style="font-size:14pt;font-weight:bold;color:#fff;">Complio</span>')

    applicable = [r for r in report.applicable_regulations if r.applies]
    # Build regulation chips in rows of 3
    chip_rows = []
    for i in range(0, len(applicable), 3):
        row_chips = applicable[i:i+3]
        cells = "".join(
            f'<td class="reg-chip-cell"><span class="reg-chip">{_h(_reg_label(r.regulation.value))}</span></td>'
            for r in row_chips
        )
        # Pad row to 3 cells
        cells += '<td class="reg-chip-cell"></td>' * (3 - len(row_chips))
        chip_rows.append(f'<tr class="regs-row">{cells}</tr>')

    return f"""
<div class="cover">
  <!-- Dark top section: two-column (left: text, right: score) -->
  <div class="cover-top">
    <div class="cover-top-inner">
      {logo_img}
      <div class="cover-label">Regulatory Compliance Assessment</div>
      <div class="cover-company">{_h(report.company_name)}</div>
      <div class="cover-date">Generated {_h(date)}</div>
    </div>
    <div class="cover-score-block">
      <span class="score-number" style="color:{sc};">{score:.0f}%</span>
      <span class="score-sub">Overall Compliance Score</span>
    </div>
  </div>

  <!-- Stats strip -->
  <div class="cover-stats">
    <div class="cover-stats-inner">
      <div class="stats-row">
        <div class="stat-cell">
          <span class="stat-num">{n_app}</span>
          <span class="stat-label">Regulations</span>
        </div>
        <div class="stat-cell">
          <span class="stat-num">{n_gaps}</span>
          <span class="stat-label">Gaps Found</span>
        </div>
        <div class="stat-cell">
          <span class="stat-num">{n_actions}</span>
          <span class="stat-label">Actions</span>
        </div>
        <div class="stat-cell">
          <span class="stat-num">{n_critical}</span>
          <span class="stat-label">Critical</span>
        </div>
      </div>
    </div>
  </div>

  <!-- White bottom section -->
  <div class="cover-bottom">
    <div class="cover-bottom-inner">
      <div class="cover-regs-title">Applicable Regulations</div>
      <table class="regs-grid">{''.join(chip_rows)}</table>
      <div class="cover-disclaimer">
        This report is produced by an autonomous AI compliance agent and does not constitute legal advice.
        Consult a qualified legal professional before making compliance decisions.
        Complio is not a substitute for certified legal audit.
      </div>
    </div>
  </div>
</div>
"""


def _section_header(company_name: str, logo_uri: str) -> str:
    """Repeating header printed at the top of each content section."""
    logo_img = (f'<img src="{logo_uri}" alt="Complio">'
                if logo_uri else
                '<strong style="color:#0c1c40;font-size:10pt;">Complio</strong>')
    return f"""
<table class="page-header">
  <tr>
    <td class="logo-cell">{logo_img}</td>
    <td class="co-name">{_h(company_name)}</td>
  </tr>
</table>
<div class="content-wrap">
"""


def _summary_section(report: ComplianceReport) -> str:
    summary = _h(_clean(report.executive_summary)) if report.executive_summary else "No executive summary generated."

    warnings_html = ""
    if report.validation_warnings:
        items = "".join(f"<li>{_h(w)}</li>" for w in report.validation_warnings)
        warnings_html = f"""
        <div class="section-subtitle">Validation Warnings</div>
        <ul style="padding-left:14pt;margin-bottom:8pt;">
          {items}
        </ul>"""

    return f"""
<div class="section-break">
  <div class="section-title">1. Executive Summary</div>
  <p class="body-text">{summary}</p>
  {warnings_html}
</div>
"""


def _applicability_section(report: ComplianceReport) -> str:
    rows = ""
    for reg in report.applicable_regulations:
        label   = _reg_label(reg.regulation.value)
        badge   = (f'<span class="badge badge-yes">Yes</span>' if reg.applies
                   else f'<span class="badge badge-no">No</span>')
        reason  = _h(_clean(reg.reason))
        rows += f"""
        <tr>
          <td><strong>{_h(label)}</strong></td>
          <td style="text-align:center;">{badge}</td>
          <td>{reason}</td>
        </tr>"""

    return f"""
<div style="margin-top:18pt;">
  <div class="section-title">2. Regulation Applicability</div>
  <p class="body-text">The table below shows which regulations apply to your organisation based on the submitted company profile.</p>
  <table class="data-table">
    <thead>
      <tr>
        <th style="width:26%;">Regulation</th>
        <th style="width:14%;text-align:center;">Applies</th>
        <th>Reason</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""


def _scores_section(report: ComplianceReport) -> str:
    score  = report.overall_score_percent
    sc     = _score_color(score)

    if not report.regulation_scores:
        return f"""
<div class="section-break">
  <div class="section-title">3. Score Breakdown</div>
  <p class="body-text">No regulation scores available.</p>
</div>"""

    rows = ""
    for rs in report.regulation_scores:
        label     = _reg_label(rs.regulation.value)
        bar_col   = _score_color(rs.score_percent)
        bar_width = min(100.0, max(0.0, rs.score_percent))
        rows += f"""
        <tr>
          <td><strong>{_h(label)}</strong></td>
          <td><span class="score-pct" style="color:{bar_col};">{rs.score_percent:.0f}%</span></td>
          <td>
            <div class="bar-track">
              <div class="bar-fill" style="width:{bar_width}%;background:{bar_col};"></div>
            </div>
          </td>
          <td class="stat-num-cell">{rs.compliant}</td>
          <td class="stat-num-cell">{rs.partially_compliant}</td>
          <td class="stat-num-cell">{rs.non_compliant}</td>
          <td class="stat-num-cell">{rs.cannot_assess}</td>
          <td class="stat-num-cell">{rs.total_requirements}</td>
        </tr>"""

    return f"""
<div class="section-break">
  <div class="section-title">3. Score Breakdown</div>

  <div class="score-banner" style="background:{sc};">
    <span class="score-banner-num">{score:.1f}%</span>
    <div class="score-banner-label">Overall Compliance Score</div>
  </div>

  <table class="score-table">
    <thead>
      <tr>
        <th style="width:28%;">Regulation</th>
        <th style="width:12%;">Score</th>
        <th>Progress</th>
        <th class="center" style="width:8%;">C</th>
        <th class="center" style="width:8%;">P</th>
        <th class="center" style="width:8%;">NC</th>
        <th class="center" style="width:8%;">?</th>
        <th class="center" style="width:9%;">Total</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="score-legend">C = Compliant &nbsp;&nbsp; P = Partially Compliant &nbsp;&nbsp; NC = Non-Compliant &nbsp;&nbsp; ? = Cannot Assess</div>
</div>
"""


def _gaps_section(report: ComplianceReport) -> str:
    if not report.gap_analysis:
        return """
<div class="section-break">
  <div class="section-title">4. Gap Analysis</div>
  <p class="body-text">No gap analysis available.</p>
</div>"""

    gaps_by_reg: dict[str, list] = {}
    for g in report.gap_analysis:
        gaps_by_reg.setdefault(g.regulation.value, []).append(g)

    content = ""
    for reg_key, gaps in gaps_by_reg.items():
        content += f'<div class="reg-banner">{_h(_reg_label(reg_key))}</div>'
        for gap in gaps:
            sc    = STATUS_COLORS.get(gap.status, "#78828f")
            slbl  = STATUS_LABELS.get(gap.status, str(gap.status))
            art   = f"Art. {_h(gap.article_number)}  ·  {_h(gap.article_title)}"
            ev    = _h(_clean(gap.evidence))
            defic = _h(_clean(gap.deficiency_description))

            defic_html = ""
            if defic:
                defic_html = f"""
              <div class="gap-deficiency">
                <div class="gap-label">What needs to change</div>
                <div class="gap-text">{defic}</div>
              </div>"""

            content += f"""
<div class="gap-card">
  <div class="gap-card-header">
    <div class="gap-status-strip" style="background:{sc};"></div>
    <div class="gap-article">{art}</div>
    <div class="gap-badge-cell">
      <span class="badge" style="background:{sc};">{_h(slbl)}</span>
    </div>
  </div>
  <div class="gap-body">
    <div class="gap-label">Assessment</div>
    <div class="gap-text">{ev}</div>
    {defic_html}
  </div>
</div>"""

    return f"""
<div class="section-break">
  <div class="section-title">4. Gap Analysis</div>
  <p class="body-text">Every assessed requirement is listed below, grouped by regulation. Green = compliant, amber = partial gaps, red = non-compliant.</p>
  {content}
</div>
"""


def _actions_section(report: ComplianceReport) -> str:
    if not report.action_plan:
        return """
<div class="section-break">
  <div class="section-title">5. Action Plan</div>
  <p class="body-text">No remediation actions required.</p>
</div>"""

    actions_by_reg: dict[str, list] = {}
    for a in report.action_plan:
        actions_by_reg.setdefault(a.regulation.value, []).append(a)

    content = ""
    for reg_key, actions in actions_by_reg.items():
        content += f'<div class="reg-banner">{_h(_reg_label(reg_key))}</div>'
        for act in actions:
            pc     = PRIORITY_COLORS.get(act.priority, "#78828f")
            prio   = _h(act.priority.value)
            effort = _h(act.estimated_effort)
            dl     = f"  <strong>Deadline:</strong> {_h(act.deadline)}" if act.deadline else ""
            action_text = _h(_clean(act.action))

            content += f"""
<div class="action-card">
  <div class="action-header">
    <div class="priority-badge-cell">
      <span class="priority-badge" style="background:{pc};">{prio}</span>
    </div>
    <div class="action-art">Art. {_h(act.article_number)} &nbsp;·&nbsp; {_h(_reg_label(act.regulation.value))}</div>
  </div>
  <div class="action-body">
    <div class="action-text">{action_text}</div>
    <div class="action-meta"><strong>Effort:</strong> {effort}{dl}</div>
  </div>
</div>"""

    return f"""
<div class="section-break">
  <div class="section-title">5. Action Plan</div>
  <p class="body-text">Recommended actions to close identified compliance gaps, ordered by priority.</p>
  {content}
</div>
"""


def _closing_section(report: ComplianceReport) -> str:
    steps = [
        "Review each gap finding with your legal or compliance team.",
        "Prioritise Critical and High priority action items immediately.",
        "Establish a compliance calendar with realistic deadlines from the Action Plan.",
        "Re-run this assessment after implementing changes to track your progress.",
        "Engage a qualified legal counsel for binding compliance decisions.",
    ]
    step_items = "".join(f"<li>{s}</li>" for s in steps)
    disclaimer = _h(report.disclaimer)

    return f"""
<div class="section-break">
  <div class="section-title">6. Next Steps &amp; Disclaimer</div>

  <div class="section-subtitle">Recommended Next Steps</div>
  <ul class="next-steps">{step_items}</ul>

  <div class="section-subtitle" style="margin-top:16pt;">Legal Disclaimer</div>
  <div class="disclaimer-box">{disclaimer}</div>

  <div class="closing-brand">
    Complio &mdash; Autonomous Regulatory Compliance for German SMEs<br>
    <span style="font-size:7.5pt;">This report was generated automatically and is not a substitute for legal advice.</span>
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _wrap_section(content: str, company_name: str, logo_uri: str) -> str:
    """Wrap a content section with the repeating header."""
    return _section_header(company_name, logo_uri) + content + "\n</div>"


def generate_pdf(report: ComplianceReport) -> bytes:
    logo_uri  = _logo_data_uri()
    co_name   = report.company_name
    logo_uri2 = logo_uri  # alias for readability

    # Playwright header template (shown on every page)
    header_logo = (
        f'<img src="{logo_uri2}" style="height:9pt;vertical-align:middle;" alt="Complio">'
        if logo_uri2 else
        '<span style="font-size:9pt;font-weight:bold;color:#0c1c40;">Complio</span>'
    )
    header_html = f"""<div style="font-family:Arial,sans-serif;font-size:7.5pt;color:#5a6070;
        display:flex;justify-content:space-between;align-items:center;
        width:100%;padding:0 15mm;border-bottom:1px solid #dde2ea;padding-bottom:3pt;">
      <span>{header_logo}</span>
      <span>{_h(co_name)}</span>
    </div>"""

    footer_html = """<div style="font-family:Arial,sans-serif;font-size:7pt;color:#9ca3af;
        display:flex;justify-content:space-between;width:100%;padding:0 15mm;">
      <span>Complio &mdash; Autonomous Regulatory Compliance</span>
      <span class="pageNumber"></span>
    </div>"""

    html_str = "\n".join([
        f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><style>{CSS}</style></head><body>',
        _cover(report, logo_uri),
        _wrap_section(_summary_section(report) + _applicability_section(report), co_name, logo_uri),
        _wrap_section(_scores_section(report), co_name, logo_uri),
        _wrap_section(_gaps_section(report), co_name, logo_uri),
        _wrap_section(_actions_section(report), co_name, logo_uri),
        _wrap_section(_closing_section(report), co_name, logo_uri),
        "</body></html>",
    ])

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page    = browser.new_page()
        page.set_content(html_str, wait_until="domcontentloaded")
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_html,
            footer_template=footer_html,
            margin={"top": "18mm", "bottom": "12mm", "left": "0mm", "right": "0mm"},
        )
        browser.close()

    return pdf_bytes
