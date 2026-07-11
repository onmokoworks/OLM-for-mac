"""
opencv_impls.py — native (numpy) implementations of the OpenCV C-API primitives
the OLM plugins delegate to, installed as detours over the emulated .aex entry
points (OPENCV_DETOUR_DESIGN.md rev 2).

P0: cvThreshold (FUN_1812b6a40 in DistanceGradation). cv2-free — the exact ops
are trivially reproducible in numpy (design §5).

P1: cvDistTransform (FUN_1812b15a0 in DistanceGradation), limited to the observed
DIST_L2 + DIST_MASK_PRECISE call shape. cv2-free native implementation uses a
Meijster-style exact EDT but follows OpenCV 4.5.5 sentinel behavior; sidecar cv2
4.5.5 is used by tests as an independent oracle.

P1C: cvResize entry (FUN_1812aef70 in DistanceGradation), limited to same-shape,
same-dtype copies. This is only enough to let the DG fieldgen probe pass through
the two observed no-resize staging calls; real resize semantics remain disabled.

An op is only registered via register_opencv_impls(ops=[...]) after its
dual-run/validation passes.

Handler contract (design §6): handler(loader, args), args = RCX/RDX/R8/R9.
Floats/doubles come from XMM via loader.read_xmm_f64; stack args via
cv_bridge.read_stack_arg. The handler reads the src IplImage(s), runs the native
op, writes the dst IplImage's existing buffer, sets the return register(s), and
returns (the detour's RET hands control back to the caller).
"""

from __future__ import annotations

import math

import numpy as np

import cv_bridge as cvb

# cvThreshold entry points, per binary (design §7). Re-confirm per module.
CVTHRESHOLD_ADDR = {
    "DistanceGradation": 0x1812b6a40,  # FUN_1812b6a40 (FACT: "cvThreshold" in assert path)
}
CV_DIST_TRANSFORM_ADDR = {
    "DistanceGradation": 0x1812b15a0,  # FUN_1812b15a0 (FACT: DG calls as DIST_L2 + PRECISE)
}
CV_RESIZE_ADDR = {
    "DistanceGradation": 0x1812aef70,  # FUN_1812aef70 (cvResize-like; P1C same-shape only)
}
CV_NORMALIZE_ADDR = {
    "DistanceGradation": 0x18117ca50,  # cvNormalize wrapper; P2 limited NORM_MINMAX/no-mask
}

# OpenCV threshold type codes
THRESH_BINARY     = 0
THRESH_BINARY_INV = 1
THRESH_TRUNC      = 2
THRESH_TOZERO     = 3
THRESH_TOZERO_INV = 4
THRESH_MASK       = 7   # low 3 bits select the type; OTSU/TRIANGLE flags are above
THRESH_OTSU       = 8
THRESH_TRIANGLE   = 16

CV_DIST_L2 = 2
CV_DIST_MASK_PRECISE = 0
CV_DIST_INF_I32 = 31_622_776
CV_NORM_MINMAX = 0x20


def cvthreshold_native(src: np.ndarray, thresh: float, maxval: float, ttype: int) -> np.ndarray:
    """
    Pure-numpy cvThreshold, bit-exact for the deterministic types on integer or
    float images (design §5). thresh/maxval are cast to the image dtype exactly
    as OpenCV does. OTSU/TRIANGLE auto-thresholding is NOT supported (raises).
    """
    flag = ttype & THRESH_MASK
    if ttype & (THRESH_OTSU | THRESH_TRIANGLE):
        raise NotImplementedError("THRESH_OTSU/TRIANGLE not supported by the detour")

    dt = src.dtype
    
    if np.issubdtype(dt, np.floating):
        t = dt.type(thresh)
        m = dt.type(maxval)
        zero = dt.type(0)
        
        if flag == THRESH_BINARY:
            return np.where(src > t, m, zero).astype(dt)
        if flag == THRESH_BINARY_INV:
            return np.where(src <= t, m, zero).astype(dt)
        if flag == THRESH_TRUNC:
            return np.where(src > t, t, src).astype(dt)
        if flag == THRESH_TOZERO:
            return np.where(src > t, src, zero).astype(dt)
        if flag == THRESH_TOZERO_INV:
            return np.where(src <= t, src, zero).astype(dt)
            
    else:
        ithresh = math.floor(thresh)
        
        info = np.iinfo(dt)
        rmaxval = round(maxval)
        if rmaxval < info.min:
            imaxval_val = info.min
        elif rmaxval > info.max:
            imaxval_val = info.max
        else:
            imaxval_val = rmaxval
            
        imaxval = dt.type(imaxval_val)
        zero = dt.type(0)
        
        if ithresh < info.min:
            if flag == THRESH_BINARY:
                return np.full_like(src, imaxval)
            elif flag in (THRESH_BINARY_INV, THRESH_TRUNC, THRESH_TOZERO_INV):
                return np.full_like(src, zero)
            elif flag == THRESH_TOZERO:
                return src.copy()
        elif ithresh > info.max:
            if flag == THRESH_BINARY_INV:
                return np.full_like(src, imaxval)
            elif flag in (THRESH_BINARY, THRESH_TOZERO):
                return np.full_like(src, zero)
            elif flag in (THRESH_TRUNC, THRESH_TOZERO_INV):
                return src.copy()
                
        t = dt.type(ithresh)
        gt = src > t
        
        if flag == THRESH_BINARY:
            return np.where(gt, imaxval, zero).astype(dt)
        if flag == THRESH_BINARY_INV:
            return np.where(gt, zero, imaxval).astype(dt)
        if flag == THRESH_TRUNC:
            return np.where(gt, t, src).astype(dt)
        if flag == THRESH_TOZERO:
            return np.where(gt, src, zero).astype(dt)
        if flag == THRESH_TOZERO_INV:
            return np.where(gt, zero, src).astype(dt)

    raise ValueError(f"unknown threshold type flag {flag}")


def _c_trunc_div(num: int, den: int) -> int:
    """C/C++ signed integer division truncates toward zero; Python // floors."""
    if den == 0:
        raise ZeroDivisionError("division by zero")
    q = abs(num) // abs(den)
    return -q if (num < 0) ^ (den < 0) else q


def _edt_f32(x: int, i: int, gi: int) -> np.float32:
    d = x - i
    return np.float32(d * d + gi * gi)


def _edt_sep(i: int, u: int, gi: int, gu: int) -> int:
    num = u * u - i * i + gu * gu - gi * gi
    den = 2 * (u - i)
    return _c_trunc_div(num, den)


def cvdisttransform_l2_precise_native(src: np.ndarray) -> np.ndarray:
    """
    Exact Euclidean distance transform for the observed DG OpenCV call:
    cvDistTransform(src_8u, dst_32f, CV_DIST_L2, CV_DIST_MASK_PRECISE, ...).

    Uses the same Meijster-style exact EDT family as the Mac port:
    src == 0 is a distance source, src != 0 is measured to the nearest zero.
    The squared distance expression is rounded to float32 before sqrtf, matching
    the Mac implementation's `edt_f` return type. The all-foreground sentinel is
    intentionally OpenCV 4.5.5-compatible, not the earlier Mac image-size sentinel.
    """
    src = np.asarray(src)
    if src.ndim != 2 or src.dtype != np.uint8:
        raise ValueError(f"cvDistTransform P1 expects single-channel uint8 src, got {src.shape}/{src.dtype}")

    h, w = src.shape
    # OpenCV 4.5.5 precise L2 returns sqrtf(1e15) for all-foreground input.
    # Use the matching integer sentinel, not an image-size sentinel, so no-zero
    # masks and partially empty rows keep the same float32 behavior.
    inf = CV_DIST_INF_I32
    g = np.empty((h, w), dtype=np.int64)

    for x in range(w):
        g[0, x] = inf if src[0, x] else 0
        for y in range(1, h):
            if src[y, x]:
                prev = int(g[y - 1, x])
                g[y, x] = inf if prev == inf else prev + 1
            else:
                g[y, x] = 0
        for y in range(h - 2, -1, -1):
            below = int(g[y + 1, x])
            cur = int(g[y, x])
            if below != inf and below + 1 < cur:
                g[y, x] = below + 1

    dst = np.empty((h, w), dtype=np.float32)
    s = np.empty(w, dtype=np.int64)
    t = np.empty(w, dtype=np.int64)
    for y in range(h):
        q = 0
        s[0] = 0
        t[0] = 0
        grow = g[y]
        for u in range(1, w):
            while q >= 0 and _edt_f32(int(t[q]), int(s[q]), int(grow[s[q]])) > _edt_f32(int(t[q]), u, int(grow[u])):
                q -= 1
            if q < 0:
                q = 0
                s[0] = u
            else:
                w_sep = 1 + _edt_sep(int(s[q]), u, int(grow[s[q]]), int(grow[u]))
                if w_sep < w:
                    q += 1
                    s[q] = u
                    t[q] = w_sep

        for u in range(w - 1, -1, -1):
            d2 = _edt_f32(u, int(s[q]), int(grow[s[q]]))
            dst[y, u] = np.sqrt(d2, dtype=np.float32)
            if u == t[q]:
                q -= 1
    return dst


def cvnormalize_minmax_native(src: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """
    Limited cvNormalize(..., NORM_MINMAX, mask=0) for the DG fieldgen path.

    OpenCV maps min(src) -> alpha and max(src) -> beta. If min == max, OpenCV's
    NORM_MINMAX path returns alpha for every element; keep that behavior because
    Constant edge crops and all-zero masks rely on it.
    """
    src = np.asarray(src)
    if src.ndim != 2 or src.dtype != np.float32:
        raise ValueError(f"cvNormalize P2 expects single-channel float32 src, got {src.shape}/{src.dtype}")
    mn = np.float32(np.min(src))
    mx = np.float32(np.max(src))
    a = np.float32(alpha)
    b = np.float32(beta)
    if not np.isfinite(float(mn)) or not np.isfinite(float(mx)):
        raise NotImplementedError("cvNormalize detour does not support NaN/Inf inputs")
    if mx == mn:
        return np.full(src.shape, a, dtype=np.float32)
    scale = np.float32((b - a) / (mx - mn))
    shift = np.float32(a - mn * scale)
    return (src * scale + shift).astype(np.float32)


def _make_cvthreshold_handler():
    def handler(loader, args):
        # cvThreshold(src, dst, thresh, maxval, type)
        src_ipl = args[0]  # RCX
        dst_ipl = args[1]  # RDX
        thresh = loader.read_xmm_f64(2)          # XMM2 (double)
        maxval = loader.read_xmm_f64(3)          # XMM3 (double)
        ttype = cvb.read_stack_arg(loader, 4)    # 5th arg on the stack
        ttype = ttype & 0xFFFFFFFF

        src = cvb.read_ipl(loader, src_ipl)
        dst = cvb.read_ipl(loader, dst_ipl)
        
        if src.shape != dst.shape or src.dtype != dst.dtype:
            raise ValueError(f"cvThreshold size/depth mismatch: src={src.shape}/{src.dtype}, dst={dst.shape}/{dst.dtype}")
            
        out = cvthreshold_native(src, thresh, maxval, ttype)
        cvb.write_ipl(loader, dst_ipl, out)

        # cvThreshold returns the used threshold as a double in XMM0.
        if np.issubdtype(src.dtype, np.floating):
            loader.write_xmm_f64(0, float(thresh))
        else:
            loader.write_xmm_f64(0, float(math.floor(thresh)))
        return 0
    return handler


def _make_cvdisttransform_handler():
    def handler(loader, args):
        # cvDistTransform(src, dst, distance_type, mask_size, mask, labels, labelType)
        src_ipl = args[0]  # RCX
        dst_ipl = args[1]  # RDX
        dist_type = args[2] & 0xFFFFFFFF  # R8D
        mask_size = args[3] & 0xFFFFFFFF  # R9D
        mask = cvb.read_stack_arg(loader, 4)
        labels = cvb.read_stack_arg(loader, 5)
        label_type = cvb.read_stack_arg(loader, 6) & 0xFFFFFFFF

        if dist_type != CV_DIST_L2 or mask_size != CV_DIST_MASK_PRECISE:
            raise NotImplementedError(f"cvDistTransform detour only supports DIST_L2/PRECISE, got dist={dist_type} mask={mask_size}")
        if mask or labels or label_type:
            raise NotImplementedError(f"cvDistTransform detour does not support mask/labels/labelType ({mask:#x}, {labels:#x}, {label_type})")

        src = cvb.read_ipl(loader, src_ipl)
        dst = cvb.read_ipl(loader, dst_ipl)
        if dst.shape != src.shape or dst.dtype != np.float32:
            raise ValueError(f"cvDistTransform dst mismatch: src={src.shape}/{src.dtype}, dst={dst.shape}/{dst.dtype}")

        out = cvdisttransform_l2_precise_native(src)
        cvb.write_ipl(loader, dst_ipl, out)
        return 0
    return handler


def _make_cvresize_same_shape_handler():
    def handler(loader, args):
        # FUN_1812aef70(src, dst, interpolation). Only same-shape/same-dtype copy
        # is validated here; broader NN/linear resize stays disabled.
        src_ipl = args[0]
        dst_ipl = args[1]
        interpolation = args[2] & 0xFFFFFFFF
        src = cvb.read_ipl(loader, src_ipl)
        dst = cvb.read_ipl(loader, dst_ipl)
        if src.shape != dst.shape or src.dtype != dst.dtype:
            raise NotImplementedError(
                "cvResize P1C only supports same-shape/same-dtype copies, "
                f"got src={src.shape}/{src.dtype} dst={dst.shape}/{dst.dtype} interp={interpolation}"
            )
        cvb.write_ipl(loader, dst_ipl, src)
        return 0
    return handler


def _make_cvnormalize_minmax_handler():
    def handler(loader, args):
        # cvNormalize(src, dst, alpha, beta, norm_type, mask)
        src_ipl = args[0]
        dst_ipl = args[1]
        alpha = loader.read_xmm_f64(2)
        beta = loader.read_xmm_f64(3)
        norm_type = cvb.read_stack_arg(loader, 4) & 0xFFFFFFFF
        mask = cvb.read_stack_arg(loader, 5)
        if norm_type != CV_NORM_MINMAX:
            raise NotImplementedError(f"cvNormalize detour only supports NORM_MINMAX, got {norm_type:#x}")
        if mask:
            raise NotImplementedError(f"cvNormalize detour does not support mask {mask:#x}")
        src = cvb.read_ipl(loader, src_ipl)
        dst = cvb.read_ipl(loader, dst_ipl)
        if src.shape != dst.shape or dst.dtype != np.float32:
            raise ValueError(f"cvNormalize dst mismatch: src={src.shape}/{src.dtype}, dst={dst.shape}/{dst.dtype}")
        out = cvnormalize_minmax_native(src.astype(np.float32, copy=False), alpha, beta)
        cvb.write_ipl(loader, dst_ipl, out)
        return 0
    return handler


# Registry: op name -> (address-map, handler factory)
_OPS = {
    "threshold": (CVTHRESHOLD_ADDR, _make_cvthreshold_handler),
    "dist_transform": (CV_DIST_TRANSFORM_ADDR, _make_cvdisttransform_handler),
    "resize_same_shape": (CV_RESIZE_ADDR, _make_cvresize_same_shape_handler),
    "normalize_minmax": (CV_NORMALIZE_ADDR, _make_cvnormalize_minmax_handler),
}


def register_opencv_impls(loader, module: str, ops=("threshold",)):
    """
    Install detours for the named ops on the given loader for a specific binary
    `module` (e.g. "DistanceGradation"). Only ops explicitly listed are enabled
    (design §9: an unvalidated op is disabled by default). Returns a dict of
    {op: guest_addr} that were patched.

    Mirrors register_libm_impls: additive, explicit, opt-in.
    """
    patched = {}
    for op in ops:
        if op not in _OPS:
            raise KeyError(f"unknown opencv op {op!r}; known: {sorted(_OPS)}")
        addr_map, factory = _OPS[op]
        if module not in addr_map:
            raise KeyError(f"no {op} address for module {module!r}; known: {sorted(addr_map)}")
        addr = addr_map[module]
        loader.detour_function(addr, f"cv::{op}", factory())
        patched[op] = addr
    return patched
