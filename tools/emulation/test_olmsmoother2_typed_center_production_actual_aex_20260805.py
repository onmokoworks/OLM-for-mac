#!/usr/bin/env python3
"""Connect production RenderBits to actual-AEX typed workers at a bounded center sample."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import test_olmsmoother2_typed_writeback_20260717 as aex_test


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/emulation/olmsmoother2_typed_center_production_harness_20260805.cpp"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother2_typed_center_production_actual_aex_20260805.json"
DOC = ROOT / "refs/conformance/olmsmoother2_typed_center_production_actual_aex_20260805.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def decoded_pf16() -> tuple[float, float, float, float]:
    # Production input is ARGB16; the AEX worker source is RGBA float32.
    a, r, g, b = (20480, 4045, 16384, 28723)
    return tuple(aex_test.f32(v / 32768.0) for v in (r, g, b, a))


def actual_aex(depth: str, source: tuple[float, float, float, float]) -> dict:
    old = aex_test.SRC
    try:
        aex_test.SRC = source
        return aex_test.run_depth(depth)
    finally:
        aex_test.SRC = old


def production() -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_typed_center_") as td:
        binary = Path(td) / "harness"
        subprocess.run(
            [
                "clang++", "-std=c++17", "-O2",
                "-I", str(ROOT / "cli/OLMSmoother2/shim"),
                "-I", str(ROOT / "mac/OLMSmoother2/Mac"),
                str(HARNESS), "-o", str(binary),
            ],
            check=True,
        )
        result = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
    rows = {}
    for line in result.stdout.splitlines():
        depth, raw_hex = line.split()
        rows[depth] = raw_hex
    require(set(rows) == {"PF16", "PF32"}, f"unexpected production rows {rows}")
    return rows


def main() -> int:
    prod = production()
    sources = {
        "PF16": decoded_pf16(),
        "PF32": tuple(aex_test.f32(v) for v in aex_test.SRC),
    }
    comparisons = []
    for depth in ("PF16", "PF32"):
        actual = actual_aex(depth, sources[depth])
        require(actual["actual_raw_hex"] == prod[depth],
                f"{depth} production {prod[depth]} != AEX {actual['actual_raw_hex']}")
        comparisons.append({
            "depth": depth,
            "source_rgba_f32": list(sources[depth]),
            "actual_aex_raw_hex": actual["actual_raw_hex"],
            "production_raw_hex": prod[depth],
            "equal": True,
            "actual_aex_worker": actual["worker"],
            "actual_aex_instructions": actual["instructions"],
        })

    report = {
        "verdict": "PASS_ACTUAL_AEX_TO_PRODUCTION_TYPED_CENTER_EXACT",
        "scope": "PF16/PF32, 1x1 center sample, v1, key disabled, gamma none, smoothness 0, no host",
        "aex_sha256": aex_test.AEX_SHA256,
        "production_source": str(SOURCE.relative_to(ROOT)),
        "production_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "harness": str(HARNESS.relative_to(ROOT)),
        "comparisons": comparisons,
        "claims_not_made": [
            "No PF8 claim (already covered by the frozen full-frame lane)",
            "No non-center classifier/c280 geometry claim",
            "No v2, key, gamma, smoothing, padding, or multi-pixel claim",
            "No After Effects host execution claim",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# OLMSmoother2 typed center actual-AEX/production boundary",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "The unchanged Windows AEX typed worker and production `RenderBits` emit identical raw ARGB storage for a 1x1 v1 center-sample fixture.",
        "",
        "| Depth | Actual AEX | Production |",
        "| --- | --- | --- |",
    ]
    for row in comparisons:
        lines.append(f"| {row['depth']} | `{row['actual_aex_raw_hex']}` | `{row['production_raw_hex']}` |")
    lines += [
        "", "## Evidence boundary", "",
        "This directly closes the previously oracle-mediated PF16/PF32 typed-store connection only for the declared 1x1 center fixture. It does not broaden the existing AE-exact case suites.",
        "", "## Reproduction", "",
        "```sh", "python3 tools/emulation/test_olmsmoother2_typed_center_production_actual_aex_20260805.py", "```", "",
    ]
    DOC.write_text("\n".join(lines))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
