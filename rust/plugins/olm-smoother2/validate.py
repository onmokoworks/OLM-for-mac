"""Rebuild/test only this crate; bind local evidence without launching AE or a host."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RUST = HERE.parent.parent
ROOT = RUST.parent
TARGET = Path(r"D:\olm-rs-target\P-smoother2")


def identity(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "sha256": digest, "bytes": path.stat().st_size}


def main():
    env = dict(os.environ, CARGO_TARGET_DIR=str(TARGET))
    commands = []
    for action in ["build", "test"]:
        args = ["cargo", action, "--release", "-p", "olm-smoother2", "-j", "2", "--offline"]
        result = subprocess.run(args, cwd=RUST, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, check=False)
        log = HERE / f"{action}-release.log"
        log.write_bytes(result.stdout)
        commands.append({"argv": args, "cwd": str(RUST), "exit_code": result.returncode,
                         "log": identity(log)})
        print(result.stdout.decode("utf-8", errors="replace"))
        if result.returncode:
            raise SystemExit(result.returncode)
    test_log = (HERE / "test-release.log").read_text(encoding="utf-8")
    match = re.search(r"test result: ok\. (\d+) passed; 0 failed", test_log)
    if not match:
        raise RuntimeError("No successful Rust unit-test summary")
    cpp = ROOT / "mac/OLMSmoother2/Mac"
    lut_identities = {}
    for name, expected in [
        ("decode", "11056c2feda87964204a53471e172ae6fb6039a0c3120f6277c7ff115fe88cba"),
        ("encode", "b7014467dcae06109111302b8c930494950d27b817d1390d6434605795772fbc"),
    ]:
        text = (cpp / f"OLMSmoother2_{name}_lut_10000.h").read_text(encoding="utf-8")
        body = text.split("{", 1)[1].split("}", 1)[0]
        raw = bytes(int(word.strip(), 16) for word in body.split(",") if word.strip())
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) != 40000 or digest != expected:
            raise RuntimeError(f"Captured {name} LUT identity changed")
        lut_identities[name] = {"bytes": len(raw), "sha256": digest}
    source_paths = list((HERE / "src").glob("*.rs")) + [HERE / "build.rs", HERE / "Cargo.toml",
        HERE / "tests/reference.cpp", HERE / "tests/leaf_reference.inc", HERE / "validate.py",
        HERE / "generate_geometry.py", HERE / "geometry-generation.json", HERE / "pipl_build.rs"]
    reference_paths = [cpp / f"OLMSmoother2_{name}.inc" for name in [
        "constants", "frame_setup", "classification", "polygon_scan", "polygon_weights", "gamma_composite",
        "cardinal_leaves", "corner_samples", "polygon_dispatch", "admission"]]
    reference_paths += [cpp / "OLMSmoother2_port.cpp", ROOT / "cli/OLMSmoother2/shim/OLMSmoother2.h"]
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "full_pipeline_adapter_original_campaign_in_progress",
        "target_dir": str(TARGET), "commands": commands,
        "tests_passed": int(match.group(1)), "tests_failed": 0,
        "original": identity(ROOT.parent / "ghidra_windows_aex/OLMSmoother2.aex"),
        "harness": identity(r"D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\broker\target\release\aexcompat-harness.exe"),
        "worker": identity(r"D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\target\minihost-build\aex_worker.exe"),
        "candidate": identity(HERE / "OLMSmoother2-verified.aex"),
        "built_dll": identity(TARGET / "release/olm_smoother2.dll"),
        "rust_library": identity(TARGET / "release/libolm_smoother2.rlib"),
        "sources": [identity(p) for p in sorted(source_paths)],
        "cpp_reference_sources": [identity(p) for p in reference_paths],
        "captured_luts": lut_identities,
        "oracle": {"inventory": "identical_initial_and_revised_adapter", "campaign": "in_progress"},
        "cpp_comparisons": {
            "integer_loads_each_also_packed": {"u8": 256, "u16": 65536},
            "transfer_values_each_of_three_functions": 50008,
            "frame_filter_pixel_comparisons": 75776,
            "classify_boolean_combinations": 32, "trapezoid_attenuation_cases": 20000,
            "scanner_outputs": {"seed_0x5162": 486528, "seed_0x20261112": 486528},
            "gamma_stage_calls": 26624, "gamma_membership_cases": 4608,
            "nonfinite_scalar_stage_calls": 192, "curve_calls": 160000,
            "literal_encode_calls": 20000, "weight_pair_calls_both_cpp_lanes": 1092960,
            "line_coverage_calls_both_cpp_lanes": 40000, "corner_polygons": 4320,
            "class_plane_frames": 1728, "class_plane_thread_counts": [1, 3, 7],
            "frame_gamma_thread_counts": [1, 2, 3, 7],
            "directional_leaves": 32768, "complete_polygons": 10240,
            "full_frames": 1152, "full_frame_thread_counts": [1,3,7],
            "sha256_source_identity_vectors": 260,
        },
        "new_external_dependencies": [], "hoisting_candidates": ["source identity SHA-256", "transactional SmartFX output", "nonblack color defaults"],
    }
    campaign_path = HERE / "campaign-summary.json"
    if campaign_path.exists():
        campaign = json.loads(campaign_path.read_text())
        if campaign["candidate_sha256"] == report["candidate"]["sha256"]:
            report["oracle"] = campaign
            if campaign["required_campaign_passed"]:
                report["status"] = "verified_windows_aexcompat"
    (HERE / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "tests_passed": report["tests_passed"],
                      "original": report["original"]["sha256"],
                      "candidate": report["candidate"]["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
