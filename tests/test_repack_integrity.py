"""Binary integrity and PyInstaller CArchive extraction tests for the Celeslib Xeno release .exe."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
CELESLIB_EXE = DIST_DIR / "Celeslib-HoK-Ace-Patcher-v1.0.0.exe"
COMPAT_EXE = DIST_DIR / "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe"
SHA256SUMS_PATH = DIST_DIR / "SHA256SUMS.txt"
PYINSTXTRACTOR = ROOT / "tools" / "pyinstxtractor.py"
if not PYINSTXTRACTOR.exists():
    PYINSTXTRACTOR = Path("/tmp/pyinstxtractor.py")

WORKER_EXACT_SIZE = 53_927_862


def test_celeslib_repack_integrity_and_worker_unpack() -> None:
    assert CELESLIB_EXE.exists(), f"Missing primary release executable: {CELESLIB_EXE}"
    assert COMPAT_EXE.exists(), f"Missing compatibility release executable: {COMPAT_EXE}"

    raw = CELESLIB_EXE.read_bytes()
    compat_raw = COMPAT_EXE.read_bytes()
    assert raw == compat_raw, "Compatibility copy must match primary release executable bit-for-bit"

    # 1. PE32+ GUI Header verification
    assert raw[:2] == b"MZ"
    pe_off = struct.unpack_from("<I", raw, 0x3C)[0]
    assert raw[pe_off : pe_off + 4] == b"PE\x00\x00"
    subsystem = struct.unpack_from("<H", raw, pe_off + 24 + 68)[0]
    assert subsystem == 2, f"Expected IMAGE_SUBSYSTEM_WINDOWS_GUI (2), got {subsystem}"

    # 2. Outer GUI Celeslib branding & Zero CPDD leakage
    assert b"Celeslib" in raw
    assert b"v1.0.0" in raw
    assert b"1.4.12" in raw
    assert b"Pasang Patch" in raw
    assert b"Install Patch" in raw
    assert b"CELESLIB_UI_LANG" in raw
    assert b"CELESLIB_PATCH_LANG" in raw
    assert b"CPDD" not in raw
    assert b"cpdd-logo" not in raw

    # Exact CLI argument strings for wxq_patch adaptive and mobile protocols
    assert "--game-dir".encode("utf-16le") in raw
    assert "--work".encode("utf-16le") in raw
    assert "--result".encode("utf-16le") in raw
    assert "mobile-worker".encode("utf-16le") in raw
    assert "--operation".encode("utf-16le") in raw

    # 3. Locate embedded worker using 8-byte footer pointer
    sha_offset = struct.unpack_from("<Q", raw, len(raw) - 8)[0]
    assert 0 < sha_offset < len(raw) - WORKER_EXACT_SIZE

    expected_sha_hdr = raw[sha_offset : sha_offset + 80]
    expected_digest = expected_sha_hdr[:64]
    assert expected_sha_hdr[64:66] == b"\r\n"
    assert expected_sha_hdr[66:80] == b"ace-worker.exe"

    worker_start = sha_offset + 80
    worker_end = len(raw) - 8
    worker = raw[worker_start:worker_end]
    assert len(worker) == WORKER_EXACT_SIZE

    actual_digest = hashlib.sha256(worker).hexdigest().upper().encode("ascii")
    assert actual_digest == expected_digest, f"Digest mismatch: {actual_digest} != {expected_digest}"

    # 4. SHA256SUMS.txt verification
    assert SHA256SUMS_PATH.exists()
    sums_text = SHA256SUMS_PATH.read_text(encoding="utf-8")
    exe_hash = hashlib.sha256(raw).hexdigest()
    assert exe_hash in sums_text
    assert CELESLIB_EXE.name in sums_text
    assert COMPAT_EXE.name in sums_text

    # 5. Unpack embedded ace-worker.exe via pyinstxtractor under Python 3.12
    unpack_root = Path("/tmp/verify_celeslib_worker_unpack")
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
        assert 3_000 <= len(cat["en_to_id"]) <= 6_000
        assert 3_000 <= len(cat["id_to_en"]) <= 6_000
        assert 3_000 <= len(cat["zh_to_en_gameplay"]) <= 6_000

        tc_pyc = ext_dir / "PYZ.pyz_extracted" / "wxq_patch" / "table_catalog.pyc"
        ad_pyc = ext_dir / "PYZ.pyz_extracted" / "wxq_patch" / "adaptive.pyc"
        assert tc_pyc.exists() and tc_pyc.read_bytes()[:4] == b"\xcb\r\r\n"
        assert ad_pyc.exists() and ad_pyc.read_bytes()[:4] == b"\xcb\r\r\n"
    finally:
        shutil.rmtree(unpack_root, ignore_errors=True)
