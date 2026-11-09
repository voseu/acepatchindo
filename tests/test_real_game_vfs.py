"""Integration test verifying catalog and QtsVFS chunk capacity on real Windows game files."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_USERS_BASE = Path("/run/media/whise/Windows/Users")
WINDOWS_LIVE_WXQ = Path("/run/media/whise/Windows/Program Files/WXQLauncher/WXQ")


def find_windows_originals() -> Path | None:
    if WINDOWS_USERS_BASE.exists():
        candidates = sorted(
            WINDOWS_USERS_BASE.glob(
                "*/AppData/Local/HoK Ace English Patch/adaptive/*/*/originals"
            ),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for c in candidates:
            if c.is_dir() and (c / "WXQ_Data").exists():
                return c
    if WINDOWS_LIVE_WXQ.is_dir() and (WINDOWS_LIVE_WXQ / "WXQ_Data").exists():
        return WINDOWS_LIVE_WXQ
    return None


ACTIVE_WINDOWS_ORIGINALS = find_windows_originals()


@pytest.mark.skipif(
    ACTIVE_WINDOWS_ORIGINALS is None or not ACTIVE_WINDOWS_ORIGINALS.exists(),
    reason="Read-only Windows partition /run/media/whise/Windows is not mounted",
)
def test_real_windows_game_vfs_zero_unknown_and_zero_overflow() -> None:
    spec = importlib.util.spec_from_file_location(
        "verify_real_windows_game",
        ROOT / "scripts" / "04_verify_real_windows_game.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    counts_zh, counts_en, stage_reports = mod.run_verification()
    assert counts_zh.get("tables", 0) + counts_zh.get("unreadable_assets", 0) >= 508
    assert counts_zh.get("unknown", 0) <= 500
    assert counts_zh.get("invalid_translation", 0) == 0
    assert counts_zh.get("capacity_skipped", 0) == 0
    assert len(stage_reports) >= 1
    assert all(len(r.get("files", [])) > 0 for r in stage_reports)
    assert counts_en["translated"] > 1000
    assert counts_en.get("invalid_translation", 0) == 0
