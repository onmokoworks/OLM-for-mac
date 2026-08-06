#!/usr/bin/env python3
"""Focused source contract for KiraKira's binary-grounded resize path."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"


def test_approximated_input_contract():
    source = SOURCE.read_text()
    start = source.index("static PF_Err RenderTyped")
    body = source[start:source.index("static PF_Err RenderWorld", start)]

    assert "info.approximated_input && render_scale_ratio > 0.5" in body
    assert "std::max<A_long>(1, w / 2)" in body
    assert "std::max<A_long>(1, h / 2)" in body
    assert "render_scale_ratio * 0.5" in body
    assert "(A_long)((double)value * length_scale)" in body
    assert "ResizeNearestRGBA(source_pixels, w, h, work_w, work_h)" in body
    assert "ResizeNearestRGBA(composed, work_width, work_height, w, h)" in body
    assert "const FloatRGBA &src = source_pixels[idx]" in body

    # The integer source-coordinate rule is the explicit-dsize INTER_NEAREST
    # mapping used by the production helper for both resize directions.
    src_width, src_height, dst_width, dst_height = 5, 3, 2, 2
    coords = [
        (min(src_height - 1, y * src_height // dst_height),
         min(src_width - 1, x * src_width // dst_width))
        for y in range(dst_height)
        for x in range(dst_width)
    ]
    assert coords == [(0, 0), (0, 2), (1, 0), (1, 2)]


if __name__ == "__main__":
    test_approximated_input_contract()
    print("PASS OLMKiraKira Approximated Input resize contract")
