#!/usr/bin/env python3
"""Record the actual exported Distance Smart owner boundary after generic host work."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
INPUT = ROOT / (
    "refs/runtime_trace_packages/"
    "olm_runtime_trace_olmdistancegradation_8bpc_case0001_anchor00_residual17_20260716/"
    "request/input/case_0001_before_effects.png"
)
REPORT = ROOT / "refs/conformance/olmdistancegradation_exported_upstream_owner_seam_20260811.json"
DOC = ROOT / "refs/conformance/olmdistancegradation_exported_upstream_owner_seam_20260811.md"
DEFAULT_WORKER = Path(
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker"
)
PARAMETERS = [
    "Invert=1",
    "In/Out=1",
    "Inside Threshold=4",
    "Outside Threshold=4",
    "Render Mode=1",
    "Use Background Color=0",
    "Gradation Color=255,28,0,238",
    "BG Color =255,16,160,48",
    "Interpolation Mode=1",
    "Power=1",
    "Blur Mode=2",
    "Blur Size=1",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(DEFAULT_WORKER)))
    if not worker.is_file():
        raise RuntimeError(f"AEXCompat worker missing: {worker}")
    with tempfile.TemporaryDirectory(prefix="dg_exported_owner_") as temporary:
        output = Path(temporary) / "output.png"
        run = subprocess.run(
            [
                str(worker),
                "render-png",
                str(AEX),
                str(INPUT),
                str(output),
                "--pixel-format",
                "argb8",
                *PARAMETERS,
            ],
            text=True,
            capture_output=True,
        )
    payload = json.loads(run.stdout)
    expected_error = "unsupported Win64 import: kernel32.dll!LoadLibraryW"
    assert run.returncode != 0
    assert expected_error in payload["error"]
    assert payload["gpu"]["pre_render"] == {
        "selector": "SMART_PRE_RENDER",
        "attempted": True,
        "completed": True,
        "error": 0,
    }
    assert payload["gpu"]["render"]["attempted"]
    assert not payload["gpu"]["render"]["completed"]
    assert payload["gpu"]["cleanup_complete"]
    assert not payload["unsupported_suite_calls"]

    report = {
        "schema": "olmdistancegradation.exported-upstream-owner-seam/1",
        "status": "BLOCKED_AFTER_SMART_PRE_RENDER_AT_LOAD_LIBRARY_W",
        "actual_aex_sha256": sha256(AEX),
        "aexcompat_worker": {
            "path": str(worker),
            "sha256": sha256(worker),
            "modified_by_olm_task": False,
        },
        "actual_exported_probe": payload,
        "representative_parameters": PARAMETERS,
        "numerical_family_already_exact": {
            "cells": 24,
            "product": "PF8/PF16/PF32 x Constant/Linear x Blur2/3 x Background off/on",
            "evidence": [
                "refs/conformance/olmdistancegradation_classic_pf8_blur_background_family_exact_20260810.md",
                "refs/conformance/olmdistancegradation_classic_pf16_blur_background_family_exact_20260810.md",
                "refs/conformance/olmdistancegradation_classic_pf32_blur_background_family_exact_20260810.md",
            ],
        },
        "owner_facts": {
            "smart_pre_render": "completed with error 0",
            "smart_render": "entered, then stopped before numerical completion at LoadLibraryW",
            "legacy_pf8_pf16_render": "typed composition of a preseeded green-lane field only",
            "legacy_pf32_render": "separate classic whole owner FUN_181172a10",
        },
        "next_required_generic_abi": (
            "kernel32!LoadLibraryW with bounded loaded-module/path resolution, reference lifetime, "
            "failure return, and last-error semantics"
        ),
        "claims_not_made": [
            "No exported SmartRender output comparison",
            "No proof that SmartRender reaches FUN_181174760 field generation",
            "No PF32 SmartRender route; the actual AEX has none",
            "No native After Effects execution in this probe",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMDistanceGradation exported upstream owner seam\n\n"
        f"Status: **{report['status']}**.\n\n"
        "The unchanged 2025 Windows AEX completes exported `SMART_PRE_RENDER` with error 0, "
        "enters `SMART_RENDER`, and now passes the previously missing `tolower`, `toupper`, "
        "`GetModuleHandleExA`, and `GetModuleFileNameW` host boundaries. It next stops "
        "explicitly at the generic `kernel32.dll!LoadLibraryW` import; cleanup completes and "
        "there are no unsupported Adobe suite calls.\n\n"
        "The bounded numerical product is already exact for 24 cells: PF8/PF16/PF32 × "
        "Constant/Linear × Blur Mode 2/3 × Background off/on. That evidence covers the actual "
        "field-generation/blur/typed-compose or PF32 whole-owner numerical chains, but it does "
        "not yet promote them to an exported Smart owner claim. PF8/PF16 legacy `PF_Cmd_RENDER` "
        "remains compose-only over a preseeded green-lane field, and the actual AEX exposes no "
        "PF32 SmartRender branch.\n\n"
        "The next host requirement is bounded, generic `LoadLibraryW` module/path resolution and "
        "lifetime/error semantics. No AEXCompat source was changed by this OLM evidence commit.\n"
    )
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
