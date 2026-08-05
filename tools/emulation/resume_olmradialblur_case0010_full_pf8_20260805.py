#!/usr/bin/env python3
"""Resume the pinned post-worker checkpoint and retain the complete native PF8 frame."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import time
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import test_m4_case0010 as m4  # noqa: E402
from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_RIP  # noqa: E402

CHECKPOINT = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805/post_worker_pre_pf8_current_callbacks.aexcp"
EXPECTED_CHECKPOINT_SHA256 = "6ee451f0ba56425886e095c56b76cfd65861e574f08832c854cd5a70055b8d39"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805/post_worker_full_pf8_argb.bin.zlib"
REPORT = ROOT / "refs/conformance/olmradialblur_case0010_full_pf8_actual_aex_20260805.json"
REPORT_MD = REPORT.with_suffix(".md")
LEGACY_PNG = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0010.png"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if sha256_file(CHECKPOINT) != EXPECTED_CHECKPOINT_SHA256:
        raise RuntimeError("migrated checkpoint SHA256 mismatch")
    params = m4.load_case0010_params()
    image = Image.open(m4.INPUT_PNG).convert("RGBA")
    width, height = image.size
    red, green, blue, alpha = image.split()
    input_bytes = Image.merge("RGBA", (alpha, red, green, blue)).tobytes()
    loader = AexLoader(str(m4.AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = m4.build_host_suites(loader)
    render_ctx = m4.build_render_context(loader, spbasic)
    input_world = m4.build_world(loader, width, height, input_bytes)
    output_world = m4.build_world(loader, width, height, bytes(width * height * 4))
    param_ctx = m4.build_param_block(loader)
    m4.install_reader_detours(loader, params)
    header = loader.load_checkpoint(CHECKPOINT)
    metadata = header.get("metadata", {})
    checks = {
        "checkpoint_kind": metadata.get("kind") == "case0010_rotation_post_worker_pre_pf8",
        "case_id": metadata.get("case_id") == "case_0010",
        "rip": loader.uc.reg_read(UC_X86_REG_RIP) == m4.FUN_180007B4A,
        "input_sha256": metadata.get("input_sha256") == sha256_file(m4.INPUT_PNG),
        "manifest_sha256": metadata.get("manifest_sha256") == sha256_file(m4.MANIFEST),
        "render_ctx": metadata.get("render_ctx") == f"0x{render_ctx:x}",
        "input_world": metadata.get("input_world") == f"0x{input_world:x}",
        "output_world": metadata.get("output_world") == f"0x{output_world:x}",
        "param_ctx": metadata.get("param_ctx") == f"0x{param_ctx:x}",
        "rotation_worker_returned": metadata.get("rotation_worker_returned") is True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"checkpoint metadata validation failed: {checks}")

    start = time.time()
    segments = []
    while loader.uc.reg_read(UC_X86_REG_RIP) != RETURN_TRAMPOLINE:
        if len(segments) >= 4:
            raise RuntimeError("PF8 owner did not return within continuation budget")
        segments.append(loader.resume_execution(max_instructions=500_000_000))
    elapsed = time.time() - start
    output_data = m4.u64(loader, output_world + 0x18)
    output_rowbytes = m4.u32(loader, output_world + 0x20)
    if output_rowbytes != width * 4:
        raise RuntimeError("unexpected output rowbytes")
    argb = loader.read_bytes(output_data, output_rowbytes * height)
    encoded = zlib.compress(argb, level=9)
    FIXTURE.write_bytes(encoded)

    argb_array = np.frombuffer(argb, dtype=np.uint8).reshape(height, width, 4)
    rgba = argb_array[:, :, [1, 2, 3, 0]]
    legacy = np.asarray(Image.open(LEGACY_PNG).convert("RGBA"), dtype=np.uint8)
    delta = rgba.astype(np.int16) - legacy.astype(np.int16)
    differing_channels = np.count_nonzero(delta, axis=(0, 1))
    differing_pixels = int(np.count_nonzero(np.any(delta != 0, axis=2)))
    first = np.argwhere(np.any(delta != 0, axis=2))
    comparison = {
        "legacy_png_sha256": sha256_file(LEGACY_PNG),
        "legacy_decoded_rgba_sha256": sha256_bytes(legacy.tobytes()),
        "native_rgba_sha256": sha256_bytes(rgba.tobytes()),
        "different_pixels": differing_pixels,
        "different_channels_rgba": [int(value) for value in differing_channels],
        "max_absolute_difference": int(np.max(np.abs(delta))),
        "first_difference_xy": [int(first[0, 1]), int(first[0, 0])] if first.size else None,
    }
    report = {
        "schema": "olmradialblur.case0010-full-pf8-actual-aex/1",
        "status": "exact" if all(checks.values()) else "failed",
        "scope": "actual Windows AEX CPU owner resumed post-worker through complete PF8 world under Mac Unicorn",
        "identity": {
            "aex_sha256": sha256_file(m4.AEX_PATH),
            "input_sha256": sha256_file(m4.INPUT_PNG),
            "manifest_sha256": sha256_file(m4.MANIFEST),
            "checkpoint_sha256": sha256_file(CHECKPOINT),
        },
        "checks": checks,
        "resume": {
            "elapsed_seconds": elapsed,
            "instruction_segments": [segment["instructions"] for segment in segments],
            "final_rip": f"0x{loader.uc.reg_read(UC_X86_REG_RIP):x}",
        },
        "frame": {
            "width": width,
            "height": height,
            "rowbytes": output_rowbytes,
            "format": "PF8 ARGB",
            "raw_bytes": len(argb),
            "raw_sha256": sha256_bytes(argb),
            "zlib_path": str(FIXTURE.relative_to(ROOT)),
            "zlib_bytes": len(encoded),
            "zlib_sha256": sha256_bytes(encoded),
            "witness_argb": {
                "1612,6": [int(value) for value in argb_array[6, 1612]],
                "1614,6": [int(value) for value in argb_array[6, 1614]],
            },
        },
        "legacy_png_comparison": comparison,
        "boundary": "PF8 world is authoritative for the AEX CPU owner; AE host/export behavior remains separate.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# OLMRadialBlur case0010 complete PF8 actual-AEX frame — 2026-08-05\n\n"
        f"Status: `{report['status']}`. Native PF8 ARGB SHA-256: `{report['frame']['raw_sha256']}`.\n\n"
        f"The post-worker checkpoint resumed for `{elapsed:.3f}` seconds and returned normally after "
        f"`{sum(segment['instructions'] for segment in segments)}` instructions.\n\n"
        f"Legacy PNG comparison: `{differing_pixels}` differing pixels, maximum absolute channel difference "
        f"`{comparison['max_absolute_difference']}`.\n\n"
        "Boundary: complete actual-AEX CPU PF8 world only; no AE host/export claim.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
