# -*- coding: utf-8 -*-
"""One-off script: fix article_number tagging bug in LkSG and GwG guidance
files by rewriting each block's first line to '<reg> §N' format, matching
the convention _chunk_separator_blocks expects and that milog/arbschg
already use. Root cause: these two files used a bare slug as line 1
(e.g. 'bafa_lksg_risk_analysis_methodology'), so the ingest regex
r'§\\s*(\\S+)' found no match and fell back to the slug itself as
article_number -- meaning these chunks could never match a '§ N' ground
truth citation in the retrieval eval, regardless of topical relevance."""
from pathlib import Path

ROOT = Path(__file__).parent.parent / "data" / "regulations"

LKSG_MAP = {
    "bafa_lksg_risk_analysis_methodology": "lksg §5",
    "bafa_lksg_human_rights_due_diligence": "lksg §2",
    "bafa_lksg_direct_supplier_assessment": "lksg §6(4)",
    "bafa_lksg_indirect_supplier_requirements": "lksg §9",
    "bafa_lksg_policy_statement": "lksg §6(2)",
    "bafa_lksg_complaints_mechanism": "lksg §8",
    "bafa_lksg_preventive_measures": "lksg §6",
    "bafa_lksg_remediation": "lksg §7",
    "bafa_lksg_reporting": "lksg §10",
    "bafa_lksg_enforcement": "lksg §13",
    "bafa_lksg_environmental_due_diligence": "lksg §2(3)",
    "bafa_lksg_sme_guidance": "lksg §3(2)",
    "bafa_lksg_documentation": "lksg §10(2)",
    "bafa_lksg_2024_update": "lksg §1",
    # bafa_lksg_sector_specific intentionally left untagged -- no single
    # clean statute citation, forcing one would be dishonest.
}

GWG_MAP = {
    "bafin_gwg_obligated_entities": "gwg §2",
    "bafin_gwg_risk_analysis_sec5": "gwg §5",
    "bafin_gwg_standard_cdd_sec10": "gwg §10",
    "bafin_gwg_beneficial_owner_sec3_sec19": "gwg §3",
    "bafin_gwg_pep_requirements": "gwg §13",
    "bafin_gwg_enhanced_cdd_sec15": "gwg §15",
    "bafin_gwg_simplified_cdd_sec14": "gwg §14",
    "bafin_gwg_sar_reporting_sec43": "gwg §43",
    "bafin_gwg_record_keeping_sec8": "gwg §8",
    # bafin_gwg_internal_safeguards_sec6 is handled separately below (split)
    "bafin_gwg_real_estate_specifics": "gwg §2",
    "bafin_gwg_crypto_vasps": "gwg §2",
    "bafin_gwg_penalties": "gwg §56",
}


def fix_first_lines(path: Path, mapping: dict[str, str]) -> int:
    text = path.read_text(encoding="utf-8")
    blocks = text.split("---")
    changed = 0
    new_blocks = []
    for block in blocks:
        stripped_lines = block.split("\n")
        # find first non-empty line
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
    n1 = fix_first_lines(ROOT / "lksg" / "bafa_lksg_guidance_expanded.txt", LKSG_MAP)
    print(f"LkSG: retagged {n1} / {len(LKSG_MAP)} blocks")
    n2 = fix_first_lines(ROOT / "gwg" / "bafin_gwg_guidance_expanded.txt", GWG_MAP)
    print(f"GwG: retagged {n2} / {len(GWG_MAP)} blocks")
