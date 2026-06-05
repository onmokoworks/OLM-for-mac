#!/usr/bin/env python3
"""AE-free OLMColorKey CLI.

Two verified Windows reference slices are covered:

1. Simple RGB/binary-alpha path (``render_rgb_binary``):
   RGB color space, one enabled key color, mean-delta threshold, no
   premultiply, no per-color/per-component box, no edge thin/blur, no replace.
   Validated exact (max=0) on case_0001..0004.

2. Premultiplied per-color/per-component path (``render_extended``):
   Premultiplied compare, per-color + per-component box keying, Color Keep,
   and Edge Thin (Distance Type 2 = L1/cityblock chamfer erode/dilate).
   Validated on case_0005..0007 (see notes/PORTING_BOARD.md):
     - dilate (Amount>0) is exact (case_0007 max=0);
     - erode (Amount<0) matches to ~0.48% of pixels, residual confined to the
       L1 distance shell where AE's matte keeps the diamond-corner pixels.

The keying math was reconstructed from decomp/OLMColorKey.aex.c.txt
(FUN_1800058a0 = orthogonal-only two-pass chamfer => exact L1 distance).
Edge Blur is partially reconstructed from FUN_1800049a0..FUN_1800056f0 and
FUN_1800085b0; it runs for cases 8/9 but is not yet reference-accurate. The
current boundary seed ignores the comp edge as an outside-matte neighbor, which
matches the Windows references better than treating the frame edge as a blur
boundary.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_cdt, distance_transform_edt


# --- parameter extraction -------------------------------------------------

def effect_params(payload):
    """Return the ordered (name, value) list for the OLM Color Key effect."""
    params = payload.get("params", payload)
    if isinstance(params, dict) and "effects" in params:
        for effect in params.get("effects", []):
            if effect.get("name") == "OLM Color Key" or effect.get("match_name") == "OLM Color Key":
                return [(p.get("name"), p.get("value")) for p in effect.get("params", [])]
    if isinstance(params, dict):
        return [(name, value) for name, value in params.items()]
    return []


def _num(value, default=0.0):
    if value is None:
        return default
    return float(value)


def _rgb(value, default=(0.0, 0.0, 0.0)):
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return np.array(default, dtype=np.float32)
    rgb = np.array([float(value[0]), float(value[1]), float(value[2])], dtype=np.float32)
    if np.max(rgb) > 1.0:
        rgb = rgb / 255.0
    return np.clip(rgb, 0.0, 1.0)


def read_params(params_path):
    with Path(params_path).open(encoding="utf-8") as handle:
        payload = json.load(handle)

    items = effect_params(payload)
    names = [name for name, _ in items]
    values = [value for _, value in items]

    def first(name, default=None):
        return values[names.index(name)] if name in names else default

    cfg = {
        "color_keep": _num(first("Color Keep")) != 0.0,
        "threshold": _num(first("Threshold")),
        "premultiplied": _num(first("Premultiplied Color")) != 0.0,
        "color_space": int(round(_num(first("Color Space"), 1.0))),
        "per_color": _num(first("Per Color")) != 0.0,
        "per_component": _num(first("Per Component")) != 0.0,
        "enable_replace": _num(first("Enable Replace")) != 0.0,
        "edge_thin_amount": 0.0,
        "edge_thin_distance_type": 1,
        "edge_blur_amount": 0.0,
        "edge_blur_distance_type": 1,
        "edge_blur_direction": 2,
        "key_color": _rgb(first("Color 1")),
        "colors": [],
    }

    # Edge Thin / Edge Blur are group headers followed by Amount / Distance Type.
    if "Edge Thin" in names:
        i = names.index("Edge Thin")
        cfg["edge_thin_amount"] = _num(values[i + 1]) if i + 1 < len(values) else 0.0
        cfg["edge_thin_distance_type"] = int(round(_num(values[i + 2], 1.0))) if i + 2 < len(values) else 1
    if "Edge Blur" in names:
        i = names.index("Edge Blur")
        cfg["edge_blur_amount"] = _num(values[i + 1]) if i + 1 < len(values) else 0.0
        cfg["edge_blur_distance_type"] = int(round(_num(values[i + 2], 1.0))) if i + 2 < len(values) else 1
        cfg["edge_blur_direction"] = int(round(_num(values[i + 3], 2.0))) if i + 3 < len(values) else 2

    # Per-color list (suffixed names are unique, e.g. "Color 1", "Use Color 1").
    ncol = int(round(_num(first("Number of Colors"), 1.0)))
    for i in range(1, ncol + 1):
        if f"Use Color {i}" in names and _num(values[names.index(f"Use Color {i}")]) == 0.0:
            continue
        cfg["colors"].append({
            "rgb": _rgb(first(f"Color {i}")),
            "threshold": _num(first(f"Threshold {i}")),
            "comp": np.array([
                _num(first(f"Threshold(R,H,L,Y,Y) {i}")),
                _num(first(f"Threshold(G,S,a,U,Cr) {i}")),
                _num(first(f"Threshold(B,V,b,V,Cb) {i}")),
            ], dtype=np.float32),
        })
    if not cfg["colors"]:
        cfg["colors"].append({"rgb": cfg["key_color"], "threshold": 0.0,
                              "comp": np.zeros(3, np.float32)})
    return cfg


# --- distance transform ---------------------------------------------------

def l1_distance(mask):
    """Exact L1 (cityblock) distance from each pixel to the nearest True pixel.

    Mirrors the plugin's FUN_1800058a0: a two-pass, orthogonal-only chamfer
    with unit step weights, which is exactly the separable L1 transform.
    Zero on ``mask`` pixels, growing outward.
    """
    inf = np.float32(1e9)
    d = np.where(mask, np.float32(0.0), inf)
    w, h = d.shape[1], d.shape[0]
    for x in range(1, w):
        np.minimum(d[:, x], d[:, x - 1] + 1.0, out=d[:, x])
    for x in range(w - 2, -1, -1):
        np.minimum(d[:, x], d[:, x + 1] + 1.0, out=d[:, x])
    for y in range(1, h):
        np.minimum(d[y, :], d[y - 1, :] + 1.0, out=d[y, :])
    for y in range(h - 2, -1, -1):
        np.minimum(d[y, :], d[y + 1, :] + 1.0, out=d[y, :])
    return d


def matte_distance(mask, distance_type):
    """Distance from each pixel to nearest True pixel for OLM distance modes."""
    if distance_type in (0, 2):
        return l1_distance(mask)
    if distance_type == 1:
        return distance_transform_cdt(~mask, metric="chessboard").astype(np.float32)
    if distance_type == 3:
        return distance_transform_edt(~mask).astype(np.float32)
    raise ValueError(f"distance type {distance_type} is not implemented")


def edge_blur_distance(mask, distance_type):
    """Distance transform used by Edge Blur's feather weighting."""
    if distance_type == 1:
        return distance_transform_edt(~mask).astype(np.float32)
    return matte_distance(mask, distance_type)


def interior8(mask):
    """Pixels whose 8-neighborhood stays inside the matte."""
    out = mask.copy()
    h, w = mask.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            shifted = np.zeros_like(mask)
            src_y = slice(max(0, dy), h + min(0, dy))
            dst_y = slice(max(0, -dy), h - max(0, dy))
            src_x = slice(max(0, dx), w + min(0, dx))
            dst_x = slice(max(0, -dx), w - max(0, dx))
            shifted[dst_y, dst_x] = mask[src_y, src_x]
            out &= shifted
    return out


def boundary8(mask):
    """Inside-matte pixels touching an in-frame outside pixel.

    AE's Edge Blur does not appear to treat the comp/image edge itself as an
    outside-matte neighbor. Padding with the edge value keeps solid matte areas
    at the frame boundary from becoming artificial blur seeds.
    """
    padded = np.pad(mask, 1, mode="edge")
    neighbors_inside = np.ones(mask.shape, dtype=bool)
    for dy in range(3):
        for dx in range(3):
            if dx == 1 and dy == 1:
                continue
            neighbors_inside &= padded[dy : dy + mask.shape[0], dx : dx + mask.shape[1]]
    return mask & ~neighbors_inside


def edge_blur_weight(seed, dist, amount, direction):
    """8-bit Edge Blur weighting reconstructed from FUN_1800049a0..004cf0."""
    amount = float(amount)
    if amount <= 0.0:
        return seed.astype(np.float32)
    inside = seed
    if direction == 1:
        weight = np.zeros(dist.shape, dtype=np.float32)
        hit = inside
        near = hit & (dist < amount)
        weight[hit] = 1.0
        weight[near] = (np.sin((dist[near] * (np.pi / amount)) - (np.pi / 2.0)) + 1.0) * 0.5
        return weight
    if direction == 2:
        weight = np.ones(dist.shape, dtype=np.float32)
        outside = ~inside
        far = outside & (dist >= amount)
        near = outside & ~far
        weight[far] = 0.0
        weight[near] = (np.sin((np.pi / 2.0) - (dist[near] * (np.pi / amount))) + 1.0) * 0.5
        return weight
    if direction == 3:
        weight = np.zeros(dist.shape, dtype=np.float32)
        far = inside & (dist >= amount)
        near = inside & ~far
        weight[far] = 1.0
        weight[near] = (np.sin((dist[near] * (np.pi / amount)) - (np.pi / 2.0)) + 1.0) * 0.5
        return weight
    raise ValueError(f"edge blur direction {direction} is not implemented")


def rgb_to_plugin_lab76(rgb):
    """Plug-in Color Space 3, reconstructed from FUN_180009f50 constants."""
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    x = g * 2.1455016136169434 + r * 0.6380193829536438 + b * 0.2165091633796692

    def lab_f(t):
        return np.where(
            t <= 0.008856000378727913,
            t * 7.7870001792907715 + 0.13793103396892548,
            np.power(t, 0.3333300054073334),
        )

    fx = lab_f(x)
    l = np.where(
        x <= 0.008856000378727913,
        g * 1938.031494140625 + r * 576.3229370117188 + b * 195.57272338867188,
        np.power(x, 0.3333300054073334) * 116.0 - 16.0,
    )
    a_source = r * 1.2373713254928589 + g * 1.0727508068084717 + b * 0.5412744283676147
    b_source = g * 0.35758259892463684 + r * 0.05800257995724678 + b * 2.8507096767425537
    a = (lab_f(a_source) - fx) * 500.0
    lab_b = (fx - lab_f(b_source)) * 200.0
    return np.stack([l, a, lab_b], axis=-1).astype(np.float32)


# --- renderers ------------------------------------------------------------

# 8-bit exact-match epsilon: |a-b| <= 0.5/255 means the two bytes are equal.
EPS_8BIT = np.float32(0.5 / 255.0)


def render_rgb_binary(image, cfg):
    """Original simple path; unchanged behaviour for case_0001..0004."""
    if cfg["color_space"] != 1:
        raise ValueError("only RGB color space is implemented in the simple path")
    if cfg["premultiplied"] or cfg["per_color"] or cfg["per_component"]:
        raise ValueError("premultiplied/per-color/per-component modes use the extended path")
    if cfg["edge_thin_amount"] != 0.0 or cfg["edge_blur_amount"] != 0.0:
        raise ValueError("edge thin/blur modes are not implemented")
    if cfg["enable_replace"]:
        raise ValueError("replace color is not implemented")

    arr = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    rgb = arr[..., :3].astype(np.float32) / 255.0
    delta = np.abs(rgb - cfg["key_color"])
    keyed = np.mean(delta, axis=-1) <= cfg["threshold"]
    keep = keyed if cfg["color_keep"] else ~keyed
    arr[..., :3] = np.where(keep[..., None], arr[..., :3], 0).astype(np.uint8)
    arr[..., 3] = np.where(keep, arr[..., 3], 0).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def render_extended(image, cfg):
    """Premultiplied per-color/per-component keying with Edge Thin.

    Validated on case_0005..0007. The per-component box uses the 8-bit
    exact-match epsilon for the global Threshold contribution; for those cases
    the per-component thresholds are 0 and the key is black, so only exactly
    matching bytes are keyed. Color space conversion is skipped because a black
    key is invariant under every supported color space.
    """
    if cfg["enable_replace"]:
        raise ValueError("replace color is not implemented")
    if not cfg["per_component"] and cfg["threshold"] == 0.0:
        pass
    elif not cfg["per_component"]:
        raise ValueError("extended path currently requires Per Component keying")

    arr = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    alpha = arr[..., 3:4].astype(np.float32) / 255.0
    rgb = arr[..., :3].astype(np.float32) / 255.0
    cmp = rgb * alpha if cfg["premultiplied"] else rgb
    if cfg["color_space"] == 3:
        cmp = rgb_to_plugin_lab76(cmp)

    matched = np.zeros(arr.shape[:2], dtype=bool)
    for color in cfg["colors"]:
        key_rgb = color["rgb"]
        comp_scale = np.ones(3, dtype=np.float32)
        if cfg["color_space"] == 3:
            key_rgb = rgb_to_plugin_lab76(key_rgb.reshape(1, 1, 3))[0, 0]
            comp_scale = np.array([151.30099487304688, 264.36700439453125, 295.572998046875], dtype=np.float32)
        if cfg["per_component"]:
            eps = EPS_8BIT + color["comp"] * comp_scale  # per-channel box half-width
            hit = np.all(np.abs(cmp - key_rgb) <= eps, axis=-1)
        else:
            hit = np.mean(np.abs(cmp - key_rgb), axis=-1) <= cfg["threshold"]
        matched |= hit

    amount = cfg["edge_thin_amount"]
    if amount < 0:
        # Erode the matte: drop matte pixels closer than |amount| to a non-match.
        # Empirically the AE contour removes L1 distance <= |amount|+1; the
        # residual is the diamond-corner shell AE keeps (see PORTING_BOARD).
        extra = 1 if cfg["edge_thin_distance_type"] in (0, 2) else 0
        dist = matte_distance(~matched, cfg["edge_thin_distance_type"])
        matched = matched & (dist > abs(amount) + extra)
    elif amount > 0:
        # Dilate the matte by Amount px (exact L1, validated on case_0007).
        dist = matte_distance(matched, cfg["edge_thin_distance_type"])
        matched = matched | (dist <= amount)

    keep = matched if cfg["color_keep"] else ~matched
    arr[..., :3] = np.where(keep[..., None], arr[..., :3], 0).astype(np.uint8)
    arr[..., 3] = np.where(keep, arr[..., 3], 0).astype(np.uint8)
    if cfg["edge_blur_amount"] != 0.0:
        dist = edge_blur_distance(boundary8(keep), cfg["edge_blur_distance_type"])
        weight = edge_blur_weight(keep, dist, cfg["edge_blur_amount"], cfg["edge_blur_direction"])
        source = np.asarray(image.convert("RGBA"), dtype=np.uint8)
        restore = (~keep) & (weight != 0.0)
        src_rgb = np.where(restore[..., None], source[..., :3], arr[..., :3])
        src_alpha = np.where(restore, source[..., 3], arr[..., 3])
        arr[..., :3] = np.clip((src_rgb.astype(np.float32) * weight[..., None]).astype(np.int32), 0, 255).astype(np.uint8)
        arr[..., 3] = np.clip((src_alpha.astype(np.float32) * weight).astype(np.int32), 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def render(image, cfg):
    extended = (
        cfg["premultiplied"]
        or cfg["per_color"]
        or cfg["per_component"]
        or cfg["edge_thin_amount"] != 0.0
        or cfg["edge_blur_amount"] != 0.0
    )
    if extended:
        return render_extended(image, cfg)
    return render_rgb_binary(image, cfg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    cfg = read_params(args.params)
    output = render(Image.open(args.input), cfg)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(out_path)
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
