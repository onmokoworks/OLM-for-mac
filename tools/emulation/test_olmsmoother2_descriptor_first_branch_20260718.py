#!/usr/bin/env python3
"""Audit the first source-level branch explaining the Smoother2 descriptor split.

This is read-only evidence classification. It deliberately does not alter the
Mac plug-in, tune pixels, or claim AE exactness.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "refs/conformance/olmsmoother2_mac_actual_ae_boundary_20260717.json"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
REPORT_JSON = ROOT / "refs/conformance/olmsmoother2_descriptor_first_branch_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmsmoother2_descriptor_first_branch_20260718.md"


def trace_value(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            return line
    raise AssertionError(f"missing trace line: {prefix}")


def source_line(lines: list[str], needle: str) -> int:
    for number, line in enumerate(lines, 1):
        if needle in line:
            return number
    raise AssertionError(f"missing source text: {needle}")


def source_line_between(lines: list[str], needle: str, start: int, end: int) -> int:
    for number in range(start, min(end, len(lines)) + 1):
        if needle in lines[number - 1]:
            return number
    raise AssertionError(f"missing scoped source text: {needle}")


def main() -> int:
    boundary = json.loads(BOUNDARY.read_text())
    source_lines = SOURCE.read_text().splitlines()
    trace_lines = boundary["mac_internal_trace"]["lines"]
    mac_desc = tuple(map(int, re.search(r"desc=\(([^)]+)\)", trace_value(trace_lines, "trace cardinal6 desc=")).group(1).split(",")))
    win_desc = tuple(boundary["boundary"]["windows_actual_aex_witness"]["descriptor"])
    expected_mac = (92, 840, 1, 92, 843, 2)
    expected_win = (92, 841, 1, 92, 842, 2)
    assert mac_desc == expected_mac, mac_desc
    assert win_desc == expected_win, win_desc

    cardinal_line = source_line(source_lines, "int s1[3]; scan_d3b0(s1, &g, center);")
    d3b0_a0_line = source_line(source_lines, "if (cp_b(g, xp1, y, 0) == 0)")
    d3b0_right_line = source_line(source_lines, "if (cp_b(g, xp1, y, 1) != 0)")
    d3b0_left_line = source_line(source_lines, "if (cp_b(g, x,   y, 1) != 0)")
    d3b0_decrement_line = source_line_between(source_lines, "y--;", d3b0_a0_line, d3b0_a0_line + 20)
    da50_stop_line = source_line(source_lines, "if (cp_b(g, xp1, y, 0) == 0) break;")

    class_lines = [line for line in trace_lines if line.startswith("trace cardinal6 cplane y=")]
    assert any("y=840 x=92 bytes=255,255,0,255 x1=93 bytes=255,0,0,0" in line for line in class_lines)
    assert any("y=841 x=92 bytes=255,0,0,255 x1=93 bytes=255,0,0,0" in line for line in class_lines)

    # The Mac trace's d3b0 path: at y=841 all three loop predicates pass,
    # then y decrements to 840; at y=840 the left-column R predicate stops.
    facts = {
        "descriptor": {
            "windows": list(win_desc),
            "mac": list(mac_desc),
            "first_differing_fields": [1, 4],
        },
        "facts": {
            "center_y841_argb": [255, 0, 0, 255],
            "left_y841_argb": [255, 0, 0, 255],
            "left_y840_argb": [255, 255, 0, 255],
        },
        "source_locations": {
            "cardinal6_descriptor_composition": cardinal_line,
            "d3b0_a0_stop": d3b0_a0_line,
            "d3b0_right_r_stop": d3b0_right_line,
            "d3b0_left_r_stop": d3b0_left_line,
            "d3b0_decrement": d3b0_decrement_line,
            "da50_a0_stop": da50_stop_line,
        },
        "classification": {
            "status": "source_branch_identified_upstream_class_plane_witness_needed",
            "first_mac_branch": "scan_d3b0 left-column R stop at (x=92,y=840)",
            "not_claimed": ["AE exact", "Windows class-plane bytes at the same point", "root cause of class-plane divergence"],
        },
        "inference": {
            "d3b0_second_iteration_stop": "At y=840, the observed left-column R byte is nonzero, so the source condition at the left-column R stop is the first decisive branch.",
            "windows_implication": "Windows returning y=841 means the same stop is not reached in the same way, or the Windows class-plane byte at that coordinate differs.",
        },
    }
    REPORT_JSON.write_text(json.dumps(facts, indent=2) + "\n")
    REPORT_MD.write_text(
        "# OLMSmoother2 descriptor first-branch audit - 2026-07-18\n\n"
        "## Conclusion\n\n"
        "The first source-level branch explaining the current Mac descriptor is "
        "the `scan_d3b0` left-column R stop at `(x=92,y=840)`. This is a "
        "branch classification, not an AE-exactness claim and not a source fix.\n\n"
        "## FACT\n\n"
        f"- Windows accepted descriptor: `{list(win_desc)}`.\n"
        f"- Mac trace descriptor: `{list(mac_desc)}`.\n"
        "- `cardinal6` constructs the descriptor from `scan_d3b0` followed by `scan_da50`.\n"
        "- Mac trace at `(92,841)` has class bytes `[A,R,G,B]=[255,0,0,255]`; "
        "at `(92,840)` the left-column bytes are `[255,255,0,255]`.\n"
        f"- In `scan_d3b0`, the left-column R stop is at source line `{d3b0_left_line}`; "
        f"the preceding vertical step is line `{d3b0_decrement_line}`.\n\n"
        "## INFERENCE\n\n"
        "- On the Mac trace, the scan passes the predicates at `y=841`, decrements "
        "to `y=840`, then stops because `R@(x=92,y=840) != 0`; that yields the "
        "second descriptor field `840`.\n"
        "- The Windows descriptor's `841` implies that this stop condition is not "
        "reached in the same way, or that the Windows class-plane byte at that "
        "coordinate differs. The current evidence does not distinguish those two "
        "possibilities.\n"
        "- The second differing field `843` vs `842` comes from the independent "
        "`scan_da50` result and must be audited separately; it is not evidence that "
        "the first `scan_d3b0` branch is wrong.\n\n"
        "## Next evidence\n\n"
        "A Windows same-run class-plane witness for `(92,840)`, `(92,841)`, and "
        "the corresponding `x+1` column is required before changing the scanner or "
        "class-plane generation. PNG tuning and Mac source changes are forbidden "
        "for this audit.\n"
    )
    print("PASS Smoother2 descriptor first-branch audit")
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
