#!/usr/bin/env python3
"""Portable-only case_0004 full-cone sensitivity to two coefficient sets."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmblur_case0004_staged_helper_replay import (  # noqa: E402
    HEIGHT,
    WIDTH,
    WITNESSES,
    bits_hex,
    compile_portable,
    crop,
    expected_staging,
    load_input,
    run_portable,
)

CALLER_REPORT = ROOT / "refs/conformance/olmblur_case0004_staged_helper_replay_20260716.json"
CALLER_REPORT_SHA256 = "015bd884f5f7186a6923c74e95e009c4d9709151a5d537c976ee741f1754f878"
MAC_REPORT = ROOT / "refs/conformance/olmblur_case0004_mac_generation_audit_20260716.json"
MAC_REPORT_SHA256 = "fa593a9bb2315d8bda3714fc8187683c0d1cf890559bf0ce45a348f57de6c155"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_report(path: Path, expected_sha256: str, schema: str) -> dict:
    blob = path.read_bytes()
    if sha256(blob) != expected_sha256:
        raise AssertionError(f"source report hash differs: {path}")
    report = json.loads(blob)
    if report.get("schema") != schema:
        raise AssertionError(f"source report schema differs: {path}")
    return report


def caller_coefficients(report: dict) -> list[dict]:
    calls = report["staging"]["helper_calls_captured"]
    if len(calls) != 48:
        raise AssertionError(f"caller schedule call count differs: {len(calls)}")
    result = []
    for iteration in range(4):
        group = calls[iteration * 12:(iteration + 1) * 12]
        radii = {call["radius"] for call in group}
        weights = {call["weights_hex"] for call in group}
        if len(radii) != 1 or len(weights) != 1:
            raise AssertionError(f"caller H/V values disagree at iteration {iteration + 1}")
        radius = radii.pop()
        raw = bytes.fromhex(weights.pop())
        if len(raw) != (radius + 1) * 4:
            raise AssertionError(f"caller coefficient count differs at iteration {iteration + 1}")
        result.append({"iteration": iteration + 1, "radius": radius, "weights": raw,
                       "words": list(struct.unpack(f"<{radius + 1}I", raw))})
    return result


def mac_coefficients(report: dict) -> list[dict]:
    result = []
    for record in report["mac_production_formula"]:
        words = [int(word, 16) for word in record["coefficient_words_hex"]]
        radius = record["radius"]
        if len(words) != radius + 1:
            raise AssertionError(f"Mac coefficient count differs at iteration {record['iteration']}")
        result.append({"iteration": record["iteration"], "radius": radius,
                       "words": words, "weights": struct.pack(f"<{len(words)}I", *words)})
    return result


def validate_deltas(a: list[dict], b: list[dict], audit: dict) -> list[dict]:
    differences = []
    if len(a) != 4 or len(b) != 4:
        raise AssertionError("coefficient sets do not contain four iterations")
    for a_iteration, b_iteration in zip(a, b):
        if (a_iteration["iteration"], a_iteration["radius"]) != (b_iteration["iteration"], b_iteration["radius"]):
            raise AssertionError("A/B iteration or radius sequence differs")
        for index, (a_word, b_word) in enumerate(zip(a_iteration["words"], b_iteration["words"])):
            if a_word != b_word:
                differences.append({
                    "iteration": a_iteration["iteration"], "index": index, "index_base": 0,
                    "a_word": f"0x{a_word:08x}", "b_word": f"0x{b_word:08x}",
                    "unsigned_word_delta": b_word - a_word,
                })
    expected = audit["first_mismatch"]
    if not differences or differences[0] != {
        "iteration": expected["iteration"], "index": expected["index"], "index_base": 0,
        "a_word": expected["actual_aex_word"], "b_word": expected["mac_word"],
        "unsigned_word_delta": int(expected["mac_word"], 16) - int(expected["actual_aex_word"], 16),
    }:
        raise AssertionError(f"coefficient discriminator differs: {differences!r}")
    if any(abs(item["unsigned_word_delta"]) != 1 for item in differences):
        raise AssertionError("a coefficient discriminator is not one float32 ULP")
    return differences


def compose(executable: Path, temp: Path, label: str, plane_full: bytes, flags_full: bytes,
            coefficients: list[dict]) -> dict:
    reach = sum(item["radius"] for item in coefficients)
    stages = []
    final = {}
    for witness_index, (x, y) in enumerate(WITNESSES):
        bounds = (x - reach, y - reach, x + reach + 1, y + reach + 1)
        if bounds[0] < 0 or bounds[1] < 0 or bounds[2] > WIDTH or bounds[3] > HEIGHT:
            raise AssertionError(f"dependency cone reaches frame edge: {(x, y)!r}")
        plane = crop(plane_full, (0, 0, WIDTH, HEIGHT), bounds, 12)
        flags = crop(flags_full, (0, 0, WIDTH, HEIGHT), bounds, 1)
        for fixture in coefficients:
            for direction in ("horizontal", "vertical"):
                input_bounds = bounds
                width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
                output = run_portable(
                    executable, temp, f"{label}_w{witness_index + 1}_i{fixture['iteration']}_{direction[0]}",
                    direction, flags, plane, fixture["weights"], width, height, fixture["radius"]
                )
                radius = fixture["radius"]
                if direction == "horizontal":
                    bounds = (bounds[0] + radius, bounds[1], bounds[2] - radius, bounds[3])
                else:
                    bounds = (bounds[0], bounds[1] + radius, bounds[2], bounds[3] - radius)
                plane = crop(output, input_bounds, bounds, 12)
                flags = crop(flags, input_bounds, bounds, 1)
                stages.append({
                    "witness": [x, y], "iteration": fixture["iteration"], "direction": direction,
                    "radius": radius, "input_dimensions": [width, height],
                    "output_dimensions": [bounds[2] - bounds[0], bounds[3] - bounds[1]],
                    "retained_output_sha256": sha256(plane), "execution": "portable_only",
                })
        if bounds != (x, y, x + 1, y + 1) or len(plane) != 12:
            raise AssertionError(f"portable cone did not converge at {(x, y)!r}")
        final[f"({x},{y})"] = bits_hex(plane)
    return {"initial_crop_dimensions": [reach * 2 + 1, reach * 2 + 1], "stages": stages, "final_bits_hex": final}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def predict_standard_writer(words_hex: list[str]) -> list[int]:
    predicted = []
    for word_hex in words_hex:
        value = struct.unpack("<f", struct.pack("<I", int(word_hex, 16)))[0]
        rounded = math.floor(f32(value + f32(0.5)))
        predicted.append(0 if rounded <= 0 else 32768 if rounded >= 32768 else int(rounded))
    return predicted


def isolate_delta(a: list[dict], b: list[dict], delta: dict) -> list[dict]:
    result = []
    for a_iteration, b_iteration in zip(a, b):
        words = list(a_iteration["words"])
        if a_iteration["iteration"] == delta["iteration"]:
            words[delta["index"]] = b_iteration["words"][delta["index"]]
        result.append({
            "iteration": a_iteration["iteration"], "radius": a_iteration["radius"],
            "words": words, "weights": struct.pack(f"<{len(words)}I", *words),
        })
    return result


def run_probe() -> dict:
    caller_report = require_report(
        CALLER_REPORT, CALLER_REPORT_SHA256, "olmblur.case0004.staged-helper-replay/1"
    )
    mac_report = require_report(
        MAC_REPORT, MAC_REPORT_SHA256, "olmblur.case0004.mac-radius-weight-generation-audit/1"
    )
    if mac_report.get("classification") != "generation_mismatch":
        raise AssertionError("Mac generation report no longer contains the discriminator")
    coefficients_a = caller_coefficients(caller_report)
    coefficients_b = mac_coefficients(mac_report)
    discriminators = validate_deltas(coefficients_a, coefficients_b, mac_report)

    pf16, input_identity = load_input()
    plane, flags = expected_staging(pf16)
    if sha256(plane) != caller_report["staging"]["plane_sha256"] or sha256(flags) != caller_report["staging"]["flags_sha256"]:
        raise AssertionError("reconstructed staged plane/flags differ from the actual-AEX capture")

    with tempfile.TemporaryDirectory(prefix="olmblur_case0004_coefficient_sensitivity_") as temporary:
        temp = Path(temporary)
        executable = temp / "portable_helper"
        compile_command = compile_portable(executable)
        result_a = compose(executable, temp, "a", plane, flags, coefficients_a)
        result_b = compose(executable, temp, "b", plane, flags, coefficients_b)
        index57_coefficients = isolate_delta(coefficients_a, coefficients_b, discriminators[0])
        result_index57 = compose(executable, temp, "index57", plane, flags, index57_coefficients)

    comparisons = {}
    for point in result_a["final_bits_hex"]:
        a_bits = result_a["final_bits_hex"][point]
        b_bits = result_b["final_bits_hex"][point]
        a_prediction = predict_standard_writer(a_bits)
        b_prediction = predict_standard_writer(b_bits)
        comparisons[point] = {
            "a_pre_store_bits_hex": a_bits, "b_pre_store_bits_hex": b_bits,
            "pre_store_exact": a_bits == b_bits,
            "a_predicted_rgb_words": a_prediction, "b_predicted_rgb_words": b_prediction,
            "predicted_words_exact": a_prediction == b_prediction,
        }
    changes_pre_store = any(not item["pre_store_exact"] for item in comparisons.values())
    changes_predicted_word = any(not item["predicted_words_exact"] for item in comparisons.values())
    index57_comparisons = {}
    for point in result_a["final_bits_hex"]:
        a_bits = result_a["final_bits_hex"][point]
        isolated_bits = result_index57["final_bits_hex"][point]
        a_prediction = predict_standard_writer(a_bits)
        isolated_prediction = predict_standard_writer(isolated_bits)
        index57_comparisons[point] = {
            "a_pre_store_bits_hex": a_bits, "index57_only_pre_store_bits_hex": isolated_bits,
            "pre_store_exact": a_bits == isolated_bits,
            "a_predicted_rgb_words": a_prediction,
            "index57_only_predicted_rgb_words": isolated_prediction,
            "predicted_words_exact": a_prediction == isolated_prediction,
        }
    index57_changes_pre_store = any(not item["pre_store_exact"] for item in index57_comparisons.values())
    index57_changes_predicted_word = any(not item["predicted_words_exact"] for item in index57_comparisons.values())
    return {
        "schema": "olmblur.case0004.coefficient-sensitivity/1",
        "status": "pass_bounded_ab",
        "platform": "Mac-only native portable helper composition; no actual-AEX Layer B execution",
        "identity": {
            "caller_report": str(CALLER_REPORT.relative_to(ROOT)), "caller_report_sha256": CALLER_REPORT_SHA256,
            "mac_generation_report": str(MAC_REPORT.relative_to(ROOT)), "mac_generation_report_sha256": MAC_REPORT_SHA256,
            "input": input_identity,
        },
        "coefficient_discriminators": discriminators,
        "radius_sequence": [item["radius"] for item in coefficients_a],
        "set_labels": {
            "a": "declared host-callback coefficient set; not Windows truth",
            "b": "current Mac production-generated coefficient set; not Windows truth",
        },
        "portable_compile_command": compile_command,
        "a": result_a,
        "b": result_b,
        "supplemental_index57_only": {
            "execution": "portable_only synthetic isolation; not coefficient set B and not Windows truth",
            "cone": result_index57,
            "comparisons": index57_comparisons,
        },
        "standard_writer_prediction": {
            "arithmetic": "for each float32 RGB value: floorf(float32(value + 0.5f)), clamped to [0,32768]",
            "claim": "reported prediction only; not an actual-AEX writer run and not Windows truth",
            "comparisons": comparisons,
        },
        "conclusion": {
            "complete_coefficient_set_changes_pre_store": changes_pre_store,
            "complete_coefficient_set_changes_predicted_word": changes_predicted_word,
            "declared_single_index57_delta_assumption_valid": len(discriminators) == 1,
            "index57_only_changes_pre_store": index57_changes_pre_store,
            "index57_only_changes_predicted_word": index57_changes_predicted_word,
        },
        "claim_limit": "Both sets are bounded Mac-side hypotheses. Neither is labeled or inferred as Windows truth.",
    }


if __name__ == "__main__":
    report = run_probe()
    print(json.dumps({"status": report["status"], "conclusion": report["conclusion"],
                      "comparisons": report["standard_writer_prediction"]["comparisons"]}, indent=2))
