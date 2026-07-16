#!/usr/bin/env python3
"""Gate double-exp/float-cast weight generation against case_0004 capture."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmblur_case0004_coefficient_sensitivity import (  # noqa: E402
    CALLER_REPORT,
    CALLER_REPORT_SHA256,
    caller_coefficients,
    compose,
    predict_standard_writer,
    require_report,
)
from probe_olmblur_case0004_staged_helper_replay import (  # noqa: E402
    compile_portable,
    expected_staging,
    load_input,
)

PROBE = ROOT / "tools/emulation/probe_olmblur_case0004_exp_double_candidate.cpp"
PRODUCTION_SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
PRODUCTION_SOURCE_SHA256 = "55def455a29f72c04748a784bcd598ddeecb84ec25d475376ea93b6e838e3b02"
REPORT_JSON = ROOT / "refs/conformance/olmblur_case0004_exp_double_candidate_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0004_exp_double_candidate_20260716.md"


def parse_candidate(output: str) -> list[dict]:
    pattern = re.compile(r"ITER (\d+) RADIUS (\d+) WEIGHTS((?: [0-9a-f]{8})+)")
    result = []
    for line in output.splitlines():
        match = pattern.fullmatch(line)
        if not match:
            raise AssertionError(f"unexpected candidate output: {line!r}")
        words = [int(word, 16) for word in match.group(3).split()]
        radius = int(match.group(2))
        if len(words) != radius + 1:
            raise AssertionError(f"candidate coefficient count differs at iteration {match.group(1)}")
        result.append({
            "iteration": int(match.group(1)), "radius": radius, "words": words,
            "weights": struct.pack(f"<{len(words)}I", *words),
        })
    return result


def compare_words(declared: list[dict], candidate: list[dict]) -> tuple[int, dict | None, list[dict]]:
    compared = 0
    first = None
    iterations = []
    if len(declared) != len(candidate):
        return 0, {"kind": "iteration_count", "declared": len(declared), "candidate": len(candidate)}, []
    for aex, generated in zip(declared, candidate):
        if (aex["iteration"], aex["radius"]) != (generated["iteration"], generated["radius"]):
            return compared, {"kind": "radius", "iteration": aex["iteration"],
                              "declared": aex["radius"], "candidate": generated["radius"]}, iterations
        mismatch_count = 0
        for index, (declared_word, candidate_word) in enumerate(zip(aex["words"], generated["words"])):
            compared += 1
            if declared_word != candidate_word:
                mismatch_count += 1
                if first is None:
                    first = {"kind": "coefficient_word", "iteration": aex["iteration"],
                             "index": index, "index_base": 0,
                             "declared_word": f"0x{declared_word:08x}",
                             "candidate_word": f"0x{candidate_word:08x}"}
        iterations.append({
            "iteration": aex["iteration"], "radius": aex["radius"],
            "coefficient_count": len(aex["words"]), "mismatch_count": mismatch_count,
            "declared_sha256": hashlib.sha256(aex["weights"]).hexdigest(),
            "candidate_sha256": hashlib.sha256(generated["weights"]).hexdigest(),
        })
    return compared, first, iterations


def main() -> int:
    production = PRODUCTION_SOURCE.read_text(encoding="utf-8")
    if hashlib.sha256(PRODUCTION_SOURCE.read_bytes()).hexdigest() != PRODUCTION_SOURCE_SHA256:
        raise AssertionError("OLMBlur production source differs from the integrated candidate")
    production_snippet = (
        "const float exponent = -(float)(k*k) / denom;\n"
        "\t\t\t\tweights[k] = (float)exp((double)exponent);"
    )
    if production.count(production_snippet) != 1:
        raise AssertionError("OLMBlur double-exp production contract is missing or ambiguous")
    caller_report = require_report(
        CALLER_REPORT, CALLER_REPORT_SHA256, "olmblur.case0004.staged-helper-replay/1"
    )
    declared = caller_coefficients(caller_report)
    params = caller_report["parameters"]
    amount_bits = struct.unpack("<I", struct.pack("<f", params["blur_amount"]))[0]
    compiler = os.environ.get("CXX", "c++")

    pf16, input_identity = load_input()
    plane, flags = expected_staging(pf16)
    if hashlib.sha256(plane).hexdigest() != caller_report["staging"]["plane_sha256"]:
        raise AssertionError("reconstructed staged plane differs")
    if hashlib.sha256(flags).hexdigest() != caller_report["staging"]["flags_sha256"]:
        raise AssertionError("reconstructed staged flags differ")

    with tempfile.TemporaryDirectory(prefix="olmblur_case0004_exp_double_candidate_") as temporary:
        temp = Path(temporary)
        generation_executable = temp / "exp_double_candidate"
        generation_compile = [compiler, "-std=c++17", "-O2", "-ffp-contract=off",
                              str(PROBE), "-o", str(generation_executable)]
        build = subprocess.run(generation_compile, cwd=ROOT, text=True, capture_output=True, check=False)
        if build.returncode:
            raise AssertionError(f"candidate compile failed: {build.stderr.strip()}")
        run = subprocess.run([str(generation_executable), f"{amount_bits:08x}", str(params["repeat"])],
                             cwd=ROOT, text=True, capture_output=True, check=False)
        if run.returncode:
            raise AssertionError(f"candidate generation failed: {run.stderr.strip()}")
        candidate = parse_candidate(run.stdout)
        compared, first_mismatch, iteration_comparisons = compare_words(declared, candidate)

        portable_executable = temp / "portable_helper"
        portable_compile = compile_portable(portable_executable)
        cone = compose(portable_executable, temp, "candidate", plane, flags, candidate)

    if compared != 177:
        raise AssertionError(f"candidate comparison did not cover 177 words: {compared}")
    coefficient_exact = first_mismatch is None
    final = {}
    for point, bits in cone["final_bits_hex"].items():
        final[point] = {
            "pre_store_bits_hex": bits,
            "standard_writer_predicted_rgb_words": predict_standard_writer(bits),
        }
    compiler_version = subprocess.check_output([compiler, "--version"], text=True).splitlines()[0]
    report = {
        "schema": "olmblur.case0004.exp-double-candidate-gate/1",
        "status": "pass_candidate_gate",
        "classification": "coefficient_exact" if coefficient_exact else "coefficient_mismatch",
        "platform": {"system": platform.system(), "architecture": platform.machine(),
                     "compiler": compiler_version},
        "identity": {"caller_report": str(CALLER_REPORT.relative_to(ROOT)),
                     "caller_report_sha256": CALLER_REPORT_SHA256, "input": input_identity,
                     "production_source": str(PRODUCTION_SOURCE.relative_to(ROOT)),
                     "production_source_sha256": PRODUCTION_SOURCE_SHA256},
        "candidate": "current powf/pow/radius/sigma/denom order; x_f32 unchanged; weight=static_cast<float>(std::exp(static_cast<double>(x_f32)))",
        "generation_compile_command": [compiler, "-std=c++17", "-O2", "-ffp-contract=off",
                                       str(PROBE.relative_to(ROOT)), "-o",
                                       "<temporary>/exp_double_candidate"],
        "portable_compile_command": portable_compile,
        "radius_sequence": [item["radius"] for item in candidate],
        "coefficient_words_compared": compared,
        "all_coefficient_words_exact": coefficient_exact,
        "first_mismatch": first_mismatch,
        "iterations": iteration_comparisons,
        "portable_full_cone": {"execution": "portable_only", "stages": cone["stages"], "final": final},
        "production_integration": "source-contract-exact; arm64/x86_64 Debug build validated separately",
        "claim_limit": "Mac production formula and portable sensitivity only; not Windows CRT truth or AE exact.",
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# OLMBlur case_0004 double-exp candidate gate", "", "## FACT", "",
        f"- Classification: `{report['classification']}`.",
        f"- Platform: `{report['platform']['system']} {report['platform']['architecture']}`; compiler `{compiler_version}`.",
        f"- Raw coefficient words exact: `{coefficient_exact}` (`{compared}/177` compared).",
        f"- First mismatch: `{first_mismatch}`.",
        f"- Radius sequence: `{report['radius_sequence']}`.",
        "- Candidate keeps current powf/pow/radius/sigma/denom order and replaces only expf(x_f32) with `static_cast<float>(std::exp(static_cast<double>(x_f32)))`.",
        "", "## Full Cone", "",
    ]
    for point, values in final.items():
        lines.append(f"- `{point}`: pre-store `{values['pre_store_bits_hex']}`; predicted RGB words `{values['standard_writer_predicted_rgb_words']}`.")
    lines.extend([
        "", "## INFERENCE", "",
        f"- Production source `{PRODUCTION_SOURCE.relative_to(ROOT)}` is pinned to `{PRODUCTION_SOURCE_SHA256}` and contains the candidate exactly once.",
        "- The production source is integrated and builds for arm64/x86_64; Mac AE output remains unvalidated.",
        "- The cone replay is portable-only, and neither coefficients nor outputs are labeled Windows truth.",
        "", "## Test", "", "```text",
        "python3 tools/emulation/test_olmblur_case0004_exp_double_candidate_20260716.py",
        "```", "", "## Changed files", "",
        "- `tools/emulation/probe_olmblur_case0004_exp_double_candidate.cpp` (new)",
        "- `tools/emulation/test_olmblur_case0004_exp_double_candidate_20260716.py` (new)",
        "- `refs/conformance/olmblur_case0004_exp_double_candidate_20260716.json` (new)",
        "- `refs/conformance/olmblur_case0004_exp_double_candidate_20260716.md` (new)",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "classification": report["classification"],
                      "coefficient_words": f"{compared}/177", "all_exact": coefficient_exact,
                      "final": final, "report_json": str(REPORT_JSON.relative_to(ROOT)),
                      "report_md": str(REPORT_MD.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
