import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/olm_roi_tile_property_harness.cpp"
HEADER = ROOT / "tests/support/olm_roi_tile_property.hpp"


class RoiTilePropertyTests(unittest.TestCase):
    def test_contract_is_explicit(self):
        text = HEADER.read_text(encoding="utf-8")
        for token in ("origin_x", "origin_y", "rowbytes", "extract_with_halo",
                      "padding_is", "compose", "insufficient halo"):
            self.assertIn(token, text)

    def test_cpp_property_harness(self):
        compiler = shutil.which("clang++") or shutil.which("g++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="olm-roi-property-") as tmp:
            binary = Path(tmp) / "roi_property"
            built = subprocess.run(
                [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra",
                 "-Werror", str(SOURCE), "-o", str(binary)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            run = subprocess.run([str(binary)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS tiles=9", run.stdout)


if __name__ == "__main__":
    unittest.main()
