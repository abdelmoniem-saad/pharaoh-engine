"""Never let tests create, migrate or overwrite a real career or preference file."""
import pytest


@pytest.fixture(autouse=True)
def isolated_app_storage(tmp_path, monkeypatch):
    from src.data import database
    from src.utils import prefs
    database.close()
    monkeypatch.setattr(database, "_DEFAULT_DB_DIR", tmp_path)
    monkeypatch.setattr(database, "_startup_backup_done", set())
    monkeypatch.setattr(prefs, "_FILE", tmp_path / "app_prefs.json")
    monkeypatch.setattr(prefs, "_cache", None)
    yield
    database.close()
