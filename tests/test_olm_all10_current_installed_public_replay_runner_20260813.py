from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_current_installed_public_replays_20260813.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("all10_installed_replays", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class All10CurrentInstalledPublicReplayRunnerTest(unittest.TestCase):
    def test_exact_ten_unique_existing_generators(self) -> None:
        runner = load_runner()
        self.assertEqual(len(runner.COMMANDS), 10)
        self.assertEqual(len({name for name, _ in runner.COMMANDS}), 10)
        self.assertEqual(len({path for _, path in runner.COMMANDS}), 10)
        self.assertTrue(all((ROOT / path).is_file() for _, path in runner.COMMANDS))

    def test_runner_is_ae_free_by_construction(self) -> None:
        text = RUNNER.read_text()
        self.assertNotIn("open -a", text)
        self.assertNotIn("DoScript", text)
        self.assertNotIn("osascript", text)
        self.assertIn("ae_processes()", text)
        self.assertIn("run_olm_all10_installed_public_routes_20260813.py", text)


if __name__ == "__main__":
    unittest.main()
