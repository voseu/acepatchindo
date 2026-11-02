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

Rilis perdana pemasang *patch* Bahasa Indonesia mandiri (*standalone*) untuk **Honor of Kings: Ace (`WXQ.exe`)** berbasis arsitektur QtsVFS `1.4.12`.

### Ringkasan Pembaruan & Verifikasi
- **41.483** entri kamus utama (`unique`), termasuk **108 string Mandarin (`409` record)** yang sebelumnya terlewat pada *English Patcher 1.4.12*.
- **29.750** entri pembaruan kontekstual (`english_updates`) dan **22.520** pemetaan pembalik tervalidasi (`en_to_id`).
- **Hierarki Terminologi 3-Tier:** Mengutamakan kamus komunitas Indonesia (`hok-ace-translate-id.netlify.app`), ensiklopedia `hokace.wiki`, dan pelestarian 100% kerangka tag Unity (`<a href=...>`, `<color=...>`, `<b>`), *placeholder* (`{0}`), token kontrol (`╫`), serta titik koma (`;`).
- **Dual-State Engine & Auto-Restore:** Otomatis memulihkan cadangan Mandarin (`originals/`) sebelum memasang Bahasa Indonesia apabila mendeteksi instalasi *English Patcher 1.4.12* aktif, serta mendukung *fallback* langsung `Inggris -> Indonesia`.
- **Verifikasi Penuh QtsVFS:** `508/508` tabel Protobuf `.bytes`, `unknown = 0`, `invalid_translation = 0`, `capacity_skipped = 0` di seluruh 6 paket QtsVFS (`1`, `4`, `15`, `19`, `20`, `21`).

### Verifikasi SHA-256
```text
f98af7f76b4b9ae8a250637895c8f57318daf0d95838833f2defb175db9bf293  Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe
2c9952158ff04be043117c9b3cb71ff3db0ac3fef4537b91ee17fccf9946dd11  ace-worker.exe (embedded @ 0x4CAC4A..0x3838C00)
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
