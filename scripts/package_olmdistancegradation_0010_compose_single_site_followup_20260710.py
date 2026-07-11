#!/usr/bin/env python3
"""Build the focused OLMDistanceGradation case_0010 single-site trace package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import zipfile
from pathlib import Path
from typing import Any


REQUEST_ID = "olmdistancegradation_0010_compose_single_site_followup_20260710"
PROFILE = "distancegradation-0010-compose-single-site-followup"
HARDWARE_REQUEST_ID = "olmdistancegradation_0010_compose_single_site_hardware_break_retry_20260710"
HARDWARE_PROFILE = "distancegradation-0010-compose-single-site-hardware-break-retry"
HARDWARE_BREAKPOINTS = False
TARGET_X = 6
TARGET_Y = 40
SITES = ("field", "source", "writer")
CONTRACT_REL = Path("refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md")
REQUEST_REL = Path(
    "handoff/ae_pixel_validation_20260618/requests/"
    "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
)
CASE_INPUT = (
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0010_before_effects.png"
)
CASE_EXPECTED = (
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0010.png"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--hardware-breakpoints",
        action="store_true",
        help="Build the dormant ba e 1 successor instead of the software-bp request.",
    )
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--target-x", type=int, default=6)
    parser.add_argument("--target-y", type=int, default=40)
    parser.add_argument(
        "--sites",
        nargs="+",
        choices=("field", "source", "writer"),
        default=["field", "source", "writer"],
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md"),
        help="Repository-relative contract to include as the package authority.",
    )
    return parser.parse_args()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def runtime_action() -> dict[str, Any]:
    breakpoint_note = (
        "Use -UseHardwareBreakpoints so both stops are execute hardware breakpoints (`ba e 1`). "
        if HARDWARE_BREAKPOINTS
        else "Use the default software breakpoints. "
    )
    site_offsets = {"field": "0x117057d", "source": "0x11705f1", "writer": "0x1170814"}
    site_matrix = ", ".join(f"{site} at +{site_offsets[site]}" for site in SITES)
    return {
        "request_id": REQUEST_ID,
        "plugin_area": "OLMDistanceGradation 16bpc case_0010 exact compose input/store binding",
        "mode": "external-trace",
        "command": (
            breakpoint_note
            + f"Run only olmdistancegradation_extended__case_0010 at target ({TARGET_X},{TARGET_Y}). "
            f"Execute the packaged PowerShell launcher once for each requested Site: {site_matrix}. "
            "Each invocation must retain only the entry breakpoint and its selected downstream "
            "breakpoint, derive target_output from the live output callback argument, and accept "
            "the downstream hit only when RDI == target_output. Return typed RCX field words, "
            "typed RDX source words, writer XMM inputs/PF16 words, or the exact failed gate."
        ),
        "stop_condition": (
            f"Satisfactory: the requested {','.join(SITES)} run(s) for ({TARGET_X},{TARGET_Y}) bind the exact RDI address "
            "and fill the matching return-template fields. Partial: field or source alone is typed, "
            "or a miss retains the entry address and exact gate failure. Reject rbp=y, broad r9=x, "
            "multiple downstream sites in one run, PNG-only evidence, or package-local recomputation."
        ),
    }


def manifest(packaged_at: str) -> dict[str, Any]:
    return {
        "schema": 1,
        "kind": "olm_runtime_trace_request_package",
        "profile": PROFILE,
        "packaged_at": packaged_at,
        "repo_root_name": "OLM as",
        "entrypoint": CONTRACT_REL.as_posix(),
        "runtime_actions": [runtime_action()],
    }


def site_result(site: str, offset: str) -> dict[str, Any]:
    common: dict[str, Any] = {
        "site": site,
        "downstream_address": f"DistanceGradation+0x{offset}",
        "status": "hit | missed | not_run",
        "console_log": None,
        "rdi": None,
        "target_output": None,
        "rdi_equals_target_output": None,
        "failed_gate_or_breakpoint_reason": None,
    }
    if site == "field":
        common.update(
            {
                "rcx_field_addr": None,
                "rcx_field_words_u16": None,
                "field_base_from_static_relation": None,
                "field_rowbytes": None,
                "field_pixel_size": 8,
                "field_channel_layout": "PF_Pixel16 / 4xuint16",
                "live_x_r9d": None,
                "live_y_r8d": None,
                "xmm0_scale": None,
                "xmm1_field_scalar": None,
                "xmm2_field_transform": None,
                "xmm4_field_channel": None,
                "xmm5_field_channel": None,
            }
        )
    elif site == "source":
        common.update(
            {
                "rdx_source_addr": None,
                "rdx_source_words_u16": None,
                "source_base_from_static_relation": None,
                "source_rowbytes": None,
                "source_pixel_size": 8,
                "source_channel_layout": "PF_Pixel16 / 4xuint16",
                "source_scalars": {
                    "xmm7_alpha": None,
                    "xmm11_green": None,
                    "xmm12_red": None,
                    "xmm13_blue": None,
                },
            }
        )
    else:
        common.update(
            {
                "prestore_xmm": {"xmm1": None, "xmm4": None, "xmm5": None, "xmm6": None},
                "final_pf16_words_at_rdi": None,
                "note": "+0x1170814 is before blue conversion/store; record words again after continuation if practical.",
            }
        )
    return common


def return_template() -> dict[str, Any]:
    return {
        "schema": 1,
        "kind": "olm_runtime_trace_result",
        "results": [
            {
                "request_id": REQUEST_ID,
                "status": "answered | answered_partial | failed_partial",
                "summary": f"Fill with the case_0010 ({TARGET_X},{TARGET_Y}) single-site exact-address witness.",
                "observations": {
                    "classification": "answered | answered_partial | failed_partial",
                    "effect": "OLM Distance Gradation",
                    "case_id": "olmdistancegradation_extended__case_0010",
                    "target_xy": [TARGET_X, TARGET_Y],
                    "gating_relation": f"RDI == output_base + {TARGET_Y}*0x3c00 + {TARGET_X}*8",
                    "entry": {
                        "module_base": None,
                        "entry_x_edx": None,
                        "entry_y_r8d": None,
                        "output_argument": None,
                        "source_argument": None,
                        "output_base": None,
                        "target_output": None,
                        "output_rowbytes": 15360,
                        "output_pixel_size": 8,
                        "output_channel_layout": "PF_Pixel16 / 4xuint16",
                    },
                    "site_runs": {
                        site: site_result(
                            site,
                            {"field": "117057d", "source": "11705f1", "writer": "1170814"}[site],
                        )
                        for site in SITES
                    },
                    "breakpoint_instability_observed": None,
                    "hardware_breakpoints_used": HARDWARE_BREAKPOINTS,
                    "artifacts_returned": [],
                },
            }
        ],
    }


def readme() -> str:
    flag = " -UseHardwareBreakpoints" if HARDWARE_BREAKPOINTS else ""
    commands = "\n".join(
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File "
        ".\\artifacts\\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 "
        f"-Site {site} -X {TARGET_X} -Y {TARGET_Y}{flag}"
        for site in SITES
    )
    return f"""# OLMDistanceGradation Single-Site Windows Handoff

Authoritative request: `{REQUEST_ID}`

Read `{CONTRACT_REL.as_posix()}` first.
The package is self-contained for case_0010: preserve its directory tree after extraction.

From the extracted package root, run:

```powershell
{commands}
```

Each command creates a separate result folder under the launcher's `-WorkRoot`.
Return the requested console/log folder(s) with a filled `RETURN_RUNTIME_TRACE_TEMPLATE.json`.
Do not run both target pixels or multiple downstream sites in one invocation.
"""


def snapshot(packaged_at: str) -> dict[str, Any]:
    return {
        "kind": "focused_runtime_trace_package_snapshot",
        "generated_at": packaged_at,
        "request_id": REQUEST_ID,
        "runtime_actions": [runtime_action()],
    }


def main() -> int:
    global REQUEST_ID, PROFILE, HARDWARE_BREAKPOINTS, TARGET_X, TARGET_Y, SITES, CONTRACT_REL
    args = parse_args()
    HARDWARE_BREAKPOINTS = args.hardware_breakpoints
    if HARDWARE_BREAKPOINTS:
        REQUEST_ID = HARDWARE_REQUEST_ID
        PROFILE = HARDWARE_PROFILE
    if args.request_id:
        REQUEST_ID = args.request_id
    if args.profile:
        PROFILE = args.profile
    TARGET_X = args.target_x
    TARGET_Y = args.target_y
    SITES = tuple(args.sites)
    root = repo_root()
    contract = args.contract if args.contract.is_absolute() else root / args.contract
    if not contract.is_file():
        raise SystemExit(f"contract not found: {contract}")
    CONTRACT_REL = Path("refs/conformance") / contract.name
    default_name = (
        "olmdistancegradation_0010_compose_single_site_hardware_break_retry_windows_20260710.zip"
        if HARDWARE_BREAKPOINTS
        else "olmdistancegradation_0010_compose_single_site_followup_windows_20260710.zip"
    )
    requested_output = args.output or root / "refs/runtime_trace_packages" / default_name
    output = requested_output if requested_output.is_absolute() else root / requested_output
    output.parent.mkdir(parents=True, exist_ok=True)
    packaged_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    files = {
        f"refs/conformance/{contract.name}": contract,
        "artifacts/run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1": root
        / "scripts/run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1",
        "scripts/ae_render_single_case.jsx": root / "scripts/ae_render_single_case.jsx",
        f"{REQUEST_REL.as_posix()}/request_manifest.json": root / REQUEST_REL / "request_manifest.json",
        f"{REQUEST_REL.as_posix()}/reference_manifest.json": root / REQUEST_REL / "reference_manifest.json",
        f"{REQUEST_REL.as_posix()}/input/{CASE_INPUT}": root / REQUEST_REL / "input" / CASE_INPUT,
        f"{REQUEST_REL.as_posix()}/expected/{CASE_EXPECTED}": root / REQUEST_REL / "expected" / CASE_EXPECTED,
    }
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing package inputs: {missing}")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("README_RUNTIME_TRACE.md", readme().encode("utf-8"))
        archive.writestr("runtime_trace_package_manifest.json", json_bytes(manifest(packaged_at)))
        archive.writestr("RETURN_RUNTIME_TRACE_TEMPLATE.json", json_bytes(return_template()))
        archive.writestr("next_reference_actions_snapshot.json", json_bytes(snapshot(packaged_at)))
        for archive_name, source in files.items():
            archive.write(source, archive_name)
    print(f"[OK] runtime trace package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
