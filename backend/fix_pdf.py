"""One-shot patch: fix orphan headers + redesign reg headers + lighten table headers."""
content = open("services/pdf_generator.py", encoding="utf-8").read()
original = content

# ── 1. Replace _reg_header with full-width blue-tint band ────────────────────
old = """def _reg_header(reg_key, gaps, first=False):
    n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
    n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
    n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
    top_border = "" if first else f"padding-top:5mm;border-top:1.5pt solid #f1f5f9;"
    return (
        f'<div style="margin-top:{"0" if first else "6mm"};margin-bottom:4mm;{top_border}page-break-inside:avoid;">'
        f'<div style="{FONT}display:inline-flex;align-items:center;gap:6pt;font-size:8pt;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:1.2pt;color:{BLUE};">'
        f'<span style="width:3.5pt;height:14pt;background:{BLUE};border-radius:2pt;display:inline-block;"></span>'
        f'{_h(_reg(reg_key))}</div>'
        f'<div style="{FONT}font-size:7.5pt;color:#94a3b8;margin-top:2.5mm;">'
        f'{n_c} compliant &nbsp;&middot;&nbsp; {n_p} partial &nbsp;&middot;&nbsp; {n_n} non-compliant'
        f'</div></div>'
    )"""

new = """def _reg_header(reg_key, gaps, first=False):
    n_c = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
    n_p = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIALLY_COMPLIANT)
    n_n = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)
    mt = "0" if first else "7mm"
    return (
        f'<div style="margin-top:{mt};margin-bottom:3mm;">'
        f'<div style="background:#eff6ff;border-left:4pt solid {BLUE};border-radius:0 6pt 6pt 0;padding:5pt 11pt;">'
        f'<div style="{FONT}font-size:8.5pt;font-weight:700;color:#1e40af;letter-spacing:.3pt;">{_h(_reg(reg_key))}</div>'
        f'<div style="{FONT}font-size:7pt;color:#6b7280;margin-top:2pt;">'
        f'{n_c} compliant &nbsp;&middot;&nbsp; {n_p} partial &nbsp;&middot;&nbsp; {n_n} non-compliant'
        f'</div></div></div>'
    )"""

assert old in content, "FAIL: _reg_header not found"
content = content.replace(old, new)

# ── 2. Fix orphan header in _gaps ────────────────────────────────────────────
old = """    body = ""
    for i, (reg_key, gaps) in enumerate(by_reg.items()):
        body += _reg_header(reg_key, gaps, first=(i == 0))
        body += "".join(_gap_card(g) for g in gaps)"""

new = """    body = ""
    for i, (reg_key, gaps) in enumerate(by_reg.items()):
        header = _reg_header(reg_key, gaps, first=(i == 0))
        cards = [_gap_card(g) for g in gaps]
        if cards:
            body += f'<div style="page-break-inside:avoid;">{header}{cards[0]}</div>'
            body += "".join(cards[1:])
        else:
            body += header"""

assert old in content, "FAIL: gaps loop not found"
content = content.replace(old, new)

# ── 3. Fix orphan header in _actions + use same band style ───────────────────
old = """    body = ""
    for i, (reg_key, acts) in enumerate(by_reg.items()):
        top_border = "" if i == 0 else f"padding-top:5mm;border-top:1.5pt solid #f1f5f9;"
        body += (
            f'<div style="margin-top:{"0" if i==0 else "6mm"};margin-bottom:4mm;{top_border}page-break-inside:avoid;">'
            f'<div style="{FONT}display:inline-flex;align-items:center;gap:6pt;font-size:8pt;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:1.2pt;color:{BLUE};">'
            f'<span style="width:3.5pt;height:14pt;background:{BLUE};border-radius:2pt;display:inline-block;"></span>'
            f'{_h(_reg(reg_key))}</div></div>'
        )
        body += "".join(_action_card(a) for a in acts)"""

new = """    body = ""
    for i, (reg_key, acts) in enumerate(by_reg.items()):
        mt = "0" if i == 0 else "7mm"
        header = (
            f'<div style="margin-top:{mt};margin-bottom:3mm;">'
            f'<div style="background:#eff6ff;border-left:4pt solid {BLUE};border-radius:0 6pt 6pt 0;padding:5pt 11pt;">'
            f'<div style="{FONT}font-size:8.5pt;font-weight:700;color:#1e40af;letter-spacing:.3pt;">{_h(_reg(reg_key))}</div>'
            f'</div></div>'
        )
        cards = [_action_card(a) for a in acts]
        if cards:
            body += f'<div style="page-break-inside:avoid;">{header}{cards[0]}</div>'
            body += "".join(cards[1:])
        else:
            body += header"""

assert old in content, "FAIL: actions loop not found"
content = content.replace(old, new)

# ── 4. Lighten applicability table header ────────────────────────────────────
old = (
    'f\'<th style="{FONT}background:{NAVY};color:#fff;font-size:7.5pt;font-weight:600;'
    'padding:6pt 9pt;text-align:left;width:22%;">Regulation</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#fff;font-size:7.5pt;font-weight:600;'
    'padding:6pt 9pt;text-align:center;width:12%;">Applies</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#fff;font-size:7.5pt;font-weight:600;'
    'padding:6pt 9pt;text-align:left;width:66%;">Reason</th>\''
)
new = (
    'f\'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7.5pt;font-weight:700;'
    'padding:6pt 9pt;text-align:left;width:22%;border-bottom:2pt solid #bfdbfe;">Regulation</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7.5pt;font-weight:700;'
    'padding:6pt 9pt;text-align:center;width:12%;border-bottom:2pt solid #bfdbfe;">Applies</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7.5pt;font-weight:700;'
    'padding:6pt 9pt;text-align:left;width:66%;border-bottom:2pt solid #bfdbfe;">Reason</th>\''
)
assert old in content, "FAIL: applicability th not found"
content = content.replace(old, new)

# ── 5. Lighten score table header ────────────────────────────────────────────
old = (
    'f\'<th style="{FONT}background:{NAVY};color:#e2e8f0;font-size:7pt;font-weight:600;'
    'text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;text-align:left;width:28%;">Regulation</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#e2e8f0;font-size:7pt;font-weight:600;'
    'text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;text-align:center;width:10%;">Score</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#e2e8f0;font-size:7pt;font-weight:600;'
    'text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;width:38%;">Progress</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#4ade80;font-size:7pt;font-weight:700;'
    'padding:5pt 8pt;text-align:center;width:8%;">C</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#fbbf24;font-size:7pt;font-weight:700;'
    'padding:5pt 8pt;text-align:center;width:8%;">P</th>\'\n'
    '        f\'<th style="{FONT}background:{NAVY};color:#f87171;font-size:7pt;font-weight:700;'
    'padding:5pt 8pt;text-align:center;width:8%;">NC</th>\''
)
new = (
    'f\'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7pt;font-weight:700;'
    'text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;text-align:left;width:28%;'
    'border-bottom:2pt solid #bfdbfe;">Regulation</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7pt;font-weight:700;'
    'text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;text-align:center;width:10%;'
    'border-bottom:2pt solid #bfdbfe;">Score</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#1e40af;font-size:7pt;font-weight:700;'
    'text-transform:uppercase;letter-spacing:.5pt;padding:5pt 8pt;width:38%;'
    'border-bottom:2pt solid #bfdbfe;">Progress</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#16a34a;font-size:7pt;font-weight:700;'
    'padding:5pt 8pt;text-align:center;width:8%;border-bottom:2pt solid #bfdbfe;">C</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#b45309;font-size:7pt;font-weight:700;'
    'padding:5pt 8pt;text-align:center;width:8%;border-bottom:2pt solid #bfdbfe;">P</th>\'\n'
    '        f\'<th style="{FONT}background:#dbeafe;color:#dc2626;font-size:7pt;font-weight:700;'
    'padding:5pt 8pt;text-align:center;width:8%;border-bottom:2pt solid #bfdbfe;">NC</th>\''
)
assert old in content, "FAIL: score th not found"
content = content.replace(old, new)

open("services/pdf_generator.py", "w", encoding="utf-8").write(content)
print(f"Done. {len(content) - len(original):+d} bytes")
