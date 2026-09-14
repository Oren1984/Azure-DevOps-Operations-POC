"""SQLite connection handling and schema setup.

A lightweight, file-based store is intentional for a POC: it needs no
external service, requires no credentials, and is trivial to inspect or
delete. See docs/ARCHITECTURE.md for why PostgreSQL was not introduced.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    received_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    resolved INTEGER NOT NULL,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_records (
    id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT NOT NULL
);
"""


class Database:
    """Owns the SQLite connection string and schema for one application instance.

    ``":memory:"`` is supported for tests: it is translated into a shared-cache
    URI so that separate connections (one per repository call) see the same
    in-memory database, and a single keepalive connection is held open for
    the lifetime of this object so the database is not dropped in between.
    """

    def __init__(self, database_path: str) -> None:
        self._keepalive_conn: sqlite3.Connection | None = None

        if database_path == ":memory:":
            self._database_path = f"file:memdb_{uuid.uuid4().hex}?mode=memory&cache=shared"
            self._uri = True
            self._keepalive_conn = sqlite3.connect(self._database_path, uri=True)
        else:
            self._database_path = database_path
            self._uri = database_path.startswith("file:")
            if not self._uri:
                parent = Path(database_path).parent
                if str(parent) not in ("", "."):
                    os.makedirs(parent, exist_ok=True)

        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._database_path, uri=self._uri)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
