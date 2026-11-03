#!/usr/bin/env python3
"""Compile the Celeslib native Win32 GUI stub and render visual previews."""

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
OUT_STUB = BUILD_DIR / "celeslib_gui_stub.exe"


def compile_celeslib_gui() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    res_obj = BUILD_DIR / "celeslib_gui_res.o"

    # 1. Compile Windows resource script (.rc -> .o)
    windres_cmd = [
        "x86_64-w64-mingw32-windres",
        "-i", str(SRC_GUI / "celeslib_gui.rc"),
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
        str(SRC_GUI / "celeslib_gui.cpp"),
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
    print(f"Successfully compiled native Celeslib GUI stub: {OUT_STUB} ({OUT_STUB.stat().st_size:,} bytes)")


def draw_vector_star(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, color: tuple[int, int, int, int]) -> None:
    ir = int(r * 0.3)
    pts = [
        (cx, cy - r),
        (cx + ir, cy - ir),
        (cx + r, cy),
        (cx + ir, cy + ir),
        (cx, cy + r),
        (cx - ir, cy + ir),
        (cx - r, cy),
        (cx - ir, cy - ir),
    ]
    draw.polygon(pts, fill=color)


def draw_vector_folder(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.rectangle([x, y + 3, x + 14, y + 13], outline=color, width=1)
    draw.line([(x, y + 3), (x + 5, y + 3)], fill=color, width=1)
    draw.line([(x + 1, y + 1), (x + 4, y + 1)], fill=color, width=1)
    draw.line([(x, y + 2), (x + 1, y + 1)], fill=color, width=1)
    draw.line([(x + 4, y + 1), (x + 5, y + 3)], fill=color, width=1)


def draw_vector_layers(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.line([(x + 7, y + 1), (x + 13, y + 4), (x + 7, y + 7), (x + 1, y + 4), (x + 7, y + 1)], fill=color, width=1)
    draw.line([(x + 1, y + 8), (x + 7, y + 11), (x + 13, y + 8)], fill=color, width=1)


def draw_vector_globe(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.ellipse([x + 1, y + 1, x + 13, y + 13], outline=color, width=1)
    draw.line([(x + 1, y + 7), (x + 13, y + 7)], fill=color, width=1)
    draw.ellipse([x + 4, y + 1, x + 10, y + 13], outline=color, width=1)


def draw_vector_play(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.polygon([(x, y), (x + 9, y + 6), (x, y + 12)], fill=color)


def draw_vector_rotate(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.arc([x, y, x + 12, y + 12], start=45, end=315, fill=color, width=1)
    draw.polygon([(x + 1, y + 2), (x + 5, y + 2), (x + 1, y + 6)], fill=color)


def draw_vector_check(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.line([(x, y + 6), (x + 4, y + 10), (x + 11, y + 1)], fill=color, width=2)


def draw_vector_phone(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle([x + 1, y, x + 11, y + 14], radius=2, outline=color, width=1)
    draw.line([(x + 4, y + 2), (x + 8, y + 2)], fill=color, width=1)
    draw.ellipse([x + 5, y + 11, x + 7, y + 13], fill=color)


def draw_vector_bolt(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.polygon([(x + 7, y), (x + 1, y + 8), (x + 6, y + 8), (x + 3, y + 14), (x + 11, y + 5), (x + 6, y + 5)], fill=color)


def draw_vector_trash(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.line([(x + 1, y + 3), (x + 11, y + 3)], fill=color, width=1)
    draw.line([(x + 4, y + 1), (x + 8, y + 1)], fill=color, width=1)
    draw.rounded_rectangle([x + 2, y + 4, x + 10, y + 13], radius=1, outline=color, width=1)
    draw.line([(x + 4, y + 6), (x + 4, y + 11)], fill=color, width=1)
    draw.line([(x + 6, y + 6), (x + 6, y + 11)], fill=color, width=1)
    draw.line([(x + 8, y + 6), (x + 8, y + 11)], fill=color, width=1)


def render_celeslib_preview(out_png: Path, lang: str = "id", mode: str = "id") -> None:
    ASSETS_PREVIEWS.mkdir(parents=True, exist_ok=True)
    w, h = 980, 620
    im = Image.new("RGBA", (w, h), (9, 9, 9, 255))
    draw = ImageDraw.Draw(im)

    # Fonts configuration
    font_bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    font_mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]

    f_title = None
    for p in font_bold_paths:
        if os.path.exists(p):
            f_title = ImageFont.truetype(p, 13)
            f_header = ImageFont.truetype(p, 11)
            f_badge = ImageFont.truetype(p, 9)
            break
    if not f_title:
        f_title = ImageFont.load_default()
        f_header = ImageFont.load_default()
        f_badge = ImageFont.load_default()

    f_reg = None
    for p in font_regular_paths:
        if os.path.exists(p):
            f_reg = ImageFont.truetype(p, 10)
            f_sub = ImageFont.truetype(p, 9)
            break
    if not f_reg:
        f_reg = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    f_mono = None
    for p in font_mono_paths:
        if os.path.exists(p):
            f_mono = ImageFont.truetype(p, 10)
            f_mono_sm = ImageFont.truetype(p, 9)
            break
    if not f_mono:
        f_mono = ImageFont.load_default()
        f_mono_sm = ImageFont.load_default()

    # -------------------------------------------------------------
    # Zone 1: Custom Frameless Titlebar (Y: 0..38, X: 0..980)
    # -------------------------------------------------------------
    draw.rectangle([0, 0, w, 38], fill=(9, 9, 9, 255))
    draw.line([(0, 38), (w, 38)], fill=(51, 51, 51, 255), width=1)

    # 4-pointed Star Logo
    draw_vector_star(draw, cx=26, cy=19, r=8, color=(255, 255, 255, 255))

    # Title: Celeslib
    draw.text((42, 11), "Celeslib", fill=(255, 255, 255, 255), font=f_title)

    # Version Pill: v1.0.0
    draw.rounded_rectangle([108, 10, 158, 28], radius=4, fill=(20, 20, 20, 255), outline=(51, 51, 51, 255), width=1)
    draw.text((118, 13), "v1.0.0", fill=(204, 204, 204, 255), font=f_badge)

    # Subtitle: Honor of Kings: Ace Patcher • Game Build 1.4.12
    draw.text((170, 13), "Honor of Kings: Ace Patcher • Game Build 1.4.12", fill=(136, 136, 136, 255), font=f_sub)

    # Window Controls (—, □, ×)
    draw.text((862, 11), "—", fill=(136, 136, 136, 255), font=f_header)
    draw.text((908, 11), "□", fill=(136, 136, 136, 255), font=f_header)
    draw.text((952, 11), "×", fill=(136, 136, 136, 255), font=f_header)

    # -------------------------------------------------------------
    # Zone 2: Connected 3-Column Configuration Strip (Y: 50..146, X: 20..960)
    # -------------------------------------------------------------
    draw.rounded_rectangle([20, 50, 960, 146], radius=10, fill=(13, 13, 13, 255), outline=(51, 51, 51, 255), width=1)

    # Vertical Column Dividers
    draw.line([(420, 62), (420, 134)], fill=(38, 38, 38, 255), width=1)
    draw.line([(710, 62), (710, 134)], fill=(38, 38, 38, 255), width=1)

    # Column 1: Game Directory (X: 20..420)
    draw_vector_folder(draw, 34, 62, (136, 136, 136, 255))
    lbl_game = "DIREKTORI GAME (HOK: ACE)" if lang == "id" else "GAME DIRECTORY (HOK: ACE)"
    draw.text((54, 62), lbl_game, fill=(136, 136, 136, 255), font=f_badge)

    # Auto-Detect Button
    draw.rounded_rectangle([318, 56, 406, 78], radius=4, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw.text((332, 61), "Auto-Detect", fill=(204, 204, 204, 255), font=f_badge)

    # Path Input Box
    draw.rounded_rectangle([34, 86, 312, 120], radius=4, fill=(5, 5, 5, 255), outline=(38, 38, 38, 255), width=1)
    draw.text((44, 96), "C:\\Program Files\\WXQLauncher\\WXQ", fill=(229, 229, 229, 255), font=f_mono_sm)

    # Browse Button
    draw.rounded_rectangle([318, 86, 406, 120], radius=4, fill=(20, 20, 20, 255), outline=(51, 51, 51, 255), width=1)
    lbl_browse = "Pilih Folder" if lang == "id" else "Browse Folder"
    draw.text((330, 96), lbl_browse, fill=(255, 255, 255, 255), font=f_badge)

    # Column 2: Game Patch Mode (X: 420..710)
    draw_vector_layers(draw, 434, 62, (136, 136, 136, 255))
    lbl_pmode = "MODE BAHASA PATCH" if lang == "id" else "GAME PATCH MODE"
    draw.text((454, 62), lbl_pmode, fill=(136, 136, 136, 255), font=f_badge)

    # Segmented Pill Track
    draw.rounded_rectangle([434, 86, 696, 120], radius=6, fill=(5, 5, 5, 255), outline=(51, 51, 51, 255), width=1)
    if mode == "id":
        draw.rounded_rectangle([437, 89, 564, 117], radius=4, fill=(255, 255, 255, 255))
        draw.text((472, 96), "ID Hybrid", fill=(0, 0, 0, 255), font=f_header)
        draw.text((608, 96), "EN Full", fill=(136, 136, 136, 255), font=f_header)
    else:
        draw.rounded_rectangle([566, 89, 693, 117], radius=4, fill=(255, 255, 255, 255))
        draw.text((472, 96), "ID Hybrid", fill=(136, 136, 136, 255), font=f_header)
        draw.text((608, 96), "EN Full", fill=(0, 0, 0, 255), font=f_header)

    sub_pmode = "UI Indonesia + Istilah MOBA English" if mode == "id" else "100% Full English Localization"
    draw.text((434, 126), sub_pmode, fill=(119, 119, 119, 255), font=f_sub)

    # Column 3: Interface Language (X: 710..960)
    draw_vector_globe(draw, 724, 62, (136, 136, 136, 255))
    lbl_ui = "BAHASA UI" if lang == "id" else "UI LANGUAGE"
    draw.text((744, 62), lbl_ui, fill=(136, 136, 136, 255), font=f_badge)

    # Segmented Pill Track
    draw.rounded_rectangle([724, 86, 946, 120], radius=6, fill=(5, 5, 5, 255), outline=(51, 51, 51, 255), width=1)
    if lang == "id":
        draw.rounded_rectangle([727, 89, 834, 117], radius=4, fill=(255, 255, 255, 255))
        draw.text((752, 96), "Indonesia", fill=(0, 0, 0, 255), font=f_header)
        draw.text((864, 96), "English", fill=(136, 136, 136, 255), font=f_header)
    else:
        draw.rounded_rectangle([836, 89, 943, 117], radius=4, fill=(255, 255, 255, 255))
        draw.text((752, 96), "Indonesia", fill=(136, 136, 136, 255), font=f_header)
        draw.text((864, 96), "English", fill=(0, 0, 0, 255), font=f_header)

    sub_ui = "Engine: 508 Tabel • 72.186 Entri" if lang == "id" else "Engine: 508 Tables • 72,186 Entries"
    draw.text((724, 126), sub_ui, fill=(119, 119, 119, 255), font=f_sub)

    # -------------------------------------------------------------
    # Zone 3: Unified Action Toolbar (Y: 158..208, X: 20..960)
    # -------------------------------------------------------------
    draw.rounded_rectangle([20, 158, 960, 208], radius=8, fill=(13, 13, 13, 255), outline=(51, 51, 51, 255), width=1)

    # PC Primary CTA: [Pasang Patch] / [Install Patch]
    draw.rounded_rectangle([30, 166, 186, 200], radius=6, fill=(255, 255, 255, 255))
    draw_vector_play(draw, 46, 175, (0, 0, 0, 255))
    lbl_install = "Pasang Patch" if lang == "id" else "Install Patch"
    draw.text((64, 174), lbl_install, fill=(0, 0, 0, 255), font=f_header)

    # PC Secondary: [Pulihkan] / [Restore]
    draw.rounded_rectangle([194, 166, 326, 200], radius=6, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw_vector_rotate(draw, 206, 175, (255, 255, 255, 255))
    lbl_restore = "Pulihkan" if lang == "id" else "Restore"
    draw.text((226, 174), lbl_restore, fill=(255, 255, 255, 255), font=f_header)

    # PC Secondary: [Periksa] / [Check]
    draw.rounded_rectangle([334, 166, 462, 200], radius=6, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw_vector_check(draw, 346, 175, (255, 255, 255, 255))
    lbl_check = "Periksa" if lang == "id" else "Check"
    draw.text((366, 174), lbl_check, fill=(255, 255, 255, 255), font=f_header)

    # Divider between PC and Android USB
    draw.line([(476, 168), (476, 198)], fill=(38, 38, 38, 255), width=1)

    # Android USB: [Pindai USB] / [Scan USB]
    draw.rounded_rectangle([490, 166, 616, 200], radius=6, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw_vector_phone(draw, 502, 174, (255, 255, 255, 255))
    lbl_scan = "Pindai USB" if lang == "id" else "Scan USB"
    draw.text((520, 174), lbl_scan, fill=(255, 255, 255, 255), font=f_header)

    # Android USB: [Patch APK]
    draw.rounded_rectangle([624, 166, 740, 200], radius=6, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw_vector_bolt(draw, 636, 174, (255, 255, 255, 255))
    draw.text((654, 174), "Patch APK", fill=(255, 255, 255, 255), font=f_header)

    # Android USB: [Pulihkan APK] / [Recover APK]
    draw.rounded_rectangle([748, 166, 868, 200], radius=6, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw_vector_rotate(draw, 758, 175, (255, 255, 255, 255))
    lbl_rec = "Pulihkan APK" if lang == "id" else "Recover APK"
    draw.text((776, 174), lbl_rec, fill=(255, 255, 255, 255), font=f_header)

    # Clear Console Button: [Clear]
    draw.rounded_rectangle([878, 166, 950, 200], radius=6, fill=(9, 9, 9, 255), outline=(51, 51, 51, 255), width=1)
    draw_vector_trash(draw, 888, 175, (136, 136, 136, 255))
    draw.text((904, 174), "Clear", fill=(136, 136, 136, 255), font=f_header)

    # -------------------------------------------------------------
    # Zone 4: Monaco/Executor-Style Diagnostic Console (Y: 220..576, X: 20..960)
    # -------------------------------------------------------------
    draw.rounded_rectangle([20, 220, 960, 576], radius=8, fill=(5, 5, 5, 255), outline=(51, 51, 51, 255), width=1)

    # Console Header Bar (Y: 220..252)
    draw.rectangle([20, 220, 960, 252], fill=(13, 13, 13, 255))
    draw.line([(20, 252), (960, 252)], fill=(38, 38, 38, 255), width=1)

    # Terminal prompt icon & header title
    draw.text((34, 230), ">_", fill=(136, 136, 136, 255), font=f_mono)
    draw.text((54, 230), "output.log — Celeslib Dual-State VFS Engine", fill=(204, 204, 204, 255), font=f_mono)

    # Status Pill (Right-aligned in header)
    draw.rounded_rectangle([840, 226, 948, 246], radius=4, fill=(17, 17, 17, 255), outline=(51, 51, 51, 255), width=1)
    draw.ellipse([848, 232, 856, 240], fill=(34, 197, 94, 255))
    status_str = "SIAP" if lang == "id" else "READY"
    draw.text((864, 229), status_str, fill=(255, 255, 255, 255), font=f_mono_sm)

    # Line-Number Gutter (X: 21..64, Y: 253..575)
    draw.rectangle([21, 253, 64, 575], fill=(9, 9, 9, 255))
    draw.line([(64, 253), (64, 575)], fill=(30, 30, 30, 255), width=1)

    # Right Minimap Rail (X: 908..959, Y: 253..575)
    draw.rectangle([908, 253, 959, 575], fill=(9, 9, 9, 255))
    draw.line([(908, 253), (908, 575)], fill=(30, 30, 30, 255), width=1)
    draw.rounded_rectangle([912, 260, 955, 340], radius=4, fill=(26, 26, 26, 255), outline=(51, 51, 51, 255), width=1)

    # Log Lines
    if lang == "id":
        log_entries = [
            ("[INFO]", "Celeslib Honor of Kings: Ace Patcher v1.0.0 siap."),
            ("[INFO]", "Mode Patch Aktif: Indonesian Hybrid (ID)."),
            ("[OK]", "Instalasi game ditemukan di C:\\Program Files\\WXQLauncher\\WXQ."),
            ("[OK]", "508 tabel Protobuf terverifikasi integritasnya tanpa galat."),
            ("[INFO]", "Sistem siap. Klik 'Pasang Patch' atau 'Periksa' untuk memulai verifikasi VFS."),
        ]
    else:
        log_entries = [
            ("[INFO]", "Celeslib Honor of Kings: Ace Patcher v1.0.0 ready."),
            ("[INFO]", "Active Patch Mode: Full English (EN)."),
            ("[OK]", "Game installation discovered at C:\\Program Files\\WXQLauncher\\WXQ."),
            ("[OK]", "508 Protobuf localization tables verified without errors."),
            ("[INFO]", "System ready. Click 'Install Patch' or 'Check' to begin VFS verification."),
        ]

    # Draw gutter line numbers 1..14
    for line_idx in range(1, 15):
        ly = 262 + (line_idx - 1) * 20
        draw.text((36, ly), f"{line_idx:03d}", fill=(85, 85, 85, 255), font=f_mono_sm)

    # Draw log lines
    for idx, (tag, text) in enumerate(log_entries, 1):
        ly = 262 + (idx - 1) * 20
        tag_col = (34, 197, 94, 255) if tag == "[OK]" else (176, 176, 176, 255)
        draw.text((74, ly), tag, fill=tag_col, font=f_mono)
        draw.text((130, ly), text, fill=(229, 229, 229, 255), font=f_mono)
        # Micro bar on minimap
        draw.line([(918, ly + 4), (948, ly + 4)], fill=tag_col, width=2)

    # -------------------------------------------------------------
    # Zone 5: Bottom Status Bar (Y: 588..620, X: 0..980)
    # -------------------------------------------------------------
    draw.rectangle([0, 588, w, 620], fill=(9, 9, 9, 255))
    draw.line([(0, 588), (w, 588)], fill=(51, 51, 51, 255), width=1)

    # Glowing Green Dot
    draw.ellipse([20, 600, 28, 608], fill=(34, 197, 94, 255))

    # Engine Status
    draw.text((36, 598), "Offline Dual-State VFS Engine • 508 Protobuf Tables • SHA-256 Verified", fill=(204, 204, 204, 255), font=f_sub)

    # Copyright / Version
    draw.text((710, 598), "© 2026 Celeslib • HoK: Ace 1.4.12 • v1.0.0", fill=(136, 136, 136, 255), font=f_sub)

    im.save(out_png)
    print(f"Rendered Celeslib Single-Page UI preview: {out_png}")


def main() -> None:
    compile_celeslib_gui()
    render_celeslib_preview(ASSETS_PREVIEWS / "celeslib_patcher_id.png", lang="id", mode="id")
    render_celeslib_preview(ASSETS_PREVIEWS / "celeslib_patcher_en.png", lang="en", mode="en")


if __name__ == "__main__":
    main()
