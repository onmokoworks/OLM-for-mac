#!/usr/bin/env python3
"""Smoke-test the bounded OLMKiraKira parameter-surface contract."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_olmkirakira_surface_contract_20260717 as contract  # noqa: E402


def main() -> int:
    report = contract.build_report()
    assert report["kind"] == "olmkirakira_parameter_surface_contract"
    assert report["artifact_date"] == "2026-07-17"
    assert report["generated_on"] == "2026-07-17"
    summary = report["mapping_summary"]
    assert summary["mapped_plugin_surface"] == 25, summary
    assert summary["shared_builtin_passthrough"] == 2, summary
    assert summary["unmappable_missing_ramp_row"] == 5, summary
    assert summary["unmappable_custom_ramp_payload_row"] == 5, summary
    assert summary["unmappable_windows_group_separator"] == 5, summary

    examples = report["validation_examples"]
    assert examples["full_windows_case"]["status"] == "unmappable", examples["full_windows_case"]
    assert examples["full_windows_case"]["code"] == "missing_ramp_row_present", examples["full_windows_case"]
    assert examples["mapped_rows_by_match_name"]["status"] == "accepted", examples["mapped_rows_by_match_name"]
    assert examples["index_only_rows"]["status"] == "rejected", examples["index_only_rows"]
    assert examples["index_only_rows"]["code"] == "index_only_request_rejected", examples["index_only_rows"]

    with tempfile.TemporaryDirectory() as tmp:
        out_json = Path(tmp) / "surface.json"
        out_md = Path(tmp) / "surface.md"
        contract.write_report(report, out_json=out_json, out_md=out_md)
        written = json.loads(out_json.read_text(encoding="utf-8"))
        md = out_md.read_text(encoding="utf-8")
    assert written["validation_policy"]["index_only_requests"] == "rejected"
    assert "OLMKiraKira Parameter Surface Contract" in md
    assert "`unmappable_missing_ramp_row`" in md
    print("[OK] OLMKiraKira parameter-surface contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
