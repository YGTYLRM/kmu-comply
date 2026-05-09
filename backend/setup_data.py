"""
Data setup script — downloads official guidance PDFs and ingests all regulations.

Run once on a fresh machine after installing requirements:
    cd backend
    python setup_data.py

This re-creates the ChromaDB vector database from official sources.
"""
import urllib.request
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Official guidance PDFs to download into compliance_guides/
# All URLs point to documents published by official EU/national bodies.
# ---------------------------------------------------------------------------
GUIDANCE_PDFS = [
    # EDPB Guidelines 05/2020 on consent (Art. 6/7 GDPR)
    (
        "edpb_consent_guidelines_2020.pdf",
        "https://edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_202005_consent_en.pdf",
        "EDPB Guidelines 05/2020 — Consent under GDPR",
    ),
    # WP250 rev.01 — Data breach notification guidelines (Art. 33/34 GDPR), endorsed by EDPB
    (
        "wp250_data_breach_notification_guidelines.pdf",
        "https://ec.europa.eu/newsroom/article29/redirection/document/51490",
        "WP250 rev.01 — Personal Data Breach Notification (EDPB)",
    ),
    # WP259 rev.01 — Consent guidelines (original, Art. 6/7 GDPR), endorsed by EDPB
    (
        "wp259_consent_guidelines.pdf",
        "https://ec.europa.eu/newsroom/article29/redirection/document/47741",
        "WP259 rev.01 — Guidelines on Consent (EDPB)",
    ),
    # WP248 rev.01 — DPIA guidelines (Art. 35 GDPR), endorsed by EDPB
    (
        "wp248_dpia_guidelines.pdf",
        "https://ec.europa.eu/newsroom/article29/redirection/document/47711",
        "WP248 rev.01 — Guidelines on DPIA (EDPB)",
    ),
    # ENISA — NIS Investments 2024 (NIS2 sector cybersecurity maturity and investment analysis)
    (
        "enisa_nis_investments_2024.pdf",
        "https://www.enisa.europa.eu/sites/default/files/2024-11/CSPA%20-%20NIS%20Investments%20-%202024_0.pdf",
        "ENISA — NIS Investments 2024 Report",
    ),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; compliance-setup/1.0)"}


def _download_pdf(dest: Path, url: str, label: str) -> bool:
    if dest.exists() and dest.stat().st_size > 10_000:
        log.info("  SKIP (already exists): %s", dest.name)
        return True
    log.info("  Downloading: %s", label)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if data[:4] != b"%PDF":
            log.warning("  NOT a valid PDF (got %r...) — skipping: %s", data[:8], dest.name)
            return False
        dest.write_bytes(data)
        log.info("  Saved %dKB → %s", len(data) // 1024, dest.name)
        return True
    except Exception as exc:
        log.warning("  FAILED: %s — %s", label, exc)
        return False


def download_guidance_pdfs() -> None:
    dest_dir = BASE / "data" / "regulations" / "compliance_guides"
    dest_dir.mkdir(parents=True, exist_ok=True)
    log.info("\n=== Downloading official guidance PDFs ===")
    for fname, url, label in GUIDANCE_PDFS:
        _download_pdf(dest_dir / fname, url, label)


def ingest_all() -> None:
    from rag.ingest import ingest_regulation, REGULATION_COLLECTIONS

    log.info("\n=== Ingesting regulation collections ===")
    for reg in REGULATION_COLLECTIONS:
        source_dir = BASE / "data" / "regulations" / reg
        if not source_dir.exists():
            log.warning("SKIP %s — directory not found", reg)
            continue
        files = [f for f in source_dir.iterdir() if f.suffix in (".txt", ".pdf")]
        if not files:
            log.warning("SKIP %s — no source files", reg)
            continue
        try:
            n = ingest_regulation(reg, reset=True)
            log.info("  %s: %d chunks", reg, n)
        except Exception as exc:
            log.warning("  FAILED %s: %s", reg, exc)


if __name__ == "__main__":
    download_guidance_pdfs()
    ingest_all()
    log.info("\nDone. ChromaDB is ready.")
