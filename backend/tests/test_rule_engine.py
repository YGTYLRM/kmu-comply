"""
Golden-profile regression tests for the RuleEngine.

Loads tests/golden_profiles/profiles.json, instantiates each as a CompanyProfile,
runs RuleEngine().check_all(), and asserts expected applicability for each regulation.

Prints a summary table at the end showing pass/fail per scenario.

Run: pytest tests/test_rule_engine.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure backend package root is on the path regardless of working directory
_BACKEND_ROOT = Path(__file__).parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from agent.rule_engine import RuleEngine, RULE_ENGINE_VERSION
from models.company_profile import CompanyProfile

_PROFILES_FILE = Path(__file__).parent / "golden_profiles" / "profiles.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def raw_profiles() -> list[dict]:
    """Load golden profiles from JSON once per test session."""
    assert _PROFILES_FILE.exists(), f"Golden profiles file not found: {_PROFILES_FILE}"
    with _PROFILES_FILE.open(encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, list), "profiles.json must be a JSON array"
    return data


def _build_profile(raw: dict) -> CompanyProfile:
    """Strip test-only metadata keys and instantiate a CompanyProfile."""
    skip_keys = {"scenario_description", "expected_applicable", "expected_not_applicable"}
    profile_data = {k: v for k, v in raw.items() if k not in skip_keys}
    return CompanyProfile(**profile_data)


# ---------------------------------------------------------------------------
# Parametrised test
# ---------------------------------------------------------------------------

def _profile_ids(raw_profiles: list[dict]) -> list[str]:
    return [
        f"[{i+1:02d}] {p.get('scenario_description', 'unnamed')[:60]}"
        for i, p in enumerate(raw_profiles)
    ]


def pytest_generate_tests(metafunc):
    """Dynamically parametrize test_golden_profile with loaded profiles."""
    if "profile_entry" in metafunc.fixturenames:
        profiles_path = _PROFILES_FILE
        if profiles_path.exists():
            with profiles_path.open(encoding="utf-8") as fh:
                raw = json.load(fh)
            ids = [
                f"[{i+1:02d}] {p.get('scenario_description', 'unnamed')[:60]}"
                for i, p in enumerate(raw)
            ]
            metafunc.parametrize("profile_entry", raw, ids=ids)


def test_golden_profile(profile_entry: dict) -> None:
    """Assert that the RuleEngine correctly determines applicability for each golden profile."""
    profile = _build_profile(profile_entry)
    engine = RuleEngine()
    results = engine.check_all(profile)

    expected_applicable = profile_entry.get("expected_applicable", [])
    expected_not_applicable = profile_entry.get("expected_not_applicable", [])
    scenario = profile_entry.get("scenario_description", "unnamed")

    failures: list[str] = []

    for reg_key in expected_applicable:
        result = results.get(reg_key)
        if result is None:
            failures.append(f"MISSING regulation key in results: {reg_key!r}")
        elif not result.applies:
            failures.append(
                f"Expected {reg_key!r} to APPLY but got applies=False "
                f"(confidence={result.confidence}, reason={result.reason!r})"
            )

    for reg_key in expected_not_applicable:
        result = results.get(reg_key)
        if result is None:
            failures.append(f"MISSING regulation key in results: {reg_key!r}")
        elif result.applies:
            failures.append(
                f"Expected {reg_key!r} NOT to apply but got applies=True "
                f"(confidence={result.confidence}, reason={result.reason!r})"
            )

    if failures:
        failure_text = "\n  ".join(failures)
        pytest.fail(
            f"Scenario: {scenario}\n"
            f"Profile: {profile.company_name} | {profile.employee_count} employees | "
            f"industry={profile.industry} | country={profile.country}\n"
            f"Rule Engine: {RULE_ENGINE_VERSION}\n"
            f"Failures:\n  {failure_text}"
        )


# ---------------------------------------------------------------------------
# Summary fixture — prints pass/fail table after all tests
# ---------------------------------------------------------------------------

class _SummaryPlugin:
    """Collect per-scenario pass/fail and print a summary table at the end."""

    def __init__(self) -> None:
        self.results: list[tuple[str, str]] = []  # (scenario, "PASS" | "FAIL")

    def pytest_runtest_logreport(self, report):
        if report.when == "call" and "test_golden_profile" in report.nodeid:
            # Extract scenario name from the node id brackets
            scenario = report.nodeid.split("[", 1)[-1].rstrip("]") if "[" in report.nodeid else report.nodeid
            status = "PASS" if report.passed else "FAIL"
            self.results.append((scenario, status))

    def pytest_terminal_summary(self, terminalreporter, exitstatus):
        if not self.results:
            return
        terminalreporter.write_sep("=", "RuleEngine Golden Profile Summary")
        passed = sum(1 for _, s in self.results if s == "PASS")
        failed = sum(1 for _, s in self.results if s == "FAIL")
        col_w = max(len(s) for s, _ in self.results) + 2
        terminalreporter.write_line(
            f"{'Scenario':<{col_w}} {'Result':>6}"
        )
        terminalreporter.write_line("-" * (col_w + 8))
        for scenario, status in self.results:
            icon = "OK" if status == "PASS" else "FAIL"
            terminalreporter.write_line(f"{scenario:<{col_w}} {icon:>6}")
        terminalreporter.write_line("-" * (col_w + 8))
        terminalreporter.write_line(
            f"Total: {len(self.results)} | PASS: {passed} | FAIL: {failed}"
        )
        terminalreporter.write_line(f"Rule Engine: {RULE_ENGINE_VERSION}")


def pytest_configure(config):
    config.pluginmanager.register(_SummaryPlugin(), "_rule_engine_summary")


# ---------------------------------------------------------------------------
# Standalone sanity test — RuleEngine version is set
# ---------------------------------------------------------------------------

def test_rule_engine_version():
    """Confirm RULE_ENGINE_VERSION is a non-empty string."""
    assert isinstance(RULE_ENGINE_VERSION, str)
    assert RULE_ENGINE_VERSION.strip(), "RULE_ENGINE_VERSION must not be empty"


def test_all_regulations_covered(raw_profiles):
    """All regulation keys in the JSON appear in the engine's _CHECKS registry."""
    engine = RuleEngine()
    known_keys = set(engine._CHECKS.keys())
    missing: list[str] = []
    for profile_data in raw_profiles:
        for key in profile_data.get("expected_applicable", []) + profile_data.get("expected_not_applicable", []):
            if key not in known_keys:
                missing.append(key)
    assert not missing, (
        f"Regulation keys in golden profiles not found in RuleEngine._CHECKS: {sorted(set(missing))}"
    )
