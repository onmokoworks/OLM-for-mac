#!/usr/bin/env python3
"""Focused regression and report writer for the bounded case_0003 probe."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmblur_case0003_legacy_fullframe import POINTS, run_probe  # noqa: E402

REPORT_JSON = ROOT / "refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.md"


def main() -> int:
    report = run_probe()
    if report["status"] != "pass_two_layer_witness":
        raise AssertionError(f"unexpected status: {report['status']}")
    schedule = report["schedule_capture"]
    if schedule["call_count"] != 120 or len(schedule["iterations"]) != 10:
        raise AssertionError("captured schedule count differs")
    if any(item["radius"] <= 0 for item in schedule["iterations"]):
        raise AssertionError("captured schedule has a non-positive radius")
    layer_a = report["layer_a_actual_helper_microfixtures"]
    if layer_a["distinct_radius_direction_count"] != 2 or len(layer_a["fixtures"]) != 2 or not layer_a["all_exact"]:
        raise AssertionError("Layer A distinct radius/direction coverage differs")
    layer_b = report["layer_b_native_portable"]
    if len(layer_b["predictions"]) != len(POINTS) or len(layer_b["retained_comparisons"]) != len(POINTS):
        raise AssertionError("Layer B does not cover all 20 residual coordinates")
    if layer_b["runtime_seconds"] >= layer_b["runtime_cap_seconds"]:
        raise AssertionError("Layer B runtime reached cap")
    coefficients = report["coefficient_candidate"]
    if coefficients["current_float_exp_diff_words"] != 16:
        raise AssertionError("current float-exp coefficient residual differs")
    if coefficients["double_exp_float_cast_diff_words"] != 0 or \
            coefficients["double_exp_float_cast_exact_words"] != 4970:
        raise AssertionError("double-exp candidate no longer matches captured coefficients")
    if coefficients["case0007_candidate_changes"] != 0 or \
            coefficients["case0007_exact_control_words"] != 110:
        raise AssertionError("double-exp candidate changes exact Legacy case_0007")

    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    mac_available = sum(item["portable_matches_mac_rgb"] is not None for item in layer_b["retained_comparisons"].values())
    mac_matches = sum(item["portable_matches_mac_rgb"] is True for item in layer_b["retained_comparisons"].values())
    windows_matches = sum(item["portable_matches_windows_rgb"] for item in layer_b["retained_comparisons"].values())
    radii = [item["radius"] for item in schedule["iterations"]]
    lines = [
        "# OLMBlur Legacy case_0003 bounded schedule/full-frame probe", "", "## FACT", "",
        f"- Pinned actual AEX: `{report['identity']['aex']}` / `{report['identity']['aex_sha256']}`; Legacy entry `{report['identity']['entry']}`.",
        "- Exact case parameters are amount `248.600006103516`, smoothness `100`, repeat `10`, bias `1`, Legacy `1`, at `960x540`.",
        f"- With both helper bodies detoured to `RET`, the actual guest caller produced exactly `{schedule['call_count']}` calls in ten `H x 6, V x 6` iterations. Captured radii: `{radii}`. Every call's dimensions, columns/rows, offset/pass range, radius, coefficient bytes, and pointers are retained in JSON.",
        f"- Coefficient provenance is `{schedule['math_backend']}`. These bytes are explicitly not Windows CRT truth and were not tuned against retained outputs.",
        f"- Layer A runs the smallest two-pixel/one-output actual helper fixture for every distinct captured radius/direction. Both `{len(layer_a['fixtures'])}` fixtures match portable C++ byte-for-byte under a `3,000,000` instruction cap.",
        f"- The dependency reaches beyond the frame, so Layer B runs the complete `960x540` composition only in compiled native portable C++. It preserves the captured call schedule and coefficient bytes and completed in `{layer_b['runtime_seconds']:.3f}` seconds (wall `{layer_b['wall_seconds']:.3f}`; cap `{layer_b['runtime_cap_seconds']}`).",
        f"- All `{len(POINTS)}` known residual coordinates retain pre-store float32 bits and grounded PF16 writer predictions. Predictions match the pinned Windows RGB at `{windows_matches}/20` points. The authoritative current Mac verifier retains words for its first `{mac_available}` samples, where predictions match `{mac_matches}/{mac_available}`; the remaining Mac words are explicitly unavailable.",
        f"- Current 16bpc Legacy float-exp generation differs from the captured coefficient words at `{coefficients['current_float_exp_diff_words']}/4970` positions, split by iteration as `{coefficients['current_float_exp_diff_by_iteration']}`. The bounded double-exp-to-float candidate matches `4970/4970`; for already-exact Legacy `case_0007`, it changes `0/{coefficients['case0007_exact_control_words']}` coefficient words. The 8bpc and 32bpc Legacy workers are outside this candidate's scope.",
        "- No actual full-frame x86 worker, Windows, NAS, SSH, or AE execution occurred.", "", "## Witnesses", "",
    ]
    for point, values in layer_b["predictions"].items():
        comparison = layer_b["retained_comparisons"][point]
        lines.append(f"- `{point}` float32 `{values['pre_store_float32']}`, bits `{values['pre_store_bits_hex']}`, predicted RGB `{values['writer_predicted_rgb_words']}`, Mac ARGB `{comparison['retained_mac_argb16_words']}`, Windows ARGB `{comparison['retained_windows_argb16_words']}`.")
    lines.extend(["", "## INFERENCE", "",
                  f"- Classification: `{report['classification']}`.",
                  "- Layer A is function-level evidence for the two distinct radius/direction helper shapes under the captured callback coefficients.",
                  "- Layer B is a complete native portable prediction, not actual-AEX full-frame execution. Its retained Mac/Windows comparison localizes agreement under the declared coefficient backend but cannot establish Windows CRT coefficient equivalence.",
                  "- The coefficient A/B is a narrow source candidate supported by captured guest-caller bytes and retained Windows outputs; it still requires a fresh Mac AE 16bpc identity-bound rerun before `AE exact` promotion.",
                  "- The probe fails closed on dependency hashes, schedule count/order/partition, helper mismatch, missing inputs, malformed native output, or excessive runtime.",
                  "", "## Test", "", "```text",
                  "python3 tools/emulation/test_olmblur_case0003_legacy_schedule_fullframe_20260716.py", "```", "",
                  "## New files", "",
                  "- `tools/emulation/probe_olmblur_case0003_legacy_fullframe.py`",
                  "- `tools/emulation/probe_olmblur_case0003_legacy_fullframe.cpp`",
                  "- `tools/emulation/test_olmblur_case0003_legacy_schedule_fullframe_20260716.py`",
                  "- `refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.json`",
                  "- `refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.md`"])
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "calls": schedule["call_count"],
                      "radii": radii, "microfixtures": len(layer_a["fixtures"]),
                      "native_seconds": layer_b["runtime_seconds"], "mac_available": mac_available,
                      "mac_matches": mac_matches,
                      "windows_matches": windows_matches, "report_json": str(REPORT_JSON.relative_to(ROOT)),
                      "report_md": str(REPORT_MD.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
