#!/usr/bin/env python3
"""Bounded diagonal actual-AEX versus typed rowdriver differential.

This owns only the experiment wrapper.  The host fixture and both compiled
detours remain shared evidence; any missing contract fact fails closed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0005_before_effects.png"
REPORT_JSON = ROOT / "refs/conformance/olmdirectionalblur_diagonal_actual_aex_port_differential_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmdirectionalblur_diagonal_actual_aex_port_differential_20260716.md"

AREA = [2, 1, 14, 15]
ROWBYTES = 76
ROWDRIVER = "0x1800038d0"
ROTATE = "0x180001ec0"
ROWDRIVER_RETURN = "0x18000553b"
NORMALIZATION = "0x180005554"
AEX_SHA256 = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fixture(temp: Path, source: Path, name: str, *, typed: bool,
                schedule_only: bool = False) -> dict:
    report = temp / f"{name}.json"
    command = [
        sys.executable, str(FIXTURE), "--source", str(source), "--output", str(report),
        "--angle", "45", "--downsample-num", "1", "--downsample-den", "2",
        "--front-strength", "48", "--size-variation", "0", "--front-sharp-tail", "0",
        "--back-strength", "0", "--back-alpha-fade", "0", "--back-sharp-tail", "0",
        "--noise-variation", "0", "--world-area", *map(str, AREA),
        "--row-padding", "12", "--detour-rotate", "--max-instructions", "200000000",
        "--detour-rowdriver" if typed else "--no-detour-rowdriver",
    ]
    if schedule_only:
        command.append("--schedule-only-rowdriver")
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if not report.exists():
        raise RuntimeError(f"fixture produced no report ({completed.returncode}): {completed.stderr[-500:]}")
    result = json.loads(report.read_text(encoding="utf-8"))
    result.setdefault("_process", {"returncode": completed.returncode, "stderr": completed.stderr[-500:]})
    return result


def require_contract(report: dict, *, typed: bool) -> dict:
    if report.get("status") != "ok" or not report.get("output", {}).get("complete"):
        raise AssertionError(f"incomplete {('typed' if typed else 'actual')} output")
    execution = report["execution"]
    calls = execution["iterate_calls"]
    if len(calls) != 2 or [call["area_words"] for call in calls] != [AREA, AREA]:
        raise AssertionError("expected both contiguous Iterate8 callbacks on the requested area")
    if any(call.get("callback_error") != 0 for call in calls):
        raise AssertionError("Iterate8 callback error")
    if report["world_layout"].get("input_extent_hint") != [0, 0, 16, 16]:
        raise AssertionError("unexpected input extent")
    if report["world_layout"].get("output_extent_hint") != [0, 0, 16, 16]:
        raise AssertionError("unexpected output extent")
    if report["world_layout"].get("downsample_num") != 1 or report["world_layout"].get("downsample_den") != 2:
        raise AssertionError("unexpected downsample")
    rotates = execution["rotate_detours"]
    if len(rotates) != 2:
        raise AssertionError("expected forward and rotate-back detours")
    if any(rotate.get("dimensions") != [26, 26] for rotate in rotates):
        raise AssertionError("unexpected diagonal rotate dimensions")
    if [rotate.get("angle_bits") for rotate in rotates] != ["0x4016cbe4", "0xc016cbe4"]:
        raise AssertionError("unexpected diagonal rotate angles")
    if "final_host_output" not in execution.get("checkpoints", {}):
        raise AssertionError("final output callback was not observed")
    if execution.get("render_return") != 1:
        raise AssertionError("final rotate return was not observed")
    if execution.get("checkpoints", {}).get("normalization") != {"after_rotateback": True}:
        raise AssertionError("normalization checkpoint was not observed")
    if typed:
        state = execution["rowdriver_state"]
        fields = ("source", "destination", "denominator", "alpha", "comp_map")
        addresses = [int(state[field], 16) for field in fields]
        if len(set(addresses)) != 5:
            raise AssertionError("typed source/destination/denominator/alpha/comp buffers alias")
        if state.get("complete") is not True or state.get("dimensions") != [26, 26]:
            raise AssertionError("typed rowdriver state is incomplete")
        detours = execution["rowdriver_detours"]
        if not detours or detours[-1]["rows"][1] != state["dimensions"][1]:
            raise AssertionError("rowdriver schedule does not end at work height")
        typed_state = {"mode": state["mode"], "dimensions": state["dimensions"],
                       "buffers": dict(zip(fields, [hex(value) for value in addresses])),
                       "rowdriver_calls": len(detours), "last_rows": detours[-1]["rows"]}
    else:
        typed_state = None
    return {"output_sha256": report["output"]["sha256"],
            "iterate_calls": len(calls), "rotate_calls": len(rotates),
            "rotate_dimensions": [rotate["dimensions"] for rotate in rotates],
            "rotate_angle_bits": [rotate["angle_bits"] for rotate in rotates],
            "normalization": execution.get("checkpoints", {}).get("normalization"),
            "typed_state": typed_state}


def main() -> int:
    payload = {"kind": "olmdirectionalblur_diagonal_actual_aex_port_differential",
               "schema": 1, "date": "2026-07-16", "status": "blocked",
               "claim_scope": "bounded diagonal actual-AEX versus typed-rowdriver differential; not AE exact",
               "contract": {"case_id": "case_0005", "primary_witness": [507, 367],
                            "crop": [499, 359, 515, 375], "angle_degrees": 45,
                            "world_dimensions": [16, 16], "world_rowbytes": ROWBYTES,
                            "world_area": AREA, "downsample": [1, 2], "front_strength": 48,
                            "zero_variations_fades_tails_back_noise": True,
                            "aex_rowdriver": ROWDRIVER, "rotate": ROTATE,
                            "rowdriver_return": ROWDRIVER_RETURN, "normalization": NORMALIZATION},
               "provenance": {"aex": str(AEX.relative_to(ROOT)), "aex_sha256": None,
                              "fixture": str(FIXTURE.relative_to(ROOT)), "source": str(SOURCE.relative_to(ROOT))},
               "differential": {}, "fail_closed": {"production_integration_claimed": False}}
    try:
        actual_sha = sha256(AEX)
        payload["provenance"]["aex_sha256"] = actual_sha
        if actual_sha != AEX_SHA256:
            raise AssertionError(f"AEX SHA mismatch: {actual_sha}")
        with tempfile.TemporaryDirectory(prefix="olm_dblur_diagonal_aex_port_") as name:
            temp = Path(name)
            cropped = temp / "case_0005_primary_witness.png"
            Image.open(SOURCE).convert("RGBA").crop((499, 359, 515, 375)).save(cropped)
            actual = run_fixture(temp, cropped, "actual", typed=False)
            typed = run_fixture(temp, cropped, "typed", typed=True)
            schedule = run_fixture(temp, cropped, "schedule", typed=True, schedule_only=True)
        payload["differential"] = {
            "actual_status": actual.get("status"),
            "typed_status": typed.get("status"),
            "actual_output_sha256": actual.get("output", {}).get("sha256"),
            "typed_output_sha256": typed.get("output", {}).get("sha256"),
            "available_typed_state": typed.get("execution", {}).get("rowdriver_state"),
        }
        actual_contract = require_contract(actual, typed=False)
        typed_contract = require_contract(typed, typed=True)
        if actual_contract["rotate_angle_bits"] != typed_contract["rotate_angle_bits"] or actual_contract["rotate_dimensions"] != typed_contract["rotate_dimensions"]:
            raise AssertionError("actual and typed rotate calls differ")
        if actual_contract["output_sha256"] != typed_contract["output_sha256"]:
            raise AssertionError("actual and typed output hashes differ")
        schedule_execution = schedule["execution"]
        schedule_detours = schedule_execution["rowdriver_detours"]
        if schedule.get("status") != "blocked" or schedule.get("blocked", {}).get("reason") != "pre-render-return":
            raise AssertionError("schedule probe did not fail closed before render return")
        if schedule_execution.get("checkpoints", {}).get("schedule_complete", {}).get("stop") != NORMALIZATION:
            raise AssertionError("schedule probe did not stop at normalization")
        if not schedule_detours or any(call.get("return_address") != ROWDRIVER_RETURN for call in schedule_detours):
            raise AssertionError("schedule probe rowdriver return mismatch")
        if schedule_detours[-1]["rows"][1] != 26:
            raise AssertionError("schedule probe does not end at work height")
        payload["differential"].update({"actual": actual_contract, "typed": typed_contract,
                                         "equal_output": True,
                                         "schedule_probe": {"status": schedule["status"],
                                             "rowdriver_calls": len(schedule_detours),
                                             "return_address": ROWDRIVER_RETURN,
                                             "normalization_stop": NORMALIZATION,
                                             "last_rows": schedule_detours[-1]["rows"]}})
        payload["status"] = "pass"
    except Exception as exc:
        payload["fail_closed"].update({"reason": type(exc).__name__, "message": str(exc)})
        payload["status"] = "blocked"
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    status_line = "pass" if payload["status"] == "pass" else "blocked"
    REPORT_MD.write_text("\n".join([
        "# OLMDirectionalBlur Diagonal Actual-AEX vs Typed-Rowdriver Differential", "",
        f"- Status: `{status_line}`.",
        "- Scope: case_0005 crop around primary witness `(507,367)`, angle `45`, 16x16 world, rowbytes `76`, area `[2,1,14,15]`.",
        "- The actual run leaves AEX rowdriver `0x1800038d0` in place; the typed run detours only that rowdriver. Both runs use the byte-exact rotate detour.",
        f"- Actual output SHA-256: `{payload['differential'].get('actual_output_sha256')}`; typed output SHA-256: `{payload['differential'].get('typed_output_sha256')}`; equal: `{payload['differential'].get('equal_output')}`.",
        f"- Typed state: `{payload['differential'].get('typed', {}).get('typed_state')}`.",
        f"- Schedule probe: `{payload['differential'].get('schedule_probe')}`.",
        "- No AE-exact claim is made; production integration is explicitly unclaimed.",
        "", f"Reproduction: `python3 {Path(__file__).relative_to(ROOT)}`", "",
    ]), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "report_json": str(REPORT_JSON), "report_md": str(REPORT_MD)}))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
