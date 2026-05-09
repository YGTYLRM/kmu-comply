"""
Temporary document storage for company-uploaded files.

Files are written to a temp directory keyed by session_id.
The job manager cleans up by calling clear() after the job TTL expires.
"""
from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from tempfile import mkdtemp

logger = logging.getLogger(__name__)

_STORE_ROOT = Path(mkdtemp(prefix="complio_docs_"))
_MAX_FILE_BYTES = 15 * 1024 * 1024   # 15 MB per file
_MAX_TOTAL_BYTES = 60 * 1024 * 1024  # 60 MB per session
_ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}


class DocumentStore:
    """
    In-process temp file store. One session per analyze request.
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
        Save one file to a session. Returns the sanitised filename.
        Raises ValueError on oversized or disallowed file types.
        """
        session_dir = self._sessions.get(session_id)
        if session_dir is None:
            raise KeyError(f"Unknown document session: {session_id}")

        # Validate
        if len(content) > _MAX_FILE_BYTES:
            raise ValueError(f"File '{filename}' exceeds the 15 MB limit.")
        suffix = Path(filename).suffix.lower()
        if suffix not in _ALLOWED_SUFFIXES:
            raise ValueError(
                f"File type '{suffix}' is not supported. Upload PDF or TXT files."
            )

        # Check total session size
        total = sum(f.stat().st_size for f in session_dir.iterdir() if f.is_file())
        if total + len(content) > _MAX_TOTAL_BYTES:
            raise ValueError("Total upload size exceeds the 60 MB session limit.")

        safe_name = _safe_filename(filename)
        dest = session_dir / safe_name
        dest.write_bytes(content)
        logger.info("saved doc %s to session %s", safe_name, session_id)
        return safe_name

    def list_files(self, session_id: str) -> list[Path]:
        session_dir = self._sessions.get(session_id)
        if session_dir is None:
            return []
        return sorted(session_dir.iterdir())

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
