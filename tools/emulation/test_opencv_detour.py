"""
test_opencv_detour.py — validator for the OpenCV detour layer.

P0 op: cvThreshold (FUN_1812b6a40 in DistanceGradation).
P1 op: cvDistTransform (FUN_1812b15a0 in DistanceGradation), limited to the
observed DIST_L2 + DIST_MASK_PRECISE call shape.

Validation gates, most-to-least grounded:

  GATE A (detour fires & round-trips) — install the detour, call FUN_1812b6a40
    under emulation, confirm the handler runs (emulated body bypassed: tiny
    instruction count), the src IplImage is decoded, and the dst IplImage buffer
    is written. Also confirms the dst header is untouched (design §6.3 tripwire).

  GATE B (bit-exactness vs independent oracle) — the detour output AND the
    XMM0 return value must be bit-identical to the real OpenCV 4.5.5
    cv2.threshold, invoked out-of-process in the .venv-cv455 sidecar
    (python3.12 + numpy<2 + opencv-python-headless==4.5.5.64; see README).
    The reference is NOT cvthreshold_native itself — a prior revision made
    that self-referential mistake and missed 44/80 boundary divergences
    (cvFloor/cvRound/saturate/special-paths, NaN in the _INV forms).
    Caveat: the sidecar wheel is arm64; integer paths are LUT-exact vs
    Windows x64 unconditionally, float paths match except 32F TRUNC on NaN
    (SSE minps returns thresh for NaN lanes; NEON/numpy pass NaN through) —
    see OPENCV_DETOUR_P0B_REPORT.md Known Limitations.

  GATE C (bounded embedded-body equivalence) — run the *real* emulated
    cvThreshold and
    compare it with the independent OpenCV 4.5.5 sidecar. The opt-in Windows
    runtime scaffold supplies the TEB TLS epoch, FLS value storage, and aligned
    allocator while the AEX executes its own OpenCV lazy initialization and
    threshold body. It is required to pass, but it is not a substitute for a
    Windows host capture: optional environment/dispatch and single-thread lock
    imports remain bounded stubs in AexLoader.

Run:
    tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
"""

from __future__ import annotations

import struct
import sys
import argparse
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader  # noqa: E402
import cv_bridge as cvb  # noqa: E402
import opencv_impls as ocv  # noqa: E402
from windows_runtime import WindowsOpenCVRuntime  # noqa: E402

AEX = str(Path(__file__).resolve().parents[2] / "plugins_2025" / "DistanceGradation.aex")
CVTHRESHOLD = ocv.CVTHRESHOLD_ADDR["DistanceGradation"]
CVDISTTRANSFORM = ocv.CV_DIST_TRANSFORM_ADDR["DistanceGradation"]
CVRESIZE = ocv.CV_RESIZE_ADDR["DistanceGradation"]
CVNORMALIZE = ocv.CV_NORMALIZE_ADDR["DistanceGradation"]

TYPE_NAMES = {0: "BINARY", 1: "BINARY_INV", 2: "TRUNC", 3: "TOZERO", 4: "TOZERO_INV"}


def _fresh_loader():
    ld = AexLoader(AEX, verbose=False)
    ld.register_libm_impls(max_threads=1)
    return ld


def _bits_equal(a: np.ndarray, b: np.ndarray) -> bool:
    a = np.ascontiguousarray(a)
    b = np.ascontiguousarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    return a.tobytes() == b.tobytes()


def _unimplemented_import_names(loader: AexLoader) -> list[str]:
    """Imports reached through AexLoader's explicit log-and-return-zero path."""
    return sorted({call.name for call in loader.import_log if call.name not in loader.import_impls})


def run_sidecar_oracle(payload: dict) -> dict[str, np.ndarray]:
    sidecar_python = Path(__file__).resolve().parent / ".venv-cv455" / "bin" / "python"
    if not sidecar_python.exists():
        raise FileNotFoundError("sidecar venv not found")

    oracle_script = Path(__file__).resolve().parent / "sidecar_oracle.py"
    import tempfile
    import subprocess
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "in.npz")
        out_path = os.path.join(tmpdir, "out.npz")
        np.savez(in_path, **payload)
        subprocess.run([str(sidecar_python), str(oracle_script), in_path, out_path], check=True)
        data = np.load(out_path)
        return {key: data[key] for key in data.files}


def run_detour_case(dtype, ttype, thresh, maxval, seed, inject_nan=False):
    """GATE A + B for one (dtype, type) case. Returns (status, detail)."""
    ld = _fresh_loader()
    ocv.register_opencv_impls(ld, "DistanceGradation", ops=["threshold"])

    rng = np.random.default_rng(seed)
    if np.issubdtype(dtype, np.floating):
        src = rng.uniform(-0.2, 1.2, size=(16, 16)).astype(dtype)
        if inject_nan:
            src[0, 0] = np.nan
            src[5, 5] = np.nan
    else:
        info = np.iinfo(dtype)
        src = rng.integers(info.min, info.max, size=(16, 16), endpoint=True).astype(dtype)

    poison = dtype.type(123) if np.issubdtype(dtype, np.integer) else dtype.type(999.0)
    dst = np.full((16, 16), poison, dtype=dtype)

    src_ipl = cvb.build_ipl(ld, src)
    dst_ipl = cvb.build_ipl(ld, dst)
    hdr_before = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)

    res = ld.call_function(
        CVTHRESHOLD,
        int_args=[src_ipl, dst_ipl, 0, 0, ttype],
        float_args={2: (thresh, "d"), 3: (maxval, "d")},
        max_instructions=2_000_000,
    )
    out = cvb.read_ipl(ld, dst_ipl)
    hdr_after = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    ret_xmm0 = ld.read_xmm_f64(0)
    
    try:
        data = run_sidecar_oracle({
            "op": np.array(["threshold"]),
            "src": src,
            "thresh": thresh,
            "maxval": maxval,
            "ttype": ttype,
        })
    except FileNotFoundError:
        return "SKIP", "sidecar venv not found; GATE B skipped"
    ref = data["dst"]
    oracle_ret = float(data["retval"][0])

    # GATE A: body bypassed (few instructions), dst actually written, header intact
    bypassed = res["instructions"] < 100
    written = not _bits_equal(out, np.full((16, 16), poison, dtype=dtype))
    header_intact = (hdr_before == hdr_after)
    # GATE B: bit-exact vs exact reference
    bit_exact = _bits_equal(out, ref)
    # Check XMM0 return value matches oracle
    # Note: NaNs in numpy are not equal, so explicitly check if both are NaN
    ret_exact = (ret_xmm0 == oracle_ret) or (np.isnan(ret_xmm0) and np.isnan(oracle_ret))

    ok = bypassed and written and header_intact and bit_exact and ret_exact
    detail = (f"instr={res['instructions']} bypassed={bypassed} written={written} "
              f"header_intact={header_intact} bit_exact={bit_exact} ret_exact={ret_exact}")
    return "PASS" if ok else "FAIL", detail


def make_distance_case(kind: str) -> np.ndarray:
    shape = {
        "one_by_one_zero": (1, 1),
        "one_by_one_nonzero": (1, 1),
        "one_by_n": (1, 17),
        "n_by_one": (17, 1),
        "all_nonzero": (3, 4),
    }.get(kind, (19, 23))
    src = np.ones(shape, dtype=np.uint8) * 255
    if kind == "single_zero":
        src[9, 11] = 0
    elif kind == "cross":
        src[9, :] = 0
        src[:, 11] = 0
    elif kind == "box":
        src[3:7, 4:9] = 0
        src[14, 19] = 0
    elif kind == "diagonal":
        yy, xx = np.indices(src.shape)
        src[(xx - yy) % 7 == 0] = 0
    elif kind == "all_nonzero":
        pass
    elif kind == "all_zero":
        src[:, :] = 0
    elif kind == "one_by_one_zero":
        src[0, 0] = 0
    elif kind == "one_by_one_nonzero":
        pass
    elif kind == "one_by_n":
        src[0, 8] = 0
    elif kind == "n_by_one":
        src[8, 0] = 0
    else:
        raise ValueError(kind)
    return src


def run_dist_transform_case(kind: str):
    """P1 GATE A+B for cvDistTransform DIST_L2/PRECISE."""
    ld = _fresh_loader()
    ocv.register_opencv_impls(ld, "DistanceGradation", ops=["dist_transform"])

    src = make_distance_case(kind)
    poison = np.full(src.shape, -999.0, dtype=np.float32)
    src_ipl = cvb.build_ipl(ld, src)
    align_step = 16 if kind in {"all_nonzero", "one_by_n", "n_by_one"} else 4
    dst_ipl = cvb.build_ipl(ld, poison, align_step=align_step)
    hdr_before = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)

    res = ld.call_function(
        CVDISTTRANSFORM,
        int_args=[src_ipl, dst_ipl, ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0, 0, 0],
        max_instructions=2_000_000,
    )
    out = cvb.read_ipl(ld, dst_ipl)
    hdr_after = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    native = ocv.cvdisttransform_l2_precise_native(src)

    try:
        data = run_sidecar_oracle({
            "op": np.array(["distance_transform_l2_precise"]),
            "src": src,
        })
    except FileNotFoundError:
        return "SKIP", "sidecar venv not found; GATE B skipped"
    ref = data["dst"]

    bypassed = res["instructions"] < 100
    written = not _bits_equal(out, poison)
    header_intact = (hdr_before == hdr_after)
    native_exact = _bits_equal(out, native)
    cv455_exact = _bits_equal(out, ref)
    max_abs = float(np.max(np.abs(out.astype(np.float64) - ref.astype(np.float64))))

    ok = bypassed and written and header_intact and native_exact and cv455_exact
    detail = (f"instr={res['instructions']} bypassed={bypassed} written={written} "
              f"header_intact={header_intact} native_exact={native_exact} "
              f"cv455_exact={cv455_exact} max_abs={max_abs:g} align_step={align_step}")
    return "PASS" if ok else "FAIL", detail


def run_real_dist_transform_case(kind: str):
    """GATE C: execute the embedded AEX OpenCV body without a detour.

    The arm64 cv455 sidecar is an independent semantic oracle, but not a byte
    oracle for x86 SIMD. Known relations are pinned explicitly so a new pattern
    fails instead of being hidden behind a tolerance.
    """
    ld = _fresh_loader()
    WindowsOpenCVRuntime(ld).install()

    src = make_distance_case(kind)
    poison = np.full(src.shape, -999.0, dtype=np.float32)
    src_ipl = cvb.build_ipl(ld, src)
    dst_ipl = cvb.build_ipl(ld, poison, align_step=16)
    hdr_before = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)

    try:
        res = ld.call_function(
            CVDISTTRANSFORM,
            int_args=[
                src_ipl,
                dst_ipl,
                ocv.CV_DIST_L2,
                ocv.CV_DIST_MASK_PRECISE,
                0,
                0,
                0,
            ],
            max_instructions=100_000_000,
        )
    except RuntimeError as exc:
        return "FAIL", f"embedded OpenCV execution fault: {exc}"

    out = cvb.read_ipl(ld, dst_ipl)
    hdr_after = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    try:
        ref = run_sidecar_oracle({
            "op": np.array(["distance_transform_l2_precise"]),
            "src": src,
        })["dst"]
    except FileNotFoundError:
        return "SKIP", "sidecar venv not found; GATE C oracle skipped"

    fls_created = any(call.name == "FlsSetValue" and call.ret == 1 for call in ld.import_log)
    body_executed = res["instructions"] > 100
    header_intact = hdr_before == hdr_after
    out_bits = out.view(np.uint32)
    ref_bits = ref.view(np.uint32)
    bit_exact = _bits_equal(out, ref)
    max_abs = float(np.max(np.abs(out.astype(np.float64) - ref.astype(np.float64))))
    mismatch = out_bits != ref_bits
    mismatch_count = int(np.count_nonzero(mismatch))
    if bit_exact:
        relation = "cv455_exact"
        relation_ok = True
    elif kind in {"single_zero", "box"}:
        expected_count = {"single_zero": 44, "box": 19}[kind]
        relation = "embedded_x86_simd_one_ulp_below_arm64_cv455"
        relation_ok = (
            mismatch_count == expected_count
            and bool(np.all(out_bits[mismatch] + np.uint32(1) == ref_bits[mismatch]))
        )
    elif kind in {"all_nonzero", "one_by_one_nonzero"}:
        relation = "embedded_no_source_sentinel_0x5f7fffff"
        relation_ok = bool(
            np.all(out_bits == np.uint32(0x5F7FFFFF))
            and np.all(ref_bits == np.uint32(0x4BF1433C))
        )
    else:
        relation = "unexpected_divergence"
        relation_ok = False
    ok = body_executed and fls_created and header_intact and relation_ok
    unresolved = _unimplemented_import_names(ld)
    detail = (
        f"instr={res['instructions']} body_executed={body_executed} "
        f"fls_created={fls_created} header_intact={header_intact} "
        f"cv455_exact={bit_exact} relation={relation} mismatches={mismatch_count} "
        f"max_abs={max_abs:g} "
        f"bounded_stub_imports={','.join(unresolved)}"
    )
    return "PASS" if ok else "FAIL", detail


def run_dist_transform_contract_case():
    """
    P1 contract regression: cvDistTransform accepts src uint8 -> dst float32 and
    rejects the old threshold-style same-dtype contract.
    """
    ld = _fresh_loader()
    ocv.register_opencv_impls(ld, "DistanceGradation", ops=["dist_transform"])

    src = make_distance_case("cross")
    good_dst = np.full(src.shape, -999.0, dtype=np.float32)
    bad_dst = np.zeros(src.shape, dtype=np.uint8)

    src_ipl = cvb.build_ipl(ld, src)
    good_dst_ipl = cvb.build_ipl(ld, good_dst, align_step=16)
    bad_dst_ipl = cvb.build_ipl(ld, bad_dst)

    good = ld.call_function(
        CVDISTTRANSFORM,
        int_args=[src_ipl, good_dst_ipl, ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0, 0, 0],
        max_instructions=200_000,
    )
    good_out = cvb.read_ipl(ld, good_dst_ipl)
    good_ok = good["instructions"] < 100 and good_out.dtype == np.float32

    def call_and_capture(dst_ptr, args):
        try:
            ld.call_function(CVDISTTRANSFORM, int_args=[src_ipl, dst_ptr, *args], max_instructions=200_000)
        except Exception as exc:  # RuntimeError wrapper carries the Python ValueError text
            return str(exc)
        return "<none>"

    bad_dst_msg = call_and_capture(
        bad_dst_ipl, [ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0, 0, 0]
    )
    bad_dist_msg = call_and_capture(
        good_dst_ipl, [3, ocv.CV_DIST_MASK_PRECISE, 0, 0, 0]
    )
    bad_mask_size_msg = call_and_capture(
        good_dst_ipl, [ocv.CV_DIST_L2, 3, 0, 0, 0]
    )
    bad_mask_msg = call_and_capture(
        good_dst_ipl, [ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0x1234, 0, 0]
    )
    bad_labels_msg = call_and_capture(
        good_dst_ipl, [ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0, 0x1234, 0]
    )
    bad_label_type_msg = call_and_capture(
        good_dst_ipl, [ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0, 0, 1]
    )

    rejected = {
        "bad_dst": "cvDistTransform dst mismatch" in bad_dst_msg,
        "dist_type": "only supports DIST_L2/PRECISE" in bad_dist_msg,
        "mask_size": "only supports DIST_L2/PRECISE" in bad_mask_size_msg,
        "mask": "does not support mask/labels/labelType" in bad_mask_msg,
        "labels": "does not support mask/labels/labelType" in bad_labels_msg,
        "label_type": "does not support mask/labels/labelType" in bad_label_type_msg,
    }
    ok = good_ok and all(rejected.values())
    detail = (f"good_path={good_ok} rejected="
              f"{','.join(name for name, value in rejected.items() if value)}/6")
    return "PASS" if ok else "FAIL", detail


def run_dist_transform_random_case(seed: int, shape: tuple[int, int], zero_probability: float):
    """P1 regression against sidecar on a deterministic non-geometric mask."""
    ld = _fresh_loader()
    ocv.register_opencv_impls(ld, "DistanceGradation", ops=["dist_transform"])
    rng = np.random.default_rng(seed)
    src = np.where(rng.random(shape) < zero_probability, 0, 255).astype(np.uint8)
    # Keep both source classes present so this checks the general two-pass path.
    src[0, 0] = 0
    src[-1, -1] = 255
    poison = np.full(shape, -999.0, dtype=np.float32)
    src_ipl = cvb.build_ipl(ld, src, align_step=16)
    dst_ipl = cvb.build_ipl(ld, poison, align_step=16)
    hdr_before = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    res = ld.call_function(
        CVDISTTRANSFORM,
        int_args=[src_ipl, dst_ipl, ocv.CV_DIST_L2, ocv.CV_DIST_MASK_PRECISE, 0, 0, 0],
        max_instructions=200_000,
    )
    out = cvb.read_ipl(ld, dst_ipl)
    hdr_after = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    data = run_sidecar_oracle({
        "op": np.array(["distance_transform_l2_precise"]),
        "src": src,
    })
    ref = data["dst"]
    ok = (
        res["instructions"] < 100
        and hdr_before == hdr_after
        and _bits_equal(out, ocv.cvdisttransform_l2_precise_native(src))
        and _bits_equal(out, ref)
    )
    detail = (f"instr={res['instructions']} header_intact={hdr_before == hdr_after} "
              f"native_exact={_bits_equal(out, ocv.cvdisttransform_l2_precise_native(src))} "
              f"cv455_exact={_bits_equal(out, ref)} max_abs="
              f"{float(np.max(np.abs(out.astype(np.float64) - ref.astype(np.float64)))):g}")
    return "PASS" if ok else "FAIL", detail


def run_resize_same_shape_case(dtype, shape, interpolation: int):
    """P1C GATE A for the limited same-shape cvResize detour."""
    ld = _fresh_loader()
    ocv.register_opencv_impls(ld, "DistanceGradation", ops=["resize_same_shape"])
    rng = np.random.default_rng(300 + interpolation + len(shape))
    if np.issubdtype(dtype, np.floating):
        src = rng.uniform(-10, 10, shape).astype(dtype)
    else:
        src = rng.integers(0, 255, shape).astype(dtype)
    poison = np.zeros(shape, dtype=dtype)
    src_ipl = cvb.build_ipl(ld, src, align_step=4)
    dst_ipl = cvb.build_ipl(ld, poison, align_step=16)
    hdr_before = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    res = ld.call_function(
        CVRESIZE,
        int_args=[src_ipl, dst_ipl, interpolation],
        max_instructions=200_000,
    )
    out = cvb.read_ipl(ld, dst_ipl)
    hdr_after = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    bypassed = res["instructions"] < 100
    written = _bits_equal(out, src)
    header_intact = (hdr_before == hdr_after)
    ok = bypassed and written and header_intact
    detail = (f"instr={res['instructions']} bypassed={bypassed} copy_exact={written} "
              f"header_intact={header_intact} interp={interpolation}")
    return "PASS" if ok else "FAIL", detail


def run_normalize_minmax_case(kind: str, beta: float):
    """P2 limited GATE A+B for cvNormalize NORM_MINMAX/no-mask."""
    ld = _fresh_loader()
    ocv.register_opencv_impls(ld, "DistanceGradation", ops=["normalize_minmax"])
    if kind == "ramp":
        src = np.linspace(0.0, 36.0, 19 * 23, dtype=np.float32).reshape(19, 23)
    elif kind == "binary":
        src = np.zeros((19, 23), dtype=np.float32)
        src[3:11, 5:17] = 36.0
    elif kind == "constant_zero":
        src = np.zeros((11, 17), dtype=np.float32)
    elif kind == "constant_nonzero":
        src = np.full((11, 17), 36.0, dtype=np.float32)
    else:
        raise ValueError(kind)
    poison = np.full(src.shape, -999.0, dtype=np.float32)
    src_ipl = cvb.build_ipl(ld, src, align_step=4)
    dst_ipl = cvb.build_ipl(ld, poison, align_step=16)
    hdr_before = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    res = ld.call_function(
        CVNORMALIZE,
        int_args=[src_ipl, dst_ipl, 0, 0, ocv.CV_NORM_MINMAX, 0],
        float_args={2: (0.0, "d"), 3: (beta, "d")},
        max_instructions=200_000,
    )
    out = cvb.read_ipl(ld, dst_ipl)
    hdr_after = ld.read_bytes(dst_ipl, cvb.IPL_SIZE)
    native = ocv.cvnormalize_minmax_native(src, 0.0, beta)
    try:
        data = run_sidecar_oracle({
            "op": np.array(["normalize_minmax"]),
            "src": src,
            "alpha": 0.0,
            "beta": beta,
        })
    except FileNotFoundError:
        return "SKIP", "sidecar venv not found; GATE B skipped"
    ref = data["dst"]
    bypassed = res["instructions"] < 100
    written = not _bits_equal(out, poison)
    header_intact = (hdr_before == hdr_after)
    native_exact = _bits_equal(out, native)
    cv455_exact = _bits_equal(out, ref)
    max_abs = float(np.max(np.abs(out.astype(np.float64) - ref.astype(np.float64))))
    ok = bypassed and written and header_intact and native_exact and cv455_exact
    detail = (f"instr={res['instructions']} bypassed={bypassed} written={written} "
              f"header_intact={header_intact} native_exact={native_exact} "
              f"cv455_exact={cv455_exact} max_abs={max_abs:g} beta={beta:g}")
    return "PASS" if ok else "FAIL", detail


def run_roundtrip_case():
    """Bridge sanity: build -> read -> write -> read is identity (design §4)."""
    ld = _fresh_loader()
    for dtype in (np.uint8, np.uint16, np.float32):
        rng = np.random.default_rng(1)
        if np.issubdtype(dtype, np.floating):
            a = rng.uniform(0, 1, (7, 13)).astype(dtype)
        else:
            a = rng.integers(0, 200, (7, 13)).astype(dtype)
        ipl = cvb.build_ipl(ld, a)
        b = cvb.read_ipl(ld, ipl)
        if not _bits_equal(a, b):
            return False, f"round-trip mismatch for {np.dtype(dtype)}"
        # 3-channel case (non-trivial widthStep padding via align)
        c = rng.integers(0, 200, (5, 6, 3)).astype(np.uint8) if dtype == np.uint8 else None
        if c is not None:
            ipl3 = cvb.build_ipl(ld, c)
            if not _bits_equal(c, cvb.read_ipl(ld, ipl3)):
                return False, "round-trip mismatch for 3-channel uint8"
    return True, "bridge round-trip ok (uint8/uint16/float32 + 3ch)"


def probe_gate_c():
    """
    Execute the embedded threshold body under the bounded runtime scaffold.

    The independent sidecar comparison, instruction-count guard, and successful
    FLS publication are all required. Reached zero-return host imports remain
    visible in the result and prevent treating this as a Windows-host oracle.
    """
    ld = _fresh_loader()
    WindowsOpenCVRuntime(ld).install()
    src = (np.arange(256, dtype=np.float32).reshape(16, 16) / 255.0)
    dst = np.zeros((16, 16), np.float32)
    s = cvb.build_ipl(ld, src)
    d = cvb.build_ipl(ld, dst)
    try:
        res = ld.call_function(
            CVTHRESHOLD,
            int_args=[s, d, 0, 0, 2],
            float_args={2: (0.1, "d"), 3: (1.0, "d")},
            max_instructions=50_000_000,
        )
        out = cvb.read_ipl(ld, d)
        
        sidecar_python = Path(__file__).resolve().parent / ".venv-cv455" / "bin" / "python"
        if not sidecar_python.exists():
            return "SKIP", "sidecar venv not found; GATE B oracle skipped"
            
        oracle_script = Path(__file__).resolve().parent / "sidecar_oracle.py"
        import tempfile
        import subprocess
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "in.npz")
            out_path = os.path.join(tmpdir, "out.npz")
            np.savez(in_path, op=np.array(["threshold"]), src=src, thresh=0.1, maxval=1.0, ttype=2)
            subprocess.run([str(sidecar_python), str(oracle_script), in_path, out_path], check=True)
            ref = np.load(out_path)["dst"]
            
        body_executed = res["instructions"] > 100
        fls_created = any(call.name == "FlsSetValue" and call.ret == 1 for call in ld.import_log)
        bit_exact = _bits_equal(out, ref)
        unresolved = _unimplemented_import_names(ld)
        ok = body_executed and fls_created and bit_exact
        return ("PASS" if ok else "BLOCKED",
                f"emulated cvThreshold completed in {res['instructions']} instr; "
                f"body_executed={body_executed}; fls_created={fls_created}; "
                f"bit-exact vs reference={bit_exact}; "
                f"bounded_stub_imports={','.join(unresolved)}")
    except RuntimeError as exc:
        msg = str(exc)
        rip = msg.split("RIP=")[-1].split(":")[0] if "RIP=" in msg else "?"
        return "FAIL", f"embedded OpenCV path faults at RIP={rip}"


def run_p1_only() -> int:
    """Run only the P1 EDT oracle/ABI gates for focused conformance capture."""
    print(f"AEX: {AEX}")
    print(f"cvDistTransform @ 0x{CVDISTTRANSFORM:x}")
    failures = 0
    for kind in (
        "single_zero", "cross", "box", "diagonal", "all_nonzero", "all_zero",
        "one_by_one_zero", "one_by_one_nonzero", "one_by_n", "n_by_one",
    ):
        status, detail = run_dist_transform_case(kind)
        print(f"[{status:4}] detour dist_transform/{kind:16} {detail}")
        failures += status == "FAIL"
    for seed, shape, probability in (
        (4101, (2, 2), 0.25),
        (4102, (5, 7), 0.50),
        (4103, (31, 29), 0.10),
        (4104, (3, 64), 0.75),
        (4105, (64, 3), 0.35),
    ):
        status, detail = run_dist_transform_random_case(seed, shape, probability)
        print(f"[{status:4}] detour dist_transform/random_{seed} shape={shape} {detail}")
        failures += status == "FAIL"
    status, detail = run_dist_transform_contract_case()
    print(f"[{status:4}] detour dist_transform/contract       {detail}")
    failures += status == "FAIL"
    print(f"RESULT: {'P1 FAIL' if failures else 'P1 native EDT + cv455 oracle PASS'}")
    return int(bool(failures))


def main():
    parser = argparse.ArgumentParser(description="Validate the OpenCV detour layer")
    parser.add_argument("--p1-only", action="store_true", help="run only cvDistTransform P1 gates")
    args = parser.parse_args()
    if args.p1_only:
        return run_p1_only()
    print(f"AEX: {AEX}")
    print(f"cvThreshold @ 0x{CVTHRESHOLD:x}\n")
    print(f"cvDistTransform @ 0x{CVDISTTRANSFORM:x}\n")
    print(f"cvResize(same-shape) @ 0x{CVRESIZE:x}\n")
    print(f"cvNormalize(NORM_MINMAX) @ 0x{CVNORMALIZE:x}\n")

    failures = 0

    ok, detail = run_roundtrip_case()
    print(f"[{'PASS' if ok else 'FAIL'}] bridge round-trip: {detail}")
    failures += not ok

    # GATE A + B across types and dtypes
    cases = []
    for dtype in (np.dtype(np.float32), np.dtype(np.uint8)):
        for ttype in (0, 1, 2, 3, 4):
            if np.issubdtype(dtype, np.floating):
                thr, mx = 0.3, 1.0
            else:
                thr, mx = 100.0, 255.0
            cases.append((dtype, ttype, thr, mx, False))

    # Extended boundary cases
    for ttype in (0, 1, 2, 3, 4):
        cases.append((np.dtype(np.uint8), ttype, 300.0, 255.0, False))
        cases.append((np.dtype(np.uint8), ttype, -10.0, 255.0, False))
        cases.append((np.dtype(np.uint8), ttype, 100.0, 254.6, False))
        cases.append((np.dtype(np.uint8), ttype, 100.0, 254.5, False))
        cases.append((np.dtype(np.uint8), ttype, 100.0, 253.5, False))
        cases.append((np.dtype(np.uint16), ttype, 70000.0, 255.0, False))
        cases.append((np.dtype(np.uint16), ttype, -10.0, 255.0, False))
        cases.append((np.dtype(np.int16), ttype, -40000.0, 255.0, False))
        cases.append((np.dtype(np.int16), ttype, 40000.0, 255.0, False))
        cases.append((np.dtype(np.int16), ttype, -5.5, 255.0, False))
        cases.append((np.dtype(np.float32), ttype, 0.5, 1.0, True)) # NaN
        cases.append((np.dtype(np.float32), ttype, 0.1, 1.0, False)) # Narrowing

    for i, (dtype, ttype, thr, mx, inj_nan) in enumerate(cases):
        status, detail = run_detour_case(dtype, ttype, thr, mx, seed=100 + i, inject_nan=inj_nan)
        tag = f"{np.dtype(dtype).name}/{TYPE_NAMES[ttype]}"
        # Format the float output nicely for the tag
        xtra = " NaN" if inj_nan else ""
        if status == "SKIP":
            print(f"[{status:4}] detour {tag:20} {detail}")
        else:
            print(f"[{status:4}] detour {tag+xtra:20} thr={thr:g} {detail}")
        if status == "FAIL":
            failures += 1

    print()
    for kind in (
        "single_zero",
        "cross",
        "box",
        "diagonal",
        "all_nonzero",
        "all_zero",
        "one_by_one_zero",
        "one_by_one_nonzero",
        "one_by_n",
        "n_by_one",
    ):
        status, detail = run_dist_transform_case(kind)
        print(f"[{status:4}] detour dist_transform/{kind:12} {detail}")
        if status == "FAIL":
            failures += 1

    status, detail = run_dist_transform_contract_case()
    print(f"[{status:4}] detour dist_transform/contract     {detail}")
    if status == "FAIL":
        failures += 1

    print()
    for kind in (
        "single_zero",
        "cross",
        "box",
        "diagonal",
        "all_nonzero",
        "all_zero",
        "one_by_one_zero",
        "one_by_one_nonzero",
        "one_by_n",
        "n_by_one",
    ):
        status, detail = run_real_dist_transform_case(kind)
        print(f"[{status:4}] GATE C embedded dist_transform/{kind:16} {detail}")
        if status != "PASS":
            failures += 1

    print()
    for dtype, shape, interp in (
        (np.uint8, (11, 17), 0),
        (np.float32, (11, 17), 1),
        (np.uint8, (7, 9, 3), 0),
    ):
        status, detail = run_resize_same_shape_case(dtype, shape, interp)
        tag = f"{np.dtype(dtype).name}/{shape}"
        print(f"[{status:4}] detour resize_same_shape/{tag:18} {detail}")
        if status == "FAIL":
            failures += 1

    print()
    for kind, beta in (
        ("ramp", 32768.0),
        ("binary", 32768.0),
        ("constant_zero", 32768.0),
        ("constant_nonzero", 255.0),
    ):
        status, detail = run_normalize_minmax_case(kind, beta)
        print(f"[{status:4}] detour normalize_minmax/{kind:16} {detail}")
        if status == "FAIL":
            failures += 1

    # GATE C executes the embedded OpenCV body under an explicit bounded host scaffold.
    status, detail = probe_gate_c()
    print(f"\n[GATE C {status}] emulated-equivalence: {detail}")
    if status != "PASS":
        failures += 1

    print()
    if failures:
        print(f"RESULT: {failures} FAIL")
        return 1
    print("RESULT: all detour + bridge gates PASS (GATE A+B + bounded C relations).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
