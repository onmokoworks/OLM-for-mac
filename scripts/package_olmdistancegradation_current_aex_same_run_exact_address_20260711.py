#!/usr/bin/env python3
"""Build the 2026-07-11 strict current-AEX DG exact-address package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import zipfile
from pathlib import Path
from typing import Any


REQUEST_ID = "olmdistancegradation_current_aex_same_run_exact_address_20260711"
PROFILE = "distancegradation-current-aex-same-run-exact-address"
CONTRACT = Path("refs/conformance/olmdistancegradation_current_aex_same_run_exact_address_contract_20260711.md")
REQUEST = Path("handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625")
RUNNER = Path("scripts/run_olmdistancegradation_current_aex_same_run_exact_address_20260711.ps1")
JSX = Path("scripts/ae_render_olmdistancegradation_current_aex_queue_20260711.jsx")
SINGLE_JSX = Path("scripts/ae_render_single_case.jsx")
COMPLETE_FIXTURE = Path("scripts/olmdg_current_aex_same_run_complete_stdout_20260711.txt")
MISSING_FIXTURE = Path("scripts/olmdg_current_aex_same_run_missing_stdout_20260711.txt")
DEAD_FIXTURE = Path("scripts/olmdg_current_aex_same_run_dead_stdout_20260711.txt")
CASES = {
    "olmdistancegradation_extended__case_0010": ("0010", (6, 40), (901, 394)),
    "olmdistancegradation_extended__case_0011": ("0011", (6, 40), (901, 394)),
}


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def dumps(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def action() -> dict[str, Any]:
    return {
        "request_id": REQUEST_ID,
        "plugin_area": "OLMDistanceGradation current-AEX 16bpc same-run field/compose/writer witness",
        "mode": "external-trace",
        "command": (
            "Run one fresh current-AEX Software AE/CDB session using the packaged "
            "run_olmdistancegradation_current_aex_same_run_exact_address_20260711.ps1. Its queue renders case_0010 and case_0011 serially "
            "and binds both (6,40) and "
            "(901,394) by output address; retain the live field-world header/base, RCX+2, "
            "source RDX+2, compose scalar bit patterns, output address/store word, and final writer."
        ),
        "stop_condition": (
            "Return one run_id shared by all four case/XY records. Every record must contain "
            "field_base/header/rowbytes/pixel_size, RCX address and word at +2, RDX address "
            "and word at +2, output address/store word, compose scalar bits, and final writer. "
            "Any absent live field is exact_bind_failure; answered_partial is forbidden."
        ),
    }


def template() -> dict[str, Any]:
    required = [
        "run_id", "case_id", "xy", "current_aex", "entry_case_tag", "entry_inside_threshold", "entry_outside_threshold", "field_world", "rcx_field_addr",
        "rcx_field_word_at_plus_2", "rdx_source_addr", "rdx_source_word_at_plus_2",
        "output_addr", "output_store_word", "compose_scalar_bits", "final_writer",
    ]
    records = []
    for case_id, (_, first, second) in CASES.items():
        for xy in (first, second):
            records.append({
                "run_id": None,
                "case_id": case_id,
                "xy": list(xy),
                "current_aex": {"module": "DistanceGradation.aex", "sha256": None, "module_base": None},
                "field_world": {
                    "base": None, "header": None, "rowbytes": None, "pixel_size": 8,
                    "channel_layout": "PF_Pixel16 / 4xuint16",
                },
                "rcx_field_addr": None,
                "rcx_field_word_at_plus_2": None,
                "rdx_source_addr": None,
                "rdx_source_word_at_plus_2": None,
                "output_addr": None,
                "output_store_word": None,
                "compose_scalar_bits": {"xmm1": None, "xmm2": None, "xmm4": None, "xmm5": None},
                "final_writer": {"site": "DistanceGradation+0x1170814", "xmm": None, "pf16_words": None},
            })
    return {
        "schema": "olmdg_current_aex_same_run_exact_address_v1",
        "kind": "olm_runtime_trace_result",
        "results": [{
            "request_id": REQUEST_ID,
            "status": "answered | exact_bind_failure",
            "summary": "Fill only from one same-run current-AEX session; never use answered_partial.",
            "observations": {
                "classification": "answered | exact_bind_failure",
                "required_fields": required,
                "entry": {
                    "run_id": None, "module_base": None, "output_base": None,
                    "source_base": None, "output_rowbytes": 15360, "output_pixel_size": 8,
                },
                "witnesses": records,
                "failure": {"stage": None, "reason": None, "missing_fields": [], "last_observation": None},
            },
        }],
    }


def manifest(timestamp: str) -> dict[str, Any]:
    return {
        "schema": 1,
        "kind": "olm_runtime_trace_request_package",
        "profile": PROFILE,
        "request_id": REQUEST_ID,
        "packaged_at": timestamp,
        "entrypoint": CONTRACT.as_posix(),
        "runtime_actions": [action()],
    }


def main() -> int:
    parsed = args()
    repo = root()
    output = parsed.output or repo / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_current_aex_same_run_exact_address_20260711.zip"
    output = output if output.is_absolute() else repo / output
    required = [repo / CONTRACT, repo / RUNNER, repo / JSX, repo / SINGLE_JSX, repo / COMPLETE_FIXTURE, repo / MISSING_FIXTURE, repo / DEAD_FIXTURE, repo / REQUEST / "request_manifest.json", repo / REQUEST / "reference_manifest.json"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    for suffix, _, _ in CASES.values():
        for kind in ("input", "expected"):
            name = next((c["before_effects_frame"] if kind == "input" else c["frame"] for c in json.loads((repo / REQUEST / "request_manifest.json").read_text())["cases"] if c["id"].endswith(f"case_{suffix}")), None)
            if not name or not (repo / REQUEST / kind / name).is_file():
                raise FileNotFoundError(f"missing {kind} fixture for case {suffix}")
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("README_RUNTIME_TRACE.md", (repo / CONTRACT).read_text(encoding="utf-8"))
        archive.writestr("runtime_trace_package_manifest.json", dumps(manifest(timestamp)))
        archive.writestr("RETURN_RUNTIME_TRACE_TEMPLATE.json", dumps(template()))
        archive.write(repo / CONTRACT, CONTRACT.as_posix())
        archive.write(repo / RUNNER, "artifacts/run_olmdistancegradation_current_aex_same_run_exact_address_20260711.ps1")
        archive.write(repo / JSX, JSX.as_posix())
        archive.write(repo / SINGLE_JSX, SINGLE_JSX.as_posix())
        archive.writestr("fixtures/complete_cdb_stdout_20260711.txt", (repo / COMPLETE_FIXTURE).read_text(encoding="utf-8").replace("\\n\n", "\n"))
        archive.writestr("fixtures/missing_cdb_stdout_20260711.txt", (repo / MISSING_FIXTURE).read_text(encoding="utf-8").replace("\\n\n", "\n"))
        archive.writestr("fixtures/dead_cdb_stdout_20260711.txt", (repo / DEAD_FIXTURE).read_text(encoding="utf-8").replace("\\n\n", "\n"))
        archive.write(repo / REQUEST / "request_manifest.json", (REQUEST / "request_manifest.json").as_posix())
        archive.write(repo / REQUEST / "reference_manifest.json", (REQUEST / "reference_manifest.json").as_posix())
        request_data = json.loads((repo / REQUEST / "request_manifest.json").read_text())
        for case in request_data["cases"]:
            if case["id"] not in CASES:
                continue
            for kind, key in (("input", "before_effects_frame"), ("expected", "frame")):
                source = repo / REQUEST / kind / case[key]
                archive.write(source, (REQUEST / kind / case[key]).as_posix())
    print(f"[OK] runtime trace package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
