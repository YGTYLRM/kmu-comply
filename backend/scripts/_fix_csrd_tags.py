# -*- coding: utf-8 -*-
"""One-off script: fix article_number tagging bug in CSRD's ESRS guidance
file, same root cause and fix pattern as _fix_lksg_gwg_tags.py /
_fix_enefg_tags.py -- bare topic slugs instead of a citable reference on
line 1. Requires the ESRS-pattern branch added to
rag/ingest.py::_chunk_separator_blocks (that function previously only
recognised '§ N', never 'ESRS N', so no retag of this file was possible
before that change).

esrs_assurance_and_penalties is intentionally left untagged -- it discusses
both ESRS-level assurance mechanics and Directive-level non-compliance
penalties, two different legal sources; forcing one citation would be
dishonest, same precedent as the lksg/gwg/enefg fix scripts.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent / "data" / "regulations" / "csrd"

ESRS_MAP = {
    "esrs1_double_materiality": "ESRS 1",
    "esrs1_value_chain_scope": "ESRS 1",
    "esrs_e1_climate_governance": "ESRS E1",
    "esrs_e1_ghg_emissions": "ESRS E1",
    "esrs_e1_transition_plan": "ESRS E1",
    "esrs_e1_physical_risks": "ESRS E1",
    "esrs_s1_workforce_disclosures": "ESRS S1",
    "esrs_s1_working_conditions": "ESRS S1",
    "esrs_s1_equal_treatment": "ESRS S1",
    "esrs_s2_value_chain_workers": "ESRS S2",
    "esrs_g1_business_conduct": "ESRS G1",
    "esrs_materiality_phased_requirements": "ESRS 1",
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
    n = fix_first_lines(ROOT / "esrs_sector_standards_expanded.txt", ESRS_MAP)
    print(f"csrd: retagged {n} / {len(ESRS_MAP)} blocks")
