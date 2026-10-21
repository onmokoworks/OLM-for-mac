from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_same_table_dual_owner_plumbing_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")
EXPECTED_FILES = {
    TOOL: "a6a7e359be9dd31ba0eaede2a248c8f51247d6feeef9f8ab4c875c342862db3c",
    REPORT: "59f36cb877f47837684fa59d97fa3cac228fd11de5decee12e13524f2a77ac6c",
    MARKDOWN: "1b556f39e35619d11253a029a4f7048beb45eef2a3334a5f3ee3fb92a08ed9d3",
}


def load_tool():
    spec = importlib.util.spec_from_file_location("olm_dg_same_table_unit", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DistanceSameTableDualOwnerPlumbingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_tool()
        cls.value = json.loads(REPORT.read_text())

    def reject(self, mutate, *, recanonicalize: bool = False) -> None:
        value = copy.deepcopy(self.value)
        mutate(value)
        if recanonicalize:
            value["rows_sha256"] = self.tool.digest(value["rows"])
        self.assertFalse(self.tool.validate(value))

    def test_live_report_and_markdown(self) -> None:
        self.assertTrue(self.tool.validate(self.value))
        self.assertEqual(MARKDOWN.read_text(), self.tool.markdown(self.value))

    def test_external_file_pins(self) -> None:
        for path, expected in EXPECTED_FILES.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, path)

    def test_unknown_top_level_rejected(self) -> None:
        self.reject(lambda value: value.__setitem__("extra", True))

    def test_table_rejected(self) -> None:
        self.reject(lambda value: value["table"].__setitem__("sha256", "0" * 64))

    def test_build_rejected(self) -> None:
        self.reject(lambda value: value["build"].__setitem__("worker_sha256", "0" * 64))

    def test_live_identity_rejected(self) -> None:
        self.reject(lambda value: value["identities"].__setitem__("production_source_sha256", "0" * 64))

    def test_paired_raw_recanonicalization_rejected(self) -> None:
        def mutate(value):
            row = value["rows"][0]
            row["raw_sha256"] = "1" * 64
            row["aex_exported"]["raw_sha256"] = "1" * 64
            row["mac_renderbits"]["raw_sha256"] = "1" * 64
            row["mac_renderbits"]["host_substituted_oracle_sha256"] = "1" * 64
        self.reject(mutate, recanonicalize=True)

    def test_row_order_recanonicalization_rejected(self) -> None:
        self.reject(lambda value: value["rows"].reverse(), recanonicalize=True)

    def test_aex_lifecycle_recanonicalization_rejected(self) -> None:
        self.reject(lambda value: value["rows"][0]["aex_exported"].__setitem__("render_error", 25),
                    recanonicalize=True)

    def test_nested_unknown_recanonicalization_rejected(self) -> None:
        self.reject(lambda value: value["rows"][0]["mac_renderbits"].__setitem__("extra", 1),
                    recanonicalize=True)

    def test_public_overclaim_rejected(self) -> None:
        self.reject(lambda value: value["scope"].__setitem__("mac_public_admission", True))

    def test_native_overclaim_rejected(self) -> None:
        self.reject(lambda value: value["scope"].__setitem__("native_windows_result_claimed", True))


if __name__ == "__main__":
    unittest.main()
