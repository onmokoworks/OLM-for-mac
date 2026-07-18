#!/usr/bin/env python3
"""Fail-closed audit of the bounded Smoother2 case_0012 actual-AEX runner.

This audit deliberately separates execution of AEX instructions from proof
that the surrounding state is the state of the accepted Windows AE run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_olmsmoother2_case0012_natural_post_f130_20260718.py"
RESULT = ROOT / "refs/conformance/olmsmoother2_case0012_natural_post_f130_20260718.json"
WINDOWS_LIVE = ROOT / (
    "refs/conformance/fixtures/olmsmoother2_corrected_witness_20260717/"
    "RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.json"
)
PARAMS = ROOT / (
    "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params/"
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex.json"
)
WINDOWS_ROOT = ROOT / (
    "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
    "OLMSmootherv2"
)
SOURCE = WINDOWS_ROOT / "input\\current_olm_cells.png"
WINDOWS_BEFORE = WINDOWS_ROOT / (
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png"
)
WINDOWS_OUTPUT = WINDOWS_ROOT / (
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex.png"
)

CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
EXPECTED_DESCRIPTOR = [92, 841, 1, 92, 842, 2]
EXPECTED_CLASS = {
    "center": [255, 255, 0, 255],
    "previous": [255, 0, 0, 0],
    "left": [0, 255, 0, 255],
}
EXPECTED_WINDOWS_PIXEL = [233, 233, 233, 237]
REQUIRED_BOUNDARIES = [
    "parameter_context",
    "crop_translation",
    "host_input",
    "class_plane",
    "dispatcher",
    "second_vertex",
    "cce0_config",
    "writer",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pf8_premultiply(value: int, alpha: int) -> int:
    return (value * alpha + 127) // 255


def live_events(document: dict[str, Any]) -> dict[str, dict[str, str]]:
    events: dict[str, dict[str, str]] = {}
    for item in document["events"]:
        name = item["event"]
        if name in {"e170_entry", "e170_return", "e3a0_return", "f270_return"}:
            require(name not in events, f"duplicate accepted Windows event: {name}")
            events[name] = item["fields"]
    return events


def parse_csv_ints(value: str) -> list[int]:
    return [int(part) for part in value.split(",")]


def u32_to_f32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def verify_crop_host_adapter(result: dict[str, Any]) -> dict[str, Any]:
    origin_x, origin_y = result["crop"]["host_origin"]
    width, height = result["crop"]["size"]
    mismatches = []
    with Image.open(SOURCE) as source_image, Image.open(WINDOWS_BEFORE) as before_image:
        source = source_image.convert("RGBA")
        before = before_image.convert("RGBA")
        for y in range(origin_y, origin_y + height):
            for x in range(origin_x, origin_x + width):
                red, green, blue, alpha = source.getpixel((x, y))
                expected = (
                    pf8_premultiply(red, alpha),
                    pf8_premultiply(green, alpha),
                    pf8_premultiply(blue, alpha),
                    alpha,
                )
                actual = before.getpixel((x, y))
                if expected != actual:
                    mismatches.append({"xy": [x, y], "expected": list(expected), "actual": list(actual)})
    require(not mismatches, f"PF8 host adapter differs within crop: {mismatches[:3]}")
    return {
        "pixels_checked": width * height,
        "mismatch_count": len(mismatches),
        "rule": "(channel * alpha + 127) // 255",
        "scope": "exported before-effects PF8 bytes over the bounded 16x16 crop",
    }


def rerun_bounded() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        output_json = Path(temporary) / "result.json"
        output_md = Path(temporary) / "result.md"
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--output-json", str(output_json), "--output-md", str(output_md)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return {
            "report": json.loads(output_json.read_text(encoding="utf-8")),
            "stdout": completed.stdout.strip().splitlines(),
        }


def inventory_entry(
    classification: str,
    aex_instructions_execute: bool,
    windows_live_equivalence_proved: bool,
    grounded: list[str],
    assumptions: list[str],
    missing_proof: list[str],
) -> dict[str, Any]:
    return {
        "classification": classification,
        "aex_instructions_execute": aex_instructions_execute,
        "windows_live_equivalence_proved": windows_live_equivalence_proved,
        "grounded": grounded,
        "synthetic_or_manual_assumptions": assumptions,
        "missing_proof": missing_proof,
    }


def audit() -> dict[str, Any]:
    for path in [RUNNER, RESULT, WINDOWS_LIVE, PARAMS, SOURCE, WINDOWS_BEFORE, WINDOWS_OUTPUT]:
        require(path.is_file(), f"required input missing: {path.relative_to(ROOT)}")

    runner_source = RUNNER.read_text(encoding="utf-8")
    for marker in [
        "CROP_ORIGIN = (84, 833)",
        "CROP_SIZE = 16",
        "translate_descriptor",
        "loader.write_bytes(render_config + 0x40, b\"\\x03\")",
        "loader.call_function(\n        FCCE0",
    ]:
        require(marker in runner_source, f"runner structure changed without audit update: {marker}")
    for writer_marker in ["FUN_1800036e0", "0x1800036e0", "FUN_1800035", "0x18000350b"]:
        require(writer_marker not in runner_source, f"runner now reaches or names a writer boundary: {writer_marker}")

    stored = json.loads(RESULT.read_text(encoding="utf-8"))
    rerun = rerun_bounded()
    bounded = rerun["report"]
    require(bounded == stored, "bounded rerun differs from checked-in result")
    require(bounded["binary"]["sha256"] == EXPECTED_AEX_SHA256, "bounded AEX identity drift")
    require(bounded["events"]["descriptor"]["host_translated"] == EXPECTED_DESCRIPTOR, "bounded descriptor drift")
    require(bounded["class_witness"]["center"] == EXPECTED_CLASS["center"], "bounded center class drift")
    require(bounded["class_witness"]["previous"] == EXPECTED_CLASS["previous"], "bounded previous class drift")

    live = json.loads(WINDOWS_LIVE.read_text(encoding="utf-8"))
    require(live["status"] == "answered", "accepted Windows fixture is not answered")
    require(live["run"]["aex_sha256"] == EXPECTED_AEX_SHA256, "accepted Windows AEX identity drift")
    require(live["run"]["renderer"] == "Software", "accepted Windows renderer drift")
    require(live["run"]["project_bits_per_channel"] == 8, "accepted Windows bpc drift")
    events = live_events(live)
    require(parse_csv_ints(events["e170_entry"]["descriptor"]) == EXPECTED_DESCRIPTOR, "accepted descriptor drift")
    require(int(events["e170_return"]["e170_c"]) == 7, "accepted e170 result drift")
    require(parse_csv_ints(events["e170_entry"]["center_class_bytes"]) == EXPECTED_CLASS["center"], "accepted center class drift")
    require(parse_csv_ints(events["e170_entry"]["prev_class_bytes"]) == EXPECTED_CLASS["previous"], "accepted previous class drift")
    require(parse_csv_ints(events["e170_entry"]["left_class_bytes"]) == EXPECTED_CLASS["left"], "accepted left class drift")
    require(int(events["f270_return"]["vertex_count"]) == 1, "accepted first-leaf count drift")

    accepted_first_rgba_u32 = [int(word, 16) for word in events["f270_return"]["first_vertex_rgba_words"].split(",")]
    accepted_first_weight_u32 = int(events["f270_return"]["weight_word"], 16)
    bounded_first = bounded["events"]["post_f130_pre_boost"]["vertices"][0]
    bounded_first_rgba_u32 = bounded_first["rgba_u32"]
    bounded_first_weight_u32 = bounded_first["weight_u32"]
    first_vertex_comparison = {
        "accepted_windows_stage": "f270_return",
        "bounded_stage": "post_dispatch_polygon_first_vertex",
        "semantic_stage_equal": False,
        "numeric_comparison_allowed": False,
        "windows_rgba_u32": accepted_first_rgba_u32,
        "bounded_rgba_u32": bounded_first_rgba_u32,
        "rgba_u32_delta_bounded_minus_windows": [
            bounded - windows for bounded, windows in zip(bounded_first_rgba_u32, accepted_first_rgba_u32)
        ],
        "rgba_bitwise_equal": bounded_first_rgba_u32 == accepted_first_rgba_u32,
        "windows_weight_u32": accepted_first_weight_u32,
        "bounded_weight_u32": bounded_first_weight_u32,
        "windows_weight_f32": u32_to_f32(accepted_first_weight_u32),
        "bounded_weight_f32": u32_to_f32(bounded_first_weight_u32),
        "weight_u32_delta_bounded_minus_windows": bounded_first_weight_u32 - accepted_first_weight_u32,
        "weight_bitwise_equal_diagnostic_only": bounded_first_weight_u32 == accepted_first_weight_u32,
    }
    require(first_vertex_comparison["rgba_u32_delta_bounded_minus_windows"] == [-3, -3, -3, 0], "first vertex ULP boundary drift")
    require(bounded_first_weight_u32 == int("3e25bedb", 16), "bounded post-dispatch weight drift")

    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    require(params["case_id"] == CASE_ID, "parameter fixture case drift")
    require(params["metadata"]["project_gpu_accel_type"]["current_name"] == "SOFTWARE", "parameter renderer drift")
    require(params["comp"]["width"] == 1920 and params["comp"]["height"] == 1080, "full-frame dimensions drift")
    crop_adapter = verify_crop_host_adapter(bounded)

    with Image.open(WINDOWS_OUTPUT) as image:
        windows_pixel = list(image.convert("RGBA").getpixel((92, 841)))
    require(windows_pixel == EXPECTED_WINDOWS_PIXEL, "Windows live output pixel drift")

    cce0_rgba = bounded["cce0_output"]["rgba"]
    require(len(cce0_rgba) == 4 and all(math.isfinite(value) for value in cce0_rgba), "invalid bounded cce0 output")

    inventory = {
        "parameter_context": inventory_entry(
            "fixture-grounded/manual-runtime-struct",
            False,
            False,
            [
                "The manifest pins the case id, 1920x1080 comp, Software renderer, and visible AE parameter values.",
                "The bounded runner rejects drift in the principal visible parameters.",
            ],
            [
                "The runner manually writes selected fields at render_config +0x00/+0x20/+0x28/+0x30/+0x38/+0x40.",
                "Unwritten config bytes are zeroed and the sixth cce0 argument is manually set to zero.",
                "The retained Windows weight is captured at f270 return while the bounded snapshot is after dispatcher normalization; those weights are not a same-stage comparison.",
            ],
            ["Same-run Windows dump of the complete cce0 config and sixth argument at the accepted pixel."],
        ),
        "crop_translation": inventory_entry(
            "synthetic-coordinate-translation",
            False,
            False,
            ["Local descriptor plus the hard-coded crop origin arithmetically equals the accepted host descriptor."],
            [
                "A 16x16 image replaces the accepted 1920x1080 plane.",
                "Host coordinates are recovered by adding the manually selected origin (84,833).",
            ],
            ["Proof that full-frame worker/scan state and all reachable neighborhoods are invariant under this crop."],
        ),
        "host_input": inventory_entry(
            "export-grounded-translated-adapter",
            False,
            False,
            [
                f"The integer PF8 premultiply rule matches all {crop_adapter['pixels_checked']} before-effects bytes in the crop.",
                "The first retained source sample agrees structurally with the accepted first vertex.",
            ],
            [
                "AE host checkout and PF8-to-float conversion are replaced by Python/PIL plus an integer adapter.",
                "The retained post-sRGB sample differs by 3 float32 ULPs. Independent pow-boundary audit shows Mac libm and a high-precision oracle agree, and forcing the retained word does not change class, descriptor, weight, or cce0 output for this witness.",
            ],
            ["Same-run Windows post-host/post-sRGB float plane for the complete dependency neighborhood."],
        ),
        "class_plane": inventory_entry(
            "actual-aex-bounded/three-live-bytes-only",
            True,
            False,
            [
                "Actual AEX ada0/ac00/ae10 produces the bounded class plane.",
                "Accepted center, previous, and left class bytes are available; the runner asserts center and previous.",
            ],
            ["The remaining bounded class plane is generated from translated crop input, not captured from the live Windows run."],
            ["Same-run Windows class-plane dependency region or a proof that the three retained pixels are sufficient."],
        ),
        "dispatcher": inventory_entry(
            "actual-aex-dispatch/direct-cce0-entry",
            True,
            False,
            [
                "Actual AEX cce0 calls c280/fef0 and selects key 20 from the generated descriptor.",
                "The accepted Windows run proves descriptor, e170 c=7, and the first f270 append.",
            ],
            [
                "The bounded runner enters cce0 directly instead of reaching it through the full-frame AE worker/caller.",
                "The bounded first-vertex snapshot is downstream of f270/dispatcher normalization, so its weight cannot be compared to the accepted raw f270-return weight.",
            ],
            ["Same-run Windows or full-frame actual-AEX proof of the cce0 call arguments and dispatch continuation."],
        ),
        "second_vertex": inventory_entry(
            "actual-aex-local-continuation/windows-live-unobserved",
            True,
            False,
            ["Actual AEX f130/e290 appends a second vertex in the bounded execution."],
            ["Windows live evidence ends after f270 with vertex_count=1; it contains no f130/e290 return or post-f130 polygon."],
            ["Same-run Windows post-f130 polygon including the second vertex float32 words and weight."],
        ),
        "cce0_config": inventory_entry(
            "manual-struct-reconstruction",
            True,
            False,
            ["Known manifest values are placed into offsets inferred from AEX/decomp and existing local oracles."],
            [
                "The config allocation is manually zero-filled and populated field by field.",
                "The gamma mode byte 3 is a reconstructed mapping from UI value 2 (Gamma Colors), not a same-run config capture.",
            ],
            ["Accepted Windows cce0 config bytes/pointers and caller argument values from the same run."],
        ),
        "writer": inventory_entry(
            "absent",
            False,
            False,
            [],
            [
                "The runner stops at the cce0 float output buffer.",
                "No full worker return, writer call, output color transform, clamp, premultiply, or PF8 pack executes.",
            ],
            ["Natural continuation from this exact cce0 result through the accepted Windows writer to the final PF8 byte."],
        ),
    }
    require(list(inventory) == REQUIRED_BOUNDARIES, "assumption inventory boundary set drift")
    require(all(not item["windows_live_equivalence_proved"] for item in inventory.values()), "live-equivalent boundary unexpectedly asserted")

    comparison = {
        "bounded_cce0_float_rgba": cce0_rgba,
        "windows_live_final_pf8_rgba": windows_pixel,
        "same_case_id": True,
        "same_coordinate": True,
        "same_semantic_stage": False,
        "writer_bridge_present": False,
        "direct_numeric_comparison_allowed": False,
        "naive_linear_times_255_rgb": [value * 255.0 for value in cce0_rgba[:3]],
        "naive_rounded_rgb": [round(value * 255.0) for value in cce0_rgba[:3]],
        "naive_conversion_is_evidence": False,
        "reasons": [
            "cce0 returns an internal float4 while 233 is a final exported PF8 code value.",
            "The bounded cce0 input/config is not proved identical to the accepted Windows live cce0 state.",
            "The only retained Windows weight and the bounded polygon weight come from different semantic stages.",
            "The natural worker-to-writer continuation and its encode/premultiply/clamp/pack rules do not execute.",
        ],
    }

    return {
        "schema": 1,
        "verdict": "FAIL_CLOSED_BOUNDED_ACTUAL_AEX_NOT_LIVE_PIXEL_COMPARABLE",
        "ae_exact": False,
        "full_windows_live_case_reproduced": False,
        "inputs": {
            "runner": str(RUNNER.relative_to(ROOT)),
            "runner_sha256": sha256(RUNNER),
            "bounded_result": str(RESULT.relative_to(ROOT)),
            "bounded_result_sha256": sha256(RESULT),
            "accepted_windows_live_fixture": str(WINDOWS_LIVE.relative_to(ROOT)),
            "accepted_windows_live_fixture_sha256": sha256(WINDOWS_LIVE),
            "parameter_manifest": str(PARAMS.relative_to(ROOT)),
            "windows_output": str(WINDOWS_OUTPUT.relative_to(ROOT)),
        },
        "accepted_windows_live_boundary": {
            "case_id": CASE_ID,
            "renderer": "Software",
            "project_bpc": 8,
            "aex_sha256": EXPECTED_AEX_SHA256,
            "descriptor": EXPECTED_DESCRIPTOR,
            "class_bytes": EXPECTED_CLASS,
            "e170_c": 7,
            "observed_polygon_count_after_f270": 1,
            "first_vertex_rgba_u32": accepted_first_rgba_u32,
            "first_vertex_weight_u32": accepted_first_weight_u32,
            "final_pf8_pixel": windows_pixel,
            "not_observed": ["post-f130 second vertex", "cce0 config/input/output", "same-chain writer input"],
        },
        "bounded_execution": {
            "verdict": bounded["verdict"],
            "rerun_stdout": rerun["stdout"],
            "crop_host_adapter_check": crop_adapter,
            "descriptor": bounded["events"]["descriptor"]["host_translated"],
            "post_f130_count": bounded["events"]["post_f130_post_boost"]["count"],
            "cce0_output": cce0_rgba,
            "first_vertex_vs_windows_live": first_vertex_comparison,
        },
        "assumption_inventory": inventory,
        "comparison_to_windows_live_pixel_233": comparison,
        "fail_closed_rules": [
            "Executing actual AEX instructions does not prove that manually supplied caller state equals the accepted live state.",
            "A crop-translated descriptor match does not prove full-frame equivalence.",
            "An internal float may not be compared to an exported PF8 byte without a proved same-chain writer bridge.",
            "Any future live-pixel comparison requires every required boundary to have windows_live_equivalence_proved=true.",
        ],
        "next_required_evidence": [
            "Same-run Windows post-f130 polygon capture for the accepted descriptor, including the second vertex.",
            "Same-run Windows cce0 config bytes, arguments, input polygon, and returned float4.",
            "Same-run natural continuation from cce0 return through the actual PF8 writer for pixel (92,841).",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    rows = []
    for name in REQUIRED_BOUNDARIES:
        item = report["assumption_inventory"][name]
        rows.append(
            f"| `{name}` | `{item['classification']}` | "
            f"{'yes' if item['aex_instructions_execute'] else 'no'} | "
            f"{'yes' if item['windows_live_equivalence_proved'] else 'no'} |"
        )
    comparison = report["comparison_to_windows_live_pixel_233"]
    first = report["bounded_execution"]["first_vertex_vs_windows_live"]
    return "\n".join([
        "# OLMSmoother2 case0012 bounded assumption hard audit - 2026-07-18",
        "",
        f"- Verdict: `{report['verdict']}`",
        "- AE exact: `false`",
        "- Full accepted Windows live case reproduced: `false`",
        "",
        "## Answer: 0.8575 vs 233",
        "",
        f"The bounded result is cce0 float4 `{comparison['bounded_cce0_float_rgba']}`. The accepted Windows image pixel is final PF8 `{comparison['windows_live_final_pf8_rgba']}`.",
        "",
        "They are not legitimately comparable yet. They share a case id and coordinate, but not a proved semantic stage. The bounded runner directly calls cce0 with reconstructed state and never executes the natural worker-to-writer bridge. Therefore even the naive conversion shown in JSON is diagnostic only and is not evidence of either agreement or disagreement.",
        "",
        f"The retained first-vertex records are not a valid weight comparison: Windows `{first['windows_weight_u32']:#010x}` is captured at raw `f270` return, while bounded `{first['bounded_weight_u32']:#010x}` is a post-dispatch polygon weight. The recorded RGB word delta `{first['rgba_u32_delta_bounded_minus_windows']}` remains diagnostic only.",
        "",
        "## Assumption Inventory",
        "",
        "| Boundary | Classification | AEX executes | Windows-live equivalent |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
        "## Detailed Boundaries",
        "",
        *sum(([
            f"### {name}",
            "",
            f"- Grounded: {'; '.join(report['assumption_inventory'][name]['grounded']) or 'none' }",
            f"- Synthetic/manual: {'; '.join(report['assumption_inventory'][name]['synthetic_or_manual_assumptions']) or 'none'}",
            f"- Missing proof: {'; '.join(report['assumption_inventory'][name]['missing_proof']) or 'none'}",
            "",
        ] for name in REQUIRED_BOUNDARIES), []),
        "## Fail-Closed Rule",
        "",
        *[f"- {rule}" for rule in report["fail_closed_rules"]],
        "",
        "## Next Evidence",
        "",
        *[f"- {item}" for item in report["next_required_evidence"]],
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/audit_olmsmoother2_case0012_bounded_assumptions_20260718.py",
        "```",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "refs/conformance/olmsmoother2_case0012_bounded_assumption_audit_20260718.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "refs/conformance/olmsmoother2_case0012_bounded_assumption_audit_20260718.md",
    )
    parser.add_argument("--self-test-tamper-writer-bridge", action="store_true")
    args = parser.parse_args()
    report = audit()
    if args.self_test_tamper_writer_bridge:
        report["comparison_to_windows_live_pixel_233"]["writer_bridge_present"] = True
        require(
            not report["comparison_to_windows_live_pixel_233"]["writer_bridge_present"],
            "tampered writer bridge must be rejected",
        )
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(report["verdict"])
    print("boundaries=" + ",".join(REQUIRED_BOUNDARIES))
    print("live_pixel_comparison_allowed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
