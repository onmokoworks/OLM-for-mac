import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "tools/perf/run_olmkirakira_generic_production_perf.py"
SMOKE = ROOT / "tools/perf/run_generic_beta_smoke.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KiraKiraGenericPerfRunnerTests(unittest.TestCase):
    def test_driver_covers_four_modes_and_three_depths(self) -> None:
        module = load(DRIVER, "kira_perf")
        self.assertEqual(set(module.GEOMETRIES), {"hd", "uhd"})
        self.assertEqual(
            set(module.MODES),
            {"box", "approximated_gaussian", "gaussian", "exponential"},
        )
        source = DRIVER.read_text(encoding="utf-8")
        self.assertIn("for depth in (8, 16, 32)", source)
        self.assertIn('"/usr/bin/time", "-lp"', source)
        self.assertIn('"peak_rss_bytes"', source)

    def test_smoke_catalog_routes_hd_and_uhd_to_kira_driver(self) -> None:
        module = load(SMOKE, "generic_smoke")
        for geometry in ("hd", "uhd"):
            command = module.COMMANDS[("OLMKiraKira", geometry)]
            self.assertEqual(command[1], "tools/perf/run_olmkirakira_generic_production_perf.py")
            self.assertEqual(command[command.index("--geometry") + 1], geometry)
        self.assertIn("mode_geometry_admitted", module.SUPPORT_PREDICATES["OLMKiraKira"])


if __name__ == "__main__":
    unittest.main()
