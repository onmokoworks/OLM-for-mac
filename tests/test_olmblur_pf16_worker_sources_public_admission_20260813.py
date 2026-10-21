from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmblur_pf16_worker_sources_public_admission_20260813.py"
SPEC = importlib.util.spec_from_file_location("olmblur_pf16_worker_admission", GENERATOR)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OLMBlurPF16WorkerSourcesAdmission(unittest.TestCase):
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
        self.assertEqual(self.value, MODULE.build(MODULE.run()))

    def test_authority_tamper(self):
        for mutation in (
            lambda d: d.update(extra=True),
            lambda d: d.update(status="PASS"),
            lambda d: d["identities"]["source"].update(sha256="0" * 64),
            lambda d: d["identities"]["windows_exported_owner"].update(sha256="0" * 64),
            lambda d: d["identities"]["retained_tuple_owner"].update(sha256="0" * 64),
            lambda d: d["identities"]["legacy_retained_owner"].update(sha256="0" * 64),
        ):
            self.reject(mutation)

    def test_contract_tamper(self):
        for mutation in (
            lambda d: d["cells"][0].update(rowbytes=108),
            lambda d: d["cells"][1].update(amount_f64=10.0),
            lambda d: d["cells"][4].update(legacy=0),
            lambda d: d["shared_parameters"].update(repeat=2),
            lambda d: d["summary"].update(negative_controls=123),
        ):
            self.reject(mutation)

    def test_recanonicalized_row_tamper(self):
        def mutation(value):
            value["run_lines"][0] = value["run_lines"][0].replace("exact=1", "exact=0")
            value["run_sha256"] = hashlib.sha256(("\n".join(value["run_lines"]) + "\n").encode()).hexdigest()
        self.reject(mutation)

    def test_docs(self):
        self.assertEqual(MODULE.DOC.read_text(), MODULE.markdown(self.value))

    def test_current_release_docs_preserve_pf16_boundary(self):
        docs = (
            ROOT / "README.md",
            ROOT / "KNOWN_LIMITATIONS.md",
            ROOT / "notes/CONFORMANCE_LEDGER.md",
            ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md",
            ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md",
            ROOT / "refs/conformance/olm_mac_port_orchestrator_boundary_20260805.md",
        )
        for path in docs:
            text = path.read_text()
            with self.subTest(path=path):
                self.assertIn("PF16", text)
                self.assertIn("22eb712a", text)
                self.assertIn("ecdf3d93", text)
                self.assertIn("494", text)
                self.assertIn("8/8", text)


if __name__ == "__main__":
    unittest.main()
