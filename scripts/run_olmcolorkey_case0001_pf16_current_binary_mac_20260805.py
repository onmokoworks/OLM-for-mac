#!/usr/bin/env python3
"""Hash-bound Mac AE Software/16bpc runner for OLMColorKey case0001.

The retained historical Mac output is deliberately not an input.  A run is
allowed only when the one live AE process maps the exact current executable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ROOT = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625"
REQUEST_MANIFEST = REQUEST_ROOT / "request_manifest.json"
REFERENCE_MANIFEST = REQUEST_ROOT / "reference_manifest.json"
FRAME = "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0001.png"
BEFORE = "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0001_before_effects.png"
INPUT = REQUEST_ROOT / "input" / BEFORE
WINDOWS_REFERENCE = REQUEST_ROOT / "expected" / FRAME
RENDER_JSX = ROOT / "scripts/ae_pixel_validation_render.jsx"
INSTALLED_BINARY = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMColorKey.plugin/Contents/MacOS/OLMColorKey"

EXPECTED = {
    "binary": "34fd47cd04c6665f75a84ffb0d2bb01390823e50d2224059917043cd45350464",
    "input": "01fe02e7d14f670c9c21564e6962ecae7a5d23ff6cb67c8f19df244a6c098105",
    "windows_reference": "d650ed20952374cdce84872aa57777c2c758884bca9c8d2c7a036a4ee7dec133",
    "request_manifest": "baea985f4caddb557695d20b0bb06f482c5658c3511100f744f63556b7f5d8b9",
    "reference_manifest": "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e",
    "render_jsx": "4cbf7a2a80eb38f8d81150cf48b353b9a326a589b91af81e0ab9833eae9c9804",
    "readable_params": "c5bcbc5d2cc1a7ffe28cd153a676dd0e22c5923de9ece7f65bb6b4655155fdb8",
    "case": "5001ce97595bc154d50c49360b599ee41d94807b0ad9d7965b3afec3b14a3356",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def case_contract() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    reference = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in reference["cases"] if row.get("id") == "olmcolorkey__case_0001"]
    if len(rows) != 1:
        raise ValueError(f"expected one case0001, found {len(rows)}")
    case = rows[0]
    effect = case["effects"][0]
    params = [
        {"match_name": row["match_name"], "value": row["value"]}
        for row in effect["params"] if row.get("value_read_method")
    ]
    if canonical_sha256(case) != EXPECTED["case"] or canonical_sha256(params) != EXPECTED["readable_params"]:
        raise ValueError("case or readable parameter payload drifted")
    if len(params) != 219 or case["bits_per_channel"] != 16:
        raise ValueError("case bit-depth/parameter count drifted")
    if case["project_gpu_accel_type"] != {"current_name": "SOFTWARE", "raw": 1816}:
        raise ValueError("Software renderer contract drifted")
    if effect.get("name") != "OLM Color Key" or effect.get("match_name") != "OLM Color Key":
        raise ValueError("effect identity drifted")
    return case, params


def ae_pids() -> list[int]:
    proc = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True)
    return [int(value) for value in proc.stdout.split() if value.isdigit()]


def mapped_colorkey(pid: int) -> list[str]:
    proc = subprocess.run(["lsof", "-Fn", "-p", str(pid)], text=True, capture_output=True)
    return sorted(set(
        line[1:] for line in proc.stdout.splitlines()
        if line.startswith("n/") and line.endswith("/Contents/MacOS/OLMColorKey")
    ))


def stage_request(base: Path) -> tuple[Path, str]:
    request_id = "ae_pixel_bitdepth16_olmcolorkey_exact_20260625"
    staged = base / "requests" / request_id
    (staged / "input").mkdir(parents=True)
    (staged / "expected").mkdir()
    shutil.copy2(INPUT, staged / "input" / BEFORE)
    shutil.copy2(WINDOWS_REFERENCE, staged / "expected" / FRAME)
    shutil.copy2(REFERENCE_MANIFEST, staged / "reference_manifest.json")
    request = json.loads(REQUEST_MANIFEST.read_text(encoding="utf-8"))
    request["cases"] = [row for row in request["cases"] if row["id"] == "olmcolorkey__case_0001"]
    request["threshold_groups"] = [{
        "name": "16bpc_case0001_exact", "case_ids": ["olmcolorkey__case_0001"],
        "max_diff": 0, "mean_diff": 0.0, "nonzero_px_percent": 0.0,
    }]
    (staged / "request_manifest.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    return staged, request_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    contract_error = None
    try:
        case, params = case_contract()
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        contract_error = str(exc); case, params = {}, []
    paths = {
        "binary": INSTALLED_BINARY, "input": INPUT, "windows_reference": WINDOWS_REFERENCE,
        "request_manifest": REQUEST_MANIFEST, "reference_manifest": REFERENCE_MANIFEST,
        "render_jsx": RENDER_JSX,
    }
    actual = {key: sha256(path) if path.is_file() else None for key, path in paths.items()}
    pids = ae_pids()
    mappings = {str(pid): mapped_colorkey(pid) for pid in pids}
    expected_path = str(INSTALLED_BINARY.resolve()) if INSTALLED_BINARY.is_file() else None
    exact_mapping = len(pids) == 1 and mappings.get(str(pids[0])) == [expected_path]
    checks: dict[str, Any] = {
        **{f"{key}_hash": value for key, value in actual.items()},
        **{f"{key}_hash_matches": actual[key] == EXPECTED[key] for key in paths},
        "case_contract_exact": contract_error is None, "case_contract_error": contract_error,
        "readable_param_count": len(params), "readable_params_sha256": canonical_sha256(params),
        "single_ae_process": len(pids) == 1, "ae_pids": pids,
        "loaded_module_paths": mappings,
        "loaded_module_is_sole_exact_current_binary": exact_mapping,
    }
    ready = all(checks[key] for key in (
        "binary_hash_matches", "input_hash_matches", "windows_reference_hash_matches",
        "request_manifest_hash_matches", "reference_manifest_hash_matches", "render_jsx_hash_matches",
        "case_contract_exact", "single_ae_process", "loaded_module_is_sole_exact_current_binary",
    ))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = (args.output_root or ROOT / f"refs/reports/olmcolorkey_case0001_pf16_current_binary_{stamp}").resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "runner_report.json"
    report: dict[str, Any] = {
        "kind": "olmcolorkey_case0001_pf16_current_binary_mac_runner",
        "schema_version": 1, "status": "ready" if ready else "restart_required",
        "ae_exact_claim": False, "checks": checks, "run_requested": args.run, "run_executed": False,
        "contract": {"case_id": "olmcolorkey__case_0001", "bits_per_channel": 16,
                     "renderer": "SOFTWARE", "renderer_raw": 1816,
                     "effect": "OLM Color Key", "readable_parameter_count": len(params),
                     "target_application": "Adobe After Effects 2026",
                     "target_version": "26.3.0.87",
                     "expected_output_sha256": EXPECTED["windows_reference"],
                     "required_loaded_binary_sha256": EXPECTED["binary"]},
        "claim_boundary": "Fresh current-binary Mac AE render only; historical Mac output is not consumed.",
    }
    if not ready or not args.run:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(report_path), "checks": checks}))
        return 2 if not ready else 0

    with tempfile.TemporaryDirectory(prefix="olmcolorkey_case0001_pf16_") as temp_name:
        base = Path(temp_name)
        _, request_id = stage_request(base)
        results = base / "results"; results.mkdir()
        batch = base / "batch.json"
        progress = base / "progress.log"
        wrapper = base / "run.jsx"
        env = {
            "OLM_AE_BASE_DIR": str(base), "OLM_AE_REQUESTS_BASE": str(base / "requests"),
            "OLM_AE_RESULTS_BASE": str(results), "OLM_AE_PROGRESS_LOG": str(progress),
            "OLM_AE_BATCH_RESULT_JSON": str(batch), "OLM_AE_REQUEST_IDS_JSON": json.dumps([request_id]),
        }
        lines = [f"$.setenv({json.dumps(key)}, {json.dumps(value)});" for key, value in env.items()]
        lines.append(f"$.evalFile(new File({json.dumps(str(RENDER_JSX))}));")
        wrapper.write_text("\n".join(lines) + "\n", encoding="utf-8")
        apple = f'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n'
        run = subprocess.run(["osascript"], input=apple, text=True, capture_output=True, timeout=args.timeout)
        candidate = results / "bitdepth16_olmcolorkey_exact" / FRAME
        report["run_executed"] = True
        report["osascript"] = {"returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
        report["fresh_output"] = {"exists": candidate.is_file(), "sha256": sha256(candidate) if candidate.is_file() else None}
        post_pids = ae_pids()
        post_mapping = mapped_colorkey(post_pids[0]) if len(post_pids) == 1 else []
        post_identity = {
            "same_single_ae_pid": post_pids == pids,
            "sole_exact_module_mapping": post_mapping == [expected_path],
            "installed_binary_hash_unchanged": sha256(INSTALLED_BINARY) == EXPECTED["binary"],
        }
        report["post_render_identity"] = post_identity
        report["status"] = "pass" if (
            run.returncode == 0 and candidate.is_file()
            and sha256(candidate) == EXPECTED["windows_reference"]
            and all(post_identity.values())
        ) else "fail_closed"
        report["ae_exact_claim"] = report["status"] == "pass"
        if progress.is_file(): report["progress_log"] = progress.read_text(encoding="utf-8", errors="replace")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path)}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
