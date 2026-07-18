#!/usr/bin/env python3
"""Bounded, disjoint RadialBlur post-worker plane evidence."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = Path(
    "/private/tmp/olmradialblur_a9d0_boundary_nway_20260718/"
    "nway_merged_at_normalization_20260718.aexcp"
)
AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
ORACLE = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/normalized_polar_plane.f32rgba")
OUT_JSON = ROOT / "refs/conformance/olmradialblur_postworker_planes_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_postworker_planes_20260718.md"

MAGIC = b"AEXCP64\x00"
VERSION = 1
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
EXPECTED_CHECKPOINT_SHA256 = "480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909"
EXPECTED_RIP = 0x180005C9F
WIDTH = 1104
HEIGHT = 1800
CELLS = WIDTH * HEIGHT
RGBA_BYTES = CELLS * 16
SCALAR_BYTES = CELLS * 4
MASK_BYTES = CELLS


def artifact_label(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Checkpoint:
    def __init__(self, header: dict[str, Any], regions: dict[str, bytes]):
        self.header = header
        self.regions = regions

    @classmethod
    def read(cls, path: Path) -> "Checkpoint":
        with path.open("rb") as stream:
            prefix = stream.read(PREFIX_SIZE)
            if len(prefix) != PREFIX_SIZE or prefix[:len(MAGIC)] != MAGIC:
                raise RuntimeError("invalid checkpoint prefix")
            version, header_size = struct.unpack("<IQ", prefix[len(MAGIC):len(MAGIC) + 12])
            if version != VERSION or header_size > 64 * 1024 * 1024:
                raise RuntimeError("unsupported checkpoint header")
            header_bytes = stream.read(header_size)
            if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
                raise RuntimeError("checkpoint header checksum mismatch")
            header = json.loads(header_bytes.decode("ascii"))
            regions: dict[str, bytes] = {}
            for region in header.get("regions", []):
                blob = stream.read(int(region["compressed_size"]))
                raw = zlib.decompress(blob)
                if len(raw) != int(region["size"]):
                    raise RuntimeError(f"checkpoint region size mismatch: {region['name']}")
                if sha256_bytes(raw) != region["sha256"]:
                    raise RuntimeError(f"checkpoint region checksum mismatch: {region['name']}")
                regions[region["name"]] = raw
            if stream.read(1):
                raise RuntimeError("checkpoint has trailing bytes")
        if header.get("format") != "aex-loader-x64-checkpoint":
            raise RuntimeError("checkpoint format mismatch")
        if header.get("aex", {}).get("sha256") != EXPECTED_AEX_SHA256:
            raise RuntimeError("checkpoint AEX identity mismatch")
        return cls(header, regions)

    def read_range(self, address: int, size: int) -> bytes:
        for region in self.header["regions"]:
            base = int(region["address"])
            end = base + int(region["size"])
            if base <= address and address + size <= end:
                raw = self.regions[region["name"]]
                return raw[address - base:address - base + size]
        raise RuntimeError(f"unreadable checkpoint range 0x{address:x}+{size}")


def qword(checkpoint: Checkpoint, address: int) -> int:
    return struct.unpack("<Q", checkpoint.read_range(address, 8))[0]


def value_classes(raw: bytes, scalar: bool = False, mask: bool = False) -> dict[str, int]:
    if mask:
        return {
            "zero": raw.count(0),
            "one": raw.count(1),
            "other": sum(value not in (0, 1) for value in raw),
            "byte_count": len(raw),
        }
    values = np.frombuffer(raw, dtype="<f4")
    result = {
        "zero": int(np.count_nonzero((values == 0.0) & ~np.signbit(values))),
        "negative_zero": int(np.count_nonzero((values == 0.0) & np.signbit(values))),
        "finite_nonzero": int(np.count_nonzero(np.isfinite(values) & (values != 0.0))),
        "positive_inf": int(np.count_nonzero(np.isposinf(values))),
        "negative_inf": int(np.count_nonzero(np.isneginf(values))),
        "nan": int(np.count_nonzero(np.isnan(values))),
    }
    if scalar:
        result["word_count"] = int(values.size)
    return result


def reconstruct(accum_raw: bytes, max_raw: bytes) -> bytes:
    accum = np.frombuffer(accum_raw, dtype="<f4").reshape(CELLS, 4)
    maximum = np.frombuffer(max_raw, dtype="<f4")
    result = np.zeros((CELLS, 4), dtype="<f4")
    gate = maximum != np.float32(0.0)
    # Separate ufuncs preserve the three DIVSS-like float32 operations and
    # their caller order; no packed or widened division is used here.
    for channel in range(3):
        np.divide(accum[:, channel], accum[:, 3], out=result[:, channel], where=gate)
    result[:, 3] = maximum
    return result.astype("<f4", copy=False).tobytes()


def first_difference(left: bytes, right: bytes) -> dict[str, Any] | None:
    index = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), None)
    if index is None:
        return None
    word = index // 4
    cell, channel = divmod(word, 4)
    return {
        "byte_offset": index,
        "cell_index": cell,
        "angle_index": cell // WIDTH,
        "radius_index": cell % WIDTH,
        "channel": "RGBA"[channel],
        "left_bits": f"0x{struct.unpack_from('<I', left, word * 4)[0]:08x}",
        "right_bits": f"0x{struct.unpack_from('<I', right, word * 4)[0]:08x}",
    }


def fail(reason: str) -> int:
    report = {
        "kind": "olmradialblur_postworker_planes_20260718",
        "schema": 1,
        "status": "blocked_fail_closed",
        "reason": reason,
        "claim_boundary": "bounded internal plane evidence only; no AE-exact claim",
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(f"# OLMRadialBlur post-worker planes (2026-07-18)\n\n- Status: `blocked_fail_closed`\n- Reason: {reason}\n", encoding="utf-8")
    return 2


def main() -> int:
    try:
        for path in (CHECKPOINT, AEX, INPUT, ORACLE):
            if not path.is_file():
                return fail(f"required identity/artifact is missing: {artifact_label(path)}")
        checkpoint_sha256 = sha256_file(CHECKPOINT)
        if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
            return fail(f"checkpoint SHA256 mismatch: {checkpoint_sha256}")
        aex_sha256 = sha256_file(AEX)
        if aex_sha256 != EXPECTED_AEX_SHA256:
            return fail(f"AEX SHA256 mismatch: {aex_sha256}")
        input_sha256 = sha256_file(INPUT)
        if input_sha256 != EXPECTED_INPUT_SHA256:
            return fail(f"input SHA256 mismatch: {input_sha256}")
        checkpoint = Checkpoint.read(CHECKPOINT)
        gp = checkpoint.header["registers"]["gp"]
        rip = int(gp["rip"])
        if rip != EXPECTED_RIP:
            return fail(f"checkpoint RIP is not normalization start: 0x{rip:x}")
        captured = checkpoint.header.get("metadata", {}).get("captured", {})
        work = int(captured.get("zoom_param1") or 0)
        if not work:
            return fail("metadata captured.zoom_param1 is absent")
        pointers = {
            "output_rgba_plus_0x38": qword(checkpoint, work + 0x38),
            "source_scalar_plus_0x40": qword(checkpoint, work + 0x40),
            "b150_scalar_gate_plus_0x48": qword(checkpoint, work + 0x48),
            "source_scalar_plus_0x50": qword(checkpoint, work + 0x50),
            "accumulation_rgba_plus_0x4210": qword(checkpoint, work + 0x4210),
            "max_alpha_plus_0x4218": qword(checkpoint, work + 0x4218),
        }
        mask_slot = int(gp["rbp"]) - 0x60
        pointers["eligibility_mask_rbp_minus_0x60"] = qword(checkpoint, mask_slot)
        ranges = {
            "output_rgba_plus_0x38": (pointers["output_rgba_plus_0x38"], RGBA_BYTES),
            "source_scalar_plus_0x40": (pointers["source_scalar_plus_0x40"], SCALAR_BYTES),
            "b150_scalar_gate_plus_0x48": (pointers["b150_scalar_gate_plus_0x48"], SCALAR_BYTES),
            "source_scalar_plus_0x50": (pointers["source_scalar_plus_0x50"], SCALAR_BYTES),
            "accumulation_rgba_plus_0x4210": (pointers["accumulation_rgba_plus_0x4210"], RGBA_BYTES),
            "max_alpha_plus_0x4218": (pointers["max_alpha_plus_0x4218"], SCALAR_BYTES),
            "eligibility_mask_rbp_minus_0x60": (pointers["eligibility_mask_rbp_minus_0x60"], MASK_BYTES),
        }
        intervals = sorted((start, start + size, name) for name, (start, size) in ranges.items())
        if any(start >= end for start, end, _ in intervals) or any(
            left_end > right_start for (_, left_end, _), (right_start, _, _) in zip(intervals, intervals[1:])
        ):
            return fail("requested plane ranges are not disjoint")
        raw = {name: checkpoint.read_range(address, size) for name, (address, size) in ranges.items()}
        expected_sizes = {name: size for name, (_, size) in ranges.items()}
        if any(len(raw[name]) != size for name, size in expected_sizes.items()):
            return fail("one or more extracted plane sizes are not exact")
        reconstructed = reconstruct(raw["accumulation_rgba_plus_0x4210"], raw["max_alpha_plus_0x4218"])
        oracle = ORACLE.read_bytes()
        if len(oracle) != RGBA_BYTES:
            return fail(f"normalized oracle size mismatch: {len(oracle)}")
        if len(reconstructed) != RGBA_BYTES:
            return fail("reconstructed normalized plane size mismatch")
        normalized_match = reconstructed == oracle
        mask_values = raw["eligibility_mask_rbp_minus_0x60"]
        report = {
            "kind": "olmradialblur_postworker_planes_20260718",
            "schema": 1,
            "status": "pass_bounded_internal_evidence",
            "claim_boundary": "bounded internal plane evidence only; no AE-exact claim",
            "FACT": [
                "Checkpoint, AEX, and case input identities matched pinned SHA256 values.",
                "Checkpoint RIP is exactly 0x180005c9f, the start of FUN_1800056f0 normalization.",
                "zoom_param1 was loaded from checkpoint metadata as the work/state pointer.",
                "All requested planes were extracted at exact geometry sizes from readable checkpoint ranges.",
                "The extracted +0x38 RGBA plane is pre-normalization at this checkpoint.",
            ],
            "INFERENCE": [
                "The established continuation normalized_polar_plane.f32rgba is the appropriate comparison oracle because the checkpoint stops before normalization.",
                "Exact reconstructed/oracle equality supports the caller normalization model for this bounded state; it does not establish AE equivalence.",
            ],
            "identities": {
                "checkpoint": {"path": artifact_label(CHECKPOINT), "sha256": checkpoint_sha256},
                "aex": {"path": artifact_label(AEX), "sha256": aex_sha256},
                "input": {"path": artifact_label(INPUT), "sha256": input_sha256},
                "normalized_oracle": {"path": artifact_label(ORACLE), "sha256": sha256_bytes(oracle)},
            },
            "checkpoint": {"rip": hex(rip), "rbp": hex(int(gp["rbp"])), "work_zoom_param1": hex(work), "mask_slot": hex(mask_slot)},
            "geometry": {"width": WIDTH, "height": HEIGHT, "cells": CELLS},
            "planes": {
                name: {
                    "pointer": hex(address),
                    "bytes": size,
                    "sha256": sha256_bytes(raw[name]),
                    "value_classes": value_classes(
                        raw[name], size != MASK_BYTES, name == "eligibility_mask_rbp_minus_0x60"
                    ),
                }
                for name, (address, size) in ranges.items()
            },
            "disjoint_exact_readability": True,
            "normalization": {
                "formula": "RGB=accum.rgb/accum.a when max_alpha != 0 else 0; A=max_alpha",
                "operation": "float32 per-channel division in caller order",
                "reconstructed_sha256": sha256_bytes(reconstructed),
                "oracle_sha256": sha256_bytes(oracle),
                "reconstructed_equals_oracle": normalized_match,
                "raw_output_plus_0x38_equals_oracle": raw["output_rgba_plus_0x38"] == oracle,
                "raw_output_plus_0x38_classification": "pre_normalization_at_checkpoint",
                "first_reconstruction_difference": first_difference(reconstructed, oracle),
            },
            "mask_value_counts": {str(value): mask_values.count(value) for value in sorted(set(mask_values))},
        }
        OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md = [
            "# OLMRadialBlur post-worker planes (2026-07-18)", "",
            "- Status: `pass_bounded_internal_evidence`", "- No AE-exact claim is made.", "",
            "## FACT", "", *[f"- {item}" for item in report["FACT"]], "",
            "## INFERENCE", "", *[f"- {item}" for item in report["INFERENCE"]], "",
            f"- Geometry: `{WIDTH}x{HEIGHT}` (`{CELLS}` cells).", f"- Work: `{hex(work)}`; RIP: `{hex(rip)}`.",
            f"- Reconstructed normalization equals established oracle: `{normalized_match}`.", "",
            "## Plane Evidence", "",
        ]
        md.extend(f"- `{name}`: pointer `{hex(address)}`, bytes `{size}`, SHA256 `{report['planes'][name]['sha256']}`." for name, (address, size) in ranges.items())
        OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"PASS bounded post-worker plane evidence: {OUT_JSON}")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, struct.error) as error:
        return fail(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
