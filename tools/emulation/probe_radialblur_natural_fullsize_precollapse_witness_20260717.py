#!/usr/bin/env python3
"""Fail-closed gate for the bounded natural full-size RadialBlur witness.

The prior natural checkpoint is setup evidence, not a resumable Unicorn
snapshot.  This probe deliberately refuses to rerun the unprefilled 250M
instruction path.  It becomes executable only when a checkpoint carries the
full-size worker state required for the actual B150/A9D0 witness rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = ROOT / "refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.json"
DEFAULT_JSON = ROOT / "refs/conformance/olmradialblur_natural_fullsize_precollapse_witness_20260717.json"
DEFAULT_MD = ROOT / "refs/conformance/olmradialblur_natural_fullsize_precollapse_witness_20260717.md"
TARGETS = ((1047, 1095), (1047, 1096), (1048, 1095), (1048, 1096))
EXPECTED = {
    "case_id": "case_0009",
    "entry": "0x1800056f0",
    "b150": "0x18000b150",
    "a9d0": "0x18000a9d0",
    "stop_before_collapse": "0x180005c9f",
    "rgba_plane": "work+0x4210",
    "scalar_plane": "work+0x4218",
    "max_instructions": 2_000_000,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    report: dict[str, Any] = {
        "kind": "olmradialblur_natural_fullsize_precollapse_witness_20260717",
        "schema": 1,
        "status": "blocked",
        "classification": "blocked-fail-closed-no-resumable-full-size-checkpoint",
        "claim_boundary": "natural case_0009 full-size pre-collapse witness only; no production, Windows, or AE-exact claim",
        "target": {**EXPECTED, "cells": [list(x) for x in TARGETS]},
        "provenance": {"checkpoint": str(args.checkpoint.relative_to(ROOT)) if args.checkpoint.is_relative_to(ROOT) else str(args.checkpoint)},
    }
    if not args.checkpoint.exists():
        report["blocker"] = "checkpoint-after-setup is missing"
    else:
        report["provenance"]["checkpoint_sha256"] = sha(args.checkpoint)
        try:
            checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report["blocker"] = f"checkpoint cannot be read: {exc}"
        else:
            report["checkpoint_status"] = checkpoint.get("status")
            harness = checkpoint.get("harness", {})
            report["checkpoint_scope"] = {
                "source_geometry": harness.get("source_geometry"),
                "max_instructions": harness.get("max_instructions"),
                "python_prefill": harness.get("python_prefill"),
                "worker_detour": harness.get("worker_detour"),
                "has_resumable_full_size_state": bool(checkpoint.get("full_size_state")),
            }
            if checkpoint.get("status") != "pass":
                report["blocker"] = "checkpoint-after-setup is not pass"
            elif not checkpoint.get("full_size_state"):
                report["blocker"] = (
                    "setup checkpoint has no resumable full-size worker state; "
                    "refusing to rerun the unchanged unprefilled 250M path"
                )
            else:
                report["blocker"] = "executor not enabled for an unrecognized checkpoint state"

    report["required_observation"] = {
        "actual_calls": [EXPECTED["b150"], EXPECTED["a9d0"]],
        "stop_rip": EXPECTED["stop_before_collapse"],
        "raw_float32": [EXPECTED["rgba_plane"], EXPECTED["scalar_plane"]],
        "cells": [list(x) for x in TARGETS],
        "classification_rule": "residual-driving only if all four RGBA/scalar rows are captured before collapse and the state is nonzero or differs from the accepted upstream baseline",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMRadialBlur natural full-size pre-collapse witness (2026-07-17)", "",
        f"- Status: `{report['status']}`",
        f"- Classification: `{report['classification']}`",
        "- No B150/A9D0 execution was attempted because the reusable checkpoint is not a resumable full-size state.",
        f"- Blocker: `{report['blocker']}`",
        "- Required bounded run: actual B150 and A9D0, stop at `0x180005c9f`, then dump raw float32 RGBA/scalar at the four requested cells from `work+0x4210`/`work+0x4218`.",
        "- Residual-driving classification: `undetermined`; no pre-collapse witness values were captured.",
    ]
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
