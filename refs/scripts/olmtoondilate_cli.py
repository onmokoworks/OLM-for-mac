#!/usr/bin/env python3
"""AE-free OLMToonDilate CLI.

OLM Toon Dilate grows opaque regions into the transparent background: every
non-opaque pixel within Search Radius (in render pixels) of a fully-opaque
pixel is filled with the colour of the nearest opaque pixel. Reconstructed from
decomp/OLMToonDilate.aex.c.txt (FUN_1801a6150):

  - seed = (alpha == 255)            # only fully-opaque pixels are sources
  - R_eff = ceil(SearchRadius * img_width / comp_width)   # downsample scaling
  - mask  = (~seed) & (chebyshev_distance_to_seed <= R_eff)   # 8-conn chamfer
  - fill colour = nearest opaque pixel's RGBA

The decomp uses an 8-connected (Chebyshev / chessboard) chamfer for the mask;
colour rides the chamfer propagation, which coincides with the Euclidean-nearest
opaque pixel in practice (verified exact on the reference's filled pixels).

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

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_cdt, distance_transform_edt


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

    # Mask: 8-connected (Chebyshev) chamfer distance from each pixel to the
    # nearest opaque pixel; fill where 0 < dist <= R_eff.
    cheb = distance_transform_cdt(~seed, metric="chessboard")
    fill = (~seed) & (cheb <= r_eff)

    # Colour: nearest opaque pixel (Euclidean feature transform).
    _, (iy, ix) = distance_transform_edt(~seed, return_indices=True)
    arr[fill] = arr[iy[fill], ix[fill]]
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
