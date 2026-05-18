"""
Persistent document vault for company-uploaded files.

Files are encrypted at rest using Fernet (AES-128-CBC + HMAC-SHA256).
Sessions live in DOCUMENT_STORE_DIR (default: backend/data/documents/) and
are cleaned up after DOCUMENT_TTL_SECONDS (default: 7 days), independently
of job TTL. This means users can reference a doc session across multiple
analysis runs without re-uploading.

On startup, existing sessions on disk are automatically recovered.
"""
from __future__ import annotations

import json
import logging
import shutil
import time
import uuid
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_MAX_FILE_BYTES  = 15 * 1024 * 1024   # 15 MB per file
_MAX_TOTAL_BYTES = 60 * 1024 * 1024   # 60 MB per session
_ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}


@lru_cache(maxsize=1)
def _fernet():
    """Return a Fernet instance keyed from settings.document_encryption_key."""
    from cryptography.fernet import Fernet
    from config import settings
    key = settings.document_encryption_key
    if key:
        try:
            return Fernet(key.encode())
        except Exception:
            logger.warning("document_store: invalid DOCUMENT_ENCRYPTION_KEY — generating ephemeral key")
    ephemeral = Fernet.generate_key()
    logger.warning(
        "document_store: ⚠ EPHEMERAL encryption key in use — uploaded documents "
        "will be LOST on process restart. Set DOCUMENT_ENCRYPTION_KEY in .env for persistence."
    )
    return Fernet(ephemeral)


def _store_root() -> Path:
    from config import settings
    root = Path(settings.document_store_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


class DocumentStore:
    """
    Persistent document vault. One session directory per upload batch.
    Each session has a metadata file (meta.json) recording created_at.
    Files are encrypted at rest.
    """

    def __init__(self) -> None:
        # session_id → session_dir (recovered on startup from disk)
        self._sessions: dict[str, Path] = {}

    def recover_sessions(self) -> int:
        """Scan DOCUMENT_STORE_DIR and register any existing sessions. Returns count."""
        root = _store_root()
        count = 0
        for session_dir in root.iterdir():
            if session_dir.is_dir() and (session_dir / "meta.json").exists():
                self._sessions[session_dir.name] = session_dir
                count += 1
        if count:
            logger.info("document_store: recovered %d session(s) from disk", count)
        return count

    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        session_dir = _store_root() / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        meta = {"created_at": time.time(), "session_id": session_id, "user_id": user_id}
        (session_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        self._sessions[session_id] = session_dir
        logger.debug("document session created: %s", session_id)
        return session_id

    def get_session_owner(self, session_id: str) -> str | None:
        """Return the user_id that created this session, or None if unknown."""
        session_dir = self._sessions.get(session_id) or _store_root() / session_id
        meta_path = session_dir / "meta.json"
        if not meta_path.exists():
            return None
        try:
            return json.loads(meta_path.read_text(encoding="utf-8")).get("user_id")
        except Exception:
            return None

    def save_file(self, session_id: str, filename: str, content: bytes) -> str:
        """Encrypt and save one file. Returns the sanitised filename."""
        session_dir = self._sessions.get(session_id)
        if session_dir is None:
            raise KeyError(f"Unknown document session: {session_id}")

        if len(content) > _MAX_FILE_BYTES:
            raise ValueError(f"File '{filename}' exceeds the 15 MB limit.")
        suffix = Path(filename).suffix.lower()
        if suffix not in _ALLOWED_SUFFIXES:
            raise ValueError(
                f"File type '{suffix}' is not supported. Upload PDF or TXT files."
            )
        # Magic bytes check — extension alone is not trustworthy
        if suffix == ".pdf":
            if not content.startswith(b"%PDF"):
                raise ValueError(f"File '{filename}' does not appear to be a valid PDF.")
        elif suffix in (".txt", ".md"):
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError(f"File '{filename}' is not valid UTF-8 text.")

        enc_files = [f for f in session_dir.iterdir() if f.suffix == ".enc"]
        total = sum(f.stat().st_size for f in enc_files)
        if total + len(content) > _MAX_TOTAL_BYTES:
            raise ValueError("Total upload size exceeds the 60 MB session limit.")

        safe_name = _safe_filename(filename)
        dest = session_dir / (safe_name + ".enc")
        dest.write_bytes(_fernet().encrypt(content))
        logger.info("saved (encrypted) doc %s to session %s", safe_name, session_id)
        return safe_name

    def read_file(self, session_id: str, filename: str) -> bytes:
        """Decrypt and return a file's contents."""
        session_dir = self._sessions.get(session_id) or _store_root() / session_id
        if not session_dir.exists():
            raise KeyError(f"Unknown document session: {session_id}")
        enc_path = session_dir / (filename + ".enc")
        if not enc_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        return _fernet().decrypt(enc_path.read_bytes())

    def list_files(self, session_id: str) -> list[Path]:
        """Return paths to encrypted files."""
        session_dir = self._sessions.get(session_id) or _store_root() / session_id
        if not session_dir.exists():
            return []
        return sorted(f for f in session_dir.iterdir() if f.suffix == ".enc")

    def session_created_at(self, session_id: str) -> float:
        """Return session creation timestamp (Unix epoch), or 0 if unknown."""
        session_dir = self._sessions.get(session_id) or _store_root() / session_id
        meta_path = session_dir / "meta.json"
        if not meta_path.exists():
            return 0.0
        try:
            return json.loads(meta_path.read_text(encoding="utf-8")).get("created_at", 0.0)
        except Exception:
            return 0.0

    def clear(self, session_id: str) -> None:
        """Delete a session and all its files."""
        session_dir = self._sessions.pop(session_id, None) or _store_root() / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
            logger.debug("document session cleared: %s", session_id)

    def purge_expired(self, ttl_seconds: int) -> int:
        """Delete sessions older than ttl_seconds. Returns number of sessions purged."""
        root = _store_root()
        cutoff = time.time() - ttl_seconds
        purged = 0
        for session_dir in list(root.iterdir()):
            if not session_dir.is_dir():
                continue
            meta_path = session_dir / "meta.json"
            try:
                created = json.loads(meta_path.read_text(encoding="utf-8")).get("created_at", 0.0)
            except Exception:
                created = 0.0
            if created < cutoff:
                self._sessions.pop(session_dir.name, None)
                shutil.rmtree(session_dir, ignore_errors=True)
                purged += 1
        if purged:
            logger.info("document_store: purged %d expired session(s)", purged)
        return purged


def _safe_filename(name: str) -> str:
    name = Path(name).name
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
    return safe[:120] or "upload"


document_store = DocumentStore()
