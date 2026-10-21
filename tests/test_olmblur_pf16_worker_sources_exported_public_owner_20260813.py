from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py"
SPEC = importlib.util.spec_from_file_location("olmblur_pf16_worker_public", GENERATOR)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OLMBlurPF16WorkerSourcesPublicOwner(unittest.TestCase):
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

    def test_authority_tamper(self):
        for mutation in (
            lambda d: d.update(extra=True),
            lambda d: d.update(status="PASS"),
            lambda d: d["identities"]["aex"].update(sha256="0" * 64),
            lambda d: d["summary"].update(cells=3),
        ):
            self.reject(mutation)

    def test_row_tamper(self):
        for mutation in (
            lambda d: d["rows"][0].update(rowbytes=108),
            lambda d: d["rows"][0].update(active_source_sha256="0" * 64),
            lambda d: d["rows"][1].update(active_output_sha256="0" * 64),
            lambda d: d["rows"][1]["public_result"].update(padding_mismatches=1),
        ):
            self.reject(mutation)

    def test_docs(self):
        self.assertEqual(MODULE.DOC.read_text(), MODULE.markdown(self.value))


if __name__ == "__main__":
    unittest.main()
