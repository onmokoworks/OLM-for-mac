#!/usr/bin/env python3
"""Audit the imported pow boundary in the bounded Smoother2 actual-AEX run.

This deliberately does not patch the plug-in.  It proves the PE import/ABI,
captures the exact arguments supplied by guest code, compares the host-backed
result with a high-precision mathematical oracle, and runs one bounded
sensitivity replay using the retained Windows float word.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import sys
from typing import Any

import pefile

ROOT = Path(__file__).resolve().parents[2]
EMULATION = ROOT / "tools" / "emulation"
sys.path.insert(0, str(EMULATION))

import aex_loader  # noqa: E402

AEX = ROOT / "plugins_2025/OLMSmoother2.aex"
DISASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
RUNNER = EMULATION / "run_olmsmoother2_case0012_natural_post_f130_20260718.py"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"

WITNESS_X_F64 = 0x3FDFA568C0E8F2A7
EXPONENT_F64 = 0x4003333333333333
HOST_RESULT_F32 = 0x3E3CE703
WINDOWS_RETAINED_F32 = 0x3E3CE706


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def f64_from_word(word: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", word))[0]


def f32_from_word(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


def f64_word(value: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def f32_word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def load_runner_module(tag: str):
    spec = importlib.util.spec_from_file_location(f"olmsmoother2_pow_runner_{tag}", RUNNER)
    require(spec is not None and spec.loader is not None, "cannot load bounded runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect_import_and_callsite() -> dict[str, Any]:
    pe = pefile.PE(str(AEX), fast_load=False)
    matches = []
    for descriptor in pe.DIRECTORY_ENTRY_IMPORT:
        dll = descriptor.dll.decode("ascii", "replace")
        for imported in descriptor.imports:
            name = imported.name.decode("ascii", "replace") if imported.name else None
            if name == "pow":
                matches.append({
                    "dll": dll,
                    "name": name,
                    "iat_va": imported.address,
                    "iat_rva": imported.address - pe.OPTIONAL_HEADER.ImageBase,
                })
    require(matches == [{
        "dll": "api-ms-win-crt-math-l1-1-0.dll",
        "name": "pow",
        "iat_va": 0x1800221D0,
        "iat_rva": 0x221D0,
    }], f"unexpected pow import: {matches}")

    disasm = DISASM.read_text(encoding="utf-8")
    sequence = re.search(
        r"180002d15\s+MULSD XMM0,XMM10\n"
        r"180002d1a\s+MOVAPS XMM1,XMM12\n"
        r"180002d1e\s+ADDSD XMM0,XMM11\n"
        r"180002d23\s+CALL 0x180020f76\n"
        r"180002d28\s+CVTSD2SS XMM0,XMM0",
        disasm,
    )
    thunk = re.search(
        r"; === pow @ 180020f76 ===\n180020f76\s+JMP qword ptr \[0x1800221d0\]",
        disasm,
    )
    require(sequence is not None, "sRGB pow call sequence drift")
    require(thunk is not None, "pow IAT thunk drift")
    return {
        "import": matches[0],
        "abi": "Windows x64 double pow(double XMM0, double XMM1), double XMM0 return",
        "callsite": "0x180002d23",
        "post_call_conversion": "0x180002d28 CVTSD2SS XMM0,XMM0",
        "thunk": "0x180020f76 -> IAT 0x1800221d0",
    }


def high_precision_oracle() -> dict[str, Any]:
    x = f64_from_word(WITNESS_X_F64)
    exponent = f64_from_word(EXPONENT_F64)
    with localcontext() as context:
        context.prec = 110
        exact_x = Decimal.from_float(x)
        exact_exponent = Decimal.from_float(exponent)
        mathematical = (exact_exponent * exact_x.ln()).exp()
        host_double = math.pow(x, exponent)
        host_f32 = f32_word(host_double)
        windows_value = Decimal.from_float(f32_from_word(WINDOWS_RETAINED_F32))
        host_value = Decimal.from_float(f32_from_word(HOST_RESULT_F32))
        f32_ulp = Decimal.from_float(f32_from_word(HOST_RESULT_F32 + 1)) - host_value
        windows_error_ulp = (windows_value - mathematical) / f32_ulp

    require(f64_word(host_double) == 0x3FC79CE06DC69584, "host pow double drift")
    require(host_f32 == HOST_RESULT_F32, "host pow float rounding drift")
    require(abs(Decimal.from_float(host_double) - mathematical) < Decimal("2e-17"),
            "host pow is not close to the high-precision oracle")
    require(windows_error_ulp > Decimal("2.5"), "retained word unexpectedly plausible for same input")
    return {
        "input_x": x,
        "input_x_f64_word": f"0x{WITNESS_X_F64:016x}",
        "exponent": exponent,
        "exponent_f64_word": f"0x{EXPONENT_F64:016x}",
        "high_precision_result": str(mathematical),
        "host_pow_double": host_double,
        "host_pow_double_word": f"0x{f64_word(host_double):016x}",
        "host_after_cvtsd2ss_word": f"0x{host_f32:08x}",
        "windows_retained_word": f"0x{WINDOWS_RETAINED_F32:08x}",
        "retained_delta_f32_ulp": WINDOWS_RETAINED_F32 - host_f32,
        "retained_error_from_mathematical_in_f32_ulp": float(windows_error_ulp),
        "conclusion": (
            "The retained Windows word cannot be attributed to a three-float-ULP "
            "UCRT error for this same input; upstream input/provenance remains unproven."
        ),
    }


def run_variant(force_retained_word: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    original_register = aex_loader.AexLoader.register_libm_impls
    calls: list[dict[str, Any]] = []

    def instrumented_register(loader: aex_loader.AexLoader, max_threads: int = 1) -> None:
        original_register(loader, max_threads)

        def imported_pow(_uc, _args):
            x = loader.read_xmm_f64(0)
            exponent = loader.read_xmm_f64(1)
            x_word = f64_word(x)
            exponent_word = f64_word(exponent)
            result = math.pow(x, exponent)
            forced = force_retained_word and x_word == WITNESS_X_F64 and exponent_word == EXPONENT_F64
            if forced:
                result = float(f32_from_word(WINDOWS_RETAINED_F32))
            calls.append({
                "x_f64_word": f"0x{x_word:016x}",
                "exponent_f64_word": f"0x{exponent_word:016x}",
                "returned_f64_word": f"0x{f64_word(result):016x}",
                "returned_f32_word": f"0x{f32_word(result):08x}",
                "forced_retained_word": forced,
            })
            loader.write_xmm_f64(0, result)
            return 0

        loader.import_impls["pow"] = imported_pow

    aex_loader.AexLoader.register_libm_impls = instrumented_register
    try:
        report = load_runner_module("forced" if force_retained_word else "baseline").run()
    finally:
        aex_loader.AexLoader.register_libm_impls = original_register
    return report, calls


def relevant_state(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "previous_rgba_u32": report["post_setup"]["previous_rgba_u32"],
        "class_witness": report["class_witness"],
        "descriptor": report["events"]["descriptor"],
        "polygon": report["events"]["post_f130_post_boost"],
        "cce0_output": report["cce0_output"],
    }


def bounded_sensitivity() -> dict[str, Any]:
    baseline, baseline_calls = run_variant(False)
    forced, forced_calls = run_variant(True)
    baseline_state = relevant_state(baseline)
    forced_state = relevant_state(forced)
    forced_count = sum(call["forced_retained_word"] for call in forced_calls)
    require(len(baseline_calls) == len(forced_calls) == 45, "pow call count drift")
    require(forced_count == 3, f"unexpected forced witness call count: {forced_count}")
    require(baseline_state["previous_rgba_u32"][0] == HOST_RESULT_F32, "baseline witness word drift")
    require(forced_state["previous_rgba_u32"][0] == WINDOWS_RETAINED_F32, "forced witness word drift")
    require(baseline_state["class_witness"] == forced_state["class_witness"], "class plane changed")
    require(baseline_state["descriptor"] == forced_state["descriptor"], "descriptor changed")
    require(
        baseline_state["polygon"]["vertices"][0]["rgba_u32"][0] !=
        forced_state["polygon"]["vertices"][0]["rgba_u32"][0],
        "injected difference did not reach polygon RGB",
    )
    require(
        [vertex["weight_u32"] for vertex in baseline_state["polygon"]["vertices"]] ==
        [vertex["weight_u32"] for vertex in forced_state["polygon"]["vertices"]],
        "polygon weights changed",
    )
    require(baseline_state["cce0_output"]["rgba_u32"] == forced_state["cce0_output"]["rgba_u32"],
            "cce0 output changed")
    return {
        "pow_calls": len(baseline_calls),
        "forced_witness_calls": forced_count,
        "baseline_previous_red_word": f"0x{baseline_state['previous_rgba_u32'][0]:08x}",
        "forced_previous_red_word": f"0x{forced_state['previous_rgba_u32'][0]:08x}",
        "class_plane_bitwise_equal": True,
        "descriptor_equal": True,
        "polygon_weights_bitwise_equal": True,
        "polygon_rgb_difference_preserved": True,
        "cce0_output_bitwise_equal": True,
        "pf8_witness_conclusion": (
            "For this bounded case_0012 witness, the retained three-ULP RGB difference "
            "does not reach cce0 output and therefore cannot change its PF8 writer result."
        ),
    }


def build_report() -> dict[str, Any]:
    import hashlib

    require(hashlib.sha256(AEX.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    return {
        "schema": 1,
        "verdict": "PASS_IMPORTED_POW_BOUNDARY_CLASSIFIED_NOT_UCRT_ONLY",
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": EXPECTED_AEX_SHA256},
        "binary_contract": inspect_import_and_callsite(),
        "numerical_oracle": high_precision_oracle(),
        "bounded_sensitivity": bounded_sensitivity(),
        "facts": [
            "The AEX imports double pow from the Universal CRT API-set and converts its double return to float32.",
            "The actual-AEX runner currently substitutes Python math.pow backed by Darwin libm.",
            "For the captured runner input, Darwin libm agrees with a high-precision oracle and rounds to 0x3e3ce703.",
            "The retained 0x3e3ce706 word is not evidence of a three-float-ULP UCRT error for that same input.",
            "Injecting 0x3e3ce706 into the bounded witness leaves class, descriptor, weights, and cce0 output unchanged.",
        ],
        "inferences": [
            "The remaining provenance gap is upstream of or at the imported pow call: Windows input bits and UCRT return bits were not captured in the same run.",
            "A PF8-wide deterministic LUT is safer than platform libm only after its entries are grounded by same-run Windows input/output captures.",
        ],
        "recommended_strategy": [
            "Capture XMM0/XMM1 at 0x180002d23 and XMM0 before 0x180002d28 on Windows for the accepted pixel.",
            "If the input bits match, store a keyed UCRT return oracle and investigate the unexpected error before production use.",
            "If the input bits differ, fix the PF8 host adapter/conversion provenance rather than compensating in pow.",
            "For PF8 production, generate a 256-code (or premultiplied code-pair) Windows-grounded sRGB decode table and verify full AE cases.",
            "For PF16/PF32, use captured UCRT boundary vectors plus a deterministic implementation; do not reuse a PF8 LUT as a broad fix.",
        ],
        "claims_not_made": [
            "No Mac plug-in source change",
            "No claim that UCRT pow equals Darwin libm for all inputs",
            "No AE exact claim",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    oracle = report["numerical_oracle"]
    sensitivity = report["bounded_sensitivity"]
    return "\n".join([
        "# OLMSmoother2 imported pow boundary audit - 2026-07-18",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Binary Fact",
        "",
        "The checked AEX imports `api-ms-win-crt-math-l1-1-0.dll!pow`. The call at "
        "`0x180002d23` uses double arguments in `XMM0/XMM1`; `0x180002d28` then executes "
        "`CVTSD2SS`.",
        "",
        "## Numerical Classification",
        "",
        f"- Guest input: `{oracle['input_x_f64_word']}`; exponent: `{oracle['exponent_f64_word']}`.",
        f"- Darwin/Python pow then float conversion: `{oracle['host_after_cvtsd2ss_word']}`.",
        f"- Retained Windows polygon word: `{oracle['windows_retained_word']}`.",
        f"- Difference: `{oracle['retained_delta_f32_ulp']}` float32 ULP.",
        "- A 110-digit Decimal `exp(y*ln(x))` oracle agrees with the Darwin result at the float32 rounding boundary.",
        "- Therefore the retained word cannot presently be classified as a UCRT-only difference for the same input. The Windows pow input and return must be captured in one run.",
        "",
        "## PF8 Sensitivity",
        "",
        f"The bounded natural AEX path replaced exactly `{sensitivity['forced_witness_calls']}` RGB pow returns with the retained word. "
        "Class bytes, descriptor, polygon weights, and final cce0 float words remained bitwise equal. "
        "The polygon RGB difference itself remained visible, proving the test was not inert.",
        "",
        sensitivity["pf8_witness_conclusion"],
        "",
        "## Binary-grounded Strategy",
        "",
        *[f"- {item}" for item in report["recommended_strategy"]],
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/audit_olmsmoother2_imported_pow_boundary_20260718.py",
        "python3 tools/emulation/test_olmsmoother2_imported_pow_boundary_20260718.py",
        "```",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmsmoother2_imported_pow_boundary_20260718.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmsmoother2_imported_pow_boundary_20260718.md")
    args = parser.parse_args()
    report = build_report()
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(report["verdict"])
    print(f"import={report['binary_contract']['import']['dll']}!pow")
    print(f"host_f32={report['numerical_oracle']['host_after_cvtsd2ss_word']}")
    print(f"retained_f32={report['numerical_oracle']['windows_retained_word']}")
    print(f"cce0_equal={report['bounded_sensitivity']['cce0_output_bitwise_equal']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
