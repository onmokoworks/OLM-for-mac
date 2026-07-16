#!/usr/bin/env python3
"""Compare current Mac OLMBlur radius/weights with captured actual-AEX words."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
SOURCE_SHA256 = "d690adb9e6c4993caf50a16aed8d91b704f0a4622bc987601ddf630de4424346"
CAPTURE = ROOT / "refs/conformance/olmblur_case0004_staged_helper_replay_20260716.json"
CAPTURE_SHA256 = "015bd884f5f7186a6923c74e95e009c4d9709151a5d537c976ee741f1754f878"
PROBE = ROOT / "tools/emulation/probe_olmblur_case0004_mac_generation.cpp"
REPORT_JSON = ROOT / "refs/conformance/olmblur_case0004_mac_generation_audit_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0004_mac_generation_audit_20260716.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_iterations(report: dict) -> list[dict]:
    calls = report["staging"]["helper_calls_captured"]
    if len(calls) != 48:
        raise AssertionError(f"captured helper call count differs: {len(calls)}")
    result = []
    for iteration in range(4):
        group = calls[iteration * 12:(iteration + 1) * 12]
        if [item["direction"] for item in group] != ["horizontal"] * 6 + ["vertical"] * 6:
            raise AssertionError(f"captured direction order differs at iteration {iteration + 1}")
        radii = {item["radius"] for item in group}
        weights = {item["weights_hex"] for item in group}
        if len(radii) != 1 or len(weights) != 1:
            raise AssertionError(f"captured H/V generation values disagree at iteration {iteration + 1}")
        raw = bytes.fromhex(weights.pop())
        radius = radii.pop()
        if len(raw) != (radius + 1) * 4:
            raise AssertionError(f"captured coefficient count differs at iteration {iteration + 1}")
        result.append({
            "iteration": iteration + 1,
            "radius": radius,
            "coefficient_words_hex": [f"0x{word:08x}" for word in struct.unpack(f"<{radius + 1}I", raw)],
            "coefficient_sha256": hashlib.sha256(raw).hexdigest(),
        })
    return result


def parse_mac_output(output: str) -> tuple[str, list[dict]]:
    lines = output.splitlines()
    if not lines or not re.fullmatch(r"DECAY [0-9a-f]{8}", lines[0]):
        raise AssertionError(f"unexpected Mac probe header: {lines[:1]!r}")
    result = []
    pattern = re.compile(
        r"ITER (\d+) RADIUS (\d+) RADIUS_D ([0-9a-f]{16}) "
        r"SIGMA ([0-9a-f]{8}) DENOM ([0-9a-f]{8}) WEIGHTS((?: [0-9a-f]{8})+)"
    )
    for line in lines[1:]:
        match = pattern.fullmatch(line)
        if not match:
            raise AssertionError(f"unexpected Mac probe output: {line!r}")
        words = [f"0x{word}" for word in match.group(6).split()]
        radius = int(match.group(2))
        if len(words) != radius + 1:
            raise AssertionError(f"Mac coefficient count differs at iteration {match.group(1)}")
        raw = struct.pack(f"<{len(words)}I", *(int(word, 16) for word in words))
        result.append({
            "iteration": int(match.group(1)),
            "radius": radius,
            "radius_d_bits_hex": f"0x{match.group(3)}",
            "sigma_bits_hex": f"0x{match.group(4)}",
            "denom_bits_hex": f"0x{match.group(5)}",
            "coefficient_words_hex": words,
            "coefficient_sha256": hashlib.sha256(raw).hexdigest(),
        })
    return f"0x{lines[0].split()[1]}", result


def first_mismatch(actual: list[dict], mac: list[dict]) -> dict | None:
    for index in range(max(len(actual), len(mac))):
        iteration = index + 1
        if index >= len(actual) or index >= len(mac):
            return {"kind": "iteration_count", "iteration": iteration,
                    "actual_aex_iterations": len(actual), "mac_iterations": len(mac)}
        aex, candidate = actual[index], mac[index]
        if aex["radius"] != candidate["radius"]:
            return {"kind": "radius", "iteration": iteration,
                    "actual_aex_radius": aex["radius"], "mac_radius": candidate["radius"]}
        aex_words = aex["coefficient_words_hex"]
        mac_words = candidate["coefficient_words_hex"]
        for coefficient in range(max(len(aex_words), len(mac_words))):
            if coefficient >= len(aex_words) or coefficient >= len(mac_words):
                return {"kind": "coefficient_count", "iteration": iteration, "index": coefficient,
                        "index_base": 0,
                        "actual_aex_count": len(aex_words), "mac_count": len(mac_words)}
            if aex_words[coefficient] != mac_words[coefficient]:
                return {"kind": "coefficient_word", "iteration": iteration, "index": coefficient,
                        "index_base": 0,
                        "actual_aex_word": aex_words[coefficient], "mac_word": mac_words[coefficient]}
    return None


def main() -> int:
    if sha256(SOURCE) != SOURCE_SHA256:
        raise AssertionError("mac/OLMBlur/OLMBlur.cpp differs from pinned formula source")
    if sha256(CAPTURE) != CAPTURE_SHA256:
        raise AssertionError("captured actual-AEX schedule report differs")
    capture_report = json.loads(CAPTURE.read_text())
    if capture_report.get("schema") != "olmblur.case0004.staged-helper-replay/1":
        raise AssertionError("captured schedule schema differs")
    actual = capture_iterations(capture_report)
    params = capture_report["parameters"]
    amount_bits = struct.unpack("<I", struct.pack("<f", params["blur_amount"]))[0]

    compiler = os.environ.get("CXX", "c++")
    with tempfile.TemporaryDirectory(prefix="olmblur_case0004_mac_generation_") as temporary:
        executable = Path(temporary) / "mac_generation"
        compile_command = [compiler, "-std=c++17", "-O2", "-ffp-contract=off", str(PROBE), "-o", str(executable)]
        build = subprocess.run(compile_command, cwd=ROOT, text=True, capture_output=True, check=False)
        if build.returncode:
            raise AssertionError(f"Mac generation probe compile failed: {build.stderr.strip()}")
        run = subprocess.run([str(executable), f"{amount_bits:08x}", str(params["repeat"])],
                             cwd=ROOT, text=True, capture_output=True, check=False)
        if run.returncode:
            raise AssertionError(f"Mac generation probe failed: {run.stderr.strip()}")
    decay_bits, mac = parse_mac_output(run.stdout)
    mismatch = first_mismatch(actual, mac)
    compiler_version = subprocess.check_output([compiler, "--version"], text=True).splitlines()[0]
    report = {
        "schema": "olmblur.case0004.mac-radius-weight-generation-audit/1",
        "status": "pass_audit",
        "classification": "exact" if mismatch is None else "generation_mismatch",
        "platform": {"system": platform.system(), "architecture": platform.machine(),
                     "compiler": compiler_version},
        "identity": {
            "production_source": str(SOURCE.relative_to(ROOT)), "production_source_sha256": SOURCE_SHA256,
            "captured_schedule": str(CAPTURE.relative_to(ROOT)), "captured_schedule_sha256": CAPTURE_SHA256,
            "formula_lines": [1257, 1267],
        },
        "parameters": {"blur_amount": params["blur_amount"], "blur_amount_f32_bits_hex": f"0x{amount_bits:08x}",
                       "repeat": params["repeat"]},
        "compile_command": [compiler, "-std=c++17", "-O2", "-ffp-contract=off",
                            str(PROBE.relative_to(ROOT)), "-o", "<temporary>/mac_generation"],
        "mac_decay_bits_hex": decay_bits,
        "actual_aex": actual,
        "mac_production_formula": mac,
        "first_mismatch": mismatch,
        "claim_limit": "Mac source-formula versus AEX guest orchestration using host-backed Python math callbacks; the captured coefficients are not Windows CRT truth. No production change or AE exactness evidence.",
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    mismatch_text = "none" if mismatch is None else json.dumps(mismatch, sort_keys=True)
    lines = [
        "# OLMBlur case_0004 Mac radius/weight generation audit", "", "## FACT", "",
        f"- Classification: `{report['classification']}`.",
        f"- Platform: `{report['platform']['system']} {report['platform']['architecture']}`; compiler `{compiler_version}`.",
        f"- Production formula: `{report['identity']['production_source']}:1257-1267` / `{SOURCE_SHA256}`.",
        f"- Captured AEX-guest radii: `{[item['radius'] for item in actual]}`.",
        f"- Current Mac formula radii: `{[item['radius'] for item in mac]}`.",
        f"- First mismatch: `{mismatch_text}`.", "", "## Iterations", "",
    ]
    for aex, candidate in zip(actual, mac):
        lines.append(
            f"- Iteration `{aex['iteration']}`: radius AEX/Mac `{aex['radius']}/{candidate['radius']}`; "
            f"coefficient SHA-256 AEX `{aex['coefficient_sha256']}`, Mac `{candidate['coefficient_sha256']}`."
        )
    lines.extend([
        "", "## INFERENCE", "",
        "- This audit compares raw float32 coefficient words generated by the exact checked-in Mac source formula against AEX guest control flow using the emulator's host-backed Python math callbacks.",
        "- The captured coefficient bytes are not Windows CRT `powf/pow/expf` truth. The 1 ULP delta is a libm-backend candidate and does not justify a production change.",
        "- Python performs parsing and raw-word comparison only; it is not a numerical oracle.",
        "- No production change, AE-exact claim, Windows/NAS/SSH execution, or full image-processing replay is included.",
        "", "## Test", "", "```text",
        "python3 tools/emulation/test_olmblur_case0004_mac_generation_audit_20260716.py",
        "```", "", "## Changed files", "",
        "- `tools/emulation/probe_olmblur_case0004_mac_generation.cpp` (new)",
        "- `tools/emulation/test_olmblur_case0004_mac_generation_audit_20260716.py` (new)",
        "- `refs/conformance/olmblur_case0004_mac_generation_audit_20260716.json` (new)",
        "- `refs/conformance/olmblur_case0004_mac_generation_audit_20260716.md` (new)",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "classification": report["classification"],
                      "first_mismatch": mismatch, "report_json": str(REPORT_JSON.relative_to(ROOT)),
                      "report_md": str(REPORT_MD.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
