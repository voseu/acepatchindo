#!/usr/bin/env python3
"""Compile the Celeslib Xeno v1.3.0 Win32 GUI stub and render visual previews."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
SRC_GUI = ROOT / "src" / "gui"
ASSETS_PREVIEWS = ROOT / "assets" / "previews"
BRAND_DIR = ROOT / "assets" / "branding"
OUT_STUB = BUILD_DIR / "celeslib_xeno_stub.exe"


def compile_xeno_gui() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    res_obj = BUILD_DIR / "celeslib_xeno_res.o"

    # 1. Compile Windows resource script (.rc -> .o)
    windres_cmd = [
        "x86_64-w64-mingw32-windres",
        "-i", str(SRC_GUI / "celeslib_xeno.rc"),
        "-o", str(res_obj),
        "-O", "coff",
    ]
    print("Running:", " ".join(windres_cmd))
    subprocess.run(windres_cmd, check=True, cwd=str(SRC_GUI))

    # 2. Compile C++ GUI executable via MinGW-w64 with -lcrypt32 for CryptoAPI SHA-256
    gxx_cmd = [
        "x86_64-w64-mingw32-g++",
        "-O2",
        "-std=c++17",
        "-municode",
        "-mwindows",
        str(SRC_GUI / "celeslib_xeno_gui.cpp"),
        str(res_obj),
        "-o", str(OUT_STUB),
        "-lgdiplus",
        "-ldwmapi",
        "-luxtheme",
        "-lshlwapi",
        "-lcomdlg32",
        "-lshell32",
        "-lole32",
        "-luuid",
        "-lcrypt32",
        "-static-libgcc",
        "-static-libstdc++",
        "-Wl,-Bstatic",
        "-lstdc++",
        "-lpthread",
        "-Wl,-Bdynamic",
        "-s",
    ]
    print("Running:", " ".join(gxx_cmd))
    subprocess.run(gxx_cmd, check=True)
    print(f"Successfully compiled native Xeno GUI stub: {OUT_STUB} ({OUT_STUB.stat().st_size:,} bytes)")


def render_xeno_preview(out_png: Path, lang: str = "id", mode: str = "id", view: str = "patcher") -> None:
    ASSETS_PREVIEWS.mkdir(parents=True, exist_ok=True)
    w, h = 980, 620
    im = Image.new("RGBA", (w, h), (9, 9, 11, 255))
    draw = ImageDraw.Draw(im)

    # 1. Header (0..48)
    draw.rectangle([0, 0, w, 48], fill=(11, 11, 14, 255))
    draw.line([0, 48, w, 48], fill=(36, 36, 46, 255), width=1)

    # Logo
    logo_path = BRAND_DIR / "celeslib_logo_32.png"
    if logo_path.exists():
        logo_img = Image.open(logo_path).convert("RGBA")
        im.paste(logo_img, (16, 8), logo_img)

    # Fonts
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    f_bold = None
    for p in font_paths:
        if os.path.exists(p):
            f_bold = ImageFont.truetype(p, 13)
            f_badge = ImageFont.truetype(p, 10)
            break
    if not f_bold:
        f_bold = ImageFont.load_default()
        f_badge = ImageFont.load_default()

    f_mono = None
    for p in font_mono_paths:
        if os.path.exists(p):
            f_mono = ImageFont.truetype(p, 11)
            break
    if not f_mono:
        f_mono = ImageFont.load_default()

    # Brand Title & Version badges
    draw.text((58, 16), "Celeslib", fill=(244, 244, 245, 255), font=f_bold)

    # v1.0.0 badge
    draw.rounded_rectangle([126, 14, 180, 34], radius=4, fill=(42, 32, 72, 255), outline=(139, 92, 246, 255), width=1)
    draw.text((134, 17), "v1.0.0", fill=(167, 139, 250, 255), font=f_badge)

    # Game Build badge
    draw.rounded_rectangle([188, 14, 308, 34], radius=4, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
    draw.text((196, 17), "Game Build 1.4.12", fill=(161, 161, 170, 255), font=f_badge)

    # Header quick toggles (Vector icons, no emoji to prevent tofu glyphs)
    # UI Toggle
    ui_str = "UI: ID" if lang == "id" else "UI: EN"
    draw.rounded_rectangle([w - 365, 12, w - 275, 36], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
    draw.ellipse([w - 355, 19, w - 347, 27], fill=(96, 165, 250, 255))
    draw.text((w - 342, 17), ui_str, fill=(244, 244, 245, 255), font=f_badge)

    # Mode Toggle
    mode_str = "Mode: ID Hybrid" if mode == "id" else "Mode: EN Full"
    draw.rounded_rectangle([w - 265, 12, w - 120, 36], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
    draw.ellipse([w - 255, 19, w - 247, 27], fill=(139, 92, 246, 255))
    draw.text((w - 242, 17), mode_str, fill=(244, 244, 245, 255), font=f_badge)

    # Window controls
    draw.text((w - 80, 16), "—", fill=(161, 161, 170, 255), font=f_bold)
    draw.text((w - 55, 16), "□", fill=(161, 161, 170, 255), font=f_bold)
    draw.text((w - 30, 16), "×", fill=(161, 161, 170, 255), font=f_bold)

    # 2. Left Sidebar (0..170, 49..h)
    draw.rectangle([0, 49, 170, h], fill=(13, 13, 17, 255))
    draw.line([170, 49, 170, h], fill=(36, 36, 46, 255), width=1)

    # Sidebar collapse toggle
    draw.rounded_rectangle([10, 56, 160, 80], radius=4, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
    draw.text((80, 60), "<", fill=(161, 161, 170, 255), font=f_badge)

    tabs = [
        ("Dashboard", 90, view == "dashboard"),
        ("Patcher", 130, view == "patcher"),
        ("Android (USB)", 170, view == "android"),
        ("Pengaturan" if lang == "id" else "Settings", 210, view == "settings"),
    ]
    for tab_label, tab_y, active in tabs:
        if active:
            draw.rounded_rectangle([10, tab_y, 160, tab_y + 32], radius=6, fill=(42, 32, 72, 255), outline=(139, 92, 246, 255), width=1)
            draw.text((24, tab_y + 8), tab_label, fill=(244, 244, 245, 255), font=f_badge)
        else:
            draw.text((24, tab_y + 8), tab_label, fill=(161, 161, 170, 255), font=f_badge)

    # Sidebar footer
    draw.text((20, h - 40), "Celeslib v1.0.0", fill=(82, 82, 91, 255), font=f_badge)
    draw.text((20, h - 25), "Game Build 1.4.12", fill=(82, 82, 91, 255), font=f_badge)

    # 3. Main Area Toolbar
    main_x = 186
    main_w = w - main_x - 16

    if view == "patcher":
        actions = [
            ("Pasang Patch" if lang == "id" else "Install Patch", 125, True),
            ("Pulihkan File" if lang == "id" else "Restore Files", 115, False),
            ("Periksa File" if lang == "id" else "Check Files", 110, False),
            ("Pilih Folder" if lang == "id" else "Browse Folder", 110, False),
            ("Auto-Detect", 105, False),
            ("Bersihkan" if lang == "id" else "Clear", 90, False),
        ]
        cur_x = main_x
        for label, btn_w, hi in actions:
            if hi:
                draw.rounded_rectangle([cur_x, 62, cur_x + btn_w, 94], radius=6, fill=(124, 58, 237, 255), outline=(167, 139, 250, 255), width=1)
                draw.text((cur_x + 12, 70), label, fill=(244, 244, 245, 255), font=f_badge)
            else:
                draw.rounded_rectangle([cur_x, 62, cur_x + btn_w, 94], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
                draw.text((cur_x + 12, 70), label, fill=(161, 161, 170, 255), font=f_badge)
            cur_x += btn_w + 8

        # Game Path & Status Bar
        bar_y = 104
        draw.rounded_rectangle([main_x, bar_y, main_x + main_w, bar_y + 32], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        path_lbl = "Jalur Game:" if lang == "id" else "Game Path:"
        draw.text((main_x + 12, bar_y + 8), f"{path_lbl} C:\\Program Files\\WXQLauncher\\WXQ (Auto-Detected)", fill=(161, 161, 170, 255), font=f_badge)

        # Status Pill - No duplicate bullet
        badge_w = 110
        badge_x = main_x + main_w - badge_w - 6
        draw.rounded_rectangle([badge_x, bar_y + 4, badge_x + badge_w, bar_y + 28], radius=4, fill=(9, 9, 11, 255), outline=(36, 36, 46, 255), width=1)
        draw.ellipse([badge_x + 8, bar_y + 12, badge_x + 16, bar_y + 20], fill=(16, 185, 129, 255))
        status_str = "SIAP" if lang == "id" else "READY"
        draw.text((badge_x + 22, bar_y + 8), status_str, fill=(244, 244, 245, 255), font=f_badge)

        # Console
        con_y = 146
        con_h = h - con_y - 16
        gutter_w = 42
        minimap_w = 54
        draw.rounded_rectangle([main_x, con_y, main_x + main_w, con_y + con_h], radius=6, fill=(16, 16, 21, 255), outline=(36, 36, 46, 255), width=1)
        draw.rectangle([main_x, con_y, main_x + gutter_w, con_y + con_h], fill=(12, 12, 16, 255))
        draw.line([main_x + gutter_w, con_y, main_x + gutter_w, con_y + con_h], fill=(36, 36, 46, 255), width=1)
        draw.rectangle([main_x + main_w - minimap_w, con_y, main_x + main_w, con_y + con_h], fill=(8, 8, 12, 255))
        draw.line([main_x + main_w - minimap_w, con_y, main_x + main_w - minimap_w, con_y + con_h], fill=(36, 36, 46, 255), width=1)

        if lang == "id":
            lines = [
                ("[INFO]", "Celeslib Honor of Kings: Ace Patcher v1.0.0 siap."),
                ("[INFO]", "Mode Patch Aktif: Indonesian Hybrid (ID)."),
                ("[OK]", "Instalasi game ditemukan di C:\\Program Files\\WXQLauncher\\WXQ."),
                ("[OK]", "508 tabel Protobuf terverifikasi integritasnya tanpa galat."),
                ("[INFO]", "Klik 'Pasang Patch' untuk memulai lokalisasi otomatis.")
            ]
        else:
            lines = [
                ("[INFO]", "Celeslib Honor of Kings: Ace Patcher v1.0.0 ready."),
                ("[INFO]", "Active Patch Mode: Full English (EN)."),
                ("[OK]", "Game installation discovered at C:\\Program Files\\WXQLauncher\\WXQ."),
                ("[OK]", "508 Protobuf localization tables verified without errors."),
                ("[INFO]", "Click 'Install Patch' to begin automatic translation.")
            ]

        for idx, (tag, text) in enumerate(lines, 1):
            ly = con_y + 10 + (idx - 1) * 20
            draw.text((main_x + 8, ly), f"{idx:03d}", fill=(82, 82, 91, 255), font=f_mono)
            tag_col = (167, 139, 250, 255) if tag == "[OK]" else (161, 161, 170, 255)
            draw.text((main_x + gutter_w + 12, ly), tag, fill=tag_col, font=f_mono)
            draw.text((main_x + gutter_w + 64, ly), text, fill=(244, 244, 245, 255), font=f_mono)
            draw.line([main_x + main_w - minimap_w + 8, ly + 6, main_x + main_w - 8, ly + 6], fill=(139, 92, 246, 120), width=2)

    elif view == "dashboard":
        # Dashboard Card
        draw.rounded_rectangle([main_x, 70, main_x + main_w, 250], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        draw.text((main_x + 16, 86), "Celeslib Honor of Kings: Ace Patcher", fill=(244, 244, 245, 255), font=f_bold)
        draw.text((main_x + 16, 110), "Eksekutor Patch & Lokalisasi Honor of Kings: Ace", fill=(161, 161, 170, 255), font=f_badge)
        draw.text((main_x + 16, 134), "Engine Target: Honor of Kings: Ace Build 1.4.12 | Celeslib Native Release v1.0.0", fill=(167, 139, 250, 255), font=f_badge)
        draw.text((main_x + 16, 210), "© 2026 Celeslib • https://celeslib.my.id", fill=(82, 82, 91, 255), font=f_badge)

    elif view == "settings":
        # Card 1: UI Lang
        card_y = 70
        draw.rounded_rectangle([main_x, card_y, main_x + main_w, card_y + 88], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        draw.text((main_x + 16, card_y + 14), "Bahasa Antarmuka (UI Language)", fill=(244, 244, 245, 255), font=f_bold)
        draw.text((main_x + 16, card_y + 36), "Pilih bahasa tampilan untuk menu dan antarmuka aplikasi patcher.", fill=(161, 161, 170, 255), font=f_badge)
        draw.rounded_rectangle([main_x + 16, card_y + 54, main_x + 156, card_y + 78], radius=4, fill=(124, 58, 237, 255))
        draw.text((main_x + 24, card_y + 58), "Bahasa Indonesia", fill=(244, 244, 245, 255), font=f_badge)
        draw.rounded_rectangle([main_x + 166, card_y + 54, main_x + 286, card_y + 78], radius=4, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        draw.text((main_x + 180, card_y + 58), "English", fill=(244, 244, 245, 255), font=f_badge)

        # Card 2: Patch Mode
        card_y += 104
        draw.rounded_rectangle([main_x, card_y, main_x + main_w, card_y + 98], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        draw.text((main_x + 16, card_y + 14), "Mode Bahasa Patch Game (Game Patch Mode)", fill=(244, 244, 245, 255), font=f_bold)
        draw.text((main_x + 16, card_y + 36), "Pilih mode terjemahan: ID Hybrid (Bahasa Indonesia) atau EN Full (Bahasa Inggris 100%).", fill=(161, 161, 170, 255), font=f_badge)
        draw.rounded_rectangle([main_x + 16, card_y + 60, main_x + 196, card_y + 86], radius=4, fill=(124, 58, 237, 255))
        draw.text((main_x + 24, card_y + 65), "Indonesian Hybrid (ID)", fill=(244, 244, 245, 255), font=f_badge)
        draw.rounded_rectangle([main_x + 206, card_y + 60, main_x + 366, card_y + 86], radius=4, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        draw.text((main_x + 220, card_y + 65), "Full English (EN)", fill=(244, 244, 245, 255), font=f_badge)

        # Card 3: Game Dir
        card_y += 114
        draw.rounded_rectangle([main_x, card_y, main_x + main_w, card_y + 80], radius=6, fill=(20, 20, 26, 255), outline=(36, 36, 46, 255), width=1)
        draw.text((main_x + 16, card_y + 14), "Direktori Game Honor of Kings: Ace", fill=(244, 244, 245, 255), font=f_bold)
        draw.text((main_x + 16, card_y + 36), "Jalur folder yang berisi berkas WXQ.exe dan WXQ_Data/Package/builtin.", fill=(161, 161, 170, 255), font=f_badge)
        draw.text((main_x + 16, card_y + 54), "C:\\Program Files\\WXQLauncher\\WXQ", fill=(167, 139, 250, 255), font=f_mono)

    im.save(out_png)
    print(f"Rendered Xeno UI preview: {out_png}")


def main() -> None:
    compile_xeno_gui()
    render_xeno_preview(ASSETS_PREVIEWS / "xeno_patcher_id.png", lang="id", mode="id", view="patcher")
    render_xeno_preview(ASSETS_PREVIEWS / "xeno_patcher_en.png", lang="en", mode="en", view="patcher")
    render_xeno_preview(ASSETS_PREVIEWS / "xeno_dashboard_id.png", lang="id", mode="id", view="dashboard")
    render_xeno_preview(ASSETS_PREVIEWS / "xeno_settings_id.png", lang="id", mode="id", view="settings")


if __name__ == "__main__":
    main()
