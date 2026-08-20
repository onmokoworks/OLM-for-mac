from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_olm_generic_beta_gate.py"
SPEC = importlib.util.spec_from_file_location("generic_beta_gate", SCRIPT)
assert SPEC and SPEC.loader
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class GenericBetaGateTests(unittest.TestCase):
    def test_manifest_is_explicit_unique_and_covers_ten_plugins_and_shared_gates(self):
        tests = [row[1] for row in GATE.MANIFEST]
        self.assertEqual(len(tests), len(set(tests)))
        plugins = {row[0] for row in GATE.MANIFEST}
        self.assertTrue({"ColorKeep", "OLMBlur", "OLMColorKey", "OLMDistanceGradation",
                         "OLMKiraKira", "OLMRadialBlur", "OLMSmoother", "OLMSmoother2",
                         "OLMToonDilate", "common-world", "property", "oracle",
                         "performance", "package-hash", "windows-oracle-bundle",
                         "ae-smoke", "documentation"}.issubset(plugins))
        self.assertTrue(all((ROOT / test).is_file() and (ROOT / source).is_file()
                            for _, test, source in GATE.MANIFEST))

    def test_stdlib_runner_pass_fail_and_skip_exit_codes(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_unit_") as raw:
            base = Path(raw)
            passing = base / "test_pass.py"
            failing = base / "test_fail.py"
            skipped = base / "test_skip.py"
            empty = base / "test_empty.py"
            passing.write_text("def test_ok():\n    assert 2 + 2 == 4\n", encoding="utf-8")
            failing.write_text("def test_bad():\n    assert False\n", encoding="utf-8")
            skipped.write_text("import pytest\n@pytest.mark.skipif(True, reason='bounded')\ndef test_skip(): pass\n", encoding="utf-8")
            empty.write_text("def helper(): pass\n", encoding="utf-8")
            self.assertEqual(GATE.run_test_file(passing), 0)
            self.assertEqual(GATE.run_test_file(failing), 1)
            self.assertEqual(GATE.run_test_file(skipped), 77)
            self.assertEqual(GATE.run_test_file(empty), 1)

    def test_missing_source_fails_closed_and_records_identity_fields(self):
        row = GATE.execute_entry("demo", "tests/absent.py", "mac/absent.cpp", 1)
        self.assertEqual(row["status"], "FAIL")
        self.assertIsNone(row["test_sha256"])
        self.assertIsNone(row["source_sha256"])
        self.assertIn("command", row)
        self.assertIn("duration_seconds", row)

    def test_manifest_rows_are_suitable_for_plugin_summary(self):
        grouped = {}
        for plugin, test, _ in GATE.MANIFEST:
            grouped.setdefault(plugin, []).append(test)
        self.assertGreaterEqual(len(grouped["OLMColorKey"]), 2)
        self.assertGreaterEqual(len(grouped["common-world"]), 2)
        self.assertTrue(all(paths for paths in grouped.values()))

    def test_skip_is_fail_closed_by_default_cli_contract(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"INCOMPLETE" if has_skip and not args.allow_skip', source)
        self.assertIn('parser.add_argument("--allow-skip"', source)


if __name__ == "__main__":
    unittest.main()
