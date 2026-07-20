"""
Obligation-coverage evaluation script.

For each regulation in OBLIGATION_REGISTRY, runs retrieve_regulatory_context()
against a representative profile in two modes:
  old  — today's (pre-refactor) generic-query-only retrieval, flat top-5 cap
  new  — obligation-augmented retrieval (agent.planning.retrieve_regulatory_context)

For each obligation, checks whether its cited article number appears among the
returned chunks' article_number for that regulation. Reports per-regulation and
overall coverage %, chunk count, and wall-clock time — old vs new.

Uses a citation-number extractor tailored to this comparison (Obligation.article
uses trailing law-name suffixes like "§ 4 LkSG"; chunk article_number uses bare
"§ 4" or "Artikel 30") rather than eval_retrieval.py's prefix-oriented
_normalise(), which doesn't recognise German "Artikel" or strip suffixes.

Run from backend/:  python scripts/eval_obligation_coverage.py
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.obligations import OBLIGATION_REGISTRY  # noqa: E402
from agent.planning import (  # noqa: E402
    _build_query,
    _to_models,
    retrieve_regulatory_context,
)
from models.company_profile import CompanyProfile, EnrichedCompanyProfile  # noqa: E402
from models.compliance_report import RegulationApplicability  # noqa: E402
from models.enums import Regulation  # noqa: E402
from rag.retrieval import deduplicate, rerank_cross_encoder, retrieve  # noqa: E402

# One representative profile per regulation — picked to plausibly trigger that
# regulation (see tests/conftest.py docstrings for the source of these shapes).
# Not a substitute for the real rule engine — good enough for a retrieval-quality
# comparison, since retrieve_regulatory_context only reads `applies`/`regulation`.
_IT_AGENCY = CompanyProfile(
    company_name="TechBit GmbH", industry="it_software", employee_count=5,
    annual_revenue_eur=400_000, processes_personal_data=True,
    processes_special_category_data=False, processing_is_occasional=False,
    has_supply_chain_abroad=False,
)
_MANUFACTURER = CompanyProfile(
    company_name="MaschBau AG", industry="manufacturing", employee_count=1200,
    annual_revenue_eur=75_000_000, balance_sheet_total_eur=40_000_000,
    processes_personal_data=True, processes_special_category_data=False,
    processing_is_occasional=False, has_supply_chain_abroad=True,
    supply_chain_countries=["CN", "VN", "IN"], annual_energy_consumption_mwh=10_000,
)
_LARGE_LISTED = CompanyProfile(
    company_name="Konzern SE", industry="manufacturing", employee_count=1500,
    annual_revenue_eur=200_000_000, balance_sheet_total_eur=80_000_000,
    processes_personal_data=True, processes_special_category_data=False,
    processing_is_occasional=False, is_listed_company=True,
    has_supply_chain_abroad=True, supply_chain_countries=["CN"],
    annual_energy_consumption_mwh=12_000,
)
_HEALTHCARE = CompanyProfile(
    company_name="MediCare Praxis GmbH", industry="healthcare", employee_count=50,
    annual_revenue_eur=3_000_000, processes_personal_data=True,
    processes_special_category_data=True, processing_is_occasional=False,
)

_PROFILE_MAP: dict[str, CompanyProfile] = {
    "gdpr_dsgvo":     _IT_AGENCY,
    "bdsg":           _IT_AGENCY,
    "agg":            _IT_AGENCY,
    "milog":          _IT_AGENCY,
    "workplace_law":  _IT_AGENCY,
    "ttdsg":          _IT_AGENCY,
    "gwg":            _IT_AGENCY,
    "hinschg":        _HEALTHCARE,
    "nis2":           _LARGE_LISTED,
    "lksg":           _MANUFACTURER,
    "enefg":          _MANUFACTURER,
}


_RE_CITATION_NUM = re.compile(r"(?:§§?|Art(?:ikel|\.)?)\s*(\d+[a-z]?)(?:\s*-\s*(\d+[a-z]?))?", re.IGNORECASE)


def _citation_numbers(text: str) -> set[str]:
    """Extract bare section/article numbers from a citation string, ignoring
    trailing law-name suffixes and Absatz/subsection detail. '§ 4 LkSG' -> {'4'};
    '§§ 4-5 GwG' -> {'4','5'}; 'Art. 30 DSGVO' -> {'30'}; 'Artikel 30' -> {'30'}.
    Returns an empty set for non-citation strings (e.g. guidance slugs like
    'bafa_lksg_risk_analysis_methodology'), which correctly never match."""
    numbers: set[str] = set()
    for m in _RE_CITATION_NUM.finditer(text):
        numbers.add(m.group(1).lower())
        if m.group(2):
            numbers.add(m.group(2).lower())
    return numbers


def _article_match(retrieved_articles: list[str], expected: list[str]) -> bool:
    expected_numbers: set[str] = set()
    for e in expected:
        expected_numbers |= _citation_numbers(e)
    for r in retrieved_articles:
        if _citation_numbers(r) & expected_numbers:
            return True
    return False


def _old_retrieve_regulatory_context(
    profile: EnrichedCompanyProfile,
    applicability: list[RegulationApplicability],
):
    """Pre-refactor logic: generic query only, flat top-5 cap. Inlined here (not
    imported) so this script can compare against the exact behaviour being
    replaced without needing to check out a prior git revision."""
    applicable = [a for a in applicability if a.applies]
    all_chunks = []
    for reg_app in applicable:
        reg_key = reg_app.regulation.value
        query = _build_query(profile, reg_app.regulation)
        raw = retrieve(query, [reg_key], top_k=15)
        if len(raw) < 5:
            broader = f"{reg_key} compliance obligations requirements Germany SME"
            raw = retrieve(broader, [reg_key], top_k=15)
        if len(raw) == 0:
            continue
        deduped = deduplicate(raw)
        reranked = rerank_cross_encoder(query, deduped, top_n=5)
        all_chunks.extend(_to_models(reranked))
    return all_chunks


def run_eval() -> None:
    print(f"\nObligation coverage eval — {len(OBLIGATION_REGISTRY)} regulations\n")
    header = f"{'Regulation':<16} {'Obl.':>5} {'Old cov.':>9} {'New cov.':>9} {'Old chunks':>11} {'New chunks':>11} {'Old s':>7} {'New s':>7}"
    print(header)
    print("-" * len(header))

    old_cov_sum = new_cov_sum = 0.0
    n_regs = 0

    for reg_key, obligations in sorted(OBLIGATION_REGISTRY.items()):
        profile = _PROFILE_MAP.get(reg_key, _IT_AGENCY)
        enriched = EnrichedCompanyProfile(**profile.model_dump())
        applicability = [RegulationApplicability(regulation=Regulation(reg_key), applies=True, reason="eval")]

        t0 = time.perf_counter()
        old_chunks = _old_retrieve_regulatory_context(enriched, applicability)
        old_elapsed = time.perf_counter() - t0

        t0 = time.perf_counter()
        new_chunks, _empty, _low = retrieve_regulatory_context(enriched, applicability)
        new_elapsed = time.perf_counter() - t0

        old_articles = [c.article_number for c in old_chunks]
        new_articles = [c.article_number for c in new_chunks]

        old_hits = sum(1 for ob in obligations if _article_match(old_articles, [ob.article]))
        new_hits = sum(1 for ob in obligations if _article_match(new_articles, [ob.article]))

        old_cov = old_hits / len(obligations) * 100 if obligations else 0.0
        new_cov = new_hits / len(obligations) * 100 if obligations else 0.0

        print(
            f"{reg_key:<16} {len(obligations):>5} {old_cov:>8.0f}% {new_cov:>8.0f}% "
            f"{len(old_chunks):>11} {len(new_chunks):>11} {old_elapsed:>6.1f}s {new_elapsed:>6.1f}s"
        )

        old_cov_sum += old_cov
        new_cov_sum += new_cov
        n_regs += 1

    print("-" * len(header))
    old_avg = old_cov_sum / n_regs if n_regs else 0.0
    new_avg = new_cov_sum / n_regs if n_regs else 0.0
    print(f"{'OVERALL avg':<16} {'':>5} {old_avg:>8.0f}% {new_avg:>8.0f}%")
    print(f"\nObligation-article coverage improved from {old_avg:.0f}% to {new_avg:.0f}% (+{new_avg - old_avg:.0f} pts)\n")


if __name__ == "__main__":
    run_eval()
