#!/usr/bin/env python3
"""Publish GitHub Release v1.4.12-id.1 and upload Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe + SHA256SUMS.txt."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
EXE_ASSET = DIST_DIR / "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe"
SUMS_ASSET = DIST_DIR / "SHA256SUMS.txt"

REPO = "voseu/acepatchindo"
TAG = "v1.4.12-id.2"
TITLE = "Honor of Kings: Ace Indonesian Patcher v1.4.12-id.2 (Hybrid Gameplay Edition)"

RELEASE_NOTES = """## Honor of Kings: Ace — Patch Bahasa Indonesia (`v1.4.12-id.2` — Hybrid Gameplay Edition)

Rilis pemasang *patch* Bahasa Indonesia **Hybrid Gameplay Edition** untuk **Honor of Kings: Ace (`WXQ.exe`)** berbasis arsitektur QtsVFS `1.4.12`.

### Fitur & Spesifikasi Hybrid Edition
1. **Bahasa Indonesia (`ID`) Khusus Deskripsi Gameplay Inti:**
   - **Kartu Hero:** Seluruh efek kartu hero (*On Play*, *Sacrifice*, *Prepare*, *Awaken*, dan mekanik kartu).
   - **Skill Hero:** Deskripsi skill penuh, ringkasan skill pendek (*collapsed skill*), peningkatan skill Lv.10/40/100, *Combine Skills*, dan *Summon Skills*.
   - **Talent:** *Standard Talents*, *Contestant Lv.6 Exclusive Talents*, mode/brawl talents, dan deskripsi *Talent Cards*.
   - **Kontestan / Lord:** Deskripsi skill aktif/pasif kontestan, aturan misi *Secret Art*, *Secret Art Cards*, dan kartu kemampuan kontestan.
2. **Bahasa Inggris Standar (`EN`) untuk Seluruh Nama & Sistem Non-Gameplay:**
   - **Nama & Judul Entitas:** Seluruh nama Hero, Skill, Talent, dan Kontestan tetap dalam bahasa Inggris resmi, baik sebagai judul kartu maupun saat dirujuk di dalam kalimat deskripsi (misalnya `<color=#FFE897>Symphony of Tides</color>`, `<color=#FFE897>Three Kingdoms Banner</color>`, `<color=#FFE897>Super Copier</color>`, `<color=#FFE897>Build Upgrade</color>`).
   - **Sistem Non-Gameplay:** Antarmuka (UI), Menu, Pengaturan, Lobi, Toko, Tutorial, Loading Tips, Acara, Misi, Pencapaian (*Achievements*), Obrolan Singkat, Gelar Rank, Kosmetik/Skin, serta nama & efek kartu perlengkapan mandiri tetap dalam bahasa Inggris standar.
3. **Pemisahan Presisi 108 String Mandarin Tambahan:**
   - **18 deskripsi gameplay inti** diterjemahkan ke Bahasa Indonesia berkualitas tinggi.
   - **90 string non-target** diterjemahkan ke Bahasa Inggris alami dan terverifikasi.
4. **Pembaruan Satu-Klik Tanpa Kerumitan (*One-Click Auto-Restore*):**
   - Mesin *patcher* secara otomatis mendeteksi dan memulihkan berkas asli Mandarin (`originals/`) terlebih dahulu sebelum memasang versi hybrid apabila mendeteksi rilis sebelumnya (`v1.4.12-id.1` atau *English Patch*), memastikan ~38.000 string UI kembali ke bahasa Inggris tanpa sisa terjemahan lama.
5. **Verifikasi Penuh QtsVFS & Runtime Integrity:**
   - `508/508` tabel Protobuf `.bytes`, `unknown = 0`, `invalid_translation = 0`, `capacity_skipped = 0` di seluruh paket QtsVFS.
   - Integritas penjaga SHA-256 binary GUI Rust dan bootloader CArchive PyInstaller 100% valid.

### Verifikasi SHA-256
```text
83dc4a1f8ca17bb2c1ec6fcfff7f45717b6fed17d19f53a42aa50561b79622b9  Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe
9c502b8f9097ad437bc5f711626b938ea5a815c25a5b2ccc331b6457ae8107a2  ace-worker.exe (embedded @ 0x4CAC4A..0x3838C00)
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
    if view.returncode == 0:
        subprocess.run(
            [
                "gh",
                "release",
                "upload",
                TAG,
                str(EXE_ASSET),
                str(SUMS_ASSET),
                "--clobber",
                "--repo",
                REPO,
            ],
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
                str(EXE_ASSET),
                str(SUMS_ASSET),
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
        for asset_path, ctype in [
            (EXE_ASSET, "application/vnd.microsoft.portable-executable"),
            (SUMS_ASSET, "text/plain; charset=utf-8"),
        ]:
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
    assert EXE_ASSET.exists() and EXE_ASSET.stat().st_size == 59_877_888
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
        "ERROR: GitHub Release API requires authentication (`gh auth login` or `GH_TOKEN`/`GITHUB_TOKEN`). "
        "SSH git push succeeded, but GitHub does not support uploading binary release assets over SSH alone.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

