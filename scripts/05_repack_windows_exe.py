#!/usr/bin/env python3
"""Deterministically repack PYZ.pyz, catalog.json.gz, ace-worker.exe, and outer Rust GUI .exe."""

from __future__ import annotations

import gzip
import hashlib
import json
import marshal
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG_EXE = ROOT / "reff" / "Honor of Kings Ace English Patcher 1.4.12.exe"
ORIG_PYZ = ROOT / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted" / "PYZ.pyz"
ORIG_CATALOG_GZ = (
    ROOT
    / "Honor of Kings Ace English Patcher 1.4.12.exe_extracted"
    / "catalog"
    / "catalog.json.gz"
)
WXQ_DIR = ROOT / "extracted_source" / "wxq_patch"
ID_CATALOG_GZ = ROOT / "data" / "catalog_checkpoints" / "catalog.json.gz"
EN_TO_ID_JSON = ROOT / "data" / "catalog_checkpoints" / "en_to_id_map.json"
DIST_DIR = ROOT / "dist"
CELESLIB_EXE = DIST_DIR / "Celeslib-HoK-Ace-Patcher-v1.0.0.exe"
COMPAT_EXE = DIST_DIR / "Honor-of-Kings-Ace-Indonesian-Patcher-1.4.12.exe"
OUT_EXE = CELESLIB_EXE
STUB_EXE = ROOT / "build" / "celeslib_gui_stub.exe"
SHA256SUMS_PATH = DIST_DIR / "SHA256SUMS.txt"

SHA256_OFFSET = 0x4CABFA
WORKER_START = 0x4CAC4A
WORKER_END = 0x3838C00
WORKER_SIZE = 53_927_862
OUTER_SIZE = 59_877_888
COOKIE_MAGIC = b"MEI\x0c\x0b\x0a\x0b\x0e"


def build_combined_catalog_gz() -> bytes:
    with gzip.open(ID_CATALOG_GZ, "rt", encoding="utf-8") as f:
        payload = json.load(f)
    en_to_id = json.loads(EN_TO_ID_JSON.read_text(encoding="utf-8"))
    payload["en_to_id"] = en_to_id
    payload["id_to_en"] = {v: k for k, v in en_to_id.items() if k != v}

    if ORIG_CATALOG_GZ.exists():
        with gzip.open(ORIG_CATALOG_GZ, "rt", encoding="utf-8") as f:
            orig_cat = json.load(f)
        orig_unique = orig_cat.get("unique", {})
        cur_unique = payload.get("unique", {})
        payload["zh_to_en_gameplay"] = {
            zh: en_val
            for zh, en_val in orig_unique.items()
            if zh in cur_unique and cur_unique[zh] != en_val
        }
    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return gzip.compress(raw_json, compresslevel=9, mtime=0)


def repack_pyz(orig_pyz_bytes: bytes, patched_modules: dict[str, Path]) -> bytes:
    assert orig_pyz_bytes[:4] == b"PYZ\x00", "Invalid PYZ magic"
    pyc_magic = orig_pyz_bytes[4:8]
    assert pyc_magic == b"\xcb\r\r\n", f"Expected Python 3.12 magic, got {pyc_magic.hex()}"
    (toc_pos,) = struct.unpack("!i", orig_pyz_bytes[8:12])
    header_extra = orig_pyz_bytes[12:17]
    toc: list[tuple[str, tuple[int, int, int]]] = marshal.loads(orig_pyz_bytes[toc_pos:])

    blobs = bytearray()
    new_toc: list[tuple[str, tuple[int, int, int]]] = []
    current_offset = 17
    replaced: set[str] = set()

    for name, (ispkg, dpos, dlen) in toc:
        if name in patched_modules:
            raw_pyc = patched_modules[name].read_bytes()
            assert raw_pyc[:4] == pyc_magic, (
                f"Module {name} compiled with wrong Python magic: {raw_pyc[:4].hex()}"
            )
            code_marshal = raw_pyc[16:]
            # Sanity check unmarshalling before packing
            marshal.loads(code_marshal)
            comp = zlib.compress(code_marshal, level=9)
            replaced.add(name)
        else:
            comp = orig_pyz_bytes[dpos : dpos + dlen]

        new_toc.append((name, (ispkg, current_offset, len(comp))))
        blobs.extend(comp)
        current_offset += len(comp)

    missing = set(patched_modules) - replaced
    assert not missing, f"Modules missing from PYZ TOC: {missing}"

    new_toc_pos = 17 + len(blobs)
    toc_bytes = marshal.dumps(new_toc)
    return (
        b"PYZ\x00"
        + pyc_magic
        + struct.pack("!i", new_toc_pos)
        + header_extra
        + bytes(blobs)
        + toc_bytes
    )


def repack_worker_carchive(
    orig_worker: bytes, new_pyz: bytes, new_catalog_gz: bytes
) -> tuple[bytes, int]:
    assert len(orig_worker) == WORKER_SIZE, (
        f"Unexpected baseline worker size: {len(orig_worker)}"
    )
    cookie_pos = orig_worker.rfind(COOKIE_MAGIC)
    assert cookie_pos == WORKER_SIZE - 88, f"Unexpected MEI cookie offset: {cookie_pos}"

    magic, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack(
        "!8sIIII64s", orig_worker[cookie_pos : cookie_pos + 88]
    )
    overlay_start = cookie_pos + 88 - pkg_len

    pos = overlay_start + toc_off
    end = pos + toc_len
    orig_entries: list[tuple[int, int, int, int, int, str]] = []
    while pos < end:
        (elen,) = struct.unpack("!I", orig_worker[pos : pos + 4])
        edpos, edlen, ulen, ecflag, etype = struct.unpack(
            "!IIIBB", orig_worker[pos + 4 : pos + 18]
        )
        name = orig_worker[pos + 18 : pos + elen].rstrip(b"\x00").decode("utf-8")
        orig_entries.append((edpos, edlen, ulen, ecflag, etype, name))
        pos += elen

    data_blobs = bytearray()
    toc_buf = bytearray()
    replaced_items: set[str] = set()

    for edpos, edlen, ulen, ecflag, etype, name in orig_entries:
        # Omit unused offline visual-diff preview PNGs (catalog\previews\*.png, 6.18 MB)
        # that are never referenced by either the Rust GUI or any wxq_patch module.
        if name.startswith("catalog\\previews\\"):
            continue

        if name == "PYZ.pyz":
            assert ecflag == 0
            raw_payload = new_pyz
            new_ulen = len(new_pyz)
            new_edlen = len(new_pyz)
            replaced_items.add(name)
        elif name == "catalog\\catalog.json.gz":
            assert ecflag == 1
            new_ulen = len(new_catalog_gz)
            raw_payload = zlib.compress(new_catalog_gz, level=9)
            new_edlen = len(raw_payload)
            replaced_items.add(name)
        else:
            raw_payload = orig_worker[
                overlay_start + edpos : overlay_start + edpos + edlen
            ]
            new_ulen = ulen
            new_edlen = edlen

        new_edpos = len(data_blobs)
        data_blobs.extend(raw_payload)

        name_bytes = name.encode("utf-8") + b"\x00"
        base_len = 18 + len(name_bytes)
        pad = (16 - (base_len % 16)) % 16
        new_elen = base_len + pad
        toc_buf.extend(
            struct.pack(
                "!IIIIBB", new_elen, new_edpos, new_edlen, new_ulen, ecflag, etype
            )
            + name_bytes
            + (b"\x00" * pad)
        )

    assert replaced_items == {"PYZ.pyz", "catalog\\catalog.json.gz"}, replaced_items

    new_toc_off = len(data_blobs)
    new_toc_len = len(toc_buf)
    new_overlay = bytes(data_blobs) + bytes(toc_buf)

    pad_len = cookie_pos - (overlay_start + len(new_overlay))
    if pad_len < 0:
        raise RuntimeError(
            f"CArchive exceeded fixed {WORKER_SIZE:,}-byte worker slot by {-pad_len:,} bytes!"
        )

    # Preserve exact pkg_len = cookie_pos + 88 - overlay_start so PyInstaller's C bootloader
    # resolves ArchivePos = cookie_pos + 88 - pkg_len == overlay_start (348,672).
    new_pkg_len = cookie_pos + 88 - overlay_start
    new_cookie = struct.pack(
        "!8sIIII64s", magic, new_pkg_len, new_toc_off, new_toc_len, pyver, pylib
    )
    repacked_worker = (
        orig_worker[:overlay_start] + new_overlay + (b"\x00" * pad_len) + new_cookie
    )
    assert len(repacked_worker) == WORKER_SIZE, (
        f"Worker size mismatch: {len(repacked_worker)} != {WORKER_SIZE}"
    )
    return repacked_worker, pad_len


def build_release_exe() -> dict[str, str | int]:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if not STUB_EXE.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "08_compile_celeslib_gui.py")],
            check=True,
        )

    outer_raw = bytearray(ORIG_EXE.read_bytes())
    assert len(outer_raw) == OUTER_SIZE

    orig_worker = bytes(outer_raw[WORKER_START:WORKER_END])
    new_catalog_gz = build_combined_catalog_gz()
    new_pyz = repack_pyz(
        ORIG_PYZ.read_bytes(),
        {
            "wxq_patch.table_catalog": WXQ_DIR / "table_catalog.pyc",
            "wxq_patch.adaptive": WXQ_DIR / "adaptive.pyc",
        },
    )
    repacked_worker, pad_len = repack_worker_carchive(
        orig_worker, new_pyz, new_catalog_gz
    )

    worker_sha256 = hashlib.sha256(repacked_worker).hexdigest().upper().encode("ascii")

    # Assemble Celeslib Release Executable
    stub_raw = STUB_EXE.read_bytes()
    pad_stub = (16 - (len(stub_raw) % 16)) % 16
    stub_aligned = stub_raw + (b"\x00" * pad_stub)
    marker = b"CELESLIB_WORKER_V1"
    sha_offset = len(stub_aligned) + len(marker)
    header = worker_sha256 + b"\r\n" + b"ace-worker.exe"
    footer = struct.pack("<Q", sha_offset)

    celeslib_payload = (
        stub_aligned
        + marker
        + header
        + repacked_worker
        + footer
    )

    CELESLIB_EXE.write_bytes(celeslib_payload)
    COMPAT_EXE.write_bytes(celeslib_payload)

    exe_sha256 = hashlib.sha256(celeslib_payload).hexdigest()
    worker_sha_lower = worker_sha256.decode("ascii").lower()
    SHA256SUMS_PATH.write_text(
        f"{exe_sha256}  {CELESLIB_EXE.name}\n"
        f"{exe_sha256}  {COMPAT_EXE.name}\n"
        f"{worker_sha_lower}  ace-worker.exe (embedded @ offset 0x{sha_offset + 80:X}..0x{len(celeslib_payload) - 8:X})\n",
        encoding="utf-8",
    )

    summary = {
        "primary_exe_path": str(CELESLIB_EXE),
        "compat_exe_path": str(COMPAT_EXE),
        "exe_size": len(celeslib_payload),
        "exe_sha256": exe_sha256,
        "worker_size": len(repacked_worker),
        "worker_sha256_upper": worker_sha256.decode("ascii"),
        "carchive_zero_pad_bytes": pad_len,
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build_release_exe()

