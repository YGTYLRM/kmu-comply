"""
PDF Report Generator — Complio
Playwright/Chromium renderer. Zero external margin — all spacing in HTML.
"""
from __future__ import annotations
import base64
import logging
import re
import threading
from pathlib import Path

from models.compliance_report import ComplianceReport
from models.enums import ComplianceStatus, Priority

logger = logging.getLogger(__name__)

# Persistent Playwright browser — launched once at startup, reused for all PDF requests.
# A semaphore limits concurrency to avoid overwhelming Chromium under load.
_pw = None
_browser = None
_browser_lock = threading.Lock()

from config import settings as _settings
_pdf_semaphore = threading.Semaphore(getattr(_settings, "pdf_concurrency", 3))


def init_browser() -> None:
    """Pre-launch the Playwright Chromium browser. Called from the app lifespan."""
    global _pw, _browser
    try:
        from playwright.sync_api import sync_playwright
        with _browser_lock:
            if _browser is None:
                _pw = sync_playwright().start()
                _browser = _pw.chromium.launch()
                logger.info("pdf_generator: Playwright browser launched")
    except Exception as exc:
        logger.warning("pdf_generator: could not pre-launch browser (%s) — will cold-start per request", exc)


def close_browser() -> None:
    """Shut down the Playwright browser. Called from the app lifespan on shutdown."""
    global _pw, _browser
    with _browser_lock:
        if _browser:
            try:
                _browser.close()
            except Exception:
                pass
            _browser = None
        if _pw:
            try:
                _pw.stop()
            except Exception:
                pass
            _pw = None
        logger.info("pdf_generator: Playwright browser closed")

LOGO_PATH  = Path(__file__).parent.parent / "assets" / "logo-dark-bg.png"
FONTS_DIR  = Path(__file__).parent.parent / "assets" / "fonts"
_FONT_WEIGHTS = [400, 500, 600, 700, 800, 900]


def _build_font_css() -> str:
    """Build @font-face CSS from local WOFF2 files (no CDN dependency).

    Falls back to a silent empty string if font files haven't been downloaded yet —
    Playwright will then use the browser's default sans-serif font (Arial/Helvetica).
    Run scripts/download_fonts.py once to populate backend/assets/fonts/.
    """
    rules: list[str] = []
    for weight in _FONT_WEIGHTS:
        font_file = FONTS_DIR / f"inter-{weight}-latin.woff2"
        if not font_file.exists():
            return ""  # font files not downloaded — fall back to system font
        b64 = base64.b64encode(font_file.read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:'Inter';font-style:normal;font-weight:{weight};"
            f"font-display:swap;"
            f"src:url('data:font/woff2;base64,{b64}') format('woff2');}}"
        )
    return "\n".join(rules)


_FONT_CSS = _build_font_css()

REGULATION_LABELS: dict[str, str] = {
    "gdpr_dsgvo":    "GDPR / DSGVO",
    "bdsg":          "BDSG",
    "lksg":          "LkSG",
    "enefg":         "EnEfG / EDL-G",
    "csrd":          "CSRD",
    "nis2":          "NIS2",
    "eu_ai_act":     "EU AI Act",
    "hinschg":       "HinSchG",
    "workplace_law": "Employment & Workplace Law",
    "agg":           "AGG",
    "milog":         "MiLoG",
}

STATUS_STYLES: dict[ComplianceStatus, dict[str, str]] = {
    ComplianceStatus.COMPLIANT:           {"c": "#16a34a", "bg": "#f0fdf4", "br": "#bbf7d0", "label": "Compliant"},
    ComplianceStatus.PARTIALLY_COMPLIANT: {"c": "#b45309", "bg": "#fffbeb", "br": "#fde68a", "label": "Partial"},
    ComplianceStatus.NON_COMPLIANT:       {"c": "#dc2626", "bg": "#fef2f2", "br": "#fecaca", "label": "Non-Compliant"},
    ComplianceStatus.CANNOT_ASSESS:       {"c": "#64748b", "bg": "#f8fafc", "br": "#e2e8f0", "label": "Cannot Assess"},
}

PRIORITY_STYLES: dict[Priority, dict[str, str]] = {
    Priority.CRITICAL: {"c": "#dc2626", "bg": "#fef2f2", "br": "#fecaca", "label": "Critical"},
    Priority.HIGH:     {"c": "#ea580c", "bg": "#fff7ed", "br": "#fed7aa", "label": "High"},
    Priority.MEDIUM:   {"c": "#b45309", "bg": "#fffbeb", "br": "#fde68a", "label": "Medium"},
    Priority.LOW:      {"c": "#16a34a", "bg": "#f0fdf4", "br": "#bbf7d0", "label": "Low"},
}


def _reg_label(key: str) -> str:
    return REGULATION_LABELS.get(key, key.upper())


def _score_color(score: float) -> str:
    if score >= 75:
        return "#16a34a"
    if score >= 40:
        return "#b45309"
    return "#dc2626"


def _score_bg(score: float) -> str:
    if score >= 75:
        return "#f0fdf4"
    if score >= 40:
        return "#fffbeb"
    return "#fef2f2"


def _score_border(score: float) -> str:
    if score >= 75:
        return "#bbf7d0"
    if score >= 40:
        return "#fde68a"
    return "#fecaca"


def _esc(text) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _clean(text) -> str:
    """Strip LLM artefacts: field=value patterns and stray dashes."""
    if not text:
        return ""
    text = re.sub(r'\b\w+=(?:true|false|null|\d+(?:\.\d+)?)\b', '', text)
    text = text.replace("—", " ").replace("–", " ").replace("--", " ")
    return re.sub(r"  +", " ", text).strip().lstrip(".,;")


def _logo_data_uri() -> str:
    if LOGO_PATH.exists():
        try:
            return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()
        except (OSError, IOError) as exc:
            logger.warning("pdf: failed to load logo: %s", exc)
    return ""


FONT         = "font-family:'Inter',Arial,sans-serif;"
NAVY         = "#0f172a"
BLUE         = "#2563eb"
PAGE_MARGIN  = "20mm"

# ─────────────────────────────────────────────────────────────────────────────
# Page header bar — dark bar + blue accent line underneath
# ─────────────────────────────────────────────────────────────────────────────

def _hbar(company, section, logo):
    return (
        f'<div>'
        f'<div style="{FONT}background:{NAVY};padding:5mm {PAGE_MARGIN};display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="font-size:9.5pt;font-weight:700;color:#fff;letter-spacing:.1pt;">{_esc(section)}</div>'
        f'<div style="font-size:7pt;color:#475569;font-weight:500;">{_esc(company)}</div>'
        f'</div>'
        f'<div style="height:2.5pt;background:linear-gradient(90deg,{BLUE} 0%,{BLUE} 55%,rgba(37,99,235,0) 100%);"></div>'
        f'</div>'
    )


def _body_open():
    return f'<div style="padding:10mm {PAGE_MARGIN} 12mm;">'

def _body_close():
    return '</div>'


def _sec_title(num, title):
    return (
        f'<div style="display:flex;align-items:center;gap:6pt;margin-bottom:3mm;">'
        f'<span style="display:inline-block;width:18pt;height:2pt;background:{BLUE};border-radius:1pt;flex-shrink:0;"></span>'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;letter-spacing:2.2pt;text-transform:uppercase;color:{BLUE};">{num}</div>'
        f'</div>'
        f'<div style="{FONT}font-size:17pt;font-weight:800;color:{NAVY};letter-spacing:-.3pt;'
        f'line-height:1.1;margin-bottom:2mm;padding-bottom:3mm;border-bottom:2pt solid #f1f5f9;">{title}</div>'
    )


def _sec_sub(text):
    return f'<p style="{FONT}font-size:9pt;color:#64748b;line-height:1.65;margin-bottom:6mm;max-width:170mm;">{text}</p>'


# ─────────────────────────────────────────────────────────────────────────────
# Cover
# ─────────────────────────────────────────────────────────────────────────────

def _cover(report: ComplianceReport, logo: str) -> str:
    sc   = _score_color(report.overall_score_percent)
    date = report.generated_at[:10] if report.generated_at else ""

    n_app  = sum(1 for r in report.applicable_regulations if r.applies)
    n_gaps = len(report.gap_analysis)
    n_act  = len(report.action_plan)
    n_crit = sum(1 for a in report.action_plan if a.priority == Priority.CRITICAL)

    logo_el = (f'<img src="{logo}" style="height:32pt;" alt="Complio">'
               if logo else
               f'<span style="{FONT}font-size:22pt;font-weight:800;color:#fff;">Complio</span>')

    chips = "".join(
        f'<span style="{FONT}font-size:7pt;font-weight:600;color:#93c5fd;'
        f'background:rgba(59,130,246,.12);border:1pt solid rgba(147,197,253,.25);'
        f'border-radius:20pt;padding:2.5pt 10pt;margin:0 2mm 2.5mm 0;display:inline-block;">'
        f'{_esc(_reg_label(r.regulation.value))}</span>'
        for r in report.applicable_regulations if r.applies
    )

    def stat(n, lbl, color="#e2e8f0"):
        return (
            f'<div style="text-align:center;padding:0 7mm;">'
            f'<div style="{FONT}font-size:24pt;font-weight:800;color:{color};line-height:1;letter-spacing:-.5pt;">{n}</div>'
            f'<div style="{FONT}font-size:5.5pt;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.9pt;color:#475569;margin-top:2mm;">{lbl}</div>'
            f'</div>'
        )

    divider = '<div style="width:1pt;height:12mm;background:rgba(255,255,255,0.08);margin:0 1mm;align-self:center;"></div>'

    return (
        f'<div style="width:100%;height:297mm;'
        f'background:linear-gradient(150deg,#020817 0%,#061230 35%,#0c1a45 65%,#0a1540 100%);'
        f'display:flex;flex-direction:column;page-break-after:always;overflow:hidden;position:relative;">'

        f'<div style="position:absolute;left:0;top:38%;width:100mm;height:100mm;border-radius:50%;'
        f'background:radial-gradient(circle,rgba(37,99,235,0.18) 0%,transparent 65%);pointer-events:none;"></div>'
        f'<div style="position:absolute;right:0;top:0;bottom:0;width:1pt;'
        f'background:linear-gradient(180deg,transparent 0%,rgba(37,99,235,0.4) 40%,rgba(37,99,235,0.4) 60%,transparent 100%);"></div>'

        f'<div style="padding:9mm {PAGE_MARGIN} 0;display:flex;align-items:center;justify-content:space-between;position:relative;z-index:1;">'
        f'{logo_el}'
        f'<div style="{FONT}font-size:6.5pt;font-weight:600;letter-spacing:1.8pt;text-transform:uppercase;'
        f'color:#93c5fd;border:1pt solid rgba(147,197,253,.25);padding:3.5pt 10pt;border-radius:20pt;">'
        f'Regulatory Compliance Assessment</div></div>'

        f'<div style="flex:1;padding:10mm {PAGE_MARGIN} 5mm;display:flex;flex-direction:column;justify-content:center;position:relative;z-index:1;">'
        f'<div style="{FONT}font-size:7pt;font-weight:700;letter-spacing:2.2pt;text-transform:uppercase;color:{BLUE};margin-bottom:4mm;">Autonomous AI Compliance Agent</div>'
        f'<div style="{FONT}font-size:34pt;font-weight:800;color:#f8fafc;line-height:1.08;'
        f'letter-spacing:-.8pt;margin-bottom:3mm;max-width:155mm;">{_esc(report.company_name)}</div>'
        f'<div style="{FONT}font-size:8.5pt;color:#475569;margin-bottom:9mm;font-weight:500;">Report issued {_esc(date)}</div>'

        f'<div style="display:flex;align-items:center;gap:0;">'
        f'<div style="position:relative;margin-right:7mm;flex-shrink:0;">'
        f'<div style="width:36mm;height:36mm;border-radius:50%;border:3pt solid {sc};'
        f'background:rgba(15,23,42,0.6);box-shadow:0 0 22pt {sc}55,0 0 6pt {sc}33;'
        f'display:flex;flex-direction:column;align-items:center;justify-content:center;">'
        f'<div style="{FONT}font-size:17pt;font-weight:800;color:{sc};line-height:1;letter-spacing:-.5pt;">'
        f'{report.overall_score_percent:.0f}%</div>'
        f'<div style="{FONT}font-size:5.5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.9pt;color:{sc};opacity:.8;margin-top:2pt;">Score</div>'
        f'</div></div>'
        f'{divider}{stat(n_app,"Regulations")}{divider}{stat(n_gaps,"Gaps")}'
        f'{divider}{stat(n_act,"Actions")}{divider}{stat(n_crit,"Critical","#f87171")}'
        f'</div></div>'

        f'<div style="padding:0 {PAGE_MARGIN} 9mm;position:relative;z-index:1;">'
        f'<div style="height:1pt;background:linear-gradient(90deg,rgba(255,255,255,0.1) 0%,transparent 100%);margin-bottom:5mm;"></div>'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;letter-spacing:1.5pt;text-transform:uppercase;color:#475569;margin-bottom:3.5mm;">Applicable Regulations</div>'
        f'<div style="line-height:1;">{chips}</div>'

        # Completeness warning on cover (only shown when < 70%)
        + (
            f'<div style="margin-top:4mm;padding:4mm 6mm;'
            f'background:rgba(251,146,60,0.10);border:1pt solid rgba(251,146,60,0.30);border-radius:6pt;">'
            f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;letter-spacing:1pt;color:#fb923c;margin-bottom:1.5mm;">'
            f'Low data completeness &nbsp;&mdash;&nbsp; {report.profile_completeness["score_percent"]:.0f}%</div>'
            f'<div style="{FONT}font-size:6.5pt;color:#94a3b8;line-height:1.6;">'
            f'{report.profile_completeness["unanswered_count"]} compliance-relevant fields were not provided. '
            f'Some findings may rely on assumptions. Re-run with a complete profile for higher accuracy.'
            f'</div></div>'
            if (report.profile_completeness and report.profile_completeness.get("score_percent", 100) < 70)
            else ""
        )

        # Legal disclaimer — prominent box on dark cover
        + f'<div style="margin-top:4mm;padding:4mm 6mm;'
        f'background:rgba(245,158,11,0.08);border:1pt solid rgba(245,158,11,0.25);border-radius:6pt;">'
        f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;letter-spacing:1pt;color:#f59e0b;margin-bottom:1.5mm;">'
        f'Preliminary screening only &nbsp;&mdash;&nbsp; Not legal advice</div>'
        f'<div style="{FONT}font-size:6.5pt;color:#94a3b8;line-height:1.6;">'
        f'{_esc(report.disclaimer) if report.disclaimer else "This report is a preliminary AI-generated compliance screening. It does not constitute legal advice and does not replace a qualified legal review. Always consult a licensed attorney before taking compliance decisions."}'
        f'</div></div>'

        f'</div></div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Section 1+2 — Summary and Applicability
# ─────────────────────────────────────────────────────────────────────────────

def _summary_and_applicability(report: ComplianceReport, logo: str) -> str:
    summary = _esc(_clean(report.executive_summary)) or "No executive summary available."

    warns = ""
    if report.validation_warnings:
        items = "".join(f'<li style="margin-bottom:3pt;">{_esc(w)}</li>'
                        for w in report.validation_warnings)
        warns = (
            f'<div style="margin-top:5mm;">'
            f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;letter-spacing:1pt;color:#94a3b8;margin-bottom:2mm;">Warnings</div>'
            f'<ul style="padding-left:14pt;">{items}</ul></div>'
        )

    rows = ""
    for i, r in enumerate(report.applicable_regulations):
        bg = "#fafafa" if i % 2 == 1 else "#fff"
        badge = ("background:#f0fdf4;color:#16a34a;border:1pt solid #bbf7d0;" if r.applies
                 else "background:#f8fafc;color:#64748b;border:1pt solid #e2e8f0;")
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="{FONT}padding:6pt 9pt;font-weight:600;font-size:8.5pt;width:22%;border-bottom:1pt solid #f1f5f9;white-space:nowrap;">{_esc(_reg_label(r.regulation.value))}</td>'
            f'<td style="padding:6pt 9pt;text-align:center;width:12%;border-bottom:1pt solid #f1f5f9;">'
            f'<span style="{FONT}display:inline-block;font-size:7pt;font-weight:700;padding:2pt 8pt;border-radius:20pt;{badge}">{"Yes" if r.applies else "No"}</span>'
            f'</td>'
            f'<td style="{FONT}padding:6pt 9pt;font-size:8.5pt;color:#334155;line-height:1.55;width:66%;border-bottom:1pt solid #f1f5f9;">{_esc(_clean(r.reason))}</td>'
            f'</tr>'
        )

    return (
        f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
        f'{_hbar(report.company_name, "Executive Summary", logo)}'
        f'{_body_open()}'
        f'{_sec_title("Section 01", "Executive Summary")}'
        f'{_sec_sub(summary)}'
        f'{warns}'
        f'<div style="margin-top:8mm;">'
        f'{_sec_title("Section 02", "Regulation Applicability")}'
        f'{_sec_sub("Which regulations apply to your company, based on your size, industry, and how you operate.")}'
        f'<div style="border-radius:8pt;overflow:hidden;box-shadow:0 1pt 6pt rgba(0,0,0,0.06);">'
        f'<table style="width:100%;border-collapse:collapse;table-layout:fixed;word-break:break-word;">'
        f'<thead><tr>'
        f'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7.5pt;font-weight:700;padding:6pt 9pt;text-align:left;width:22%;border-bottom:2pt solid #bfdbfe;">Regulation</th>'
        f'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7.5pt;font-weight:700;padding:6pt 9pt;text-align:center;width:12%;border-bottom:2pt solid #bfdbfe;">Applies</th>'
        f'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7.5pt;font-weight:700;padding:6pt 9pt;text-align:left;width:66%;border-bottom:2pt solid #bfdbfe;">Reason</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'</div>'
        f'{_body_close()}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Scores
# ─────────────────────────────────────────────────────────────────────────────

def _scores(report: ComplianceReport, logo: str) -> str:
    sc  = _score_color(report.overall_score_percent)
    sbg = _score_bg(report.overall_score_percent)
    sbr = _score_border(report.overall_score_percent)
    n_c = sum(rs.compliant for rs in report.regulation_scores)
    n_p = sum(rs.partially_compliant for rs in report.regulation_scores)
    n_n = sum(rs.non_compliant for rs in report.regulation_scores)
    n_t = sum(rs.total_requirements for rs in report.regulation_scores)

    def sbox(n, lbl, c):
        return (
            f'<td style="width:25%;padding:0 2mm;">'
            f'<div style="{FONT}border:1pt solid #e2e8f0;border-radius:8pt;padding:4.5mm;text-align:center;'
            f'background:#fafafa;box-shadow:0 1pt 4pt rgba(0,0,0,0.05);">'
            f'<div style="font-size:20pt;font-weight:800;color:{c};line-height:1;margin-bottom:1.5mm;">{n}</div>'
            f'<div style="font-size:6.5pt;font-weight:600;text-transform:uppercase;letter-spacing:.8pt;color:#94a3b8;">{lbl}</div>'
            f'</div></td>'
        )

    rows = ""
    for i, rs in enumerate(report.regulation_scores):
        bc  = _score_color(rs.score_percent)
        bw  = min(100.0, max(0.0, rs.score_percent))
        bg  = "#fafafa" if i % 2 == 1 else "#fff"
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="{FONT}padding:6pt 8pt;font-weight:600;font-size:8.5pt;width:28%;">{_esc(_reg_label(rs.regulation.value))}</td>'
            f'<td style="{FONT}padding:6pt 8pt;text-align:center;font-weight:800;font-size:10pt;color:{bc};width:10%;">{rs.score_percent:.0f}%</td>'
            f'<td style="padding:6pt 8pt;width:38%;">'
            f'<div style="height:8pt;background:#f1f5f9;border-radius:10pt;overflow:hidden;">'
            f'<div style="height:8pt;width:{bw}%;background:linear-gradient(90deg,{bc}cc,{bc});border-radius:10pt;"></div>'
            f'</div></td>'
            f'<td style="{FONT}padding:6pt 8pt;text-align:center;color:#16a34a;font-weight:600;font-size:8.5pt;width:8%;">{rs.compliant}</td>'
            f'<td style="{FONT}padding:6pt 8pt;text-align:center;color:#b45309;font-weight:600;font-size:8.5pt;width:8%;">{rs.partially_compliant}</td>'
            f'<td style="{FONT}padding:6pt 8pt;text-align:center;color:#dc2626;font-weight:600;font-size:8.5pt;width:8%;">{rs.non_compliant}</td>'
            f'</tr>'
        )

    return (
        f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
        f'{_hbar(report.company_name, "Score Breakdown", logo)}'
        f'{_body_open()}'
        f'{_sec_title("Section 03", "Score Breakdown")}'
        f'<div style="background:{sbg};border:1.5pt solid {sbr};border-radius:10pt;'
        f'padding:7mm 9mm;margin-bottom:6mm;display:flex;align-items:center;gap:9mm;'
        f'box-shadow:0 2pt 10pt rgba(0,0,0,0.06);">'
        f'<div style="width:38mm;height:38mm;border-radius:50%;border:3pt solid {sc};'
        f'background:rgba(255,255,255,0.6);box-shadow:0 0 14pt {sc}33;'
        f'display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;">'
        f'<div style="{FONT}font-size:20pt;font-weight:800;color:{sc};letter-spacing:-1pt;line-height:1;">{report.overall_score_percent:.1f}%</div>'
        f'<div style="{FONT}font-size:5.5pt;font-weight:700;text-transform:uppercase;letter-spacing:.9pt;color:{sc};opacity:.8;margin-top:2pt;">Score</div>'
        f'</div>'
        f'<div>'
        f'<div style="{FONT}font-size:11pt;font-weight:700;color:{NAVY};margin-bottom:2.5mm;">Overall Compliance Score</div>'
        f'<div style="{FONT}font-size:8pt;color:#64748b;line-height:1.7;">'
        f'{len(report.regulation_scores)} regulations checked &nbsp;&middot;&nbsp; '
        f'{n_t} requirements assessed &nbsp;&middot;&nbsp; '
        f'{len(report.gap_analysis)} gaps found</div>'
        f'</div></div>'
        f'<table style="width:100%;border-collapse:collapse;margin-bottom:6mm;table-layout:fixed;">'
        f'<tr>{sbox(n_c,"Compliant","#16a34a")}{sbox(n_p,"Partial","#b45309")}{sbox(n_n,"Non-Compliant","#dc2626")}{sbox(n_t,"Total Checked",NAVY)}</tr>'
        f'</table>'
        f'<div style="border-radius:8pt;overflow:hidden;box-shadow:0 1pt 6pt rgba(0,0,0,0.06);">'
        f'<table style="width:100%;border-collapse:collapse;table-layout:fixed;word-break:break-word;">'
        f'<thead><tr>'
        f'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7pt;font-weight:700;text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;text-align:left;width:28%;border-bottom:2pt solid #bfdbfe;">Regulation</th>'
        f'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7pt;font-weight:700;text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;text-align:center;width:10%;border-bottom:2pt solid #bfdbfe;">Score</th>'
        f'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7pt;font-weight:700;text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;width:38%;border-bottom:2pt solid #bfdbfe;">Progress</th>'
        f'<th style="{FONT}background:#dbeafe;color:#16a34a;font-size:7pt;font-weight:700;padding:5pt 8pt;text-align:center;width:8%;border-bottom:2pt solid #bfdbfe;">C</th>'
        f'<th style="{FONT}background:#dbeafe;color:#b45309;font-size:7pt;font-weight:700;padding:5pt 8pt;text-align:center;width:8%;border-bottom:2pt solid #bfdbfe;">P</th>'
        f'<th style="{FONT}background:#dbeafe;color:#dc2626;font-size:7pt;font-weight:700;padding:5pt 8pt;text-align:center;width:8%;border-bottom:2pt solid #bfdbfe;">NC</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'<div style="{FONT}font-size:7pt;color:#94a3b8;margin-top:3mm;">C = Compliant &nbsp;&nbsp; P = Partially Compliant &nbsp;&nbsp; NC = Non-Compliant</div>'
        f'{_body_close()}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Gap Analysis (continuous flow, no per-regulation page breaks)
# ─────────────────────────────────────────────────────────────────────────────

def _gap_card(g) -> str:
    cm    = STATUS_STYLES.get(g.status, STATUS_STYLES[ComplianceStatus.CANNOT_ASSESS])
    ev    = _esc(_clean(g.evidence))
    defic = _esc(_clean(g.deficiency_description))
    art_n = _esc(_clean(g.article_number))
    art_t = _esc(_clean(g.article_title))

    fix = ""
    if defic:
        fix = (
            f'<div style="margin-top:6pt;padding:6pt 9pt;'
            f'border-left:3.5pt solid #dc2626;background:#fef2f2;border-radius:0 5pt 5pt 0;">'
            f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1.1pt;color:#dc2626;margin-bottom:2.5pt;">What needs to change</div>'
            f'<div style="{FONT}font-size:8.5pt;color:#7f1d1d;line-height:1.65;">{defic}</div>'
            f'</div>'
        )

    conf = getattr(g, "confidence", "HIGH")
    conf_reason = getattr(g, "confidence_reason", None)
    conf_style = ""
    if conf == "MEDIUM":
        conf_style = "background:#fffbeb;color:#b45309;border:1pt solid #fde68a;"
    elif conf == "LOW":
        conf_style = "background:#fff7ed;color:#c2410c;border:1pt solid #fed7aa;"

    conf_badge = ""
    if conf in ("MEDIUM", "LOW"):
        conf_badge = (
            f'<span style="{FONT}display:inline-block;font-size:6.5pt;font-weight:700;'
            f'padding:2pt 7pt;border-radius:20pt;{conf_style}margin-right:4pt;">'
            f'{_esc(conf)} confidence</span>'
        )

    return (
        f'<div style="border:1pt solid #e8edf2;border-radius:8pt;'
        f'margin-bottom:8mm;overflow:hidden;page-break-inside:avoid;'
        f'box-shadow:0 1pt 6pt rgba(0,0,0,0.07);">'
        f'<div style="display:flex;align-items:stretch;background:#f1f5f9;border-bottom:1pt solid #e8edf2;">'
        f'<div style="width:5pt;background:{cm["c"]};flex-shrink:0;"></div>'
        f'<div style="flex:1;padding:5.5pt 10pt;display:flex;align-items:center;justify-content:space-between;gap:8pt;">'
        f'<div>'
        f'<div style="{FONT}font-size:8.5pt;font-weight:700;color:{NAVY};">Art.&nbsp;{art_n} &nbsp;&middot;&nbsp; {art_t}</div>'
        + (f'<div style="{FONT}font-size:6.5pt;color:#94a3b8;margin-top:1.5pt;font-style:italic;">{_esc(conf_reason)}</div>' if conf_reason and conf != "HIGH" else "")
        + f'</div>'
        f'<div style="display:flex;align-items:center;gap:4pt;flex-shrink:0;">'
        f'{conf_badge}'
        f'<div style="{FONT}display:inline-flex;align-items:center;gap:4pt;font-size:7pt;font-weight:700;'
        f'padding:3pt 9pt;border-radius:20pt;border:1pt solid {cm["br"]};'
        f'background:{cm["bg"]};color:{cm["c"]};white-space:nowrap;">'
        f'<span style="width:5pt;height:5pt;border-radius:50%;background:{cm["c"]};display:inline-block;"></span>'
        f'{_esc(cm["label"])}</div>'
        f'</div>'
        f'</div></div>'
        f'<div style="padding:7pt 10pt 8pt 14pt;background:#fff;">'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:#94a3b8;margin-bottom:2.5pt;">Assessment</div>'
        f'<div style="{FONT}font-size:8.5pt;color:#334155;line-height:1.65;">{ev}</div>'
        f'{fix}</div></div>'
    )


def _reg_header(reg_key, gaps, first=False):
    n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
    n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
    n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
    return (
        f'<div style="margin-bottom:4mm;display:flex;align-items:baseline;'
        f'justify-content:space-between;padding-bottom:3mm;border-bottom:1.5pt solid #e8edf2;">'
        f'<div style="{FONT}font-size:10pt;font-weight:700;color:{BLUE};">{_esc(_reg_label(reg_key))}</div>'
        f'<div style="{FONT}font-size:7pt;color:#94a3b8;">'
        f'{n_c} compliant &nbsp;&middot;&nbsp; {n_p} partial &nbsp;&middot;&nbsp; {n_n} non-compliant'
        f'</div></div>'
    )


def _gaps(report: ComplianceReport, logo: str) -> str:
    if not report.gap_analysis:
        return (
            f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
            f'{_hbar(report.company_name, "Gap Analysis", logo)}'
            f'{_body_open()}{_sec_title("Section 04","Gap Analysis")}<p>No gaps found.</p>{_body_close()}'
            f'</div>'
        )

    by_reg: dict[str, list] = {}
    for g in report.gap_analysis:
        by_reg.setdefault(g.regulation.value, []).append(g)

    body = ""
    for i, (reg_key, gaps) in enumerate(by_reg.items()):
        spacer = "" if i == 0 else '<div style="height:12mm;"></div>'
        header = _reg_header(reg_key, gaps, first=(i == 0))
        cards = [_gap_card(g) for g in gaps]
        if cards:
            body += f'<div style="page-break-inside:avoid;">{spacer}{header}{cards[0]}</div>'
            body += "".join(cards[1:])
        else:
            body += spacer + header

    return (
        f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
        f'{_hbar(report.company_name, "Gap Analysis", logo)}'
        f'{_body_open()}'
        f'{_sec_title("Section 04", "Gap Analysis")}'
        f'{_sec_sub("Every requirement we checked, grouped by regulation. Exactly why each one passed or failed, and what needs to change.")}'
        f'{body}'
        f'{_body_close()}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Action Plan (continuous flow, no per-regulation page breaks)
# ─────────────────────────────────────────────────────────────────────────────

def _action_card(a) -> str:
    pm  = PRIORITY_STYLES.get(a.priority, PRIORITY_STYLES[Priority.LOW])
    dl  = f"&nbsp;&nbsp;<b style='color:#374151;'>Deadline:</b> {_esc(_clean(a.deadline))}" if a.deadline else ""
    return (
        f'<div style="border:1pt solid #e8edf2;border-radius:8pt;'
        f'margin-bottom:8mm;overflow:hidden;page-break-inside:avoid;'
        f'box-shadow:0 1pt 6pt rgba(0,0,0,0.07);">'
        f'<div style="display:flex;align-items:center;gap:8pt;padding:5.5pt 10pt;'
        f'background:#f1f5f9;border-bottom:1pt solid #e8edf2;">'
        f'<span style="{FONT}display:inline-block;font-size:7pt;font-weight:700;'
        f'padding:2.5pt 9pt;border-radius:20pt;border:1pt solid {pm["br"]};'
        f'background:{pm["bg"]};color:{pm["c"]};flex-shrink:0;">{_esc(pm["label"])}</span>'
        f'<span style="{FONT}font-size:8.5pt;font-weight:700;color:{NAVY};">Art.&nbsp;{_esc(_clean(a.article_number))}</span>'
        f'<span style="{FONT}font-size:7pt;color:#94a3b8;margin-left:auto;">{_esc(_reg_label(a.regulation.value))}</span>'
        f'</div>'
        f'<div style="padding:7pt 10pt 8pt;background:#fff;">'
        f'<div style="{FONT}font-size:8.5pt;color:#1a202c;line-height:1.65;margin-bottom:4.5pt;">{_esc(_clean(a.action))}</div>'
        f'<div style="{FONT}font-size:7.5pt;color:#64748b;">'
        f'<b style="color:#374151;">Effort:</b> {_esc(_clean(a.estimated_effort))}{dl}'
        f'</div></div></div>'
    )


def _actions(report: ComplianceReport, logo: str) -> str:
    if not report.action_plan:
        return (
            f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
            f'{_hbar(report.company_name, "Action Plan", logo)}'
            f'{_body_open()}{_sec_title("Section 05","Action Plan")}<p>No actions required.</p>{_body_close()}'
            f'</div>'
        )

    by_reg: dict[str, list] = {}
    for a in report.action_plan:
        by_reg.setdefault(a.regulation.value, []).append(a)

    body = ""
    for i, (reg_key, acts) in enumerate(by_reg.items()):
        spacer = "" if i == 0 else '<div style="height:12mm;"></div>'
        header = (
            f'<div style="margin-bottom:4mm;display:flex;align-items:baseline;'
            f'justify-content:space-between;padding-bottom:3mm;border-bottom:1.5pt solid #e8edf2;">'
            f'<div style="{FONT}font-size:10pt;font-weight:700;color:{BLUE};">{_esc(_reg_label(reg_key))}</div>'
            f'</div>'
        )
        cards = [_action_card(a) for a in acts]
        if cards:
            body += f'<div style="page-break-inside:avoid;">{spacer}{header}{cards[0]}</div>'
            body += "".join(cards[1:])
        else:
            body += spacer + header

    return (
        f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
        f'{_hbar(report.company_name, "Action Plan", logo)}'
        f'{_body_open()}'
        f'{_sec_title("Section 05", "Action Plan")}'
        f'{_sec_sub("A concrete to-do list for closing your compliance gaps. Start with Critical and High items.")}'
        f'{body}'
        f'{_body_close()}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge base audit trail
# ─────────────────────────────────────────────────────────────────────────────

_REG_DISPLAY: dict[str, str] = {
    "gdpr_dsgvo":    "GDPR / DSGVO",
    "bdsg":          "BDSG",
    "nis2":          "NIS2",
    "eu_ai_act":     "EU AI Act",
    "hinschg":       "HinSchG",
    "workplace_law": "ArbSchG / Employment Law",
    "agg":           "AGG",
    "milog":         "MiLoG",
    "lksg":          "LkSG",
    "enefg":         "EnEfG",
    "csrd":          "CSRD",
    "ttdsg":         "TTDSG / TDDDG",
    "gwg":           "GwG",
    "eu_data_act":   "EU Data Act",
}


def _kb_versions_table(report: ComplianceReport) -> str:
    """Render a compact audit-trail table showing which KB version each finding used,
    with Rule Engine Version and Prompt Version rows at the top."""
    versions = report.knowledge_base_versions or {}

    # Version rows at the top (Rule Engine + Prompt)
    engine_ver = _esc(report.rule_engine_version or "—")
    prompt_ver = _esc(report.prompt_version or "—")
    version_rows = (
        f'<tr style="border-bottom:0.5pt solid #f1f5f9;background:#f0f9ff;">'
        f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;font-weight:700;color:#0369a1;">Rule Engine Version</td>'
        f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;color:#0369a1;font-family:monospace;" colspan="3">{engine_ver}</td>'
        f'</tr>'
        f'<tr style="border-bottom:0.5pt solid #f1f5f9;background:#f0f9ff;">'
        f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;font-weight:700;color:#0369a1;">Prompt Version</td>'
        f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;color:#0369a1;font-family:monospace;" colspan="3">{prompt_ver}</td>'
        f'</tr>'
    )

    kb_rows = ""
    for reg_key, meta in sorted(versions.items()):
        fetched = meta.get("fetched_at", "unknown")[:10]  # date part only
        src_hash = meta.get("source_file_hash", "")
        hash_short = src_hash[:12] if src_hash and src_hash != "unknown" else "—"
        src_url = meta.get("source_url", "")
        label = _REG_DISPLAY.get(reg_key, reg_key.upper())
        url_html = (
            f'<a href="{_esc(src_url)}" style="color:{BLUE};text-decoration:none;">'
            f'official text</a>'
            if src_url else "—"
        )
        kb_rows += (
            f'<tr style="border-bottom:0.5pt solid #f1f5f9;">'
            f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;font-weight:600;color:#334155;">{_esc(label)}</td>'
            f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;color:#64748b;font-family:monospace;">{_esc(fetched)}</td>'
            f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;color:#94a3b8;font-family:monospace;">{_esc(hash_short)}</td>'
            f'<td style="padding:2.5mm 3mm;{FONT}font-size:7.5pt;">{url_html}</td>'
            f'</tr>'
        )

    all_rows = version_rows + kb_rows

    return (
        f'<div style="margin-top:8mm;">'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:#94a3b8;margin-bottom:2.5mm;">Knowledge Base Audit Trail</div>'
        f'<table style="width:100%;border-collapse:collapse;border:1pt solid #e8edf2;border-radius:6pt;overflow:hidden;">'
        f'<thead><tr style="background:#f8fafc;">'
        f'<th style="padding:2.5mm 3mm;{FONT}font-size:7pt;font-weight:600;color:#64748b;text-align:left;">Component / Regulation</th>'
        f'<th style="padding:2.5mm 3mm;{FONT}font-size:7pt;font-weight:600;color:#64748b;text-align:left;">Ingested / Version</th>'
        f'<th style="padding:2.5mm 3mm;{FONT}font-size:7pt;font-weight:600;color:#64748b;text-align:left;">Source Hash</th>'
        f'<th style="padding:2.5mm 3mm;{FONT}font-size:7pt;font-weight:600;color:#64748b;text-align:left;">Source</th>'
        f'</tr></thead>'
        f'<tbody>{all_rows}</tbody>'
        f'</table>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Input Assumptions box
# ─────────────────────────────────────────────────────────────────────────────

def _input_assumptions(report: ComplianceReport) -> str:
    """Render a box listing the key profile fields used in the assessment."""
    # Extract applicable_regulations list — the profile fields are embedded in the report
    # We reconstruct key fields from what's stored on the report itself.
    regs = report.applicable_regulations or []
    applicable_reg_names = [
        r.regulation.value for r in regs if r.applies
    ]

    def _val(v: object) -> str:
        if v is None:
            return '<em style="color:#94a3b8;">Not provided</em>'
        if isinstance(v, bool):
            return "Yes" if v else "No"
        return _esc(str(v))

    # We can only access what's on the report; the raw profile fields are not
    # stored on ComplianceReport. We show what we know: company name, applicable regs.
    # For richer assumptions the caller can pass extra context. Here we show
    # the inferred_characteristics and inferred_assumptions that are stored.
    chars = report.inferred_characteristics or []
    assumptions = report.inferred_assumptions or []

    char_rows = "".join(
        f'<li style="{FONT}font-size:8pt;color:#334155;margin-bottom:1.5mm;">{_esc(c)}</li>'
        for c in chars
    ) if chars else f'<li style="{FONT}font-size:8pt;color:#94a3b8;font-style:italic;">None recorded</li>'

    assumption_rows = "".join(
        f'<li style="{FONT}font-size:8pt;color:#334155;margin-bottom:1.5mm;">{_esc(a)}</li>'
        for a in assumptions
    ) if assumptions else ""

    reg_list = ", ".join(r.upper() for r in applicable_reg_names) or "None determined"

    html = (
        f'<div style="margin-top:8mm;padding:5mm 6mm;background:#fafafa;border:1pt solid #e8edf2;'
        f'border-radius:8pt;box-shadow:0 1pt 4pt rgba(0,0,0,0.04);">'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:#94a3b8;margin-bottom:3mm;">Input Assumptions Used in This Assessment</div>'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<tr><td style="{FONT}font-size:8pt;font-weight:600;color:#64748b;padding:1.5mm 0;width:45%;">Company</td>'
        f'<td style="{FONT}font-size:8pt;color:#334155;padding:1.5mm 0;">{_esc(report.company_name)}</td></tr>'
        f'<tr><td style="{FONT}font-size:8pt;font-weight:600;color:#64748b;padding:1.5mm 0;">Applicable Regulations</td>'
        f'<td style="{FONT}font-size:8pt;color:#334155;padding:1.5mm 0;">{_esc(reg_list)}</td></tr>'
        f'</table>'
        f'<div style="{FONT}font-size:7.5pt;font-weight:600;color:#64748b;margin-top:3mm;margin-bottom:1.5mm;">Inferred Characteristics</div>'
        f'<ul style="margin:0;padding-left:4mm;">{char_rows}</ul>'
    )
    if assumption_rows:
        html += (
            f'<div style="{FONT}font-size:7.5pt;font-weight:600;color:#e67e22;margin-top:3mm;margin-bottom:1.5mm;">'
            f'Inferred Assumptions (not confirmed by user — verify before acting)</div>'
            f'<ul style="margin:0;padding-left:4mm;">{assumption_rows}</ul>'
        )
    html += '</div>'
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
    items = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:8pt;margin-bottom:5mm;">'
        f'<div style="{FONT}width:18pt;height:18pt;border-radius:50%;background:{NAVY};'
        f'color:#fff;font-size:7.5pt;font-weight:700;display:flex;align-items:center;'
        f'justify-content:center;flex-shrink:0;margin-top:1pt;">{i+1}</div>'
        f'<div style="{FONT}font-size:9pt;color:#334155;line-height:1.65;flex:1;">{s}</div>'
        f'</div>'
        for i, s in enumerate(steps)
    )
    return (
        f'<div style="page-break-before:always;border-left:3.5pt solid {BLUE};">'
        f'{_hbar(report.company_name, "Next Steps", logo)}'
        f'{_body_open()}'
        f'{_sec_title("Section 06", "Next Steps")}'
        f'{_sec_sub("You know where you stand now. Here is what to do next.")}'
        f'<div style="margin-top:2mm;">{items}</div>'
        + _input_assumptions(report)
        + f'<div style="margin-top:8mm;">'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;letter-spacing:1pt;color:#94a3b8;margin-bottom:2.5mm;">Legal Disclaimer</div>'
        f'<div style="{FONT}padding:6mm 7mm;background:#f8fafc;border:1pt solid #e8edf2;'
        f'border-radius:8pt;font-size:8pt;color:#64748b;line-height:1.75;font-style:italic;'
        f'box-shadow:0 1pt 4pt rgba(0,0,0,0.04);">{_esc(report.disclaimer)}</div>'
        f'</div>'
        + _kb_versions_table(report)
        + f'<div style="margin-top:8mm;padding-top:5mm;border-top:1pt solid #f1f5f9;'
        f'text-align:center;{FONT}font-size:7.5pt;color:#94a3b8;">'
        f'<strong style="color:{NAVY};">Complio</strong> &nbsp;&middot;&nbsp; Autonomous Regulatory Compliance for German SMEs<br>'
        f'<span style="font-size:7pt;">Produced by an AI agent. Not a certified legal audit. Not legal advice.</span>'
        f'</div>'
        f'{_body_close()}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf(report: ComplianceReport) -> bytes:
    logo = _logo_data_uri()

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        f'<style>{_FONT_CSS}'
        '*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}'
        "body{font-family:'Inter',Arial,sans-serif;font-size:9.5pt;color:#0f172a;background:#fff;"
        '-webkit-print-color-adjust:exact;print-color-adjust:exact;}'
        '@page{size:A4;margin:0;}'
        '</style></head><body>'
        + _cover(report, logo)
        + _summary_and_applicability(report, logo)
        + _scores(report, logo)
        + _gaps(report, logo)
        + _actions(report, logo)
        + _closing(report, logo)
        + '</body></html>'
    )

    with _pdf_semaphore:
        browser = _browser
        if browser is None:
            # Fallback: cold-start if init_browser() was never called or failed
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                cold_browser = pw.chromium.launch()
                pg = cold_browser.new_page()
                pg.set_default_timeout(30_000)
                pg.route("**/*", lambda route: route.abort())
                pg.set_viewport_size({"width": 794, "height": 1123})
                pg.set_content(html, wait_until="load", timeout=30_000)
                pdf_bytes = pg.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
                cold_browser.close()
            return pdf_bytes

        pg = browser.new_page()
        try:
            pg.set_default_timeout(30_000)
            # Block all network requests — the PDF is self-contained (fonts/images as data URIs)
            pg.route("**/*", lambda route: route.abort())
            pg.set_viewport_size({"width": 794, "height": 1123})
            pg.set_content(html, wait_until="load", timeout=30_000)
            return pg.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            pg.close()
