#!/usr/bin/env python3
"""Fail-closed smoke for the OLMSmoother2 case0012 live config contract.

This smoke ensures production has no render-path trace I/O and validates the shape of a
future same-run Windows return. It deliberately does not edit or execute
production plugin code, and it never promotes local replay config to live
truth.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
DEFAULT_PACKAGE = ROOT / "refs/runtime_trace_packages/olm_smoother2_current_aex_0012_typed_bind_read_20260710.zip"
TARGET_CASE = "legacy_case_0012_gamma5_red_blue_current_aex"
TARGET_PIXEL = [91, 841]

# These are the minimum values that must be emitted from one live call pair.
# They are schema requirements, not expected values. The local replay happens
# to use scale_fixed=[65536, 65536] and cce0 mode 0, but a live run may differ.
LIVE_FIELDS = (
    "observations.c280.config_raw_bytes",
    "observations.c280.config_pointer",
    "observations.c280.config_pointer_arithmetic",
    "observations.c280.scale_fixed",
    "observations.cce0.config_raw_bytes",
    "observations.cce0.config_pointer",
    "observations.cce0.config_pointer_arithmetic",
    "observations.cce0.mode_byte",
    "observations.cce0.mode_name",
)

CONFIG_BYTE_REQUIREMENTS = {
    "c280": {
        "raw_span": "the exact 8 bytes covering the two 32-bit scale fields",
        "field_offsets": {"scale_m": "+0x20", "scale_h": "+0x24"},
        "decoded_field": "scale_fixed",
    },
    "cce0": {
        "raw_span": "the exact gamma-context bytes through the mode byte",
        "field_offsets": {"gamma_value": "+0x00", "curve_index": "+0x04", "mode_byte": "+0x06"},
        "decoded_field": "mode_byte",
    },
}

DIAGNOSTIC_HOST_TRACE = (
    "stage=input_setup pixel_bytes=",
    "class_neighbor xy=",
    "params smoothness=",
    "polygon count=",
    "stage=orchestrator xy=",
)
FORBIDDEN_CONFIG_TRACE = (
    "c280_config",
    "cce0_config",
    "config_raw_bytes",
    "config_pointer_arithmetic",
    "cce0_mode_byte",
)


def get(value: Any, path: str) -> Any:
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def present(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, (list, dict)):
        return bool(value) and all(item is not None for item in value) if isinstance(value, list) else bool(value)
    return True


def load_return(path: Path | None) -> tuple[dict[str, Any] | None, str]:
    if path is None:
        return None, "no return supplied"
    if path.is_dir():
        candidates = list(path.rglob("RETURN.json")) + list(path.rglob("RETURN_RUNTIME_TRACE_RESULT.json"))
        if not candidates:
            return None, f"no return JSON under {path}"
        return json.loads(candidates[0].read_text(encoding="utf-8-sig")), str(candidates[0])
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(("RETURN.json", "RETURN_RUNTIME_TRACE_RESULT.json"))]
            if not names:
                return None, f"no return JSON in {path}"
            return json.loads(archive.read(names[0]).decode("utf-8-sig")), f"{path}:{names[0]}"
    return json.loads(path.read_text(encoding="utf-8-sig")), str(path)


def check(report: dict[str, Any], label: str, ok: bool, detail: str) -> None:
    report["checks"].append({"label": label, "status": "PASS" if ok else "BLOCKED", "detail": detail})
    if not ok:
        report["blockers"].append(label)


def audit_host_trace(report: dict[str, Any]) -> None:
    source = SOURCE.read_text(encoding="utf-8")
    check(report, "host_trace_source_present", SOURCE.is_file(), str(SOURCE))
    check(report, "host_trace_absent_from_production", all(item not in source for item in DIAGNOSTIC_HOST_TRACE), "Production render path performs no diagnostic trace I/O or duplicate polygon build.")
    check(report, "host_trace_config_gap", all(item not in source for item in FORBIDDEN_CONFIG_TRACE), "Current trace emits no c280/cce0 raw config bytes, pointer arithmetic, or cce0 mode byte.")


def audit_package(report: dict[str, Any], package: Path) -> None:
    check(report, "package_present", package.is_file(), str(package))
    if not package.is_file():
        return
    with zipfile.ZipFile(package) as archive:
        manifests = [name for name in archive.namelist() if name.endswith("/manifest.json")]
        manifest = json.loads(archive.read(manifests[0])) if manifests else {}
    check(report, "package_witness", manifest.get("case_id") == TARGET_CASE and manifest.get("pixel") == TARGET_PIXEL, "Typed-bind package remains scoped to case0012 at (91,841).")
    check(report, "package_one_fresh_run", manifest.get("run_policy") == "one_fresh_windows_run_for_bind_and_all_reads", "All observations must share one fresh Windows run.")


def audit_live_return(report: dict[str, Any], result: dict[str, Any] | None, source: str) -> None:
    if result is None:
        report["verdict"] = "BLOCKED_MISSING_LIVE_CONFIG_BINDING"
        report["facts"].append("No same-run live return was supplied; the existing package is a request package, not a config observation.")
        return
    check(report, "live_status", result.get("status") == "answered", f"status={result.get('status')!r}; exact_bind_failure is not a live answer.")
    check(report, "live_identity", get(result, "run.case_id") == TARGET_CASE and get(result, "run.pixel") == TARGET_PIXEL and present(get(result, "run.run_id")), "Run id, case, and pixel identify one fresh witness.")
    for field in LIVE_FIELDS:
        check(report, field, present(get(result, field)), "Required live config evidence is present in the same return.")
    if all(present(get(result, field)) for field in LIVE_FIELDS):
        report["verdict"] = "READY_FOR_LIVE_CONFIG_COMPARISON"
        report["facts"].append(f"Live return source: {source}")
    else:
        report["verdict"] = "BLOCKED_INCOMPLETE_LIVE_CONFIG_BINDING"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--return", dest="return_path", type=Path)
    parser.add_argument("--strict-live", action="store_true", help="return 2 unless a complete live config answer is supplied")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "schema": "olmsmoother2_case0012_live_config_contract_v1",
        "scope": "case0012 c280/cce0 live config capture; no production edits",
        "target": {"case_id": TARGET_CASE, "pixel": TARGET_PIXEL, "idx": 105, "descriptor": [91, 841, 1, 91, 843, 5]},
        "required_live_fields": list(LIVE_FIELDS),
        "config_byte_requirements": CONFIG_BYTE_REQUIREMENTS,
        "local_replay_baseline": {"c280_scale_fixed": [65536, 65536], "cce0_mode_byte": 0, "claim": "schema evidence only"},
        "verdict": "BLOCKED_MISSING_LIVE_CONFIG_BINDING",
        "checks": [],
        "blockers": [],
        "facts": [],
    }
    audit_host_trace(report)
    audit_package(report, args.package.resolve())
    result, source = load_return(args.return_path.resolve() if args.return_path else None)
    audit_live_return(report, result, source)
    print(json.dumps(report, indent=2, sort_keys=True))

    host_ok = all(item["status"] == "PASS" for item in report["checks"] if item["label"].startswith("host_trace_"))
    package_ok = all(item["status"] == "PASS" for item in report["checks"] if item["label"].startswith("package_"))
    live_ok = report["verdict"] == "READY_FOR_LIVE_CONFIG_COMPARISON"
    if not host_ok or not package_ok:
        return 1
    if args.strict_live and not live_ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
