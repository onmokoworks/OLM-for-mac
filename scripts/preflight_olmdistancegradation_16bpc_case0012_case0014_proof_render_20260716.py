#!/usr/bin/env python3
"""Fail-closed non-destructive DG 16bpc proof-render preflight.

This script does not launch After Effects, does not quit After Effects, and
does not execute any render. It verifies the canonical 16bpc request assets for
DG cases 0012 and 0014, the sole installed MediaCore plug-in bundle and pinned
SHA-256, and whether the DG binary is already mapped into the currently running
After Effects process. It emits preview commands that reuse
`scripts/run_ae_single_case.py`, but refuses proof-render readiness unless an
explicit disposable-project flag is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
REQUEST_DIR = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / REQUEST_ID
CASE_IDS = (
    "olmdistancegradation_extended__case_0012",
    "olmdistancegradation_extended__case_0014",
)
CANONICAL_REQUEST_MANIFEST_SHA256 = (
    "7c4761b3b4de904c2a8baa8883c964f234943604414d2cd34bab107ccc43cf29"
)
CANONICAL_REFERENCE_MANIFEST_SHA256 = (
    "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
)
CANONICAL_REQUEST_CASES: dict[str, dict[str, Any]] = {
    "olmdistancegradation_extended__case_0012": {
        "before_effects_frame": (
            "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
            "olmdistancegradation_extended__case_0012_before_effects.png"
        ),
        "before_effects_frame_sha256": (
            "4df66ca58088631115a48a7396d5f7f5b272866f8f6444a02c996751d1afc43c"
        ),
        "frame": (
            "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
            "olmdistancegradation_extended__case_0012.png"
        ),
        "frame_sha256": "72034695ab9bc4202638bc3716e311397956625f97e7d64c87725c75d2e70716",
        "reference_comp_name": "olmdistancegradation_extended__case_0012_software_16bpc_24",
        "requested_effect_match_name": "OLM Distance Gradation",
        "project_gpu_accel_type": "SOFTWARE",
        "bits_per_channel": 16,
    },
    "olmdistancegradation_extended__case_0014": {
        "before_effects_frame": (
            "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
            "olmdistancegradation_extended__case_0014_before_effects.png"
        ),
        "before_effects_frame_sha256": (
            "4df66ca58088631115a48a7396d5f7f5b272866f8f6444a02c996751d1afc43c"
        ),
        "frame": (
            "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
            "olmdistancegradation_extended__case_0014.png"
        ),
        "frame_sha256": "5d5902e2ec453ef5275672433d4a0acdd2df29e94deef35d22c717356b32134a",
        "reference_comp_name": "olmdistancegradation_extended__case_0014_software_16bpc_24",
        "requested_effect_match_name": "OLM Distance Gradation",
        "project_gpu_accel_type": "SOFTWARE",
        "bits_per_channel": 16,
    },
}
CANONICAL_REQUEST_IDENTITY: dict[str, Any] = {
    "request_id": REQUEST_ID,
    "request_manifest_sha256": CANONICAL_REQUEST_MANIFEST_SHA256,
    "reference_manifest_sha256": CANONICAL_REFERENCE_MANIFEST_SHA256,
    "cases": CANONICAL_REQUEST_CASES,
}
PLUGIN_BUNDLE = "OLMDistanceGradation.plugin"
PLUGIN_BINARY = "OLMDistanceGradation"
EXPECTED_PLUGIN_SHA256 = "af328faed0fcfbdefac7618d1218c2e5e5c9c0420c3bc58cdde7a7b6f64232fd"
DEFAULT_MEDIA_CORE = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Adobe"
    / "Common"
    / "Plug-ins"
    / "7.0"
    / "MediaCore"
)
DEFAULT_OUTPUT_ROOT = Path("/tmp/olmdg_16bpc_case0012_case0014_proof_render_20260716")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def path_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_asset_path(base_dir: Path, asset_name: Any) -> tuple[Path | None, str | None]:
    if not isinstance(asset_name, str) or not asset_name:
        return None, "missing_or_invalid"
    candidate = Path(asset_name)
    if candidate.is_absolute():
        return None, "absolute_path"
    resolved = (base_dir / candidate).resolve()
    if not path_within(resolved, base_dir.resolve()):
        return None, "outside_base_dir"
    return resolved, None


def classify_subprocess_error(exc: BaseException) -> str:
    if isinstance(exc, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(exc, OSError):
        return "oserror"
    return "unexpected_error"


def invoke_subprocess(command: list[str]) -> tuple[subprocess.CompletedProcess[str] | None, str | None]:
    try:
        return run_subprocess(command), None
    except (subprocess.TimeoutExpired, OSError) as exc:
        return None, classify_subprocess_error(exc)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=REQUEST_DIR)
    parser.add_argument("--media-core-dir", type=Path, default=DEFAULT_MEDIA_CORE)
    parser.add_argument("--expect-plugin-sha256", default=EXPECTED_PLUGIN_SHA256)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--ae-process-name", default="After Effects")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument(
        "--disposable-project",
        action="store_true",
        help="Acknowledge that the next proof render may replace the current AE project.",
    )
    return parser.parse_args(argv)


def find_case(items: list[dict[str, Any]], case_id: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("id") == case_id:
            return item
    return None


def verify_request(request_dir: Path) -> tuple[dict[str, Any], list[str]]:
    request_dir = request_dir.resolve()
    failures: list[str] = []
    request_manifest_path = request_dir / "request_manifest.json"
    reference_manifest_path = request_dir / "reference_manifest.json"
    input_dir = request_dir / "input"
    expected_dir = request_dir / "expected"

    checks: dict[str, Any] = {
        "request_dir": str(request_dir),
        "request_manifest_path": str(request_manifest_path),
        "reference_manifest_path": str(reference_manifest_path),
        "input_dir": str(input_dir),
        "expected_dir": str(expected_dir),
        "exists": {
            "request_dir": request_dir.is_dir(),
            "request_manifest": request_manifest_path.is_file(),
            "reference_manifest": reference_manifest_path.is_file(),
            "input_dir": input_dir.is_dir(),
            "expected_dir": expected_dir.is_dir(),
        },
        "canonical_identity": CANONICAL_REQUEST_IDENTITY,
    }
    for key, ok in checks["exists"].items():
        if not ok:
            failures.append(f"request_paths:{key}")
    if failures:
        checks["status"] = "blocked"
        return checks, failures

    checks["request_manifest_sha256"] = sha256_file(request_manifest_path)
    checks["reference_manifest_sha256"] = sha256_file(reference_manifest_path)
    checks["request_manifest_sha256_matches_canonical"] = (
        checks["request_manifest_sha256"] == CANONICAL_REQUEST_MANIFEST_SHA256
    )
    checks["reference_manifest_sha256_matches_canonical"] = (
        checks["reference_manifest_sha256"] == CANONICAL_REFERENCE_MANIFEST_SHA256
    )
    if not checks["request_manifest_sha256_matches_canonical"]:
        failures.append("request_manifest:sha256_mismatch")
    if not checks["reference_manifest_sha256_matches_canonical"]:
        failures.append("reference_manifest:sha256_mismatch")

    try:
        request_manifest = load_json(request_manifest_path)
        checks["request_manifest_load_status"] = "ok"
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        checks["request_manifest_load_status"] = "blocked_malformed_json"
        failures.append("request_manifest:malformed_json")
        checks["status"] = "blocked"
        return checks, failures

    try:
        reference_manifest = load_json(reference_manifest_path)
        checks["reference_manifest_load_status"] = "ok"
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        checks["reference_manifest_load_status"] = "blocked_malformed_json"
        failures.append("reference_manifest:malformed_json")
        checks["status"] = "blocked"
        return checks, failures

    checks["request_id"] = request_manifest.get("request_id")
    checks["request_kind"] = request_manifest.get("kind")
    checks["reference_project_bits_per_channel"] = (
        (reference_manifest.get("project") or {}).get("bits_per_channel")
    )
    checks["reference_manifest_name"] = request_manifest.get("reference_manifest")
    checks["cases"] = []

    if request_manifest.get("kind") != "olm_ae_pixel_validation_request":
        failures.append("request_manifest:kind")
    if request_manifest.get("request_id") != REQUEST_ID:
        failures.append("request_manifest:request_id")
    if request_manifest.get("reference_manifest") != "reference_manifest.json":
        failures.append("request_manifest:reference_manifest")
    if request_manifest.get("input_dir") != "input":
        failures.append("request_manifest:input_dir")
    if request_manifest.get("expected_dir") != "expected":
        failures.append("request_manifest:expected_dir")
    if (reference_manifest.get("project") or {}).get("bits_per_channel") != 16:
        failures.append("reference_manifest:project_bits_per_channel_16")

    request_cases = request_manifest.get("cases") or []
    reference_cases = reference_manifest.get("cases") or []
    for case_id in CASE_IDS:
        request_case = find_case(request_cases, case_id)
        reference_case = find_case(reference_cases, case_id)
        canonical_case = CANONICAL_REQUEST_CASES[case_id]
        case_row: dict[str, Any] = {
            "case_id": case_id,
            "present_in_request_manifest": request_case is not None,
            "present_in_reference_manifest": reference_case is not None,
        }
        if request_case is None:
            failures.append(f"{case_id}:request_case_missing")
            checks["cases"].append(case_row)
            continue
        if reference_case is None:
            failures.append(f"{case_id}:reference_case_missing")
            checks["cases"].append(case_row)
            continue
        before_name = request_case.get("before_effects_frame")
        frame_name = request_case.get("frame")
        before_path, before_path_error = resolve_asset_path(input_dir, before_name)
        frame_path, frame_path_error = resolve_asset_path(expected_dir, frame_name)
        case_row.update(
            {
                "before_effects_frame": before_name,
                "frame": frame_name,
                "before_effects_path": str(before_path) if before_path else "",
                "expected_frame_path": str(frame_path) if frame_path else "",
                "before_effects_path_status": before_path_error or "ok",
                "expected_frame_path_status": frame_path_error or "ok",
                "before_effects_exists": before_path is not None and before_path.is_file(),
                "expected_frame_exists": frame_path is not None and frame_path.is_file(),
                "reference_case_bits_per_channel": reference_case.get("bits_per_channel"),
                "reference_comp_name": (reference_case.get("comp") or {}).get("name"),
                "requested_effect_name": (reference_case.get("requested_effect") or {}).get("name"),
                "requested_effect_match_name": (reference_case.get("requested_effect") or {}).get("match_name"),
                "project_gpu_accel_type": (
                    (reference_case.get("project_gpu_accel_type") or {}).get("current_name")
                ),
            }
        )
        if before_name != canonical_case.get("before_effects_frame"):
            failures.append(f"{case_id}:before_effects_frame_canonical_mismatch")
        if frame_name != canonical_case.get("frame"):
            failures.append(f"{case_id}:frame_canonical_mismatch")
        if before_name != reference_case.get("before_effects_frame"):
            failures.append(f"{case_id}:before_effects_frame_drift")
        if frame_name != reference_case.get("frame"):
            failures.append(f"{case_id}:frame_drift")
        if before_path_error:
            failures.append(f"{case_id}:before_effects_frame_{before_path_error}")
        elif not before_path.is_file():
            failures.append(f"{case_id}:before_effects_missing")
        if frame_path_error:
            failures.append(f"{case_id}:frame_{frame_path_error}")
        elif not frame_path.is_file():
            failures.append(f"{case_id}:expected_frame_missing")
        if before_path is not None and before_path.is_file():
            case_row["before_effects_sha256"] = sha256_file(before_path)
            case_row["before_effects_sha256_matches_canonical"] = (
                case_row["before_effects_sha256"] == canonical_case["before_effects_frame_sha256"]
            )
            if not case_row["before_effects_sha256_matches_canonical"]:
                failures.append(f"{case_id}:before_effects_sha256_mismatch")
        else:
            case_row["before_effects_sha256_matches_canonical"] = False
        if frame_path is not None and frame_path.is_file():
            case_row["expected_frame_sha256"] = sha256_file(frame_path)
            case_row["expected_frame_sha256_matches_canonical"] = (
                case_row["expected_frame_sha256"] == canonical_case["frame_sha256"]
            )
            if not case_row["expected_frame_sha256_matches_canonical"]:
                failures.append(f"{case_id}:frame_sha256_mismatch")
        else:
            case_row["expected_frame_sha256_matches_canonical"] = False
        if reference_case.get("bits_per_channel") != 16:
            failures.append(f"{case_id}:reference_bits_per_channel_16")
        if reference_case.get("bits_per_channel") != canonical_case["bits_per_channel"]:
            failures.append(f"{case_id}:reference_bits_per_channel_canonical_mismatch")
        if (reference_case.get("requested_effect") or {}).get("match_name") != "OLM Distance Gradation":
            failures.append(f"{case_id}:effect_match_name")
        if (
            (reference_case.get("requested_effect") or {}).get("match_name")
            != canonical_case["requested_effect_match_name"]
        ):
            failures.append(f"{case_id}:effect_match_name_canonical_mismatch")
        if (reference_case.get("project_gpu_accel_type") or {}).get("current_name") != "SOFTWARE":
            failures.append(f"{case_id}:project_gpu_accel_type_software")
        if (
            (reference_case.get("project_gpu_accel_type") or {}).get("current_name")
            != canonical_case["project_gpu_accel_type"]
        ):
            failures.append(f"{case_id}:project_gpu_accel_type_canonical_mismatch")
        if (reference_case.get("comp") or {}).get("name") != canonical_case["reference_comp_name"]:
            failures.append(f"{case_id}:reference_comp_name_canonical_mismatch")
        checks["cases"].append(case_row)

    checks["status"] = "ok" if not failures else "blocked"
    return checks, failures


def verify_installed_plugin(media_core_dir: Path, expected_sha256: str) -> tuple[dict[str, Any], list[str]]:
    media_core_dir = media_core_dir.resolve()
    failures: list[str] = []
    direct_bundle_path = (media_core_dir / PLUGIN_BUNDLE).resolve()
    bundle_candidates = sorted(
        {
            bundle.resolve()
            for bundle in media_core_dir.rglob(PLUGIN_BUNDLE)
            if bundle.is_dir()
        }
    )
    checks: dict[str, Any] = {
        "media_core_dir": str(media_core_dir),
        "bundle_name": PLUGIN_BUNDLE,
        "binary_name": PLUGIN_BINARY,
        "expected_sha256": expected_sha256,
        "direct_bundle_path": str(direct_bundle_path),
        "direct_bundle_exists": direct_bundle_path.is_dir(),
        "bundle_candidates": [str(path) for path in bundle_candidates],
        "bundle_count": len(bundle_candidates),
        "recursive_descendant_candidates": [
            str(path) for path in bundle_candidates if path != direct_bundle_path
        ],
    }
    if not direct_bundle_path.is_dir():
        failures.append("plugin:direct_media_core_bundle_missing")
    if bundle_candidates != [direct_bundle_path]:
        failures.append("plugin:direct_media_core_bundle_only")
    if failures:
        checks["status"] = "blocked"
        return checks, failures

    bundle_path = direct_bundle_path
    binary_path = bundle_path / "Contents" / "MacOS" / PLUGIN_BINARY
    checks["bundle_path"] = str(bundle_path)
    checks["binary_path"] = str(binary_path)
    checks["binary_exists"] = binary_path.is_file()
    if not binary_path.is_file():
        failures.append("plugin:binary_missing")
        checks["status"] = "blocked"
        return checks, failures

    actual_sha256 = sha256_file(binary_path)
    checks["actual_sha256"] = actual_sha256
    checks["sha256_matches_expected"] = actual_sha256 == expected_sha256
    if actual_sha256 != expected_sha256:
        failures.append("plugin:sha256_mismatch")
    checks["status"] = "ok" if not failures else "blocked"
    return checks, failures


def run_subprocess(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, timeout=120)


def detect_running_ae(process_name: str, plugin_binary_path: Path) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    checks: dict[str, Any] = {
        "process_name": process_name,
        "status": "not_running",
        "pids": [],
        "process_count": 0,
        "plugin_binary_path": str(plugin_binary_path.resolve()),
        "mapping_method": "vmmap_exact_path_suffix",
        "processes": [],
        "dg_binary_mapped_in_any_running_ae": False,
    }
    pgrep, pgrep_error = invoke_subprocess(["pgrep", "-x", process_name])
    if pgrep_error is not None:
        checks["status"] = "blocked"
        checks["pgrep_status"] = pgrep_error
        failures.append(f"ae_process:pgrep_{pgrep_error}")
        return checks, failures
    assert pgrep is not None
    if pgrep.returncode not in (0, 1):
        checks["status"] = "blocked"
        checks["pgrep_returncode"] = pgrep.returncode
        checks["pgrep_status"] = "returncode_failed"
        return checks, ["ae_process:pgrep_failed"]

    pids = [int(token) for token in pgrep.stdout.split() if token.isdigit()]
    checks["pids"] = pids
    checks["process_count"] = len(pids)
    if not pids:
        return checks, failures

    if len(pids) > 1:
        failures.append("ae_process:expected_zero_or_one_after_effects_process")

    resolved_binary = str(plugin_binary_path.resolve())
    mapped_any = False
    for pid in pids:
        vmmap, vmmap_error = invoke_subprocess(["vmmap", str(pid)])
        lines = [] if vmmap is None else vmmap.stdout.splitlines()
        exact_mapping = any(line.rstrip().endswith(resolved_binary) for line in lines)
        process_row = {
            "pid": pid,
            "vmmap_returncode": None if vmmap is None else vmmap.returncode,
            "dg_binary_mapped_exact_path": exact_mapping,
        }
        if vmmap_error is not None:
            failures.append(f"ae_process:vmmap_{vmmap_error}:{pid}")
            process_row["status"] = f"vmmap_{vmmap_error}"
            process_row["vmmap_status"] = vmmap_error
        elif vmmap.returncode != 0:
            failures.append(f"ae_process:vmmap_failed:{pid}")
            process_row["status"] = "vmmap_failed"
        else:
            process_row["status"] = "ok"
        checks["processes"].append(process_row)
        mapped_any = mapped_any or exact_mapping

    checks["dg_binary_mapped_in_any_running_ae"] = mapped_any
    if len(pids) == 1:
        checks["status"] = "running"
        checks["single_running_pid"] = pids[0]
        checks["dg_binary_mapped_in_single_running_ae"] = checks["processes"][0][
            "dg_binary_mapped_exact_path"
        ]
    else:
        checks["status"] = "running_ambiguous"
    if any(row["status"] != "ok" for row in checks["processes"]):
        checks["status"] = "blocked"
    return checks, failures


def build_preview_commands(
    request_dir: Path,
    output_root: Path,
    app_name: str,
) -> list[dict[str, Any]]:
    runner = ROOT / "scripts" / "run_ae_single_case.py"
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        output_dir = output_root / case_id
        command = [
            sys.executable,
            str(runner),
            "--request-dir",
            str(request_dir),
            "--case-id",
            case_id,
            "--output-dir",
            str(output_dir),
            "--app-name",
            app_name,
            "--timeout",
            "1200",
            "--ae-env",
            "OLM_AE_FORCE_NEW_PROJECT=1",
            "--ae-env",
            "OLM_AE_FORCE_SOFTWARE=1",
            "--ae-env",
            "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1",
        ]
        rows.append(
            {
                "case_id": case_id,
                "output_dir": str(output_dir),
                "argv": command,
                "shell_command": shlex.join(command),
            }
        )
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    request_checks, request_failures = verify_request(args.request_dir)
    plugin_checks, plugin_failures = verify_installed_plugin(
        args.media_core_dir,
        args.expect_plugin_sha256,
    )
    binary_path = Path(plugin_checks.get("binary_path", args.media_core_dir))
    ae_checks, ae_failures = detect_running_ae(args.ae_process_name, binary_path)
    preview_commands = build_preview_commands(
        request_dir=args.request_dir.resolve(),
        output_root=args.output_root.resolve(),
        app_name=args.app_name,
    )

    structural_failures = request_failures + plugin_failures + ae_failures
    guard_failures: list[str] = []
    if not args.disposable_project:
        guard_failures.append("proof_render:explicit_disposable_project_flag_required")

    if structural_failures:
        status = "blocked_structural_preflight_failure"
    elif guard_failures:
        status = "blocked_refused_missing_disposable_project_flag"
    else:
        status = "ready_for_disposable_project_proof_render_no_execution"

    report = {
        "schema": 1,
        "kind": "olmdistancegradation_16bpc_case0012_case0014_proof_render_preflight",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "claim_boundary": (
            "non-destructive local preflight only; no AE launch, no AE quit, "
            "no render execution, and no AE exact claim"
        ),
        "ae_exact_claim": False,
        "canonical_request_id": REQUEST_ID,
        "canonical_cases": list(CASE_IDS),
        "canonical_request_identity": CANONICAL_REQUEST_IDENTITY,
        "request_checks": request_checks,
        "installed_plugin_checks": plugin_checks,
        "running_ae_checks": ae_checks,
        "proof_render_guard": {
            "disposable_project_flag_required": True,
            "disposable_project_flag_supplied": args.disposable_project,
            "existing_runner_api": str(ROOT / "scripts" / "run_ae_single_case.py"),
            "preview_commands": preview_commands,
            "status": (
                "ready_no_execution"
                if not structural_failures and args.disposable_project
                else "refused_no_execution"
            ),
        },
        "failures": {
            "structural": structural_failures,
            "guard": guard_failures,
        },
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    request = report["request_checks"]
    plugin = report["installed_plugin_checks"]
    ae = report["running_ae_checks"]
    guard = report["proof_render_guard"]
    failures = report["failures"]
    lines = [
        "# OLMDistanceGradation 16bpc case0012/case0014 proof-render preflight",
        "",
        f"- Status: `{report['status']}`",
        f"- Claim boundary: `{report['claim_boundary']}`",
        f"- Canonical request: `{report['canonical_request_id']}`",
        f"- Canonical cases: `{', '.join(report['canonical_cases'])}`",
        (
            "- Canonical request manifest SHA-256: "
            f"`{report['canonical_request_identity']['request_manifest_sha256']}`"
        ),
        (
            "- Canonical reference manifest SHA-256: "
            f"`{report['canonical_request_identity']['reference_manifest_sha256']}`"
        ),
        f"- Request dir: `{request['request_dir']}`",
        f"- MediaCore bundle count: `{plugin.get('bundle_count')}`",
        f"- Installed bundle: `{plugin.get('bundle_path', '')}`",
        f"- Installed binary SHA-256: `{plugin.get('actual_sha256', '')}`",
        f"- Running AE PIDs: `{ae.get('pids', [])}`",
        f"- DG mapped in any running AE: `{ae.get('dg_binary_mapped_in_any_running_ae')}`",
        f"- Disposable-project flag supplied: `{guard['disposable_project_flag_supplied']}`",
        "",
        "## Structural checks",
        "",
        f"- Request check status: `{request.get('status')}`",
        (
            "- Request manifest hash matches canonical: "
            f"`{request.get('request_manifest_sha256_matches_canonical')}`"
        ),
        (
            "- Reference manifest hash matches canonical: "
            f"`{request.get('reference_manifest_sha256_matches_canonical')}`"
        ),
        f"- Installed plug-in check status: `{plugin.get('status')}`",
        f"- Running AE check status: `{ae.get('status')}`",
        "",
        "## Guard",
        "",
        "- Existing runner API is reused through `scripts/run_ae_single_case.py`.",
        "- The preflight does not launch AE, quit AE, or execute a render.",
    ]
    if failures["structural"]:
        lines.append(f"- Structural failures: `{json.dumps(failures['structural'])}`")
    if failures["guard"]:
        lines.append(f"- Guard failures: `{json.dumps(failures['guard'])}`")
    lines.extend(
        [
            "",
            "## Preview commands",
            "",
        ]
    )
    for row in guard["preview_commands"]:
        lines.append(f"- `{row['case_id']}`: `{row['shell_command']}`")
    lines.append("")
    return "\n".join(lines)


def write_report(path: Path | None, body: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def redact_local_paths(value: Any) -> Any:
    """Keep checked-in evidence portable without changing runtime checks."""
    replacements = {
        str(ROOT): "$REPO",
        str(Path.home()): "$HOME",
        tempfile.gettempdir(): "$TMP",
        str(Path(tempfile.gettempdir()).resolve()): "$TMP",
        "/private/tmp": "$TMP",
        "/tmp": "$TMP",
    }
    ordered = sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True)
    if isinstance(value, str):
        for source, replacement in ordered:
            value = value.replace(source, replacement)
        return value
    if isinstance(value, list):
        return [redact_local_paths(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_local_paths(item) for key, item in value.items()}
    return value


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = redact_local_paths(build_report(args))
    json_body = json.dumps(report, indent=2) + "\n"
    md_body = render_markdown(report)
    write_report(args.output_json, json_body)
    write_report(args.output_md, md_body)

    if args.output_json:
        print(f"[OK] wrote {args.output_json}")
    if args.output_md:
        print(f"[OK] wrote {args.output_md}")
    print(f"[INFO] status={report['status']}")

    if report["status"] == "ready_for_disposable_project_proof_render_no_execution":
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
