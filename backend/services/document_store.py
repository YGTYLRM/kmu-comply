"""
Temporary document storage for company-uploaded files.

Files are encrypted at rest using Fernet (AES-128-CBC + HMAC-SHA256).
The encryption key is derived from DOCUMENT_ENCRYPTION_KEY in the environment,
or auto-generated per process startup if not set (dev mode — key is lost on restart,
which is fine since documents are temp files cleaned up within the job TTL).

Files are written to a temp directory keyed by session_id.
The job manager cleans up by calling clear() after the job TTL expires.
"""
from __future__ import annotations

import logging
import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from tempfile import mkdtemp

logger = logging.getLogger(__name__)

_STORE_ROOT = Path(mkdtemp(prefix="complio_docs_"))
_MAX_FILE_BYTES = 15 * 1024 * 1024   # 15 MB per file
_MAX_TOTAL_BYTES = 60 * 1024 * 1024  # 60 MB per session
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
    # Auto-generate an ephemeral key (lost on restart, acceptable for temp files)
    ephemeral = Fernet.generate_key()
    logger.info("document_store: using ephemeral encryption key (set DOCUMENT_ENCRYPTION_KEY for persistence)")
    return Fernet(ephemeral)


class DocumentStore:
    """
    In-process temp file store. One session per analyze request.
    All files are encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256).
    Thread-safe for reads; writes happen only during upload before analysis starts.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, Path] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        session_dir = _STORE_ROOT / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self._sessions[session_id] = session_dir
        logger.debug("document session created: %s", session_id)
        return session_id

    def save_file(self, session_id: str, filename: str, content: bytes) -> str:
        """
        Encrypt and save one file to a session. Returns the sanitised filename.
        Raises ValueError on oversized or disallowed file types.
        """
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

        # Check total session size (compare plaintext sizes against limit)
        total = sum(f.stat().st_size for f in session_dir.iterdir() if f.is_file())
        if total + len(content) > _MAX_TOTAL_BYTES:
            raise ValueError("Total upload size exceeds the 60 MB session limit.")

        safe_name = _safe_filename(filename)
        dest = session_dir / (safe_name + ".enc")
        dest.write_bytes(_fernet().encrypt(content))
        logger.info("saved (encrypted) doc %s to session %s", safe_name, session_id)
        return safe_name

    def read_file(self, session_id: str, filename: str) -> bytes:
        """Decrypt and return a file's contents."""
        session_dir = self._sessions.get(session_id)
        if session_dir is None:
            raise KeyError(f"Unknown document session: {session_id}")
        enc_path = session_dir / (filename + ".enc")
        if not enc_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        return _fernet().decrypt(enc_path.read_bytes())

    def list_files(self, session_id: str) -> list[Path]:
        """Return paths to encrypted files (callers must use read_file to decrypt)."""
        session_dir = self._sessions.get(session_id)
        if session_dir is None:
            return []
        return sorted(f for f in session_dir.iterdir() if f.suffix == ".enc")

    def clear(self, session_id: str) -> None:
        session_dir = self._sessions.pop(session_id, None)
        if session_dir and session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
            logger.debug("document session cleared: %s", session_id)


def _safe_filename(name: str) -> str:
    """Strip path components and replace dangerous characters."""
    name = Path(name).name
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
    return safe[:120] or "upload"


document_store = DocumentStore()
