"""Self-contained Python 3.12 Dual-State (ZH->ID, EN->ID, ZH->EN, ID->EN) bytecode generator for wxq_patch.

Embeds original marshalled code objects directly as bytes constants so modules execute
identically both from disk and inside PyInstaller's in-memory PYZ.pyz importer on Windows.
"""

from __future__ import annotations


def render_table_catalog_source(orig_marshal_bytes: bytes) -> str:
    return f'''"""Dual-state (ZH->ID, EN->ID, ZH->EN, ID->EN) table_catalog module for Celeslib HoK Ace Patcher."""
from __future__ import annotations

import copy
import gzip
import json
import marshal
import os
import re
from collections import Counter
from pathlib import Path

_ORIG_MARSHAL = {orig_marshal_bytes!r}
exec(marshal.loads(_ORIG_MARSHAL), globals())

_OrigCatalog = Catalog

_PROTECTED_RE = re.compile(r"(<[^>]+>|\{{[^{{}}]+\}}|\[[^\]]+\])")
_NUM_RE = re.compile(r"(?<![#=A-Za-z0-9_])\d+(?:\.\d+)?%?(?![A-Za-z0-9_])")


def _make_zh_num_template(text: str) -> tuple[str, list[str]]:
    tokens = _PROTECTED_RE.split(text)
    nums: list[str] = []
    out: list[str] = []
    for i, part in enumerate(tokens):
        if i % 2 == 1:
            out.append(part)
        else:
            def _sub(m: re.Match) -> str:
                idx = len(nums)
                nums.append(m.group(0))
                return f"\\x01N{{idx}}\\x01"
            out.append(_NUM_RE.sub(_sub, part))
    return "".join(out), nums


def _make_id_num_template(text_id: str, nums_zh: list[str]) -> str:
    tokens = _PROTECTED_RE.split(text_id)
    zh_matched = [False] * len(nums_zh)
    out: list[str] = []
    cursor = 0
    for i, part in enumerate(tokens):
        if i % 2 == 1:
            out.append(part)
        else:
            def _sub(m: re.Match) -> str:
                nonlocal cursor
                val = m.group(0)
                idx = -1
                for j in range(cursor, len(nums_zh)):
                    if not zh_matched[j] and nums_zh[j] == val:
                        idx = j
                        cursor = j + 1
                        break
                if idx == -1:
                    for j in range(len(nums_zh)):
                        if not zh_matched[j] and nums_zh[j] == val:
                            idx = j
                            break
                if idx != -1:
                    zh_matched[idx] = True
                    return f"\\x01N{{idx}}\\x01"
                return val
            out.append(_NUM_RE.sub(_sub, part))
    return "".join(out)


class Catalog(_OrigCatalog):
    def __init__(self, data: dict) -> None:
        patch_lang = os.environ.get("CELESLIB_PATCH_LANG", "id").strip().lower()
        self.patch_lang = "en" if patch_lang == "en" else "id"

        raw_en_to_id = data.get("en_to_id") if isinstance(data.get("en_to_id"), dict) else {{}}
        raw_id_to_en = data.get("id_to_en") if isinstance(data.get("id_to_en"), dict) else {{
            v: k for k, v in raw_en_to_id.items() if isinstance(k, str) and isinstance(v, str) and k != v
        }}
        raw_zh_to_en = data.get("zh_to_en_gameplay") if isinstance(data.get("zh_to_en_gameplay"), dict) else {{}}

        if self.patch_lang == "en" and (raw_zh_to_en or raw_id_to_en):
            data = copy.copy(data)
            if "unique" in data and isinstance(data["unique"], dict):
                u = dict(data["unique"])
                for zh_k, en_v in raw_zh_to_en.items():
                    if zh_k in u:
                        u[zh_k] = en_v
                data["unique"] = u
            if "assets" in data and isinstance(data["assets"], dict):
                new_assets = {{}}
                for a_k, a_map in data["assets"].items():
                    if isinstance(a_map, dict):
                        am = dict(a_map)
                        for rec_k, val in list(am.items()):
                            if isinstance(val, str) and val in raw_id_to_en:
                                am[rec_k] = raw_id_to_en[val]
                        new_assets[a_k] = am
                    else:
                        new_assets[a_k] = a_map
                data["assets"] = new_assets
            if "english_updates" in data and isinstance(data["english_updates"], list):
                new_eu = []
                for item in data["english_updates"]:
                    if isinstance(item, list) and len(item) >= 4 and item[3] in raw_id_to_en:
                        it = list(item)
                        it[3] = raw_id_to_en[item[3]]
                        new_eu.append(it)
                    elif isinstance(item, dict) and item.get("target") in raw_id_to_en:
                        it = dict(item)
                        it["target"] = raw_id_to_en[item["target"]]
                        new_eu.append(it)
                    else:
                        new_eu.append(item)
                data["english_updates"] = new_eu

        super().__init__(data)

        self._zh_num_templates: dict[str, tuple[str, int]] = {{}}
        if hasattr(self, "unique") and isinstance(self.unique, dict):
            for zh, id_val in self.unique.items():
                if isinstance(zh, str) and isinstance(id_val, str) and len(zh) >= 8 and zh != id_val:
                    tpl_zh, nums_zh = _make_zh_num_template(zh)
                    if nums_zh:
                        tpl_id = _make_id_num_template(id_val, nums_zh)
                        self._zh_num_templates[tpl_zh] = (tpl_id, len(nums_zh))

        if self.patch_lang == "en":
            self.en_to_id: dict[str, str] = {{
                k: v
                for k, v in raw_id_to_en.items()
                if isinstance(k, str) and isinstance(v, str) and k != v and k not in self.targets
            }}
        else:
            self.en_to_id = {{
                k: v
                for k, v in raw_en_to_id.items()
                if isinstance(k, str) and isinstance(v, str) and k != v and k not in self.targets
            }}


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
            if cand is None and hasattr(catalog, "_zh_num_templates"):
                tpl_src, nums_src = _make_zh_num_template(source)
                if tpl_src in catalog._zh_num_templates:
                    tpl_id, count_expected = catalog._zh_num_templates[tpl_src]
                    if len(nums_src) == count_expected:
                        subbed = tpl_id
                        for i, n in enumerate(nums_src):
                            subbed = subbed.replace(f"\\x01N{{i}}\\x01", n)
                        if validate_translation(source, subbed)[0]:
                            cand = subbed
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
    return f'''"""Auto-restore Chinese originals before installing patch if prior receipt or mode differs."""
from __future__ import annotations

import marshal
import os
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
        "File terjemahan sudah terpasang, tetapi metadata ukuran file launcher perlu diperbaiki.",
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
    if not (isinstance(report, dict) and isinstance(report.get("message"), str)):
        return report
    msg = report["message"]
    ui_lang = os.environ.get("CELESLIB_UI_LANG", "id").strip().lower()
    patch_lang = os.environ.get("CELESLIB_PATCH_LANG", "id").strip().lower()

    if ui_lang == "en":
        if patch_lang == "id":
            msg = msg.replace(
                "English installed and verified. Unknown text was preserved.",
                "Indonesian Hybrid patch installed and verified. Unknown text was preserved.",
            ).replace(
                "English installed and verified.",
                "Indonesian Hybrid patch installed and verified.",
            ).replace(
                "English files are installed",
                "Indonesian Hybrid files are installed",
            )
        else:
            msg = msg.replace(
                "English installed and verified. Unknown text was preserved.",
                "Full English patch installed and verified. Unknown text was preserved.",
            ).replace(
                "English installed and verified.",
                "Full English patch installed and verified.",
            ).replace(
                "English files are installed",
                "Full English files are installed",
            )
        report["message"] = msg
        return report

    # ui_lang == "id" (default)
    if patch_lang == "en":
        msg = msg.replace(
            "English installed and verified. Unknown text was preserved.",
            "Bahasa Inggris (Full) berhasil dipasang dan diverifikasi. Teks tidak dikenal dipertahankan.",
        ).replace(
            "English installed and verified.",
            "Bahasa Inggris (Full) berhasil dipasang dan diverifikasi.",
        ).replace(
            "English files are installed",
            "File Bahasa Inggris (Full) sudah terpasang",
        )
    for en_sub, id_sub in _ID_MESSAGE_REPLACEMENTS:
        if en_sub in msg:
            msg = msg.replace(en_sub, id_sub)
    report["message"] = msg
    return report


def _catalog_fingerprint(assets: Path) -> str:
    cat_path = (assets / "catalog.json.gz") if assets.is_dir() else assets
    patch_lang = os.environ.get("CELESLIB_PATCH_LANG", "id").strip().lower()
    if cat_path.exists():
        import hashlib
        sha = hashlib.sha256(cat_path.read_bytes()).hexdigest()
        return f"{{sha}}:{{patch_lang}}"
    return f"legacy:{{patch_lang}}"


def _find_all_receipt_dirs(resolved_game: Path) -> set[Path]:
    receipt_dirs: set[Path] = set()
    try:
        matches = _matching_restore_items(resolved_game)
        if matches:
            for item in matches:
                if isinstance(item, tuple) and len(item) >= 1 and isinstance(item[0], Path):
                    receipt_dirs.add(item[0].parent)
                elif isinstance(item, Path):
                    receipt_dirs.add(item.parent if item.is_file() else item)
    except Exception:
        pass

    try:
        root = receipt_root(resolved_game)
        roots = [root]
        root_str = str(root)
        if "HoK Ace English Patch" in root_str:
            roots.append(Path(root_str.replace("HoK Ace English Patch", "Celeslib/HoK Ace Patcher")))
        elif "Celeslib" in root_str:
            roots.append(Path(root_str.replace("Celeslib/HoK Ace Patcher", "HoK Ace English Patch")))
        for r in roots:
            if r.exists():
                for r_json in r.glob("*/receipt.json"):
                    receipt_dirs.add(r_json.parent)
    except Exception:
        pass

    return receipt_dirs


def _needs_pre_install_restore(resolved_game: Path, cat_sha: str) -> bool:
    try:
        receipt_dirs = _find_all_receipt_dirs(resolved_game)
        if not receipt_dirs:
            return False

        for r_dir in receipt_dirs:
            sha_file = r_dir / "patcher_catalog_sha256.txt"
            if not sha_file.exists() or sha_file.read_text(encoding="utf-8").strip() != cat_sha:
                return True

        return False
    except Exception:
        return False


def _stamp_receipt_catalog_sha(resolved_game: Path, cat_sha: str) -> None:
    try:
        receipt_dirs = _find_all_receipt_dirs(resolved_game)
        for r_dir in receipt_dirs:
            sha_file = r_dir / "patcher_catalog_sha256.txt"
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
