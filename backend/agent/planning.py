"""
Steps 2-5 of the analysis pipeline.

  determine_applicability(profile)                     — Step 2: threshold check
  retrieve_regulatory_context(profile, applicability)  — Step 3: RAG per regulation
  run_gap_analysis(profile, chunks, failures)          — Step 4: LLM gap analysis
  generate_action_plan(profile, gaps, failures)        — Step 5: LLM action plan
  compute_deterministic_score(gaps, missing_fields)    — deterministic score formula
"""
import json
import logging
import re
from functools import lru_cache

import anthropic

from config import settings
from models.company_profile import EnrichedCompanyProfile
from models.compliance_report import (
    ActionItem,
    ComplianceGap,
    RegulationApplicability,
    RegulatoryChunk,
)
from models.enums import ComplianceStatus, ObligationType, Priority, Regulation
from agent.obligations import get_obligations
from rag.company_ingest import retrieve_company_docs
from rag.prompts import SYSTEM_PERSONA, action_plan_prompt, gap_analysis_prompt
from rag.retrieval import deduplicate, retrieve as _retrieve_chroma, retrieve_pgvector, rerank_cross_encoder
from services.threshold_engine import determine_applicable_regulations

logger = logging.getLogger(__name__)


def retrieve(query: str, regulations: list[str], top_k: int | None = None) -> list[dict]:
    """Static-regulation retrieval entry point used by this module.

    Dispatches to pgvector or ChromaDB per settings.pgvector_retrieval_enabled
    (pgvector migration Phase 4 cutover) — see config.py for the eval-gate
    numbers behind the default. rag.retrieval.retrieve/retrieve_pgvector stay
    independently importable so eval scripts can still diff both backends
    directly.

    Falls back to ChromaDB when no DATABASE_URL is configured — local dev
    and fresh clones have historically never needed Postgres for retrieval
    (see .dev-notes.md's ChromaDB-only setup_data.py flow), and this flag
    flipping to true shouldn't force that requirement on them.
    """
    if settings.pgvector_retrieval_enabled and settings.database_url:
        return retrieve_pgvector(query, regulations, top_k)
    return _retrieve_chroma(query, regulations, top_k)

_RE_CITATION = re.compile(r"^(§|Art(ikel|\.)?)\s*\d|^ESRS\s+\S")

# Extracts bare section/article numbers from a citation string, e.g.
# "§ 7 GwG" -> {"7"}, "§§ 4-5 GwG" -> {"4", "5"}, "Art. 6-7 DSGVO" -> {"6", "7"}.
_RE_CITATION_NUM = re.compile(r"(?:§§?|Art(?:ikel|\.)?)\s*(\d+[a-z]?)(?:\s*-\s*(\d+[a-z]?))?", re.IGNORECASE)

# ESRS citations use their own code system (e.g. "ESRS E1", "ESRS 1"), not
# §/Art numbers — matched and namespaced separately so "ESRS 1" can never
# collide with an unrelated bare "§ 1"/"Art. 1" citation.
_RE_ESRS_CODE = re.compile(r"ESRS\s+([A-Za-z]?\d+)", re.IGNORECASE)


def _citation_numbers(text: str) -> set[str]:
    numbers: set[str] = set()
    for m in _RE_CITATION_NUM.finditer(text):
        numbers.add(m.group(1).lower())
        if m.group(2):
            numbers.add(m.group(2).lower())
    for m in _RE_ESRS_CODE.finditer(text):
        numbers.add("esrs" + m.group(1).lower())
    return numbers

_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


# ── Deterministic score formula ───────────────────────────────────────────────

def compute_deterministic_score(
    gaps: list[ComplianceGap],
    missing_required_fields: int = 0,
) -> float:
    """
    Deterministic compliance score starting at 100, deducting for each gap.

    Deductions:
      CRITICAL + NON_COMPLIANT:           -20
      HIGH + NON_COMPLIANT:               -12
      MEDIUM + NON_COMPLIANT:             -6
      LOW + NON_COMPLIANT:                -2
      Any NON_COMPLIANT + LOW confidence: extra -3
      CANNOT_ASSESS (genuine, not missing-field): -4
      Each missing_required_field (capped at 5): -5

    Floor: 0.
    """
    _deduct_by_priority = {
        Priority.CRITICAL: 20,
        Priority.HIGH: 12,
        Priority.MEDIUM: 6,
        Priority.LOW: 2,
    }

    score = 100.0
    for gap in gaps:
        if gap.status == ComplianceStatus.NON_COMPLIANT:
            deduction = _deduct_by_priority.get(gap.priority, 6)
            score -= deduction
            # Extra penalty for low confidence — indicates the finding may understate the problem
            if getattr(gap, "confidence", "HIGH") == "LOW":
                score -= 3
        elif gap.status == ComplianceStatus.CANNOT_ASSESS:
            score -= 4

    # Missing required fields — each one means we couldn't fully assess a regulation
    capped_missing = min(missing_required_fields, 5)
    score -= capped_missing * 5

    return max(0.0, round(score, 1))


def compute_regulation_deterministic_score(
    regulation_gaps: list[ComplianceGap],
    missing_required_fields: int = 0,
) -> float:
    """Same formula applied to a single regulation's gaps."""
    return compute_deterministic_score(regulation_gaps, missing_required_fields)


@lru_cache(maxsize=1)
def _async_llm_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=settings.llm_api_key)


# ── Step 2 ────────────────────────────────────────────────────────────────────

def determine_applicability(
    profile: EnrichedCompanyProfile,
) -> list[RegulationApplicability]:
    """Deterministic regulation applicability — never delegates to an LLM.

    Runs the RuleEngine first to collect per-regulation applicability results,
    missing fields, and confidence grades.  The rule results are logged for
    audit purposes; the threshold_engine's RegulationApplicability list is
    returned so the rest of the pipeline remains unchanged.
    """
    from agent.rule_engine import RuleEngine, RULE_ENGINE_VERSION

    engine = RuleEngine()
    rule_results = engine.check_all(profile)

    # Log rule engine results for observability
    for reg_key, result in rule_results.items():
        if result.missing_fields:
            logger.info(
                "rule_engine (%s) %s: applies=%s confidence=%s missing=%s",
                RULE_ENGINE_VERSION,
                reg_key,
                result.applies,
                result.confidence,
                result.missing_fields,
            )
        else:
            logger.debug(
                "rule_engine (%s) %s: applies=%s confidence=%s",
                RULE_ENGINE_VERSION,
                reg_key,
                result.applies,
                result.confidence,
            )

    return determine_applicable_regulations(profile)


# ── Deterministic overall score with missing-field penalty ────────────────────

def compute_overall_deterministic_score(
    profile: EnrichedCompanyProfile,
    gaps: list[ComplianceGap],
) -> float:
    """
    Compute the overall compliance score using the deterministic formula in
    compute_deterministic_score(), incorporating missing required fields from
    the rule engine as an additional penalty.

    Call this in place of any LLM-computed or simple average score to ensure
    reproducible results.
    """
    from agent.rule_engine import RuleEngine

    engine = RuleEngine()
    rule_results = engine.check_all(profile)

    total_missing = sum(
        len(r.missing_fields)
        for r in rule_results.values()
        if r.applies
    )

    return compute_deterministic_score(gaps, missing_required_fields=total_missing)


# ── Missing info summary ───────────────────────────────────────────────────────

def missing_info_summary(profile: EnrichedCompanyProfile) -> list[str]:
    """
    Return a human-readable list of missing profile fields and the regulations
    they affect.  Used to populate the "Missing Information" section of the report.

    Each entry is a string like:
      "annual_energy_consumption_mwh is missing — affects: enefg"
    """
    from agent.rule_engine import RuleEngine

    engine = RuleEngine()
    missing_by_reg = engine.get_all_missing_fields(profile)

    # Invert: field -> [regulation, ...]
    field_to_regs: dict[str, list[str]] = {}
    for reg_key, fields in missing_by_reg.items():
        for f in fields:
            field_to_regs.setdefault(f, []).append(reg_key)

    summary: list[str] = []
    for field_name in sorted(field_to_regs):
        regs = ", ".join(sorted(field_to_regs[field_name]))
        summary.append(
            f"{field_name} is missing — affects: {regs}"
        )
    return summary


# ── Step 3 ────────────────────────────────────────────────────────────────────

def retrieve_regulatory_context(
    profile: EnrichedCompanyProfile,
    applicability: list[RegulationApplicability],
) -> tuple[list[RegulatoryChunk], list[str], list[str]]:
    """RAG retrieval for each applicable regulation, deduplicated and capped per-regulation.

    Returns (chunks, empty_regulations, low_confidence_regulations) where:
      - empty_regulations: zero chunks after both attempts → CANNOT_ASSESS
      - low_confidence_regulations: 1-4 chunks → analysis proceeds but flagged for manual review
    """
    applicable = [a for a in applicability if a.applies]
    if not applicable:
        return [], [], []

    all_chunks: list[RegulatoryChunk] = []
    empty_regulations: list[str] = []
    low_confidence_regulations: list[str] = []

    for reg_app in applicable:
        reg_key = reg_app.regulation.value
        query = _build_query(profile, reg_app.regulation)
        raw = retrieve(query, [reg_key], top_k=15)

        if len(raw) < 5:
            broader = f"{reg_key} compliance obligations requirements Germany SME"
            raw = retrieve(broader, [reg_key], top_k=15)

        if len(raw) == 0:
            logger.warning(
                "step 3: ZERO chunks for %s — knowledge base not populated. "
                "Marking as CANNOT_ASSESS, bypassing LLM gap analysis for this regulation.",
                reg_key,
            )
            empty_regulations.append(reg_key)
            continue
        elif len(raw) < 5:
            logger.warning(
                "step 3: only %d chunks for %s after retry (expected >= 5) — "
                "flagging for manual review",
                len(raw), reg_key,
            )
            low_confidence_regulations.append(reg_key)

        # Obligation-driven augmentation: additive, never replaces generic raw.
        # get_obligations() returns [] for any regulation without a registry
        # entry — clean no-op fallback there.
        obligations = get_obligations(reg_key)
        obligation_chunks: list[dict] = []
        for ob in obligations:
            ob_query = f"{ob.article} {ob.title}"
            ob_candidates = retrieve(ob_query, [reg_key], top_k=8)
            # Prefer the chunk whose article_number is the exact statute this
            # obligation cites, over just any statute-formatted chunk. On small
            # collections a handful of broad/foundational articles (e.g. gwg's
            # § 1 "Begriffsbestimmungen") semantically dominate nearly every
            # query in that collection, crowding out the actually-cited article
            # (e.g. § 7) from the top of a purely-semantic ranking even though
            # it's present in the corpus — exact citation-number matching
            # sidesteps that by looking it up directly instead of hoping
            # semantic similarity favours it.
            target_numbers = _citation_numbers(ob.article)
            exact_hits = [
                c for c in ob_candidates
                if target_numbers & _citation_numbers(c.get("article_number", ""))
            ][:3]
            # Fallback: prefer chunks with a real statute citation (§ N / Artikel
            # N) over guidance-slug chunks (e.g. "bafa_lksg_risk_analysis_
            # methodology") — explanatory guidance prose tends to outrank terse
            # law text in semantic search, which would defeat the point of an
            # obligation-targeted lookup (guaranteeing the actual law text is
            # present). Citation format, not document_type, drives this: even
            # correctly-labeled "law" chunks (e.g. ESRS-style references) don't
            # always carry a § N/Artikel N citation.
            law_hits = [c for c in ob_candidates if _RE_CITATION.match(c.get("article_number", ""))][:3]
            obligation_chunks.extend(exact_hits or law_hits or ob_candidates[:3])

        # Rerank the generic pool on its own, capped at 5 (today's baseline
        # behaviour). Obligation-targeted law chunks are deliberately NOT run
        # through this rerank — reranking against the single generic per-
        # regulation query would re-bury them under guidance text for the same
        # reason the per-obligation query needed the citation preference above,
        # defeating the guarantee this augmentation exists to provide.
        deduped_generic = deduplicate(raw)
        reranked_generic = rerank_cross_encoder(query, deduped_generic, top_n=5)

        # deduplicate() returns results sorted by score descending, so this cap
        # keeps the highest-scoring distinct articles and bounds gap-analysis
        # prompt growth (mirrors the original flat-cap ceiling).
        deduped_obligation = deduplicate(obligation_chunks)[:15]
        combined = deduplicate(reranked_generic + deduped_obligation)

        all_chunks.extend(_to_models(combined))
        logger.debug(
            "step 3: %s — %d chunks selected (%d generic + %d obligation-augmented, deduped)",
            reg_key, len(combined), len(reranked_generic), len(deduped_obligation),
        )

    return all_chunks, empty_regulations, low_confidence_regulations


# ── Step 4 ────────────────────────────────────────────────────────────────────

async def run_gap_analysis(
    profile: EnrichedCompanyProfile,
    chunks: list[RegulatoryChunk],
    failures: list[str],
    job_id: str = "",
    empty_regulations: list[str] | None = None,
) -> list[ComplianceGap]:
    """LLM gap analysis, processed per regulation. Includes company doc evidence when available.

    Regulations in empty_regulations had zero KB chunks — they receive a hard CANNOT_ASSESS
    finding without calling the LLM, preventing ungrounded legal citation hallucination.
    """
    by_reg: dict[str, list[RegulatoryChunk]] = {}
    for chunk in chunks:
        by_reg.setdefault(chunk.regulation.value, []).append(chunk)

    profile_json = profile.model_dump_json(indent=2)
    all_gaps: list[ComplianceGap] = []

    # Hard CANNOT_ASSESS for regulations with empty knowledge base — never delegate to LLM
    for reg_key in (empty_regulations or []):
        logger.info("step 4: %s has empty KB — adding CANNOT_ASSESS without LLM call", reg_key)
        all_gaps.append(ComplianceGap(
            regulation=_reg_from_key(reg_key),
            article_number="KB-EMPTY",
            article_title="Knowledge base not populated",
            status=ComplianceStatus.CANNOT_ASSESS,
            priority=Priority.MEDIUM,
            evidence=(
                f"The regulatory knowledge base for {reg_key} has not been indexed. "
                f"Gap analysis requires retrieved legal text to produce article-level findings — "
                f"generating findings without source text would risk hallucinated citations. "
                f"Run the ingestion pipeline to populate this regulation's collection, "
                f"then re-run this analysis."
            ),
            deficiency_description=(
                f"Compliance screening for {reg_key} is incomplete. "
                f"Rerun analysis after knowledge base ingestion."
            ),
        ))

    for reg_key, reg_chunks in by_reg.items():
        chunks_json = _chunks_to_json(reg_chunks)

        company_docs_json = ""
        if job_id:
            query = _build_query(profile, _reg_from_key(reg_key))
            doc_chunks = retrieve_company_docs(job_id, query, top_k=6)
            if doc_chunks:
                company_docs_json = _doc_chunks_to_json(doc_chunks)

        prompt = gap_analysis_prompt(
            profile_json, chunks_json, company_docs_json,
            inferred_assumptions=getattr(profile, "inferred_assumptions", []),
        )
        gaps = await _async_llm_call(
            prompt, _parse_gaps, f"gap_analysis:{reg_key}", failures, max_tokens=8192,
            tool=_TOOL_GAP_ANALYSIS, tool_result_key="gaps",
        )

        # Attach Rechtsstand from the matching source chunk — not requested from
        # the LLM; the model only echoes article_number, so look it up ourselves.
        legal_dates = {c.article_number: c.legal_version_date for c in reg_chunks if c.legal_version_date}
        for gap in gaps:
            gap.legal_version_date = legal_dates.get(gap.article_number)

        if reg_chunks and not gaps:
            # The prompt instructs the model to assess EVERY retrieved requirement
            # chunk, so a genuinely empty result here is never legitimate "full
            # compliance" — it's the same silent-empty-success failure mode as the
            # max_tokens truncation case above, just via a call that didn't raise.
            # Left unflagged, it renders only as a passive total_requirements=0
            # state on the report (see _compute_scores) instead of an active
            # manual-review item.
            msg = (
                f"gap analysis for {reg_key} returned zero findings despite "
                f"{len(reg_chunks)} retrieved chunk(s) — likely a generation failure, "
                f"not genuine full compliance; flagged for manual review"
            )
            logger.warning("step 4: %s", msg)
            failures.append(msg)

        all_gaps.extend(gaps)

    return all_gaps


# ── Step 5 ────────────────────────────────────────────────────────────────────

_ACTION_PLAN_BATCH_SIZE = 20
_ACTION_PLAN_TOKEN_LIMIT = 50_000  # ~200k chars; above this we batch


async def generate_action_plan(
    profile: EnrichedCompanyProfile,
    gaps: list[ComplianceGap],
    failures: list[str],
) -> list[ActionItem]:
    """LLM action plan for every NON_COMPLIANT and PARTIALLY_COMPLIANT gap."""
    actionable = [
        g for g in gaps
        if g.status in (ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT)
    ]
    if not actionable:
        return []

    profile_json = profile.model_dump_json(indent=2)
    gaps_json = json.dumps([g.model_dump() for g in actionable], indent=2, default=str)

    # Batch if the input prompt would be too large (~4 chars/token), OR if the
    # number of actionable items alone risks truncating the *output* — each
    # detailed action item runs ~250-300 tokens, so an unbatched call for
    # dozens of items can silently hit max_tokens mid-generation. When Anthropic
    # truncates a forced tool_choice call this way, the SDK can still yield a
    # structurally valid but empty/partial tool result with no error raised,
    # so this isn't just an input-size problem — it also needs an item-count
    # cap independent of how verbose the gap evidence text happens to be.
    if len(gaps_json) // 4 > _ACTION_PLAN_TOKEN_LIMIT or len(actionable) > _ACTION_PLAN_BATCH_SIZE:
        logger.info(
            "generate_action_plan: %d gaps — batching in groups of %d",
            len(actionable), _ACTION_PLAN_BATCH_SIZE,
        )
        all_actions: list[ActionItem] = []
        for i in range(0, len(actionable), _ACTION_PLAN_BATCH_SIZE):
            batch = actionable[i : i + _ACTION_PLAN_BATCH_SIZE]
            batch_json = json.dumps([g.model_dump() for g in batch], indent=2, default=str)
            prompt = action_plan_prompt(profile_json, batch_json)
            batch_actions = await _async_llm_call(
                prompt, _parse_actions, f"action_plan_batch_{i}", failures, max_tokens=8192,
                tool=_TOOL_ACTION_PLAN, tool_result_key="actions",
            )
            if batch and not batch_actions:
                msg = (
                    f"action plan batch {i}//{_ACTION_PLAN_BATCH_SIZE} returned zero items "
                    f"for {len(batch)} actionable gap(s) — likely a generation failure, "
                    f"flagged for manual review"
                )
                logger.warning("step 5: %s", msg)
                failures.append(msg)
            all_actions.extend(batch_actions)
        return sorted(all_actions, key=lambda a: _PRIORITY_ORDER.get(a.priority, 4))

    prompt = action_plan_prompt(profile_json, gaps_json)
    actions = await _async_llm_call(
        prompt, _parse_actions, "action_plan", failures, max_tokens=8192,
        tool=_TOOL_ACTION_PLAN, tool_result_key="actions",
    )
    if actionable and not actions:
        # Same rationale as run_gap_analysis's zero-findings guard: every
        # actionable gap should produce at least one action item, so an empty
        # result from a call that didn't raise is a silent failure, not a
        # legitimate "nothing to do" outcome.
        msg = (
            f"action plan returned zero items for {len(actionable)} actionable gap(s) "
            f"— likely a generation failure, flagged for manual review"
        )
        logger.warning("step 5: %s", msg)
        failures.append(msg)

    return sorted(actions, key=lambda a: _PRIORITY_ORDER.get(a.priority, 4))


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_query(profile: EnrichedCompanyProfile, regulation: Regulation) -> str:
    base = f"{profile.industry} company {profile.employee_count} employees Germany"
    if regulation == Regulation.GDPR:
        extras = []
        if profile.processes_special_category_data:
            extras.append("special category data Art. 9")
        if not profile.has_processing_records:
            extras.append("records of processing activities Art. 30")
        if not profile.has_dpo:
            extras.append("data protection officer")
        return f"GDPR DSGVO compliance obligations {base} {' '.join(extras)}"
    if regulation == Regulation.LKSG:
        countries = (
            ", ".join(profile.supply_chain_countries[:5])
            if profile.supply_chain_countries
            else "abroad"
        )
        return f"LkSG supply chain due diligence {base} suppliers {countries}"
    if regulation == Regulation.ENEFG:
        energy = (
            f"{profile.annual_energy_consumption_mwh} MWh"
            if profile.annual_energy_consumption_mwh
            else ""
        )
        return f"EnEfG energy efficiency audit management {base} {energy}"
    if regulation == Regulation.CSRD:
        return f"CSRD sustainability reporting ESG disclosure {base}"
    if regulation == Regulation.BDSG:
        return f"BDSG Bundesdatenschutzgesetz data protection {base}"
    if regulation == Regulation.NIS2:
        entity = "besonders wichtige Einrichtung" if profile.employee_count >= 250 else "wichtige Einrichtung"
        return f"NIS2 BSIG cybersecurity risk management incident reporting {entity} {base}"
    if regulation == Regulation.AI_ACT:
        return f"EU AI Act high-risk AI system deployer transparency human oversight obligations {base}"
    if regulation == Regulation.HINSCHG:
        return f"HinSchG Hinweisgeberschutzgesetz whistleblower internal reporting channel {base}"
    if regulation == Regulation.ARBSCHG:
        return (
            f"ArbSchG ArbZG MuSchG JArbSchG BUrlG BBiG AEntG workplace law "
            f"Gefaehrdungsbeurteilung risk assessment working time employee protection {base}"
        )
    if regulation == Regulation.AGG:
        return f"AGG Gleichbehandlung anti-discrimination employer obligations complaints {base}"
    if regulation == Regulation.MILOG:
        return f"MiLoG Mindestlohn minimum wage documentation working time records {base}"
    return f"{regulation.value} compliance obligations {base}"


_REG_ALIASES: dict[str, str] = {
    "gdpr": "gdpr_dsgvo",  # ChromaDB metadata uses short key; enum uses full key
}


def _to_models(chunks: list[dict]) -> list[RegulatoryChunk]:
    result = []
    for c in chunks:
        try:
            raw_applicable = c.get("applicable_to", [])
            if isinstance(raw_applicable, str):
                try:
                    raw_applicable = json.loads(raw_applicable)
                except json.JSONDecodeError:
                    raw_applicable = [raw_applicable] if raw_applicable else []

            reg_val = c.get("regulation", "")
            reg_val = _REG_ALIASES.get(reg_val, reg_val)

            # Normalise ObligationType: fall back to MUST for unknown values
            ob_raw = c.get("obligation_type", ObligationType.MUST.value)
            try:
                ob_type = ObligationType(ob_raw)
            except ValueError:
                ob_type = ObligationType.MUST

            result.append(RegulatoryChunk(
                regulation=Regulation(reg_val),
                article_number=c.get("article_number", ""),
                title=c.get("title", ""),
                text=c.get("text", ""),
                obligation_type=ob_type,
                applicable_to=raw_applicable,
                threshold=c.get("threshold"),
                source_url=c.get("source_url"),
                document_type=c.get("document_type", "law"),
                legal_version_date=c.get("legal_version_date") or None,
            ))
        except Exception as exc:
            logger.warning("could not parse retrieval chunk: %s", exc)
    return result


def _reg_from_key(reg_key: str) -> Regulation:
    try:
        return Regulation(reg_key)
    except ValueError:
        logger.warning("_reg_from_key: unknown regulation key %r — falling back to GDPR", reg_key)
        return Regulation.GDPR


def _doc_chunks_to_json(chunks: list[dict]) -> str:
    from rag.prompts import _sanitize
    parts = []
    for c in chunks:
        safe_text   = _sanitize(c.get("text", ""), max_len=800)
        safe_source = _sanitize(c.get("source", "uploaded document"), max_len=100)
        parts.append(
            f"[Level 3 — Company document (evidence only, not legal authority) | "
            f"Source: {safe_source}]\n{safe_text}"
        )
    return "\n\n---\n\n".join(parts)


_SOURCE_AUTHORITY: dict[str, str] = {
    "law":      "Level 1 — Official law text (binding)",
    "guidance": "Level 2 — Regulatory guidance (authoritative interpretation)",
}


def _chunks_to_json(chunks: list[RegulatoryChunk]) -> str:
    return json.dumps(
        [
            {
                "source_authority": _SOURCE_AUTHORITY.get(c.document_type, "Level 1 — Official law text (binding)"),
                "regulation": c.regulation.value,
                "article_number": c.article_number,
                "title": c.title,
                "text": c.text[:2000],
                "obligation_type": c.obligation_type.value,
                "threshold": c.threshold,
            }
            for c in chunks
        ],
        indent=2,
    )


# ── Tool schemas for structured output ───────────────────────────────────────
# Using Anthropic tool use instead of text parsing eliminates the need for
# _strip_fences() and guarantees valid, schema-conformant JSON output.

_TOOL_GAP_ANALYSIS = {
    "name": "submit_gap_analysis",
    "description": "Submit the compliance gap analysis results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "regulation":             {"type": "string"},
                        "article_number":         {"type": "string"},
                        "article_title":          {"type": "string"},
                        "status":                 {"type": "string", "enum": ["COMPLIANT","PARTIALLY_COMPLIANT","NON_COMPLIANT","CANNOT_ASSESS"]},
                        "evidence":               {"type": "string"},
                        "deficiency_description": {"type": "string"},
                        "evidence_quote":         {"type": "string", "description": "For VERIFIED findings: verbatim sentence from the retrieved chunk supporting this finding. Omit for SELF-REPORTED or CANNOT_ASSESS findings."},
                    },
                    "required": ["regulation","article_number","article_title","status","evidence"],
                },
            }
        },
        "required": ["gaps"],
    },
}

_TOOL_ACTION_PLAN = {
    "name": "submit_action_plan",
    "description": "Submit the prioritized compliance action plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "regulation":       {"type": "string"},
                        "article_number":   {"type": "string"},
                        "action":           {"type": "string"},
                        "priority":         {"type": "string", "enum": ["CRITICAL","HIGH","MEDIUM","LOW"]},
                        "estimated_effort": {"type": "string"},
                        "deadline":         {"type": ["string", "null"]},
                        "dependencies":     {"type": "array", "items": {"type": "string"}},
                        "gap_reference":    {"type": "string"},
                    },
                    "required": ["regulation","article_number","action","priority","estimated_effort","gap_reference"],
                },
            }
        },
        "required": ["actions"],
    },
}


async def _async_llm_call(
    prompt: str,
    parse_fn,
    step_name: str,
    failures: list[str],
    max_tokens: int = 4096,
    tool: dict | None = None,
    tool_result_key: str | None = None,
    model: str | None = None,
    system: str | None = None,
) -> list:
    """
    Async LLM call with structured output parsing.

    When `tool` is provided the call uses Anthropic tool use — the model is
    forced to return data matching the tool's JSON schema, eliminating manual
    fence-stripping and json.loads() fragility.  The structured dict at
    `tool_result_key` is serialised back to a JSON string so that `parse_fn`
    (which expects a JSON string) remains unchanged.

    `model`/`system` default to the main analysis model and persona — pass
    overrides for lightweight auxiliary checks (e.g. a cheap verification
    pass) that shouldn't use the main model or its German compliance-consultant
    system prompt.
    """
    import asyncio
    if not settings.llm_api_key:
        logger.warning("%s: no LLM API key configured, skipping", step_name)
        failures.append(step_name)
        return []

    last_exc: Exception | None = None
    max_attempts = settings.llm_max_retries + 1
    for attempt in range(max_attempts):
        try:
            kwargs: dict = dict(
                model=model or settings.llm_model,
                max_tokens=max_tokens,
                temperature=0,
                system=system if system is not None else SYSTEM_PERSONA,
                messages=[{"role": "user", "content": prompt}],
            )
            if tool:
                kwargs["tools"] = [tool]
                kwargs["tool_choice"] = {"type": "tool", "name": tool["name"]}

            response = await _async_llm_client().messages.create(**kwargs)

            if tool and tool_result_key:
                tool_block = next(
                    (b for b in response.content if b.type == "tool_use"),
                    None,
                )
                if tool_block is None:
                    raise ValueError("model did not return a tool_use block")
                if response.stop_reason == "max_tokens":
                    # Anthropic can still hand back a structurally valid but
                    # incomplete/empty tool_use block when a forced tool_choice
                    # call is cut off mid-generation - no exception is raised by
                    # the SDK for this. Left alone, that silently looks like a
                    # legitimate empty result (e.g. "zero compliance gaps
                    # found"), which is worse than an error: it reads as a
                    # clean bill of health when nothing was actually analysed.
                    # Route it through the same retry/failure path as a real
                    # API error instead of returning early.
                    raise ValueError(
                        f"response truncated at max_tokens={max_tokens} before "
                        f"completing tool call (partial input: {tool_block.input!r})"
                    )
                raw_list = tool_block.input.get(tool_result_key, [])
                return parse_fn(json.dumps(raw_list))
            else:
                text = response.content[0].text.strip()
                if text.startswith("```"):
                    lines = text.splitlines()
                    end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
                    text = "\n".join(lines[1:end]).strip()
                return parse_fn(text)

        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("%s: parse error attempt %d/%d: %s", step_name, attempt + 1, max_attempts, exc)
            last_exc = exc
        except anthropic.APIError as exc:
            logger.warning("%s: API error attempt %d/%d: %s", step_name, attempt + 1, max_attempts, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("%s: unexpected error attempt %d/%d: %s", step_name, attempt + 1, max_attempts, exc)
            last_exc = exc

        if attempt < max_attempts - 1:
            backoff = 2 ** attempt
            logger.info("%s: retrying in %ds", step_name, backoff)
            await asyncio.sleep(backoff)

    logger.error("%s: all %d attempts failed (%s)", step_name, max_attempts, last_exc)
    failures.append(step_name)
    return []


def _parse_gaps(text: str) -> list[ComplianceGap]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array, got {type(data).__name__}")
    return [
        ComplianceGap(
            regulation=Regulation(item["regulation"]),
            article_number=item["article_number"],
            article_title=item["article_title"],
            status=ComplianceStatus(item["status"]),
            evidence=item["evidence"],
            deficiency_description=item.get("deficiency_description"),
            priority=Priority(item.get("priority", "MEDIUM")),
            evidence_quote=item.get("evidence_quote"),
        )
        for item in data
    ]


def _parse_actions(text: str) -> list[ActionItem]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array, got {type(data).__name__}")
    return [
        ActionItem(
            regulation=Regulation(item["regulation"]),
            article_number=item["article_number"],
            action=item["action"],
            priority=Priority(item["priority"]),
            estimated_effort=item["estimated_effort"],
            deadline=item.get("deadline"),
            dependencies=item.get("dependencies", []),
            gap_reference=item["gap_reference"],
        )
        for item in data
    ]
