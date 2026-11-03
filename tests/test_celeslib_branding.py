from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "assets" / "branding"
HEADER_PATH = ROOT / "src" / "gui" / "celeslib_logo_rgba.h"


def test_celeslib_branding_assets_generated() -> None:
    ico = BRAND_DIR / "celeslib.ico"
    png512 = BRAND_DIR / "celeslib_logo_512.png"
    png64 = BRAND_DIR / "celeslib_logo_64.png"
    png32 = BRAND_DIR / "celeslib_logo_32.png"

    assert ico.exists() and ico.stat().st_size > 1_000
    assert png512.exists() and png512.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert png64.exists() and png64.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert png32.exists() and png32.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert HEADER_PATH.exists()
    header_txt = HEADER_PATH.read_text(encoding="utf-8")
    assert "CELESLIB_LOGO_64_BGRA" in header_txt
    assert "CELESLIB_LOGO_32_BGRA" in header_txt

