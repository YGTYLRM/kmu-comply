"""
Website scanner — detects TTDSG §25 cookie compliance, Impressum, privacy policy, HTTPS,
and third-party tracker loading before consent.

Used by POST /api/scan-website. Runs Playwright in a thread executor so it doesn't
block the async event loop. Hard timeout: 45 seconds total per scan.
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_ssrf_target(hostname: str) -> bool:
    """Return True if the hostname resolves to a private/loopback address."""
    try:
        infos = socket.getaddrinfo(hostname, None)
        for _family, _type, _proto, _canonname, sockaddr in infos:
            ip = ipaddress.ip_address(sockaddr[0])
            if any(ip in net for net in _PRIVATE_NETWORKS):
                return True
    except Exception:
        pass
    return False

# ── Known tracker domains (loaded before consent = §25 TTDSG violation) ───────

_TRACKER_DOMAINS: frozenset[str] = frozenset({
    # Google
    "google-analytics.com", "googletagmanager.com", "googleadservices.com",
    "googlesyndication.com", "doubleclick.net", "google.com/ads",
    # Meta / Facebook
    "facebook.com", "facebook.net",
    # Microsoft
    "clarity.ms", "bing.com",
    # HubSpot
    "hs-analytics.net", "hubspot.com", "hsforms.com",
    # LinkedIn
    "linkedin.com", "snap.licdn.com",
    # Twitter/X
    "twitter.com", "ads-twitter.com",
    # Hotjar
    "hotjar.com",
    # Mixpanel
    "mixpanel.com",
    # Segment
    "cdn.segment.com",
    # Intercom
    "intercom.io", "intercomcdn.com",
    # Crisp
    "crisp.chat",
    # Klaviyo
    "klaviyo.com",
    # Taboola
    "taboola.com",
    # Outbrain
    "outbrain.com",
    # TikTok
    "tiktok.com", "analytics.tiktok.com",
    # Snapchat
    "snapchat.com", "sc-static.net",
    # Pinterest
    "pinterest.com", "pinimg.com",
})

# ── Cookie banner framework fingerprints ──────────────────────────────────────

_BANNER_SIGNATURES: list[tuple[str, str]] = [
    # CSS class / ID patterns on common CMPs
    ("#CybotCookiebotDialog",         "CookieBot"),
    ("#onetrust-banner-sdk",          "OneTrust"),
    ("#usercentrics-root",            "Usercentrics"),
    (".cc-banner",                    "CookieConsent (osano)"),
    ("#cookie-law-info-bar",          "CookieLawInfo"),
    (".klaro",                        "Klaro"),
    ("#cookie-notice",                "Cookie Notice"),
    (".cookiefirst-root",             "CookieFirst"),
    ("#PrivacyManagerbar",            "Privacy Manager"),
    (".borlabs-cookie",               "Borlabs Cookie"),
    (".cmplz-cookiebanner",           "Complianz"),
    ("#CookieConsent",                "generic-cookie-consent"),
    (".cookie-consent",               "generic-cookie-consent"),
    (".cookie-banner",                "generic-cookie-banner"),
    (".cookie-overlay",               "generic-cookie-overlay"),
    ('[data-cookie-consent]',         "generic-data-attr"),
    ('[aria-label*="cookie" i]',      "generic-aria-cookie"),
    ('[role="dialog"][aria-label*="cookie" i]', "generic-dialog-cookie"),
]

# Impressum / legal notice link patterns
_IMPRESSUM_PATTERNS = re.compile(
    r"impressum|legal\s*notice|legal\s*information|rechtliche\s*hinweise|anbieterkennzeichnung",
    re.IGNORECASE,
)

# Privacy policy link patterns (German + English)
_PRIVACY_PATTERNS = re.compile(
    r"datenschutz|privacy\s*policy|datenschutzerkl[äa]rung|datenschutzhinweise",
    re.IGNORECASE,
)


@dataclass
class WebScanResult:
    url: str
    scanned_at: str  # ISO 8601
    https: bool
    has_impressum: bool
    impressum_url: str | None
    has_privacy_policy: bool
    privacy_policy_url: str | None
    has_cookie_banner: bool
    cookie_banner_framework: str | None
    trackers_before_consent: list[str]
    cookie_compliant: bool  # banner present AND no trackers fired before consent
    scan_duration_seconds: float
    error: str | None = None
    # Suggested profile field updates based on scan findings
    profile_suggestions: dict[str, bool] = field(default_factory=dict)


def _is_tracker(url: str) -> str | None:
    """Return the matching tracker domain name if url belongs to a known tracker, else None."""
    try:
        host = urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return None
    for domain in _TRACKER_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return domain
    return None


def _scan_sync(raw_url: str) -> WebScanResult:
    """Blocking Playwright scan — run this in a thread executor."""
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    start = datetime.now(timezone.utc)

    # Normalise URL
    if not raw_url.startswith(("http://", "https://")):
        raw_url = "https://" + raw_url
    parsed = urlparse(raw_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    is_https = parsed.scheme == "https"

    # SSRF guard — reject private/loopback targets
    if _is_ssrf_target(parsed.hostname or ""):
        return _build_result(
            raw_url, start, 0.0, is_https,
            False, None, False, None,
            False, None, [],
            "Scan target resolves to a private or loopback address and was blocked.",
        )

    trackers: list[str] = []
    has_banner = False
    banner_framework: str | None = None
    has_impressum = False
    impressum_url: str | None = None
    has_privacy = False
    privacy_url: str | None = None
    error: str | None = None

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                locale="de-DE",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True,
                # Clear cookies and storage so no prior consent is remembered
                storage_state=None,
            )
            # Intercept all network requests to detect trackers firing before consent
            tracker_seen: set[str] = set()

            def _on_request(request):
                domain = _is_tracker(request.url)
                if domain and domain not in tracker_seen:
                    tracker_seen.add(domain)
                    trackers.append(domain)

            page = context.new_page()
            page.on("request", _on_request)

            try:
                page.goto(raw_url, wait_until="domcontentloaded", timeout=30_000)
                # Wait briefly for dynamic banners to appear
                page.wait_for_timeout(2_000)
            except PWTimeout:
                error = "Page load timed out (30s)"
                browser.close()
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                return _build_result(
                    raw_url, start, elapsed, is_https,
                    False, None, False, None,
                    False, None, [], error,
                )

            # ── Cookie banner detection ────────────────────────────────────────
            for selector, framework in _BANNER_SIGNATURES:
                try:
                    el = page.query_selector(selector)
                    if el and el.is_visible():
                        has_banner = True
                        banner_framework = framework
                        break
                except Exception:
                    pass

            # Fallback: check page text for cookie consent phrases
            if not has_banner:
                try:
                    body_text = page.inner_text("body") or ""
                    cookie_phrases = [
                        "cookies akzeptieren", "cookies ablehnen", "alle cookies",
                        "einwilligung", "consent", "accept cookies", "decline cookies",
                        "cookie-einstellungen", "cookie settings", "wir verwenden cookies",
                        "we use cookies", "datenschutz und cookies",
                    ]
                    body_lower = body_text.lower()
                    if any(phrase in body_lower for phrase in cookie_phrases):
                        has_banner = True
                        banner_framework = "detected-via-text"
                except Exception:
                    pass

            # ── Link scanning for Impressum and Datenschutz ───────────────────
            # Priority: footer links first (most reliable for legal pages),
            # then all links, then full body text as fallback.
            def _scan_links(selector: str, limit: int = 300) -> None:
                nonlocal has_impressum, impressum_url, has_privacy, privacy_url
                try:
                    links = page.query_selector_all(selector)
                    for link in links[:limit]:
                        try:
                            href = link.get_attribute("href") or ""
                            text = (link.inner_text() or "").strip()
                            full_href = urljoin(base_url, href) if not href.startswith("http") else href
                            combined = f"{href} {text}"
                            if not has_impressum and _IMPRESSUM_PATTERNS.search(combined):
                                has_impressum = True
                                impressum_url = full_href
                            if not has_privacy and _PRIVACY_PATTERNS.search(combined):
                                has_privacy = True
                                privacy_url = full_href
                        except Exception:
                            pass
                except Exception:
                    pass

            _scan_links("footer a[href]")
            if not (has_impressum and has_privacy):
                _scan_links("a[href]", limit=300)

            # Final fallback: search full page text
            try:
                body_text = page.inner_text("body") or ""
                if not has_impressum and _IMPRESSUM_PATTERNS.search(body_text):
                    has_impressum = True
                if not has_privacy and _PRIVACY_PATTERNS.search(body_text):
                    has_privacy = True
            except Exception:
                pass

            browser.close()

    except Exception as exc:
        error = f"Scan failed: {type(exc).__name__}: {exc}"
        logger.warning("website_scanner: %s — %s", raw_url, error)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    return _build_result(
        raw_url, start, elapsed, is_https,
        has_impressum, impressum_url,
        has_privacy, privacy_url,
        has_banner, banner_framework,
        trackers, error,
    )


def _build_result(
    url: str,
    start: datetime,
    elapsed: float,
    is_https: bool,
    has_impressum: bool,
    impressum_url: str | None,
    has_privacy: bool,
    privacy_url: str | None,
    has_banner: bool,
    banner_framework: str | None,
    trackers: list[str],
    error: str | None,
) -> WebScanResult:
    cookie_compliant = has_banner and len(trackers) == 0

    # Derive profile field suggestions from scan findings
    suggestions: dict[str, bool] = {}
    if has_privacy:
        suggestions["has_privacy_policy"] = True
    if has_banner:
        suggestions["has_cookie_banner"] = True
    if has_banner:
        suggestions["has_cookie_policy"] = True
    suggestions["has_website"] = True

    return WebScanResult(
        url=url,
        scanned_at=start.isoformat(),
        https=is_https,
        has_impressum=has_impressum,
        impressum_url=impressum_url,
        has_privacy_policy=has_privacy,
        privacy_policy_url=privacy_url,
        has_cookie_banner=has_banner,
        cookie_banner_framework=banner_framework,
        trackers_before_consent=trackers,
        cookie_compliant=cookie_compliant,
        scan_duration_seconds=round(elapsed, 2),
        error=error,
        profile_suggestions=suggestions,
    )


async def scan_website(url: str) -> WebScanResult:
    """Async entry point — runs the blocking Playwright scan in a thread executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _scan_sync, url)
