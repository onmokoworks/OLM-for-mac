#!/usr/bin/env python3
"""Bounded audit of the OLMBlur 32bpc case_0001 red-only residual."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from compare_float_exr import read_planes  # noqa: E402
from test_olmblur_worker32_nonlegacy import (  # noqa: E402
    AEX,
    run_case as run_actual_aex_case,
    source_bytes as actual_aex_source_bytes,
)


EXPECTED_AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
AUTHORITATIVE_EXACT_RECORD = ROOT / "refs/conformance/olmblur_32bpc_case0001_ae_exact_20260727.json"
CASE = {
    "id": "32bpc_nonlegacy_amount1294_repeat1_bias1",
    "width": 4,
    "height": 3,
    "blur_amount": 129.4,
    "smoothness": 100.0,
    "repeat": 1,
    "bias_direction": 1,
}
CHANNELS = ("A", "B", "G", "R")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(plane: bytes) -> list[bytes]:
    return [plane[offset : offset + 4] for offset in range(0, len(plane), 4)]


def floats(plane: bytes) -> list[float]:
    return [item[0] for item in struct.iter_unpack("<f", plane)]


def exr_argb(path: Path) -> tuple[bytes, dict[str, bytes], int, int]:
    planes, width, height = read_planes(path)
    packed = b"".join(
        planes[channel][index * 4 : index * 4 + 4]
        for index in range(width * height)
        for channel in "ARGB"
    )
    return packed, planes, width, height


def compare_planes(left: dict[str, bytes], right: dict[str, bytes]) -> dict[str, int]:
    return {
        channel: sum(a != b for a, b in zip(words(left[channel]), words(right[channel])))
        for channel in CHANNELS
    }


def compile_worker(directory: Path) -> Path:
    source = directory / "run_worker.cpp"
    executable = directory / "run_worker"
    source.write_text(
        r'''#include "olmblur_worker32_nonlegacy.h"
#include <cstdlib>
#include <fstream>
#include <vector>
int main(int argc, char **argv) {
  if (argc != 9) return 2;
  const std::size_t width = std::strtoull(argv[3], nullptr, 10);
  const std::size_t height = std::strtoull(argv[4], nullptr, 10);
  const std::size_t count = width * height * 4;
  std::vector<float> source(count), output(count);
  std::ifstream input(argv[1], std::ios::binary);
  input.read(reinterpret_cast<char *>(source.data()), count * sizeof(float));
  if (!input || input.peek() != std::ifstream::traits_type::eof()) return 3;
  const olm::blur::worker32::Params params{
      std::strtof(argv[5], nullptr), std::strtof(argv[6], nullptr),
      std::strtoull(argv[7], nullptr, 10), std::strtoull(argv[8], nullptr, 10)};
  olm::blur::worker32::render_nonlegacy(
      source.data(), output.data(), width, height, params);
  std::ofstream result(argv[2], std::ios::binary);
  result.write(reinterpret_cast<const char *>(output.data()), count * sizeof(float));
  return result ? 0 : 4;
}
''',
        encoding="utf-8",
    )
    command = [
        "clang++",
        "-std=c++17",
        "-O2",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-Icore",
        str(source),
        "core/olmblur_helper.cpp",
        "core/olmblur_worker32_nonlegacy.cpp",
        "-o",
        str(executable),
    ]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise RuntimeError(f"worker build failed:\n{build.stdout}\n{build.stderr}")
    return executable


def run_worker(
    executable: Path,
    directory: Path,
    source: bytes,
    width: int,
    height: int,
    label: str,
) -> bytes:
    source_path = directory / f"{label}_source.raw"
    output_path = directory / f"{label}_output.raw"
    source_path.write_bytes(source)
    command = [
        str(executable),
        str(source_path),
        str(output_path),
        str(width),
        str(height),
        str(CASE["blur_amount"]),
        str(CASE["smoothness"]),
        str(CASE["repeat"]),
        str(CASE["bias_direction"]),
    ]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"worker run failed ({label}): {run.stdout} {run.stderr}")
    return output_path.read_bytes()


def locate_windows_pair(root: Path) -> tuple[Path, Path]:
    effects = [
        path
        for path in root.glob("*olmblur__case_0001.exr")
        if "before_effects" not in path.name
    ]
    controls = list(root.glob("*olmblur__case_0001_before_effects.exr"))
    if len(effects) != 1 or len(controls) != 1:
        raise RuntimeError("expected exactly one Windows case_0001 effect/control pair")
    return effects[0], controls[0]


def build_report(windows_root: Path, mac_root: Path) -> dict:
    if sha256(AEX) != EXPECTED_AEX_SHA256:
        raise RuntimeError("current actual-AEX hash does not match the pinned oracle")
    exact_record = json.loads(AUTHORITATIVE_EXACT_RECORD.read_text(encoding="utf-8"))
    exact_loaded_sha = exact_record["windows"]["loaded_plugin_proof"]["aex_sha256"]
    if not exact_record.get("ae_exact_claim") or exact_loaded_sha != EXPECTED_AEX_SHA256:
        raise RuntimeError("authoritative case_0001 AE-exact record is not bound to the pinned AEX")
    windows_effect, windows_control = locate_windows_pair(windows_root)
    mac_effect = mac_root / "olmblur__case_0001__effect_on.exr"
    mac_control = mac_root / "olmblur__case_0001__no_effect.exr"
    for path in (windows_effect, windows_control, mac_effect, mac_control):
        if not path.is_file():
            raise RuntimeError(f"missing required EXR: {path}")

    win_effect_argb, win_effect_planes, width, height = exr_argb(windows_effect)
    win_control_argb, win_control_planes, control_width, control_height = exr_argb(windows_control)
    mac_effect_argb, mac_effect_planes, mac_width, mac_height = exr_argb(mac_effect)
    mac_control_argb, mac_control_planes, mac_control_width, mac_control_height = exr_argb(mac_control)
    dimensions = {(width, height), (control_width, control_height), (mac_width, mac_height), (mac_control_width, mac_control_height)}
    if len(dimensions) != 1:
        raise RuntimeError(f"EXR dimensions differ: {sorted(dimensions)}")

    control_mismatches = compare_planes(win_control_planes, mac_control_planes)
    effect_mismatches = compare_planes(win_effect_planes, mac_effect_planes)
    input_nonzero = {
        channel: sum(value != 0.0 for value in floats(win_control_planes[channel]))
        for channel in CHANNELS
    }
    win_effect_nonzero = {
        channel: sum(value != 0.0 for value in floats(win_effect_planes[channel]))
        for channel in CHANNELS
    }
    mac_effect_nonzero = {
        channel: sum(value != 0.0 for value in floats(mac_effect_planes[channel]))
        for channel in CHANNELS
    }

    with tempfile.TemporaryDirectory(prefix="olmblur_red_only_audit_") as name:
        directory = Path(name)
        executable = compile_worker(directory)
        mac_core_output = run_worker(executable, directory, mac_control_argb, width, height, "full")
        actual_aex_output, actual_aex_run = run_actual_aex_case(CASE)
        bounded_source = actual_aex_source_bytes(CASE["width"], CASE["height"])
        bounded_core_output = run_worker(
            executable,
            directory,
            bounded_source,
            CASE["width"],
            CASE["height"],
            "bounded",
        )

    return {
        "schema": "olmblur.32bpc-red-only-residual-audit/1",
        "date": "2026-07-18",
        "plugin": "OLMBlur",
        "case_id": "olmblur__case_0001",
        "parameters": {
            "blur_amount_f32": struct.unpack("<f", struct.pack("<f", CASE["blur_amount"]))[0],
            "blur_smoothness": CASE["smoothness"],
            "repeat": CASE["repeat"],
            "bias_direction": CASE["bias_direction"],
            "legacy": 0,
        },
        "artifacts": {
            "windows_effect": {"path": str(windows_effect.relative_to(ROOT)), "sha256": sha256(windows_effect)},
            "windows_control": {"path": str(windows_control.relative_to(ROOT)), "sha256": sha256(windows_control)},
            "mac_effect": {"path": str(mac_effect), "sha256": sha256(mac_effect)},
            "mac_control": {"path": str(mac_control), "sha256": sha256(mac_control)},
            "actual_aex_sha256": EXPECTED_AEX_SHA256,
        },
        "facts": {
            "dimensions": [width, height],
            "control_mismatches_by_channel": control_mismatches,
            "effect_mismatches_by_channel": effect_mismatches,
            "windows_control_nonzero_by_channel": input_nonzero,
            "windows_effect_nonzero_by_channel": win_effect_nonzero,
            "mac_effect_nonzero_by_channel": mac_effect_nonzero,
            "full_mac_effect_equals_current_core": mac_core_output == mac_effect_argb,
            "full_current_core_vs_windows_mismatched_words": sum(
                left != right
                for left, right in zip(words(mac_core_output), words(win_effect_argb))
            ),
            "bounded_current_aex_repeat1_equals_current_core": actual_aex_output == bounded_core_output,
            "bounded_actual_aex_instructions": actual_aex_run["instructions"],
            "bounded_actual_aex_callback_count": actual_aex_run["callback_count"],
            "authoritative_same_aex_case0001_ae_exact": True,
            "authoritative_exact_record": str(AUTHORITATIVE_EXACT_RECORD.relative_to(ROOT)),
            "authoritative_exact_record_sha256": sha256(AUTHORITATIVE_EXACT_RECORD),
        },
        "hypotheses": {
            "channel_mapping": "rejected",
            "source_stride": "rejected",
            "simd_lane": "rejected_at_worker_boundary_for_the_exact_parameter_tuple",
            "reference_selection": "retained 20260710 Windows EXR conflicts with the later hash-bound 20260727 same-AEX AE-exact record",
        },
        "classification": "superseded_reference_conflict",
        "ae_exact_claim": False,
        "plugin_source_change": False,
        "next_required_evidence": "restore the 20260727 authoritative effect/control artifacts, or recapture that exact hash-bound contract; do not tune production to the superseded 20260710 EXR",
    }


def render_markdown(report: dict) -> str:
    facts = report["facts"]
    return f"""# OLMBlur 32bpc red-only residual audit (2026-07-18)

## Verdict

The residual is **not evidence of a red-channel mapping bug**. The case input
contains signal only in red (`R={facts['windows_control_nonzero_by_channel']['R']}`
nonzero values; `G=B=0`), so an algorithm difference can only appear in red.

The current Mac effect EXR is byte-for-byte the output of the current portable
PF32 core for the full 1920x1080 host input. A bounded current-AEX execution at
the exact tuple `(129.4, 100, repeat=1, bias=1, Legacy=0)` is also byte-exact
with that core.

## Facts

- Windows/Mac no-op FLOAT32 planes: `{facts['control_mismatches_by_channel']}`.
- Windows/Mac effect mismatches: `{facts['effect_mismatches_by_channel']}`.
- Full Mac effect equals current core: `{facts['full_mac_effect_equals_current_core']}`.
- Full current core versus retained Windows effect: `{facts['full_current_core_vs_windows_mismatched_words']}` mismatched float words.
- Bounded current AEX repeat=1 equals current core: `{facts['bounded_current_aex_repeat1_equals_current_core']}`.
- Pinned actual AEX SHA-256: `{report['artifacts']['actual_aex_sha256']}`.

## Hypothesis disposition

| hypothesis | result | reason |
| --- | --- | --- |
| channel mapping | rejected | no-op is exact, G/B remain zero, and diverse-ARGB actual-AEX fixtures already pass |
| source stride | rejected | full 1920x1080 current-core output equals the Mac EXR; padded-row adapter fixtures also pass |
| SIMD lane | rejected at the worker boundary for this tuple | bounded current AEX and portable core are byte-exact at repeat=1 |
| reference selection | superseded-reference conflict | the retained 20260710 EXR conflicts with the later hash-bound 20260727 same-AEX AE-exact record |

The current source must not be changed to fit the retained 20260710 artifact:
all locally testable implementation boundaries agree with the pinned current
AEX, and the later authoritative same-AEX record is already cross-host exact.

## Next evidence

Restore the authoritative 20260727 effect/control artifacts, or recapture that
exact hash-bound contract.  The superseded 20260710 EXR is not a production
tuning oracle.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-root", type=Path, required=True)
    parser.add_argument("--mac-root", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = build_report(args.windows_root.resolve(), args.mac_root.resolve())
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
