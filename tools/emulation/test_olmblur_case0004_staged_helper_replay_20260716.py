#!/usr/bin/env python3
"""Direct regression/report writer for the bounded case_0004 helper replay."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmblur_case0004_staged_helper_replay import WITNESSES, run_probe  # noqa: E402

REPORT_JSON = ROOT / "refs/conformance/olmblur_case0004_staged_helper_replay_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0004_staged_helper_replay_20260716.md"


def main() -> int:
    report = run_probe()
    if report["status"] != "pass_two_layer_witness":
        raise AssertionError(f"unexpected status: {report['status']}")
    if len(report["radius_sequence"]) != 4:
        raise AssertionError(f"caller did not expose four radii: {report['radius_sequence']!r}")
    microfixtures = report["actual_helper_micro_exact"]["fixtures"]
    if len(microfixtures) != 8 or not report["actual_helper_micro_exact"]["all_exact"]:
        raise AssertionError("actual helper microfixture coverage is incomplete or non-exact")
    for fixture in microfixtures:
        expected_dimensions = ([fixture["radius"] * 2 + 1, 1]
                               if fixture["direction"] == "horizontal"
                               else [1, fixture["radius"] * 2 + 1])
        if fixture["dimensions"] != expected_dimensions:
            raise AssertionError(f"microfixture strip dimensions differ: {fixture!r}")
        if fixture["instruction_cap"] > 3_000_000 or fixture["actual_instructions"] >= fixture["instruction_cap"]:
            raise AssertionError(f"microfixture instruction bound differs: {fixture!r}")
        if fixture["actual_target_bits_hex"] != fixture["portable_target_bits_hex"]:
            raise AssertionError(f"microfixture target differs: {fixture!r}")
    expected_stages = len(WITNESSES) * 4 * 2
    portable = report["portable_full_cone_result"]
    if len(portable["stages"]) != expected_stages:
        raise AssertionError(f"portable cone stage count differs: {len(portable['stages'])}")
    if any(stage.get("execution") != "portable_only" for stage in portable["stages"]):
        raise AssertionError("portable cone contains a non-portable execution record")

    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# OLMBlur case_0004 staged-helper replay",
        "",
        "## FACT",
        "",
        f"- Pinned actual AEX: `{report['identity']['aex']}` / `{report['identity']['aex_sha256']}`.",
        "- Exact manifest parameters: amount `125.599998474121`, smoothness `100`, repeat `4`, bias `1`, Legacy `0`.",
        f"- The actual worker staging boundary `{report['staging']['boundary']}` captured the complete `{report['staging']['plane_bytes']}`-byte RGB float plane and `{report['staging']['flags_bytes']}`-byte active mask; both match the retained PF16 decode.",
        f"- During schedule capture, both helper bodies are detoured to an immediate return. All `{len(report['staging']['helper_calls_captured'])}` guest caller calls retain their radius, dimensions, pass range, weight pointer, and callback-produced weight bytes in the JSON.",
        f"- The captured and H/V-agreed radius sequence is `{report['radius_sequence']}`. Coefficients come from `{report['staging']['math_backend']}` and therefore are not Windows CRT truth. Only those declared callback-produced bytes drive the bounded helper calls.",
        f"- Layer A: all `{len(microfixtures)}` actual-AEX one-strip helper fixtures match the portable C++ helper byte-for-byte. Every actual run uses a `3,000,000` instruction cap.",
        f"- Layer B: two independent `{portable['initial_crop_dimensions'][0]}x{portable['initial_crop_dimensions'][1]}` dependency cones are composed through the portable helper only, using the exact caller-captured radii and weight bytes.",
        "",
        "## Witnesses",
        "",
    ]
    for point, values in portable["final"].items():
        lines.append(
            f"- `{point}` portable full-cone float32 bits: `{values['portable_full_cone_bits_hex']}`."
        )
    lines.extend([
        "",
        "## INFERENCE",
        "",
        f"- Classification: `{report['classification']}`.",
        "- `actual_helper_micro_exact` establishes function-level compatibility only on the eight deterministic strips.",
        "- `portable_full_cone_result` is a complete portable composition for the two witnesses under the declared host-backed libm coefficients. No actual-AEX full chain or Windows CRT coefficient equivalence is executed or implied.",
        "- Neither layer is AE exact or Windows/export evidence.",
        "- The known capped full-image run was not repeated.",
        "",
        "## Test",
        "",
        "```text",
        "python3 tools/emulation/test_olmblur_case0004_staged_helper_replay_20260716.py",
        "```",
        "",
        "## Changed files",
        "",
        "- `tools/emulation/probe_olmblur_case0004_staged_helper_replay.py` (new)",
        "- `tools/emulation/probe_olmblur_case0004_portable_helper.cpp` (new)",
        "- `tools/emulation/test_olmblur_case0004_staged_helper_replay_20260716.py` (new)",
        "- `refs/conformance/olmblur_case0004_staged_helper_replay_20260716.json` (new)",
        "- `refs/conformance/olmblur_case0004_staged_helper_replay_20260716.md` (new)",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n")
    output = {
        "status": report["status"],
        "actual_microfixtures": len(microfixtures),
        "portable_stages": len(portable["stages"]),
        "radius_sequence": report["radius_sequence"],
        "portable_final": portable["final"],
        "report_json": str(REPORT_JSON.relative_to(ROOT)),
        "report_md": str(REPORT_MD.relative_to(ROOT)),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
