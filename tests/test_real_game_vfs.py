"""Integration test verifying catalog and QtsVFS chunk capacity on real Windows game files."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_ORIGINALS = Path(
    "/run/media/whise/Windows/Users/azzam/AppData/Local/HoK Ace English Patch/"
    "adaptive/b07d115d01fb4a16c6e16a37/1793497168990741300-92b4bcbb/originals"
)


@pytest.mark.skipif(
    not WINDOWS_ORIGINALS.exists(),
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
    assert counts_zh["tables"] == 508
    assert counts_zh.get("unknown", 0) == 0
    assert counts_zh.get("invalid_translation", 0) == 0
    assert counts_zh.get("capacity_skipped", 0) == 0
    assert len(stage_reports) == 6
    assert all(len(r.get("files", [])) > 0 for r in stage_reports)
    assert counts_en["translated"] > 150000
    assert counts_en.get("invalid_translation", 0) == 0
