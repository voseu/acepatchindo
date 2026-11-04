#!/usr/bin/env python3
"""Publish GitHub Release v1.0.0-celeslib with Celeslib Single-Page UI executable and SHA256SUMS.txt."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
CELESLIB_EXE = DIST_DIR / "Celeslib-HoK-Ace-Patcher-v1.0.0.exe"
SUMS_ASSET = DIST_DIR / "SHA256SUMS.txt"
PREVIEW_ID = ROOT / "assets" / "previews" / "celeslib_patcher_id.png"
PREVIEW_EN = ROOT / "assets" / "previews" / "celeslib_patcher_en.png"

REPO = "voseu/acepatchindo"
TAG = "v1.0.0-celeslib"
TITLE = "Celeslib Honor of Kings: Ace Patcher v1.0.0 (Game Build 1.4.12)"

RELEASE_NOTES = """## Celeslib Honor of Kings: Ace Patcher `v1.0.0` (Game Build `1.4.12`)

Aplikasi *patcher* lokalisasi resmi **Celeslib** untuk gim **Honor of Kings: Ace (`WXQ.exe`)** di PC dan Android (USB).

### Fungsi Utama

- **Mode Bahasa Patch (`ID Hybrid` / `EN Full`):**
  - **`ID Hybrid`:** Menerjemahkan seluruh deskripsi efek kartu hero, skill aktif/pasif, talent, dan efek gameplay ke **Bahasa Indonesia**, dengan tetap mempertahankan istilah nama hero/skill dan menu utama dalam Bahasa Inggris.
  - **`EN Full`:** Menerjemahkan seluruh teks gim ke **Bahasa Inggris** penuh.
- **Manajemen Patch PC:**
  - **`Auto-Detect` & `Pilih Folder`:** Mendeteksi lokasi instalasi gim secara otomatis atau memilih folder `WXQ` secara manual.
  - **`Pasang Patch`:** Memasang patch bahasa yang dipilih ke dalam gim.
  - **`Pulihkan`:** Mengembalikan berkas gim ke kondisi asli sebelum di-patch.
  - **`Periksa`:** Memeriksa status berkas gim dan memverifikasi integritas patch yang terpasang.
- **Patching Perangkat Android (USB):**
  - **`Pindai USB`:** Mendeteksi perangkat Android yang terhubung melalui ADB/USB.
  - **`Patch APK` & `Pulihkan APK`:** Memasang patch bahasa atau memulihkan instalasi gim di perangkat Android.
- **Bahasa Antarmuka (`Indonesia` / `English`):** Mengganti bahasa tampilan aplikasi secara instan.

---

### Checksum SHA-256

```text
bb52ffcde848e0988698512aa2e64f6617d6733fc4b2ce5f7ea9148d69cc0d9e  Celeslib-HoK-Ace-Patcher-v1.0.0.exe
abbfffec6bab992b31c25e32dc8a33571fd5f279033185f84361af87632253f2  ace-worker.exe (embedded @ offset 0x11CC62..0x348AC18)
```
"""

OBSOLETE_RELEASES = ["v1.4.12-id.1", "v1.4.12-id.2"]
LEGACY_ASSET_NAMES = [
    "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe",
    "xeno_patcher_id.png",
    "xeno_patcher_en.png",
    "xeno_dashboard_id.png",
    "xeno_settings_id.png",
    "celeslib_dashboard_id.png",
    "celeslib_settings_id.png",
]


def publish_via_gh_cli() -> bool:
    auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if auth.returncode != 0:
        return False

    # Delete obsolete old releases and their tags
    for old_tag in OBSOLETE_RELEASES:
        subprocess.run(
            ["gh", "release", "delete", old_tag, "--cleanup-tag", "-y", "--repo", REPO],
            capture_output=True,
        )

    view = subprocess.run(
        ["gh", "release", "view", TAG, "--repo", REPO],
        capture_output=True,
        text=True,
    )

    # Clean up any legacy asset names from GitHub Release
    for leg_name in LEGACY_ASSET_NAMES:
        subprocess.run(
            ["gh", "release", "delete-asset", TAG, leg_name, "-y", "--repo", REPO],
            capture_output=True,
        )

    assets = [
        str(CELESLIB_EXE),
        str(SUMS_ASSET),
    ]
    if PREVIEW_ID.exists():
        assets.append(str(PREVIEW_ID))
    if PREVIEW_EN.exists():
        assets.append(str(PREVIEW_EN))

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
        else:
            resp.raise_for_status()
            rel_id = resp.json()["id"]
            resp = client.patch(
                f"https://api.github.com/repos/{REPO}/releases/{rel_id}",
                json={
                    "name": TITLE,
                    "body": RELEASE_NOTES,
                },
            )
        resp.raise_for_status()
        release = resp.json()
        upload_base = release["upload_url"].split("{")[0]

        existing = {a["name"]: a["id"] for a in release.get("assets", [])}

        for leg_name in LEGACY_ASSET_NAMES:
            if leg_name in existing:
                client.delete(
                    f"https://api.github.com/repos/{REPO}/releases/assets/{existing[leg_name]}"
                ).raise_for_status()

        assets_to_upload = [
            (CELESLIB_EXE, "application/vnd.microsoft.portable-executable"),
            (SUMS_ASSET, "text/plain; charset=utf-8"),
        ]
        if PREVIEW_ID.exists():
            assets_to_upload.append((PREVIEW_ID, "image/png"))
        if PREVIEW_EN.exists():
            assets_to_upload.append((PREVIEW_EN, "image/png"))

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
