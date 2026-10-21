from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = (
    ROOT / "tools/emulation/"
    "test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py"
)
REPORT = (
    ROOT / "refs/conformance/"
    "olmdirectionalblur_dual_side_public_source_guard_closure_20260813.json"
)
TOOL_SHA256 = "40e86f9c878d688043afef508ffbd9c885093a432c82a47e2f5b03f4676e2eb8"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tool():
    spec = importlib.util.spec_from_file_location("directional_dual_guard", TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import closure tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalDualSidePublicSourceGuardClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_tool()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_generator_identity_is_externally_pinned(self) -> None:
        self.assertEqual(sha256(TOOL), TOOL_SHA256)

    def test_checked_in_report_validates(self) -> None:
        self.assertTrue(self.module.validate_report(self.report))

    def test_top_level_identity_tuple_and_boundary_tampering_fails_closed(self) -> None:
        mutations = (
            lambda r: r.update(extra=True),
            lambda r: r.update(status="pass"),
            lambda r: r["identities"].update(production_sha256="0" * 64),
            lambda r: r["identities"].update(feature_report_sha256="0" * 64),
            lambda r: r["tuples"][1].__setitem__(1, 50),
            lambda r: r["claim_boundary"].update(not_proven=[]),
        )
        for index, mutate in enumerate(mutations):
            candidate = copy.deepcopy(self.report)
            mutate(candidate)
            with self.subTest(index=index):
                self.assertFalse(self.module.validate_report(candidate))

    def test_positive_recanonicalized_tampering_fails_closed(self) -> None:
        mutations = (
            lambda r: r["positives"][0].update(input_active_sha256="0" * 64),
            lambda r: r["positives"][2].update(input_output_rowbytes=269),
            lambda r: r["positives"][4]["callbacks"].update(input_checkin=0),
            lambda r: r["positives"][0].update(raw_exact=False),
        )
        for index, mutate in enumerate(mutations):
            candidate = copy.deepcopy(self.report)
            mutate(candidate)
            candidate["positive_digest"] = self.module.canonical_sha(candidate["positives"])
            with self.subTest(index=index):
                self.assertFalse(self.module.validate_report(candidate))

    def test_negative_recanonicalized_tampering_fails_closed(self) -> None:
        candidates = []
        removed = copy.deepcopy(self.report)
        removed["negatives"].pop()
        candidates.append(removed)

        swapped = copy.deepcopy(self.report)
        swapped["negatives"][0]["name"], swapped["negatives"][1]["name"] = (
            swapped["negatives"][1]["name"], swapped["negatives"][0]["name"]
        )
        candidates.append(swapped)

        error = copy.deepcopy(self.report)
        error["negatives"][7]["error"] = 0
        candidates.append(error)

        lifecycle = copy.deepcopy(self.report)
        lifecycle["negatives"][20]["callbacks"]["param_checkin"] = 20
        candidates.append(lifecycle)

        extra = copy.deepcopy(self.report)
        extra["negatives"][30]["extra"] = True
        candidates.append(extra)

        for index, candidate in enumerate(candidates):
            candidate["negative_digest"] = self.module.canonical_sha(candidate["negatives"])
            with self.subTest(index=index):
                self.assertFalse(self.module.validate_report(candidate))


if __name__ == "__main__":
    unittest.main()
