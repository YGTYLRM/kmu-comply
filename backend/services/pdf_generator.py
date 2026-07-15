"""
PDF Report Generator — Complio
Playwright/Chromium renderer. Self-contained HTML (no external dependencies).
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

_pw = None
_browser = None
_browser_lock = threading.Lock()

from config import settings as _settings  # noqa: E402
_pdf_semaphore = threading.Semaphore(getattr(_settings, "pdf_concurrency", 2))


def init_browser() -> None:
    global _pw, _browser
    try:
        from playwright.sync_api import sync_playwright
        with _browser_lock:
            if _browser is None:
                _pw = sync_playwright().start()
                _browser = _pw.chromium.launch()
                logger.info("pdf_generator: Playwright browser launched")
    except Exception as exc:
        logger.warning("pdf_generator: could not pre-launch browser (%s) -- will cold-start per request", exc)


def close_browser() -> None:
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
    rules: list[str] = []
    for weight in _FONT_WEIGHTS:
        font_file = FONTS_DIR / f"inter-{weight}-latin.woff2"
        if not font_file.exists():
            return ""
        b64 = base64.b64encode(font_file.read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:'Inter';font-style:normal;font-weight:{weight};"
            f"font-display:swap;"
            f"src:url('data:font/woff2;base64,{b64}') format('woff2');}}"
        )
    return "\n".join(rules)


_FONT_CSS = _build_font_css()

# ─── Design tokens ─────────────────────────────────────────────────────────────
# Professional document-grade palette
FONT       = "font-family:'Inter','Segoe UI',Calibri,Arial,Helvetica,sans-serif;"
NAVY       = "#1e293b"
BLUE       = "#1d4ed8"
BLUE_LIGHT = "#eff6ff"
BORDER     = "#e2e8f0"
TEXT       = "#1e293b"
MUTED      = "#64748b"
PAGE_PAD   = "20mm"

REGULATION_LABELS: dict[str, str] = {
    "gdpr_dsgvo":    "GDPR / DSGVO",
    "bdsg":          "BDSG",
    "lksg":          "LkSG",
    "enefg":         "EnEfG / EDL-G",
    "csrd":          "CSRD",
    "nis2":          "NIS2",
    "eu_ai_act":     "EU AI Act",
    "hinschg":       "HinSchG",
    "workplace_law": "Arbeitsrecht",
    "agg":           "AGG",
    "milog":         "MiLoG",
    "ttdsg":         "TTDSG / TDDDG",
    "gwg":           "GwG",
    "eu_data_act":   "EU Data Act",
}

_REG_DISPLAY: dict[str, str] = REGULATION_LABELS

STATUS_STYLES: dict[ComplianceStatus, dict[str, str]] = {
    ComplianceStatus.COMPLIANT:           {"c": "#15803d", "bg": "#f0fdf4", "br": "#bbf7d0", "label": "Konform"},
    ComplianceStatus.PARTIALLY_COMPLIANT: {"c": "#a16207", "bg": "#fefce8", "br": "#fef08a", "label": "Teilweise"},
    ComplianceStatus.NON_COMPLIANT:       {"c": "#b91c1c", "bg": "#fef2f2", "br": "#fecaca", "label": "Nicht konform"},
    ComplianceStatus.CANNOT_ASSESS:       {"c": "#475569", "bg": "#f8fafc", "br": "#e2e8f0", "label": "Nicht bewertbar"},
}

PRIORITY_STYLES: dict[Priority, dict[str, str]] = {
    Priority.CRITICAL: {"c": "#b91c1c", "bg": "#fef2f2", "br": "#fecaca", "label": "Kritisch"},
    Priority.HIGH:     {"c": "#c2410c", "bg": "#fff7ed", "br": "#fed7aa", "label": "Hoch"},
    Priority.MEDIUM:   {"c": "#a16207", "bg": "#fefce8", "br": "#fef08a", "label": "Mittel"},
    Priority.LOW:      {"c": "#15803d", "bg": "#f0fdf4", "br": "#bbf7d0", "label": "Niedrig"},
}


def _reg_label(key: str) -> str:
    return REGULATION_LABELS.get(key, key.upper())


def _score_color(score: float) -> str:
    if score >= 75:
        return "#15803d"
    if score >= 40:
        return "#a16207"
    return "#b91c1c"


def _score_bg(score: float) -> str:
    if score >= 75:
        return "#f0fdf4"
    if score >= 40:
        return "#fefce8"
    return "#fef2f2"


def _score_border(score: float) -> str:
    if score >= 75:
        return "#bbf7d0"
    if score >= 40:
        return "#fef08a"
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
    """Strip LLM artefacts: field=value patterns, em/en dashes, repeated punctuation."""
    if not text:
        return ""
    text = re.sub(r'\b\w+=(?:true|false|null|\d+(?:\.\d+)?)\b', '', text)
    text = text.replace("—", " - ").replace("–", " - ").replace("--", " - ")
    # Collapse " - - " artifacts left by replacing multiple dashes
    text = re.sub(r'(\s*-\s*){2,}', ' - ', text)
    return re.sub(r"  +", " ", text).strip().lstrip(".,;")


def _clean_warning(w: str) -> tuple[str, str]:
    """Strip technical prefixes from validation warnings.
    Returns (category, cleaned_text). Category: 'critical' | 'warning' | 'note'."""
    w = w.strip()
    cat = "note"
    critical_prefixes = ["KRITISCHER WIDERSPRUCH:", "CRITICAL CONFLICT:", "KRITISCH:"]
    warning_prefixes = ["WARNING:", "WARNUNG:", "WARN:"]
    note_prefixes = ["HINWEIS:", "NOTE:", "INFO:"]
    for p in critical_prefixes:
        if w.upper().startswith(p.upper()):
            w = w[len(p):].strip(" -:")
            cat = "critical"
            break
    if cat == "note":
        for p in warning_prefixes:
            if w.upper().startswith(p.upper()):
                w = w[len(p):].strip(" -:")
                cat = "warning"
                break
    if cat == "note":
        for p in note_prefixes:
            if w.upper().startswith(p.upper()):
                w = w[len(p):].strip(" -:")
                break
    # Remove internal field-name references (snake_case like has_cookie_banner, transfers_data_outside_eea)
    w = re.sub(r"'[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?::\s*[^\s']+)?'", "", w)  # 'field_name' or 'field_name: value'
    w = re.sub(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+){2,}\b", "", w)              # bare snake_case
    # Clean up orphaned connectors/commas left after removal (e.g. "und  sind", "' und '", ", sind")
    w = re.sub(r"'\s*'", "", w)
    w = re.sub(r"\s*,\s*(?=(?:und|oder|sowie|sind|ist|fehlt|nicht)\b)", " ", w)
    w = re.sub(r",\s*,", ",", w)
    # Loop to collapse chains of 2+ connectors (single-pass re.sub only merges adjacent pairs,
    # leaving e.g. "und oder sowie sind" -> "oder sind" with one orphan behind)
    prev = None
    while prev != w:
        prev = w
        w = re.sub(r"\b(und|oder|sowie)\s+(und|oder|sowie|sind|ist|fehlt|nicht)\b", r"\2", w)
    w = re.sub(r"\s*(und|oder)\s*$", "", w)
    w = re.sub(r"  +", " ", w).strip(" -:'\"")
    return cat, w


def _logo_data_uri() -> str:
    if LOGO_PATH.exists():
        try:
            return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()
        except (OSError, IOError) as exc:
            logger.warning("pdf: failed to load logo: %s", exc)
    return ""


# ─── Layout helpers ────────────────────────────────────────────────────────────

def _section_header(company: str, section: str) -> str:
    """No running header — clean document pages."""
    return ""


def _body_open() -> str:
    # No top padding — @page margin:14mm handles the top spacing on all non-cover pages
    return f'<div style="padding:2mm {PAGE_PAD} 10mm;">'


def _body_close() -> str:
    return '</div>'


def _sec_title(num: str, title: str) -> str:
    return (
        f'<div style="margin-bottom:4mm;">'
        f'<div style="{FONT}font-size:6pt;font-weight:700;letter-spacing:2.5pt;'
        f'text-transform:uppercase;color:{BLUE};margin-bottom:2mm;">{_esc(num)}</div>'
        f'<div style="{FONT}font-size:18pt;font-weight:800;color:{NAVY};'
        f'letter-spacing:-0.4pt;line-height:1.1;padding-bottom:3mm;'
        f'border-bottom:2pt solid {BORDER};">{_esc(title)}</div>'
        f'</div>'
    )


def _sec_sub(text: str) -> str:
    return (
        f'<p style="{FONT}font-size:9pt;color:{MUTED};line-height:1.65;'
        f'margin-bottom:4mm;max-width:170mm;">{_esc(text)}</p>'
    )


def _divider() -> str:
    return f'<div style="height:1pt;background:{BORDER};margin:6mm 0;"></div>'


# ─── Cover page ───────────────────────────────────────────────────────────────

def _cover(report: ComplianceReport, logo: str) -> str:
    sc   = _score_color(report.overall_score_percent)
    date = report.generated_at[:10] if report.generated_at else ""

    n_app  = sum(1 for r in report.applicable_regulations if r.applies)
    n_gaps = len(report.gap_analysis)
    n_act  = len(report.action_plan)
    n_crit = sum(1 for a in report.action_plan if a.priority == Priority.CRITICAL)

    logo_el = (
        f'<img src="{logo}" style="height:28pt;" alt="Complio">'
        if logo else
        f'<span style="{FONT}font-size:20pt;font-weight:800;color:#fff;">Complio</span>'
    )

    chips = "".join(
        f'<span style="{FONT}font-size:7pt;font-weight:600;color:#93c5fd;'
        f'background:rgba(59,130,246,0.12);border:1pt solid rgba(147,197,253,0.25);'
        f'border-radius:20pt;padding:2.5pt 9pt;margin:0 2mm 2.5mm 0;display:inline-block;">'
        f'{_esc(_reg_label(r.regulation.value))}</span>'
        for r in report.applicable_regulations if r.applies
    )

    def stat(n, lbl, color="#e2e8f0"):
        return (
            f'<div style="text-align:center;padding:0 6mm;">'
            f'<div style="{FONT}font-size:22pt;font-weight:800;color:{color};line-height:1;">{n}</div>'
            f'<div style="{FONT}font-size:5.5pt;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1pt;color:#475569;margin-top:2mm;">{lbl}</div>'
            f'</div>'
        )

    vdivider = '<div style="width:1pt;height:11mm;background:rgba(255,255,255,0.1);align-self:center;"></div>'

    low_completeness = (
        report.profile_completeness
        and report.profile_completeness.get("score_percent", 100) < 70
    )

    return (
        f'<div style="width:100%;min-height:297mm;'
        f'background:linear-gradient(150deg,#020817 0%,#061230 40%,#0c1a45 100%);'
        f'display:flex;flex-direction:column;page-break-after:always;overflow:hidden;position:relative;">'

        # Subtle glow orb
        f'<div style="position:absolute;left:-20mm;top:35%;width:90mm;height:90mm;border-radius:50%;'
        f'background:radial-gradient(circle,rgba(29,78,216,0.2) 0%,transparent 70%);pointer-events:none;"></div>'

        # Top bar: logo + document type badge
        f'<div style="padding:10mm {PAGE_PAD} 0;display:flex;align-items:center;'
        f'justify-content:space-between;position:relative;z-index:1;">'
        f'{logo_el}'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;letter-spacing:1.8pt;'
        f'text-transform:uppercase;color:#93c5fd;border:1pt solid rgba(147,197,253,0.25);'
        f'padding:3.5pt 10pt;border-radius:20pt;">Compliance-Screening</div>'
        f'</div>'

        # Main title area
        f'<div style="flex:1;padding:10mm {PAGE_PAD} 5mm;display:flex;flex-direction:column;'
        f'justify-content:center;position:relative;z-index:1;">'
        f'<div style="{FONT}font-size:7pt;font-weight:700;letter-spacing:2.5pt;'
        f'text-transform:uppercase;color:{BLUE};margin-bottom:4mm;">KI-gestütztes Analyse-Ergebnis</div>'
        f'<div style="{FONT}font-size:30pt;font-weight:800;color:#f8fafc;line-height:1.08;'
        f'letter-spacing:-0.6pt;margin-bottom:2.5mm;max-width:155mm;">{_esc(report.company_name)}</div>'
        f'<div style="{FONT}font-size:8.5pt;color:#475569;margin-bottom:9mm;font-weight:500;">'
        f'Erstellt am {_esc(date)}</div>'

        # Score ring + stats
        f'<div style="display:flex;align-items:center;gap:0;">'
        f'<div style="position:relative;margin-right:7mm;flex-shrink:0;">'
        f'<div style="width:34mm;height:34mm;border-radius:50%;border:3pt solid {sc};'
        f'background:rgba(15,23,42,0.6);box-shadow:0 0 18pt {sc}55;'
        f'display:flex;flex-direction:column;align-items:center;justify-content:center;">'
        f'<div style="{FONT}font-size:16pt;font-weight:800;color:{sc};line-height:1;">'
        f'{report.overall_score_percent:.0f}%</div>'
        f'<div style="{FONT}font-size:5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:{sc};opacity:0.8;margin-top:2pt;">Score</div>'
        f'</div></div>'
        f'{vdivider}{stat(n_app,"Vorschriften")}{vdivider}{stat(n_gaps,"Lücken")}'
        f'{vdivider}{stat(n_act,"Maßnahmen")}{vdivider}{stat(n_crit,"Kritisch","#f87171")}'
        f'</div></div>'

        # Bottom area: applicable regs chips + disclaimer
        f'<div style="padding:0 {PAGE_PAD} 9mm;position:relative;z-index:1;">'
        f'<div style="height:1pt;background:linear-gradient(90deg,rgba(255,255,255,0.08) 0%,transparent 100%);'
        f'margin-bottom:5mm;"></div>'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;letter-spacing:1.5pt;'
        f'text-transform:uppercase;color:#475569;margin-bottom:3.5mm;">Anwendbare Vorschriften</div>'
        f'<div style="line-height:1;">{chips}</div>'

        + (
            f'<div style="margin-top:4mm;padding:4mm 5mm;background:rgba(251,146,60,0.08);'
            f'border:1pt solid rgba(251,146,60,0.28);border-radius:5pt;">'
            f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1pt;color:#fb923c;margin-bottom:1.5mm;">'
            f'Niedrige Datenvollständigkeit - {report.profile_completeness["score_percent"]:.0f}%</div>'
            f'<div style="{FONT}font-size:6.5pt;color:#94a3b8;line-height:1.55;">'
            f'{report.profile_completeness["unanswered_count"]} compliance-relevante Felder nicht ausgefüllt. '
            f'Einige Befunde können auf Annahmen basieren. Profil vervollständigen und erneut ausführen.'
            f'</div></div>'
            if low_completeness else ""
        )

        + f'<div style="margin-top:4mm;padding:4mm 5mm;'
        f'background:rgba(245,158,11,0.06);border:1pt solid rgba(245,158,11,0.22);border-radius:5pt;">'
        f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:#f59e0b;margin-bottom:1.5mm;">'
        f'Vorläufiges Screening - Keine Rechtsberatung</div>'
        f'<div style="{FONT}font-size:6.5pt;color:#94a3b8;line-height:1.55;">'
        f'Dieser Bericht ist ein vorläufiges KI-gestütztes Compliance-Screening. '
        f'Er stellt keine Rechtsberatung dar und ersetzt keine qualifizierte rechtliche Prüfung.'
        f'</div></div>'

        f'</div></div>'
    )


# ─── Section 1+2: Summary & Applicability ─────────────────────────────────────

def _summary_and_applicability(report: ComplianceReport, logo: str) -> str:
    summary = _esc(_clean(report.executive_summary)) or "Keine Zusammenfassung verfügbar."

    # Render validation warnings with cleaned prefixes
    warns_html = ""
    if report.validation_warnings:
        items_html = ""
        for w in report.validation_warnings:
            cat, cleaned = _clean_warning(w)
            if not cleaned:
                continue
            if cat == "critical":
                label = "Widerspruch"
                label_color = "#b91c1c"
            elif cat == "warning":
                label = "Hinweis"
                label_color = "#a16207"
            else:
                label = "Info"
                label_color = "#64748b"
            items_html += (
                f'<div style="display:flex;gap:8pt;padding:5pt 0;border-bottom:0.5pt solid #f1f5f9;">'
                f'<span style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.8pt;color:{label_color};flex-shrink:0;padding-top:1pt;'
                f'min-width:40pt;">{_esc(label)}</span>'
                f'<span style="{FONT}font-size:8pt;color:#334155;line-height:1.6;">{_esc(cleaned)}</span>'
                f'</div>'
            )
        if items_html:
            warns_html = (
                f'<div style="margin-top:5mm;border:1pt solid #fde68a;border-radius:6pt;'
                f'overflow:hidden;">'
                f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:1pt;color:#a16207;padding:3.5mm 5mm;background:#fefce8;'
                f'border-bottom:1pt solid #fde68a;">Profilhinweise</div>'
                f'<div style="padding:0 5mm 3mm;background:#fff;">{items_html}</div>'
                f'</div>'
            )

    rows = ""
    for i, r in enumerate(report.applicable_regulations):
        bg = "#fafafa" if i % 2 == 1 else "#fff"
        if r.applies:
            badge = "background:#f0fdf4;color:#15803d;border:1pt solid #bbf7d0;"
            badge_text = "Ja"
        else:
            badge = "background:#f8fafc;color:#64748b;border:1pt solid #e2e8f0;"
            badge_text = "Nein"
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="{FONT}padding:3.5pt 8pt;font-weight:600;font-size:8.5pt;'
            f'width:24%;border-bottom:1pt solid #f1f5f9;white-space:nowrap;color:{NAVY};">'
            f'{_esc(_reg_label(r.regulation.value))}</td>'
            f'<td style="padding:3.5pt 8pt;text-align:center;width:13%;border-bottom:1pt solid #f1f5f9;">'
            f'<span style="{FONT}display:inline-block;font-size:7pt;font-weight:700;'
            f'padding:2pt 10pt;border-radius:20pt;white-space:nowrap;{badge}">{badge_text}</span></td>'
            f'<td style="{FONT}padding:3.5pt 8pt;font-size:8.5pt;color:#334155;'
            f'line-height:1.38;width:63%;border-bottom:1pt solid #f1f5f9;">'
            f'{_esc(_clean(r.reason))}</td>'
            f'</tr>'
        )

    return (
        # Abschnitt 01 — Zusammenfassung (own page)
        f'<div style="page-break-before:always;">'
        f'{_section_header(report.company_name, "Zusammenfassung")}'
        f'{_body_open()}'
        f'{_sec_title("Abschnitt 01", "Zusammenfassung")}'
        f'<div style="{FONT}font-size:9pt;color:{TEXT};line-height:1.7;margin-bottom:4mm;">{summary}</div>'
        f'{warns_html}'
        f'{_body_close()}</div>'

        # Abschnitt 02 — Anwendbarkeit (own page)
        f'<div style="page-break-before:always;">'
        f'{_section_header(report.company_name, "Anwendbarkeit der Vorschriften")}'
        f'{_body_open()}'
        f'{_sec_title("Abschnitt 02", "Anwendbarkeit der Vorschriften")}'
        f'{_sec_sub("Welche der 14 Vorschriften auf Ihr Unternehmen zutreffen - basierend auf Größe, Branche und Profil.")}'
        f'<div style="border-radius:6pt;overflow:hidden;border:1pt solid {BORDER};">'
        f'<table style="width:100%;border-collapse:collapse;table-layout:fixed;">'
        f'<thead><tr>'
        f'<th style="{FONT}background:#f1f5f9;color:#374151;font-size:7.5pt;font-weight:700;'
        f'padding:4.5pt 8pt;text-align:left;width:24%;border-bottom:2pt solid {BORDER};">Vorschrift</th>'
        f'<th style="{FONT}background:#f1f5f9;color:#374151;font-size:7.5pt;font-weight:700;'
        f'padding:4.5pt 8pt;text-align:center;width:13%;border-bottom:2pt solid {BORDER};">Gilt</th>'
        f'<th style="{FONT}background:#f1f5f9;color:#374151;font-size:7.5pt;font-weight:700;'
        f'padding:4.5pt 8pt;text-align:left;width:63%;border-bottom:2pt solid {BORDER};">Begründung</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'{_body_close()}</div>'
    )


# ─── Section 3: Scores ────────────────────────────────────────────────────────

def _scores(report: ComplianceReport, logo: str) -> str:
    sc  = _score_color(report.overall_score_percent)
    sbg = _score_bg(report.overall_score_percent)
    n_c = sum(rs.compliant for rs in report.regulation_scores)
    n_p = sum(rs.partially_compliant for rs in report.regulation_scores)
    n_n = sum(rs.non_compliant for rs in report.regulation_scores)
    n_t = sum(rs.total_requirements for rs in report.regulation_scores)

    def stat_box(n, lbl, c):
        return (
            f'<td style="width:25%;padding:0 2mm;">'
            f'<div style="{FONT}border:1pt solid {BORDER};border-radius:6pt;padding:4mm;'
            f'text-align:center;background:#fafafa;">'
            f'<div style="font-size:18pt;font-weight:800;color:{c};line-height:1;margin-bottom:1.5mm;">{n}</div>'
            f'<div style="font-size:6.5pt;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:0.8pt;color:#94a3b8;">{lbl}</div>'
            f'</div></td>'
        )

    rows = ""
    for i, rs in enumerate(report.regulation_scores):
        bc = _score_color(rs.score_percent)
        bw = min(100.0, max(0.0, rs.score_percent))
        bg = "#fafafa" if i % 2 == 1 else "#fff"
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="{FONT}padding:4pt 7pt;font-weight:600;font-size:8.5pt;'
            f'color:{NAVY};width:30%;">{_esc(_reg_label(rs.regulation.value))}</td>'
            f'<td style="{FONT}padding:4pt 7pt;text-align:center;font-weight:800;'
            f'font-size:10pt;color:{bc};width:10%;">{rs.score_percent:.0f}%</td>'
            f'<td style="padding:4pt 7pt;width:36%;">'
            f'<div style="height:7pt;background:#f1f5f9;border-radius:10pt;overflow:hidden;">'
            f'<div style="height:7pt;width:{bw}%;background:{bc};border-radius:10pt;"></div>'
            f'</div></td>'
            f'<td style="{FONT}padding:4pt 7pt;text-align:center;color:#15803d;'
            f'font-weight:700;font-size:8pt;width:8%;">{rs.compliant}</td>'
            f'<td style="{FONT}padding:4pt 7pt;text-align:center;color:#a16207;'
            f'font-weight:700;font-size:8pt;width:8%;">{rs.partially_compliant}</td>'
            f'<td style="{FONT}padding:4pt 7pt;text-align:center;color:#b91c1c;'
            f'font-weight:700;font-size:8pt;width:8%;">{rs.non_compliant}</td>'
            f'</tr>'
        )

    return (
        f'<div>'
        f'{_divider()}'
        f'{_sec_title("Abschnitt 03", "Score-Übersicht")}'
        f'<div style="{sbg};border:1.5pt solid {_score_border(report.overall_score_percent)};'
        f'border-radius:8pt;padding:6mm 8mm;margin-bottom:5mm;display:flex;align-items:center;gap:8mm;">'
        f'<div style="width:32mm;height:32mm;border-radius:50%;border:3pt solid {sc};'
        f'background:rgba(255,255,255,0.7);display:flex;flex-direction:column;'
        f'align-items:center;justify-content:center;flex-shrink:0;">'
        f'<div style="{FONT}font-size:18pt;font-weight:800;color:{sc};line-height:1;">'
        f'{report.overall_score_percent:.1f}%</div>'
        f'<div style="{FONT}font-size:5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:{sc};margin-top:2pt;">Score</div>'
        f'</div>'
        f'<div>'
        f'<div style="{FONT}font-size:11pt;font-weight:700;color:{NAVY};margin-bottom:2mm;">'
        f'Gesamt-Compliance-Score</div>'
        f'<div style="{FONT}font-size:8pt;color:{MUTED};line-height:1.6;">'
        f'{len(report.regulation_scores)} Vorschriften geprüft &nbsp;·&nbsp; '
        f'{n_t} Anforderungen bewertet &nbsp;·&nbsp; '
        f'{len(report.gap_analysis)} Lücken gefunden</div>'
        f'</div></div>'
        f'<table style="width:100%;border-collapse:collapse;margin-bottom:5mm;table-layout:fixed;">'
        f'<tr>{stat_box(n_c,"Konform","#15803d")}{stat_box(n_p,"Teilweise","#a16207")}'
        f'{stat_box(n_n,"Nicht konform","#b91c1c")}{stat_box(n_t,"Gesamt",NAVY)}</tr>'
        f'</table>'
        f'<div style="border-radius:6pt;overflow:hidden;border:1pt solid {BORDER};">'
        f'<table style="width:100%;border-collapse:collapse;table-layout:fixed;">'
        f'<thead><tr style="background:#f8fafc;">'
        f'<th style="{FONT}font-size:7pt;font-weight:700;text-transform:uppercase;letter-spacing:0.5pt;'
        f'color:{MUTED};padding:4pt 7pt;text-align:left;width:30%;border-bottom:1.5pt solid {BORDER};">Vorschrift</th>'
        f'<th style="{FONT}font-size:7pt;font-weight:700;text-transform:uppercase;letter-spacing:0.5pt;'
        f'color:{MUTED};padding:4pt 7pt;text-align:center;width:10%;border-bottom:1.5pt solid {BORDER};">Score</th>'
        f'<th style="{FONT}font-size:7pt;font-weight:700;padding:4pt 7pt;width:36%;border-bottom:1.5pt solid {BORDER};"></th>'
        f'<th style="{FONT}font-size:6.5pt;font-weight:700;color:#15803d;padding:4pt 7pt;'
        f'text-align:center;width:8%;border-bottom:1.5pt solid {BORDER};">K</th>'
        f'<th style="{FONT}font-size:6.5pt;font-weight:700;color:#a16207;padding:4pt 7pt;'
        f'text-align:center;width:8%;border-bottom:1.5pt solid {BORDER};">T</th>'
        f'<th style="{FONT}font-size:6.5pt;font-weight:700;color:#b91c1c;padding:4pt 7pt;'
        f'text-align:center;width:8%;border-bottom:1.5pt solid {BORDER};">NK</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'<div style="{FONT}font-size:6.5pt;color:#94a3b8;margin-top:2.5mm;">'
        f'K = Konform &nbsp;·&nbsp; T = Teilweise konform &nbsp;·&nbsp; NK = Nicht konform</div>'
        f'</div>'
    )


# ─── Section 4: Gap Analysis ─────────────────────────────────────────────────

def _gap_card(g) -> str:
    cm    = STATUS_STYLES.get(g.status, STATUS_STYLES[ComplianceStatus.CANNOT_ASSESS])
    ev    = _esc(_clean(g.evidence))
    defic = _esc(_clean(g.deficiency_description))
    art_n = _esc(_clean(g.article_number))
    art_t = _esc(_clean(g.article_title))

    conf = getattr(g, "confidence", "HIGH")
    conf_reason = getattr(g, "confidence_reason", None)

    conf_badge = ""
    if conf in ("MEDIUM", "LOW"):
        conf_bg = "#fefce8" if conf == "MEDIUM" else "#fff7ed"
        conf_c  = "#a16207" if conf == "MEDIUM" else "#c2410c"
        conf_br = "#fef08a" if conf == "MEDIUM" else "#fed7aa"
        conf_badge = (
            f'<span style="{FONT}font-size:6.5pt;font-weight:700;padding:2pt 7pt;'
            f'border-radius:20pt;background:{conf_bg};color:{conf_c};'
            f'border:1pt solid {conf_br};margin-right:5pt;">'
            f'{_esc(conf)} Konfidenz</span>'
        )

    defic_block = ""
    if defic:
        defic_block = (
            f'<div style="margin-top:6pt;padding:5pt 9pt;'
            f'border-left:3pt solid #b91c1c;background:#fef2f2;border-radius:0 4pt 4pt 0;">'
            f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1pt;color:#b91c1c;margin-bottom:2pt;">Handlungsbedarf</div>'
            f'<div style="{FONT}font-size:8.5pt;color:#7f1d1d;line-height:1.6;">{defic}</div>'
            f'</div>'
        )

    conf_note = ""
    if conf_reason and conf != "HIGH":
        conf_note = (
            f'<div style="{FONT}font-size:7pt;color:#94a3b8;font-style:italic;margin-top:3pt;">'
            f'{_esc(_clean(conf_reason))}</div>'
        )

    return (
        f'<div style="border-left:4pt solid {cm["c"]};border:1pt solid {BORDER};'
        f'border-left-width:4pt;border-left-color:{cm["c"]};'
        f'border-radius:0 6pt 6pt 0;margin-bottom:5mm;background:#fff;">'
        # Header
        f'<div style="padding:5pt 10pt;background:#f8fafc;border-bottom:1pt solid {BORDER};'
        f'display:flex;align-items:center;justify-content:space-between;gap:8pt;">'
        f'<div style="{FONT}font-size:8.5pt;font-weight:700;color:{NAVY};">'
        f'{"" if art_n.startswith("§") or art_n.startswith("Art") else "§ "}{art_n} &nbsp;·&nbsp; {art_t}</div>'
        f'<div style="display:flex;align-items:center;flex-shrink:0;">'
        f'{conf_badge}'
        f'<span style="{FONT}font-size:7pt;font-weight:700;padding:2.5pt 9pt;border-radius:20pt;'
        f'border:1pt solid {cm["br"]};background:{cm["bg"]};color:{cm["c"]};white-space:nowrap;">'
        f'{_esc(cm["label"])}</span>'
        f'</div></div>'
        # Body
        f'<div style="padding:7pt 10pt 8pt;">'
        f'<div style="{FONT}font-size:6pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1.2pt;color:#94a3b8;margin-bottom:2pt;">Bewertung</div>'
        f'<div style="{FONT}font-size:8.5pt;color:#334155;line-height:1.65;">{ev}</div>'
        f'{conf_note}'
        f'{defic_block}'
        f'</div></div>'
    )


def _reg_group_header(reg_key: str, gaps: list, is_action: bool = False) -> str:
    if is_action:
        count_html = ""
    else:
        n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
        n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
        n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
        count_html = (
            f'<span style="{FONT}font-size:7.5pt;color:{MUTED};">'
            f'{n_c} konform &nbsp;·&nbsp; {n_p} teilweise &nbsp;·&nbsp; {n_n} nicht konform'
            f'</span>'
        )
    return (
        f'<div style="margin-top:6mm;margin-bottom:3mm;padding-bottom:3mm;'
        f'border-bottom:2pt solid {BORDER};display:flex;align-items:baseline;'
        f'justify-content:space-between;">'
        f'<span style="{FONT}font-size:11pt;font-weight:700;color:{NAVY};">'
        f'{_esc(_reg_label(reg_key))}</span>'
        f'{count_html}'
        f'</div>'
    )


def _gaps(report: ComplianceReport, logo: str) -> str:
    if not report.gap_analysis:
        return (
            f'<div style="page-break-before:always;">'
            f'{_section_header(report.company_name, "Lückenanalyse")}'
            f'{_body_open()}{_sec_title("Abschnitt 04", "Lückenanalyse")}'
            f'<p style="{FONT}font-size:9pt;color:{MUTED};">Keine Compliance-Lücken gefunden.</p>'
            f'{_body_close()}</div>'
        )

    by_reg: dict[str, list] = {}
    for g in report.gap_analysis:
        by_reg.setdefault(g.regulation.value, []).append(g)

    body = ""
    for reg_key, gaps in by_reg.items():
        header_html = _reg_group_header(reg_key, gaps)
        cards = [_gap_card(g) for g in gaps]
        # Keep header + first card together to avoid orphaned headers
        if cards:
            body += header_html + cards[0]
            body += "".join(cards[1:])
        else:
            body += header_html

    return (
        f'<div style="page-break-before:always;">'
        f'{_section_header(report.company_name, "Lückenanalyse - Abschnitt 04")}'
        f'{_body_open()}'
        f'{_sec_title("Abschnitt 04", "Lückenanalyse")}'
        f'{_sec_sub("Jede geprüfte Anforderung, nach Vorschrift gruppiert. Status, Bewertung und konkreter Handlungsbedarf.")}'
        f'{body}'
        f'{_body_close()}</div>'
    )


# ─── Section 5: Action Plan ──────────────────────────────────────────────────

def _action_card(a) -> str:
    pm      = PRIORITY_STYLES.get(a.priority, PRIORITY_STYLES[Priority.LOW])
    action  = _esc(_clean(a.action))
    effort  = _esc(_clean(a.estimated_effort)) if a.estimated_effort else ""
    dl      = _esc(_clean(a.deadline)) if a.deadline else ""
    _raw_ref = _clean(getattr(a, "gap_reference", "") or "")
    # Convert internal refs like "milog:§ 17" → "MiLoG § 17"
    def _fmt_ref(r: str) -> str:
        if ":" in r:
            key, rest = r.split(":", 1)
            label = REGULATION_LABELS.get(key.strip(), key.strip().upper())
            return f"{label} {rest.strip()}"
        return r
    gap_ref = _esc(_fmt_ref(_raw_ref)) if _raw_ref else ""
    deps    = getattr(a, "dependencies", []) or []
    deps_str = "; ".join(_clean(d) for d in deps if d) if deps else ""

    meta_parts = []
    if effort:
        meta_parts.append(f'<b style="color:{TEXT};">Aufwand:</b> {effort}')
    if dl:
        meta_parts.append(f'<b style="color:{TEXT};">Frist:</b> {dl}')
    meta_row = f'<span style="{FONT}font-size:7.5pt;color:{MUTED};">' + " &nbsp;·&nbsp; ".join(meta_parts) + '</span>' if meta_parts else ""

    ref_row = ""
    if gap_ref:
        ref_row = (
            f'<div style="{FONT}font-size:7.5pt;color:{MUTED};margin-top:3pt;">'
            f'<b style="color:{TEXT};">Bezieht sich auf:</b> {gap_ref}</div>'
        )

    deps_row = ""
    if deps_str:
        deps_row = (
            f'<div style="{FONT}font-size:7.5pt;color:{MUTED};margin-top:2pt;">'
            f'<b style="color:{TEXT};">Abhangigkeiten:</b> {_esc(deps_str)}</div>'
        )

    return (
        f'<div style="border-left:4pt solid {pm["c"]};border:1pt solid {BORDER};'
        f'border-left-width:4pt;border-left-color:{pm["c"]};'
        f'border-radius:0 6pt 6pt 0;margin-bottom:5mm;background:#fff;">'
        # Header bar
        f'<div style="padding:5pt 10pt;background:#f8fafc;border-bottom:1pt solid {BORDER};'
        f'display:flex;align-items:center;gap:8pt;">'
        f'<span style="{FONT}font-size:7pt;font-weight:700;padding:2.5pt 9pt;border-radius:20pt;'
        f'border:1pt solid {pm["br"]};background:{pm["bg"]};color:{pm["c"]};flex-shrink:0;">'
        f'{_esc(pm["label"])}</span>'
        f'<span style="{FONT}font-size:8.5pt;font-weight:700;color:{NAVY};">'
        f'{"" if _clean(a.article_number).startswith("§") or _clean(a.article_number).startswith("Art") else "§ "}{_esc(_clean(a.article_number))}</span>'
        f'<span style="{FONT}font-size:7.5pt;color:{MUTED};margin-left:auto;flex-shrink:0;">'
        f'{_esc(_reg_label(a.regulation.value))}</span>'
        f'</div>'
        # Body
        f'<div style="padding:7pt 10pt 8pt;">'
        f'<div style="{FONT}font-size:8.5pt;color:{TEXT};line-height:1.7;margin-bottom:5pt;">'
        f'{action}</div>'
        f'{meta_row}'
        f'{ref_row}'
        f'{deps_row}'
        f'</div></div>'
    )


def _actions(report: ComplianceReport, logo: str) -> str:
    if not report.action_plan:
        return (
            f'<div style="page-break-before:always;">'
            f'{_section_header(report.company_name, "Maßnahmenplan")}'
            f'{_body_open()}{_sec_title("Abschnitt 05", "Maßnahmenplan")}'
            f'<p style="{FONT}font-size:9pt;color:{MUTED};">Keine Maßnahmen erforderlich.</p>'
            f'{_body_close()}</div>'
        )

    # Sort by priority: CRITICAL first, then HIGH, MEDIUM, LOW
    _prio_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
    by_reg: dict[str, list] = {}
    for a in report.action_plan:
        by_reg.setdefault(a.regulation.value, []).append(a)
    for reg_key in by_reg:
        by_reg[reg_key].sort(key=lambda x: _prio_order.get(x.priority, 4))

    body = ""
    for reg_key, acts in by_reg.items():
        header_html = _reg_group_header(reg_key, acts, is_action=True)
        cards = [_action_card(a) for a in acts]
        if cards:
            body += header_html + cards[0]
            body += "".join(cards[1:])
        else:
            body += header_html

    return (
        f'<div style="page-break-before:always;">'
        f'{_section_header(report.company_name, "Maßnahmenplan - Abschnitt 05")}'
        f'{_body_open()}'
        f'{_sec_title("Abschnitt 05", "Maßnahmenplan")}'
        f'{_sec_sub("Priorisierte Aufgabenliste zum Schließen Ihrer Compliance-Lücken. Beginnen Sie mit Kritisch und Hoch.")}'
        f'{body}'
        f'{_body_close()}</div>'
    )


# ─── Section 6: Closing ──────────────────────────────────────────────────────

def _closing(report: ComplianceReport, logo: str) -> str:
    steps = [
        ("01", "Beginnen Sie mit Maßnahmen der Priorität <b>Kritisch</b> und <b>Hoch</b>. "
               "Das sind Ihre aktuellen rechtlichen Risiken mit dem größten Handlungsbedarf."),
        ("02", "Weisen Sie jeder Maßnahme eine verantwortliche Person und eine konkrete Frist zu. "
               "Ohne klare Verantwortlichkeit werden Maßnahmen nicht umgesetzt."),
        ("03", "Dokumentieren Sie alles schriftlich. Behörden werden bei einer Prüfung Nachweise verlangen - "
               "Protokolle, Richtlinien, Schulungsnachweise und Verträge."),
        ("04", "Führen Sie das Screening nach der Umsetzung erneut durch. "
               "Ihr Compliance-Score wird sich verbessern und Sie sehen, was noch fehlt."),
        ("05", "Bei Unsicherheiten konsultieren Sie vor Entscheidungen einen zugelassenen deutschen Rechtsanwalt - "
               "insbesondere bei DSGVO, NIS2, LkSG und CSRD."),
    ]
    items = ""
    for num, text in steps:
        items += (
            f'<div style="display:flex;align-items:flex-start;gap:9pt;margin-bottom:5mm;">'
            f'<div style="{FONT}width:20pt;height:20pt;border-radius:50%;background:{BLUE};'
            f'color:#fff;font-size:7.5pt;font-weight:700;display:flex;align-items:center;'
            f'justify-content:center;flex-shrink:0;margin-top:1pt;">{num}</div>'
            f'<div style="{FONT}font-size:9pt;color:#334155;line-height:1.7;flex:1;">{text}</div>'
            f'</div>'
        )

    # Profile characteristics
    chars = report.inferred_characteristics or []
    char_rows = "".join(
        f'<li style="{FONT}font-size:8pt;color:#334155;margin-bottom:1.5mm;">{_esc(c)}</li>'
        for c in chars
    ) if chars else f'<li style="{FONT}font-size:8pt;color:#94a3b8;font-style:italic;">Keine aufgezeichnet</li>'

    assumptions = report.inferred_assumptions or []
    assumption_rows = "".join(
        f'<li style="{FONT}font-size:8pt;color:#334155;margin-bottom:1.5mm;">{_esc(a)}</li>'
        for a in assumptions
    ) if assumptions else ""

    assumptions_block = ""
    if assumption_rows:
        assumptions_block = (
            f'<div style="{FONT}font-size:7.5pt;font-weight:600;color:#c2410c;'
            f'margin-top:3mm;margin-bottom:1.5mm;">'
            f'Angenommene Werte (nicht bestätigt - vor Maßnahmen prüfen)</div>'
            f'<ul style="margin:0;padding-left:4mm;">{assumption_rows}</ul>'
        )

    input_block = (
        f'<div style="margin-top:7mm;padding:5mm 6mm;background:#fafafa;border:1pt solid {BORDER};'
        f'border-radius:6pt;">'
        f'<div style="{FONT}font-size:6.5pt;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1pt;color:#94a3b8;margin-bottom:3mm;">Eingabeannahmen</div>'
        f'<div style="{FONT}font-size:7.5pt;font-weight:600;color:{MUTED};margin-bottom:1.5mm;">Abgeleitete Merkmale</div>'
        f'<ul style="margin:0;padding-left:4mm;">{char_rows}</ul>'
        f'{assumptions_block}'
        f'</div>'
    )

    return (
        f'<div style="page-break-before:always;">'
        f'{_section_header(report.company_name, "Nächste Schritte - Abschnitt 06")}'
        f'{_body_open()}'
        f'{_sec_title("Abschnitt 06", "Nächste Schritte")}'
        f'{_sec_sub("Sie kennen jetzt Ihren Compliance-Stand. Das sind die empfohlenen nächsten Schritte.")}'
        f'<div style="margin-top:2mm;">{items}</div>'
        f'{input_block}'
        f'<div style="margin-top:7mm;padding-top:4mm;border-top:1pt solid #f1f5f9;'
        f'text-align:center;{FONT}font-size:7.5pt;color:#94a3b8;">'
        f'<strong style="color:{NAVY};">Complio</strong> &nbsp;·&nbsp; '
        f'Automatisiertes Compliance-Screening fur deutsche KMU<br>'
        f'<span style="font-size:7pt;">Erstellt von einem KI-System. Kein zertifiziertes Audit. Keine Rechtsberatung.</span>'
        f'</div>'
        f'<div style="margin-top:6mm;padding:5mm 6mm;background:#f8fafc;border:1pt solid {BORDER};'
        f'border-radius:6pt;{FONT}font-size:7.5pt;color:{MUTED};line-height:1.7;font-style:italic;">'
        f'{_esc(report.disclaimer)}'
        f'</div>'
        f'{_body_close()}</div>'
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

def generate_pdf(report: ComplianceReport) -> bytes:
    logo = _logo_data_uri()

    html = (
        '<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">'
        f'<style>{_FONT_CSS}'
        '*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}'
        f"body{{{FONT}font-size:9.5pt;color:{TEXT};background:#fff;"
        '-webkit-print-color-adjust:exact;print-color-adjust:exact;}'
        # First page (cover) stays full-bleed; every other page gets consistent top/bottom margin
        '@page{size:A4;margin:14mm 0 12mm 0;}'
        '@page:first{size:A4;margin:0;}'
        'table{border-collapse:collapse;}'
        '</style></head><body>'
        + _cover(report, logo)
        + _summary_and_applicability(report, logo)
        + f'<div style="page-break-before:always;padding:0 {PAGE_PAD} 8mm;">{_scores(report, logo)}</div>'
        + _gaps(report, logo)
        + _actions(report, logo)
        + _closing(report, logo)
        + '</body></html>'
    )

    pdf_options = dict(
        format="A4",
        print_background=True,
        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        display_header_footer=False,
    )

    with _pdf_semaphore:
        browser = _browser
        if browser is None:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                cold_browser = pw.chromium.launch()
                pg = cold_browser.new_page()
                pg.set_default_timeout(30_000)
                pg.route("**/*", lambda route: route.abort())
                pg.set_viewport_size({"width": 794, "height": 1123})
                pg.set_content(html, wait_until="load", timeout=30_000)
                result = pg.pdf(**pdf_options)
                cold_browser.close()
            return result

        pg = browser.new_page()
        try:
            pg.set_default_timeout(30_000)
            pg.route("**/*", lambda route: route.abort())
            pg.set_viewport_size({"width": 794, "height": 1123})
            pg.set_content(html, wait_until="load", timeout=30_000)
            return pg.pdf(**pdf_options)
        finally:
            pg.close()
