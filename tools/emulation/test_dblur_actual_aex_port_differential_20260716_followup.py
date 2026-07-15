#!/usr/bin/env python3
"""Bound the angle-0 actual-AEX versus typed-rowdriver world differential.

This is a host-boundary harness, not a production integration test.  It keeps
the actual AEX path and the typed port on the same padded PF_EffectWorld and
non-full Iterate8 area, then requires the typed rowdriver to own distinct
source/destination and accumulator buffers.  A schedule-only run proves the
exact fail-closed stop when the real production return cannot be carried
through the remaining host boundary.
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
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT_JSON = ROOT / "refs/conformance/olmdirectionalblur_actual_aex_port_differential_20260716_followup.json"
REPORT_MD = ROOT / "refs/conformance/olmdirectionalblur_actual_aex_port_differential_20260716_followup.md"

AREA = [2, 1, 14, 15]
ROW_PADDING = 12
STOP = "0x180005554"
ROWDRIVER_RETURN = "0x18000553b"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fixture(temp: Path, source: Path, name: str, *, rowdriver: bool,
                schedule_only: bool = False) -> dict:
    report = temp / f"{name}.json"
    command = [
        sys.executable, str(FIXTURE), "--source", str(source), "--output", str(report),
        "--angle", "0", "--downsample-num", "1", "--downsample-den", "2",
        "--front-strength", "48", "--size-variation", "0", "--front-sharp-tail", "0",
        "--back-strength", "0", "--back-alpha-fade", "0", "--noise-variation", "0",
        "--world-area", *map(str, AREA), "--row-padding", str(ROW_PADDING),
        "--detour-rotate", "--max-instructions", "200000000",
    ]
    command.append("--detour-rowdriver" if rowdriver else "--no-detour-rowdriver")
    if schedule_only:
        command.append("--schedule-only-rowdriver")
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(report.read_text(encoding="utf-8"))


def assert_world_contract(report: dict) -> dict:
    execution = report["execution"]
    calls = execution["iterate_calls"]
    assert len(calls) == 2
    assert [call["area_words"] for call in calls] == [AREA, AREA]
    assert all(call["callback_error"] == 0 for call in calls)
    assert all(call["source_world"] != "0x0" and call["dst_world"] != "0x0" for call in calls)
    assert report["world_layout"]["input_extent_hint"] == [0, 0, 16, 16]
    assert report["world_layout"]["output_extent_hint"] == [0, 0, 16, 16]
    return {
        "iterate_calls": len(calls),
        "areas": [call["area_words"] for call in calls],
        "source_worlds": sorted({call["source_world"] for call in calls}),
        "destination_worlds": sorted({call["dst_world"] for call in calls}),
        "rowbytes": ROW_PADDING + 16 * 4,
    }


def assert_typed_ownership(report: dict) -> dict:
    state = report["execution"]["rowdriver_state"]
    assert state["mode"] in (0, 1)
    source = int(state["source"], 16)
    destination = int(state["destination"], 16)
    denominator = int(state["denominator"], 16)
    alpha = int(state["alpha"], 16)
    comp_map = int(state["comp_map"], 16)
    assert source != destination
    assert len({source, destination, denominator, alpha, comp_map}) == 5
    assert state["complete"] is True
    calls = report["execution"]["rowdriver_detours"]
    assert calls
    assert calls[-1]["rows"][1] == state["dimensions"][1]
    return {
        "mode": state["mode"],
        "dimensions": state["dimensions"],
        "typed_buffers": {
            "source": hex(source), "destination": hex(destination),
            "denominator": hex(denominator), "alpha_max": hex(alpha),
            "comp_map": hex(comp_map),
        },
        "rowdriver_calls": len(calls),
        "last_rows": calls[-1]["rows"],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_aex_port_followup_") as name:
        temp = Path(name)
        source = temp / "source.png"
        Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
        actual = run_fixture(temp, source, "actual", rowdriver=False)
        port = run_fixture(temp, source, "port", rowdriver=True)
        stopped = run_fixture(temp, source, "schedule", rowdriver=True, schedule_only=True)

    assert actual["status"] == port["status"] == "ok"
    assert actual["output"]["complete"] is True
    assert port["output"]["complete"] is True
    assert actual["output"]["sha256"] == port["output"]["sha256"]
    world = assert_world_contract(port)
    typed = assert_typed_ownership(port)

    stopped_execution = stopped["execution"]
    assert stopped["status"] == "blocked"
    assert stopped["output"]["complete"] is False
    assert stopped["blocked"]["reason"] == "pre-render-return"
    assert stopped_execution["checkpoints"]["schedule_complete"]["stop"] == STOP
    assert stopped_execution["rowdriver_detours"]
    assert all(call["return_address"] == ROWDRIVER_RETURN for call in stopped_execution["rowdriver_detours"])
    assert stopped_execution["iterate_calls"][0]["area_words"] == AREA

    payload = {
        "kind": "olmdirectionalblur_actual_aex_port_differential_followup",
        "schema": 1,
        "date": "2026-07-16",
        "status": "pass",
        "claim_scope": "angle-0 local actual-AEX versus typed-port host-boundary differential; not AE exact",
        "provenance": {
            "aex": str((ROOT / "plugins_2025/OLMDirectionalBlur.aex").relative_to(ROOT)),
            "aex_sha256": sha256(ROOT / "plugins_2025/OLMDirectionalBlur.aex"),
            "fixture": str(FIXTURE.relative_to(ROOT)),
            "fixture_sha256": sha256(FIXTURE),
            "source": str(SOURCE.relative_to(ROOT)),
        },
        "contract": {"angle_degrees": 0, "world_area": AREA, "rowbytes": world["rowbytes"], "row_padding": ROW_PADDING},
        "differential": {
            "actual_status": actual["status"], "port_status": port["status"],
            "actual_output_sha256": actual["output"]["sha256"],
            "port_output_sha256": port["output"]["sha256"],
            "equal_output": actual["output"]["sha256"] == port["output"]["sha256"],
            "world": world,
            "typed_ownership": typed,
        },
        "fail_closed": {
            "status": stopped["status"], "reason": stopped["blocked"]["reason"],
            "exact_stop": STOP, "observed_stop": stopped_execution["checkpoints"]["schedule_complete"]["stop"],
            "rowdriver_return": ROWDRIVER_RETURN,
            "rowdriver_calls": len(stopped_execution["rowdriver_detours"]),
            "production_integration_claimed": False,
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text("\n".join([
        "# OLMDirectionalBlur Actual-AEX vs Typed-Port Differential Follow-Up",
        "",
        "- Status: `pass`.",
        "- Scope: angle 0, padded PF_EffectWorld (`rowbytes=76`), non-full area `[2, 1, 14, 15]`.",
        f"- Actual AEX and typed port output SHA-256: `{actual['output']['sha256']}`.",
        f"- Typed ownership: `{typed['typed_buffers']}`; source and destination are distinct.",
        f"- Fail-closed schedule proof: stopped at `{STOP}`; rowdriver returns to `{ROWDRIVER_RETURN}` after `{len(stopped_execution['rowdriver_detours'])}` typed calls.",
        "- Production integration was not callable in this environment; no AE-exact claim is made.",
        "",
        "Reproduction: `python3 tools/emulation/test_dblur_actual_aex_port_differential_20260716_followup.py`",
        "",
    ]), encoding="utf-8")
    print(json.dumps({"status": "pass", "report_json": str(REPORT_JSON), "report_md": str(REPORT_MD)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
