from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olm_actual_aex_native_ucrt_table_replay_readiness_20260814.py"
REPORT = ROOT / "refs/conformance/olm_actual_aex_native_ucrt_table_replay_readiness_20260814.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("olm_actual_aex_ucrt_replay", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ActualAexNativeUcrtTableReplayReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_tool()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_default_is_live_read_only_valid(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(TOOL)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("READY_NATIVE_TABLE_REPLAY_HOST_SUBSTITUTE_DUAL_OWNER_PLUMBING_PROVEN", run.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_build_and_boundary_are_exact(self) -> None:
        self.assertTrue(self.module.validate(self.report))
        self.assertTrue(self.report["build"]["cargo_check_passed"])
        self.assertTrue(self.report["table_contract"]["missing_key_fails_closed"])
        self.assertFalse(self.report["table_contract"]["host_math_fallback_when_table_present"])
        self.assertEqual(self.report["next_exact_proof"]["directional_exported_cells"], 6)
        self.assertEqual(self.report["next_exact_proof"]["distance_exported_cells"], 8)
        self.assertEqual(self.report["next_exact_proof"]["host_substitute_same_table_directional_proven"], 6)
        self.assertEqual(self.report["next_exact_proof"]["host_substitute_same_table_distance_proven"], 8)

    def test_scope_escalation_and_recanonicalization_rejected(self) -> None:
        for mutate in (
            lambda value: value.update(extra=True),
            lambda value: value["scope"].update(actual_aex_replay_executed=True),
            lambda value: value["table_contract"].update(host_math_fallback_when_table_present=True),
            lambda value: value["next_exact_proof"].update(distance_exported_cells=7),
            lambda value: value["build"].update(patched_callbacks_sha256="0" * 64),
        ):
            changed = copy.deepcopy(self.report)
            mutate(changed)
            self.assertFalse(self.module.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()
