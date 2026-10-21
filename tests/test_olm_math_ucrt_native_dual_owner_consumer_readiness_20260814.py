from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "tools/emulation/run_olm_math_ucrt_native_dual_owner_replay_20260814.py"
TOOL = ROOT / "tools/emulation/test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.py"
REPORT = ROOT / "refs/conformance/olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")
EXPECTED = {
    CONSUMER: "af09ca96130d88272ea901e5ef86fbbc195ff08c1d060ab909bdf000c0b8ffc3",
    TOOL: "a00f3f13e91876b74d98bf557ea122a5df70721bbe856ef5f9dbfda1ce258fa3",
    REPORT: "7f2e525ab3d47adacaf86bebd378143249dafa6938aae0ceb147b25c72cbdef2",
    MARKDOWN: "b071c5f655d037b8ecbe67a24d67b2b87852ac5a3432e7e2c7db18bdce3e0a42",
}


def load_tool():
    spec = importlib.util.spec_from_file_location("olm_native_consumer_readiness_unit", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeDualOwnerConsumerReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_tool()
        cls.value = json.loads(REPORT.read_text())

    def reject(self, mutate, *, recanonicalize: str | None = None) -> None:
        value = copy.deepcopy(self.value)
        mutate(value)
        if recanonicalize:
            value["consumer"][recanonicalize + "_rows_sha256"] = hashlib.sha256(
                json.dumps(value["consumer"][recanonicalize + "_rows"], sort_keys=True,
                           separators=(",", ":")).encode()).hexdigest()
        self.assertFalse(self.tool.validate(value))

    def test_live_report_and_markdown(self) -> None:
        self.assertTrue(self.tool.validate(self.value))
        self.assertEqual(MARKDOWN.read_text(), self.tool.markdown(self.value))

    def test_external_pins(self) -> None:
        for path, expected in EXPECTED.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, path)

    def test_consumer_requires_return_path(self) -> None:
        run = subprocess.run([sys.executable, str(CONSUMER)], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(run.returncode, 0)

    def test_unknown_top_level_rejected(self) -> None:
        self.reject(lambda value: value.__setitem__("extra", True))

    def test_synthetic_native_overclaim_rejected(self) -> None:
        self.reject(lambda value: value["synthetic_return"].__setitem__(
            "explicitly_not_native_windows_evidence", False))

    def test_worker_identity_rejected(self) -> None:
        self.reject(lambda value: value["consumer"]["worker_build"].__setitem__(
            "worker_sha256", "0" * 64))

    def test_directional_math_call_census_rejected(self) -> None:
        self.reject(lambda value: value["consumer"]["directional_mac_table_calls"].__setitem__(
            "pow", 47513))

    def test_table_identity_rejected(self) -> None:
        self.reject(lambda value: value["consumer"]["table"].__setitem__("sha256", "0" * 64))

    def test_directional_paired_recanonicalization_rejected(self) -> None:
        def mutate(value):
            row = value["consumer"]["directional_rows"][0]
            row["aex_raw_sha256"] = row["mac_production_direct_raw_sha256"] = "1" * 64
        self.reject(mutate, recanonicalize="directional")

    def test_distance_paired_recanonicalization_rejected(self) -> None:
        def mutate(value):
            row = value["consumer"]["distance_rows"][0]
            row["aex_raw_sha256"] = row["mac_renderbits_raw_sha256"] = "1" * 64
        self.reject(mutate, recanonicalize="distance")

    def test_scope_overclaim_rejected(self) -> None:
        self.reject(lambda value: value["scope"].__setitem__("native_windows_result_claimed", True))

    def test_public_promotion_overclaim_rejected(self) -> None:
        self.reject(lambda value: value["consumer"]["decision"].__setitem__(
            "directional_public_effectmain_closure_still_required", False))


if __name__ == "__main__":
    unittest.main()
