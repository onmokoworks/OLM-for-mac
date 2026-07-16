#!/usr/bin/env python3
"""Package the bounded OLMSmoother2 in-process collector Windows witness."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.compiler import compile_witness  # noqa: E402


SOURCE_ROOT = ROOT / "refs/windows_witness_specs/olmsmoother2_legacy_key_producer_common_core_20260716"
SOURCE_SPEC = SOURCE_ROOT / "witness-spec.json"
REQUEST_ID = "olmsmoother2_legacy_upstream_classplane_inprocess_20260716"
RUN_ID_PREFIX = "smoother2-legacy-upstream-classplane-inprocess"
QUEUE_PROFILE = "olmsmoother2-legacy-upstream-classplane-inprocess"
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
OUTPUT_DIR = ROOT / "refs/runtime_trace_packages/windows_witness_olmsmoother2_legacy_upstream_classplane_inprocess_20260716"
OUTPUT_ZIP = OUTPUT_DIR.with_suffix(".zip")
ARM_TIMEOUT_SECONDS = 30
CAPTURE_TIMEOUT_SECONDS = 300
COLLECTOR_TIMEOUT_MS = 300000
REQUIRED_OUTPUTS = ["collector_trace.txt", "collector_status.json", "collector.jsonl"]
FIXTURE_PROBES = [
    {"name": "writer_anchor", "rva": "0x350b"},
    {"name": "c280_entry", "rva": "0xc280"},
    {"name": "cardinal_10760", "rva": "0x10760"},
    {"name": "d3b0_entry", "rva": "0xd3b0"},
    {"name": "da50_entry", "rva": "0xda50"},
    {"name": "fef0_entry", "rva": "0xfef0"},
    {"name": "e170_entry", "rva": "0xe170", "return_rva": "0xf284"},
    {"name": "e170_return", "rva": "0xf284"},
    {"name": "f270_entry", "rva": "0xf270", "return_rva": "0xff5b"},
    {"name": "f270_return", "rva": "0xff5b"},
    {"name": "e3a0_entry", "rva": "0xe3a0", "return_rva": "0xff5b"},
    {"name": "e3a0_return0", "rva": "0xe3f4"},
    {"name": "e3a0_return1", "rva": "0xe420"},
]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--injector", type=Path, required=True, help="Path to the real injector .exe")
    parser.add_argument("--collector-dll", type=Path, required=True, help="Path to the real collector .dll")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=OUTPUT_ZIP)
    return parser.parse_args(argv)


def _resolve_binary(path: Path, *, suffix: str, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.suffix.lower() != suffix:
        raise SystemExit(f"{label} must use the {suffix} extension: {resolved}")
    if not resolved.is_file():
        raise SystemExit(f"{label} is missing: {resolved}")
    if resolved.stat().st_size <= 0:
        raise SystemExit(f"{label} must be a non-empty file: {resolved}")
    return resolved


def _resolve_output(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _load_source_spec() -> dict[str, Any]:
    return json.loads(SOURCE_SPEC.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _config_template(aex_sha256: str) -> str:
    payload = {
        "run_id": "{{RUN_ID}}",
        "ae_pid": "{{AE_PID}}",
        "case_id": "{{CASE_ID}}",
        "project_bpc": 8,
        "renderer": "Software",
        "module": "OLMSmoother2.aex",
        "sha256": aex_sha256,
        "output_dir": "{{OUTPUT_DIR}}",
        "target_x": 91,
        "target_y": 841,
        "timeout_ms": COLLECTOR_TIMEOUT_MS,
        "probes": FIXTURE_PROBES,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    return text.replace('"{{AE_PID}}"', "{{AE_PID}}")


def _build_temp_spec(temp_root: Path, injector: Path, collector_dll: Path) -> Path:
    spec_root = temp_root / REQUEST_ID
    shutil.copytree(SOURCE_ROOT, spec_root)

    spec = _load_source_spec()
    plugin = spec["plugin"]
    queue = spec["queue"]
    spec["request_id"] = REQUEST_ID
    spec["run_id_prefix"] = RUN_ID_PREFIX
    spec["description"] = (
        "One fresh AE2025 Software 8bpc case0012 run using the bounded x64 "
        "in-process collector transport. The same run captures the upstream "
        "c280/cardinal6/d3b0/da50/fef0 origin and descriptor lane before the "
        "already grounded e170/f270/e3a0 producer chain. Final writer bytes and PNG/export output "
        "remain outside acceptance. Known host limitation: packaging and smoke only "
        "verify deterministic package structure and fail-closed contracts here; "
        "they do not claim Windows executability on this host."
    )
    queue["profile"] = QUEUE_PROFILE
    queue["command"] = (
        "Run one fresh AE2025 Software 8bpc case0012 render at (91,841), bind one "
        "PID/module/AEX identity, inject the bounded same-bitness collector, and "
        "capture producer returns through the concrete in-process probe RVAs."
    )
    queue["stop_condition"] = (
        "answered only when collector armed/ok status, bind, c280/cardinal6/"
        "d3b0/da50/fef0 upstream events, e170/f270/e3a0 return events, class "
        "base/stride reads, vertex count, first vertex RGBA, weight, and same-run "
        "identity all validate; otherwise exact_bind_failure"
    )
    spec.pop("cdb", None)
    host = spec.get("host")
    if isinstance(host, dict):
        host.pop("cdb_path", None)
    spec["transport"] = {
        "kind": "in_process_collector",
        "injector_path": "olm_injector.exe",
        "collector_dll": "olm_smoother2_collector.dll",
        "config_template": "collector-config.json.in",
        "required_outputs": REQUIRED_OUTPUTS,
        "arm_timeout_seconds": ARM_TIMEOUT_SECONDS,
        "capture_timeout_seconds": CAPTURE_TIMEOUT_SECONDS,
    }
    for case in spec["cases"]:
        case.pop("cdb_template", None)

    request_manifest_path = spec_root / "request" / "request_manifest.json"
    request_manifest = json.loads(request_manifest_path.read_text(encoding="utf-8-sig"))
    request_manifest["request_id"] = REQUEST_ID
    _write_json(request_manifest_path, request_manifest)

    (spec_root / "olm_injector.exe").write_bytes(injector.read_bytes())
    (spec_root / "olm_smoother2_collector.dll").write_bytes(collector_dll.read_bytes())
    (spec_root / "collector-config.json.in").write_text(
        _config_template(str(plugin["aex_sha256"])),
        encoding="ascii",
        newline="\n",
    )
    _write_json(spec_root / "witness-spec.json", spec)
    return spec_root / "witness-spec.json"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    injector = _resolve_binary(args.injector, suffix=".exe", label="injector")
    collector_dll = _resolve_binary(args.collector_dll, suffix=".dll", label="collector DLL")
    output_dir = _resolve_output(args.output_dir).resolve()
    zip_path = _resolve_output(args.zip_path).resolve()

    with tempfile.TemporaryDirectory(prefix="olmsmoother2_inprocess_collector_") as raw:
        spec_path = _build_temp_spec(Path(raw), injector, collector_dll)
        package, archive = compile_witness(spec_path, output_dir, zip_path)

    print(
        json.dumps(
            {
                "status": "ok",
                "package": str(package),
                "zip": str(archive),
                "request_id": REQUEST_ID,
                "transport": "in_process_collector",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
