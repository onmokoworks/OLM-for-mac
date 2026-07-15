#!/usr/bin/env python3
"""Prove the local AEX schedule distinction between angle 0 and diagonal control."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT_JSON = ROOT / "refs/conformance/olmdirectionalblur_angle0_diagonal_schedule_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmdirectionalblur_angle0_diagonal_schedule_20260716.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(source: Path, output: Path, angle: int) -> dict:
    command = [
        sys.executable,
        str(FIXTURE),
        "--source", str(source),
        "--output", str(output),
        "--angle", str(angle),
        "--downsample-num", "1",
        "--downsample-den", "1",
        "--front-strength", "48",
        "--size-variation", "0",
        "--front-sharp-tail", "0",
        "--back-strength", "0",
        "--back-alpha-fade", "0",
        "--noise-variation", "0",
        "--max-instructions", "200000000",
        "--schedule-only-rowdriver",
        "--detour-rotate",
        "--detour-rowdriver",
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    report = json.loads(output.read_text(encoding="utf-8"))
    execution = report["execution"]
    assert report["status"] == "blocked"
    assert report["blocked"]["reason"] == "pre-render-return"
    assert report["output"]["complete"] is False
    assert len(execution["rotate_detours"]) == 1
    assert len(execution["iterate_calls"]) == 1
    assert len(execution["rowdriver_detours"]) == 26
    assert execution["checkpoints"]["schedule_complete"]["stop"] == "0x180005554"
    assert execution["iterate_calls"][0]["area_words"] == [0, 0, 16, 16]
    return report


def compact_case(report: dict) -> dict:
    execution = report["execution"]
    rotate = execution["rotate_detours"][0]
    context = execution["param_context"]
    return {
        "requested_angle_degrees": report["param_def_case_values"]["1"]["value"],
        "materialized_angle_radians": context["angle_radians"],
        "materialized_angle_bits": rotate["angle_bits"],
        "materialized_angle_degrees": math.degrees(rotate["angle"]),
        "rotate_dimensions": rotate["dimensions"],
        "iterate_area": execution["iterate_calls"][0]["area_words"],
        "rowdriver_calls": len(execution["rowdriver_detours"]),
        "schedule_stop": execution["checkpoints"]["schedule_complete"]["stop"],
        "aex_rotate_source_sha256": rotate["source_sha256"],
        "aex_rotate_destination_after_sha256": rotate["destination_after_sha256"],
    }


def render_markdown(payload: dict) -> str:
    zero = payload["cases"]["angle_0"]
    diagonal = payload["cases"]["angle_45"]
    return "\n".join([
        "# OLMDirectionalBlur Angle-0 vs Diagonal Schedule Proof",
        "",
        "## Status",
        "",
        "- `pass`, local actual-AEX schedule differential.",
        "- The fixture intentionally stops at `0x180005554` after rowdriver scheduling; no final image or AE-exact claim is made.",
        "- No production file, existing fixture, ledger, Windows package, or NAS archive was changed.",
        "",
        "## Evidence",
        "",
        f"- AEX: `{payload['provenance']['aex']}`",
        f"- AEX SHA-256: `{payload['provenance']['aex_sha256']}`",
        f"- Source fixture: `{payload['provenance']['source']}`",
        f"- Fixture SHA-256: `{payload['provenance']['fixture_sha256']}`",
        "",
        "| control angle | materialized rotate angle | bits | dimensions | Iterate8 area | rowdriver calls | stop |",
        "| ---: | ---: | --- | --- | --- | ---: | --- |",
        f"| 0 deg | {zero['materialized_angle_radians']:.10f} rad ({zero['materialized_angle_degrees']:.6f} deg) | `{zero['materialized_angle_bits']}` | `{zero['rotate_dimensions']}` | `{zero['iterate_area']}` | {zero['rowdriver_calls']} | `{zero['schedule_stop']}` |",
        f"| 45 deg | {diagonal['materialized_angle_radians']:.10f} rad ({diagonal['materialized_angle_degrees']:.6f} deg) | `{diagonal['materialized_angle_bits']}` | `{diagonal['rotate_dimensions']}` | `{diagonal['iterate_area']}` | {diagonal['rowdriver_calls']} | `{diagonal['schedule_stop']}` |",
        "",
        "## Proof",
        "",
        "- User angle 0 does not bypass rotation or mean a zero-angle rotate call: the actual AEX passes `pi/2` to `FUN_180001ec0`.",
        "- User angle 45 changes the same rotate argument to `3pi/4`; the AEX still uses the same rotate invocation, PF Iterate8 area, and 26 rowdriver chunks.",
        "- Therefore the next semantic split is the rotate angle/value path (`pi/2` axis-aligned versus `3pi/4` diagonal), not host-world rectangle mapping or an angle-0 rotate bypass.",
        "- This does not prove Mac AE host binding, rotated sampler validity, normalization, final writeback, or production integration.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/test_dblur_angle0_diagonal_schedule_20260716.py",
        "```",
        "",
    ])


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_angle_schedule_") as name:
        temp = Path(name)
        source = temp / "source.png"
        Image.open(SOURCE).convert("RGBA").crop((0, 0, 16, 16)).save(source)
        angle_0 = run_case(source, temp / "angle_0.json", 0)
        angle_45 = run_case(source, temp / "angle_45.json", 45)

    zero = compact_case(angle_0)
    diagonal = compact_case(angle_45)
    assert zero["materialized_angle_bits"] == "0x3fc90fdb"
    assert diagonal["materialized_angle_bits"] == "0x4016cbe4"
    assert zero["rotate_dimensions"] == diagonal["rotate_dimensions"] == [26, 26]
    assert zero["iterate_area"] == diagonal["iterate_area"] == [0, 0, 16, 16]
    assert zero["rowdriver_calls"] == diagonal["rowdriver_calls"] == 26
    payload = {
        "kind": "olmdirectionalblur_angle0_diagonal_schedule",
        "schema": 1,
        "date": "2026-07-16",
        "status": "pass",
        "claim_scope": "local actual-AEX schedule evidence; not Mac AE exact",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE.relative_to(ROOT)),
            "fixture_sha256": sha256(FIXTURE),
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(SOURCE),
        },
        "cases": {"angle_0": zero, "angle_45": diagonal},
        "conclusion": "angle 0 materializes pi/2 and follows the same rotate/schedule path as diagonal control; only the rotate angle differs in this bounded proof",
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "report_json": str(REPORT_JSON), "report_md": str(REPORT_MD)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
