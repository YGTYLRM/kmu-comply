"""
Official-source regulation update fetcher.

Fetches regulation texts from gesetze-im-internet.de and EUR-Lex,
compares hashes against the current production files, and creates
PendingRegulationUpdate records for any changed regulations.

Updates are staged — they do NOT replace production files or re-ingest
until a human approves them via the admin API.
"""
from __future__ import annotations

import hashlib
import logging
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR    = Path(__file__).parent.parent / "data" / "regulations"
STAGING_DIR = Path(__file__).parent.parent / "data" / "staging"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; compliance-research/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-GB,en;q=0.9,de;q=0.8",
}

REGULATION_SOURCES = [
    {
        "regulation": "lksg",
        "type": "gesetze",
        "prefix": "lksg",
        "dest_filename": "lksg_text.txt",
        "source_url": "https://www.gesetze-im-internet.de/lksg/",
    },
    {
        "regulation": "enefg",
        "type": "gesetze",
        "prefix": "enefg",
        "dest_filename": "enefg_text.txt",
        "source_url": "https://www.gesetze-im-internet.de/enefg/",
    },
    {
        "regulation": "hinschg",
        "type": "gesetze",
        "prefix": "hinschg",
        "dest_filename": "hinschg_text.txt",
        "source_url": "https://www.gesetze-im-internet.de/hinschg/",
    },
    {
        "regulation": "agg",
        "type": "gesetze",
        "prefix": "agg",
        "dest_filename": "agg_text.txt",
        "source_url": "https://www.gesetze-im-internet.de/agg/",
    },
    {
        "regulation": "milog",
        "type": "gesetze",
        "prefix": "milog",
        "dest_filename": "milog_text.txt",
        "source_url": "https://www.gesetze-im-internet.de/milog/",
    },
    {
        "regulation": "csrd",
        "type": "eurlex",
        "celex": "32022L2464",
        "dest_filename": "csrd_directive.txt",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022L2464",
    },
    {
        "regulation": "nis2",
        "type": "eurlex",
        "celex": "32022L2555",
        "dest_filename": "nis2_full_directive.txt",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022L2555",
    },
    {
        "regulation": "eu_ai_act",
        "type": "eurlex",
        "celex": "32024R1689",
        "dest_filename": "eu_ai_act_full.txt",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689",
    },
]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_html(html_text: str) -> str:
    import html as html_module
    html_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
    html_text = re.sub(r"<(br|p|div|tr|li|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"<[^>]+>", "", html_text)
    html_text = html_module.unescape(html_text)
    html_text = re.sub(r"\n{3,}", "\n\n", html_text)
    return html_text.strip()


def _fetch_gesetze(prefix: str, source_url: str) -> str | None:
    index_url = f"https://www.gesetze-im-internet.de/{prefix}/"
    req = urllib.request.Request(index_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read().decode("utf-8", errors="replace")
    except Exception as exc:
        logger.warning("regulation_updater: fetch_gesetze index failed for %s: %s", prefix, exc)
        return None
    matches = re.findall(r'href="(BJNR[^"]+\.html)"', page)
    if not matches:
        matches = re.findall(r'href="([^"]+BJNR[^"]+\.html)"', page)
    if not matches:
        logger.warning("regulation_updater: no full-text link found for %s", prefix)
        return None
    full_url = f"https://www.gesetze-im-internet.de/{prefix}/{matches[0]}"
    req2 = urllib.request.Request(full_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req2, timeout=30) as r:
            raw = r.read().decode("utf-8", errors="replace")
        return _strip_html(raw)
    except Exception as exc:
        logger.warning("regulation_updater: fetch_gesetze full text failed for %s: %s", prefix, exc)
        return None


def _fetch_eurlex(celex: str, source_url: str) -> str | None:
    req = urllib.request.Request(source_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8", errors="replace")
        return _strip_html(raw)
    except Exception as exc:
        logger.warning("regulation_updater: fetch_eurlex failed for %s: %s", celex, exc)
        return None


async def fetch_and_stage_updates() -> list[str]:
    """
    Fetch all regulation sources, compare with current production files,
    and create PendingRegulationUpdate DB records for any that changed.
    Returns list of regulation names that have pending updates.
    """
    from config import settings
    if not settings.database_url:
        logger.warning("regulation_updater: DATABASE_URL not set — cannot stage updates")
        return []

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    pending: list[str] = []

    for src in REGULATION_SOURCES:
        reg = src["regulation"]
        logger.info("regulation_updater: checking %s", reg)
        try:
            if src["type"] == "gesetze":
                new_text = _fetch_gesetze(src["prefix"], src["source_url"])
            else:
                new_text = _fetch_eurlex(src["celex"], src["source_url"])

            if not new_text:
                logger.warning("regulation_updater: fetch returned empty for %s", reg)
                continue

            new_hash = _sha256(new_text)

            # Compare with current production file
            prod_dir  = DATA_DIR / reg
            prod_file = prod_dir / src["dest_filename"]
            prev_hash: str | None = None
            if prod_file.exists():
                prev_hash = _sha256(prod_file.read_text(encoding="utf-8"))
                if prev_hash == new_hash:
                    logger.info("regulation_updater: %s unchanged", reg)
                    continue

            # Changed (or new) — stage it
            staging_file = STAGING_DIR / f"{reg}_{new_hash[:8]}_{src['dest_filename']}"
            staging_file.write_text(new_text, encoding="utf-8")

            change_summary = (
                f"Source file changed. New hash: {new_hash[:12]}. "
                + (f"Previous hash: {prev_hash[:12]}." if prev_hash else "No previous file (first fetch).")
                + f" Source: {src['source_url']}"
            )

            await _create_pending(
                regulation=reg,
                source_url=src["source_url"],
                new_hash=new_hash,
                previous_hash=prev_hash,
                staging_path=str(staging_file),
                change_summary=change_summary,
            )
            pending.append(reg)
            logger.info("regulation_updater: staged update for %s", reg)

        except Exception as exc:
            logger.error("regulation_updater: error processing %s: %s", reg, exc)

    return pending


async def _create_pending(
    regulation: str,
    source_url: str,
    new_hash: str,
    previous_hash: str | None,
    staging_path: str,
    change_summary: str,
) -> None:
    from db.database import AsyncSessionLocal
    from db.models import PendingRegulationUpdate
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Don't create a duplicate if the same hash is already pending
        existing = (await db.execute(
            select(PendingRegulationUpdate).where(
                PendingRegulationUpdate.regulation == regulation,
                PendingRegulationUpdate.new_hash == new_hash,
                PendingRegulationUpdate.status == "pending",
            )
        )).scalar_one_or_none()
        if existing:
            return
        db.add(PendingRegulationUpdate(
            regulation=regulation,
            source_url=source_url,
            new_hash=new_hash,
            previous_hash=previous_hash,
            staging_path=staging_path,
            change_summary=change_summary,
        ))
        await db.commit()


async def approve_update(update_id: str) -> dict:
    """
    Approve a pending regulation update:
    1. Copy staging file to production regulations directory
    2. Re-ingest the regulation into ChromaDB
    3. Mark the update as approved
    """
    from db.database import AsyncSessionLocal
    from db.models import PendingRegulationUpdate
    from sqlalchemy import select
    import asyncio

    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(PendingRegulationUpdate).where(PendingRegulationUpdate.id == update_id)
        )).scalar_one_or_none()
        if not row:
            raise ValueError(f"Update {update_id} not found")
        if row.status != "pending":
            raise ValueError(f"Update {update_id} is already {row.status}")

        staging = Path(row.staging_path)
        if not staging.exists():
            raise FileNotFoundError(f"Staging file missing: {staging}")

        # Find the destination filename from REGULATION_SOURCES
        src = next((s for s in REGULATION_SOURCES if s["regulation"] == row.regulation), None)
        if not src:
            raise ValueError(f"Unknown regulation: {row.regulation}")

        prod_dir  = DATA_DIR / row.regulation
        prod_dir.mkdir(parents=True, exist_ok=True)
        prod_file = prod_dir / src["dest_filename"]
        prod_file.write_text(staging.read_text(encoding="utf-8"), encoding="utf-8")

        # Re-ingest
        loop = asyncio.get_event_loop()
        def _ingest():
            from rag.ingest import ingest_regulation
            return ingest_regulation(row.regulation, reset=True)
        chunk_count = await loop.run_in_executor(None, _ingest)

        # Mark approved
        row.status      = "approved"
        row.reviewed_at = datetime.now(timezone.utc)
        row.change_summary = (row.change_summary or "") + f" | Approved: {chunk_count} chunks ingested."
        await db.commit()

        # Clean up staging file
        try:
            staging.unlink()
        except Exception:
            pass

        return {"regulation": row.regulation, "chunks_indexed": chunk_count}


async def reject_update(update_id: str) -> None:
    """Reject a pending update — mark as rejected and delete the staging file."""
    from db.database import AsyncSessionLocal
    from db.models import PendingRegulationUpdate
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(PendingRegulationUpdate).where(PendingRegulationUpdate.id == update_id)
        )).scalar_one_or_none()
        if not row:
            raise ValueError(f"Update {update_id} not found")
        row.status      = "rejected"
        row.reviewed_at = datetime.now(timezone.utc)
        await db.commit()
        try:
            Path(row.staging_path).unlink(missing_ok=True)
        except Exception:
            pass
