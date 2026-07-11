"""
test_dg_fieldgen_p1b.py -- first direct-call probe for DistanceGradation
`FUN_181174760` with validated OpenCV P0/P1B detours.

This is intentionally a scaffold, not a conformance claim. The goal is to call
the real binary field-generation function far enough to identify the next
missing detour/mock precisely, without reimplementing the plugin path.
"""

from __future__ import annotations

import json
import argparse
import importlib.util
import struct
import sys
import traceback
from pathlib import Path

import numpy as np
from unicorn.x86_const import UC_X86_REG_RIP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader, TEB_BASE  # noqa: E402
import cv_bridge as cvb  # noqa: E402
import opencv_impls as ocv  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX = REPO_ROOT / "plugins_2025" / "DistanceGradation.aex"
FUN_FIELDGEN = 0x181174760
FUN_CVRESIZE_OR_CONVERT = 0x1812aef70
FUN_NORMALIZE = 0x18117ca50
DEFAULT_POINTS = "8,5;7,5;9,5"


def _u64(loader: AexLoader, addr: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(addr, 8))[0]


def build_host_suites(loader: AexLoader) -> int:
    """Minimal SPBasic + PF Handle Suite mock used by FUN_181395230."""

    def h_new(ld: AexLoader, args):
        size = args[0] & 0xFFFFFFFFFFFFFFFF
        data = ld.bump_alloc(max(size, 1), align=64)
        ld.write_bytes(data, b"\x00" * max(size, 1))
        handle = ld.host_alloc(8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        return handle

    def h_lock(ld: AexLoader, args):
        return _u64(ld, args[0]) if args[0] else 0

    def h_noop(ld: AexLoader, args):
        return 0

    handle_suite = loader.host_alloc(0x20)
    loader.write_bytes(
        handle_suite,
        struct.pack(
            "<4Q",
            loader.install_callback("PFHandle.new", h_new),
            loader.install_callback("PFHandle.lock", h_lock),
            loader.install_callback("PFHandle.unlock", h_noop),
            loader.install_callback("PFHandle.dispose", h_noop),
        ),
    )

    def sp_acquire(ld: AexLoader, args):
        out_ptr = args[2]
        ld.write_bytes(out_ptr, struct.pack("<Q", handle_suite))
        return 0

    spbasic = loader.host_alloc(0x10)
    loader.write_bytes(
        spbasic,
        struct.pack(
            "<2Q",
            loader.install_callback("SPBasic.AcquireSuite", sp_acquire),
            loader.install_callback("SPBasic.ReleaseSuite", h_noop),
        ),
    )
    return spbasic


def build_context(loader: AexLoader, spbasic: int) -> int:
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\x00" * 0x200)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", spbasic))
    return ctx


def setup_tls(loader: AexLoader, n_slots: int = 256, block_size: int = 0x4000) -> int:
    """Provide the OpenCV TLS array read via TEB.ThreadLocalStoragePointer."""
    block = loader.host_alloc(block_size, align=16)
    loader.write_bytes(block, b"\x00" * block_size)
    arr = loader.host_alloc(n_slots * 8, align=16)
    for i in range(n_slots):
        loader.write_bytes(arr + i * 8, struct.pack("<Q", block))
    loader.write_bytes(TEB_BASE + 0x58, struct.pack("<Q", arr))
    return arr


def make_mask(width: int, height: int) -> np.ndarray:
    src = np.ones((height, width), dtype=np.uint8) * 255
    src[height // 2, width // 2] = 0
    src[height // 2, max(0, width // 2 - 2): min(width, width // 2 + 3)] = 0
    return src


def parse_xy_list(spec: str) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        x_text, y_text = chunk.split(",", 1)
        points.append((int(x_text), int(y_text)))
    return points


def parse_crop(spec: str | None) -> tuple[int, int, int, int] | None:
    if not spec:
        return None
    parts = [int(v.strip()) for v in spec.split(",")]
    if len(parts) != 4:
        raise ValueError("--crop must be x,y,w,h")
    x, y, w, h = parts
    if w <= 0 or h <= 0:
        raise ValueError("--crop width/height must be positive")
    return x, y, w, h


def load_verify_manifest():
    path = REPO_ROOT / "refs" / "scripts" / "verify_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_manifest_for_dg_fieldgen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mask_from_rgba_png(path: Path, *, channel: str, crop: tuple[int, int, int, int] | None) -> tuple[np.ndarray, dict[str, object]]:
    verify = load_verify_manifest()
    rgba = verify.load_rgba(path)
    if rgba.ndim != 3 or rgba.shape[2] < 4:
        raise ValueError(f"expected RGBA image: {path}")

    origin_x = origin_y = 0
    if crop:
        origin_x, origin_y, w, h = crop
        rgba = rgba[origin_y : origin_y + h, origin_x : origin_x + w]
        if rgba.shape[0] != h or rgba.shape[1] != w:
            raise ValueError(f"crop {crop} falls outside {path} shape {rgba.shape}")

    if channel == "alpha":
        src = rgba[..., 3]
    elif channel == "red":
        src = rgba[..., 0]
    elif channel == "green":
        src = rgba[..., 1]
    elif channel == "blue":
        src = rgba[..., 2]
    elif channel == "luma":
        rgb = rgba[..., :3].astype(np.float64)
        src = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    else:
        raise ValueError(f"unsupported channel {channel!r}")

    mask = np.where(src.astype(np.float64) > 0.0, 255, 0).astype(np.uint8)
    meta = {
        "source_png": str(path),
        "source_shape": list(rgba.shape),
        "source_dtype": str(rgba.dtype),
        "mask_channel": channel,
        "crop_xywh": list(crop) if crop else None,
        "crop_origin_xy": [origin_x, origin_y],
        "mask_nonzero": int(np.count_nonzero(mask)),
        "mask_zero": int(mask.size - np.count_nonzero(mask)),
    }
    return mask, meta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mask-png", type=Path, help="Load a uint8 0/255 mask from this RGBA PNG.")
    parser.add_argument(
        "--mask-channel",
        default="alpha",
        choices=["alpha", "red", "green", "blue", "luma"],
        help="RGBA channel used to derive the binary mask when --mask-png is set.",
    )
    parser.add_argument("--crop", help="Optional x,y,w,h crop applied before mask derivation.")
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--param8", type=int, default=1)
    parser.add_argument("--invert-mask", action="store_true", help="Invert the derived uint8 mask before calling FUN_181174760.")
    parser.add_argument("--points", default=DEFAULT_POINTS, help="Semicolon-separated local or global x,y points.")
    parser.add_argument(
        "--points-global",
        action="store_true",
        help="Treat --points as full-frame coordinates and subtract the crop origin in samples.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    crop = parse_crop(args.crop)
    if args.mask_png:
        mask, input_meta = mask_from_rgba_png(args.mask_png, channel=args.mask_channel, crop=crop)
    else:
        mask = make_mask(17, 11)
        input_meta = {
            "source_png": None,
            "source_shape": [11, 17],
            "source_dtype": "synthetic",
            "mask_channel": "synthetic",
            "crop_xywh": None,
            "crop_origin_xy": [0, 0],
            "mask_nonzero": int(np.count_nonzero(mask)),
            "mask_zero": int(mask.size - np.count_nonzero(mask)),
        }
    if args.invert_mask:
        mask = np.where(mask != 0, 0, 255).astype(np.uint8)
        input_meta["invert_mask"] = True
        input_meta["mask_nonzero"] = int(np.count_nonzero(mask))
        input_meta["mask_zero"] = int(mask.size - np.count_nonzero(mask))
    else:
        input_meta["invert_mask"] = False
    height, width = mask.shape
    origin_x, origin_y = input_meta["crop_origin_xy"]
    sample_points = parse_xy_list(args.points)

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
        def _hook(ld: AexLoader, address: int, size: int):
            hits.append(label)
        return _hook

    loader.add_code_hook(FUN_CVRESIZE_OR_CONVERT, record("FUN_1812aef70"))
    loader.add_code_hook(FUN_NORMALIZE, record("FUN_18117ca50"))

    spbasic = build_host_suites(loader)
    ctx = build_context(loader, spbasic)
    src_ipl = cvb.build_ipl(loader, mask, align_step=4)
    dst_ipl = cvb.build_ipl(loader, np.full((height, width), -777.0, np.float32), align_step=16)

    result: dict[str, object] = {
        "aex": str(AEX),
        "function": hex(FUN_FIELDGEN),
        "shape": [height, width],
        "threshold": args.threshold,
        "param8": args.param8,
        "input": input_meta,
    }
    try:
        regs = loader.call_function(
            FUN_FIELDGEN,
            int_args=[ctx, src_ipl, dst_ipl, args.threshold, 0, width, height, args.param8],
            max_instructions=5_000_000,
        )
        out = cvb.read_ipl(loader, dst_ipl)
        samples = []
        for px, py in sample_points:
            lx, ly = (px - origin_x, py - origin_y) if args.points_global else (px, py)
            row: dict[str, object] = {
                "requested_xy": [px, py],
                "local_xy": [lx, ly],
            }
            if 0 <= lx < width and 0 <= ly < height:
                row.update(
                    mask=int(mask[ly, lx]),
                    output=float(out[ly, lx]),
                )
            else:
                row["out_of_bounds"] = True
            samples.append(row)
        result.update(
            status="completed",
            instructions=regs["instructions"],
            hits=hits,
            callback_counts=_callback_counts(loader),
            output_min=float(np.min(out)),
            output_max=float(np.max(out)),
            output_mean=float(np.mean(out)),
            samples=samples,
        )
    except Exception as exc:
        rip = loader.uc.reg_read(UC_X86_REG_RIP)
        result.update(
            status="blocked",
            blocker=str(exc),
            rip=hex(rip),
            hits=hits,
            callback_counts=_callback_counts(loader),
            traceback=traceback.format_exc(limit=4),
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "completed" else 2


def _callback_counts(loader: AexLoader) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label, _args, _ret in loader.callback_log:
        counts[label] = counts.get(label, 0) + 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
