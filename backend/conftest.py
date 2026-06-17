"""
Root conftest.py — stubs the database so tests run without PostgreSQL.

All production code uses `app.` imports consistently (app.database.session,
app.database.init_db, etc.) so there is no double-import ambiguity.

We only need to:
1. Stub `app.database.session` with an in-memory SQLite engine so no real
   Postgres connection is attempted.
2. Stub `app.database.init_db.init_db` as a no-op so main.py starts cleanly.
"""

import sys
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── SQLite in-memory engine ──────────────────────────────────────────────────
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)
_TestSessionLocal = sessionmaker(
    bind=_test_engine, autoflush=False, autocommit=False
)

_db_session_stub = MagicMock(name="app.database.session")
_db_session_stub.engine = _test_engine
_db_session_stub.SessionLocal = _TestSessionLocal
sys.modules["app.database.session"] = _db_session_stub

# ── Stub init_db so main.py startup never touches Postgres ──────────────────
_db_init_stub = MagicMock(name="app.database.init_db")
_db_init_stub.init_db = MagicMock(return_value=None)
sys.modules["app.database.init_db"] = _db_init_stub
