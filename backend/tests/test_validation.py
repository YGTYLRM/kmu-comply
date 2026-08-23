"""
Tests for agent/validation.py, focused on the entailment check
(verify_evidence_entailment) added on top of the existing string-match
evidence_quote check (check_evidence_quotes).

Fast tests mock the LLM call. The -m integration test hits the real Haiku
model to validate the prompt actually distinguishes supporting vs.
contradicting quotes — skipped by default in CI to avoid LLM API costs.
"""
import pytest

from agent.validation import verify_evidence_entailment
from models.compliance_report import ComplianceGap
from models.enums import ComplianceStatus, Regulation


def _gap(status=ComplianceStatus.NON_COMPLIANT, confidence="HIGH", quote="some quote text here") -> ComplianceGap:
    return ComplianceGap(
        regulation=Regulation.GDPR,
        article_number="Art. 30",
        article_title="Verzeichnis von Verarbeitungstätigkeiten",
        status=status,
        evidence="evidence text",
        evidence_quote=quote,
        confidence=confidence,
    )


class TestEligibilityFiltering:
    """Fast, no-LLM tests for which gaps get sent to the entailment check at all."""

    async def test_skips_when_no_eligible_gaps(self):
        gaps = [
            _gap(quote=None),                                   # no quote
            _gap(confidence="LOW"),                              # already LOW
            _gap(status=ComplianceStatus.CANNOT_ASSESS),         # CANNOT_ASSESS
        ]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        assert warnings == []
        # None of the gaps should have been touched
        for g in gaps:
            assert g.confidence in ("HIGH", "LOW")

    async def test_no_llm_key_fails_open(self, monkeypatch):
        from config import settings
        monkeypatch.setattr(settings, "llm_api_key", "")
        gaps = [_gap()]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        # Missing key must not raise, must not downgrade confidence, must not
        # propagate into the caller's failures list — this is a best-effort
        # safety net, not a required pipeline step.
        assert warnings == []
        assert gaps[0].confidence == "HIGH"


class TestVerdictApplication:
    """Fast tests for how LLM verdicts get applied, with the LLM call mocked."""

    async def test_contradicts_downgrades_to_low(self, monkeypatch):
        async def fake_call(*args, **kwargs):
            return [{"gap_index": 0, "verdict": "CONTRADICTS", "reason": "quote says the opposite"}]

        monkeypatch.setattr("agent.planning._async_llm_call", fake_call)
        gaps = [_gap()]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        assert len(warnings) == 1
        assert gaps[0].confidence == "LOW"
        assert "quote says the opposite" in gaps[0].confidence_reason

    async def test_supports_leaves_confidence_untouched(self, monkeypatch):
        async def fake_call(*args, **kwargs):
            return [{"gap_index": 0, "verdict": "SUPPORTS", "reason": "quote matches"}]

        monkeypatch.setattr("agent.planning._async_llm_call", fake_call)
        gaps = [_gap()]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        assert warnings == []
        assert gaps[0].confidence == "HIGH"

    async def test_llm_failure_does_not_downgrade(self, monkeypatch):
        async def fake_call(prompt, parse_fn, step_name, failures, **kwargs):
            failures.append(step_name)  # simulate _async_llm_call's own failure path
            return []

        monkeypatch.setattr("agent.planning._async_llm_call", fake_call)
        gaps = [_gap()]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        assert warnings == []
        assert gaps[0].confidence == "HIGH"


@pytest.mark.integration
class TestEntailmentIntegration:
    """Real LLM calls — validates the prompt itself, not just the wiring."""

    async def test_contradicting_quote_detected(self):
        gaps = [_gap(
            status=ComplianceStatus.NON_COMPLIANT,
            quote="Micro-enterprises with fewer than 10 employees are exempt from this requirement.",
        )]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        assert len(warnings) == 1
        assert gaps[0].confidence == "LOW"

    async def test_supporting_quote_passes(self):
        gaps = [_gap(
            status=ComplianceStatus.NON_COMPLIANT,
            quote="Controllers shall maintain a record of processing activities under their responsibility.",
        )]
        warnings = await verify_evidence_entailment(gaps, failures=[])
        assert warnings == []
        assert gaps[0].confidence == "HIGH"
