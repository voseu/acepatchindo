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
TAG = "v1.4.12-id.1"
TITLE = "Honor of Kings: Ace Indonesian Patcher v1.4.12-id.1"

RELEASE_NOTES = """## Honor of Kings: Ace — Patch Bahasa Indonesia (`v1.4.12-id.1`)

Rilis pemasang *patch* Bahasa Indonesia mandiri (*standalone*) untuk **Honor of Kings: Ace (`WXQ.exe`)** berbasis arsitektur QtsVFS `1.4.12`.

### Ringkasan Pembaruan & Verifikasi
- **41.483** entri kamus utama (`unique`), termasuk **108 string Mandarin (`409` record)** yang sebelumnya terlewat pada *English Patcher 1.4.12*.
- **29.750** entri pembaruan kontekstual (`english_updates`) dan **38.828** pemetaan pembalik tervalidasi (`en_to_id`, dari `42.773` kandidat).
- **Hierarki Terminologi 3-Tier & Bebas Indlish (`0` Stopword Hits):** Mengutamakan kamus komunitas Indonesia (`hok-ace-translate-id.netlify.app` termasuk penyelarasan `234` rumus dinamis Skill Hero dan `19` Chess Player/Lord), `624` halaman detail dwibahasa `hokace.wiki`, mesin leksikon & tata bahasa Indonesia (`lexicon_id.py`), serta pelestarian 100% kerangka tag Unity (`<a href=...>`, `<color=...>`, `<b>`), *placeholder* (`{0}`, `[194010p1q2/100]`), token kontrol (`╫`), dan titik koma (`;`).
- **Dual-State Engine & Auto-Restore:** Otomatis memulihkan cadangan Mandarin (`originals/`) sebelum memasang Bahasa Indonesia apabila mendeteksi instalasi *English Patcher 1.4.12* aktif, serta mendukung *fallback* langsung `Inggris -> Indonesia` dengan pesan status runtime berbahasa Indonesia.
- **Verifikasi Penuh QtsVFS:** `508/508` tabel Protobuf `.bytes`, `unknown = 0`, `invalid_translation = 0`, `capacity_skipped = 0` di seluruh 6 paket QtsVFS (`1`, `4`, `15`, `19`, `20`, `21`).

### Verifikasi SHA-256
```text
3baffa77dd167f88c440af370edd747d4c686d8306e3e0823510de02a20c8a50  Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe
08f4e0bfe896aae037a06b2f612cf9c0bf7140623c6bb320401b826aaa1f8f6a  ace-worker.exe (embedded @ 0x4CAC4A..0x3838C00)
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

