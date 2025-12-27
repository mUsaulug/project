from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Optional
import os
import sqlite3


@dataclass
class ReviewRecord:
    review_id: str
    status: str
    created_at: str
    updated_at: str
    masked_text: str
    category: str
    category_confidence: float
    urgency: str
    urgency_confidence: float
    notes: Optional[str] = None


class ReviewStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._db_path = os.getenv("REVIEW_DB_PATH", "reviews.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_records (
                    review_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    masked_text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    category_confidence REAL NOT NULL,
                    urgency TEXT NOT NULL,
                    urgency_confidence REAL NOT NULL,
                    notes TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_audit (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_review(
        self,
        review_id: str,
        masked_text: str,
        category: str,
        category_confidence: float,
        urgency: str,
        urgency_confidence: float,
    ) -> ReviewRecord:
        now = datetime.now(timezone.utc).isoformat()
        record = ReviewRecord(
            review_id=review_id,
            status="PENDING_REVIEW",
            created_at=now,
            updated_at=now,
            masked_text=masked_text,
            category=category,
            category_confidence=category_confidence,
            urgency=urgency,
            urgency_confidence=urgency_confidence,
        )
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO review_records (
                    review_id, status, created_at, updated_at, masked_text, category,
                    category_confidence, urgency, urgency_confidence, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.review_id,
                    record.status,
                    record.created_at,
                    record.updated_at,
                    record.masked_text,
                    record.category,
                    record.category_confidence,
                    record.urgency,
                    record.urgency_confidence,
                    record.notes,
                ),
            )
            conn.execute(
                """
                INSERT INTO review_audit (review_id, status, notes, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (record.review_id, record.status, record.notes, now),
            )
        return record

    def update_review(self, review_id: str, status: str, notes: Optional[str] = None) -> Optional[ReviewRecord]:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM review_records WHERE review_id = ?
                """,
                (review_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            conn.execute(
                """
                UPDATE review_records
                SET status = ?, updated_at = ?, notes = ?
                WHERE review_id = ?
                """,
                (status, now, notes, review_id),
            )
            conn.execute(
                """
                INSERT INTO review_audit (review_id, status, notes, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (review_id, status, notes, now),
            )
            return ReviewRecord(
                review_id=row["review_id"],
                status=status,
                created_at=row["created_at"],
                updated_at=now,
                masked_text=row["masked_text"],
                category=row["category"],
                category_confidence=row["category_confidence"],
                urgency=row["urgency"],
                urgency_confidence=row["urgency_confidence"],
                notes=notes,
            )


review_store = ReviewStore()
