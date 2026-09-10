from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Evidence, PreferenceWeight, utc_now_iso


class SQLiteTasteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    context TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_evidence_domain_created
                ON evidence(domain, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_evidence_scope_created
                ON evidence(domain, context, source, created_at DESC);

                CREATE TABLE IF NOT EXISTS preference_weights (
                    domain TEXT NOT NULL,
                    feature TEXT NOT NULL,
                    weight REAL NOT NULL,
                    updates INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(domain, feature)
                );
                """
            )

    def add_evidence(self, evidence: Evidence) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence
                (id, kind, domain, context, source, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (evidence.id, evidence.kind, evidence.domain, evidence.context, evidence.source,
                 json.dumps(evidence.payload, ensure_ascii=False, sort_keys=True), evidence.created_at),
            )

    def get_weights(self, domain: str) -> dict[str, PreferenceWeight]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT domain, feature, weight, updates, updated_at
                   FROM preference_weights WHERE domain = ?""", (domain,)
            ).fetchall()
        return {row["feature"]: PreferenceWeight(domain=row["domain"], feature=row["feature"],
                weight=float(row["weight"]), updates=int(row["updates"]), updated_at=row["updated_at"])
                for row in rows}

    def update_weights(self, domain: str, deltas: dict[str, float]) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            for feature, delta in deltas.items():
                conn.execute(
                    """INSERT INTO preference_weights(domain, feature, weight, updates, updated_at)
                       VALUES (?, ?, ?, 1, ?)
                       ON CONFLICT(domain, feature) DO UPDATE SET
                         weight = preference_weights.weight + excluded.weight,
                         updates = preference_weights.updates + 1,
                         updated_at = excluded.updated_at""",
                    (domain, feature, float(delta), now),
                )

    @staticmethod
    def _evidence_from_row(row: sqlite3.Row) -> Evidence:
        return Evidence(id=row["id"], kind=row["kind"], domain=row["domain"], context=row["context"],
                        source=row["source"], payload=json.loads(row["payload_json"]), created_at=row["created_at"])

    def query_evidence(self, *, domain: str, context: str | None = None, source: str | None = None,
                       kind: str | None = None, limit: int = 20) -> list[Evidence]:
        """Return deterministic newest-first evidence within an explicit provenance scope."""
        if not domain.strip():
            raise ValueError("domain must be non-empty")
        limit = max(1, min(int(limit), 500))
        clauses = ["domain = ?"]
        params: list[object] = [domain]
        for column, value in (("context", context), ("source", source), ("kind", kind)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""SELECT id, kind, domain, context, source, payload_json, created_at
                    FROM evidence WHERE {' AND '.join(clauses)}
                    ORDER BY created_at DESC, id DESC LIMIT ?""", params
            ).fetchall()
        return [self._evidence_from_row(row) for row in rows]

    def recent_evidence(self, domain: str, limit: int = 20) -> list[Evidence]:
        return self.query_evidence(domain=domain, limit=limit)
