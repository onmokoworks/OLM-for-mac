from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmblur_pf16_retained_tuples_exported_public_owner_20260813.py"
SPEC = importlib.util.spec_from_file_location("olmblur_pf16_retained_owner", GENERATOR)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OLMBlurPF16RetainedTuplesOwner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(MODULE.REPORT.read_text())
        MODULE.validate(cls.value)

    def reject(self, mutation):
        changed = copy.deepcopy(self.value)
        mutation(changed)
        with self.assertRaises((ValueError, RuntimeError, KeyError, TypeError)):
            MODULE.validate(changed)

    def test_live(self):
        self.assertEqual(self.value, MODULE.live())

    def test_both_exact_rows_are_pinned(self):
        self.assertEqual([row["mismatched_bytes"] for row in self.value["rows"]], [0, 0])
        self.assertEqual([row["disposition"] for row in self.value["rows"]],
                         ["promotable_exact", "promotable_exact"])

    def test_tamper(self):
        for mutation in (
            lambda d: d.update(extra=True),
            lambda d: d["summary"].update(raw_exact=1),
            lambda d: d["rows"][0].update(public_output_sha256="0" * 64),
            lambda d: d["rows"][1].update(mismatched_bytes=1),
            lambda d: d["rows"][1].update(disposition="fail_closed_public_mismatch"),
        ):
            self.reject(mutation)

    def test_doc(self):
        self.assertEqual(MODULE.DOC.read_text(), MODULE.markdown(self.value))


if __name__ == "__main__":
    unittest.main()
