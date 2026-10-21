from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = (
    ROOT
    / "tools/emulation/"
    "test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py"
)
REPORT = (
    ROOT
    / "refs/conformance/"
    "olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("dblur_natural64_closure", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("generator import failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalBlurNatural64ClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_generator()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_checked_in_report_validates(self) -> None:
        self.module.validate_report(copy.deepcopy(self.report))

    def test_worker_hash_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["worker_actual"][1]["raw_pixel_sha256"] = "0" * 64
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_worker_contract_mutations_fail_closed(self) -> None:
        for field, value in (("pixel_format", "argb8"), ("suite_requests", []), ("setup", {})):
            mutated = copy.deepcopy(self.report)
            mutated["worker_actual"][1][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                self.module.validate_report(mutated)

    def test_public_hash_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["public_effectmain"][2]["raw_sha256"] = "f" * 64
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_identity_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["identities"]["worker_commit"] = "0" * 40
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_lifecycle_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["public_effectmain"][0]["param_checkin"] = 20
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_public_contract_mutations_fail_closed(self) -> None:
        for field, value in (
            ("pre_checkout", 1), ("pixel_checkout", 1), ("output_checkout", 0),
            ("input_checkin", 0), ("noise_layer_optional_and_absent", False),
            ("padding", False), ("input_unchanged", False),
        ):
            mutated = copy.deepcopy(self.report)
            mutated["public_effectmain"][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                self.module.validate_report(mutated)

    def test_source_basis_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["source_basis"][2]["public_raw_sha256"]["PF32"] = "0" * 64
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_source_identity_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["source_basis"][1]["typed_input_sha256"]["PF16"] = "0" * 64
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_counterfactual_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["counterfactuals"]["rejects"] = 11
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)

    def test_claim_boundary_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.report)
        mutated["claim_boundary"]["admitted"] = "all Type2 geometry"
        with self.assertRaises(RuntimeError):
            self.module.validate_report(mutated)


if __name__ == "__main__":
    unittest.main()
