"""
SQLite database with WAL mode for evidence storage.
"""
import json
import time
import uuid
from typing import List, Optional, Dict, Any

import aiosqlite


class Database:
    """Manages SQLite database for evidence storage."""

    def __init__(self, db_path: str = "aurora.db"):
        self.db_path = db_path

    async def initialize(self):
        """Create database and enable WAL mode."""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrency
            await db.execute("PRAGMA journal_mode=WAL")

            # Create evidence table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    score REAL,
                    facets TEXT,
                    created_at REAL
                )
            """)

            # Create index on score for sorting
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_evidence_score
                ON evidence(score DESC)
            """)

            # Create index on created_at
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_evidence_created
                ON evidence(created_at DESC)
            """)

            await db.commit()

    async def insert_evidence(
        self,
        url: str,
        title: Optional[str],
        score: float,
        facets: Dict[str, Any]
    ) -> str:
        """Insert new evidence record."""
        evidence_id = str(uuid.uuid4())
        created_at = time.time()
        facets_json = json.dumps(facets)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO evidence (id, url, title, score, facets, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (evidence_id, url, title, score, facets_json, created_at)
            )
            await db.commit()

        return evidence_id

    async def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evidence by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM evidence WHERE id = ?",
                (evidence_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None

    async def list_evidence(
        self,
        limit: int = 100,
        offset: int = 0,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """List evidence with optional filtering."""
        query = "SELECT * FROM evidence"
        params = []

        if min_score is not None:
            query += " WHERE score >= ?"
            params.append(min_score)

        query += " ORDER BY score DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]

    async def count_evidence(self, min_score: Optional[float] = None) -> int:
        """Count evidence records."""
        query = "SELECT COUNT(*) as cnt FROM evidence"
        params = []

        if min_score is not None:
            query += " WHERE score >= ?"
            params.append(min_score)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """Convert row to dictionary."""
        return {
            "id": row["id"],
            "url": row["url"],
            "title": row["title"],
            "score": row["score"],
            "facets": json.loads(row["facets"]) if row["facets"] else {},
            "created_at": row["created_at"]
        }