#!/usr/bin/env python3
"""Focused regression for the natural B150 entry checkpoint."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_radialblur_natural_b150_checkpoint_20260717.py"


def main() -> int:
    source = PROBE.read_text(encoding="utf-8")
    for forbidden in (
        "write_bytes(param_ctx + 0x6C",
        "write_bytes(param_ctx + 0x70",
        "write_bytes(work + 0x4200",
        "write_bytes(work + 0x4204",
        "write_bytes(work + 0x3EE0",
        "write_bytes(work + 0x4070",
    ):
        assert forbidden not in source, f"direct state fabrication found: {forbidden}"
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        output_json = root / "checkpoint.json"
        output_md = root / "checkpoint.md"
        completed = subprocess.run(
            [sys.executable, str(PROBE), "--output-json", str(output_json), "--output-md", str(output_md)],
            check=False,
        )
        assert completed.returncode == 0, f"probe exit {completed.returncode}"
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["status"] == "pass"
        assert all(value for group in report["gates"].values() for value in group.values()), report["gates"]
        assert report["harness"]["max_instructions"] == 2_000_000
        assert report["harness"]["python_prefill"] is False
        assert report["harness"]["worker_detour"] is False
        assert len(report["provenance"]["reference_edge_fades"]) == 13
        assert all(item["outer_edge_fade"] == 0 and item["inner_edge_fade"] == 0
                   for item in report["provenance"]["reference_edge_fades"])
        baseline = report["runs"]["manifest_baseline"]
        minimum = report["runs"]["outer_edge_fade_1"]
        checkpoint = minimum["checkpoint"]
        assert checkpoint["abi"]["effective_cells"] == 49 * 4
        assert baseline["checkpoint"]["context"]["left_span_i32"] == 0
        assert baseline["checkpoint"]["context"]["left_table_inline"]["nonzero_count"] == 0
        assert checkpoint["context"]["left_span_i32"] == 1
        assert checkpoint["context"]["right_span_i32"] == 0
        assert checkpoint["context"]["left_table_inline"]["nonzero_count"] == 1
        assert minimum["parameter_materialization"]["direct_param_field_writes_by_harness"] == 0
        assert any(item["reader_index"] == 5 and item["value"] == 1
                   for item in minimum["parameter_materialization"]["edge_reader_provenance"])
        assert checkpoint["planes"]["source_rgba"]["nonzero_cell_count"] == 49 * 4
        assert checkpoint["planes"]["source_alpha"]["nonzero_cell_count"] == 49 * 4
        assert checkpoint["planes"]["scale"]["nonzero_value_count"] == 0
        assert "## FACT" in output_md.read_text(encoding="utf-8")
        assert "## INFERENCE" in output_md.read_text(encoding="utf-8")
    print("[OK] natural B150 entry checkpoint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
