#!/usr/bin/env python3
"""Unit tests for the bounded OLMKiraKira parameter-surface contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_olmkirakira_surface_contract_20260717 as contract  # noqa: E402


class OLMKiraKiraSurfaceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.windows_rows, _ = contract.load_windows_surface()
        cls.mac_rows = contract.load_mac_surface()
        cls.mapping_table = contract.build_mapping_table(cls.windows_rows, cls.mac_rows)
        cls.mapping_by_match = contract.mapping_table_by_match_name(cls.mapping_table)

    def test_mapping_summary_matches_expected_surface_counts(self) -> None:
        counts = {}
        for row in self.mapping_table:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        self.assertEqual(
            counts,
            {
                "mapped_plugin_surface": 30,
                "shared_builtin_passthrough": 2,
                "unmappable_custom_ramp_payload_row": 5,
                "unmappable_windows_group_separator": 5,
            },
        )

    def test_full_windows_case_fails_closed_on_missing_ramp_rows(self) -> None:
        result = contract.validate_requested_rows(
            [row.request_row() for row in self.windows_rows],
            self.mapping_by_match,
        )
        self.assertEqual(result["status"], "unmappable")
        self.assertEqual(result["code"], "unmappable_row_present")

    def test_mapped_rows_are_accepted_by_match_name(self) -> None:
        request_rows = [
            row.request_row()
            for row in self.windows_rows
            if self.mapping_by_match[row.match_name]["application_allowed"]
        ]
        result = contract.validate_requested_rows(request_rows, self.mapping_by_match)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["code"], "all_rows_match_name_mapped")
        self.assertGreater(result["accepted_count"], 0)
        self.assertEqual(result["rejected_count"], 0)

    def test_index_only_rows_are_rejected(self) -> None:
        request_rows = [
            {"name": row.name, "property_index": row.property_index, "value": row.value}
            for row in self.windows_rows[:4]
        ]
        result = contract.validate_requested_rows(request_rows, self.mapping_by_match)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["code"], "index_only_request_rejected")
        self.assertEqual(result["accepted_count"], 0)
        self.assertEqual(result["rejected_count"], 4)

    def test_custom_ramp_ui_is_declared_to_the_host(self) -> None:
        source = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text()
        pipl = (ROOT / "mac/OLMKiraKira/OLMKiraKiraPiPL.r").read_text()
        self.assertIn("def.ui_flags = PF_PUI_CONTROL", source)
        self.assertIn("out_data->out_flags  = 0x02008040;", source)
        self.assertIn("AE_Effect_Global_OutFlags { 0x02008040 }", pipl)


if __name__ == "__main__":
    unittest.main()
