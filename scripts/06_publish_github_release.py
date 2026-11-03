#!/usr/bin/env python3
"""Publish GitHub Release v1.0.0-celeslib with Celeslib UI executable and SHA256SUMS.txt."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
CELESLIB_EXE = DIST_DIR / "Celeslib-HoK-Ace-Patcher-v1.0.0.exe"
COMPAT_EXE = DIST_DIR / "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe"
SUMS_ASSET = DIST_DIR / "SHA256SUMS.txt"
PREVIEW_ID = ROOT / "assets" / "previews" / "celeslib_patcher_id.png"
PREVIEW_EN = ROOT / "assets" / "previews" / "celeslib_patcher_en.png"
PREVIEW_DASHBOARD = ROOT / "assets" / "previews" / "celeslib_dashboard_id.png"
PREVIEW_SETTINGS = ROOT / "assets" / "previews" / "celeslib_settings_id.png"

REPO = "voseu/acepatchindo"
TAG = "v1.0.0-celeslib"
TITLE = "Celeslib Honor of Kings: Ace Patcher v1.0.0 (Game Build 1.4.12)"

RELEASE_NOTES = """## Celeslib Honor of Kings: Ace Patcher `v1.0.0` (Target Game Build `1.4.12`)

Rilis resmi pertama **Celeslib Honor of Kings: Ace Patcher v1.0.0** (`Celeslib-HoK-Ace-Patcher-v1.0.0.exe`) dengan antarmuka native Windows x86-64 **Celeslib Ultra-Dark Carbon** (`#09090B` background, aksen `#8B5CF6` Celeslib), pergantian bahasa UI real-time (`ID` / `EN`), dan pilihan mode patch terjemahan game (`Indonesian Hybrid Gameplay` / `Full English`).

---

### Fitur Utama & Pembaruan

1. **Antarmuka Native Celeslib Ultra-Dark Carbon (Win32 + GDI+ + DWM Frameless):**
   - Desain ultra-dark carbon modern dengan layout terstruktur dan responsif.
   - Custom dark titlebar frameless dengan logo pixel-star resmi Celeslib, badge versi `v1.0.0`, target badge `Game Build 1.4.12`, serta tombol kontrol jendela (`—`, `□`, `×`).
   - Left Sidebar navigasi (`Dashboard`, `Patcher`, `Android (USB)`, `Settings`).
   - Top Pill Action Toolbar (`▷ Pasang Patch / Install Patch`, `↺ Pulihkan File / Restore Files`, `🔍 Periksa File / Check Files`, `📁 Pilih Folder / Browse Folder`, `⚡ Auto-Detect`, `🗑 Bersihkan / Clear Log`).
   - Konsol diagnostik monospace bernomor baris (*editor-style line numbers gutter*) dengan pewarnaan sintaks dan minimap visual di sisi kanan.

2. **Dua Mode Patch Terjemahan Game (`🎯 Mode Patch`):**
   - **`ID Hybrid Gameplay` (Default):** Menerjemahkan 100% deskripsi efek kartu hero (*On Play*, *Sacrifice*, *Awaken*), skill aktif/pasif, *Combine/Summon skills*, talent cards, dan deskripsi kontestan ke Bahasa Indonesia berkualitas tinggi, sementara seluruh nama entitas (Hero, Skill, Talent) dan sistem menu/UI tetap dalam bahasa Inggris resmi.
   - **`EN Full English`:** Menerjemahkan 100% berkas game ke Bahasa Inggris resmi standar (memulihkan gameplay ke English dan menerjemahkan string game Mandarin yang belum memiliki terjemahan).
   - Penggantian mode otomatis melakukan *pre-install restore* dari cadangan `originals/` tanpa resiko tumpang tindih terjemahan.

3. **Dukungan Dua Bahasa Antarmuka (`🌐 Bahasa UI`):**
   - Quick header toggle **`[🌐 UI: ID | EN]`** dan pengaturan di menu **Settings** untuk mengganti seluruh teks antarmuka patcher antara **Bahasa Indonesia** dan **English** secara instan.
   - Pesan laporan worker (`result.json`) otomatis disesuaikan dengan bahasa UI yang aktif.

4. **Zero CPDD Branding Leakage:**
   - Seluruh biner luar, resources Windows PE, dan aset grafis 100% menggunakan logo bintang resmi Celeslib dan identitas Celeslib (`0` string CPDD di executable luar).

5. **Integritas Binary & Keamanan Sertifikat:**
   - Penjaga digest SHA-256 64-karakter untuk memvalidasi integritas `ace-worker.exe` sebelum dieksekusi via Windows CryptoAPI.
   - Beroperasi **100% offline** di komputer pengguna tanpa pengumpulan data atau koneksi eksternal. (Sertifikat Mozilla `cacert.pem` yang ada di dalam PyInstaller hanya bawaan pustaka dependensi upstream dan tidak pernah melakukan kontak jaringan saat patch PC).

---

### Verifikasi Berkas & Checksum SHA-256

```text
5174030edcd9589fd708651bc51b9e8de08af5edda38a337c91088fc08bcd808  Celeslib-HoK-Ace-Patcher-v1.0.0.exe
5174030edcd9589fd708651bc51b9e8de08af5edda38a337c91088fc08bcd808  Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe
abbfffec6bab992b31c25e32dc8a33571fd5f279033185f84361af87632253f2  ace-worker.exe (embedded @ offset 0x11C462..0x348A418)
```
"""


def publish_via_gh_cli() -> bool:
    auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if auth.returncode != 0:
        return False

    view = subprocess.run(
        ["gh", "release", "view", TAG, "--repo", REPO],
        capture_output=True,
        text=True,
    )

    # Clean up any legacy preview asset names from GitHub Release
    legacy_names = [
        "xeno_patcher_id.png",
        "xeno_patcher_en.png",
        "xeno_dashboard_id.png",
        "xeno_settings_id.png",
    ]
    for leg_name in legacy_names:
        subprocess.run(
            ["gh", "release", "delete-asset", TAG, leg_name, "-y", "--repo", REPO],
            capture_output=True,
        )

    assets = [
        str(CELESLIB_EXE),
        str(COMPAT_EXE),
        str(SUMS_ASSET),
    ]
    if PREVIEW_ID.exists():
        assets.append(str(PREVIEW_ID))
    if PREVIEW_EN.exists():
        assets.append(str(PREVIEW_EN))
    if PREVIEW_DASHBOARD.exists():
        assets.append(str(PREVIEW_DASHBOARD))
    if PREVIEW_SETTINGS.exists():
        assets.append(str(PREVIEW_SETTINGS))

    if view.returncode == 0:
        subprocess.run(
            ["gh", "release", "upload", TAG, *assets, "--clobber", "--repo", REPO],
            check=True,
        )
        subprocess.run(
            [
                "gh",
                "release",
                "edit",
                TAG,
                "--title",
                TITLE,
                "--notes",
                RELEASE_NOTES,
                "--repo",
                REPO,
            ],
            check=True,
        )
    else:
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                TAG,
                *assets,
                "--repo",
                REPO,
                "--title",
                TITLE,
                "--notes",
                RELEASE_NOTES,
            ],
            check=True,
        )
    return True


def publish_via_rest_api(token: str) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(timeout=300.0, headers=headers) as client:
        resp = client.get(f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}")
        if resp.status_code == 404:
            resp = client.post(
                f"https://api.github.com/repos/{REPO}/releases",
                json={
                    "tag_name": TAG,
                    "target_commitish": "main",
                    "name": TITLE,
                    "body": RELEASE_NOTES,
                    "draft": False,
                    "prerelease": False,
                },
            )
        resp.raise_for_status()
        release = resp.json()
        upload_base = release["upload_url"].split("{")[0]

        existing = {a["name"]: a["id"] for a in release.get("assets", [])}

        # Delete any legacy preview names
        legacy_names = [
            "xeno_patcher_id.png",
            "xeno_patcher_en.png",
            "xeno_dashboard_id.png",
            "xeno_settings_id.png",
        ]
        for leg_name in legacy_names:
            if leg_name in existing:
                client.delete(
                    f"https://api.github.com/repos/{REPO}/releases/assets/{existing[leg_name]}"
                ).raise_for_status()

        assets_to_upload = [
            (CELESLIB_EXE, "application/vnd.microsoft.portable-executable"),
            (COMPAT_EXE, "application/vnd.microsoft.portable-executable"),
            (SUMS_ASSET, "text/plain; charset=utf-8"),
        ]
        if PREVIEW_ID.exists():
            assets_to_upload.append((PREVIEW_ID, "image/png"))
        if PREVIEW_EN.exists():
            assets_to_upload.append((PREVIEW_EN, "image/png"))
        if PREVIEW_DASHBOARD.exists():
            assets_to_upload.append((PREVIEW_DASHBOARD, "image/png"))
        if PREVIEW_SETTINGS.exists():
            assets_to_upload.append((PREVIEW_SETTINGS, "image/png"))

        for asset_path, ctype in assets_to_upload:
            if asset_path.name in existing:
                client.delete(
                    f"https://api.github.com/repos/{REPO}/releases/assets/{existing[asset_path.name]}"
                ).raise_for_status()
            up_resp = client.post(
                upload_base,
                params={"name": asset_path.name},
                headers={"Content-Type": ctype},
                content=asset_path.read_bytes(),
            )
            up_resp.raise_for_status()
            print(f"Uploaded: {up_resp.json()['browser_download_url']}")


def main() -> int:
    assert CELESLIB_EXE.exists() and CELESLIB_EXE.stat().st_size > 50_000_000
    assert COMPAT_EXE.exists() and COMPAT_EXE.stat().st_size > 50_000_000
    assert SUMS_ASSET.exists()

    if publish_via_gh_cli():
        print(f"Published https://github.com/{REPO}/releases/tag/{TAG} via gh CLI.")
        return 0

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        publish_via_rest_api(token)
        print(f"Published https://github.com/{REPO}/releases/tag/{TAG} via GitHub REST API.")
        return 0

    print(
        "ERROR: GitHub Release API requires authentication (`gh auth login` or `GH_TOKEN`/`GITHUB_TOKEN`).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
