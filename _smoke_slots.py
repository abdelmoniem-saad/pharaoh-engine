import sys
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, ".")
from src.data import database as db  # noqa: E402

tmp = Path(tempfile.mkdtemp())
db._DEFAULT_DB_DIR = tmp

# Simulate a legacy default.db save
p = db.get_db_path("default")
c = sqlite3.connect(str(p))
c.execute(
    """CREATE TABLE game_state (id INTEGER PRIMARY KEY DEFAULT 1,
    save_name TEXT DEFAULT '', season_year INTEGER DEFAULT 2025,
    current_date TEXT DEFAULT '2025-08-15', user_club_id INTEGER DEFAULT 0,
    user_club_name TEXT DEFAULT '', user_club_name_ar TEXT DEFAULT '',
    manager_name TEXT DEFAULT 'M', rng_seed INTEGER DEFAULT 42,
    day_count INTEGER DEFAULT 0)"""
)
c.execute(
    "INSERT INTO game_state (manager_name, user_club_name) VALUES (?, ?)",
    ("Bob", "Al Ahly"),
)
c.commit()
c.close()

# Legacy migration: default.db -> slot1.db
db.migrate_legacy_default_slot()
assert db.get_db_path("slot1").exists(), "slot1 missing after migration"
assert not p.exists(), "legacy default.db still present"

# Metadata peek
info = db.peek_save_info("slot1")
assert info and info["manager_name"] == "Bob", info
assert info["user_club_name"] == "Al Ahly", info
assert db.peek_save_info("slot2") is None

print("SLOTS_MIGRATE_PEEK_OK ->",
      info["manager_name"], "/", info["user_club_name"])
