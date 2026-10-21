#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("olm_fixed_fixture_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class UCRTFixedFixtureRunnerIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        module = load_runner()
        cls.lanes = {lane.name: lane.commands for lane in module.LANES}

    def assert_command_once(self, lane: str, suffix: tuple[str, ...]) -> None:
        matches = [command for command in self.lanes[lane] if command[1:] == suffix]
        self.assertEqual(len(matches), 1, suffix)
        self.assertTrue(matches[0][0].endswith("python") or "python" in matches[0][0], matches[0])

    def test_directional_same_table_gate_is_official(self) -> None:
        self.assert_command_once(
            "directionalblur",
            ("tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py",),
        )
        self.assert_command_once(
            "directionalblur",
            ("-m", "unittest", "tests.test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814"),
        )
        self.assert_command_once(
            "directionalblur",
            ("tools/emulation/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py",),
        )
        self.assert_command_once(
            "directionalblur",
            ("-m", "unittest", "tests.test_olmdirectionalblur_current_installed_complete_bounded_union_20260814"),
        )

    def test_distance_and_cross_plugin_readiness_gates_are_official(self) -> None:
        expected = (
            ("tools/emulation/test_olm_math_ucrt_batch_request_20260814.py",),
            ("-m", "unittest", "tests.test_olm_math_ucrt_batch_request_20260814"),
            ("tools/emulation/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py",),
            ("-m", "unittest", "tests.test_olmdistancegradation_same_table_dual_owner_plumbing_20260814"),
            ("tools/emulation/test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.py",),
            ("-m", "unittest", "tests.test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814"),
            ("tools/emulation/test_olm_native_ucrt_promotion_table_readiness_20260814.py",),
            ("-m", "unittest", "tests.test_olm_native_ucrt_promotion_table_readiness_20260814"),
        )
        for suffix in expected:
            self.assert_command_once("distancegradation", suffix)

    def test_radial_strength290_host_math_boundary_is_official(self) -> None:
        self.assert_command_once(
            "radialblur",
            ("tools/emulation/test_olmradialblur_strength290_exported_math_boundary_20260814.py", "--validate-only"),
        )
        self.assert_command_once(
            "radialblur",
            ("-m", "unittest", "tests.test_olmradialblur_strength290_exported_math_boundary_20260814"),
        )
        self.assert_command_once(
            "radialblur",
            ("tools/emulation/test_olmradialblur_strength290_ucrt_math_request_20260814.py", "--validate-only"),
        )
        self.assert_command_once(
            "radialblur",
            ("-m", "unittest", "tests.test_olmradialblur_strength290_ucrt_math_request_20260814"),
        )

    def test_official_gates_do_not_invoke_native_capture_or_ae(self) -> None:
        commands = "\n".join(" ".join(command) for lane in self.lanes.values() for command in lane)
        self.assertNotIn("run_olm_math_ucrt_native_dual_owner_replay_20260814.py", commands)
        self.assertNotIn("olm_math_ucrt_batch_capture.ps1", commands)
        self.assertNotIn("test_olmdistancegradation_pf32_power_ucrt_request_20260813.py", commands)
        self.assertNotIn("olmdirectionalblur_expffloat_arm15_universal_candidate_20260814/test_build_identity.py", commands)
        self.assertNotIn("After Effects", commands)
        self.assertNotIn("aerender", commands)

    def test_colorkeep_uses_current_complete_union_not_pre_union_count9(self) -> None:
        self.assert_command_once(
            "colorkeep",
            ("tools/emulation/test_colorkeep_current_installed_complete_union_20260814.py",),
        )
        self.assert_command_once(
            "colorkeep",
            ("-m", "unittest", "tests.test_colorkeep_current_installed_complete_union_20260814"),
        )
        commands = "\n".join(" ".join(command) for command in self.lanes["colorkeep"])
        self.assertNotIn("test_colorkeep_current_installed_count9_20260813", commands)

    def test_smoother_v1_uses_complete_installed_union(self) -> None:
        self.assert_command_once(
            "smoother",
            ("tools/emulation/test_olmsmoother_v1_current_installed_admission_union_20260813.py",),
        )
        self.assert_command_once(
            "smoother",
            ("-m", "unittest", "tests.test_olmsmoother_v1_current_installed_admission_union_20260813"),
        )
        commands = "\n".join(" ".join(command) for command in self.lanes["smoother"])
        self.assertNotIn("test_olmsmoother_v1_current_installed_public_20260813", commands)


if __name__ == "__main__":
    unittest.main()
