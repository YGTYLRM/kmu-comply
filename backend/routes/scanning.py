"""
Website scanning endpoint — POST /api/scan-website

Runs a headless Playwright scan against a company's website and returns
structured findings: HTTPS, Impressum, privacy policy, cookie banner, and
trackers that fired before consent. Results can be used to pre-populate
CompanyProfile fields before running a full compliance analysis.
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from dependencies import check_endpoint_rate_limit
from services.auth_service import get_current_user
from services.website_scanner import WebScanResult, scan_website

logger = logging.getLogger(__name__)
router = APIRouter()


class ScanRequest(BaseModel):
    url: str

    @field_validator("url", mode="before")
    @classmethod
    def normalise_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class ScanResponse(BaseModel):
    url: str
    scanned_at: str
    https: bool
    has_impressum: bool
    impressum_url: Optional[str]
    has_privacy_policy: bool
    privacy_policy_url: Optional[str]
    has_cookie_banner: bool
    cookie_banner_framework: Optional[str]
    trackers_before_consent: list[str]
    cookie_compliant: bool
    scan_duration_seconds: float
    error: Optional[str]
    profile_suggestions: dict[str, bool]
    # Human-readable compliance findings
    findings: list[str]


def _build_findings(result: WebScanResult) -> list[str]:
    findings = []
    if not result.https:
        findings.append(
            "HTTPS not detected — data transmitted in plain text. "
            "Required for GDPR Art. 32 (encryption in transit)."
        )
    if not result.has_impressum:
        findings.append(
            "Impressum not found — legally required for German commercial websites "
            "under §5 TMG / §5 DDG."
        )
    if not result.has_privacy_policy:
        findings.append(
            "Datenschutzerklärung (privacy policy) not found — required under GDPR Art. 13/14 "
            "for any website processing personal data of EU residents."
        )
    if not result.has_cookie_banner:
        findings.append(
            "No cookie consent banner detected — §25 TTDSG requires prior informed consent "
            "before storing non-essential cookies or accessing terminal equipment."
        )
    elif result.trackers_before_consent:
        tracker_list = ", ".join(result.trackers_before_consent[:5])
        findings.append(
            f"Cookie banner present but tracker requests fired before consent: {tracker_list}. "
            f"This violates §25 TTDSG — scripts must be blocked until the user actively consents."
        )
    if result.cookie_compliant:
        findings.append(
            "Cookie consent appears compliant: banner detected and no tracker requests "
            "fired before user interaction."
        )
    if result.error:
        findings.append(f"Scan error: {result.error} — some checks may be incomplete.")
    return findings


@router.post("/api/scan-website", response_model=ScanResponse)
async def scan_website_endpoint(
    body: ScanRequest,
    current_user: dict = Depends(get_current_user),
):
    await check_endpoint_rate_limit(current_user["id"], "scan_website", limit=10)
    try:
        result = await asyncio.wait_for(scan_website(body.url), timeout=45.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Website scan timed out after 45 seconds.")
    except Exception as exc:
        logger.error("scan_website: unexpected error for %s: %s", body.url, exc)
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}")

    findings = _build_findings(result)

    return ScanResponse(
        url=result.url,
        scanned_at=result.scanned_at,
        https=result.https,
        has_impressum=result.has_impressum,
        impressum_url=result.impressum_url,
        has_privacy_policy=result.has_privacy_policy,
        privacy_policy_url=result.privacy_policy_url,
        has_cookie_banner=result.has_cookie_banner,
        cookie_banner_framework=result.cookie_banner_framework,
        trackers_before_consent=result.trackers_before_consent,
        cookie_compliant=result.cookie_compliant,
        scan_duration_seconds=result.scan_duration_seconds,
        error=result.error,
        profile_suggestions=result.profile_suggestions,
        findings=findings,
    )
