#!/usr/bin/env python3
"""Fail-closed continuation probe for the proven RadialBlur A9D0 checkpoint.

This is a Mac-only Unicorn probe.  It resumes an existing natural AEX
checkpoint and records internal PF32 planes at four sequential boundaries.  It
does not launch AE, reconstruct a caller, use synthetic image data, or claim
Windows/AE exactness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402
from test_m4_case0010 import (  # noqa: E402
    build_host_suites,
    build_param_block,
    build_render_context,
    build_world,
    install_reader_detours,
)
from test_zoom_case0009 import load_case_params  # noqa: E402


DEFAULT_CHECKPOINT = Path(
    "/tmp/olmradialblur_a9d0_boundary_fork_20260718/"
    "full_merged_at_normalization_20260718.aexcp"
)
DEFAULT_AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
DEFAULT_MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
DEFAULT_INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
DEFAULT_JSON = Path("/tmp/olmradialblur_continuation_20260718.json")
DEFAULT_MD = Path("/tmp/olmradialblur_continuation_20260718.md")

STOPS = (
    ("normalized_polar_plane", 0x180005D96),
    ("complete_pf32_frame", 0x180005E8E),
    ("pre_return", 0x1800063A1),
)
EXPECTED_HARNESS = "test_zoom_case0009"
EXPECTED_HARNESS_VERSION = 1
FORBIDDEN_CONFIG = (
    "direct_zoom_core", "direct_fast_forward_prefill", "direct_python_prefill",
    "direct_detour_prepass", "direct_detour_scatter",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable(value: Any) -> Any:
    """Remove workstation-specific paths from reports while preserving evidence."""
    if isinstance(value, dict):
        return {key: portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item) for item in value]
    if isinstance(value, str):
        value = value.replace(str(ROOT), "<repo>")
        value = value.replace("/private/tmp/", "<temporary>/")
        value = value.replace("/tmp/", "<temporary>/")
        return value
    return value


def parse_pixel(value: str) -> tuple[int, int]:
    try:
        x, y = (int(part.strip()) for part in value.split(",", 1))
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("pixel must be X,Y") from exc
    if x < 0 or y < 0:
        raise argparse.ArgumentTypeError("pixel coordinates must be non-negative")
    return x, y


def checkpoint_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--aex-path", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--input-png", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--pixel", action="append", type=parse_pixel,
                        default=[(0, 0), (6, 0), (7, 0), (8, 0), (24, 0)])
    parser.add_argument("--max-instructions", type=int, default=2_000_000_000)
    parser.add_argument("--dump-dir", type=Path)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    checkpoint_args(parser)
    return parser.parse_args()


def checkpoint_metadata_gate(header: dict[str, Any], checkpoint: Path,
                             aex: Path, manifest: Path, input_png: Path,
                             case_id: str) -> dict[str, Any]:
    metadata = header.get("metadata", {})
    config = metadata.get("config", {})
    if metadata.get("harness") != EXPECTED_HARNESS:
        raise ValueError("checkpoint harness identity mismatch")
    if metadata.get("harness_checkpoint_version") != EXPECTED_HARNESS_VERSION:
        raise ValueError("unsupported checkpoint harness version")
    if config.get("case_id") != case_id:
        raise ValueError("checkpoint case identity mismatch")
    if any(config.get(name) for name in FORBIDDEN_CONFIG):
        raise ValueError("checkpoint contains synthetic or detoured execution")
    for key, path in (("input_sha256", input_png), ("manifest_sha256", manifest)):
        if config.get(key) != sha256_file(path):
            raise ValueError(f"checkpoint {key} mismatch")
    aex_meta = header.get("aex", {})
    actual_aex = sha256_file(aex)
    if aex_meta.get("sha256") != actual_aex:
        raise ValueError("checkpoint AEX hash mismatch")
    captured = metadata.get("captured", {})
    work = int(captured.get("zoom_param1") or 0)
    param = int(captured.get("zoom_param2") or 0)
    if not work or not param:
        raise ValueError("checkpoint has no live work/param pointers")
    return {
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "aex_sha256": actual_aex,
        "case_id": case_id,
        "work": work,
        "param_2": param,
        "source_config": config,
    }


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def u32(loader: AexLoader, address: int) -> int:
    return struct.unpack("<I", loader.read_bytes(address, 4))[0]


def geometry(loader: AexLoader, param_2: int) -> dict[str, int]:
    ptr = u64(loader, param_2 + 0x08)
    width = u32(loader, ptr + 0x24)
    height = u32(loader, ptr + 0x28)
    if not (0 < width <= 30000 and 0 < height <= 30000):
        raise ValueError(f"invalid checkpoint geometry: {width}x{height}")
    return {"pointer": ptr, "width": width, "height": height,
            "cells": width * height}


def polar_geometry(loader: AexLoader, work: int) -> dict[str, int]:
    min_radius = struct.unpack("<i", loader.read_bytes(work + 0x18, 4))[0]
    max_radius = struct.unpack("<i", loader.read_bytes(work + 0x1C, 4))[0]
    width = max_radius - min_radius + 1
    output_rgba = u64(loader, work + 0x4210)
    output_scalar = u64(loader, work + 0x4218)
    normalized_rgba = u64(loader, work + 0x38)
    rgba_bytes = output_scalar - output_rgba
    scalar_bytes = normalized_rgba - output_scalar
    if width <= 0 or rgba_bytes <= 0 or scalar_bytes <= 0:
        raise ValueError("invalid polar geometry pointers")
    if rgba_bytes % 16 or scalar_bytes % 4 or rgba_bytes // 16 != scalar_bytes // 4:
        raise ValueError("polar RGBA/scalar plane sizes disagree")
    cells = rgba_bytes // 16
    if cells % width:
        raise ValueError("polar cell count is not divisible by radius width")
    return {"width": width, "height": cells // width, "cells": cells,
            "min_radius": min_radius, "max_radius": max_radius}


def plane_snapshot(loader: AexLoader, address: int, cells: int,
                   pixels: list[tuple[int, int]], width: int,
                   dump_path: Path | None = None) -> dict[str, Any]:
    size = cells * 16
    raw = bytes(loader.read_bytes(address, size))
    selected = {}
    for x, y in pixels:
        if x >= width or y >= cells // width:
            selected[f"{x},{y}"] = {"out_of_bounds": True}
            continue
        offset = (y * width + x) * 16
        selected[f"{x},{y}"] = {
            "float32": list(struct.unpack_from("<4f", raw, offset)),
            "hex": raw[offset:offset + 16].hex(),
        }
    report = {"address": hex(address), "size": size,
              "sha256": sha256_bytes(raw), "selected_pixels": selected}
    if dump_path is not None:
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_path.write_bytes(raw)
        report["dump_path"] = str(dump_path)
        report["dump_sha256"] = sha256_file(dump_path)
    return report


def capture_planes(loader: AexLoader, work: int, param_2: int,
                   geo: dict[str, int], polar_geo: dict[str, int], pixels: list[tuple[int, int]],
                   stage_name: str, dump_dir: Path | None) -> dict[str, Any]:
    normalized = u64(loader, work + 0x38)
    output = u64(loader, param_2 + 0xA0)
    return {
        "normalized_polar_plane": plane_snapshot(
            loader, normalized, polar_geo["cells"], pixels, polar_geo["width"],
            dump_dir / "normalized_polar_plane.f32rgba" if dump_dir is not None and stage_name == "normalized_polar_plane" else None),
        "pf32_output_frame": plane_snapshot(
            loader, output, geo["cells"], pixels, geo["width"],
            dump_dir / "complete_pf32_frame.f32rgba" if dump_dir is not None and stage_name == "complete_pf32_frame" else None),
    }


def build_loader(aex: Path, manifest: Path, input_png: Path,
                 case_id: str) -> tuple[AexLoader, dict[str, Any]]:
    params = load_case_params(manifest, case_id)
    image = Image.open(input_png).convert("RGBA")
    width, height = image.size
    r, g, b, alpha = image.split()
    input_bytes = Image.merge("RGBA", (alpha, r, g, b)).tobytes()
    loader = AexLoader(str(aex), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = build_host_suites(loader)
    render_ctx = build_render_context(loader, spbasic)
    input_world = build_world(loader, width, height, input_bytes)
    output_world = build_world(loader, width, height, bytes(width * height * 4))
    param_ctx = build_param_block(loader)
    install_reader_detours(loader, params)
    return loader, {
        "render_ctx": render_ctx, "input_world": input_world,
        "output_world": output_world, "param_ctx": param_ctx,
        "width": width, "height": height,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    checkpoint_before = sha256_file(args.checkpoint)
    loader, pointers = build_loader(args.aex_path, args.manifest, args.input_png, args.case_id)
    header = loader.load_checkpoint(args.checkpoint)
    identity = checkpoint_metadata_gate(
        header, args.checkpoint, args.aex_path, args.manifest, args.input_png, args.case_id,
    )
    expected_pointers = {
        key: pointers[key] for key in ("render_ctx", "input_world", "output_world", "param_ctx")
    }
    captured = header["metadata"]["captured"]
    if header["metadata"].get("pointers") != expected_pointers:
        raise ValueError("checkpoint host pointer layout mismatch")
    geo = geometry(loader, identity["param_2"])
    polar_geo = polar_geometry(loader, identity["work"])
    if (geo["width"], geo["height"]) != (pointers["width"], pointers["height"]):
        raise ValueError("checkpoint geometry differs from pinned input")

    report: dict[str, Any] = {
        "kind": "olmradialblur_continuation_20260718",
        "status": "rejected_fail_closed",
        "claims_not_made": ["AE exact", "Windows exact", "PNG equivalence"],
        "facts": [
            "The continuation resumes a natural AEX checkpoint under Unicorn.",
            "The reported planes are internal PF32 memory, not host-rendered output.",
        ],
        "inferences": [
            "A matching internal plane is evidence about the AEX path, not proof of Mac AE equivalence.",
        ],
        "identity": identity,
        "geometry": geo,
        "polar_geometry": polar_geo,
        "sequential_stops": [],
    }

    def stop_once(stage_name: str, target: int) -> dict[str, Any]:
        state = {"hit": False, "rip": None}

        def hook(ld: AexLoader, address: int, _size: int) -> None:
            if state["hit"]:
                return
            state["hit"] = True
            state["rip"] = hex(address)
            ld.uc.emu_stop()

        loader.add_code_hook(target, hook)
        result = loader.resume_execution(args.max_instructions)
        if not state["hit"] or result["rip"] != target:
            raise RuntimeError(f"did not reach sequential stop 0x{target:x}: {result}")
        return {"rip": hex(target), "instructions": result["instructions"],
                "planes": capture_planes(loader, identity["work"], identity["param_2"], geo, polar_geo, args.pixel, stage_name, args.dump_dir)}

    for name, target in STOPS:
        stage = stop_once(name, target)
        stage["name"] = name
        report["sequential_stops"].append(stage)
    final = loader.resume_execution(args.max_instructions)
    if final["rip"] != RETURN_TRAMPOLINE:
        raise RuntimeError(f"AEX did not return normally: {final}")
    report["return"] = {"rip": hex(final["rip"]), "instructions": final["instructions"],
                        "return_trampoline": hex(RETURN_TRAMPOLINE)}
    report["gates"] = {
        "aex_hash_validated": True,
        "checkpoint_metadata_validated": True,
        "geometry_validated": True,
        "three_sequential_stops_reached": len(report["sequential_stops"]) == 3,
        "normal_return": True,
        "checkpoint_unchanged": sha256_file(args.checkpoint) == checkpoint_before,
    }
    if not all(report["gates"].values()):
        raise ValueError("one or more continuation gates failed")
    report["status"] = "pass_internal_continuation_only"
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur continuation probe (2026-07-18)", "",
        f"- Status: `{report['status']}`",
        "- Scope: natural AEX Unicorn continuation and internal PF32 plane capture.",
        "- No AE-exact or Windows-exact claim is made.", "",
        "## Gates", "",
    ]
    for key, value in report.get("gates", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Sequential stops", ""])
    for stage in report.get("sequential_stops", []):
        lines.append(f"- `{stage['name']}` at `{stage['rip']}`; "
                     f"instructions `{stage['instructions']}`")
        for plane_name, plane in stage["planes"].items():
            lines.append(f"  - `{plane_name}`: `{plane['size']}` bytes, `{plane['sha256']}`")
    if report.get("return"):
        lines.extend(["", f"- Normal return: `{report['return']['rip']}`"])
    lines.extend(["", "## Fact / inference", ""])
    lines.extend(f"- FACT: {item}" for item in report.get("facts", []))
    lines.extend(f"- INFERENCE: {item}" for item in report.get("inferences", []))
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        report = run(args)
    except Exception as exc:
        report = {
            "kind": "olmradialblur_continuation_20260718",
            "status": "blocked_fail_closed",
            "error": f"{type(exc).__name__}: {exc}",
            "claims_not_made": ["AE exact", "Windows exact", "PNG equivalence"],
        }
        exit_code = 2
    else:
        exit_code = 0
    report = portable(report)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"status={report['status']}")
    if "error" in report:
        print(f"error={report['error']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
