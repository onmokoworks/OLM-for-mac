import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olmkirakira_mode3_32x18_universal_candidate_20260815.py"
REPORT = ROOT / "handoffs/olmkirakira_mode3_32x18_candidate_20260815/build_identity.json"


class KiraMode332x18UniversalCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = REPORT.read_bytes()
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        cls.after = REPORT.read_bytes()
        cls.report = json.loads(cls.after)

    def test_identity_and_binary_contract(self):
        self.assertEqual(
            self.report["status"],
            "PASS_OLMKIRAKIRA_MODE3_32X18_DURABLE_UNIVERSAL_CANDIDATE_NO_INSTALL_NO_AE",
        )
        self.assertEqual(self.report["architectures"], ["x86_64", "arm64"])
        self.assertEqual(
            self.report["minimum_versions"],
            {"x86_64": "11.0", "arm64": "11.0", "Info.plist": "11.0"},
        )
        self.assertEqual(self.report["codesign"]["identity"], "adhoc")
        self.assertEqual(self.report["codesign"]["team_identifier"], "not set")
        self.assertTrue(self.report["codesign"]["deep_strict_verify"])
        self.assertEqual(len(self.report["codesign"]["cdhash"]), 40)
        self.assertTrue(self.report["frozen_transient_build_match"])
        for exports in self.report["exports"].values():
            self.assertEqual(exports, ["_EffectMain", "_PluginDataEntryFunction2"])

    def test_complete_inventory_and_public_replays(self):
        summary = self.report["inventory_summary"]
        self.assertEqual(summary["node_count"], len(self.report["inventory"]))
        self.assertGreaterEqual(summary["file_count"], 5)
        self.assertEqual(self.report["public_replay_5x3"]["positive_count"], 42)
        self.assertEqual(self.report["public_replay_5x3"]["negative_count"], 765)
        self.assertEqual(self.report["public_replay_mode3_32x18"]["positive_count"], 3)
        self.assertEqual(self.report["public_replay_mode3_32x18"]["lifecycle_failure_count"], 50)
        self.assertEqual(self.report["public_replay_mode3_32x18"]["negative_count"], 7)
        self.assertTrue(self.report["public_replay_mode3_32x18"]["all_failure_outputs_untouched"])

    def test_read_only_and_scope(self):
        self.assertEqual(self.before, self.after)
        self.assertEqual(
            self.report["scope"],
            {"aggregate_updated": False, "developer_id_or_notarization": False,
             "installed": False, "native_ae": False, "release_gate_updated": False},
        )


if __name__ == "__main__":
    unittest.main()
