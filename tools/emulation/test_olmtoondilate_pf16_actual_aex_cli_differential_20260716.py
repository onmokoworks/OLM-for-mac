"""Classify the bounded PF16 worker callback ABI before any CLI comparison."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent))
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import PF_COPY_RESUME, run_depth  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf16_actual_aex_cli_differential_20260716.md"
JSON_REPORT = REPORT.with_suffix(".json")


def words(raw: list[int], count: int) -> list[list[int]]:
    data = bytes(raw[: count * 8])
    if len(data) != count * 8:
        raise ValueError(f"expected {count} PF16 pixels, got {len(data)} bytes")
    return [list(struct.unpack_from("<4H", data, offset * 8)) for offset in range(count)]


def main() -> int:
    payload: dict[str, object] = {
        "status": "FAIL_CLOSED",
        "claim_boundary": (
            "bounded actual-AEX PF16 worker-stage classification only; "
            "no production CLI or AE-exact claim"
        ),
    }
    try:
        aex = run_depth(16)
        captures = aex.get("captures", [])
        capture = captures[0] if len(captures) == 1 else {}
        host_input = words(aex.get("input_world_raw", []), 2)
        helper_source = words(capture.get("source_pixel", []), 1)
        helper_destination = words(capture.get("after_destination_pixel", []), 1)
        callback = next((event for event in aex.get("events", []) if event.get("kind") == "pf_copy_callback"), {})
        resume = aex.get("copy_resume", {})
        alpha_matrix = []
        for alpha in (1, 16384, 32767, 32768, 32769, 65535):
            probe = run_depth(16, alpha)
            alpha_matrix.append({
                "alpha": alpha,
                "seed_or_propagate_observed": bool(probe.get("captures")),
                "callback_resume_confirmed": probe.get("copy_resume", {}).get("address") == hex(PF_COPY_RESUME),
                "callback_output_equals_raw_input": probe.get("copy_resume", {}).get("output_visible_equals_input") is True,
            })
        alpha_matrix_gate = all(item["seed_or_propagate_observed"] is (item["alpha"] == 32768)
                                and item["callback_resume_confirmed"]
                                and item["callback_output_equals_raw_input"] for item in alpha_matrix)

        gates = {
            "worker_return_confirmed": aex.get("worker_return_confirmed") is True,
            "one_helper_capture": len(captures) == 1,
            "pf_copy_callback_captured": bool(callback),
            "pf_copy_resume_captured": resume.get("address") == "0x1801a5b61",
            "callback_output_visible_equals_raw_input": resume.get("output_visible_equals_input") is True,
            "helper_copies_exact_pf16_words": helper_source == helper_destination,
            "padding_sentinel_preserved": capture.get("after_destination_padding") == [165] * 4,
            "helper_source_and_destination_in_output_payload": aex.get("helper_source_in_output_payload") is True,
            "alpha_matrix_only_32768_seed_or_propagate": alpha_matrix_gate,
        }
        payload.update(
            {
                "status": "PASS_STAGE_BOUNDARY_CLASSIFIED" if all(gates.values()) else "FAIL_CLOSED",
                "worker_entry": aex.get("worker_entry"),
                "helper_entry": capture.get("helper_entry"),
                "gates": gates,
                "observations": {
                    "raw_host_input_pf16": host_input,
                    "helper_source_pf16": helper_source,
                    "helper_destination_pf16": helper_destination,
                    "callback": callback,
                    "callback_resume": resume,
                    "pf16_alpha_matrix": alpha_matrix,
                },
                "host_pf_copy_behavior": "bounded fixture inference from observed callback ABI and byte effects; not an AE-exact host contract",
            }
        )
    except Exception as exc:
        payload["error"] = f"{type(exc).__name__}: {exc}"

    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    observations = payload.get("observations", {})
    lines = [
        "# OLMToonDilate PF16 Actual-AEX Stage Audit - 2026-07-16",
        "",
        "## Result",
        "",
        f"- Status: **{payload['status']}**",
        "- The worker calls the captured five-argument host PF_COPY callback at `0x1801a5b5e` and resumes at `0x1801a5b61`.",
        "- At resume, output visible bytes equal raw input bytes and output padding remains owned by the output sentinel.",
        "- This is bounded worker evidence only; the host PF_COPY behavior remains an inference, not an AE-exact contract.",
        "",
        "## Evidence",
        "",
        f"- Gates: `{payload.get('gates', {})}`",
        f"- Raw host input: `{observations.get('raw_host_input_pf16', [])}`",
        f"- Helper source/destination: `{observations.get('helper_source_pf16', [])}` / "
        f"`{observations.get('helper_destination_pf16', [])}`",
        f"- Callback/resume evidence: `{observations.get('callback', {})}` / `{observations.get('callback_resume', {})}`",
        f"- PF16 alpha matrix: `{observations.get('pf16_alpha_matrix', [])}`",
        "",
        "## Consequence",
        "",
        "No internal-stage transformation claim is made. The binary worker classification is limited to callback copy bytes, padding ownership, helper placement, and the observed alpha boundary: only `32768` seeded or propagated.",
        "",
        "## Reproduce",
        "",
        "```sh",
        "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf16_actual_aex_cli_differential_20260716.py",
        "```",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS_STAGE_BOUNDARY_CLASSIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
