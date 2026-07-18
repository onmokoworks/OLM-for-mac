#!/usr/bin/env python3
"""Fail-closed B150 zero-inner contract for case_0009.

This test consumes the identity-pinned natural checkpoint at the start of
normalization.  It reconstructs the scalar B150 writeback from checkpoint
inputs, and reconstructs the normalized plane from the captured accumulation
and max-alpha planes.  It does not run the AEX or modify repository artifacts.
"""

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
DISASM = ROOT / "disasm/OLMRadialBlur.aex.asm.txt"
NORMALIZED_ORACLE = Path(
    "/private/tmp/olmradialblur_continuation_dump_20260718_corrected/"
    "normalized_polar_plane.f32rgba"
)
AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"

WIDTH = 1104
HEIGHT = 1800
CELLS = WIDTH * HEIGHT
RGBA_BYTES = CELLS * 16
SCALAR_BYTES = CELLS * 4
CHECKPOINT_SHA256 = "480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
SOURCE_SCALAR_SHA256 = "13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce"
NORMALIZED_SHA256 = "c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8"
SOURCE_SCALAR_COUNTS = {
    0x3F800000: 1_922_504,
    0x3F7FFFFF: 58_895,
    0x3F800001: 5_108,
    0x3F7FFFFE: 693,
}

MAGIC = b"AEXCP64\x00"
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


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
            if len(prefix) != PREFIX_SIZE or prefix[: len(MAGIC)] != MAGIC:
                raise ValueError("invalid checkpoint prefix")
            version, header_size = struct.unpack("<IQ", prefix[len(MAGIC):len(MAGIC) + 12])
            if version != 1 or header_size > 64 * 1024 * 1024:
                raise ValueError("unsupported checkpoint header")
            header_bytes = stream.read(header_size)
            if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
                raise ValueError("checkpoint header checksum mismatch")
            header = json.loads(header_bytes.decode("ascii"))
            regions: dict[str, bytes] = {}
            for region in header.get("regions", []):
                compressed = stream.read(int(region["compressed_size"]))
                raw = zlib.decompress(compressed)
                if len(raw) != int(region["size"]):
                    raise ValueError(f"checkpoint region size mismatch: {region['name']}")
                if sha256_bytes(raw) != region["sha256"]:
                    raise ValueError(f"checkpoint region checksum mismatch: {region['name']}")
                regions[region["name"]] = raw
            if stream.read(1):
                raise ValueError("checkpoint has trailing data")
        if header.get("format") != "aex-loader-x64-checkpoint":
            raise ValueError("checkpoint format mismatch")
        return cls(header, regions)

    def read_range(self, address: int, size: int) -> bytes:
        for region in self.header["regions"]:
            base = int(region["address"])
            if base <= address and address + size <= base + int(region["size"]):
                raw = self.regions[region["name"]]
                start = address - base
                return raw[start:start + size]
        raise ValueError(f"unreadable checkpoint range 0x{address:x}+{size}")


def qword(checkpoint: Checkpoint, address: int) -> int:
    return struct.unpack("<Q", checkpoint.read_range(address, 8))[0]


def f32(value: np.ndarray) -> np.ndarray:
    return np.asarray(value, dtype="<f4")


def scalar_b150_reconstruction(preblur: bytes, gate: bytes) -> bytes:
    """Model B150's zero-inner scalar path in source-cell order.

    B150 loads source alpha from +0x38[3], loads +0x48 as XMM5, rejects either
    zero, then stores the normalized accumulated alpha to its +0x50 output.
    With inner strength/offset zero and +0x48 == 1.0 everywhere, no inner
    taps alter that alpha, so the scalar result is the source alpha.
    """
    rgba = np.frombuffer(preblur, dtype="<f4").reshape(CELLS, 4)
    gate_values = np.frombuffer(gate, dtype="<f4")
    if not np.all(gate_values == np.float32(1.0)):
        raise ValueError("unsupported +0x48 gate plane: expected all 1.0f")
    alpha = f32(rgba[:, 3])
    result = np.where((alpha != np.float32(0.0)) & (gate_values != np.float32(0.0)), alpha, np.float32(0.0))
    return result.astype("<f4", copy=False).tobytes()


def normalized_from_accum_max(accum: bytes, maximum: bytes) -> bytes:
    accum_array = np.frombuffer(accum, dtype="<f4").reshape(CELLS, 4)
    max_array = np.frombuffer(maximum, dtype="<f4")
    result = np.zeros((CELLS, 4), dtype="<f4")
    valid = max_array != np.float32(0.0)
    for channel in range(3):
        np.divide(accum_array[:, channel], accum_array[:, 3], out=result[:, channel], where=valid)
    result[:, 3] = max_array
    return result.astype("<f4", copy=False).tobytes()


def fail(reason: str) -> int:
    print(json.dumps({"status": "blocked_fail_closed", "reason": reason}, sort_keys=True))
    return 2


def main() -> int:
    try:
        for path in (CHECKPOINT, DISASM, NORMALIZED_ORACLE, AEX):
            if not path.is_file():
                return fail(f"missing required artifact: {path}")
        if sha256_file(CHECKPOINT) != CHECKPOINT_SHA256:
            return fail("checkpoint SHA256 mismatch")
        if sha256_file(AEX) != AEX_SHA256:
            return fail("AEX SHA256 mismatch")
        if sha256_file(NORMALIZED_ORACLE) != NORMALIZED_SHA256:
            return fail("normalized oracle SHA256 mismatch")

        asm = DISASM.read_text(encoding="utf-8")
        anchors = {
            "b150_entry": "18000b150  PUSH RBX" in asm,
            "source_alpha_from_0x38": "18000b238  MOVSS XMM2,dword ptr [RDI + 0xc]" in asm,
            "gate_input_0x48": "18000b251  MOVSS XMM5,dword ptr [R8]" in asm,
            "gate_zero_branch": "18000b25a  UCOMISS XMM2,XMM6" in asm and "18000b26b  UCOMISS XMM5,XMM6" in asm and "18000b265  JZ 0x18000b57d" in asm,
            "scalar_divide": "18000b542  DIVSS XMM2,XMM3" in asm,
            "scalar_store_0x50_output": "18000b595  MOVSS dword ptr [R12],XMM2" in asm,
            "accum_rgba_store": "18000b555  MOVSS dword ptr [R9],XMM0" in asm,
            "max_plane_store": "18000b59e  MOVSS dword ptr [R13],XMM2" in asm,
        }
        if not all(anchors.values()):
            return fail(f"B150 asm anchor failure: {anchors}")

        checkpoint = Checkpoint.read(CHECKPOINT)
        if checkpoint.header.get("aex", {}).get("sha256") != AEX_SHA256:
            return fail("checkpoint embedded AEX identity mismatch")
        metadata = checkpoint.header.get("metadata", {})
        config = metadata.get("config", {})
        captured = metadata.get("captured", {})
        if config.get("case_id") != "case_0009":
            return fail("checkpoint case is not case_0009")
        if any(config.get(name) for name in ("direct_python_prefill", "direct_detour_prepass", "direct_detour_scatter", "direct_fast_forward_prefill")):
            return fail("checkpoint contains a synthetic or detoured path")
        params = metadata.get("param_ctx_dump", {})
        expected_params = {"inner_strength": 0, "inner_offset": 0, "outer_offset": 0}
        if any(params.get(key) != value for key, value in expected_params.items()):
            return fail(f"inner-zero parameter gate failed: {params}")
        if int(checkpoint.header["registers"]["gp"]["rip"]) != 0x180005C9F:
            return fail("checkpoint is not at pre-normalization RIP")
        work = int(captured.get("zoom_param1") or 0)
        if not work:
            return fail("checkpoint has no zoom work pointer")

        pointers = {
            "preblur_plus_0x38": qword(checkpoint, work + 0x38),
            "input_plus_0x40": qword(checkpoint, work + 0x40),
            "input_plus_0x48": qword(checkpoint, work + 0x48),
            "output_plus_0x50": qword(checkpoint, work + 0x50),
            "accum_plus_0x4210": qword(checkpoint, work + 0x4210),
            "max_plus_0x4218": qword(checkpoint, work + 0x4218),
        }
        preblur = checkpoint.read_range(pointers["preblur_plus_0x38"], RGBA_BYTES)
        gate = checkpoint.read_range(pointers["input_plus_0x48"], SCALAR_BYTES)
        observed_source_scalar = checkpoint.read_range(pointers["output_plus_0x50"], SCALAR_BYTES)
        accum = checkpoint.read_range(pointers["accum_plus_0x4210"], RGBA_BYTES)
        maximum = checkpoint.read_range(pointers["max_plus_0x4218"], SCALAR_BYTES)
        if len(preblur) != RGBA_BYTES or len(gate) != SCALAR_BYTES or len(observed_source_scalar) != SCALAR_BYTES:
            return fail("checkpoint plane size mismatch")

        generated_scalar = scalar_b150_reconstruction(preblur, gate)
        scalar_words = np.frombuffer(generated_scalar, dtype="<u4")
        scalar_counts = {int(word): int(count) for word, count in zip(*np.unique(scalar_words, return_counts=True))}
        if scalar_counts != SOURCE_SCALAR_COUNTS:
            return fail(f"generated +0x50 bit distribution mismatch: {scalar_counts}")
        if sha256_bytes(generated_scalar) != SOURCE_SCALAR_SHA256:
            return fail("generated +0x50 SHA256 mismatch")
        if generated_scalar != observed_source_scalar:
            return fail("generated +0x50 differs from checkpoint output plane")

        generated_normalized = normalized_from_accum_max(accum, maximum)
        if sha256_bytes(generated_normalized) != NORMALIZED_SHA256:
            return fail("accum/max scalar reconstruction SHA256 mismatch")
        if generated_normalized != NORMALIZED_ORACLE.read_bytes():
            return fail("accum/max reconstruction differs from normalized checkpoint oracle")

        facts = [
            "The identity-pinned natural checkpoint is case_0009 with inner_strength=0 and inner_offset=0.",
            "B150 reads source alpha from the +0x38 RGBA input and the gate/span input from +0x48.",
            "The captured +0x48 plane is exactly 1.0f in all 1,987,200 cells.",
            "B150 divides the accumulated alpha by its accumulated weight and stores it at +0x50.",
            "The captured accumulation and max-alpha planes normalize to the pinned internal polar oracle.",
        ]
        inferences = [
            "+0x48 is a unit gate/span input in this zero-inner case; it does not itself become +0x50.",
            "For this bounded input, +0x50 is the source alpha lane from +0x38 because no inner taps modify the alpha accumulation.",
            "The matching normalized plane supports the captured accum/max writeback model, not Windows or AE exactness.",
        ]
        print(json.dumps({
            "status": "pass",
            "classification": "bounded_case0009_b150_zero_inner_contract",
            "FACT": facts,
            "INFERENCE": inferences,
            "geometry": {"width": WIDTH, "height": HEIGHT, "float_words": CELLS},
            "sha256": {"generated_plus_0x50": sha256_bytes(generated_scalar), "expected_plus_0x50": SOURCE_SCALAR_SHA256, "normalized_from_accum_max": sha256_bytes(generated_normalized), "normalized_oracle": NORMALIZED_SHA256},
            "pointers": {name: hex(value) for name, value in pointers.items()},
            "asm_anchors": anchors,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        return fail(f"exception: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
