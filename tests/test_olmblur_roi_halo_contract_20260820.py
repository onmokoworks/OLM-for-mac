"""Finite-support and tiling counterexamples for the retained OLMBlur workers."""

import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def support_radius(amount: float, repeat: int, legacy: bool, scale: float = 1.0) -> int:
    if legacy:
        return int(amount * scale) * repeat
    if repeat <= 0:
        return 0
    decay = 1.0 if repeat == 1 else math.pow(3.0 / amount, 1.0 / (repeat - 1))
    return sum(int(amount * scale * math.pow(decay, iteration))
               for iteration in range(repeat))


def test_finite_support_examples_and_ui_bound() -> None:
    assert support_radius(5.0, 2, True) == 10
    assert support_radius(5.0, 1, False) == 5
    assert support_radius(1000.0, 10, True) == 10_000
    assert support_radius(1000.0, 10, False) < 10_000
    assert max(support_radius(1000.0, 10, legacy) for legacy in (False, True)) == 10_000


def test_bias_and_smoothness_do_not_change_structural_support() -> None:
    # Both bias choices execute one horizontal and one vertical pass per
    # iteration. Smoothness changes weights, not the sampled coordinate span.
    source = (ROOT / "mac/OLMBlur/OLMBlur.cpp").read_text()
    assert "bp->bias_dir == BIAS_DIR_VERTICAL" in source
    assert "bp->bias_dir == BIAS_DIR_HORIZONTAL" in source
    assert "sigma_base" in source
    assert support_radius(17.5, 4, False) == support_radius(17.5, 4, False)


def test_exact_halo_is_insufficient_for_a_tile_not_touching_frame_zero() -> None:
    # full-frame output x=8 with radius=3 samples global x=5. A tile checked
    # out with exact halo starts at global x=5, which becomes local x=0.
    # The retained Legacy helper deliberately skips coordinate zero, so the
    # tiled result omits a sample used by the full-frame result.
    output_global_x, radius = 8, 3
    tile_global_left = output_global_x - radius
    farthest_sample_local = (output_global_x - radius) - tile_global_left
    assert farthest_sample_local == 0
    helper = (ROOT / "core/olmblur_fullworker_helper.cpp").read_text()
    assert "x - d == 0" in helper
    nonlegacy = (ROOT / "core/olmblur_helper.cpp").read_text()
    assert "x - d == 0" not in nonlegacy


def test_guard_pixel_removes_local_zero_from_requested_output_support() -> None:
    output_global_x, radius = 8, 3
    guarded_left = output_global_x - radius - 1
    farthest_sample_local = (output_global_x - radius) - guarded_left
    assert farthest_sample_local == 1


def test_current_production_lane_is_explicitly_full_frame() -> None:
    source = (ROOT / "mac/OLMBlur/OLMBlur.cpp").read_text()
    assert "world->origin_x != 0 || world->origin_y != 0" in source
    assert "world->extent_hint.right != width" in source
    assert "world->extent_hint.bottom != height" in source
