#!/usr/bin/env python3
"""Replay observed Smoother2 Windows writer-frame floats through the AEX PF8 worker.

This is deliberately a writer-only boundary audit.  It does not claim that the
float tuples came from the Mac host, crop, classifier, c280, or cce0 path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

import test_olmsmoother2_typed_writeback_20260717 as typed  # noqa: E402

REPORT_JSON = ROOT / "refs/conformance/olmsmoother2_writer_frame_replay_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmsmoother2_writer_frame_replay_20260718.md"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"

CASES = [
    {
        "case_id": "legacy_case_0004_writer_frame",
        "windows_writer_frame_rgba_f32": [0.80824906, 0.80824906, 0.80824906, 0.44156867],
        "windows_pf8_argb_hex": "e8e8e871",
    },
    {
        "case_id": "legacy_case_0012_writer_frame",
        "windows_writer_frame_rgba_f32": [1.0, 1.0, 1.0, 0.0],
        "windows_pf8_argb_hex": "ffffff00",
    },
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    typed.SRC = tuple(case["windows_writer_frame_rgba_f32"])
    observed = typed.run_depth("PF8")
    expected = case["windows_pf8_argb_hex"]
    expected_memory = int(expected, 16).to_bytes(4, "little").hex()
    return {
        "case_id": case["case_id"],
        "windows_writer_frame_rgba_f32": case["windows_writer_frame_rgba_f32"],
        "windows_pf8_argb_hex": expected,
        "windows_pf8_argb_memory_hex": expected_memory,
        "aex_observed_pf8_argb_hex": observed["actual_raw_hex"],
        "raw_equal": observed["actual_raw_hex"] == expected_memory,
        "writer_replay_classification": "reproduced" if observed["actual_raw_hex"] == expected_memory else "not_reproduced_from_supplied_float_tuple",
        "worker": observed["worker"],
        "dynamic_ranges": observed["dynamic_ranges"],
        "dynamic_next_calls": observed["dynamic_next_calls"],
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 observed writer-frame replay",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "Observed Windows writer-frame float4 tuples were fed directly into the checked-in AEX PF8 typed worker. The result is fail-closed: one tuple reproduces and one does not.",
        "",
        "## Results",
        "",
        "| Case | Windows writer-frame RGBA float4 | Windows PF8 ARGB integer | Windows memory bytes | AEX memory bytes | Result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['windows_writer_frame_rgba_f32']}` | "
            f"`{row['windows_pf8_argb_hex']}` | `{row['windows_pf8_argb_memory_hex']}` | "
            f"`{row['aex_observed_pf8_argb_hex']}` | `{row['writer_replay_classification']}` |"
        )
    lines += [
        "",
        "## FACT",
        "",
        "- The AEX PF8 worker consumed both supplied float4 tuples and produced deterministic raw bytes.",
        "- Case 0012 reproduces the Windows packed record after interpreting the logged integer as little-endian memory bytes.",
        "- Case 0004 does not: the supplied tuple produces `71cecece`, while the Windows packed record is `71e8e8e8` in memory order.",
        "- The worker and AEX identity are checked by the existing typed-writeback grounding.",
        "",
        "## INFERENCE",
        "",
        "- The writer is not ruled out: the 0004 tuple may not be the actual writer-entry tuple, or the Windows raw record may refer to another stage/packing convention.",
        "- The 0012 match alone is insufficient to generalize the writer boundary.",
        "- This does not identify the upstream config, crop translation, classifier, c280, or cce0 state; no production behavior was changed.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/audit_olmsmoother2_writer_frame_replay_20260718.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=REPORT_MD)
    args = parser.parse_args()
    require(hashlib.sha256(typed.AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    rows = [run_case(case) for case in CASES]
    report = {
        "verdict": "PARTIAL_SMOOTHER2_OBSERVED_WRITER_FRAME_REPLAY",
        "scope": "Mac-local Unicorn replay of Windows-observed PF8 writer-frame tuples",
        "aex_sha256": EXPECTED_AEX_SHA256,
        "cases": rows,
        "facts": [
            "The AEX PF8 worker replayed both supplied tuples; only the 0012 packed record reproduced.",
            "No production plugin source was changed.",
        ],
        "inferences": [
            "The PF8 writer/store remains unresolved because the 0004 supplied tuple did not reproduce its Windows packed record.",
            "Upstream config/crop/classifier/c280/cce0 semantics remain unresolved.",
        ],
        "claims_not_made": ["AE exactness", "Mac host equivalence", "full-frame equivalence", "upstream producer equivalence"],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render(report) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
