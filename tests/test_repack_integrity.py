"""Binary integrity and PyInstaller CArchive extraction tests for the repacked Windows .exe."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_EXE = ROOT / "dist" / "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe"
PYINSTXTRACTOR = Path("/tmp/pyinstxtractor.py")

SHA256_OFFSET = 0x4CABFA
WORKER_START = 0x4CAC4A
WORKER_END = 0x3838C00
WORKER_SIZE = 53_927_862
OUTER_SIZE = 59_877_888


def test_repacked_exe_sizes_sha256_guard_and_pyinstaller_unpack() -> None:
    assert OUT_EXE.exists(), f"Missing repacked executable: {OUT_EXE}"
    raw = OUT_EXE.read_bytes()
    assert len(raw) == OUTER_SIZE

    worker = raw[WORKER_START:WORKER_END]
    assert len(worker) == WORKER_SIZE

    expected_digest = hashlib.sha256(worker).hexdigest().upper().encode("ascii") + b"\r\n"
    actual_digest = raw[SHA256_OFFSET : SHA256_OFFSET + 66]
    assert actual_digest == expected_digest

    # Verify localized outer Rust GUI strings are present
    assert b"Honor of Kings: Ace Patch Indonesia" in raw[WORKER_END:]
    assert b"Pasang Patch ID" in raw[WORKER_END:]
    assert b"Pulihkan File" in raw[WORKER_END:]

    # Unpack embedded ace-worker.exe via pyinstxtractor under Python 3.12 and verify zero errors
    unpack_root = Path("/tmp/verify_unpack_gate6")
    if unpack_root.exists():
        shutil.rmtree(unpack_root)
    unpack_root.mkdir(parents=True, exist_ok=True)
    try:
        worker_file = unpack_root / "ace-worker.exe"
        worker_file.write_bytes(worker)
        proc = subprocess.run(
            [
                "/home/whise/.local/bin/uv",
                "run",
                "--python",
                "3.12",
                str(PYINSTXTRACTOR),
                str(worker_file),
            ],
            cwd=unpack_root,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Successfully extracted pyinstaller archive" in proc.stdout
        assert "[!] Error" not in proc.stdout
        assert "Unmarshalling FAILED" not in proc.stdout

        ext_dir = unpack_root / "ace-worker.exe_extracted"
        cat_gz = ext_dir / "catalog" / "catalog.json.gz"
        assert cat_gz.exists()
        with gzip.open(cat_gz, "rt", encoding="utf-8") as f:
            cat = json.load(f)
        assert len(cat["unique"]) == 41_483
        assert len(cat["english_updates"]) == 29_750
        assert len(cat["en_to_id"]) > 20_000

        tc_pyc = ext_dir / "PYZ.pyz_extracted" / "wxq_patch" / "table_catalog.pyc"
        ad_pyc = ext_dir / "PYZ.pyz_extracted" / "wxq_patch" / "adaptive.pyc"
        assert tc_pyc.exists() and tc_pyc.read_bytes()[:4] == b"\xcb\r\r\n"
        assert ad_pyc.exists() and ad_pyc.read_bytes()[:4] == b"\xcb\r\r\n"
    finally:
        shutil.rmtree(unpack_root, ignore_errors=True)

