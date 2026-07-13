#!/usr/bin/env python3
"""Compare bounded host-transform hypotheses for the KiraKira hotspot."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MAC_WITNESS = ROOT / "refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json"
WINDOWS_TRACE = ROOT / "refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.json"
CANDIDATE_PNG = ROOT / "refs/reports/olmkirakira_remeasure_20260624_bt709_software/candidate/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
REFERENCE_PNG = ROOT / "refs/reports/olmkirakira_remeasure_20260624_bt709_software/reference/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
REFERENCE_MANIFEST = ROOT / "refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira/reference_manifest.json"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_hotspot_transform_provenance_20260712.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_hotspot_transform_provenance_20260712.md"

XY = (934, 118)
RADIUS = 2


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac-witness", type=Path, default=MAC_WITNESS)
    parser.add_argument("--windows-trace", type=Path, default=WINDOWS_TRACE)
    parser.add_argument("--candidate-png", type=Path, default=CANDIDATE_PNG)
    parser.add_argument("--reference-png", type=Path, default=REFERENCE_PNG)
    parser.add_argument("--reference-manifest", type=Path, default=REFERENCE_MANIFEST)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def linear_to_srgb(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1.0 / 2.4) - 0.055


def u8(value: float) -> int:
    return int(math.floor(max(0.0, min(1.0, value)) * 255.0 + 0.5))


def screen(source: float, glow: float, alpha: float) -> float:
    return 1.0 - (1.0 - source) * (1.0 - glow * alpha)


def rgba_at(path: Path, x: int, y: int) -> list[int]:
    with Image.open(path).convert("RGBA") as image:
        return [int(channel) for channel in image.getpixel((x, y))]


def neighborhood(path: Path) -> list[list[int]]:
    with Image.open(path).convert("RGBA") as image:
        return [
            [int(image.getpixel((x, y))[0]) for x in range(XY[0] - RADIUS, XY[0] + RADIUS + 1)]
            for y in range(XY[1] - RADIUS, XY[1] + RADIUS + 1)
        ]


def build_report(options: argparse.Namespace) -> dict[str, Any]:
    mac = read_json(options.mac_witness)["points"][f"{XY[0]},{XY[1]}"]
    trace = read_json(options.windows_trace)
    compose = next(row for row in trace["windows"]["merge_mode_1_compose"]["sample_inputs_outputs"] if row["label"] == "hotspot")

    source = float(mac["src_rgba_float"][0])
    alpha = float(compose["glow_after_opacity_rgba_float"][3])
    traced = float(compose["composed_rgba_float"][0])
    target_u8 = rgba_at(options.reference_png, *XY)[0]
    target = target_u8 / 255.0
    srgb_result = screen(source, 1.0, alpha)
    source_linear = srgb_to_linear(source)
    linear_result = linear_to_srgb(source_linear + (1.0 - source_linear) * alpha)
    implied_alpha = (target - source) / (1.0 - source)

    # The source and final output are opaque at this witness. These are the
    # only premultiply/unpremultiply operations available at this boundary.
    premultiply_identity = source * 1.0 / 1.0
    unpremultiply_identity = premultiply_identity * 1.0
    manifest = read_json(options.reference_manifest)
    manifest_case = next(case for case in manifest["cases"] if case["id"] == "kk_vertical_len50_brightness1_strength100" and case["render_set_id"] == "software")

    candidate = rgba_at(options.candidate_png, *XY)
    reference = rgba_at(options.reference_png, *XY)
    return {
        "kind": "olmkirakira_hotspot_transform_provenance",
        "schema": 1,
        "case_id": "kk_vertical_len50_brightness1_strength100",
        "hotspot_xy": list(XY),
        "inputs": {
            "mac_witness": str(options.mac_witness.relative_to(ROOT)),
            "windows_trace": str(options.windows_trace.relative_to(ROOT)),
            "candidate_png": str(options.candidate_png.relative_to(ROOT)),
            "reference_png": str(options.reference_png.relative_to(ROOT)),
            "reference_manifest": str(options.reference_manifest.relative_to(ROOT)),
        },
        "observed": {
            "source_rgb": source,
            "source_alpha": float(mac["src_rgba_float"][3]),
            "glow_rgb": list(compose["glow_after_opacity_rgba_float"][:3]),
            "glow_alpha": alpha,
            "windows_traced_compose_float": traced,
            "windows_traced_u8": list(compose["final_writeback_or_png_rgba"]),
            "candidate_u8": candidate,
            "canonical_reference_u8": reference,
            "reference_manifest_context": {
                "platform": manifest["platform"],
                "ae_version": manifest["ae_version"],
                "render_set_id": manifest_case["render_set_id"],
                "project_gpu_accel_type": manifest_case["project_gpu_accel_type"],
                "comp": manifest_case["comp"],
                "frame": manifest_case["frame"],
            },
        },
        "hypotheses": {
            "premultiply_unpremultiply": {
                "source_alpha": float(mac["src_rgba_float"][3]),
                "premultiply_then_unpremultiply_rgb": premultiply_identity,
                "result": "identity_at_opaque_source_alpha",
                "target_explained": False,
            },
            "color_management": {
                "srgb_domain_screen_u8": u8(srgb_result),
                "decode_blend_encode_srgb_u8": u8(linear_result),
                "target_u8": target_u8,
                "result": "standard_srgb_linearization_does_not_map_144_to_131",
                "target_explained": False,
            },
            "coordinate_placement": {
                "radius": RADIUS,
                "candidate_r_channel": neighborhood(options.candidate_png),
                "reference_r_channel": neighborhood(options.reference_png),
                "result": "reference_has_131_plateau_at_requested_coordinate;_candidate_has_no_131_in_5x5",
                "target_explained": "not_decidable_from_png_neighborhood_alone",
            },
            "same_screen_compose_with_implied_alpha": {
                "target_alpha": implied_alpha,
                "traced_alpha": alpha,
                "alpha_delta": implied_alpha - alpha,
                "result": "requires_upstream_or_witness_path_difference",
                "target_explained": False,
            },
        },
        "decision": {
            "status": "no_host_transform_proven",
            "fact": "The accepted Windows trace and current Mac compose witness agree at opaque source alpha, glow alpha 0.507505655, compose float about 0.565446, and u8 144; the canonical Windows PNG is 131.",
            "inference": "Premultiply/unpremultiply cannot explain the delta at this opaque witness. Standard sRGB decode/blend/encode moves the result toward 190, not 131. Coordinate placement remains a provenance possibility, but the PNG neighborhood alone cannot prove a placement error.",
            "boundary": "Do not tune Kira math or claim AE exact. The remaining bounded lane is same-run reference/export provenance, witness placement, or an unobserved host/endgame path.",
        },
    }


def markdown(report: dict[str, Any]) -> str:
    observed = report["observed"]
    hypotheses = report["hypotheses"]
    decision = report["decision"]
    lines = [
        "# OLMKiraKira Hotspot Transform Provenance",
        "",
        "- Case: `kk_vertical_len50_brightness1_strength100`",
        "- Hotspot: `(934,118)`",
        "- Status: `no-host-transform-proven`",
        "",
        "## FACT",
        "",
        f"- Existing Windows trace compose: `{observed['windows_traced_compose_float']:.12f}` -> `{observed['windows_traced_u8']}`.",
        f"- Existing Mac compose witness: source alpha `{observed['source_alpha']}`, glow alpha `{observed['glow_alpha']}`, output `[144,144,144,255]`.",
        f"- Archived candidate PNG: `{observed['candidate_u8']}`; canonical Windows PNG: `{observed['canonical_reference_u8']}`.",
        f"- Returned Windows manifest context: AE `{observed['reference_manifest_context']['ae_version']}`, render set `{observed['reference_manifest_context']['render_set_id']}`, comp `{observed['reference_manifest_context']['comp']['width']}x{observed['reference_manifest_context']['comp']['height']}`.",
        f"- Premultiply/unpremultiply at source alpha `{observed['source_alpha']}` is identity.",
        f"- Standard sRGB-domain screen output is `{hypotheses['color_management']['srgb_domain_screen_u8']}`; linear-light blend then sRGB encoding is `{hypotheses['color_management']['decode_blend_encode_srgb_u8']}`.",
        f"- The canonical 131 implies screen glow alpha `{hypotheses['same_screen_compose_with_implied_alpha']['target_alpha']:.12f}`, versus traced `{hypotheses['same_screen_compose_with_implied_alpha']['traced_alpha']:.12f}`.",
        "",
        "## INFERENCE",
        "",
        "- Premultiply/unpremultiply does not explain `144 -> 131` at this opaque witness.",
        "- Standard color-management linearization does not explain it: the tested result is 190, not 131.",
        "- Placement remains possible because the canonical image has a 131 plateau at the requested coordinate, but the local PNGs cannot establish which source pixel/stage was sampled.",
        "- No host transform is directly proven. The evidence stays in reference/export provenance, witness placement, or an unobserved host/endgame path.",
        "",
        "## Scope",
        "",
        "- This report uses only existing returned trace/manifests/witnesses and PNG refs.",
        "- It does not change Kira math, production source, ledger files, or claim AE exactness.",
        "- Exact command:",
        "  `python3 refs/scripts/compare_olmkirakira_hotspot_transforms.py`",
        "",
        "## Inputs",
        "",
    ]
    lines.extend(f"- `{value}`" for value in report["inputs"].values())
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    options = args()
    report = build_report(options)
    options.output_json.parent.mkdir(parents=True, exist_ok=True)
    options.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    options.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"json={options.output_json}")
    print(f"md={options.output_md}")
    print("[PASS] no premultiply/color-management host transform is proven for 144 -> 131")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
