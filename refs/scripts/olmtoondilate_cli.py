#!/usr/bin/env python3
"""AE-free OLMToonDilate CLI.

OLM Toon Dilate grows opaque regions into the transparent background.
Reconstructed from decomp/OLMToonDilate.aex.c.txt (FUN_1801a6150):

  - seed = (alpha == 255)            # only fully-opaque pixels are sources
  - R_eff = ceil(SearchRadius * img_width / comp_width)   # downsample scaling
  - forward/backward raster passes over an 8-connected chamfer distance buffer
  - each relaxed pixel immediately copies the winning neighbour's current RGBA
  - remaining semi-alpha pixels are premultiplied on output

The immediate neighbour-copy rule is important: it is not an Euclidean nearest
source lookup, and case_0003 exposes the difference.

NOTE: ADBE Force CPU GPU=1 is a reference property, not a render-path
indicator. Compare CUDA vs Software renders using a separately recorded
project_gpu_accel_type field. This CPU port matches the decomp-derived model
but leaves a small boundary residual against the current references (~0.37% of
pixels on case_0001) — see notes/PORTING_BOARD.md.

Requires numpy, Pillow, and scipy (distance transforms).
"""

import argparse
import json
import math
from pathlib import Path

from PIL import Image
import numpy as np


def effect_params(payload):
    params = payload.get("params", payload)
    if isinstance(params, dict) and "effects" in params:
        for effect in params.get("effects", []):
            if effect.get("name") == "OLM Toon Dilate" or effect.get("match_name") == "OLM Toon Dilate":
                return {p.get("name"): p.get("value") for p in effect.get("params", [])}
    if isinstance(params, dict):
        return params
    return {}


def read_search_radius(params_path):
    with Path(params_path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    params = effect_params(payload)
    value = params.get("Search Radius", 0)
    comp = None
    # Allow an injected comp width (mirrors OLMBlur's comp propagation).
    root = payload if isinstance(payload, dict) else {}
    if isinstance(root.get("comp"), dict):
        comp = root["comp"].get("width")
    return float(value or 0.0), comp


def render(image, search_radius, comp_width):
    arr = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    h, w = arr.shape[:2]
    seed = arr[..., 3] == 255
    if not seed.any() or search_radius <= 0:
        return Image.fromarray(arr, "RGBA")

    scale = (w / comp_width) if comp_width else 1.0
    r_eff = math.ceil(search_radius * scale)

    inf = np.iinfo(np.uint32).max
    dist = np.full((h, w), inf, dtype=np.uint32)
    dist[seed] = 0

    def relax(x, y, coords):
        if dist[y, x] == 0:
            return
        best = inf
        best_xy = None
        for nx, ny in coords:
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            d = int(dist[ny, nx])
            if d < best:
                best = d
                best_xy = (nx, ny)
        if best_xy is None:
            return
        candidate = best + 1
        if candidate >= int(dist[y, x]):
            return
        dist[y, x] = candidate
        if candidate <= r_eff:
            bx, by = best_xy
            arr[y, x] = arr[by, bx]

    for y in range(h):
        for x in range(w):
            relax(x, y, ((x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1)))
    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            relax(x, y, ((x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1)))

    alpha = arr[..., 3].astype(np.uint16)
    semi = (alpha != 0) & (alpha != 255)
    rgb = arr[..., :3].astype(np.uint16)
    rgb[semi] = (rgb[semi] * alpha[semi, None] + 127) // 255
    arr[..., :3] = rgb.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--comp-width", type=float, default=None,
                        help="composition width in px for downsample scaling (default: read from params, else 1920)")
    args = parser.parse_args()

    search_radius, comp_from_params = read_search_radius(args.params)
    comp_width = args.comp_width or comp_from_params or 1920.0

    out = render(Image.open(args.input), search_radius, comp_width)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    print(f"wrote: {out_path} (search_radius={search_radius} comp_width={comp_width})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
