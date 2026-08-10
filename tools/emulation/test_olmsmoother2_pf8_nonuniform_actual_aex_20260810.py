#!/usr/bin/env python3
"""PF8 natural classifier/c280/typed-worker chain: checked-in AEX versus production."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as base
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/emulation/olmsmoother2_pf8_nonuniform_production_harness_20260810.cpp"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother2_pf8_nonuniform_actual_aex_20260810.json"
DOC = ROOT / "refs/conformance/olmsmoother2_pf8_nonuniform_actual_aex_20260810.md"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError("FAIL CLOSED: " + message)


def production() -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="sm2_pf8_nonuniform_") as td:
        binary = Path(td) / "harness"
        subprocess.run([
            "clang++", "-std=c++17", "-O2",
            "-I", str(ROOT / "cli/OLMSmoother2/shim"),
            "-I", str(ROOT / "mac/OLMSmoother2/Mac"),
            str(HARNESS), "-o", str(binary),
        ], check=True)
        stdout = subprocess.run([str(binary)], check=True, text=True, capture_output=True).stdout
    return {label: bytes.fromhex(raw) for label, raw in (line.split() for line in stdout.splitlines())}


def main() -> int:
    # These are exactly the normalized values read by production from the PF8 fixture.
    pixels = [
        (0.0, 0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0, 1.0),
        (0.0, 0.0, 1.0, 1.0),
        (1.0, 1.0, 1.0, 1.0),
        tuple(typed.f32(v / 255.0) for v in (128, 128, 128, 255)),
    ]
    candidates = production()
    actual, class_plane, classifier_instructions, worker_instructions = base.actual("PF8", pixels, 5)
    require(actual == candidates["v1"], f"PF8 v1 mismatch: actual={actual.hex()} production={candidates['v1'].hex()}")
    v2_encoded = [
        (0.0, 0.0, 0.0, 1.0), (0.0, 1.0, 1.0, 1.0), (1.0, 0.0, 1.0, 1.0),
        (1.0, 1.0, 0.0, 1.0),
        tuple(typed.f32(value / 255.0) for value in (64, 64, 64, 255)),
        tuple(typed.f32(value / 255.0) for value in (191, 191, 191, 255)),
    ]
    v2_actual, v2_plane, _linear, v2_ci, v2_wi = v2.actual("PF8", v2_encoded, 5)
    require(v2_actual == candidates["v2"], f"PF8 v2 mismatch: actual={v2_actual.hex()} production={candidates['v2'].hex()}")
    fixtures = []
    for version, raw, plane, ci, wi in (
        ("v1", actual, class_plane, classifier_instructions, worker_instructions),
        ("v2", v2_actual, v2_plane, v2_ci, v2_wi),
    ):
        require(any(plane), f"{version} natural classifier plane unexpectedly stayed zero")
        for y in range(base.H):
            rowbytes = base.W * 4 + 5
            require(raw[y * rowbytes + base.W * 4:(y + 1) * rowbytes] == b"\xa5" * 5,
                    f"PF8 {version} output padding row {y} changed")
        fixtures.append({
            "version": version,
            "geometry": [base.W, base.H],
            "padding_per_row": 5,
            "padding_preserved": True,
            "class_plane_hex": plane.hex(),
            "class_nonzero_bytes": sum(value != 0 for value in plane),
            "raw_hex": raw.hex(),
            "classifier_instructions": ci,
            "typed_worker_instructions": wi,
            "equal": True,
        })

    report = {
        "verdict": "PASS_PF8_NATURAL_AEX_CLASSIFIER_C280_TYPED_WORKER_TO_PRODUCTION_EXACT",
        "scope": "PF8 v1/v2, key disabled, gamma UI none, smoothness 100, range 1, extra smooth 0, padded 3x2 nonuniform fixtures",
        "aex_sha256": typed.AEX_SHA256,
        "production_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "fixtures": fixtures,
        "claims_not_made": [
            "No other geometry or parameter combination",
            "No PF16/PF32 claim from this fixture",
            "No AE-host execution claim",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMSmoother2 PF8 nonuniform production boundary\n\n"
        f"Verdict: `{report['verdict']}`\n\n"
        "The checked-in Windows AEX naturally generated nonzero class planes and ran its PF8 "
        "typed worker for both v1 and v2. Production `RenderBits<PF_Pixel8>` matches every output "
        "byte and preserves five padding bytes per row on both declared 3x2 fixtures. The v2 path "
        "also consumes the captured 10,000-entry decode/inverse LUT pair.\n\n"
        f"- v1 class-plane nonzero bytes: `{fixtures[0]['class_nonzero_bytes']} / 24`\n"
        f"- v2 class-plane nonzero bytes: `{fixtures[1]['class_nonzero_bytes']} / 24`\n\n"
        "This closes only the listed PF8 fixtures. Other geometry, parameter combinations, and "
        "AE-host execution remain outside this evidence boundary.\n"
    )
    print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
