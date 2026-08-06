#!/usr/bin/env python3
"""Focused AE-free gate for the bounded Mac Merge Mode 2 integration.

The numeric oracle is independently binary-grounded in the checked-in AEX.
This test also fail-closes on the production source shape.  It proves the
no-ramp inner aggregator, outer scalar compose, and typed writer boundary; it
does not prove ray production, host loading, or AE output.
"""

from __future__ import annotations

import importlib.util
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
CORE = ROOT / "core/kirakira_merge2.h"
INNER = ROOT / "tools/emulation/olmkirakira_merge2_float_oracle_20260728.py"
OUTER = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    inner = load(INNER, "kirakira_merge2_inner")
    outer = load(OUTER, "kirakira_merge2_outer")

    anchors = {
        "distinct_mode2_dispatch": "if (info.merge_mode == 2)" in source,
        "five_mode2_layers": source.count("AddColoredMerge2(glow,") == 5,
        "five_layer_order": source.index("AddColoredMerge2(glow, vertical")
        < source.index("AddColoredMerge2(glow, horizontal")
        < source.index("AddColoredMerge2(glow, diagonal,")
        < source.index("AddColoredMerge2(glow, highlight")
        < source.index("AddColoredMerge2(glow, diagonal2"),
        "strict_skip_boundary": "if (amount[i] <= 0.001f)" in core,
        "raw_ray_alpha": "glow[i].a += amount[i];" in core,
        "post_five_layer_clamp": all(f"g.{c} = Clamp01(g.{c});" in source for c in "rgba"),
        "outer_mode2_helper": "out = ComposeMerge2Pixel(" in source,
        "unscaled_alpha_zero_test": "raw_alpha_sum = glow.a + source.a;" in core,
        "source_then_glow_weighting": "red = source_r + glow_r;" in core,
        "mode2_typed_truncate": "? PixelTraits<PixelT>::WriteAexTruncate(out)" in source,
        "pf8_scale": "Clamp01(p.a) * 255.0f" in source,
        "pf16_scale": "truncate_merge2_channel(p.a, 32768.0f)" in source,
    }
    assert all(anchors.values()), anchors

    rays = (0.2, 0.0, 0.003, 0.7, 0.4)
    colors = (
        (0.0, 0.5, 0.75),
        (1.0, 0.0, 0.0),
        (0.25, 0.125, 0.5),
        (0.75, 0.25, 0.125),
        (0.1, 0.2, 0.3),
    )
    glow = inner.aggregate_pixel(rays, colors, skip_threshold=0.001)
    assert struct.pack("<4f", *glow).hex() == "0000803f" * 4

    source_pixel = (0.2, 0.4, 0.7, 0.35)
    composed = outer.compose_pixel(
        glow, source_pixel, glow_opacity=0.75, source_opacity=0.5, merge_mode=2
    )
    assert struct.pack("<4f", *composed).hex() == "c3f5483f85eb513f295c5f3fcdcc6c3f"
    assert outer.stage_typed_writer(composed, depth="PF8").hex() == "ebc8d1de"
    assert outer.stage_typed_writer(composed, depth="PF16").hex() == "66767a64f568ae6f"
    assert outer.stage_typed_writer(composed, depth="PF32").hex() == "cdcc6c3fc3f5483f85eb513f295c5f3f"

    zero = outer.compose_pixel(
        (0.5, 0.5, 0.5, 0.0), (0.5, 0.5, 0.5, 0.0),
        glow_opacity=1.0, source_opacity=1.0, merge_mode=2,
    )
    assert zero == (0.0, 0.0, 0.0, 0.0)
    print("PASS_OLMKIRAKIRA_MERGE2_MAC_PRODUCTION_BOUNDARY_20260805")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
