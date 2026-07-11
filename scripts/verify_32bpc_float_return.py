#!/usr/bin/env python3
"""Fail-closed verifier for returned 32bpc float EXR reference artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_CHANNELS = {"R", "G", "B", "A"}
MAGIC = 20000630


class VerificationError(Exception):
    pass


def canonical_sha256(value: Any) -> str:
    """Hash JSON data without allowing platform/order-dependent serialization."""
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def u32(data: bytes, pos: int) -> tuple[int, int]:
    return struct.unpack_from("<I", data, pos)[0], pos + 4


def i32(data: bytes, pos: int) -> tuple[int, int]:
    return struct.unpack_from("<i", data, pos)[0], pos + 4


def cstr(data: bytes, pos: int) -> tuple[str, int]:
    end = data.index(b"\0", pos)
    return data[pos:end].decode("utf-8"), end + 1


def parse_exr_header(path: Path) -> tuple[dict[str, Any], int]:
    data = path.read_bytes()
    if len(data) < 8 or struct.unpack_from("<I", data)[0] != MAGIC:
        raise VerificationError(f"{path}: not an OpenEXR file")
    pos = 8
    attrs: dict[str, Any] = {}
    while True:
        name, pos = cstr(data, pos)
        if not name:
            return attrs, pos
        attr_type, pos = cstr(data, pos)
        size, pos = u32(data, pos)
        value = data[pos : pos + size]
        if len(value) != size:
            raise VerificationError(f"{path}: truncated {name} attribute")
        pos += size
        attrs[name] = (attr_type, value)


def decode_attrs(attrs: dict[str, Any], path: Path) -> dict[str, Any]:
    def required(name: str) -> tuple[str, bytes]:
        if name not in attrs:
            raise VerificationError(f"{path}: missing EXR header attribute {name}")
        return attrs[name]

    typ, raw = required("channels")
    if typ != "chlist":
        raise VerificationError(f"{path}: channels is not chlist")
    channels = []
    pos = 0
    while True:
        name, pos = cstr(raw, pos)
        if not name:
            break
        if pos + 16 > len(raw):
            raise VerificationError(f"{path}: truncated channel entry {name}")
        sample_type, p_linear, x_sampling, y_sampling = struct.unpack_from("<iB3xii", raw, pos)
        pos += 16
        channels.append({"name": name, "sample_type": sample_type, "p_linear": p_linear,
                         "x_sampling": x_sampling, "y_sampling": y_sampling})

    typ, raw = required("dataWindow")
    if typ != "box2i" or len(raw) != 16:
        raise VerificationError(f"{path}: invalid dataWindow")
    min_x, min_y, max_x, max_y = struct.unpack("<4i", raw)
    width, height = max_x - min_x + 1, max_y - min_y + 1
    if width <= 0 or height <= 0:
        raise VerificationError(f"{path}: invalid dimensions {width}x{height}")
    compression = required("compression")[1]
    if len(compression) != 1:
        raise VerificationError(f"{path}: invalid compression attribute")
    result = {"channels": channels, "width": width, "height": height,
              "data_window": [min_x, min_y, max_x, max_y],
              "compression": compression[0], "header": {}}
    for name in ("color_space", "alpha_mode", "renderer", "ae_version"):
        if name in attrs and attrs[name][0] == "string":
            result["header"][name] = attrs[name][1].rstrip(b"\0").decode("utf-8")
    return result


def decode_builtin_scanlines(path: Path, header_end: int, info: dict[str, Any]) -> dict[str, int]:
    if info["compression"] != 0:
        raise VerificationError(f"{path}: no usable EXR decoder for compression code {info['compression']}")
    if any(ch["sample_type"] != 2 for ch in info["channels"]):
        raise VerificationError(f"{path}: channel sample type is not FLOAT")
    if any(ch["x_sampling"] != 1 or ch["y_sampling"] != 1 for ch in info["channels"]):
        raise VerificationError(f"{path}: sampled/subsampled channels are unsupported")
    data = path.read_bytes()
    width, height = info["width"], info["height"]
    counts = {"finite": 0, "nan": 0, "+inf": 0, "-inf": 0}
    expected_row = width * len(info["channels"]) * 4
    table_end = header_end + height * 8
    if table_end > len(data):
        raise VerificationError(f"{path}: truncated scanline offset table")
    offsets = struct.unpack_from("<" + "Q" * height, data, header_end)
    seen_rows: set[int] = set()
    min_y, max_y = info["data_window"][1], info["data_window"][3]
    for offset in offsets:
        if offset < table_end or offset + 8 > len(data):
            raise VerificationError(f"{path}: invalid scanline chunk offset {offset}")
        pos = offset
        y, pos = i32(data, pos)
        if y < min_y or y > max_y:
            raise VerificationError(f"{path}: out-of-range scanline y={y}")
        size, pos = u32(data, pos)
        payload = data[pos : pos + size]
        if len(payload) != size or size != expected_row:
            raise VerificationError(f"{path}: invalid scanline payload size {size}, expected {expected_row}")
        if y in seen_rows:
            raise VerificationError(f"{path}: duplicate scanline y={y}")
        seen_rows.add(y)
        values = struct.unpack("<" + "f" * (size // 4), payload)
        for value in values:
            if math.isnan(value): counts["nan"] += 1
            elif math.isinf(value): counts["+inf" if value > 0 else "-inf"] += 1
            else: counts["finite"] += 1
    expected_rows = set(range(min_y, max_y + 1))
    if seen_rows != expected_rows:
        raise VerificationError(f"{path}: incomplete/misaligned scanline image")
    counts["total"] = width * height * len(info["channels"])
    return counts


def decoder_status() -> str:
    for module in ("OpenEXR", "Imath"):
        try:
            importlib.import_module(module)
            return "OpenEXR Python"
        except ImportError:
            pass
    for tool in ("oiiotool", "exrheader", "magick", "convert"):
        if shutil.which(tool):
            return tool
    return "none"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_float_rgba_exr(path: Path, expected_dimensions: tuple[int, int] | None = None) -> dict[str, Any]:
    """Inspect the small, uncompressed EXR contract used by Mac candidates."""
    raw, header_end = parse_exr_header(path)
    info = decode_attrs(raw, path)
    names = [channel["name"] for channel in info["channels"]]
    if set(names) != EXPECTED_CHANNELS or len(names) != 4:
        raise VerificationError(f"{path}: expected exactly FLOAT RGBA channels, got {names!r}")
    if any(channel["sample_type"] != 2 for channel in info["channels"]):
        raise VerificationError(f"{path}: 32bpc candidate must use FLOAT channels")
    if info["compression"] != 0:
        raise VerificationError(f"{path}: compressed EXR is not accepted for Mac candidate validation")
    dimensions = (info["width"], info["height"])
    if expected_dimensions is not None and dimensions != expected_dimensions:
        raise VerificationError(f"{path}: dimensions {dimensions!r} do not match {expected_dimensions!r}")
    counts = decode_builtin_scanlines(path, header_end, info)
    return {
        "path": str(path),
        "sha256": sha256(path),
        "dimensions": list(dimensions),
        "channel_order": names,
        "sample_types": [channel["sample_type"] for channel in info["channels"]],
        "compression": info["compression"],
        "sample_counts": counts,
    }


def verify_mac_candidate_index(index_path: Path, require_rendered: bool = True) -> dict[str, Any]:
    """Validate a Mac candidate index without making an AE-exact claim."""
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if not isinstance(index, dict) or index.get("kind") != "olm_mac_ae_32bpc_candidate_index":
        raise VerificationError("candidate index has an unexpected kind")
    if index.get("ae_exact_claim") is not False:
        raise VerificationError("candidate index must explicitly disable AE exact claims")
    candidates = index.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise VerificationError("candidate index has no candidates")
    results = []
    pending = 0
    for row in candidates:
        if not isinstance(row, dict):
            raise VerificationError("candidate row must be an object")
        request_id, case_id = row.get("request_id"), row.get("case_id")
        if not isinstance(request_id, str) or not request_id or not isinstance(case_id, str) or not case_id:
            raise VerificationError("candidate row is missing request_id/case_id")
        if row.get("bit_depth") != "32bpc" or row.get("bits_per_channel") != 32:
            raise VerificationError(f"{case_id}: candidate is not declared as 32bpc/32")
        case = row.get("case")
        if not isinstance(case, dict) or case.get("id") != case_id:
            raise VerificationError(f"{case_id}: missing case metadata")
        params = case.get("params_full")
        if not isinstance(params, list) or not params:
            raise VerificationError(f"{case_id}: missing params_full")
        expected_params_hash = canonical_sha256(params)
        if row.get("params_sha256") != expected_params_hash:
            raise VerificationError(f"{case_id}: params_sha256 mismatch")
        state = row.get("state")
        if state != "rendered":
            pending += 1
            if require_rendered:
                raise VerificationError(f"{case_id}: candidate is {state!r}, Mac AE execution is not complete")
            continue
        artifact = row.get("exr")
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            raise VerificationError(f"{case_id}: rendered candidate is missing EXR metadata")
        path = Path(artifact["path"])
        if not path.is_file():
            raise VerificationError(f"{case_id}: candidate EXR not found: {path}")
        inspected = inspect_float_rgba_exr(path)
        if artifact.get("sha256") != inspected["sha256"]:
            raise VerificationError(f"{case_id}: artifact SHA-256 mismatch in candidate index")
        results.append({"request_id": request_id, "case_id": case_id, "exr": inspected, "params_sha256": expected_params_hash})
    return {
        "status": "pass" if pending == 0 else "not_ready",
        "index": str(index_path),
        "rendered": len(results),
        "pending": pending,
        "candidates": results,
    }


def find_artifact(case: dict[str, Any], root: Path) -> tuple[Path, str | None]:
    candidates: list[tuple[Any, str | None]] = []
    for key in ("artifact", "effect_output", "output", "exr", "frame"):
        if key in case: candidates.append((case[key], case.get("output_sha256") or case.get("sha256")))
    artifacts = case.get("artifacts")
    if isinstance(artifacts, dict):
        for key in ("effect_output", "output", "exr", "frame"):
            value = artifacts.get(key)
            if isinstance(value, dict): candidates.append((value.get("path") or value.get("name"), value.get("sha256")))
            elif value: candidates.append((value, None))
    for value, digest in candidates:
        if not isinstance(value, str) or not value: continue
        path = Path(value)
        if not path.is_absolute(): path = root / path
        if path.exists(): return path, digest
    raise VerificationError(f"case {case.get('id')}: returned artifact not found")


def required_hash(case: dict[str, Any], stated: str | None) -> str:
    value = stated or case.get("artifact_sha256") or case.get("output_sha256") or case.get("effect_sha256") or case.get("sha256")
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        raise VerificationError(f"case {case.get('id')}: missing valid artifact SHA-256")
    return value.lower()


def verify(manifest_path: Path, request_path: Path, artifact_root: Path) -> dict[str, Any]:
    # Windows ExtendScript/PowerShell emitters may include a UTF-8 BOM.
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    request = json.loads(request_path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict) or not isinstance(request, dict): raise VerificationError("JSON roots must be objects")
    request_id = request.get("request_id")
    if manifest.get("request_id") and manifest["request_id"] != request_id: raise VerificationError("request_id mismatch")
    scope = request.get("scope")
    if not isinstance(scope, dict) or scope.get("bit_depth") != "32bpc": raise VerificationError("request is not scoped to 32bpc")
    render_sets = request.get("render_sets")
    if not isinstance(render_sets, list) or not any(isinstance(r, dict) and r.get("bits_per_channel") == 32 and r.get("bit_depth") == "32bpc" for r in render_sets):
        raise VerificationError("request has no 32bpc/32 bits-per-channel render set")
    requested = request.get("cases")
    returned = manifest.get("cases")
    if not isinstance(requested, list) or not requested or not isinstance(returned, list): raise VerificationError("request/manifest cases must be non-empty lists")
    req_ids = [c.get("id") for c in requested if isinstance(c, dict)]
    ret_map = {c.get("id"): c for c in returned if isinstance(c, dict)}
    if set(req_ids) != set(ret_map) or len(ret_map) != len(req_ids): raise VerificationError("returned case IDs do not exactly match request case IDs")
    if not manifest.get("ae_version"): raise VerificationError("manifest missing ae_version")
    decoder = decoder_status()
    results = []
    for req in requested:
        case = ret_map[req["id"]]
        if str(case.get("output_format", "")).lower() == "png" or str(case.get("frame", "")).lower().endswith(".png"):
            raise VerificationError(f"case {req['id']}: PNG-only return is probe-only and cannot pass")
        if case.get("float_preserving") is False: raise VerificationError(f"case {req['id']}: float_preserving=false")
        gpu = case.get("project_gpu_accel_type", {})
        renderer = gpu.get("current_name") if isinstance(gpu, dict) else None
        renderer = renderer or case.get("project_gpu_accel_type.current_name")
        if renderer != "SOFTWARE": raise VerificationError(f"case {req['id']}: renderer is not SOFTWARE")
        if not case.get("render_set_id"): raise VerificationError(f"case {req['id']}: missing render_set_id/32bpc render association")
        comp = case.get("comp", {})
        if not isinstance(comp, dict) or not comp.get("width") or not comp.get("height"): raise VerificationError(f"case {req['id']}: missing dimensions")
        if not case.get("effects") or not any(isinstance(e, dict) and e.get("params") is not None for e in case["effects"]): raise VerificationError(f"case {req['id']}: missing effect params")
        if req.get("params_full") is None and req.get("params") is None: raise VerificationError(f"case {req['id']}: request params missing")
        path, stated = find_artifact(case, artifact_root)
        actual = sha256(path)
        expected = required_hash(case, stated)
        if actual != expected: raise VerificationError(f"case {req['id']}: artifact SHA-256 mismatch")
        if path.suffix.lower() != ".exr": raise VerificationError(f"case {req['id']}: only EXR is accepted for exact 32bpc verification")
        info_raw, header_end = parse_exr_header(path)
        info = decode_attrs(info_raw, path)
        names = [ch["name"] for ch in info["channels"]]
        if set(names) != EXPECTED_CHANNELS or len(names) != len(EXPECTED_CHANNELS):
            raise VerificationError(f"case {req['id']}: channels {names!r}, expected exactly RGBA")
        header_metadata = case.get("header_metadata")
        if not isinstance(header_metadata, dict):
            header_metadata = {}
        declared_order = case.get("channel_order") or header_metadata.get("channel_order")
        if isinstance(declared_order, list):
            if declared_order != names:
                raise VerificationError(
                    f"case {req['id']}: declared physical channel_order {declared_order!r} does not match EXR {names!r}"
                )
        elif isinstance(declared_order, str):
            # Some Windows runners record logical RGBA while OpenEXR stores
            # physical scanlines as A/B/G/R. The inspected EXR header remains
            # authoritative for physical order; require the complete semantic set.
            if set(declared_order) != EXPECTED_CHANNELS or len(declared_order) != len(EXPECTED_CHANNELS):
                raise VerificationError(
                    f"case {req['id']}: declared semantic channel_order {declared_order!r} is not RGBA"
                )
        else:
            raise VerificationError(f"case {req['id']}: missing channel_order declaration")
        if any(ch["sample_type"] != 2 for ch in info["channels"]): raise VerificationError(f"case {req['id']}: HALF/non-FLOAT channel rejected")
        if [comp["width"], comp["height"]] != [info["width"], info["height"]]: raise VerificationError(f"case {req['id']}: dimensions mismatch")
        for key in ("color_space", "alpha_mode"):
            if not (case.get(key) or header_metadata.get(key) or info["header"].get(key)):
                raise VerificationError(f"case {req['id']}: missing {key}")
        counts = decode_builtin_scanlines(path, header_end, info)
        results.append({"case_id": req["id"], "artifact": str(path), "sha256": actual, "decoder": decoder, "dimensions": [info["width"], info["height"]], "channels": names, "counts": counts})
    return {"status": "pass", "request_id": request_id, "cases": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?", help="Windows return manifest (omit with --mac-candidate-index).")
    parser.add_argument("--request", type=Path, help="Windows request JSON (required unless validating a Mac candidate index).")
    parser.add_argument("--artifact-root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mac-candidate-index", type=Path, help="Validate a Mac candidate index instead of a Windows return manifest.")
    parser.add_argument("--allow-unrendered", action="store_true", help="Validate package metadata/readiness without requiring rendered EXRs.")
    args = parser.parse_args()
    try:
        if args.mac_candidate_index:
            result = verify_mac_candidate_index(args.mac_candidate_index, require_rendered=not args.allow_unrendered)
        else:
            if args.manifest is None or args.request is None:
                parser.error("manifest and --request are required unless --mac-candidate-index is used")
            result = verify(args.manifest, args.request, args.artifact_root)
    except (OSError, ValueError, struct.error, VerificationError) as exc:
        if args.json: print(json.dumps({"status": "fail", "error": str(exc)}, indent=2))
        else: print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.mac_candidate_index:
        marker = "OK" if result["status"] == "pass" else "NOT READY"
        print(f"[{marker}] Mac candidate index: rendered={result['rendered']} pending={result['pending']}")
    else:
        print(f"[OK] {result['request_id']}: {len(result['cases'])} EXR case(s) verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
