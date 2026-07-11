#!/usr/bin/env python3
"""Run the OLMSmoother2 producer witness on the actual AEX binary.

This is deliberately a small, typed probe for the legacy current-AEX witness
at (91, 841).  It executes FUN_18000e170, FUN_18000f270, and FUN_18000e3a0
directly through the existing Unicorn AEX loader.  The result is local AEX
CPU-emulation evidence, not Windows truth or AE-exact evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EMU = ROOT / "tools" / "emulation"
sys.path.insert(0, str(EMU))

import test_smoother2_producer as producer  # noqa: E402


WITNESS_X = 91
WITNESS_Y = 841
DESCRIPTOR = [91, 841, 1, 91, 843, 5]
WIDTH = 92
HEIGHT = 844
SOURCE_RGBA = (0.99106717, 0.99106717, 0.99106717, 0.99607843)


def read_class_bytes(ss: Any, x: int, y: int) -> dict[str, int]:
    base = ss.class_base + y * ss.class_stride + x * 4
    raw = ss.loader.read_bytes(base, 4)
    return {"b0": raw[0], "b1": raw[1], "b2": raw[2], "b3": raw[3]}


def run_case(name: str, center_b0: int, prev_b0: int, left_b1: int) -> dict[str, Any]:
    loader = producer.AexLoader(str(producer.AEX_PATH), verbose=False, fast=True)
    ss = producer.SmootherStruct(loader, WIDTH, HEIGHT)
    ss.set_cur(WITNESS_X, WITNESS_Y)
    ss.set_base_weight(0.4)
    ss.set_smoothness(2.0)
    ss.set_src_pixel(WITNESS_X, WITNESS_Y - 1, SOURCE_RGBA)
    ss.set_class_pixel(WITNESS_X, WITNESS_Y, b0=center_b0)
    ss.set_class_pixel(WITNESS_X, WITNESS_Y - 1, b0=prev_b0)
    ss.set_class_pixel(WITNESS_X - 1, WITNESS_Y, b0=0, b1=left_b1)

    c = producer.call_e170(loader, ss, DESCRIPTOR)
    f270_ret, f270_count, f270_vertices = producer.call_f270(loader, ss, DESCRIPTOR, 1.0)
    e3a0_ret, e3a0_count, e3a0_vertices = producer.call_e3a0(loader, ss, DESCRIPTOR, 1.0, 1.0)

    return {
        "name": name,
        "xy": [WITNESS_X, WITNESS_Y],
        "descriptor": DESCRIPTOR,
        "producer_bytes": {
            "center_b0": center_b0,
            "prev_b0": prev_b0,
            "left_b1": left_b1,
            "center_pixel": read_class_bytes(ss, WITNESS_X, WITNESS_Y),
            "prev_pixel": read_class_bytes(ss, WITNESS_X, WITNESS_Y - 1),
            "left_pixel": read_class_bytes(ss, WITNESS_X - 1, WITNESS_Y),
        },
        "e170": {"c": c, "return_type": "u8"},
        "f270": {
            "return": f270_ret,
            "return_type": "u8",
            "append": f270_count == 1,
            "count": f270_count,
            "vertices": f270_vertices,
        },
        "e3a0": {
            "return": e3a0_ret,
            "return_type": "u8",
            "append": e3a0_count == 1,
            "count": e3a0_count,
            "vertices": e3a0_vertices,
        },
        # In this producer chain, the requested aggregate append gate is the
        # f270 wrapper result. e3a0 is also recorded independently above.
        "append": f270_count == 1,
    }


def build_result() -> dict[str, Any]:
    cases = [
        run_case("legacy_current_aex", center_b0=0, prev_b0=1, left_b1=0),
        run_case("control_suppressing", center_b0=0, prev_b0=0, left_b1=1),
    ]
    expected = {
        "legacy_current_aex": {"c": 2, "f270_append": True, "e3a0_append": True},
        "control_suppressing": {"c": 4, "f270_append": False, "e3a0_append": True},
    }
    checks = []
    for case in cases:
        exp = expected[case["name"]]
        checks.append(
            case["e170"]["c"] == exp["c"]
            and case["f270"]["append"] is exp["f270_append"]
            and case["e3a0"]["append"] is exp["e3a0_append"]
        )
    return {
        "kind": "olmsmoother2_typed_witness",
        "status": "local-aex-cpu-execution",
        "source": "tools/emulation/test_smoother2_typed_witness.py",
        "aex": str(producer.AEX_PATH.relative_to(ROOT)),
        "functions": ["FUN_18000e170", "FUN_18000f270", "FUN_18000e3a0"],
        "claim_boundary": "This is not Windows truth and not AE exact evidence; Mac source was not modified.",
        "cases": cases,
        "assertions": {"expected_shape_matches": all(checks), "per_case": checks},
    }


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Typed Witness",
        "",
        "- Status: `local-aex-cpu-execution`",
        f"- AEX: `{result['aex']}`",
        f"- Functions: `{', '.join(result['functions'])}`",
        "- Witness: `legacy current-AEX (91,841)`",
        "- Descriptor: `[91,841,1,91,843,5]`",
        "- Boundary: this result is not Windows truth and not AE exact evidence; Mac source was not modified.",
        "",
        "| Case | center_b0 | prev_b0 | left_b1 | c | f270 | e3a0 | chain append |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for case in result["cases"]:
        b = case["producer_bytes"]
        lines.append(
            f"| `{case['name']}` | {b['center_b0']} | {b['prev_b0']} | {b['left_b1']} | "
            f"{case['e170']['c']} | `{case['f270']['append']}` | `{case['e3a0']['append']}` | `{case['append']}` |"
        )
    lines.extend([
        "",
        f"- Shape assertions: `{'PASS' if result['assertions']['expected_shape_matches'] else 'FAIL'}`.",
        "- The legacy row is the requested `c=2 / f270=1 / e3a0=1` path.",
        "- The control row is the requested `c=4 / chain append=0` path; direct e3a0 execution is recorded separately.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    result = build_result()
    output_json = args.output_json or ROOT / "refs/conformance/olmsmoother2_typed_witness_20260710.json"
    output_md = args.output_md or ROOT / "refs/conformance/olmsmoother2_typed_witness_20260710.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    output_md.write_text(render_md(result), encoding="utf-8")
    print(render_md(result), end="")
    print(f"wrote_json={output_json}")
    print(f"wrote_md={output_md}")
    return 0 if result["assertions"]["expected_shape_matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
