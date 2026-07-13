#!/usr/bin/env python3
"""Fail-closed classifier for the OLMBlur case_0006 Windows return contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


SCHEMA = "olmblur-case0006-same-run-internal-return-v1"
CASE_ID = "olmblur__case_0006"
MODULE = "OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PROJECT_DEPTH = 16
COORDINATES = ((29, 71), (314, 14))
HEX32 = re.compile(r"^0x[0-9a-fA-F]{8}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_return(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".zip":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        require(isinstance(payload, dict), "return JSON is not an object")
        return payload
    with zipfile.ZipFile(path) as archive:
        names = [
            name for name in archive.namelist()
            if name.replace("\\", "/").rsplit("/", 1)[-1] == "RETURN_OLMBLUR_CASE0006.json"
        ]
        require(len(names) == 1, "expected one RETURN_OLMBLUR_CASE0006.json")
        payload = json.loads(archive.read(names[0]).decode("utf-8-sig"))
        require(isinstance(payload, dict), "return JSON is not an object")
        return payload


def safe_archive_path(value: object, field: str = "exported_png.archive_path") -> str:
    path = nonempty_string(value, field)
    require("\\" not in path and "\x00" not in path, f"{field} is not a safe relative path")
    parsed = PurePosixPath(path)
    require(not parsed.is_absolute() and parsed.parts and ":" not in parsed.parts[0],
            f"{field} is not a safe relative path")
    require(all(part not in ("", ".", "..") for part in parsed.parts),
            f"{field} contains traversal")
    require(path.lower().endswith(".png"), f"{field} must name a PNG")
    return path


def verify_zip_png(path: Path, payload: dict[str, Any]) -> None:
    """Verify the PNG bytes named by the return, before accepting its metadata."""
    exported = payload.get("exported_png")
    require(isinstance(exported, dict), "exported_png is missing")
    archive_path = safe_archive_path(exported.get("archive_path"))
    with zipfile.ZipFile(path) as archive:
        matches = [info for info in archive.infolist() if info.filename == archive_path]
        require(len(matches) == 1, "exported PNG archive_path is missing or not unique")
        data = archive.read(matches[0])
    require(data.startswith(PNG_SIGNATURE), "exported PNG has an invalid PNG signature")
    expected_size = positive_int(exported.get("png_size_bytes"), "exported_png.png_size_bytes")
    expected_hash = nonempty_string(exported.get("png_sha256"), "exported_png.png_sha256")
    require(HEX64.fullmatch(expected_hash) is not None, "exported_png.png_sha256 is invalid")
    require(len(data) == expected_size, "exported PNG size does not match metadata")
    require(hashlib.sha256(data).hexdigest() == expected_hash.lower(),
            "exported PNG SHA-256 does not match metadata")
def nonempty_string(value: object, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} is missing")
    return value


def positive_int(value: object, field: str) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} is invalid")
    return value


def address(value: object, field: str) -> str:
    text = nonempty_string(value, field)
    require(re.fullmatch(r"0x[0-9a-fA-F]+", text) is not None, f"{field} is not hexadecimal")
    require(int(text, 16) > 0, f"{field} is zero")
    return text.lower()


def coordinate(value: object, field: str) -> tuple[int, int]:
    require(isinstance(value, list) and len(value) == 2, f"{field} is not [x,y]")
    require(all(isinstance(item, int) and not isinstance(item, bool) for item in value), f"{field} is not integral")
    return value[0], value[1]


def bits(value: object, field: str) -> list[str]:
    require(isinstance(value, list) and len(value) == 3, f"{field} must contain three RGB words")
    require(all(isinstance(item, str) and HEX32.fullmatch(item) for item in value), f"{field} contains a non-RGB32 word")
    return [item.lower() for item in value]


def rgb16(value: object, field: str) -> list[int]:
    require(isinstance(value, list) and len(value) == 3, f"{field} must contain three RGB16 words")
    require(all(isinstance(item, int) and not isinstance(item, bool) and 0 <= item <= 65535 for item in value),
            f"{field} contains an invalid RGB16 word")
    return list(value)


def identity(value: object, field: str) -> dict[str, object]:
    require(isinstance(value, dict), f"{field} is missing")
    run_id = nonempty_string(value.get("run_id"), f"{field}.run_id")
    pid = positive_int(value.get("ae_pid"), f"{field}.ae_pid")
    base = address(value.get("module_base"), f"{field}.module_base")
    require(value.get("module") == MODULE, f"{field}.module mismatch")
    require(str(value.get("aex_sha256", "")).lower() == AEX_SHA256, f"{field}.aex_sha256 mismatch")
    require(value.get("project_depth") == PROJECT_DEPTH, f"{field}.project_depth mismatch")
    return {"run_id": run_id, "ae_pid": pid, "module_base": base}


def validate_payload(payload: dict[str, Any], *, png_scope: str = "metadata-only") -> dict[str, object]:
    require(png_scope in ("metadata-only", "zip-png-bytes-verified"), "invalid PNG verification scope")
    require(payload.get("schema") == SCHEMA, "schema mismatch")
    require(payload.get("status") == "answered", f"return is not answered: {payload.get('status')}")
    require(payload.get("case_id") == CASE_ID, "case_id mismatch")
    root_identity = identity(payload.get("run"), "run")

    rows = payload.get("witnesses")
    require(isinstance(rows, list) and len(rows) == len(COORDINATES), "expected exactly two witnesses")
    normalized: dict[tuple[int, int], dict[str, object]] = {}
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"witness {index} is not an object")
        xy = coordinate(row.get("xy"), f"witness[{index}].xy")
        require(xy in COORDINATES and xy not in normalized, f"unexpected or duplicate witness coordinate: {xy}")
        row_identity = identity(row, f"witness[{index}]")
        require(row_identity == root_identity, f"witness[{index}] identity differs from run")
        normalized[xy] = {
            "pre_store_rgb_bits_hex": bits(row.get("pre_store_rgb_bits_hex"), f"witness[{index}].pre_store_rgb_bits_hex"),
            "stored_rgb16": rgb16(row.get("stored_rgb16"), f"witness[{index}].stored_rgb16"),
        }
    require(set(normalized) == set(COORDINATES), "witness coordinate set mismatch")

    exported = payload.get("exported_png")
    require(isinstance(exported, dict), "exported_png is missing")
    export_identity = identity(exported, "exported_png")
    require(export_identity == root_identity, "exported PNG is not from the same run")
    png_sha256 = nonempty_string(exported.get("png_sha256"), "exported_png.png_sha256")
    require(HEX64.fullmatch(png_sha256) is not None, "exported_png.png_sha256 is invalid")
    png_size = positive_int(exported.get("png_size_bytes"), "exported_png.png_size_bytes")
    archive_path = exported.get("archive_path")
    if png_scope == "zip-png-bytes-verified":
        safe_archive_path(archive_path)
    elif archive_path is not None:
        safe_archive_path(archive_path)
    export_rows = exported.get("witnesses")
    require(isinstance(export_rows, list) and len(export_rows) == len(COORDINATES), "expected two exported PNG witnesses")
    export_coords: set[tuple[int, int]] = set()
    for index, row in enumerate(export_rows):
        require(isinstance(row, dict), f"exported PNG witness {index} is not an object")
        xy = coordinate(row.get("xy"), f"exported_png.witnesses[{index}].xy")
        require(xy in COORDINATES and xy not in export_coords, f"unexpected or duplicate exported coordinate: {xy}")
        export_coords.add(xy)
        require(identity(row, f"exported_png.witnesses[{index}]") == root_identity,
                f"exported PNG witness {index} identity differs from run")
        rgba = row.get("rgba16")
        require(isinstance(rgba, list) and len(rgba) == 4, f"exported_png.witnesses[{index}].rgba16 must be RGBA16")
        require(all(isinstance(item, int) and not isinstance(item, bool) and 0 <= item <= 65535 for item in rgba),
                f"exported_png.witnesses[{index}].rgba16 contains an invalid word")
    require(export_coords == set(COORDINATES), "exported PNG coordinate set mismatch")

    return {
        "schema": SCHEMA,
        "classification": "accepted_same_run_internal_store_and_png_identity",
        "evidence_gate": "same-run-pid-module-base-aex-sha-project-depth16-two-witness-store-png",
        "png_verification_scope": png_scope,
        "case_id": CASE_ID,
        "run": root_identity,
        "aex_sha256": AEX_SHA256,
        "project_depth": PROJECT_DEPTH,
        "coordinates": [list(xy) for xy in COORDINATES],
        "witnesses": [normalized[xy] | {"xy": list(xy)} for xy in COORDINATES],
        "exported_png": {
            "archive_path": archive_path,
            "png_sha256": png_sha256.lower(),
            "png_size_bytes": png_size,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    payload = load_return(args.return_path)
    png_scope = "metadata-only"
    if args.return_path.suffix.lower() == ".zip":
        verify_zip_png(args.return_path, payload)
        png_scope = "zip-png-bytes-verified"
    result = validate_payload(payload, png_scope=png_scope)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
