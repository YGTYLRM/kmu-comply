"""
Unit tests for the website scanner service.

These tests do NOT make real network requests — they test the helper functions
and the result-building logic with mocked data.
"""
import pytest

from services.website_scanner import (
    _build_result,
    _is_tracker,
    _TRACKER_DOMAINS,
    WebScanResult,
)
from routes.scanning import _build_findings


# ── _is_tracker ────────────────────────────────────────────────────────────────

class TestIsTracker:
    def test_google_analytics(self):
        assert _is_tracker("https://www.google-analytics.com/analytics.js") == "google-analytics.com"

    def test_gtm(self):
        assert _is_tracker("https://www.googletagmanager.com/gtm.js?id=GTM-XXXX") == "googletagmanager.com"

    def test_facebook_pixel(self):
        assert _is_tracker("https://connect.facebook.net/en_US/fbevents.js") == "facebook.net"

    def test_hotjar(self):
        assert _is_tracker("https://static.hotjar.com/c/hotjar-123.js") == "hotjar.com"

    def test_cdn_not_tracker(self):
        assert _is_tracker("https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css") is None

    def test_own_domain_not_tracker(self):
        assert _is_tracker("https://mycompany.de/assets/logo.png") is None

    def test_subdomain_of_tracker(self):
        assert _is_tracker("https://static.hotjar.com/something") == "hotjar.com"

    def test_invalid_url_returns_none(self):
        assert _is_tracker("not-a-url") is None


# ── _build_result ──────────────────────────────────────────────────────────────

class TestBuildResult:
    def _make(self, **kwargs):
        from datetime import datetime, timezone
        defaults = dict(
            url="https://example.de",
            start=datetime.now(timezone.utc),
            elapsed=5.0,
            is_https=True,
            has_impressum=True,
            impressum_url="https://example.de/impressum",
            has_privacy=True,
            privacy_url="https://example.de/datenschutz",
            has_banner=True,
            banner_framework="CookieBot",
            trackers=[],
            error=None,
        )
        defaults.update(kwargs)
        return _build_result(**defaults)

    def test_compliant_when_banner_and_no_trackers(self):
        result = self._make(has_banner=True, trackers=[])
        assert result.cookie_compliant is True

    def test_not_compliant_when_no_banner(self):
        result = self._make(has_banner=False, trackers=[])
        assert result.cookie_compliant is False

    def test_not_compliant_when_trackers_before_consent(self):
        result = self._make(has_banner=True, trackers=["google-analytics.com"])
        assert result.cookie_compliant is False

    def test_profile_suggestions_has_privacy(self):
        result = self._make(has_privacy=True)
        assert result.profile_suggestions.get("has_privacy_policy") is True

    def test_profile_suggestions_has_cookie_banner(self):
        result = self._make(has_banner=True)
        assert result.profile_suggestions.get("has_cookie_banner") is True

    def test_website_always_suggested(self):
        result = self._make()
        assert result.profile_suggestions.get("has_website") is True


# ── _build_findings ───────────────────────────────────────────────────────────

class TestBuildFindings:
    def _result(self, **kwargs):
        from datetime import datetime, timezone
        base = dict(
            url="https://example.de",
            start=datetime.now(timezone.utc),
            elapsed=5.0,
            is_https=True,
            has_impressum=True,
            impressum_url=None,
            has_privacy=True,
            privacy_url=None,
            has_banner=True,
            banner_framework="CookieBot",
            trackers=[],
            error=None,
        )
        base.update(kwargs)
        return _build_result(**base)

    def test_http_site_flagged(self):
        result = self._result(is_https=False)
        findings = _build_findings(result)
        assert any("HTTPS" in f for f in findings)

    def test_missing_impressum_flagged(self):
        result = self._result(has_impressum=False)
        findings = _build_findings(result)
        assert any("Impressum" in f for f in findings)

    def test_missing_privacy_policy_flagged(self):
        result = self._result(has_privacy=False)
        findings = _build_findings(result)
        assert any("Datenschutz" in f for f in findings)

    def test_missing_banner_flagged(self):
        result = self._result(has_banner=False)
        findings = _build_findings(result)
        assert any("§25 TTDSG" in f for f in findings)

    def test_trackers_before_consent_flagged(self):
        result = self._result(has_banner=True, trackers=["google-analytics.com"])
        findings = _build_findings(result)
        assert any("before consent" in f for f in findings)

    def test_compliant_site_gets_positive_finding(self):
        result = self._result(
            is_https=True, has_impressum=True, has_privacy=True,
            has_banner=True, trackers=[],
        )
        findings = _build_findings(result)
        assert any("compliant" in f.lower() for f in findings)

    def test_error_reported_in_findings(self):
        result = self._result(error="Page load timed out (30s)")
        findings = _build_findings(result)
        assert any("Scan error" in f for f in findings)
