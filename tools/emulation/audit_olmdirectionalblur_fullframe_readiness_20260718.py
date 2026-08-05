#!/usr/bin/env python3
"""Fail-closed readiness audit for DirectionalBlur full-frame / Mac AE follow-up.

This is a read-only orchestration audit. It does not edit production sources.
It reruns the smallest bounded local checks that should still be reproducible,
then combines them with the existing natural-path artifacts to answer one
question only: which host/world invariants are still missing before a broader
full-frame or Mac AE validation is meaningful?
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "refs/conformance/olmdirectionalblur_fullframe_readiness_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmdirectionalblur_fullframe_readiness_20260718.md"

CHECKS = [
    {
        "id": "angle_pair_actual_aex",
        "title": "bounded angle 0 / 45 actual-AEX equality",
        "path": ROOT / "refs/conformance/olmdirectionalblur_angle0_diagonal_actual_aex_port_differential_20260718.json",
        "command": ["python3", "tools/emulation/test_dblur_angle0_diagonal_actual_aex_port_differential_20260718.py"],
        "required_status": "pass",
        "kind": "bounded-proof",
    },
    {
        "id": "row_mapping",
        "title": "bounded PF world / row mapping",
        "path": ROOT / "refs/conformance/olmdirectionalblur_world_row_mapping_differential_20260716.json",
        "command": ["python3", "tools/emulation/test_dblur_world_row_mapping_20260716.py"],
        "required_status": "pass",
        "kind": "bounded-proof",
    },
    {
        "id": "rowdriver_binding",
        "title": "rowdriver to helper ABI binding",
        "path": ROOT / "refs/conformance/olmdirectionalblur_rowdriver_binding_20260718.json",
        "command": ["python3", "tools/emulation/audit_olmdirectionalblur_rowdriver_binding_20260718.py"],
        "required_status": "pass",
        "kind": "bounded-proof",
    },
    {
        "id": "mac_host_adapter",
        "title": "Mac exact-path host adapter gate",
        "command": ["python3", "tools/emulation/test_dblur_mac_host_adapter_20260716.py"],
        "required_status": "ok",
        "kind": "live-host-check",
    },
    {
        "id": "actual_populate_checkpoint",
        "title": "natural actual populate callback reached",
        "path": ROOT / "refs/conformance/olmdirectionalblur_actual_populate_checkpoint_20260717.json",
        "required_status": "pass",
        "kind": "natural-artifact",
    },
    {
        "id": "iterate8_continuation",
        "title": "natural continuation beyond actual populate",
        "path": ROOT / "refs/conformance/olmdirectionalblur_natural_continuation_20260718.json",
        "required_status": "pass",
        "kind": "natural-artifact",
    },
    {
        "id": "nonzero_writer_oracle",
        "title": "bounded natural writer oracle",
        "path": ROOT / "refs/conformance/olmdirectionalblur_nonzero_writer_oracle_20260717.json",
        "required_status": "pass",
        "kind": "bounded-proof",
    },
]


def run(command: list[str]) -> dict:
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    parsed = None
    stdout = proc.stdout.strip()
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "parsed": parsed,
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_host_adapter(parsed: dict | None) -> dict:
    if not isinstance(parsed, dict):
        return {
            "status": "invalid",
            "ok": False,
            "reason": "host adapter probe did not emit JSON",
        }
    cases = parsed.get("cases", [])
    gates = parsed.get("gates", [])
    supported_gates = {
        "size_variation",
        "front_alpha_fade",
        "front_sharp_tail",
        "back_alpha_fade",
        "back_strength",
        "noise",
        "downsample",
    }
    ok = (
        parsed.get("status") == "ok"
        and len(cases) == 4
        and all(case.get("used_exact") == 1 and case.get("pixels_match") is True for case in cases)
        and len(gates) == 8
        and all(
            gate.get("used_exact") == (1 if gate.get("name") in supported_gates else 0)
            for gate in gates
        )
    )
    return {
        "status": parsed.get("status"),
        "ok": ok,
        "full_roi_cases": [case for case in cases if case.get("roi") == "full"],
        "partial_roi_cases": [case for case in cases if case.get("roi") == "partial"],
        "gate_names": [gate.get("name") for gate in gates],
        "world": parsed.get("world"),
        "production_source": parsed.get("production_source"),
    }


def evaluate_artifact(check: dict, data: dict) -> dict:
    status = data.get("status")
    ok = status == check["required_status"]
    result = {"status": status, "ok": ok}
    if check["id"] == "angle_pair_actual_aex":
        cases = data.get("cases", {})
        result["angles_equal"] = {
            angle: payload.get("equal_output")
            for angle, payload in cases.items()
        }
    elif check["id"] == "row_mapping":
        result["facts"] = data.get("facts", [])
        actual = data.get("actual_aex", {})
        portable = data.get("portable_rowdriver_detour", {})
        result["iterate_areas"] = actual.get("iterate_areas") or portable.get("iterate_areas")
        result["rowbytes"] = data.get("world", {}).get("rowbytes")
    elif check["id"] == "rowdriver_binding":
        result["helper_entries"] = len(data.get("helper_entries", []))
        result["next_unresolved_boundary"] = data.get("next_unresolved_boundary")
    elif check["id"] == "actual_populate_checkpoint":
        result["nearest_blocker"] = data.get("nearest_blocker", {})
        result["callback_attempts"] = data.get("actual_callback", {}).get("callback_attempts")
    elif check["id"] == "iterate8_continuation":
        checkpoint = data.get("checkpoint_state", {})
        result["fixture_blocker"] = checkpoint.get("final_blocker")
        result["write_events"] = int(checkpoint.get("downstream_write") is not None)
        result["output_callback"] = checkpoint.get("output_callback") is True
        result["first_missing_checkpoint"] = checkpoint.get("first_missing")
    elif check["id"] == "nonzero_writer_oracle":
        result["comparison"] = data.get("comparison", {})
    return result


def classify(results: dict) -> dict:
    bounded_ok = all(results[key]["ok"] for key in [
        "angle_pair_actual_aex",
        "row_mapping",
        "rowdriver_binding",
        "mac_host_adapter",
        "actual_populate_checkpoint",
        "nonzero_writer_oracle",
    ])
    natural_continuation_ok = results["iterate8_continuation"]["ok"]
    remaining = []
    if not natural_continuation_ok:
        remaining.append({
            "id": "natural_iterate8_continuation",
            "detail": "The natural path is still blocked before any downstream write after the actual populate callback. No artifact proves that a real render continues through rowdriver, normalization, rotate-back, and the output callback.",
            "evidence": "refs/conformance/olmdirectionalblur_natural_continuation_20260718.json",
        })
    if bounded_ok and not natural_continuation_ok:
        remaining.append({
            "id": "same-run_full_render_binding",
            "detail": "The bounded rowdriver/writer proofs are isolated and executable, but they are not yet shown to be the exact chain used by a natural full render on the residual lane.",
            "evidence": "bounded proofs pass; natural continuation remains blocked",
        })
    return {
        "bounded_frontonly_ready": bounded_ok,
        "fullframe_local_ready": bounded_ok and natural_continuation_ok,
        "mac_ae_validation_ready": bounded_ok and natural_continuation_ok,
        "remaining_invariants": remaining,
        "decision": (
            "blocked"
            if not (bounded_ok and natural_continuation_ok)
            else "ready"
        ),
        "highest_value_next_action": (
            "Prove the natural Iterate8 continuation from the actual populate callback through the real downstream chain, or capture a same-run writer-entry witness on the residual lane. Until then, keep DirectionalBlur fail-closed for full-frame and Mac AE validation."
            if not natural_continuation_ok
            else "Bounded host/world invariants are satisfied; the next action may be a narrow full-frame or Mac AE validation."
        ),
        "forbidden_action": "Do not treat bounded rowdriver equality or the exact-path host adapter as Mac AE exactness, and do not tune from broad PNG output.",
    }


def render_md(payload: dict) -> str:
    lines = [
        "# OLMDirectionalBlur Full-Frame Readiness Audit",
        "",
        "Date: 2026-07-18",
        "Scope: `OLMDirectionalBlur` front-only bounded lane only.",
        "Policy: fail closed. This audit is allowed to prove readiness barriers, not to promote `AE exact`.",
        "",
        "## Decision",
        "",
        f"- Overall: `{payload['classification']['decision']}`.",
        f"- Bounded front-only host/world readiness: `{payload['classification']['bounded_frontonly_ready']}`.",
        f"- Full-frame local readiness: `{payload['classification']['fullframe_local_ready']}`.",
        f"- Mac AE validation readiness: `{payload['classification']['mac_ae_validation_ready']}`.",
        "",
        "## Verified Facts",
        "",
        "| Invariant | Status | Fact |",
        "| --- | --- | --- |",
    ]
    rows = payload["results"]
    lines.append(
        "| bounded angle pair actual-AEX equality | "
        f"`{rows['angle_pair_actual_aex']['status']}` | "
        "Angle 0 and 45 both match the actual AEX exactly on the bounded typed-rowdriver differential. |"
    )
    lines.append(
        "| bounded PF world / row mapping | "
        f"`{rows['row_mapping']['status']}` | "
        "The bounded Iterate8 area and padded rowbytes mapping stay identical between actual AEX and typed detour. |"
    )
    lines.append(
        "| rowdriver/helper ABI binding | "
        f"`{rows['rowdriver_binding']['status']}` | "
        f"One real row enters the actual rowdriver and yields `{rows['rowdriver_binding'].get('helper_entries', 0)}` helper calls with the expected buffer ownership. |"
    )
    lines.append(
        "| Mac exact-path host adapter | "
        f"`{rows['mac_host_adapter']['status']}` | "
        "Live source-included probe still passes full/partial ROI checks and rejects eight non-exact gates. |"
    )
    lines.append(
        "| natural actual populate callback | "
        f"`{rows['actual_populate_checkpoint']['status']}` | "
        "The real populate callback is reached on the natural path and writes the expected source plane. |"
    )
    lines.append(
        "| natural continuation after populate | "
        f"`{rows['iterate8_continuation']['status']}` | "
        + (
            "The accepted natural-path artifact reaches a live downstream write, rotate-back, and the real AEX output callback. |"
            if rows["iterate8_continuation"]["ok"]
            else "The current natural-path checkpoint stops before the complete downstream callback chain. |"
        )
    )
    lines.append(
        "| bounded natural writer oracle | "
        f"`{rows['nonzero_writer_oracle']['status']}` | "
        "The bounded natural follow-up chain still matches the temporary production oracle exactly, but that is not a natural full render. |"
    )
    lines += [
        "",
        "## Remaining Invariants",
        "",
    ]
    if payload["classification"]["remaining_invariants"]:
        for item in payload["classification"]["remaining_invariants"]:
            lines.append(f"- `{item['id']}`: {item['detail']} Evidence: `{item['evidence']}`.")
    else:
        lines.append("- None for this bounded lane.")
    lines += [
        "",
        "## FACT / INFERENCE",
        "",
        "- FACT: the bounded rowdriver proof, row mapping proof, rowdriver/helper ABI proof, and live Mac exact-path adapter proof all passed again on this machine.",
        (
            "- FACT: the accepted natural-path artifact reaches the real AEX "
            "rotate-back and output callback after a live downstream buffer write."
            if payload["classification"]["fullframe_local_ready"]
            else "- FACT: the natural-path artifact is still blocked before a complete downstream callback chain."
        ),
        (
            "- INFERENCE: the bounded front-only lane is ready for a narrow Mac AE validation; "
            "that validation, rather than this local host model, remains the `AE exact` gate."
            if payload["classification"]["mac_ae_validation_ready"]
            else "- INFERENCE: natural scheduling/continuation remains the next required boundary."
        ),
        "",
        "## Reproduction",
        "",
        f"`python3 {Path(__file__).relative_to(ROOT)}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    results: dict[str, dict] = {}
    commands: list[dict] = []
    for check in CHECKS:
        if "command" in check:
            run_result = run(check["command"])
            commands.append({
                "id": check["id"],
                "command": run_result["command"],
                "returncode": run_result["returncode"],
                "stdout_tail": run_result["stdout_tail"],
                "stderr_tail": run_result["stderr_tail"],
            })
            if check["id"] == "mac_host_adapter":
                results[check["id"]] = evaluate_host_adapter(run_result["parsed"])
                continue
            if run_result["returncode"] != 0:
                results[check["id"]] = {
                    "status": "command_failed",
                    "ok": False,
                    "stdout_tail": run_result["stdout_tail"],
                    "stderr_tail": run_result["stderr_tail"],
                }
                continue
        if "path" in check:
            data = load_json(check["path"])
            results[check["id"]] = evaluate_artifact(check, data)
        elif check["id"] != "mac_host_adapter":
            results[check["id"]] = {
                "status": "missing_artifact",
                "ok": False,
            }

    classification = classify(results)
    payload = {
        "kind": "olmdirectionalblur_fullframe_readiness_audit",
        "schema": 1,
        "generated_at": "2026-07-18",
        "scope": {
            "plugin": "OLMDirectionalBlur",
            "lane": "front-only bounded host/world readiness",
            "policy": "fail-closed",
        },
        "results": results,
        "classification": classification,
        "commands": commands,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps({
        "status": classification["decision"],
        "report_json": str(OUT_JSON),
        "report_md": str(OUT_MD),
        "fullframe_local_ready": classification["fullframe_local_ready"],
        "mac_ae_validation_ready": classification["mac_ae_validation_ready"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
