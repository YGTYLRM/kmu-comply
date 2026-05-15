"""Patch: section name in header bar (no logo on content pages) + more spacing."""
content = open("services/pdf_generator.py", encoding="utf-8").read()

# ── 1. _hbar: section name on left, company on right, no logo ────────────────
old = """def _hbar(company, section, logo):
    logo_el = (f'<img src="{logo}" style="height:12pt;vertical-align:middle;" alt="Complio">'
               if logo else
               f'<span style="font-weight:800;font-size:11pt;color:#fff;{FONT}">Complio</span>')
    return (
        f'<div>'
        f'<div style="{FONT}background:{NAVY};padding:5.5mm {M};display:flex;align-items:center;justify-content:space-between;">'
        f'<div>{logo_el}</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:7.5pt;color:#94a3b8;font-weight:500;">{_h(company)}</div>'
        f'<div style="font-size:6pt;color:#64748b;text-transform:uppercase;letter-spacing:.9pt;margin-top:2pt;">{_h(section)}</div>'
        f'</div></div>'
        f'<div style="height:2.5pt;background:linear-gradient(90deg,{BLUE} 0%,{BLUE} 55%,rgba(37,99,235,0) 100%);"></div>'
        f'</div>'
    )"""

new = """def _hbar(company, section, logo):
    return (
        f'<div>'
        f'<div style="{FONT}background:{NAVY};padding:5mm {M};display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="font-size:9.5pt;font-weight:700;color:#fff;letter-spacing:.1pt;">{_h(section)}</div>'
        f'<div style="font-size:7pt;color:#475569;font-weight:500;">{_h(company)}</div>'
        f'</div>'
        f'<div style="height:2.5pt;background:linear-gradient(90deg,{BLUE} 0%,{BLUE} 55%,rgba(37,99,235,0) 100%);"></div>'
        f'</div>'
    )"""

assert old in content, "FAIL: _hbar not found"
content = content.replace(old, new)

# ── 2. _reg_header: increase top margin and add more space before line ────────
old = """def _reg_header(reg_key, gaps, first=False):
    n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
    n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
    n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
    mt = "0" if first else "7mm"
    return (
        f'<div style="margin-top:{mt};margin-bottom:4mm;display:flex;align-items:baseline;'
        f'justify-content:space-between;padding-bottom:3mm;border-bottom:1.5pt solid #e8edf2;">'
        f'<div style="{FONT}font-size:10pt;font-weight:700;color:{NAVY};">{_h(_reg(reg_key))}</div>'
        f'<div style="{FONT}font-size:7pt;color:#94a3b8;">'
        f'{n_c} compliant &nbsp;&middot;&nbsp; {n_p} partial &nbsp;&middot;&nbsp; {n_n} non-compliant'
        f'</div></div>'
    )"""

new = """def _reg_header(reg_key, gaps, first=False):
    n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
    n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
    n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
    mt = "2mm" if first else "12mm"
    return (
        f'<div style="margin-top:{mt};margin-bottom:4mm;display:flex;align-items:baseline;'
        f'justify-content:space-between;padding-bottom:3mm;border-bottom:1.5pt solid #e8edf2;">'
        f'<div style="{FONT}font-size:10pt;font-weight:700;color:{NAVY};">{_h(_reg(reg_key))}</div>'
        f'<div style="{FONT}font-size:7pt;color:#94a3b8;">'
        f'{n_c} compliant &nbsp;&middot;&nbsp; {n_p} partial &nbsp;&middot;&nbsp; {n_n} non-compliant'
        f'</div></div>'
    )"""

assert old in content, "FAIL: _reg_header not found"
content = content.replace(old, new)

# ── 3. Action plan inline headers: same margin increase ───────────────────────
old = """        mt = "0" if i == 0 else "7mm"
        header = (
            f'<div style="margin-top:{mt};margin-bottom:4mm;display:flex;align-items:baseline;'
            f'justify-content:space-between;padding-bottom:3mm;border-bottom:1.5pt solid #e8edf2;">'
            f'<div style="{FONT}font-size:10pt;font-weight:700;color:{NAVY};">{_h(_reg(reg_key))}</div>'
            f'</div>'
        )"""

new = """        mt = "2mm" if i == 0 else "12mm"
        header = (
            f'<div style="margin-top:{mt};margin-bottom:4mm;display:flex;align-items:baseline;'
            f'justify-content:space-between;padding-bottom:3mm;border-bottom:1.5pt solid #e8edf2;">'
            f'<div style="{FONT}font-size:10pt;font-weight:700;color:{NAVY};">{_h(_reg(reg_key))}</div>'
            f'</div>'
        )"""

assert old in content, "FAIL: actions mt not found"
content = content.replace(old, new)

# ── 4. Body top padding: 7mm → 10mm so first element has more room ────────────
old = "def _body_open():\n    return f'<div style=\"padding:7mm {M} 12mm;\">'"
new = "def _body_open():\n    return f'<div style=\"padding:10mm {M} 12mm;\">'"

assert old in content, "FAIL: _body_open not found"
content = content.replace(old, new)

open("services/pdf_generator.py", "w", encoding="utf-8").write(content)
print("Done")
