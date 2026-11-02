"""Self-contained Python 3.12 Dual-State (ZH->ID & EN->ID) bytecode generator for wxq_patch.

Embeds original marshalled code objects directly as bytes constants so modules execute
identically both from disk and inside PyInstaller's in-memory PYZ.pyz importer on Windows.
"""

from __future__ import annotations


def render_table_catalog_source(orig_marshal_bytes: bytes) -> str:
    return f'''"""Dual-state (ZH->ID and EN->ID) table_catalog module for HoK Ace Indonesian Patcher."""
from __future__ import annotations

import gzip
import json
import marshal
from collections import Counter
from pathlib import Path

_ORIG_MARSHAL = {orig_marshal_bytes!r}
exec(marshal.loads(_ORIG_MARSHAL), globals())

_OrigCatalog = Catalog


class Catalog(_OrigCatalog):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        raw_en_map = data.get("en_to_id")
        if isinstance(raw_en_map, dict):
            self.en_to_id: dict[str, str] = {{
                k: v
                for k, v in raw_en_map.items()
                if isinstance(k, str) and isinstance(v, str) and k != v and k not in self.targets
            }}
        else:
            self.en_to_id = {{}}


def load_catalog(path: Path) -> Catalog:
    path = Path(path)
    cat_file = (path / "catalog.json.gz") if path.is_dir() else path
    with gzip.open(cat_file, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    if "en_to_id" not in payload:
        sibling = cat_file.with_name("en_to_id.json.gz")
        if sibling.exists():
            with gzip.open(sibling, "rt", encoding="utf-8") as mh:
                payload["en_to_id"] = json.load(mh)
    return Catalog(payload)


def translate_table(
    raw: bytes,
    asset: int | str,
    catalog: Catalog,
    *,
    build_output: bool = True,
) -> tuple[bytes | None, Counter]:
    output = bytearray() if build_output else None
    count: Counter = Counter()
    asset_hex = f"{{asset:016X}}" if isinstance(asset, int) else str(asset)
    asset_int = asset if isinstance(asset, int) else 0
    en_to_id: dict[str, str] = getattr(catalog, "en_to_id", {{}})

    for tag, nested, encoded in fields(raw):
        if tag != 10:
            raise ProtobufError("Unexpected top-level field")
        parts = list(fields(nested))
        if len(parts) != 2 or sorted(p[0] for p in parts) != [10, 18]:
            raise ProtobufError("Missing, duplicate, or unknown record fields")

        key = next(p[1].decode("utf-8") for p in parts if p[0] == 10)
        source = next(p[1].decode("utf-8") for p in parts if p[0] == 18)
        count["records"] += 1
        target: str | None = None
        identity = (asset_hex, key, source)

        if identity in catalog.english_updates:
            cand = catalog.english_updates[identity]
            if validate_translation(catalog.english_sources[identity], cand)[0]:
                target = cand
            else:
                count["invalid_translation"] += 1
        elif source in catalog.targets:
            count["already_english"] += 1
        elif CJK_RE.search(source):
            cand = (
                catalog.lookup(asset_int, key, source)
                if isinstance(asset, int)
                else catalog.unique.get(source)
            )
            if cand is None:
                count["unknown"] += 1
            elif validate_translation(source, cand)[0]:
                target = cand
            else:
                count["invalid_translation"] += 1
        elif en_to_id and source in en_to_id:
            cand = en_to_id[source]
            if validate_translation(source, cand)[0]:
                target = cand
            else:
                count["invalid_translation"] += 1

        if target is None or target == source:
            if output is not None:
                output.extend(encoded)
            continue

        value = target.encode("utf-8")
        if output is not None:
            record = b"".join(
                p[2] if p[0] == 10 else (b"\\x12" + encode_varint(len(value)) + value)
                for p in parts
            )
            output.extend(b"\\n" + encode_varint(len(record)) + record)
        count["translated"] += 1

    if not count["records"]:
        raise ProtobufError("Empty table")
    return (bytes(output) if output is not None else None, count)
'''


def render_adaptive_source(orig_marshal_bytes: bytes) -> str:
    return f'''"""Auto-restore Chinese originals before installing Indonesian patch if prior receipt matches."""
from __future__ import annotations

import marshal
from pathlib import Path

_ORIG_MARSHAL = {orig_marshal_bytes!r}
exec(marshal.loads(_ORIG_MARSHAL), globals())

# Rebind Catalog, translate_table, and load_catalog in adaptive globals to use Dual-State engine
from wxq_patch.table_catalog import Catalog, translate_table  # noqa: E402
from wxq_patch.table_catalog import load_catalog as _tc_load_catalog  # noqa: E402


def load_catalog(folder: Path) -> Catalog | None:
    try:
        return _tc_load_catalog(folder)
    except Exception:
        return None


_orig_run = _run

_ID_MESSAGE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "English installed and verified. Unknown text was preserved.",
        "Bahasa Indonesia berhasil dipasang dan diverifikasi. Teks tidak dikenal dipertahankan.",
    ),
    (
        "Saved originals restored and verified.",
        "File asli berhasil dipulihkan dan diverifikasi.",
    ),
    (
        "No matching restore backup. Updated game files will not be overwritten.",
        "Tidak ada cadangan pemulihan yang cocok. File game terbaru tidak ditimpa.",
    ),
    (
        "No safe new replacements found. Unknown Chinese text is preserved.",
        "Tidak ada pembaruan teks baru. Teks tidak dikenal dipertahankan.",
    ),
    (
        "English files are installed, but launcher file-size metadata needs repair.",
        "File Bahasa Indonesia sudah terpasang, tetapi metadata ukuran file launcher perlu diperbaiki.",
    ),
    (
        "Installed package metadata repaired; translated files were already installed.",
        "Metadata paket berhasil diperbaiki; file terjemahan sudah terpasang.",
    ),
    (
        "Interrupted operation recovered; previous files restored and verified.",
        "Operasi yang terputus berhasil dipulihkan; file sebelumnya dikembalikan dan diverifikasi.",
    ),
    (
        "Known translations found in the current files.",
        "Terjemahan yang dikenal ditemukan di dalam file saat ini.",
    ),
    (
        "Offline stage verified; game files unchanged.",
        "Stage offline diverifikasi; file game tidak berubah.",
    ),
    (
        "No installation found. Select the game folder or WXQ.exe.",
        "Instalasi tidak ditemukan. Pilih folder game atau WXQ.exe.",
    ),
    (
        "Select WXQ.exe or a folder containing WXQ.exe and WXQ_Data/Package/builtin.",
        "Pilih WXQ.exe atau folder yang berisi WXQ.exe dan WXQ_Data/Package/builtin.",
    ),
    ("Installation discovered.", "Instalasi ditemukan."),
    (" known strings; ", " string dikenal; "),
    (" unknown left Chinese; ", " tidak dikenal dipertahankan; "),
    (" graphics; ", " grafik; "),
    (" strings skipped for capacity.", " string dilewati karena kapasitas."),
)


def _localize_report_message(report: dict) -> dict:
    if isinstance(report, dict) and isinstance(report.get("message"), str):
        msg = report["message"]
        for en_sub, id_sub in _ID_MESSAGE_REPLACEMENTS:
            if en_sub in msg:
                msg = msg.replace(en_sub, id_sub)
        report["message"] = msg
    return report


def _catalog_fingerprint(assets: Path) -> str:
    cat_path = (assets / "catalog.json.gz") if assets.is_dir() else assets
    if cat_path.exists():
        import hashlib
        return hashlib.sha256(cat_path.read_bytes()).hexdigest()
    return "legacy"


def _needs_pre_install_restore(resolved_game: Path, cat_sha: str) -> bool:
    try:
        matches = _matching_restore_items(resolved_game)
        if not matches:
            return False
        receipt_dirs: set[Path] = set()
        for item in matches:
            if isinstance(item, tuple) and len(item) >= 1 and isinstance(item[0], Path):
                receipt_dirs.add(item[0].parent)
            elif isinstance(item, Path):
                receipt_dirs.add(item.parent if item.is_file() else item)

        if not receipt_dirs:
            root = receipt_root(resolved_game)
            if root.exists():
                for r_json in root.glob("*/receipt.json"):
                    receipt_dirs.add(r_json.parent)

        if not receipt_dirs:
            return False

        for r_dir in receipt_dirs:
            sha_file = r_dir / "patcher_catalog_sha256.txt"
            if sha_file.exists() and sha_file.read_text(encoding="utf-8").strip() == cat_sha:
                return False

        return True
    except Exception:
        return False


def _stamp_receipt_catalog_sha(resolved_game: Path, cat_sha: str) -> None:
    try:
        root = receipt_root(resolved_game)
        if not root.exists():
            return
        for r_json in root.glob("*/receipt.json"):
            sha_file = r_json.parent / "patcher_catalog_sha256.txt"
            sha_file.write_text(cat_sha, encoding="utf-8")
    except Exception:
        pass


def _run(action: str, game: Path, assets: Path, work: Path) -> dict:
    if action == "install":
        resolved_game = Path(game).resolve()
        try:
            cat_sha = _catalog_fingerprint(assets)
            if _needs_pre_install_restore(resolved_game, cat_sha):
                _orig_run("restore", resolved_game, assets, work)
        except Exception:
            pass
    report = _orig_run(action, game, assets, work)
    if action == "install":
        try:
            cat_sha = _catalog_fingerprint(assets)
            if cat_sha:
                resolved_game = Path(game).resolve()
                _stamp_receipt_catalog_sha(resolved_game, cat_sha)
        except Exception:
            pass
    return _localize_report_message(report)
'''
