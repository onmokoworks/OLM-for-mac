#!/usr/bin/env python3
"""Bind RadialBlur semantic trace points to same-run and pinned PNG bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import zlib
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TARGETS = ((7, 0), (8, 0), (24, 0))
POISON_RE = re.compile(
    r"(?:^|[,;:])(?:UNREAD|SENTINEL|MISSING|UNKNOWN|NONE|NULL|N/?A|"
    r"DEADBEEF|BAADF00D|CCCCCCCC|CDCDCDCD|FEEEFEEE|FFFFFFFF|7FC00000)(?:$|[,;:])",
    re.IGNORECASE,
)
HEX_WORD_RE = re.compile(r"^[0-9a-fA-F]{8}$")
POINTER_RE = re.compile(r"^(?:0x)?[0-9a-fA-F]+(?:`[0-9a-fA-F]+)?$")
BYTE_RGBA_RE = re.compile(r"^(?:[0-9]{1,3},){3}[0-9]{1,3}$")


def has_hex_words(value: str, count: int) -> bool:
    words = value.split(",")
    return len(words) == count and all(HEX_WORD_RE.fullmatch(word) for word in words)


def pointer_value(value: str) -> int | None:
    if POINTER_RE.fullmatch(value) is None:
        return None
    return int(value.removeprefix("0x").removeprefix("0X").replace("`", ""), 16)


def validate_typed_point(fields: dict[str, Any], index: int) -> list[str]:
    issues: list[str] = []
    if fields.get("run_identity") != "same-run":
        issues.append(f"point[{index}]:run_identity=same-run")
    for name in ("inverse_coords", "radius_index", "angle_index"):
        if name == "inverse_coords":
            valid = has_hex_words(str(fields.get(name, "")), 2)
        else:
            valid = bool(HEX_WORD_RE.fullmatch(str(fields.get(name, ""))))
        if not valid:
            issues.append(f"point[{index}]:{name}=typed_float32_words")

    slots = ("cell00", "cell10", "cell01", "cell11")
    addresses: list[int] = []
    for slot in slots:
        ident = pointer_value(str(fields.get(f"{slot}_id", "")))
        address = pointer_value(str(fields.get(f"{slot}_addr", "")))
        if ident is None or address is None or ident == 0 or address == 0:
            issues.append(f"point[{index}]:{slot}=live_cell_id_and_address")
        elif ident != address:
            issues.append(f"point[{index}]:{slot}_id_matches_address")
        addresses.append(address or 0)
        if not has_hex_words(str(fields.get(f"{slot}_accum_rgba", "")), 4):
            issues.append(f"point[{index}]:{slot}_accum_rgba=float32_rgba")
        if not HEX_WORD_RE.fullmatch(str(fields.get(f"{slot}_denom", ""))):
            issues.append(f"point[{index}]:{slot}_denom=float32")
        if not HEX_WORD_RE.fullmatch(str(fields.get(f"{slot}_valid", ""))):
            issues.append(f"point[{index}]:{slot}_valid=float32")
        if not has_hex_words(str(fields.get(f"{slot}_final_rgba", "")), 4):
            issues.append(f"point[{index}]:{slot}_final_rgba=float32_rgba")
    if len(set(addresses)) != len(addresses) or 0 in addresses:
        issues.append(f"point[{index}]:cell_addresses=distinct_nonzero")
    if not has_hex_words(str(fields.get("bilinear_weights", "")), 4):
        issues.append(f"point[{index}]:bilinear_weights=float32[4]")
    for name in ("final_rgba",):
        if not has_hex_words(str(fields.get(name, "")), 4):
            issues.append(f"point[{index}]:{name}=float32_rgba")
    for name in ("final_alpha_sum", "pre_byte_alpha"):
        if not HEX_WORD_RE.fullmatch(str(fields.get(name, ""))):
            issues.append(f"point[{index}]:{name}=float32")
    return issues


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def fail(contract: dict[str, Any], stage: str, reason: str, missing: list[str], last: str = "") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "exact_bind_failure",
        "request_id": contract["request_id"],
        "failure": {
            "stage": stage,
            "reason": reason,
            "missing_fields": sorted(set(missing)),
            "last_observation": last,
        },
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_rgba8_png(path: Path, width: int, height: int) -> bytes:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("PNG signature is missing")
    offset = len(PNG_SIGNATURE)
    chunks: list[bytes] = []
    saw_ihdr = False
    saw_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk payload")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected_crc:
            raise ValueError(f"bad {kind.decode('ascii', 'replace')} CRC")
        if kind == b"IHDR":
            if saw_ihdr or offset != len(PNG_SIGNATURE) or length != 13:
                raise ValueError("invalid IHDR")
            actual = struct.unpack(">IIBBBBB", payload)
            if actual != (width, height, 8, 6, 0, 0, 0):
                raise ValueError(
                    f"wrong PNG class {actual}; expected {width}x{height} RGBA8 non-interlaced"
                )
            saw_ihdr = True
        elif kind == b"IDAT":
            if not saw_ihdr or saw_iend:
                raise ValueError("IDAT is out of order")
            chunks.append(payload)
        elif kind == b"IEND":
            if length != 0:
                raise ValueError("invalid IEND")
            saw_iend = True
            offset = end
            break
        offset = end
    if not saw_ihdr or not chunks or not saw_iend or offset != len(data):
        raise ValueError("incomplete PNG structure")

    packed = zlib.decompress(b"".join(chunks))
    stride = width * 4
    if len(packed) != height * (stride + 1):
        raise ValueError("wrong decompressed PNG size")
    pixels = bytearray(height * stride)
    source = 0
    for y in range(height):
        filter_type = packed[source]
        source += 1
        row = bytearray(packed[source : source + stride])
        source += stride
        previous = pixels[(y - 1) * stride : y * stride] if y else bytes(stride)
        if filter_type not in range(5):
            raise ValueError(f"unsupported PNG filter {filter_type}")
        for index in range(stride):
            left = row[index - 4] if index >= 4 else 0
            up = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 0xFF
            elif filter_type == 2:
                row[index] = (row[index] + up) & 0xFF
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) >> 1)) & 0xFF
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                predictor = left if distances[0] <= distances[1] and distances[0] <= distances[2] else up if distances[1] <= distances[2] else upper_left
                row[index] = (row[index] + predictor) & 0xFF
        pixels[y * stride : (y + 1) * stride] = row
    return bytes(pixels)


def rgba_at(pixels: bytes, width: int, xy: tuple[int, int]) -> list[int]:
    offset = (xy[1] * width + xy[0]) * 4
    return list(pixels[offset : offset + 4])


def normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(str(path))))


def read_key_value_log(path: Path, marker: str) -> dict[str, str] | None:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line == marker or line.startswith(marker + "\n"):
            continue
        if line.startswith(marker):
            return dict(
                item.split("=", 1)
                for item in line[len(marker):].strip().splitlines()
                if "=" in item
            )
    return None


def parse_binding_log(path: Path, marker: str) -> dict[str, str] | None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if line == marker:
            values: dict[str, str] = {}
            for candidate in lines[index + 1 :]:
                if "=" not in candidate:
                    break
                key, value = candidate.split("=", 1)
                values[key] = value
            return values
    return None


def enrich(contract: dict[str, Any], status: dict[str, Any], work: Path) -> dict[str, Any]:
    if status.get("status") != "answered":
        return status
    case = contract["cases"][0]
    values = case["template_values"]
    width = int(values["width"])
    height = int(values["height"])
    case_id = case["id"]
    observed_path = work / case["exports"][0]["source"].replace("{case_id}", case_id)
    reference_path = Path(__file__).resolve().parents[1] / values["reference_png_path"]
    result_path = work / f"ae_result_{case_id}.json"
    log_path = work / f"ae_{case_id}.log"
    queue_bootstrap_path = work / "queue_bootstrap.log"
    queue_log_path = work / "queue.log"
    required = [observed_path, reference_path, result_path, log_path, queue_bootstrap_path, queue_log_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        return fail(contract, "radial_artifact_binding", "required render or reference artifact is missing", missing)

    result = read_json(result_path)
    expected_output = normalized_path(observed_path)
    actual_output = normalized_path(Path(str(result.get("output_png", ""))))
    log = log_path.read_text(encoding="utf-8", errors="replace")
    result_issues: list[str] = []
    if result.get("status") != "ok":
        result_issues.append("ae_result.status=ok")
    if result.get("case_id") != case_id:
        result_issues.append(f"ae_result.case_id={case_id}")
    if result.get("project_bits_per_channel") != 8:
        result_issues.append("ae_result.project_bits_per_channel=8")
    if actual_output != expected_output:
        result_issues.append("ae_result.output_png=exact_same_run_export")
    if "gpuAccelType=SOFTWARE" not in log:
        result_issues.append("ae_log.gpuAccelType=SOFTWARE")
    queue_binding = parse_binding_log(queue_bootstrap_path, "WITNESS_QUEUE_BOOTSTRAP")
    queue_log = queue_log_path.read_text(encoding="utf-8", errors="replace")
    run_id = str(status["run"]["run_id"])
    queue_path = Path(__file__).resolve().parents[1] / contract["queue"]
    queue_sha256 = sha256(queue_path) if queue_path.is_file() else ""
    if not queue_binding:
        result_issues.append("queue_bootstrap=published_binding")
    else:
        for name, expected in (("run_id", run_id), ("work", str(work)), ("root", str(queue_path.parents[1]))):
            actual = queue_binding.get(name, "")
            matches = (
                actual.lower() == expected.lower()
                if name == "run_id"
                else normalized_path(Path(actual)) == normalized_path(Path(expected))
            )
            if not matches:
                result_issues.append(f"queue_bootstrap.{name}=contract_bound")
        if queue_binding.get("queue_sha256", "").lower() != queue_sha256.lower():
            result_issues.append("queue_bootstrap.queue_sha256=packaged_queue")
    if f"WITNESS_QUEUE_START run_id={run_id}" not in queue_log or f"WITNESS_QUEUE_END run_id={run_id}" not in queue_log:
        result_issues.append("queue.log.run_id=trace_run_id")
    if result_issues:
        return fail(contract, "radial_render_identity", "AE result is not the canonical same-run render", result_issues, json.dumps(result, sort_keys=True))

    reference_hash = sha256(reference_path)
    if reference_hash != values["reference_png_sha256"]:
        return fail(contract, "radial_reference_identity", "pinned reference PNG hash mismatch", ["reference_png_sha256"], reference_hash)
    try:
        observed_pixels = decode_rgba8_png(observed_path, width, height)
        reference_pixels = decode_rgba8_png(reference_path, width, height)
    except (OSError, ValueError, zlib.error) as exc:
        return fail(contract, "radial_png_validation", str(exc), [values["render_class"]])

    point_events = [row for row in status.get("events", []) if row.get("prefix") == "RB9_POINT_TYPED"]
    by_xy: dict[tuple[int, int], dict[str, Any]] = {}
    semantic_issues: list[str] = []
    for index, row in enumerate(point_events):
        fields = row.get("fields", {})
        try:
            xy = (int(fields.get("x", "")), int(fields.get("y", "")))
        except ValueError:
            semantic_issues.append(f"point[{index}]:xy")
            continue
        if xy in by_xy:
            semantic_issues.append(f"point[{index}]:duplicate_xy={xy[0]},{xy[1]}")
        by_xy[xy] = row
        semantic_issues.extend(validate_typed_point(fields, index))
        for field, value in fields.items():
            text = str(value)
            if not text or POISON_RE.search(text):
                semantic_issues.append(f"point[{index}]:{field}=sentinel")
    if set(by_xy) != set(TARGETS):
        semantic_issues.append("points=7,0;8,0;24,0 exactly")
    if semantic_issues:
        return fail(contract, "radial_semantic_binding", "semantic point set contains missing, duplicate, or sentinel data", semantic_issues)

    observed_hash = sha256(observed_path)
    run = status["run"]
    witnesses: list[dict[str, Any]] = []
    for xy in TARGETS:
        observed = rgba_at(observed_pixels, width, xy)
        reference = rgba_at(reference_pixels, width, xy)
        fields = by_xy[xy]["fields"]
        fields.update({
            "observed_rgba8": ",".join(map(str, observed)),
            "reference_rgba8": ",".join(map(str, reference)),
            "observed_png_sha256": observed_hash,
            "reference_png_sha256": reference_hash,
            "render_class": values["render_class"],
            "image_run_id": run["run_id"],
            "image_case_id": case_id,
            "export_rgba8": ",".join(map(str, observed)),
        })
        witnesses.append({
            "run_id": run["run_id"],
            "ae_pid": run["ae_pid"],
            "module_base": run["module_base"],
            "aex_sha256": run["aex_sha256"],
            "project_bits_per_channel": run["project_bits_per_channel"],
            "renderer": run["renderer"],
            "case_id": case_id,
            "xy": list(xy),
            "observed_rgba8": observed,
            "reference_rgba8": reference,
            "observed_png_sha256": observed_hash,
            "reference_png_sha256": reference_hash,
            "width": width,
            "height": height,
            "render_class": values["render_class"],
        })
    status["pixel_witnesses"] = witnesses
    status["image_bindings"] = {
        "run_id": run["run_id"],
        "case_id": case_id,
        "observed": {"sha256": observed_hash, "width": width, "height": height, "render_class": values["render_class"]},
        "reference": {"sha256": reference_hash, "width": width, "height": height, "render_class": values["render_class"]},
    }
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    contract = read_json(args.contract)
    status = enrich(contract, read_json(args.status), args.work.resolve())
    write_json(args.status, status)
    print(json.dumps({"status": status["status"]}, sort_keys=True))
    return 0 if status["status"] == "answered" else 2


if __name__ == "__main__":
    raise SystemExit(main())
