from __future__ import annotations

import struct
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STUB_EXE = ROOT / "build" / "celeslib_gui_stub.exe"
ASSETS_PREVIEWS = ROOT / "assets" / "previews"


def test_compiled_celeslib_gui_stub_pe_headers_and_branding() -> None:
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

    # Must NOT contain xeno / Xeno references
    assert b"xeno" not in raw
    assert b"Xeno" not in raw
    assert "xeno".encode("utf-16le") not in raw
    assert "Xeno".encode("utf-16le") not in raw

    # Exact CLI argument strings for wxq_patch adaptive and mobile protocols
    assert "--game-dir".encode("utf-16le") in raw
    assert "--work".encode("utf-16le") in raw
    assert "--result".encode("utf-16le") in raw
    assert "mobile-worker".encode("utf-16le") in raw
    assert "--operation".encode("utf-16le") in raw

    # Must NOT contain obsolete or invalid CLI flags
    assert '" --json '.encode("utf-16le") not in raw
    assert ' --game "'.encode("utf-16le") not in raw


def test_preview_pngs_integrity_and_no_missing_glyphs() -> None:
    legacy_xeno = list(ASSETS_PREVIEWS.glob("xeno_*.png"))
    assert not legacy_xeno, f"Found legacy xeno preview files: {legacy_xeno}"

    # Assert obsolete multi-page preview files no longer exist
    obsolete_previews = [
        ASSETS_PREVIEWS / "celeslib_dashboard_id.png",
        ASSETS_PREVIEWS / "celeslib_settings_id.png",
    ]
    for obs in obsolete_previews:
        assert not obs.exists(), f"Obsolete multi-page preview should not exist: {obs}"

    expected_previews = [
        ASSETS_PREVIEWS / "celeslib_patcher_id.png",
        ASSETS_PREVIEWS / "celeslib_patcher_en.png",
    ]
    for preview_path in expected_previews:
        assert preview_path.exists(), f"Missing expected preview PNG: {preview_path}"
        with Image.open(preview_path) as im:
            assert im.format == "PNG"
            assert im.size == (980, 620)
            assert im.mode in ("RGB", "RGBA")

            # Check single-page obsidian palette and elements
            rgb_im = im.convert("RGB")
            # 1. Background obsidian canvas (#090909)
            bg_pixel = rgb_im.getpixel((5, 5))
            assert bg_pixel == (9, 9, 9), f"Expected #090909 canvas, got {bg_pixel}"

            # 2. Primary CTA white fill (#FFFFFF) inside [30, 166, 186, 200]
            cta_pixel = rgb_im.getpixel((36, 180))
            assert cta_pixel == (255, 255, 255), f"Expected #FFFFFF CTA fill, got {cta_pixel}"

            # 3. Status emerald green dot (#22C55E = rgb(34, 197, 94))
            dot_pixel = rgb_im.getpixel((24, 604))
            assert dot_pixel == (34, 197, 94), f"Expected #22C55E status dot, got {dot_pixel}"


def test_no_dangling_temporary_iterators_or_null_browseinfo() -> None:
    cpp_src = (ROOT / "src" / "gui" / "celeslib_gui.cpp").read_text(encoding="utf-8")
    # Must never pass .begin() and .end() from two separate temporary cmd.str() calls
    assert "cmd.str().begin()" not in cpp_src
    assert "cmd.str().end()" not in cpp_src
    # Must provide non-NULL pszDisplayName buffer and OleInitialize for SHBrowseForFolderW
    assert "bi.pszDisplayName = display_name;" in cpp_src
    assert "OleInitialize(NULL);" in cpp_src


