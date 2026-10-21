from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "tools/emulation/audit_olm_hostless_batch5_incremental_install_20260813.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("olm_batch5_audit_test", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch5Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_auditor()
        cls.live = cls.module.generate()

    def test_live_report(self):
        self.module.validate(self.live)

    def test_exact_partition(self):
        self.assertEqual(set(self.live["plugins"]), {"OLMBlur", "OLMDirectionalBlur", "OLMRadialBlur"})
        self.assertTrue(self.live["identity_change"]["other_seven_rows_exact"])
        self.assertEqual(self.live["all10_preflight"]["exact_bundles"], 10)

    def test_scope(self):
        self.assertFalse(self.live["scope"]["after_effects_launched"])
        self.assertFalse(self.live["scope"]["batched_ae_checkpoint_complete"])
        self.assertFalse(self.live["scope"]["formal_gate_complete"])

    def test_top_level_extra_rejected(self):
        changed = copy.deepcopy(self.live)
        changed["extra"] = True
        with self.assertRaises(ValueError):
            self.module.validate(changed)

    def test_plugin_hash_tamper_rejected(self):
        changed = copy.deepcopy(self.live)
        changed["plugins"]["OLMBlur"]["new_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.module.validate(changed)

    def test_scope_tamper_rejected(self):
        changed = copy.deepcopy(self.live)
        changed["scope"]["batched_ae_checkpoint_complete"] = True
        with self.assertRaises(ValueError):
            self.module.validate(changed)


if __name__ == "__main__":
    unittest.main()
