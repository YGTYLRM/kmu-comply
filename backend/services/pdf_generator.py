"""
PDF Report Generator — Complio
Playwright/Chromium renderer. Zero external margin — all spacing in HTML.
"""
from __future__ import annotations
import base64, re
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright
from models.compliance_report import ComplianceReport
from models.enums import ComplianceStatus, Priority

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo-dark-bg.png"

REG_LABELS = {
    "gdpr_dsgvo":"GDPR / DSGVO","bdsg":"BDSG","lksg":"LkSG","enefg":"EnEfG",
    "csrd":"CSRD","nis2":"NIS2","eu_ai_act":"EU AI Act","hinschg":"HinSchG",
    "arbschg":"ArbSchG","agg":"AGG","milog":"MiLoG",
}
S = {
    ComplianceStatus.COMPLIANT:           {"c":"#16a34a","bg":"#f0fdf4","br":"#bbf7d0","label":"Compliant"},
    ComplianceStatus.PARTIALLY_COMPLIANT: {"c":"#b45309","bg":"#fffbeb","br":"#fde68a","label":"Partial"},
    ComplianceStatus.NON_COMPLIANT:       {"c":"#dc2626","bg":"#fef2f2","br":"#fecaca","label":"Non-Compliant"},
    ComplianceStatus.CANNOT_ASSESS:       {"c":"#64748b","bg":"#f8fafc","br":"#e2e8f0","label":"Cannot Assess"},
}
P = {
    Priority.CRITICAL:{"c":"#dc2626","bg":"#fef2f2","br":"#fecaca","label":"Critical"},
    Priority.HIGH:    {"c":"#ea580c","bg":"#fff7ed","br":"#fed7aa","label":"High"},
    Priority.MEDIUM:  {"c":"#b45309","bg":"#fffbeb","br":"#fde68a","label":"Medium"},
    Priority.LOW:     {"c":"#16a34a","bg":"#f0fdf4","br":"#bbf7d0","label":"Low"},
}

def _reg(k): return REG_LABELS.get(k, k.upper())
def _sc(v):
    if v>=75: return "#16a34a"
    if v>=40: return "#b45309"
    return "#dc2626"
def _sbg(v):
    if v>=75: return "#f0fdf4"
    if v>=40: return "#fffbeb"
    return "#fef2f2"
def _sbr(v):
    if v>=75: return "#bbf7d0"
    if v>=40: return "#fde68a"
    return "#fecaca"

def _h(t):
    if not t: return ""
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def _c(t):
    """Clean LLM artefacts: field=value patterns and dashes."""
    if not t: return ""
    t = re.sub(r'\b\w+=(?:true|false|null|\d+(?:\.\d+)?)\b', '', t)
    t = t.replace('—',' ').replace('–',' ').replace('--',' ')
    return re.sub(r'  +', ' ', t).strip().lstrip('.,;')

def _logo():
    if LOGO_PATH.exists():
        try:
            return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()
        except: pass
    return ""

# Shared inline style values
FONT  = "font-family:'Inter',Arial,sans-serif;"
NAVY  = "#0f172a"
BLUE  = "#1d4ed8"
M     = "14mm"   # horizontal margin for body text

# ─────────────────────────────────────────────────────────────────────────────
# Page header bar — embedded in every content page
# ─────────────────────────────────────────────────────────────────────────────

def _hbar(company: str, section: str, logo: str) -> str:
    logo_el = (f'<img src="{logo}" style="height:11pt;vertical-align:middle;" alt="Complio">'
               if logo else
               f'<span style="font-weight:800;font-size:11pt;color:#fff;">{FONT}Complio</span>')
    return f"""<div style="{FONT}background:{NAVY};padding:5mm {M};
        display:flex;align-items:center;justify-content:space-between;">
  <div>{logo_el}</div>
  <div style="text-align:right;">
    <div style="font-size:7.5pt;color:#94a3b8;">{_h(company)}</div>
    <div style="font-size:6.5pt;color:#475569;text-transform:uppercase;letter-spacing:.8pt;margin-top:1pt;">{_h(section)}</div>
  </div>
</div>"""


def _body_open() -> str:
    return f'<div style="padding:7mm {M} 12mm;">'


def _body_close() -> str:
    return '</div>'


def _sec_title(num: str, title: str) -> str:
    return f"""<div style="{FONT}font-size:6pt;font-weight:600;letter-spacing:2pt;
        text-transform:uppercase;color:{BLUE};margin-bottom:2mm;">{num}</div>
<div style="{FONT}font-size:17pt;font-weight:800;color:{NAVY};letter-spacing:-.3pt;
        line-height:1.1;margin-bottom:2mm;padding-bottom:3mm;
        border-bottom:2pt solid #f1f5f9;">{title}</div>"""


def _sec_sub(text: str) -> str:
    return f'<p style="{FONT}font-size:9pt;color:#64748b;line-height:1.65;margin-bottom:6mm;max-width:170mm;">{text}</p>'


# ─────────────────────────────────────────────────────────────────────────────
# Cover
# ─────────────────────────────────────────────────────────────────────────────

def _cover(report: ComplianceReport, logo: str) -> str:
    sc   = _sc(report.overall_score_percent)
    sbg  = _sbg(report.overall_score_percent)
    date = report.generated_at[:10] if report.generated_at else ""

    n_app  = sum(1 for r in report.applicable_regulations if r.applies)
    n_gaps = len(report.gap_analysis)
    n_act  = len(report.action_plan)
    n_crit = sum(1 for a in report.action_plan if a.priority == Priority.CRITICAL)

    logo_el = (f'<img src="{logo}" style="height:30pt;" alt="Complio">'
               if logo else
               f'<span style="{FONT}font-size:22pt;font-weight:800;color:#fff;">Complio</span>')

    chips = "".join(
        f'<span style="{FONT}font-size:7pt;font-weight:600;color:#93c5fd;'
        f'background:rgba(59,130,246,.12);border:1pt solid rgba(147,197,253,.3);'
        f'border-radius:20pt;padding:2pt 9pt;margin:0 2mm 2mm 0;display:inline-block;">'
        f'{_h(_reg(r.regulation.value))}</span>'
        for r in report.applicable_regulations if r.applies
    )

    def stat(n, lbl, color="#fff"):
        return f"""<div style="text-align:center;padding:0 6mm;">
      <div style="{FONT}font-size:22pt;font-weight:800;color:{color};line-height:1;">{n}</div>
      <div style="{FONT}font-size:6pt;font-weight:600;text-transform:uppercase;
          letter-spacing:.8pt;color:#475569;margin-top:1.5mm;">{lbl}</div>
    </div>"""

    divider = '<div style="width:1pt;height:10mm;background:rgba(255,255,255,.1);margin:0 2mm;"></div>'

    return f"""
<div style="width:100%;height:297mm;background:linear-gradient(145deg,#020817 0%,#0c1a40 55%,#0f2052 100%);
    display:flex;flex-direction:column;page-break-after:always;overflow:hidden;position:relative;">

  <!-- Top bar -->
  <div style="padding:9mm {M} 0;display:flex;align-items:center;justify-content:space-between;">
    {logo_el}
    <div style="{FONT}font-size:6.5pt;font-weight:600;letter-spacing:1.8pt;text-transform:uppercase;
        color:#93c5fd;border:1pt solid rgba(147,197,253,.3);padding:3pt 9pt;border-radius:20pt;">
      Regulatory Compliance Assessment
    </div>
  </div>

  <!-- Hero -->
  <div style="flex:1;padding:10mm {M} 5mm;display:flex;flex-direction:column;justify-content:center;">
    <div style="{FONT}font-size:7pt;font-weight:600;letter-spacing:2pt;text-transform:uppercase;
        color:#3b82f6;margin-bottom:4mm;">Autonomous AI Compliance Agent</div>
    <div style="{FONT}font-size:33pt;font-weight:800;color:#fff;line-height:1.1;
        letter-spacing:-.8pt;margin-bottom:4mm;max-width:155mm;">{_h(report.company_name)}</div>
    <div style="{FONT}font-size:8.5pt;color:#475569;margin-bottom:8mm;">Report issued {_h(date)}</div>

    <!-- Score + stats row -->
    <div style="display:flex;align-items:center;gap:0;">
      <!-- Score ring -->
      <div style="width:26mm;height:26mm;border-radius:50%;border:2.5pt solid {sc};
          background:{sbg}20;display:flex;flex-direction:column;align-items:center;
          justify-content:center;flex-shrink:0;margin-right:6mm;">
        <div style="{FONT}font-size:15pt;font-weight:800;color:{sc};line-height:1;">
          {report.overall_score_percent:.0f}%
        </div>
        <div style="{FONT}font-size:5.5pt;font-weight:600;text-transform:uppercase;
            letter-spacing:.8pt;color:{sc};opacity:.75;margin-top:1pt;">Score</div>
      </div>
      {divider}
      {stat(n_app, "Regulations")}
      {divider}
      {stat(n_gaps, "Gaps")}
      {divider}
      {stat(n_act, "Actions")}
      {divider}
      {stat(n_crit, "Critical", "#f87171")}
    </div>
  </div>

  <!-- Bottom -->
  <div style="padding:0 {M} 8mm;">
    <div style="border-top:1pt solid rgba(255,255,255,.08);margin-bottom:5mm;"></div>
    <div style="{FONT}font-size:6.5pt;font-weight:600;letter-spacing:1.5pt;text-transform:uppercase;
        color:#475569;margin-bottom:3mm;">Applicable Regulations</div>
    <div>{chips}</div>
    <div style="{FONT}font-size:7pt;color:#334155;line-height:1.6;margin-top:5mm;">
      Complio checks your company against German and EU regulations using an autonomous AI agent.
      This report shows where gaps likely exist. It is not a legal audit and does not replace a lawyer.
    </div>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 1+2 — Summary and Applicability
# ─────────────────────────────────────────────────────────────────────────────

def _summary_and_applicability(report: ComplianceReport, logo: str) -> str:
    summary = _h(_c(report.executive_summary)) or "No executive summary available."

    warns = ""
    if report.validation_warnings:
        items = "".join(f'<li style="margin-bottom:3pt;">{_h(w)}</li>'
                        for w in report.validation_warnings)
        warns = f'<div style="margin-top:5mm;"><div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;letter-spacing:1pt;color:#94a3b8;margin-bottom:2mm;">Warnings</div><ul style="padding-left:14pt;">{items}</ul></div>'

    # Table column widths must sum to 100%
    rows = ""
    for r in report.applicable_regulations:
        bg = "#fafafa" if report.applicable_regulations.index(r) % 2 == 1 else "#fff"
        badge_style = ("background:#f0fdf4;color:#16a34a;border:1pt solid #bbf7d0;" if r.applies
                       else "background:#f8fafc;color:#64748b;border:1pt solid #e2e8f0;")
        rows += f"""<tr style="background:{bg};">
          <td style="{FONT}padding:6pt 9pt;font-weight:600;font-size:8.5pt;width:22%;border-bottom:1pt solid #f1f5f9;white-space:nowrap;">{_h(_reg(r.regulation.value))}</td>
          <td style="padding:6pt 9pt;text-align:center;width:12%;border-bottom:1pt solid #f1f5f9;">
            <span style="{FONT}display:inline-block;font-size:7pt;font-weight:700;
                padding:2pt 7pt;border-radius:20pt;{badge_style}">{'Yes' if r.applies else 'No'}</span>
          </td>
          <td style="{FONT}padding:6pt 9pt;font-size:8.5pt;color:#334155;line-height:1.55;width:66%;border-bottom:1pt solid #f1f5f9;">{_h(_c(r.reason))}</td>
        </tr>"""

    return f"""
<div style="page-break-before:always;">
  {_hbar(report.company_name, "Executive Summary", logo)}
  {_body_open()}
    {_sec_title("Section 01", "Executive Summary")}
    {_sec_sub(summary)}
    {warns}

    <div style="margin-top:8mm;">
      {_sec_title("Section 02", "Regulation Applicability")}
      {_sec_sub("Which regulations apply to your company, based on your size, industry, and how you operate.")}
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;word-break:break-word;">
        <thead>
          <tr>
            <th style="{FONT}background:{NAVY};color:#fff;font-size:7.5pt;font-weight:600;
                padding:5.5pt 9pt;text-align:left;width:22%;">Regulation</th>
            <th style="{FONT}background:{NAVY};color:#fff;font-size:7.5pt;font-weight:600;
                padding:5.5pt 9pt;text-align:center;width:12%;">Applies</th>
            <th style="{FONT}background:{NAVY};color:#fff;font-size:7.5pt;font-weight:600;
                padding:5.5pt 9pt;text-align:left;width:66%;">Reason</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  {_body_close()}
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Scores
# ─────────────────────────────────────────────────────────────────────────────

def _scores(report: ComplianceReport, logo: str) -> str:
    sc  = _sc(report.overall_score_percent)
    sbg = _sbg(report.overall_score_percent)
    sbr = _sbr(report.overall_score_percent)
    n_c = sum(rs.compliant for rs in report.regulation_scores)
    n_p = sum(rs.partially_compliant for rs in report.regulation_scores)
    n_n = sum(rs.non_compliant for rs in report.regulation_scores)
    n_t = sum(rs.total_requirements for rs in report.regulation_scores)

    def sbox(n, lbl, c):
        return f"""<td style="width:25%;padding:0 2mm;">
          <div style="{FONT}border:1pt solid #e2e8f0;border-radius:6pt;padding:4mm;text-align:center;background:#fafafa;">
            <div style="font-size:18pt;font-weight:800;color:{c};line-height:1;margin-bottom:1mm;">{n}</div>
            <div style="font-size:6.5pt;font-weight:600;text-transform:uppercase;letter-spacing:.8pt;color:#94a3b8;">{lbl}</div>
          </div>
        </td>"""

    # Score table rows — widths must sum to 100%: 28+10+38+8+8+8 = 100
    rows = ""
    for i, rs in enumerate(report.regulation_scores):
        bc  = _sc(rs.score_percent)
        bw  = min(100.0, max(0.0, rs.score_percent))
        bg  = "#fafafa" if i % 2 == 1 else "#fff"
        rows += f"""<tr style="background:{bg};">
          <td style="{FONT}padding:6pt 8pt;font-weight:600;font-size:8.5pt;width:28%;">{_h(_reg(rs.regulation.value))}</td>
          <td style="{FONT}padding:6pt 8pt;text-align:center;font-weight:800;font-size:10pt;color:{bc};width:10%;">{rs.score_percent:.0f}%</td>
          <td style="padding:6pt 8pt;width:38%;">
            <div style="height:6pt;background:#f1f5f9;border-radius:10pt;overflow:hidden;">
              <div style="height:6pt;width:{bw}%;background:{bc};border-radius:10pt;"></div>
            </div>
          </td>
          <td style="{FONT}padding:6pt 8pt;text-align:center;color:#16a34a;font-weight:600;font-size:8.5pt;width:8%;">{rs.compliant}</td>
          <td style="{FONT}padding:6pt 8pt;text-align:center;color:#b45309;font-weight:600;font-size:8.5pt;width:8%;">{rs.partially_compliant}</td>
          <td style="{FONT}padding:6pt 8pt;text-align:center;color:#dc2626;font-weight:600;font-size:8.5pt;width:8%;">{rs.non_compliant}</td>
        </tr>"""

    return f"""
<div style="page-break-before:always;">
  {_hbar(report.company_name, "Score Breakdown", logo)}
  {_body_open()}
    {_sec_title("Section 03", "Score Breakdown")}

    <!-- Hero score -->
    <div style="background:{sbg};border:1.5pt solid {sbr};border-radius:8pt;
        padding:7mm 9mm;margin-bottom:6mm;display:flex;align-items:center;gap:8mm;">
      <div style="{FONT}font-size:44pt;font-weight:800;color:{sc};letter-spacing:-2pt;line-height:1;flex-shrink:0;">
        {report.overall_score_percent:.1f}%
      </div>
      <div>
        <div style="{FONT}font-size:10pt;font-weight:700;color:{NAVY};margin-bottom:2mm;">Overall Compliance Score</div>
        <div style="{FONT}font-size:8pt;color:#64748b;line-height:1.6;">
          {len(report.regulation_scores)} regulations checked &nbsp;|&nbsp;
          {n_t} requirements assessed &nbsp;|&nbsp;
          {len(report.gap_analysis)} gaps found
        </div>
      </div>
    </div>

    <!-- Stat boxes -->
    <table style="width:100%;border-collapse:collapse;margin-bottom:6mm;table-layout:fixed;">
      <tr>
        {sbox(n_c, "Compliant", "#16a34a")}
        {sbox(n_p, "Partial", "#b45309")}
        {sbox(n_n, "Non-Compliant", "#dc2626")}
        {sbox(n_t, "Total Checked", NAVY)}
      </tr>
    </table>

    <!-- Score table: col widths 28+10+38+8+8+8 = 100 -->
    <table style="width:100%;border-collapse:collapse;table-layout:fixed;word-break:break-word;">
      <thead>
        <tr>
          <th style="{FONT}background:#f1f5f9;color:#64748b;font-size:7pt;font-weight:600;
              text-transform:uppercase;letter-spacing:.5pt;padding:4pt 8pt;text-align:left;
              border-bottom:1.5pt solid #e2e8f0;width:28%;">Regulation</th>
          <th style="{FONT}background:#f1f5f9;color:#64748b;font-size:7pt;font-weight:600;
              text-transform:uppercase;letter-spacing:.5pt;padding:4pt 8pt;text-align:center;
              border-bottom:1.5pt solid #e2e8f0;width:10%;">Score</th>
          <th style="{FONT}background:#f1f5f9;color:#64748b;font-size:7pt;font-weight:600;
              text-transform:uppercase;letter-spacing:.5pt;padding:4pt 8pt;
              border-bottom:1.5pt solid #e2e8f0;width:38%;">Progress</th>
          <th style="{FONT}background:#f1f5f9;color:#16a34a;font-size:7pt;font-weight:600;
              padding:4pt 8pt;text-align:center;border-bottom:1.5pt solid #e2e8f0;width:8%;">C</th>
          <th style="{FONT}background:#f1f5f9;color:#b45309;font-size:7pt;font-weight:600;
              padding:4pt 8pt;text-align:center;border-bottom:1.5pt solid #e2e8f0;width:8%;">P</th>
          <th style="{FONT}background:#f1f5f9;color:#dc2626;font-size:7pt;font-weight:600;
              padding:4pt 8pt;text-align:center;border-bottom:1.5pt solid #e2e8f0;width:8%;">NC</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <div style="{FONT}font-size:7pt;color:#94a3b8;margin-top:3mm;">
      C = Compliant &nbsp;&nbsp; P = Partially Compliant &nbsp;&nbsp; NC = Non-Compliant
    </div>
  {_body_close()}
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Gap Analysis (one page per regulation)
# ─────────────────────────────────────────────────────────────────────────────

def _gap_card(g) -> str:
    cm    = S.get(g.status, S[ComplianceStatus.CANNOT_ASSESS])
    ev    = _h(_c(g.evidence))
    defic = _h(_c(g.deficiency_description))
    art_n = _h(_c(g.article_number))
    art_t = _h(_c(g.article_title))

    fix = ""
    if defic:
        fix = f"""<div style="margin-top:5pt;padding:5pt 8pt;
            border-left:3pt solid #dc2626;background:#fef2f2;border-radius:0 4pt 4pt 0;">
          <div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;
              letter-spacing:1pt;color:#dc2626;margin-bottom:2pt;">What needs to change</div>
          <div style="{FONT}font-size:8.5pt;color:#7f1d1d;line-height:1.6;">{defic}</div>
        </div>"""

    return f"""<div style="border:1pt solid #e2e8f0;border-radius:6pt;
        margin-bottom:4mm;overflow:hidden;page-break-inside:avoid;">
  <!-- Card header -->
  <div style="display:flex;align-items:stretch;background:#f8fafc;border-bottom:1pt solid #f1f5f9;">
    <div style="width:4pt;background:{cm['c']};flex-shrink:0;"></div>
    <div style="flex:1;padding:5pt 9pt;display:flex;align-items:center;justify-content:space-between;gap:6pt;">
      <div>
        <div style="{FONT}font-size:8.5pt;font-weight:700;color:{NAVY};">Art. {art_n} &nbsp;·&nbsp; {art_t}</div>
        <div style="{FONT}font-size:7pt;color:#94a3b8;margin-top:1pt;">{_h(_reg(g.regulation.value))}</div>
      </div>
      <div style="{FONT}display:inline-flex;align-items:center;gap:4pt;font-size:7pt;font-weight:700;
          padding:2.5pt 8pt;border-radius:20pt;border:1pt solid {cm['br']};
          background:{cm['bg']};color:{cm['c']};white-space:nowrap;flex-shrink:0;">
        <span style="width:5pt;height:5pt;border-radius:50%;background:{cm['c']};display:inline-block;"></span>
        {_h(cm['label'])}
      </div>
    </div>
  </div>
  <!-- Card body -->
  <div style="padding:6pt 9pt 7pt 13pt;">
    <div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;
        letter-spacing:1pt;color:#94a3b8;margin-bottom:2pt;">Assessment</div>
    <div style="{FONT}font-size:8.5pt;color:#334155;line-height:1.65;">{ev}</div>
    {fix}
  </div>
</div>"""


def _gaps(report: ComplianceReport, logo: str) -> str:
    if not report.gap_analysis:
        return f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, "Gap Analysis", logo)}
  {_body_open()}{_sec_title("Section 04","Gap Analysis")}<p>No gaps found.</p>{_body_close()}
</div>"""

    by_reg: dict[str,list] = {}
    for g in report.gap_analysis:
        by_reg.setdefault(g.regulation.value, []).append(g)

    # Section intro page
    html = f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, "Gap Analysis", logo)}
  {_body_open()}
    {_sec_title("Section 04", "Gap Analysis")}
    {_sec_sub("Every requirement we checked, grouped by regulation. You can see exactly why each one passed or failed, and what needs to change where something is missing.")}
  {_body_close()}
</div>"""

    # One page per regulation
    for reg_key, gaps in by_reg.items():
        n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
        n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
        n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
        cards = "".join(_gap_card(g) for g in gaps)

        html += f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, f"Gap Analysis — {_reg(reg_key)}", logo)}
  {_body_open()}
    <div style="margin-bottom:5mm;">
      <div style="{FONT}display:inline-flex;align-items:center;gap:6pt;font-size:8pt;
          font-weight:700;text-transform:uppercase;letter-spacing:1.2pt;color:{BLUE};">
        <span style="width:3pt;height:14pt;background:{BLUE};border-radius:2pt;display:inline-block;"></span>
        {_h(_reg(reg_key))}
      </div>
      <div style="{FONT}font-size:7.5pt;color:#94a3b8;margin-top:2mm;">
        {n_c} compliant &nbsp;·&nbsp; {n_p} partial &nbsp;·&nbsp; {n_n} non-compliant
      </div>
    </div>
    {cards}
  {_body_close()}
</div>"""

    return html


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Action Plan (one page per regulation)
# ─────────────────────────────────────────────────────────────────────────────

def _action_card(a) -> str:
    pm  = P.get(a.priority, P[Priority.LOW])
    dl  = f"&nbsp;&nbsp;<b>Deadline:</b> {_h(_c(a.deadline))}" if a.deadline else ""
    return f"""<div style="border:1pt solid #e2e8f0;border-radius:6pt;
        margin-bottom:4mm;overflow:hidden;page-break-inside:avoid;">
  <div style="display:flex;align-items:center;gap:7pt;padding:5pt 9pt;
      background:#f8fafc;border-bottom:1pt solid #f1f5f9;">
    <span style="{FONT}display:inline-block;font-size:7pt;font-weight:700;
        padding:2pt 8pt;border-radius:20pt;border:1pt solid {pm['br']};
        background:{pm['bg']};color:{pm['c']};flex-shrink:0;">{_h(pm['label'])}</span>
    <span style="{FONT}font-size:8pt;font-weight:700;color:{NAVY};">Art. {_h(_c(a.article_number))}</span>
    <span style="{FONT}font-size:7pt;color:#94a3b8;margin-left:auto;">{_h(_reg(a.regulation.value))}</span>
  </div>
  <div style="padding:6pt 9pt 7pt;">
    <div style="{FONT}font-size:8.5pt;color:#1a202c;line-height:1.65;margin-bottom:4pt;">{_h(_c(a.action))}</div>
    <div style="{FONT}font-size:7.5pt;color:#64748b;">
      <b style="color:#374151;">Effort:</b> {_h(_c(a.estimated_effort))}{dl}
    </div>
  </div>
</div>"""


def _actions(report: ComplianceReport, logo: str) -> str:
    if not report.action_plan:
        return f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, "Action Plan", logo)}
  {_body_open()}{_sec_title("Section 05","Action Plan")}<p>No actions required.</p>{_body_close()}
</div>"""

    by_reg: dict[str,list] = {}
    for a in report.action_plan:
        by_reg.setdefault(a.regulation.value, []).append(a)

    html = f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, "Action Plan", logo)}
  {_body_open()}
    {_sec_title("Section 05", "Action Plan")}
    {_sec_sub("A concrete to-do list for closing your compliance gaps. Start with Critical and High items. Each one includes an effort estimate so you can plan realistically.")}
  {_body_close()}
</div>"""

    for reg_key, acts in by_reg.items():
        cards = "".join(_action_card(a) for a in acts)
        html += f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, f"Action Plan — {_reg(reg_key)}", logo)}
  {_body_open()}
    <div style="margin-bottom:5mm;">
      <div style="{FONT}display:inline-flex;align-items:center;gap:6pt;font-size:8pt;
          font-weight:700;text-transform:uppercase;letter-spacing:1.2pt;color:{BLUE};">
        <span style="width:3pt;height:14pt;background:{BLUE};border-radius:2pt;display:inline-block;"></span>
        {_h(_reg(reg_key))}
      </div>
    </div>
    {cards}
  {_body_close()}
</div>"""

    return html


# ─────────────────────────────────────────────────────────────────────────────
# Section 6 — Closing
# ─────────────────────────────────────────────────────────────────────────────

def _closing(report: ComplianceReport, logo: str) -> str:
    steps = [
        "Start with <b>Critical</b> and <b>High</b> priority items. These are your live legal risks right now.",
        "Give every action an owner and a deadline. Without that, nothing gets done.",
        "Keep written records of everything you implement. Regulators will ask for proof.",
        "Run this assessment again after you make changes. You will see the score move.",
        "For anything you are unsure about, talk to a lawyer before acting on it.",
    ]
    items = "".join(f'<li style="{FONT}font-size:9pt;color:#334155;margin-bottom:5pt;line-height:1.65;">{s}</li>'
                    for s in steps)
    return f"""<div style="page-break-before:always;">
  {_hbar(report.company_name, "Next Steps", logo)}
  {_body_open()}
    {_sec_title("Section 06", "Next Steps")}
    {_sec_sub("You know where you stand now. Here is what to do next.")}
    <ul style="padding-left:16pt;">{items}</ul>

    <div style="margin-top:8mm;">
      <div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;
          letter-spacing:1pt;color:#94a3b8;margin-bottom:2mm;">Legal Disclaimer</div>
      <div style="{FONT}padding:5.5mm 6mm;background:#f8fafc;border:1pt solid #e2e8f0;
          border-radius:6pt;font-size:8pt;color:#64748b;line-height:1.75;font-style:italic;">
        {_h(report.disclaimer)}
      </div>
    </div>

    <div style="margin-top:8mm;padding-top:5mm;border-top:1pt solid #f1f5f9;
        text-align:center;{FONT}font-size:7.5pt;color:#94a3b8;">
      <strong style="color:{NAVY};">Complio</strong> &nbsp;·&nbsp; Autonomous Regulatory Compliance for German SMEs<br>
      <span style="font-size:7pt;">Produced by an AI agent. Not a certified legal audit. Not legal advice.</span>
    </div>
  {_body_close()}
</div>"""


# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf(report: ComplianceReport) -> bytes:
    logo = _logo()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:'Inter',Arial,sans-serif;font-size:9.5pt;color:#0f172a;background:#fff;
    -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
  @page{{size:A4;margin:0;}}
</style>
</head>
<body>
{_cover(report, logo)}
{_summary_and_applicability(report, logo)}
{_scores(report, logo)}
{_gaps(report, logo)}
{_actions(report, logo)}
{_closing(report, logo)}
</body></html>"""

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg      = browser.new_page()
        pg.set_viewport_size({"width": 794, "height": 1123})   # A4 at 96dpi
        pg.set_content(html, wait_until="networkidle")
        pdf_bytes = pg.pdf(
            format="A4",
            print_background=True,
            margin={"top":"0","bottom":"0","left":"0","right":"0"},
        )
        browser.close()
    return pdf_bytes
