"""
Regulatory document ingestion pipeline.

For each regulation collection:
  1. Load source files (.txt or .pdf) from backend/data/regulations/<regulation>/
  2. Extract text (plain read for .txt, pypdf for .pdf)
  3. Chunk at article / section level — never by arbitrary token count
  4. Embed each chunk with multilingual-e5-large
  5. Upsert into ChromaDB with rich metadata

Collection → directory mapping:
  gdpr_dsgvo       <- gdpr/
  bdsg             <- bdsg/
  lksg             <- lksg/
  enefg            <- enefg/
  csrd             <- csrd/
  compliance_guides <- compliance_guides/
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import chromadb
import pdfplumber
from pypdf import PdfReader

from rag.embeddings import embed_passages

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data" / "regulations"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"

# ~4.5 chars per token for German; cap at 1 500 tokens per chunk
MAX_CHUNK_CHARS = 1_500 * 4

REGULATION_COLLECTIONS: dict[str, str] = {
    "gdpr":             "gdpr_dsgvo",
    "gdpr_dsgvo":       "gdpr_dsgvo",  # alias so Regulation enum value resolves correctly
    "bdsg":             "bdsg",
    "lksg":             "lksg",
    "enefg":            "enefg",
    "csrd":             "csrd",
    "compliance_guides":"compliance_guides",
    "nis2":             "nis2",
    "eu_ai_act":        "eu_ai_act",
    "hinschg":          "hinschg",
    "workplace_law":    "workplace_law",
    "arbschg":          "workplace_law",  # alias: collection renamed from arbschg
    "agg":              "agg",
    "milog":            "milog",
    "ttdsg":            "ttdsg",
    "gwg":              "gwg",
    "eu_data_act":      "eu_data_act",
}

OFFICIAL_URLS: dict[str, str] = {
    "gdpr":             "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679",
    "gdpr_dsgvo":       "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679",
    "bdsg":             "https://www.gesetze-im-internet.de/bdsg_2018/",
    "lksg":             "https://www.gesetze-im-internet.de/lksg/",
    "enefg":            "https://www.gesetze-im-internet.de/enefg/",
    "csrd":             "https://eur-lex.europa.eu/eli/dir/2022/2464/oj/eng",
    "compliance_guides":"https://www.edpb.europa.eu",
    "nis2":             "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2555",
    "eu_ai_act":        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202401689",
    "hinschg":          "https://www.gesetze-im-internet.de/hinschg/",
    "workplace_law":    "https://www.gesetze-im-internet.de/arbschg/",
    "arbschg":          "https://www.gesetze-im-internet.de/arbschg/",
    "agg":              "https://www.gesetze-im-internet.de/agg/",
    "milog":            "https://www.gesetze-im-internet.de/milog/",
    "ttdsg":            "https://www.gesetze-im-internet.de/ttdsg/",
    "gwg":              "https://www.gesetze-im-internet.de/gwg_2017/",
    "eu_data_act":      "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202302854",
}

# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _extract_pdf(path: Path) -> str:
    raw = path.read_bytes()
    if not raw or raw[:4] != b"%PDF":
        raise ValueError(f"Not a valid PDF (first bytes: {raw[:8]!r}): {path.name}")
    try:
        with pdfplumber.open(str(path)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(p for p in pages if p.strip())
    except Exception:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n".join(pages)


def _load(path: Path) -> str:
    if path.suffix == ".pdf":
        return _extract_pdf(path)
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Chunkers
# ---------------------------------------------------------------------------

# Format A — standard gesetze-im-internet.de layout: § N\n then title on next line
# The lookahead requires \n after the number so mid-body cross-refs (§ 26 Abs. 2\n...) don't
# falsely terminate a section.
_RE_GERMAN_A = re.compile(
    r"(?m)^§\s{1,3}(\d+[a-z]?)\s*\n(.*?)(?=^§\s{1,3}\d+[a-z]?\s*\n|\Z)",
    re.DOTALL,
)

# Format B — SGB books layout: § [NBSP]NTitle all on one line.
# The title starts immediately after the section number (no separator), so we capture
# everything up to the end of the line with ([^\n]*).
_RE_GERMAN_B = re.compile(
    r"(?m)^§[ \t\xa0]{0,3}(\d+[a-z]?)([^\n]*)\n(.*?)(?=^§[ \t\xa0]{0,3}\d+[a-z]?|\Z)",
    re.DOTALL,
)

# EU Artikel (GDPR German)
_RE_EU_ARTIKEL = re.compile(
    r"(?m)^Artikel\s+(\d+)\s*\n(.*?)(?=^Artikel\s+\d+\s*\n|\Z)",
    re.DOTALL,
)

# EU Article (CSRD / ESRS English)
_RE_EU_ARTICLE = re.compile(
    r"(?m)^Article\s+(\d+)\s*\n(.*?)(?=^Article\s+\d+\s*\n|\Z)",
    re.DOTALL,
)

# Numbered section headings for guidance docs
_RE_SECTION = re.compile(
    r"(?m)^(\d+(?:\.\d+)*\.?|[IVX]+\.)\s{1,4}([A-ZÜÄÖ][^\n]{3,80})\n(.*?)(?=^(?:\d+(?:\.\d+)*\.?|[IVX]+\.)\s{1,4}[A-ZÜÄÖ]|\Z)",
    re.DOTALL,
)

# Sub-paragraph markers for oversized articles
_RE_ABSATZ = re.compile(r"(?m)^\(\d+\)")

# Minimum useful chunk size — below this a chunk has no retrievable legal content
MIN_CHUNK_CHARS = 150

def _strip_gesetze_noise(text: str) -> str:
    """Remove navigation links and JS remnants from gesetze-im-internet.de downloads.

    These strings appear after every section as in-page nav links — they must be
    removed inline, not by cutting at their position, because large files (SGB, etc.)
    contain hundreds of them scattered throughout.
    """
    text = re.sub(r'\bzum Seitenanfang\b\s*', "", text)
    text = re.sub(r'\bNichtamtliches Inhaltsverzeichnis\b[^\n]*', "", text)
    text = re.sub(r'\bInhaltsübersicht\b[^\n]*', "", text)
    text = re.sub(r'\bSeite ausdrucken\b[^\n]*', "", text)
    # Normalize non-breaking space between section number and title on the same line.
    # gesetze-im-internet.de TOC entries use "§ N\xa0Title" — convert to "§ N\nTitle"
    # so Format A regex can split section number from title correctly.
    text = re.sub(r'(?m)(^§\s*\d+[a-z]?)\xa0', r'\1\n', text)
    # JS remnants and footer block — only strip from the last 1000 chars
    tail_start = max(0, len(text) - 1_000)
    head, tail = text[:tail_start], text[tail_start:]
    tail = re.sub(r'(Impressum|Datenschutz|Barrierefreiheitserkl|Feedback-Formular).*', "", tail, flags=re.DOTALL)
    tail = re.sub(r'["\']?\s*\)\s*/\*.*?\*/\s*//.*', "", tail, flags=re.DOTALL)
    return head + tail.rstrip()


def _split_oversized(text: str, header: str) -> list[str]:
    """Split a chunk that exceeds MAX_CHUNK_CHARS by Absatz markers."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    # Split on Absatz boundaries, keeping the marker with its paragraph
    parts = re.split(r"(?m)(?=^\(\d+\))", text)
    if len(parts) < 2:
        # No Absatz markers — hard split at midpoint word boundary
        words = text.split()
        mid = len(words) // 2
        return [" ".join(words[:mid]), header + "\n" + " ".join(words[mid:])]

    chunks: list[str] = []
    current = ""
    for part in parts:
        if current and len(current) + len(part) > MAX_CHUNK_CHARS:
            chunks.append(current.strip())
            current = header + "\n" + part
        else:
            current += part
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text[:MAX_CHUNK_CHARS]]


# Negated obligation phrases — must be removed before keyword matching so that
# "muss nicht" / "ist nicht verpflichtet" / "shall not" don't classify as MUST.
_RE_NEGATED_OBLIGATION = re.compile(
    r"(muss(?:te)?|müssen|darf|dürfen|kann|können|soll(?:te)?n?|hat|haben)\s+"
    r"(?:\w+\s+){0,3}?nicht\b"
    r"|ist\s+nicht\s+(?:dazu\s+)?verpflichtet"
    r"|sind\s+nicht\s+(?:dazu\s+)?verpflichtet"
    r"|besteht\s+keine\s+(?:pflicht|verpflichtung)"
    r"|(?:shall|must|may|should)\s+not\b"
    r"|is\s+not\s+(?:required|obliged|obligated)",
    re.IGNORECASE,
)


def _obligation(text: str) -> str:
    t = _RE_NEGATED_OBLIGATION.sub(" ", text.lower())
    if any(w in t for w in ["muss", "müssen", "ist verpflichtet", "sind verpflichtet",
                             "hat zu", "haben zu", "must", "shall", "is required"]):
        return "MUST"
    if any(w in t for w in ["soll ", "sollen ", "sollte", "should", "ought"]):
        return "SHOULD"
    if any(w in t for w in [" kann ", " können ", " darf ", " dürfen ", " may ", " might "]):
        return "MAY"
    return "CONDITIONAL"


def _make_chunk(
    text: str,
    regulation: str,
    article_number: str,
    title: str,
    doc_type: str,
    source_file: str,
    source_url: str,
    paragraph: str = "",
) -> dict:
    return {
        "text": text,
        "metadata": {
            "regulation": regulation,
            "article_number": article_number,
            "paragraph": paragraph,
            "title": title,
            "document_type": doc_type,
            "obligation_type": _obligation(text),
            "source_file": source_file,
            "source_url": source_url,
        },
    }


def _chunk_german_law(text: str, regulation: str, filename: str, url: str) -> list[dict]:
    text = _strip_gesetze_noise(text)

    # Choose format by counting valid matches from each regex.
    # Format B wins if it produces at least 2× more valid-body matches than Format A —
    # which reliably distinguishes SGB-style files from standard short laws.
    format_a_matches = [m for m in _RE_GERMAN_A.finditer(text) if len(m.group(2).strip()) >= 80]
    format_b_matches = [m for m in _RE_GERMAN_B.finditer(text) if len(m.group(3).strip()) >= 80]
    use_format_b = len(format_b_matches) > len(format_a_matches) * 2

    best: dict[str, dict] = {}

    if use_format_b:
        for m in _RE_GERMAN_B.finditer(text):
            num = m.group(1)
            inline_title = m.group(2).strip()
            body = m.group(3).strip()
            if len(body) < 80:
                continue
            raw_title = inline_title or f"§ {num}"
            if raw_title == "(weggefallen)" or raw_title.startswith("(weggefallen)"):
                continue
            abs_match = re.search(r'\s*\(\s*1\s*\)', raw_title)
            title = (raw_title[:abs_match.start()].strip() if abs_match else raw_title[:120]).strip() or f"§ {num}"
            full = f"§ {num} {title}\n\n{body}"
            key = f"§ {num}"
            if key not in best or len(full) > len(best[key]["text"]):
                best[key] = {"text": full, "title": title, "num": num}
    else:
        # Collect all Format A matches, deduplicate by section number keeping longest.
        # gesetze-im-internet.de pages contain both a TOC and the full text, so each § N
        # appears twice — once as a short TOC entry and once with its actual content.
        for m in _RE_GERMAN_A.finditer(text):
            num = m.group(1)
            body = m.group(2).strip()
            if len(body) < 80:
                continue
            lines = body.splitlines()
            raw_title = lines[0].strip() if lines else f"§ {num}"
            if raw_title == "(weggefallen)" or raw_title.startswith("(weggefallen)"):
                continue
            abs_match = re.search(r'\s*\(\s*1\s*\)', raw_title)
            title = (raw_title[:abs_match.start()].strip() if abs_match else raw_title[:120]).strip() or f"§ {num}"
            full = f"§ {num} {title}\n\n{body}"
            key = f"§ {num}"
            if key not in best or len(full) > len(best[key]["text"]):
                best[key] = {"text": full, "title": title, "num": num}

    chunks: list[dict] = []
    for key, item in best.items():
        header = f"§ {item['num']} {item['title']}"
        for i, sub in enumerate(_split_oversized(item["text"], header)):
            chunks.append(_make_chunk(sub, regulation, key, item["title"], "law",
                                      filename, url, str(i + 1) if i else ""))
    return chunks


def _chunk_eu_law(text: str, regulation: str, filename: str, url: str) -> list[dict]:
    """Try German 'Artikel' then English 'Article' pattern. Deduplicate by article number."""
    pattern = _RE_EU_ARTIKEL
    label = "Artikel"
    matches = list(pattern.finditer(text))
    if len(matches) < 3:
        pattern = _RE_EU_ARTICLE
        label = "Article"
        matches = list(pattern.finditer(text))

    best: dict[str, dict] = {}
    for m in matches:
        num = m.group(1)
        body = m.group(2).strip()
        if len(body) < 80:
            continue
        lines = body.splitlines()
        title = lines[0].strip() if lines else f"{label} {num}"
        full = f"{label} {num} {title}\n\n{body}"
        key = f"{label} {num}"
        if key not in best or len(full) > len(best[key]["text"]):
            best[key] = {"text": full, "title": title, "num": num, "label": label}

    chunks: list[dict] = []
    for key, item in best.items():
        header = f"{item['label']} {item['num']} {item['title']}"
        for i, sub in enumerate(_split_oversized(item["text"], header)):
            chunks.append(_make_chunk(sub, regulation, key, item["title"], "law",
                                      filename, url, str(i + 1) if i else ""))
    return chunks


def _chunk_guidance(text: str, regulation: str, filename: str, url: str) -> list[dict]:
    """Chunk guidance PDFs by numbered section headings; fall back to fixed-size."""
    matches = list(_RE_SECTION.finditer(text))
    if len(matches) < 3:
        return _chunk_fixed(text, regulation, filename, url)

    chunks: list[dict] = []
    for m in matches:
        sec_num = m.group(1).strip()
        title = m.group(2).strip()
        body = m.group(3).strip()
        if len(body) < 80:
            continue
        full = f"{sec_num} {title}\n\n{body}"
        header = f"{sec_num} {title}"
        for i, sub in enumerate(_split_oversized(full, header)):
            chunks.append(_make_chunk(sub, regulation, sec_num, title, "guidance",
                                      filename, url, str(i + 1) if i else ""))
    return chunks


def _chunk_separator_blocks(text: str, regulation: str, filename: str, url: str) -> list[dict]:
    """Chunk files structured as blocks separated by '---' markers.
    Used for *_expanded.txt files where each block covers one article/provision."""
    import re as _re
    blocks = [b.strip() for b in text.split("---") if b.strip()]
    chunks = []
    for block in blocks:
        if len(block) < 80:
            continue
        lines = block.splitlines()
        first = lines[0].strip()
        # Extract article reference (e.g. "hinschg §12(1)" → "§12(1)")
        art_match = _re.search(r"§\s*(\S+)", first)
        article_number = f"§ {art_match.group(1)}" if art_match else first[:40]
        # Extract title from "Title: ..." line
        title = article_number
        for line in lines[1:6]:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
                break
        chunks.append(_make_chunk(block, regulation, article_number, title, "law", filename, url))
    return chunks


def _chunk_fixed(text: str, regulation: str, filename: str, url: str) -> list[dict]:
    """Fixed-size word-based fallback for documents with no detectable structure."""
    words = text.split()
    step = 300
    chunks = []
    for i in range(0, len(words), step):
        segment = " ".join(words[i : i + step]).strip()
        if len(segment) < 80:
            continue
        part = i // step + 1
        chunks.append(_make_chunk(
            segment, regulation, f"chunk_{part}", f"{filename} (part {part})",
            "guidance", filename, url,
        ))
    return chunks


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _stamp_provenance(chunks: list[dict], path: Path) -> list[dict]:
    """Add source versioning metadata to every chunk from a given file.

    Fields added:
      fetched_at       — ISO-8601 UTC timestamp of the file's last modification
                         (proxy for when the source was downloaded / last updated)
      source_file_hash — first 16 hex chars of SHA-256 of the raw file bytes;
                         changes when the source document is updated
      content_hash     — first 16 hex chars of SHA-256 of the chunk text;
                         used for section-level change detection in the scheduler
    """
    raw = path.read_bytes()
    file_hash = hashlib.sha256(raw).hexdigest()[:16]
    fetched_at = datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    for chunk in chunks:
        text = chunk["text"]
        chunk["metadata"]["fetched_at"] = fetched_at
        chunk["metadata"]["source_file_hash"] = file_hash
        chunk["metadata"]["content_hash"] = hashlib.sha256(text.encode()).hexdigest()[:16]

    return chunks


def _chunks_for_file(path: Path, regulation: str) -> list[dict]:
    url = OFFICIAL_URLS.get(regulation, "")
    text = _load(path)
    name = path.name

    # Structured expanded files (any regulation) — split on '---' blocks
    if "_expanded" in path.stem:
        chunks = _chunk_separator_blocks(text, regulation, name, url)

    elif regulation in ("bdsg", "lksg", "enefg", "hinschg", "arbschg", "workplace_law", "agg", "milog", "ttdsg", "gwg") and path.suffix == ".txt":
        chunks = _chunk_german_law(text, regulation, name, url)
        if not chunks:
            chunks = _chunk_guidance(text, regulation, name, url)

    elif regulation in ("gdpr", "csrd", "nis2", "eu_ai_act", "eu_data_act"):
        chunks = _chunk_eu_law(text, regulation, name, url)
        if not chunks:
            chunks = _chunk_guidance(text, regulation, name, url)

    elif regulation == "compliance_guides" and path.suffix == ".txt":
        if _RE_GERMAN_A.search(text):
            chunks = _chunk_german_law(text, regulation, name, url)
            if not chunks:
                chunks = _chunk_guidance(text, regulation, name, url)
        else:
            chunks = _chunk_guidance(text, regulation, name, url)

    else:
        chunks = _chunk_guidance(text, regulation, name, url)

    return _stamp_provenance(chunks, path)


# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------

_chroma: chromadb.PersistentClient | None = None


def _chroma_client():
    global _chroma
    if _chroma is None:
        from config import settings
        if settings.chroma_server_url:
            _chroma = chromadb.HttpClient(host=settings.chroma_server_url)
            logger.info("ChromaDB: using server mode at %s", settings.chroma_server_url)
        else:
            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            _chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
            logger.info("ChromaDB: using embedded mode at %s", CHROMA_DIR)
    return _chroma


def ingest_regulation(
    regulation: str,
    source_dir: Path | None = None,
    reset: bool = False,
) -> int:
    """
    Parse, chunk, embed, and index all documents for one regulation.
    Returns total number of chunks indexed.
    """
    collection_name = REGULATION_COLLECTIONS[regulation]
    if source_dir is None:
        # workplace_law data lives in the arbschg/ folder on disk (folder name unchanged)
        source_dir = DATA_DIR / ("arbschg" if regulation == "workplace_law" else regulation)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    files = sorted(
        f for f in source_dir.iterdir()
        if f.suffix in (".txt", ".pdf") and not f.name.startswith(".")
    )
    if not files:
        raise ValueError(f"No .txt or .pdf files in {source_dir}")

    client = _chroma_client()

    existing = {c.name for c in client.list_collections()}
    if reset and collection_name in existing:
        client.delete_collection(collection_name)
        logger.info("Deleted collection: %s", collection_name)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    total = 0
    for path in files:
        logger.info("Processing %s ...", path.name)
        try:
            chunks = _chunks_for_file(path, regulation)
        except (ValueError, Exception) as exc:
            logger.warning("  SKIPPED %s: %s", path.name, exc)
            continue
        if not chunks:
            logger.warning("  No chunks from %s", path.name)
            continue

        before = len(chunks)
        chunks = [c for c in chunks if len(c["text"]) >= MIN_CHUNK_CHARS]
        dropped = before - len(chunks)
        if dropped:
            logger.info("  Dropped %d stub chunk(s) under %d chars", dropped, MIN_CHUNK_CHARS)

        BATCH = 32
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i : i + BATCH]
            texts = [c["text"] for c in batch]
            embeddings = embed_passages(texts)
            ids = [f"{regulation}_{path.stem}_{i + j}" for j in range(len(batch))]
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=[c["metadata"] for c in batch],
            )

        logger.info("  %d chunks from %s", len(chunks), path.name)
        total += len(chunks)

    logger.info("Total indexed into '%s': %d chunks", collection_name, total)
    return total
