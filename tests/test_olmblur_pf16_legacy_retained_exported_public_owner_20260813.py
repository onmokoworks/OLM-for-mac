from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py"
SPEC = importlib.util.spec_from_file_location("olmblur_pf16_legacy_retained_owner", GENERATOR)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OLMBlurPF16LegacyRetainedOwner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.value = json.loads(MODULE.REPORT.read_text())
        MODULE.validate(cls.value)

    def reject(self, mutation) -> None:
        changed = copy.deepcopy(self.value)
        mutation(changed)
        with self.assertRaises((ValueError, RuntimeError, KeyError, TypeError)):
            MODULE.validate(changed)

    def test_external_pins(self) -> None:
        self.assertEqual(sha(GENERATOR), "98c5629825e1d21d35569e4056aa7f174e613796254764fffa4670f2156d495a")
        self.assertEqual(sha(MODULE.REPORT), "3082206c93d62bada802d6bf567d6c1e885ac3cfcc2478b4fa12eda03fd2c8d7")

    def test_live(self) -> None:
        self.assertEqual(self.value, MODULE.live())

    def test_exact_and_mismatch_boundary(self) -> None:
        self.assertEqual([row["mismatched_bytes"] for row in self.value["rows"]], [0, 0, 0, 369])
        self.assertEqual([row["disposition"] for row in self.value["rows"]],
                         ["promotable_exact", "promotable_exact", "promotable_exact", "fail_closed_public_mismatch"])
        self.assertEqual(self.value["summary"], {"cells": 4, "raw_exact": 3, "public_mismatch": 1, "mismatch_bytes": 369, "padding_untouched": 4})

    def test_tamper(self) -> None:
        for mutation in (
            lambda d: d.update(extra=True),
            lambda d: d["identities"]["aex"].update(sha256="0" * 64),
            lambda d: d["rows"][0].update(public_output_sha256="0" * 64),
            lambda d: d["rows"][2].update(mismatched_bytes=1),
            lambda d: d["rows"][3].update(disposition="promotable_exact"),
            lambda d: d["summary"].update(raw_exact=4),
            lambda d: d["claims_not_made"].clear(),
        ):
            self.reject(mutation)

    def test_doc(self) -> None:
        self.assertEqual(MODULE.DOC.read_text(), MODULE.markdown(self.value))


if __name__ == "__main__":
    unittest.main()
