from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB_EXE = ROOT / "build" / "celeslib_xeno_stub.exe"


def test_compiled_xeno_gui_stub_pe_headers_and_branding() -> None:
    assert STUB_EXE.exists(), f"Missing compiled GUI stub: {STUB_EXE}"
    raw = STUB_EXE.read_bytes()
    assert raw[:2] == b"MZ"
    pe_off = struct.unpack_from("<I", raw, 0x3C)[0]
    assert raw[pe_off : pe_off + 4] == b"PE\x00\x00"
    subsystem = struct.unpack_from("<H", raw, pe_off + 24 + 68)[0]
    assert subsystem == 2, f"Expected IMAGE_SUBSYSTEM_WINDOWS_GUI (2), got {subsystem}"

    # Must contain Celeslib branding, version v1.0.0, and bilingual ID/EN strings
    assert b"Celeslib" in raw
    assert b"v1.0.0" in raw
    assert b"1.4.12" in raw
    assert b"Pasang Patch" in raw
    assert b"Install Patch" in raw
    assert b"CELESLIB_UI_LANG" in raw
    assert b"CELESLIB_PATCH_LANG" in raw

    # Must NOT contain legacy CPDD branding
    assert b"CPDD" not in raw
    assert b"cpdd-logo" not in raw
