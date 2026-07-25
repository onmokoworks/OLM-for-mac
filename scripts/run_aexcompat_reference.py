#!/usr/bin/env python3
"""Run Windows AEX reference cases through AEXCompat and compare pixels."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops

SUPPORTED_PARAMETER_TYPES = {1, 2, 3, 4, 5, 6, 7, 10}
REPORTED_PARAMETER_TYPES = SUPPORTED_PARAMETER_TYPES
PARAMETER_TYPE_NAMES = {
    1: "slider",
    2: "fixed_slider",
    3: "angle",
    4: "checkbox",
    5: "color",
    6: "point",
    7: "popup",
    10: "float_slider",
}
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True, help="Reference request ZIP or extracted directory.")
    parser.add_argument("--aex", type=Path, required=True, help="Windows x64 AEX to execute.")
    parser.add_argument("--worker", type=Path, required=True, help="AEXCompat aex-guest-worker executable.")
    parser.add_argument("--case", action="append", default=[], help="Case ID to run; repeat or omit for all cases.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--trace", action="store_true", help="Emit execution dossiers; intended for small probe images.")
    parser.add_argument(
        "--allow-large-trace",
        action="store_true",
        help="Permit tracing inputs larger than 128x128; dossier size can grow dramatically.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def require_argb8_manifest(manifest: dict[str, Any]) -> None:
    bits_per_channel = manifest.get("project", {}).get("bits_per_channel")
    if bits_per_channel not in (None, 8):
        raise ValueError(
            "AEXCompat reference runner currently accepts only 8bpc manifests; "
            f"got bits_per_channel={bits_per_channel!r}"
        )


def require_8bit_png(path: Path) -> None:
    header = path.read_bytes()[:25]
    if len(header) < 25 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"AEXCompat ARGB8 runner requires PNG input: {path}")
    if header[24] != 8:
        raise ValueError(
            f"AEXCompat ARGB8 runner requires an 8-bit PNG; "
            f"{path.name} has PNG bit depth {header[24]}"
        )


def format_parameter_value(value: float) -> str:
    return format(value, ".17g")


def format_parameter_assignment(
    name: str,
    slot: int | None,
    value: float | tuple[float, float] | tuple[int, int, int, int],
) -> str:
    if isinstance(value, tuple):
        encoded = ",".join(format_parameter_value(component) for component in value)
    else:
        encoded = format_parameter_value(value)
    selector = f"{name}@{slot}" if slot is not None else name
    return f"{selector}={encoded}"


def describe_parameter_type(param_type: int | None) -> str:
    if param_type is None:
        return "unknown"
    return PARAMETER_TYPE_NAMES.get(param_type, f"type_{param_type}")


def rgba_float_to_argb8(value: Any) -> tuple[int, int, int, int]:
    if not (
        isinstance(value, (list, tuple))
        and len(value) == 4
        and all(
            isinstance(component, (int, float)) and not isinstance(component, bool)
            for component in value
        )
    ):
        raise ValueError(f"color value must be four normalized RGBA components: {value!r}")
    rgba = []
    for component in value:
        if not 0.0 <= float(component) <= 1.0:
            raise ValueError(f"color component is outside 0..1: {component!r}")
        rgba.append(min(255, math.floor(float(component) * 255.0 + 0.5)))
    red, green, blue, alpha = rgba
    return alpha, red, green, blue


def find_manifest(root: Path) -> Path:
    candidates = sorted(root.rglob("reference_manifest.json"))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one reference_manifest.json under {root}, found {len(candidates)}")
    return candidates[0]


def resolve_case_image(root: Path, directory: str, filename: str) -> Path:
    nested = root / directory / filename
    if nested.is_file():
        return nested
    flat = root / filename
    if flat.is_file():
        return flat
    return nested


def resolve_manifest_file(root: Path, filename: str) -> Path:
    normalized = Path(filename.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError(f"unsafe manifest file path: {filename!r}")
    candidates = [
        root / normalized,
        root / filename,
        root / normalized.name,
        root / "input" / normalized.name,
        root / f"input\\{normalized.name}",
    ]
    root_resolved = root.resolve()
    matches = [
        path
        for path in candidates
        if path.is_file() and path.resolve().is_relative_to(root_resolved)
    ]
    unique = list(dict.fromkeys(path.resolve() for path in matches))
    if len(unique) == 1:
        return unique[0]
    if len(unique) > 1:
        hashes = {sha256(path) for path in unique}
        if len(hashes) == 1:
            return unique[0]
        raise ValueError(f"ambiguous manifest file {filename!r}: {unique}")
    return candidates[0]


def source_input_for_case(
    manifest_root: Path,
    manifest: dict[str, Any],
    case: dict[str, Any],
) -> tuple[Path, dict[str, Any]] | None:
    input_id = case.get("input_id")
    if not isinstance(input_id, str):
        return None
    matches = [
        row
        for row in manifest.get("source_inputs", [])
        if isinstance(row, dict) and row.get("id") == input_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{case.get('id')}: expected one source_inputs entry for {input_id!r}, "
            f"found {len(matches)}"
        )
    source = matches[0]
    filename = source.get("file")
    if not isinstance(filename, str):
        raise ValueError(f"{case.get('id')}: source input {input_id!r} has no file")
    path = resolve_manifest_file(manifest_root, filename)
    if not path.is_file():
        raise FileNotFoundError(f"{case.get('id')}: source input is missing: {path}")
    expected_hash = source.get("sha256")
    actual_hash = sha256(path)
    if isinstance(expected_hash, str) and actual_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"{case.get('id')}: source input SHA-256 mismatch: "
            f"expected {expected_hash.lower()}, got {actual_hash}"
        )
    return path, source


def write_ae_png_premultiplied(raw_path: Path, output_path: Path) -> None:
    with Image.open(raw_path) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint16)
    alpha = rgba[..., 3:4]
    rgb = (rgba[..., :3] * alpha + 127) // 255
    output = np.concatenate((rgb, alpha), axis=2).astype(np.uint8)
    Image.fromarray(output, mode="RGBA").save(output_path)


def require_source_matches_before_effects(source_path: Path, before_path: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".png") as handle:
        normalized = Path(handle.name)
        write_ae_png_premultiplied(source_path, normalized)
        comparison = pixel_diff(normalized, before_path)
    if not comparison.get("exact"):
        raise ValueError(
            "source input does not reproduce before_effects_frame through "
            "AE ARGB8 premultiply; refusing an unproven host-I/O normalization "
            f"(max_diff={comparison.get('max_diff')}, "
            f"nonzero_pixels={comparison.get('nonzero_pixels')})"
        )


def require_lossless_before_effects_input(path: Path) -> None:
    with Image.open(path) as image:
        alpha = image.convert("RGBA").getchannel("A")
        minimum, maximum = alpha.getextrema()
    if minimum != 255 or maximum != 255:
        raise ValueError(
            "manifest has no original source input and before_effects_frame "
            "contains non-opaque alpha; refusing an irreversible 8bpc host input"
        )


def setup_parameters(
    worker: Path, aex: Path, timeout: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    proc = subprocess.run(
        [str(worker), "setup", str(aex)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"AEX setup failed ({proc.returncode}): {proc.stderr.strip()}")
    report = json.loads(proc.stdout)
    parameters = [
        row
        for row in report.get("parameters", [])
        if isinstance(row.get("name"), str) and isinstance(row.get("slot"), int)
    ]
    return report, parameters


def case_parameters(
    case: dict[str, Any], accepted_parameters: set[str] | list[dict[str, Any]]
) -> list[
    tuple[
        str,
        int | None,
        float | tuple[float, float] | tuple[int, int, int, int],
    ]
]:
    effects = case.get("effects", [])
    if len(effects) != 1:
        raise ValueError(f"{case.get('id')}: expected one effect, found {len(effects)}")
    legacy_names = accepted_parameters if isinstance(accepted_parameters, set) else None
    all_surface_by_slot = (
        {}
        if legacy_names is not None
        else {
            row["slot"]: row
            for row in accepted_parameters
            if isinstance(row.get("slot"), int)
            and row.get("param_type") in REPORTED_PARAMETER_TYPES
        }
    )
    editable_surface_by_slot = (
        {}
        if legacy_names is not None
        else {
            slot: row
            for slot, row in all_surface_by_slot.items()
            if row.get("param_type") in SUPPORTED_PARAMETER_TYPES
        }
    )
    result: list[
        tuple[
            str,
            int | None,
            float | tuple[float, float] | tuple[int, int, int, int],
        ]
    ] = []
    for param in effects[0].get("params", []):
        name = param.get("name")
        slot: int | None = None
        if legacy_names is not None:
            if name not in legacy_names:
                continue
        else:
            path = param.get("path")
            if isinstance(path, list) and len(path) > 2:
                continue
            property_index = param.get("property_index")
            surface = all_surface_by_slot.get(property_index)
            if surface is None:
                continue
            param_type = surface.get("param_type")
            if param_type not in SUPPORTED_PARAMETER_TYPES:
                continue
            slot = property_index
            name = surface["name"]
        value = param.get("value")
        if isinstance(value, bool):
            value = int(value)
        if legacy_names is None and param_type == 5:
            result.append((name, slot, rgba_float_to_argb8(value)))
        elif isinstance(value, (list, tuple)) and len(value) == 2 and all(
            isinstance(component, (int, float)) and not isinstance(component, bool)
            for component in value
        ):
            result.append((name, slot, (float(value[0]), float(value[1]))))
        elif isinstance(value, (int, float)):
            result.append((name, slot, float(value)))
        else:
            raise ValueError(f"{case.get('id')}: unsupported value for {name}: {value!r}")
    missing = (
        legacy_names.difference(name for name, _, _ in result)
        if legacy_names is not None
        else set(editable_surface_by_slot).difference(slot for _, slot, _ in result)
    )
    if missing:
        missing_details = (
            sorted(missing)
            if legacy_names is not None
            else [
                f"{slot}:{editable_surface_by_slot[slot]['name']}:{describe_parameter_type(editable_surface_by_slot[slot].get('param_type'))}"
                for slot in sorted(missing)
            ]
        )
        raise ValueError(f"{case.get('id')}: manifest is missing AEX parameters: {missing_details}")
    return result


def pixel_diff(actual_path: Path, expected_path: Path) -> dict[str, Any]:
    with Image.open(actual_path) as actual_image, Image.open(expected_path) as expected_image:
        actual = actual_image.convert("RGBA")
        expected = expected_image.convert("RGBA")
        if actual.size != expected.size:
            return {
                "exact": False,
                "actual_size": list(actual.size),
                "expected_size": list(expected.size),
                "error": "size_mismatch",
            }
        difference = ImageChops.difference(actual, expected)
        extrema = difference.getextrema()
        max_diff = max(high for _, high in extrema)
        pixels = (
            difference.get_flattened_data()
            if hasattr(difference, "get_flattened_data")
            else difference.getdata()
        )
        nonzero_pixels = sum(1 for pixel in pixels if any(pixel))
        return {
            "exact": max_diff == 0,
            "actual_size": list(actual.size),
            "expected_size": list(expected.size),
            "max_diff": max_diff,
            "nonzero_pixels": nonzero_pixels,
            "total_pixels": actual.width * actual.height,
            "per_channel_max": [high for _, high in extrema],
        }


def run_case(
    *,
    worker: Path,
    aex: Path,
    manifest_root: Path,
    manifest: dict[str, Any],
    case: dict[str, Any],
    accepted_parameters: set[str] | list[dict[str, Any]],
    output_dir: Path,
    trace: bool,
    allow_large_trace: bool,
    timeout: int,
) -> dict[str, Any]:
    case_id = case["id"]
    before_path = resolve_case_image(
        manifest_root, "input", case["before_effects_frame"]
    )
    expected_path = resolve_case_image(manifest_root, "expected", case["frame"])
    if not before_path.is_file() or not expected_path.is_file():
        raise FileNotFoundError(f"{case_id}: missing input or expected image")
    source_input = source_input_for_case(manifest_root, manifest, case)
    if source_input is None:
        input_path = before_path
        require_lossless_before_effects_input(input_path)
        host_io_mode = "before_effects_raw"
    else:
        input_path, _ = source_input
        require_source_matches_before_effects(input_path, before_path)
        host_io_mode = "straight_source_ae_png_premultiply_round"
    require_8bit_png(input_path)
    require_8bit_png(before_path)
    require_8bit_png(expected_path)
    with Image.open(input_path) as image:
        dimensions = image.size
    if trace and not allow_large_trace and (dimensions[0] > 128 or dimensions[1] > 128):
        raise ValueError(
            f"{case_id}: refusing {dimensions[0]}x{dimensions[1]} trace; "
            "use a small probe or pass --allow-large-trace"
        )

    output_png = output_dir / f"{case_id}.png"
    raw_output_png = (
        output_dir / f"{case_id}.raw.png"
        if source_input is not None
        else output_png
    )
    report_json = output_dir / f"{case_id}.{'dossier' if trace else 'render'}.json"
    stderr_path = output_dir / f"{case_id}.stderr.txt"
    params = case_parameters(case, accepted_parameters)
    command = [
        str(worker),
        "render-trace-png" if trace else "render-png",
        str(aex),
        str(input_path),
        str(raw_output_png),
        *[
            format_parameter_assignment(name, slot, value)
            for name, slot, value in params
        ],
    ]
    with report_json.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        proc = subprocess.run(
            command,
            text=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
            timeout=timeout,
        )
    if proc.returncode != 0:
        error_text = stderr_path.read_text(encoding="utf-8").strip()
        raise RuntimeError(f"{case_id}: worker failed ({proc.returncode}): {error_text}")
    report = load_json(report_json)
    if report.get("render_error") != 0:
        raise RuntimeError(
            f"{case_id}: worker reported render_error={report.get('render_error')!r}"
        )
    if source_input is not None:
        write_ae_png_premultiplied(raw_output_png, output_png)
    comparison = pixel_diff(output_png, expected_path)
    truncation = [
        {"selector": trace_row.get("selector"), "truncation": trace_row.get("truncation")}
        for trace_row in report.get("execution_traces", [])
        if trace_row.get("truncation")
    ]
    return {
        "case_id": case_id,
        "parameters": {
            f"{name}@{slot}" if slot is not None else name: value
            for name, slot, value in params
        },
        "render_error": report.get("render_error"),
        "render_mode": report.get("render_mode"),
        "host_io_mode": host_io_mode,
        "normalization": {
            "applied": source_input is not None,
            "mode": (
                "ae_export_premultiply_u8_round"
                if source_input is not None
                else "none"
            ),
            "formula": (
                "(rgb * alpha + 127) // 255"
                if source_input is not None
                else None
            ),
            "boundary_proof": (
                "premultiplied source input equals before_effects_frame"
                if source_input is not None
                else None
            ),
        },
        "trace_truncation": truncation,
        "comparison": comparison,
        "artifacts": {
            "input_sha256": sha256(input_path),
            "before_effects_sha256": sha256(before_path),
            "reference_sha256": sha256(expected_path),
            "output_sha256": sha256(output_png),
            "raw_output_sha256": sha256(raw_output_png),
            "worker_report": report_json.name,
            "stderr": stderr_path.name,
            "output_png": output_png.name,
            "raw_output_png": raw_output_png.name,
        },
    }


def main() -> int:
    args = parse_args()
    worker = args.worker.resolve()
    aex = args.aex.resolve()
    request = args.request.resolve()
    for path, label in ((worker, "worker"), (aex, "AEX"), (request, "request")):
        if not path.exists():
            print(f"[FAIL] {label} not found: {path}", file=sys.stderr)
            return 1

    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else Path("/tmp") / f"olm_aexcompat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="olm_aexcompat_request_") as temporary:
        if request.is_file():
            if not zipfile.is_zipfile(request):
                print(f"[FAIL] request is not a ZIP: {request}", file=sys.stderr)
                return 1
            with zipfile.ZipFile(request) as archive:
                archive.extractall(temporary)
            request_root = Path(temporary)
        else:
            request_root = request

        try:
            manifest_path = find_manifest(request_root)
            manifest = load_json(manifest_path)
            require_argb8_manifest(manifest)
            setup_report, accepted_parameters = setup_parameters(
                worker, aex, args.timeout
            )
            selected = set(args.case)
            cases = [case for case in manifest.get("cases", []) if not selected or case.get("id") in selected]
            missing = selected.difference(case.get("id") for case in cases)
            if missing:
                raise ValueError(f"case IDs not found: {sorted(missing)}")
            if not cases:
                raise ValueError("manifest contains no selected cases")
            results: list[dict[str, Any]] = []
            for case in cases:
                try:
                    result = run_case(
                        worker=worker,
                        aex=aex,
                        manifest_root=manifest_path.parent,
                        manifest=manifest,
                        case=case,
                        accepted_parameters=accepted_parameters,
                        output_dir=output_dir,
                        trace=args.trace,
                        allow_large_trace=args.allow_large_trace,
                        timeout=args.timeout,
                    )
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
                    result = {
                        "case_id": case.get("id"),
                        "status": "error",
                        "error": str(error),
                        "comparison": {"exact": False},
                    }
                results.append(result)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            print(f"[FAIL] {error}", file=sys.stderr)
            print(f"[INFO] output_dir: {output_dir}")
            return 1

    summary = {
        "schema": 1,
        "kind": "olm_aexcompat_reference_run",
        "created_at": datetime.now().astimezone().isoformat(),
        "request_name": request.name,
        "aex_sha256": sha256(aex),
        "worker_sha256": sha256(worker),
        "setup": setup_report,
        "trace": args.trace,
        "counts": {
            "total": len(results),
            "pixel_exact": sum(row["comparison"].get("exact") is True for row in results),
            "render_success": sum(row.get("render_error") == 0 for row in results),
            "truncated": sum(bool(row.get("trace_truncation")) for row in results),
            "errors": sum(row.get("status") == "error" for row in results),
        },
        "cases": results,
    }
    summary_path = output_dir / "AEXCOMPAT_REFERENCE_RESULT.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row in results:
        comparison = row["comparison"]
        if row.get("status") == "error":
            print(f"[ERROR] {row['case_id']} {row['error']}")
            continue
        print(
            f"[{'EXACT' if comparison.get('exact') else 'DIFF'}] {row['case_id']} "
            f"max={comparison.get('max_diff', 'n/a')} "
            f"pixels={comparison.get('nonzero_pixels', 'n/a')}"
        )
    print(
        f"[SUMMARY] exact={summary['counts']['pixel_exact']}/{summary['counts']['total']} "
        f"render_success={summary['counts']['render_success']}/{summary['counts']['total']} "
        f"truncated={summary['counts']['truncated']}"
    )
    print(f"[INFO] result: {summary_path}")
    if summary["counts"]["errors"]:
        return 1
    return 0 if summary["counts"]["pixel_exact"] == summary["counts"]["total"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
