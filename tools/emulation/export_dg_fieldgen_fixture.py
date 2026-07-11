#!/usr/bin/env python3
"""Export a deterministic function-level fixture from the real DG AEX helper."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
import cv_bridge as cvb  # noqa: E402
import opencv_impls as ocv  # noqa: E402
from fixture_contract import verify_fixture  # noqa: E402
from test_dg_fieldgen_p1b import (  # noqa: E402
    FUN_CVRESIZE_OR_CONVERT,
    FUN_FIELDGEN,
    FUN_NORMALIZE,
    build_context,
    build_host_suites,
    make_mask,
    mask_from_rgba_png,
    setup_tls,
)

AEX = ROOT / "plugins_2025" / "DistanceGradation.aex"
DEFAULT_OUTPUT = HERE / "fixtures" / "distancegradation_fieldgen_synthetic_17x11"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def descriptor(name: str, data: bytes) -> dict[str, object]:
    return {"blob": name, "offset": 0, "size": len(data), "sha256": sha256_bytes(data)}


def callback_counts(loader: AexLoader) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label, _args, _ret in loader.callback_log:
        counts[label] = counts.get(label, 0) + 1
    return counts


def run_aex_fieldgen(mask: np.ndarray, threshold: int, param8: int) -> tuple[np.ndarray, dict[str, object]]:
    height, width = mask.shape
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    setup_tls(loader)
    ocv.register_opencv_impls(
        loader,
        "DistanceGradation",
        ops=["threshold", "dist_transform", "resize_same_shape", "normalize_minmax"],
    )

    hits: list[str] = []

    def record(label: str):
        def hook(_loader: AexLoader, _address: int, _size: int) -> None:
            hits.append(label)
        return hook

    loader.add_code_hook(FUN_CVRESIZE_OR_CONVERT, record("FUN_1812aef70"))
    loader.add_code_hook(FUN_NORMALIZE, record("FUN_18117ca50"))
    spbasic = build_host_suites(loader)
    ctx = build_context(loader, spbasic)
    src_ipl = cvb.build_ipl(loader, mask, align_step=4)
    dst_ipl = cvb.build_ipl(loader, np.full((height, width), -777.0, np.float32), align_step=16)
    regs = loader.call_function(
        FUN_FIELDGEN,
        int_args=[ctx, src_ipl, dst_ipl, threshold, 0, width, height, param8],
        max_instructions=5_000_000,
    )
    field = np.ascontiguousarray(cvb.read_ipl(loader, dst_ipl), dtype="<f4")
    trace = {
        "instructions": int(regs["instructions"]),
        "hits": hits,
        "callback_counts": callback_counts(loader),
    }
    return field, trace


def export_fixture(
    output: Path,
    *,
    replace: bool,
    mask: np.ndarray | None = None,
    threshold: int = 3,
    param8: int = 1,
    case_id: str = "distancegradation.fieldgen.synthetic_17x11.threshold3.param8_1",
    source: dict[str, object] | None = None,
) -> Path:
    if output.exists():
        if not replace:
            raise FileExistsError(f"fixture exists: {output}; pass --replace")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    if mask is None:
        mask = make_mask(17, 11)
    mask = np.ascontiguousarray(mask, dtype=np.uint8)
    field, trace = run_aex_fieldgen(mask, threshold, param8)
    height, width = mask.shape

    mask_bytes = mask.tobytes(order="C")
    field_bytes = field.tobytes(order="C")
    # This is an explicit harness call block, not an AE-built PF_ParamDef block.
    params_bytes = struct.pack(
        "<8i",
        threshold,
        0,
        width,
        height,
        param8,
        0,
        width,
        height,
    )
    blobs = {
        "input_mask_u8.bin": mask_bytes,
        "field_f32.bin": field_bytes,
        "call_params_le_i32.bin": params_bytes,
    }
    for name, data in blobs.items():
        (output / name).write_bytes(data)

    manifest = {
        "schema": "olm.aex.cpu-fixture/1",
        "case_id": case_id,
        "scope": "function",
        "provenance": {
            "oracle": "unicorn-aex",
            "binary_sha256": sha256_file(AEX),
            "binary_path": "plugins_2025/DistanceGradation.aex",
            "function": hex(FUN_FIELDGEN),
            "parameter_block_origin": "harness-constructed",
        },
        "world": {
            "name": "source_mask",
            "format": "SCALAR",
            "sample_type": "uint8",
            "byte_order": "little",
            "width": width,
            "height": height,
            "rowbytes": width,
            "bpc": 8,
            "descriptor": descriptor("input_mask_u8.bin", mask_bytes),
        },
        "raw_param_block": {
            "format": "raw",
            "layout": [
                "threshold:i32", "reserved:i32", "width:i32", "height:i32",
                "param8:i32", "invert:i32", "source_width:i32", "source_height:i32",
            ],
            "descriptor": descriptor("call_params_le_i32.bin", params_bytes),
        },
        "intermediates": [],
        "output": {
            "name": "normalized_distance_field",
            "format": "SCALAR",
            "sample_type": "float32",
            "byte_order": "little",
            "width": width,
            "height": height,
            "rowbytes": width * 4,
            "bpc": 32,
            "descriptor": descriptor("field_f32.bin", field_bytes),
        },
        "execution": trace,
        "input_source": source or {"kind": "synthetic-cross-mask"},
        "claim": "Actual AEX function output for this harness-constructed small input; not an AE-host fixture.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verify_fixture(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--mask-png", type=Path)
    parser.add_argument("--mask-channel", choices=("alpha", "red", "green", "blue", "luma"), default="alpha")
    parser.add_argument("--invert-mask", action="store_true")
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--param8", type=int, default=1)
    parser.add_argument("--case-id", default="distancegradation.fieldgen.synthetic_17x11.threshold3.param8_1")
    args = parser.parse_args()
    mask = None
    source = None
    if args.mask_png:
        mask_path = args.mask_png.resolve()
        mask, metadata = mask_from_rgba_png(mask_path, channel=args.mask_channel, crop=None)
        if args.invert_mask:
            mask = np.where(mask != 0, 0, 255).astype(np.uint8)
        try:
            display_path = mask_path.relative_to(ROOT).as_posix()
        except ValueError:
            display_path = str(mask_path)
        metadata["source_png"] = display_path
        source = {
            "kind": "reference-image-mask",
            "path": display_path,
            "sha256": sha256_file(mask_path),
            "channel": args.mask_channel,
            "inverted": args.invert_mask,
            "metadata": metadata,
        }
    elif args.invert_mask:
        mask = np.where(make_mask(17, 11) != 0, 0, 255).astype(np.uint8)
    fixture = export_fixture(
        args.output.resolve(),
        replace=args.replace,
        mask=mask,
        threshold=args.threshold,
        param8=args.param8,
        case_id=args.case_id,
        source=source,
    )
    print(f"[OK] exported and verified DG AEX fieldgen fixture: {fixture}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
