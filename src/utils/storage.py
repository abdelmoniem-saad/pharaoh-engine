"""Writable app storage shared by career saves and appearance preferences."""
import os
from pathlib import Path


def save_directory() -> Path:
    override = os.getenv("PHARAOH_SAVE_DIR")
    if override:
        return Path(override)
    mobile_data = os.getenv("FLET_APP_STORAGE_DATA")
    if mobile_data:
        return Path(mobile_data) / "saves"
    return Path(__file__).resolve().parents[2] / "saves"
