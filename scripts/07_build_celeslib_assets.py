#!/usr/bin/env python3
"""Extract official Celeslib logo from celeslib-webnovel and build .ico, .png, and C++ BGRA headers."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WEBNOVEL_PUBLIC = Path("/home/whise/project/project-pribadi/celeslib-webnovel/public")
BRAND_DIR = ROOT / "assets" / "branding"
GUI_DIR = ROOT / "src" / "gui"


def _to_bgra_c_array(img: Image.Image, var_name: str) -> str:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    raw = rgba.tobytes()
    bgra = bytearray(len(raw))
    # Convert RGBA -> premultiplied-ready BGRA for GDI+ PixelFormat32bppARGB
    for i in range(0, len(raw), 4):
        r, g, b, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
        bgra[i] = b
        bgra[i + 1] = g
        bgra[i + 2] = r
        bgra[i + 3] = a
    hex_vals = ", ".join(f"0x{b:02X}" for b in bgra)
    return (
        f"static const unsigned int {var_name}_WIDTH = {w};\n"
        f"static const unsigned int {var_name}_HEIGHT = {h};\n"
        f"static const unsigned char {var_name}[{len(bgra)}] = {{ {hex_vals} }};\n"
    )


def main() -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    GUI_DIR.mkdir(parents=True, exist_ok=True)

    src_512 = WEBNOVEL_PUBLIC / "web-app-manifest-512x512.png"
    src_webp = WEBNOVEL_PUBLIC / "Logo.webp"
    base_img = Image.open(src_512 if src_512.exists() else src_webp).convert("RGBA")

    img_512 = base_img.resize((512, 512), Image.Resampling.NEAREST)
    img_256 = base_img.resize((256, 256), Image.Resampling.NEAREST)
    img_128 = base_img.resize((128, 128), Image.Resampling.NEAREST)
    img_64 = base_img.resize((64, 64), Image.Resampling.NEAREST)
    img_48 = base_img.resize((48, 48), Image.Resampling.NEAREST)
    img_32 = base_img.resize((32, 32), Image.Resampling.NEAREST)
    img_16 = base_img.resize((16, 16), Image.Resampling.NEAREST)

    img_512.save(BRAND_DIR / "celeslib_logo_512.png", format="PNG")
    img_64.save(BRAND_DIR / "celeslib_logo_64.png", format="PNG")
    img_32.save(BRAND_DIR / "celeslib_logo_32.png", format="PNG")

    img_256.save(
        BRAND_DIR / "celeslib.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    header_content = (
        "#pragma once\n"
        "// Auto-generated from celeslib-webnovel/public/Logo.webp\n\n"
        + _to_bgra_c_array(img_64, "CELESLIB_LOGO_64_BGRA")
        + "\n"
        + _to_bgra_c_array(img_32, "CELESLIB_LOGO_32_BGRA")
    )
    (GUI_DIR / "celeslib_logo_rgba.h").write_text(header_content, encoding="utf-8")
    print("Generated Celeslib branding assets in", BRAND_DIR)


if __name__ == "__main__":
    main()

