#!/usr/bin/env python3
"""Compare actual AEX and typed rowdriver runs for angle 0 and 45 degrees.

The experiment is deliberately bounded.  It uses the checked-in Windows AEX
under Unicorn, keeps the AEX rotate path behind the existing byte-exact
rotate detour, and swaps only FUN_1800038d0 in the typed run.  It is evidence
for the rowdriver port at both geometry controls, not AE-host evidence.
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
REPORT_JSON = ROOT / "refs/conformance/olmdirectionalblur_angle0_diagonal_actual_aex_port_differential_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmdirectionalblur_angle0_diagonal_actual_aex_port_differential_20260718.md"
AREA = [2, 1, 14, 15]
EXPECTED_ROTATE_BITS = {0: ["0x3fc90fdb", "0xbfc90fdb"],
                        45: ["0x4016cbe4", "0xc016cbe4"]}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fixture(temp: Path, source: Path, angle: int, typed: bool) -> dict:
    output = temp / f"{'typed' if typed else 'actual'}_{angle}.json"
    command = [
        sys.executable, str(FIXTURE), "--source", str(source), "--output", str(output),
        "--angle", str(angle), "--downsample-num", "1", "--downsample-den", "2",
        "--front-strength", "48", "--size-variation", "0", "--front-sharp-tail", "0",
        "--back-strength", "0", "--back-alpha-fade", "0", "--back-sharp-tail", "0",
        "--noise-variation", "0", "--world-area", *map(str, AREA), "--row-padding", "12",
        "--detour-rotate", "--max-instructions", """200000000""",
        "--detour-rowdriver" if typed else "--no-detour-rowdriver",
    ]
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if not output.exists():
        raise RuntimeError(f"fixture produced no report for angle {angle}: {process.stderr[-800:]}")
    report = json.loads(output.read_text(encoding="utf-8"))
    report["process"] = {"returncode": process.returncode, "stderr_tail": process.stderr[-800:]}
    return report


def summarize(report: dict, angle: int, typed: bool) -> dict:
    if report.get("status") != "ok" or not report.get("output", {}).get("complete"):
        raise AssertionError(f"incomplete {'typed' if typed else 'actual'} run at angle {angle}")
    execution = report["execution"]
    rotates = execution["rotate_detours"]
    if len(rotates) != 2:
        raise AssertionError(f"angle {angle}: expected forward and rotate-back calls")
    bits = [item["angle_bits"] for item in rotates]
    if bits != EXPECTED_ROTATE_BITS[angle]:
        raise AssertionError(f"angle {angle}: unexpected rotate bits {bits}")
    if any(item["dimensions"] != [26, 26] for item in rotates):
        raise AssertionError(f"angle {angle}: unexpected rotate dimensions")
    if [item["area_words"] for item in execution["iterate_calls"]] != [AREA, AREA]:
        raise AssertionError(f"angle {angle}: unexpected Iterate8 area")
    if execution.get("checkpoints", {}).get("normalization") != {"after_rotateback": True}:
        raise AssertionError(f"angle {angle}: normalization checkpoint missing")
    if typed:
        state = execution.get("rowdriver_state", {})
        if state.get("complete") is not True or state.get("dimensions") != [26, 26]:
            raise AssertionError(f"angle {angle}: typed rowdriver state incomplete")
    return {
        "angle_degrees": angle,
        "output_sha256": report["output"]["sha256"],
        "rotate_angle_bits": bits,
        "rotate_dimensions": [item["dimensions"] for item in rotates],
        "iterate_areas": [item["area_words"] for item in execution["iterate_calls"]],
        "rowdriver_calls": len(execution.get("rowdriver_detours", [])),
        "normalization": execution["checkpoints"]["normalization"],
        "typed_rowdriver_complete": bool(typed),
    }


def render(payload: dict) -> str:
    lines = [
        "# OLMDirectionalBlur Angle 0 / Diagonal Actual-AEX Port Differential",
        "",
        f"- Status: `{payload['status']}`.",
        "- Scope: bounded 16x16 world from case_0005, area `[2,1,14,15]`, downsample `1/2`.",
        "- The checked-in Windows AEX runs under Unicorn. The rotate primitive uses the existing byte-exact detour; only the rowdriver is replaced in the typed run.",
        "- This is binary-grounded rowdriver evidence, not Mac AE exactness.",
        "",
        "| angle | actual-AEX output | typed output | equal | rotate bits | rowdriver calls |",
        "| ---: | --- | --- | :---: | --- | ---: |",
    ]
    for angle in (0, 45):
        item = payload["cases"][str(angle)]
        lines.append(f"| {angle} | `{item['actual']['output_sha256']}` | `{item['typed']['output_sha256']}` | `{item['equal_output']}` | `{item['actual']['rotate_angle_bits']}` | {item['typed']['rowdriver_calls']} |")
    lines += [
        "",
        "## FACT / INFERENCE",
        "",
        "- FACT: both control angles reached two real AEX rotate calls, two Iterate8 callbacks, normalization, and the complete output callback.",
        "- FACT: for both angle 0 and 45 degrees, actual-AEX and typed-rowdriver output hashes are identical.",
        "- FACT: user angle 0 materializes `pi/2`; user angle 45 materializes `3pi/4`.",
        "- INFERENCE: the bounded typed rowdriver is compatible with the AEX at both geometry controls for this host fixture.",
        "- LIMIT: this does not prove Mac AE parameter/host binding, full-frame output, modes 2/3, or Windows-vs-Mac AE exactness.",
        "",
        f"Reproduction: `python3 {Path(__file__).relative_to(ROOT)}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    payload = {
        "kind": "olmdirectionalblur_angle0_diagonal_actual_aex_port_differential",
        "schema": 1, "status": "blocked", "claim_scope": "bounded actual-AEX rowdriver proof; not AE exact",
        "provenance": {"aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
                       "fixture": str(FIXTURE.relative_to(ROOT)), "source": str(SOURCE.relative_to(ROOT)),
                       "source_sha256": sha256(SOURCE)},
        "contract": {"case_id": "case_0005", "world": [16, 16], "area": AREA,
                     "downsample": [1, 2], "rowdriver": "0x1800038d0",
                     "rotate": "0x180001ec0"}, "cases": {},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="olm_dblur_angle_pair_") as name:
            temp = Path(name)
            cropped = temp / "case_0005_16x16.png"
            Image.open(SOURCE).convert("RGBA").crop((499, 359, 515, 375)).save(cropped)
            for angle in (0, 45):
                actual_report = run_fixture(temp, cropped, angle, False)
                typed_report = run_fixture(temp, cropped, angle, True)
                actual = summarize(actual_report, angle, False)
                typed = summarize(typed_report, angle, True)
                payload["cases"][str(angle)] = {"actual": actual, "typed": typed,
                                                "equal_output": actual["output_sha256"] == typed["output_sha256"]}
                if not payload["cases"][str(angle)]["equal_output"]:
                    raise AssertionError(f"angle {angle}: actual and typed output differ")
        payload["status"] = "pass"
    except Exception as exc:
        payload["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "report_json": str(REPORT_JSON), "report_md": str(REPORT_MD)}))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
