from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_same_table_dual_owner_plumbing_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")
EXPECTED_FILES = {
    TOOL: "8f11d24a0e9dfb1943493e5aef6f32a7b089de7575e577d827a5434e677da626",
    REPORT: "77fc65535ca2390e3e626446a86aa9ebbbbd6612db76875ccca9714876095e98",
    MARKDOWN: "80360215dcca0a6774fa3fe5a1307cdb26542d0a269a7b607aafda377881d3f0",
}


def load_tool():
    spec = importlib.util.spec_from_file_location("olm_directional_same_table_unit", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SameTableDualOwnerPlumbingTest(unittest.TestCase):
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

    def test_table_identity_rejected(self) -> None:
        self.reject(lambda value: value["table"].__setitem__("sha256", "0" * 64))

    def test_mac_table_call_census_rejected(self) -> None:
        self.reject(lambda value: value["mac_table_calls"].__setitem__("pow", 47513))

    def test_build_identity_rejected(self) -> None:
        self.reject(lambda value: value["build"].__setitem__("worker_sha256", "0" * 64))

    def test_live_input_identity_rejected(self) -> None:
        self.reject(lambda value: value["identities"].__setitem__("aex_sha256", "0" * 64))

    def test_paired_raw_recanonicalization_rejected(self) -> None:
        def mutate(value):
            row = value["rows"][0]
            for owner in (row, row["aex_exported"], row["mac_production_direct"]):
                owner["raw_sha256"] = "1" * 64
            row["aex_exported"]["expected_exported_sha256"] = "1" * 64
            row["mac_production_direct"]["exported_oracle_sha256"] = "1" * 64
        self.reject(mutate, recanonicalize=True)

    def test_row_order_recanonicalization_rejected(self) -> None:
        self.reject(lambda value: value["rows"].reverse(), recanonicalize=True)

    def test_aex_lifecycle_recanonicalization_rejected(self) -> None:
        self.reject(lambda value: value["rows"][0]["aex_exported"].__setitem__("render_mode", "classic"),
                    recanonicalize=True)

    def test_nested_unknown_key_recanonicalization_rejected(self) -> None:
        self.reject(lambda value: value["rows"][0]["mac_production_direct"].__setitem__("extra", 1),
                    recanonicalize=True)

    def test_scope_overclaim_rejected(self) -> None:
        self.reject(lambda value: value["scope"].__setitem__("native_windows_result_claimed", True))

    def test_summary_rejected(self) -> None:
        self.reject(lambda value: value["summary"].__setitem__("same_table_full_raw_exact", 5))


if __name__ == "__main__":
    unittest.main()
