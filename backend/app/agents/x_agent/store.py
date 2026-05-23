"""Persistent dedup + audit log for the X agent (SQLite, file-backed)."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


_DDL = """
CREATE TABLE IF NOT EXISTS processed_tweets (
    tweet_id        TEXT PRIMARY KEY,
    author_handle   TEXT NOT NULL,
    matched_keyword TEXT,
    decision        TEXT NOT NULL,        -- 'replied' | 'skipped'
    reason          TEXT,
    reply_id        TEXT,
    reply_text      TEXT,
    tweet_text      TEXT,
    processed_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_tweets(processed_at DESC);
"""


class TweetStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_DDL)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def is_processed(self, tweet_id: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM processed_tweets WHERE tweet_id = ?",
                (tweet_id,),
            ).fetchone()
            return row is not None

    def record(
        self,
        *,
        tweet_id: str,
        author_handle: str,
        decision: str,
        reason: str | None = None,
        reply_id: str | None = None,
        reply_text: str | None = None,
        tweet_text: str | None = None,
        matched_keyword: str | None = None,
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_tweets
                  (tweet_id, author_handle, matched_keyword, decision, reason,
                   reply_id, reply_text, tweet_text, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tweet_id, author_handle, matched_keyword, decision, reason,
                    reply_id, reply_text, tweet_text,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def recent(self, limit: int = 20) -> list[dict]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM processed_tweets ORDER BY processed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
