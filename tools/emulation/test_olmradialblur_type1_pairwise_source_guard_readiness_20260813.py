#!/usr/bin/env python3
"""Bind the four retained Type-1 pairwise fixture sources before promotion."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
PF8_TOOL = ROOT / "tools/emulation/test_olmradialblur_noise_type1_pf8_combo_actual_aex_20260811.py"
PF16_TOOL = ROOT / "tools/emulation/test_olmradialblur_noise_type1_pf16_pairwise_actual_aex_20260811.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_pairwise_source_guard_readiness_20260813.json"
NOTE = REPORT.with_suffix(".md")
PROBE = ROOT / "tools/emulation/probe_olmradialblur_type1_pairwise_source_guard_20260813.cpp"
EXPECTED = {
    "PF8_9x7": "3b62de8577b33598ede56c0a3ca5bc636a40b9bf7bc9599000d9840b531eeffe",
    "PF16_9x7": "5c853513cbbbdab275383c7aa6b6d82e0f7fef95565a7d0d4f6dd04426a75b33",
    "PF8_32x18": "85143eda82a237f32b5c9b1d3cf5f73a121bffa9eaba6e05d4728bda4216f000",
    "PF16_32x18": "c9d92745cba73fde78d7ad5868d643ad7a88b1dd481e6caacfc7c945ae153b3c",
}
STATUS = "pass_pairwise_source_guard_integrated_hostless"
RUN_SHA256 = "a319697bf043a51ecddea2eff31e2f9769e42c339870cc922e55648fbb14b84d"
CLAIM_BOUNDARY = {
    "proven": "four retained PF8/PF16 pairwise fixture identities admit 16 cells unchanged and 12 source mutations fail closed on arm64 and x86_64",
    "not_proven": [
        "arbitrary source content",
        "the remaining 90 rows of the 98-cell Type1 projection",
        "PF32 pairwise route, which is not in this pairwise family",
        "native After Effects output",
    ],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def active_hash(raw: bytes, rowbytes: int, active: int, height: int) -> str:
    return hashlib.sha256(b"".join(
        raw[y * rowbytes:y * rowbytes + active] for y in range(height)
    )).hexdigest()


def reconstruct() -> dict[str, str]:
    pf8 = load(PF8_TOOL, "radial_pairwise_pf8_source")
    pf16 = load(PF16_TOOL, "radial_pairwise_pf16_source")
    result = {}
    for width, height in ((9, 7), (32, 18)):
        target = pf8.configure("rotation", width, height, 25, 1, 0, 3)
        rowbytes8 = width * 4 + 8
        result[f"PF8_{width}x{height}"] = active_hash(
            target.source_frame(), rowbytes8, width * 4, height
        )
        rowbytes16 = 80 if width == 9 else 272
        result[f"PF16_{width}x{height}"] = active_hash(
            pf16.frame(width, height, rowbytes16), rowbytes16, width * 8, height
        )
    return result


def run_probe(arch: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix=f"radial-pairwise-source-{arch}.") as raw:
        executable = Path(raw) / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [
            "clang++", "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-isysroot", sdk,
            "-Wno-pragma-pack", "-Wno-deprecated-declarations",
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            "-I", str(ROOT / "core"), "-I", str(ROOT / "mac/OLMRadialBlur"),
            str(PROBE), str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"),
            "-framework", "Cocoa", "-o", str(executable),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"{arch} probe rc={run.returncode}: {run.stdout} {run.stderr}")
    if hashlib.sha256(run.stdout.encode()).hexdigest() != RUN_SHA256:
        raise RuntimeError(f"{arch} transcript drift")
    lines = run.stdout.splitlines()
    if len(lines) != 28 or sum(line.startswith("POS ") for line in lines) != 16 or \
            sum(line.startswith("NEG ") for line in lines) != 12:
        raise RuntimeError(f"{arch} row count drift")
    return lines


def generate() -> dict:
    hashes = reconstruct()
    if hashes != EXPECTED:
        raise RuntimeError(f"pairwise fixture source drift: {hashes}")
    production = SOURCE.read_text(encoding="utf-8")
    match = re.search(
        r"const bool use_aex_typed_noise_type1_pairwise\s*=.*?;",
        production, re.DOTALL,
    )
    if not match:
        raise RuntimeError("pairwise admission predicate missing")
    block = match.group(0)
    source_guard_present = "MatchesRadialType1PairwiseFixture<PixelT>(input)" in block
    if not source_guard_present:
        raise RuntimeError("pairwise source guard is not integrated")
    runs = [{"arch": arch, "lines": run_probe(arch), "transcript_sha256": RUN_SHA256}
            for arch in ("arm64", "x86_64")]
    return {
        "schema": "olmradialblur.type1-pairwise-source-guard-readiness/1",
        "status": STATUS,
        "authorities": {
            "production_sha256": sha(SOURCE),
            "pf8_generator_sha256": sha(PF8_TOOL),
            "pf16_generator_sha256": sha(PF16_TOOL),
            "probe_sha256": sha(PROBE),
        },
        "active_source_sha256": hashes,
        "current_public_admission_source_guard_present": True,
        "runs": runs,
        "promotion_state": "hostless_source_guard_and_universal_candidate_closed_install_pending",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def validate(report: dict) -> None:
    if set(report) != {
        "schema", "status", "authorities", "active_source_sha256",
        "current_public_admission_source_guard_present", "runs", "promotion_state",
        "claim_boundary",
    }:
        raise RuntimeError("schema drift")
    if report["schema"] != "olmradialblur.type1-pairwise-source-guard-readiness/1":
        raise RuntimeError("schema value drift")
    if report["status"] != STATUS or report["active_source_sha256"] != EXPECTED:
        raise RuntimeError("status or source identity drift")
    if report["authorities"] != {
        "production_sha256": sha(SOURCE),
        "pf8_generator_sha256": sha(PF8_TOOL),
        "pf16_generator_sha256": sha(PF16_TOOL),
        "probe_sha256": sha(PROBE),
    }:
        raise RuntimeError("authority drift")
    if report["current_public_admission_source_guard_present"] is not True:
        raise RuntimeError("guard state drift")
    if report["promotion_state"] != "hostless_source_guard_and_universal_candidate_closed_install_pending":
        raise RuntimeError("promotion state drift")
    if [row.get("arch") for row in report["runs"]] != ["arm64", "x86_64"]:
        raise RuntimeError("architecture run drift")
    for run in report["runs"]:
        if set(run) != {"arch", "lines", "transcript_sha256"} or \
                run["transcript_sha256"] != RUN_SHA256 or len(run["lines"]) != 28:
            raise RuntimeError("run transcript drift")
        if hashlib.sha256(("\n".join(run["lines"]) + "\n").encode()).hexdigest() != RUN_SHA256:
            raise RuntimeError("run transcript content drift")
    if report["claim_boundary"] != CLAIM_BOUNDARY:
        raise RuntimeError("boundary claim drift")


def markdown(report: dict) -> str:
    rows = "\n".join(f"- {name}: `{value}`" for name, value in EXPECTED.items())
    return f"""# RadialBlur Type1 pairwise source-guard readiness (2026-08-13)

Status: `{STATUS}`

The retained PF8/PF16 pairwise fixture sources reconstruct to four exact active-row identities:

{rows}

Current production now requires these exact active-row identities. Both arm64 and x86_64 hostless probes retain all 16 pairwise outputs and reject first/middle/last mutations for each source (12 controls) with input unchanged and output untouched. A strict/deep-valid ad-hoc Universal candidate is complete; install and installed replay remain pending. AE was not launched.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fresh = generate(); validate(fresh)
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(markdown(fresh))
    else:
        saved = json.loads(REPORT.read_text()); validate(saved)
        if saved != fresh or NOTE.read_text() != markdown(saved):
            raise RuntimeError("persisted drift")
    print("PASS_OLMRADIALBLUR_TYPE1_PAIRWISE_SOURCE_GUARD_READINESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
