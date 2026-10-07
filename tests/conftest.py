import sqlite3

import pytest


@pytest.fixture
def conn():
    """In-memory database with just the counters table that numbering.py needs."""
    c = sqlite3.connect(":memory:", isolation_level=None)
    c.execute("CREATE TABLE counters (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
    yield c
    c.close()
