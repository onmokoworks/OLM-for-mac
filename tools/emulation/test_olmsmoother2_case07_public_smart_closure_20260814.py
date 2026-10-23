#!/usr/bin/env python3
"""AE-free real-SDK public Smart closure for OLMSmoother2 case 07."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
HARNESS = ROOT / "tools/emulation/olmsmoother2_case07_public_smart_harness_20260814.cpp"
INPUT = ROOT / "refs/conformance/fixtures/olmsmoother2_case07_pf32_entry_20260727/pf32_input_entry_argb.bin.gz"
ORACLE = ROOT / "refs/conformance/olmsmoother2_case07_unique_direct_oracle_20260814.json"
REPORT = ROOT / "refs/conformance/olmsmoother2_case07_public_smart_closure_20260814.json"
NOTE = REPORT.with_suffix(".md")
VERDICT = "PASS_OLMSMOOTHER2_CASE07_PUBLIC_SMART_SOURCE_BOUND_AE_FREE"
CASE_NAMES = [
    "positive", "source_first", "source_middle", "source_last", "gamma_next",
    "key_color_one", "palette_one", "width_one", "rowbytes_one", "input_flags_one",
    "output_flags_one", "origin_one", "downsample_one", "extent_one", "format_one",
    "alias", "overlap", "layer_error", "output_error", "param_checkout_error",
    "param_checkin_error", "world_error", "color_error", "color_wrong_success",
]
EXPECTED = {
    "source": "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168",
    "harness": "df1419b9992e18442b91aa1d7d4aa84f2538ca5192a52ebfa298ae8d2c7afe31",
    "input_gzip": "f29cad40b4f0081fa5f279da0e875198a2970ea2d9c1161db7cc2058acf4044c",
    "oracle": "5be3cc58fb73fed148a927df4bc888ce217dd0f96906f54b44a9dce1b62b0063",
}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def live_identities() -> dict[str, str]:
    return {"source": sha256(SOURCE), "harness": sha256(HARNESS),
            "input_gzip": sha256(INPUT), "oracle": sha256(ORACLE)}

def run_harness() -> tuple[list[dict[str, object]], str]:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2-case07-public.") as td:
        exe = Path(td) / "probe"
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                             text=True, check=True).stdout.strip()
        command = [
            "clang++", "-std=c++17", "-arch", "arm64", "-O2",
            "-Wno-pragma-pack", "-Wno-deprecated-declarations", "-isysroot", sdk,
            "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", "-Imac/OLMSmoother2",
            str(HARNESS), "mac/OLMSmoother2/OLMSmoother2_Strings.cpp",
            str(resolve_asset("Util/AEGP_SuiteHandler.cpp")), str(resolve_asset("Util/MissingSuiteError.cpp")),
            "-lz", "-framework", "Cocoa", "-o", str(exe),
        ]
        subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        run = subprocess.run([str(exe), str(INPUT)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise ValueError("public harness failed: " + run.stdout + run.stderr)
    rows = []
    for line in run.stdout.splitlines():
        if not line.startswith("CASE "):
            continue
        fields = line.split()
        rows.append({"name": fields[1], "pass": fields[2] == "pass=1",
                     "err": int(fields[3].split("=", 1)[1])})
    if [row["name"] for row in rows] != CASE_NAMES or not all(row["pass"] for row in rows):
        raise ValueError("case transcript drift")
    if run.stdout.splitlines()[-1] != "SUMMARY pass=24 total=24":
        raise ValueError("summary drift")
    return rows, hashlib.sha256(run.stdout.encode()).hexdigest()

def build_report() -> dict[str, object]:
    if live_identities() != EXPECTED:
        raise ValueError("identity drift")
    rows, transcript = run_harness()
    return {
        "schema_version": 1,
        "verdict": VERDICT,
        "scope": "one exact 1920x1080 PF32 case-07 Smart tuple/source plus bounded safety negatives; AE-free real-SDK source inclusion",
        "identities": EXPECTED,
        "contract": {
            "dimensions": [1920, 1080], "depth": 32, "rowbytes": 30720,
            "input_active_sha256": "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b",
            "direct_output_sha256": "31bbdb17ef62802bc7d67fd66e552e5c0fd7d1e5a740d7aca923acb1d15bf65c",
            "gamma_value_binary64": "3ff451eb80000000",
            "positive_count": 1, "negative_count": 23,
        },
        "cases": rows,
        "case_names_sha256": hashlib.sha256("\n".join(CASE_NAMES).encode()).hexdigest(),
        "transcript_sha256": transcript,
        "claims_not_made": [
            "No arbitrary source, tuple, geometry, or depth claim",
            "No native Windows output-world memory capture",
            "No After Effects launch, installed-binary, or release claim",
            "No assertion that the premultiplied final EXR equals the straight plugin output",
        ],
    }

def validate(data: dict[str, object], live: bool = True) -> bool:
    try:
        if set(data) != {"schema_version", "verdict", "scope", "identities", "contract",
                         "cases", "case_names_sha256", "transcript_sha256", "claims_not_made"}:
            return False
        if data["schema_version"] != 1 or data["verdict"] != VERDICT or data["identities"] != EXPECTED:
            return False
        if live and live_identities() != EXPECTED:
            return False
        contract = data["contract"]
        if set(contract) != {"dimensions", "depth", "rowbytes", "input_active_sha256",
                            "direct_output_sha256", "gamma_value_binary64", "positive_count", "negative_count"}:
            return False
        if contract != {
            "dimensions": [1920, 1080], "depth": 32, "rowbytes": 30720,
            "input_active_sha256": "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b",
            "direct_output_sha256": "31bbdb17ef62802bc7d67fd66e552e5c0fd7d1e5a740d7aca923acb1d15bf65c",
            "gamma_value_binary64": "3ff451eb80000000", "positive_count": 1, "negative_count": 23,
        }:
            return False
        cases = data["cases"]
        if not isinstance(cases, list) or [row.get("name") for row in cases] != CASE_NAMES:
            return False
        for index, row in enumerate(cases):
            if set(row) != {"name", "pass", "err"} or row["pass"] is not True:
                return False
            if index == 0 and row["err"] != 0:
                return False
            if index and (not isinstance(row["err"], int) or row["err"] == 0):
                return False
        if data["case_names_sha256"] != hashlib.sha256("\n".join(CASE_NAMES).encode()).hexdigest():
            return False
        expected_claims = [
            "No arbitrary source, tuple, geometry, or depth claim",
            "No native Windows output-world memory capture",
            "No After Effects launch, installed-binary, or release claim",
            "No assertion that the premultiplied final EXR equals the straight plugin output",
        ]
        return data["claims_not_made"] == expected_claims and len(data["transcript_sha256"]) == 64
    except (AttributeError, KeyError, TypeError, ValueError):
        return False

def note(data: dict[str, object]) -> str:
    return ("# OLMSmoother2 case-07 bounded public Smart closure\n\n"
            f"Verdict: `{data['verdict']}`\n\n"
            "A fresh real-SDK, source-included SmartRender call admits one exact PF32 1920x1080 source/tuple and produces the straight direct oracle `31bb…`. "
            "Twenty-three source, parameter, world, overlap, lifecycle, and suite controls fail before host-output commit.\n\n"
            "This is AE-free hostless evidence. The Windows final EXR is a separate premultiplied presentation and is not treated as direct plugin memory.\n")

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.validate_only:
            data = json.loads(REPORT.read_text())
        else:
            data = build_report()
        if not validate(data):
            raise ValueError("validation failed")
        if args.write:
            REPORT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            NOTE.write_text(note(data))
        elif REPORT.exists() and json.loads(REPORT.read_text()) != data:
            raise ValueError("persisted report drift")
        print(VERDICT); return 0
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL_OLMSMOOTHER2_CASE07_PUBLIC_SMART: {exc}"); return 1

if __name__ == "__main__":
    raise SystemExit(main())
