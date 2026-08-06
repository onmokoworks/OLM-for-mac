#!/usr/bin/env python3
"""Show that the actual Ramp flat blob is not relocation-stable."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"
SOURCE_REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_flat_relocation_boundary_20260805.json"


def run(preallocate: int) -> dict:
    env = os.environ.copy()
    env["OLM_KK_RAMP_PREALLOCATE"] = str(preallocate)
    subprocess.run([sys.executable, str(PROBE)], cwd=ROOT, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    return json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))


def main() -> int:
    baseline = run(0)
    relocated = run(0x3000)
    assert baseline["roundtrip_compare"] == relocated["roundtrip_compare"] == 0
    assert baseline["flat_size"] == relocated["flat_size"] == 0x145
    assert baseline["flat_sha256"] != relocated["flat_sha256"]
    a = bytes.fromhex(baseline["flat_hex"])
    b = bytes.fromhex(relocated["flat_hex"])
    difference_offsets = [i for i, (left, right) in enumerate(zip(a, b)) if left != right]
    ignored_tail = baseline["wire_fields"]["ignored_tail"]
    assert difference_offsets
    assert all(i >= ignored_tail["offset"] for i in difference_offsets)
    assert baseline["canonical_flat_sha256"] == relocated["canonical_flat_sha256"]
    assert baseline["mode2_output_bits"] == relocated["mode2_output_bits"]
    assert all(value == 0 for value in baseline["garbage_taint_compare_results"].values())
    assert all(value == 0 for value in relocated["garbage_taint_compare_results"].values())
    spans: list[dict[str, int]] = []
    for offset in difference_offsets:
        if not spans or offset != spans[-1]["end"] + 1:
            spans.append({"start": offset, "end": offset})
        else:
            spans[-1]["end"] = offset
    report = {
        "schema": "olmkirakira-ramp-flat-relocation-boundary/1",
        "status": "canonical_pointer_free_wire_accepted_semantics_and_mode2_stable",
        "raw_blob_difference_offsets": difference_offsets,
        "raw_blob_difference_spans": spans,
        "runs": [
            {"preallocated_host_bytes": baseline["preallocated_host_bytes"], "flat_sha256": baseline["flat_sha256"], "difference_from_source_inline": baseline["source_inline_difference_offsets"]},
            {"preallocated_host_bytes": relocated["preallocated_host_bytes"], "flat_sha256": relocated["flat_sha256"], "difference_from_source_inline": relocated["source_inline_difference_offsets"]},
        ],
        "canonical_flat_sha256": baseline["canonical_flat_sha256"],
        "wire_fields": baseline["wire_fields"],
        "taint_patterns": ["zero", "0xA5", "allocation-derived byte pattern"],
        "conclusion": "All relocation differences are in the ignored tail. Actual UNFLATTEN accepts canonical zero-fill and tainted tails, compares equal, and produces bit-exact Mode2 output.",
        "mac_registration": "canonical deterministic serializer contract is green",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS_OLMKIRAKIRA_RAMP_FLAT_RELOCATION_BOUNDARY_20260805 differences={difference_offsets} canonical=accepted mode2=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
