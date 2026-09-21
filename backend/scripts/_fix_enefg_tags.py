# -*- coding: utf-8 -*-
"""One-off script: fix article_number tagging bug in EnEfG/EDL-G guidance
files, same root cause and same fix pattern as _fix_lksg_gwg_tags.py.
Blocks whose content genuinely spans multiple statute provisions (no single
clean citation) are intentionally left untagged, matching that script's
documented precedent -- forcing one would be dishonest.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent / "data" / "regulations" / "enefg"

DENA_MAP = {
    "enefg_scope_non_sme": "enefg §8",
    "enefg_edlg_audit_obligation": "enefg §8",
    "enefg_7500_mwh_threshold": "enefg §8(1)",
    "din_en_16247_methodology": "enefg §8",
    "iso_50001_energy_management": "enefg §8",
    "enefg_waste_heat_utilisation": "enefg §16",
    "enefg_bafa_reporting_obligations": "enefg §8",
    "enefg_energy_monitoring": "enefg §8",
    # enefg_building_energy_requirements intentionally left untagged --
    # interacts with GEG (a different statute), no single EnEfG/EDL-G
    # citation covers it.
    # enefg_sme_voluntary_measures intentionally left untagged -- describes
    # voluntary BAFA/KfW funding programmes, not a statutory obligation.
}

BAFA_MAP = {
    # "enefg EDL-G Penalties" intentionally left untagged -- the block
    # itself cites four different provisions (EDL-G §8, EnEfG §8(1),
    # EnEfG §9, EnEfG §16) as the violated obligations behind the fines
    # it describes; no single clean citation, forcing one would be
    # dishonest.
    # "enefg Energy Data Centre Obligations" intentionally left untagged --
    # its own title spans EnEfG §11-12, two sections, not one.
}


def fix_first_lines(path: Path, mapping: dict[str, str]) -> int:
    text = path.read_text(encoding="utf-8")
    blocks = text.split("---")
    changed = 0
    new_blocks = []
    for block in blocks:
        stripped_lines = block.split("\n")
        idx = None
        for i, line in enumerate(stripped_lines):
            if line.strip():
                idx = i
                break
        if idx is not None and stripped_lines[idx].strip() in mapping:
            slug = stripped_lines[idx].strip()
            new_tag = mapping[slug]
            stripped_lines[idx] = f"{new_tag}  ({slug})"
            changed += 1
        new_blocks.append("\n".join(stripped_lines))
    path.write_text("---".join(new_blocks), encoding="utf-8")
    return changed


if __name__ == "__main__":
    n1 = fix_first_lines(ROOT / "dena_energy_audit_guidance_expanded.txt", DENA_MAP)
    print(f"dena: retagged {n1} / {len(DENA_MAP)} blocks")
    n2 = fix_first_lines(ROOT / "bafa_enefg_obligations_expanded.txt", BAFA_MAP)
    print(f"bafa: retagged {n2} / {len(BAFA_MAP)} blocks")
