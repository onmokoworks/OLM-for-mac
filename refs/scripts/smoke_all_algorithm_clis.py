#!/usr/bin/env python3
"""Run all current AE-free algorithm smoke tests.

Some ports are intentionally still red measurement scaffolds. For those, a
nonzero exit with DIFF output is treated as expected observation, while missing
CLIs/references or command failures without DIFF still fail this aggregate.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Smoke:
    name: str
    command: list[str]
    expected: str = "green"  # green | red-measurement


def run(root: Path, smoke: Smoke) -> tuple[bool, str]:
    print(f"\n=== {smoke.name} ({smoke.expected}) ===", flush=True)
    proc = subprocess.run(
        smoke.command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = proc.stdout or ""
    print(output, end="" if output.endswith("\n") else "\n")

    if smoke.expected == "green":
        if proc.returncode == 0:
            return True, "OK"
        return False, f"FAILED exit={proc.returncode}"

    if proc.returncode == 0:
        return True, "OK-now-green"
    if "[DIFF]" in output:
        return True, "DIFF-observed"
    return False, f"FAILED exit={proc.returncode} without DIFF"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("quick", "full"),
        default="full",
        help="quick runs only green gates; full also runs expected-red diagnostic probes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    smokes = [
        Smoke("harness", [py, "refs/scripts/smoke_algorithm_harness.py"]),
        Smoke("ColorKeep synthetic", [py, "refs/scripts/smoke_colorkeep_cli.py"]),
        Smoke("OLMBlur build", ["refs/scripts/build_olmblur_cli.sh"]),
        Smoke("OLMBlur", [py, "refs/scripts/smoke_olmblur_cli.py"]),
        Smoke("OLMColorKey RGB", [py, "refs/scripts/smoke_olmcolorkey_cli.py"]),
        Smoke("OLMColorKey Edge Thin", [py, "refs/scripts/smoke_olmcolorkey_extended_cli.py"]),
        Smoke("OLMColorKey Edge Blur", [py, "refs/scripts/smoke_olmcolorkey_edgeblur_cli.py"]),
        Smoke("OLMColorKey C++", [py, "refs/scripts/smoke_olmcolorkey_cpp_cli.py"]),
        Smoke("OLMColorKey C++ Edge Blur", [py, "refs/scripts/smoke_olmcolorkey_cpp_edgeblur_cli.py"]),
        Smoke("OLMColorKey Rust", [py, "refs/scripts/smoke_olmcolorkey_rust_cli.py"]),
        Smoke("OLMToonDilate", [py, "refs/scripts/smoke_olmtoondilate_cli.py"]),
        Smoke("OLMToonDilate C++ build", ["refs/scripts/build_olmtoondilate_cli.sh"]),
        Smoke("OLMToonDilate C++", [py, "refs/scripts/smoke_olmtoondilate_cpp_cli.py"]),
        Smoke("OLMDistanceGradation", [py, "refs/scripts/smoke_olmdistancegradation_cli.py"]),
        Smoke("OLMSmoother build", ["refs/scripts/build_olmsmoother_cli.sh"]),
        Smoke("OLMSmoother", [py, "refs/scripts/smoke_olmsmoother_cli.py"], "red-measurement"),
        Smoke("OLMSmoother2 build", ["refs/scripts/build_olmsmoother2_cli.sh"]),
        Smoke("OLMSmoother2 key paths", [py, "refs/scripts/smoke_olmsmoother2_keypaths_cli.py"]),
        Smoke("OLMSmoother2 Gamma Colors", [py, "refs/scripts/smoke_olmsmoother2_gamma_cli.py"]),
        Smoke("OLMSmoother2", [py, "refs/scripts/smoke_olmsmoother2_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur tiny Rotation", [py, "refs/scripts/smoke_olmradialblur_tiny_rotation_cli.py"]),
        Smoke("OLMRadialBlur C++ tiny Rotation", [py, "refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py"]),
        Smoke("OLMRadialBlur Rotation", [py, "refs/scripts/smoke_olmradialblur_rotation_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Rotation", [py, "refs/scripts/smoke_olmradialblur_cpp_rotation_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur Zoom", [py, "refs/scripts/smoke_olmradialblur_zoom_cli.py"]),
        Smoke("OLMRadialBlur Zoom Offset", [py, "refs/scripts/smoke_olmradialblur_zoom_offset_cli.py"]),
        Smoke("OLMRadialBlur C++ Zoom Offset", [py, "refs/scripts/smoke_olmradialblur_cpp_cli.py"]),
        Smoke("OLMRadialBlur C++ Zoom", [py, "refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py"]),
        Smoke("OLMRadialBlur Inner", [py, "refs/scripts/smoke_olmradialblur_inner_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Alpha Mode probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_alpha_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Source Scatter Prepass probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_source_scatter_prepass_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Prepass Mode probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_prepass_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Scatter RGB probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_scatter_rgb_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Source Scale probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_source_scale_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Dynamic Offset probe", [py, "refs/scripts/smoke_olmradialblur_cpp_dynamic_offset_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Final Norm probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_final_norm_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Seed Alpha probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_seed_alpha_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Span Scale probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_span_scale_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Wrap probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_wrap_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur", [py, "refs/scripts/smoke_olmdirectionalblur_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur Back probe", [py, "refs/scripts/smoke_olmdirectionalblur_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Back probe", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Direct Map", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_direct_map_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Full Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Pad Full Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_pad_full_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Prepass Full Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_prepass_full_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Half-height", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_halfheight_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Trunc Output", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_trunc_output_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Truncated Span", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_truncated_span_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Row Init probe", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_row_init_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Pad", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_pad_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Alpha Sum", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_alpha_sum_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Preserve Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_preserve_alpha_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Front Strength Preserve Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_front_strength_preserve_alpha_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Rowdriver Prepass", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_rowdriver_prepass_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Gather", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_gather_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Map", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Map Alpha Coeff", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_alpha_coeff_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Map Preserve Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_preserve_alpha_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira", [py, "refs/scripts/smoke_olmkirakira_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++", [py, "refs/scripts/smoke_olmkirakira_cpp_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira Brightness probe", [py, "refs/scripts/smoke_olmkirakira_brightness_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira Rotate probe", [py, "refs/scripts/smoke_olmkirakira_rotate_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Rotate Filter probe", [py, "refs/scripts/smoke_olmkirakira_cpp_rotate_filter_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Rotate Border probe", [py, "refs/scripts/smoke_olmkirakira_cpp_rotate_border_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Rotate Size probe", [py, "refs/scripts/smoke_olmkirakira_cpp_rotate_size_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Warp Mode probe", [py, "refs/scripts/smoke_olmkirakira_cpp_warp_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ AEX getRotationMatrix2D probe", [py, "refs/scripts/smoke_olmkirakira_cpp_aex_getrot_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Direct Rotate-Back probe", [py, "refs/scripts/smoke_olmkirakira_cpp_direct_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Crop Mode probe", [py, "refs/scripts/smoke_olmkirakira_cpp_crop_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Glow Normalize probe", [py, "refs/scripts/smoke_olmkirakira_cpp_glow_normalize_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Aggregation probe", [py, "refs/scripts/smoke_olmkirakira_cpp_aggregation_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Anchor probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_anchor_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Normalize probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_normalize_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Output Depth probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_output_depth_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Size probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_size_probe_cli.py"], "red-measurement"),
    ]
    if args.profile == "quick":
        smokes = [smoke for smoke in smokes if smoke.expected == "green"]

    results: list[tuple[str, bool, str]] = []
    print(f"running smoke profile: {args.profile} ({len(smokes)} checks)", flush=True)
    for smoke in smokes:
        ok, status = run(root, smoke)
        results.append((smoke.name, ok, status))

    print("\n=== summary ===")
    for name, ok, status in results:
        mark = "OK" if ok else "FAIL"
        print(f"{mark:4} {name}: {status}")

    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
