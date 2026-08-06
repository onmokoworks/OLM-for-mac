#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "refs/reference_requests/olm_crosshost_linear_input_20260806.zip"
FIXTURE = ROOT / "refs/fixtures/olm_crosshost_linear/opaque_cells_linear_float32.exr"
MANIFEST = ROOT / "refs/fixtures/olm_crosshost_linear/manifest.json"


class CrossHostLinearInputTests(unittest.TestCase):
    def test_fixture_and_package_are_hash_bound_and_minimal(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), manifest["output_sha256"])
        self.assertEqual((manifest["width"], manifest["height"]), (1920, 1080))
        self.assertEqual((manifest["sample_type"], manifest["compression"]), ("FLOAT32", "none"))
        with zipfile.ZipFile(PACKAGE) as archive:
            contract = json.loads(archive.read("BATCH_CONTRACT.json"))
            jsx = archive.read("scripts/ae_render_olm_crosshost_linear_input_20260806.jsx").decode()
            ps = archive.read("scripts/run_olm_crosshost_linear_input_20260806.ps1").decode()
            self.assertEqual(len(contract["acquire"]), 6)
            self.assertEqual({row["plugin"] for row in contract["acquire"]}, {"ColorKeep", "OLMKiraKira"})
            self.assertEqual({row["depth"] for row in contract["acquire"]}, {8, 16, 32})
            self.assertTrue(all(row["source_sha256"] == manifest["output_sha256"] for row in contract["acquire"]))
            self.assertIn('preserveRGBAvailable=(typeof footage[0].mainSource.preserveRGB!=="undefined")', jsx)
            self.assertIn('color_profile_name:String(footage[0].mainSource.colorProfileName)', jsx)
            self.assertIn('source_extension!==".exr"', jsx)
            self.assertIn("@($contract.acquire).Count -ne 6", ps)

    def test_existing_png_return_cannot_satisfy_new_rows(self) -> None:
        old = ROOT / "refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/verify_olm_crosshost_linear_input_20260806.py"), str(old), str(old), str(PACKAGE)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected one outputs/", result.stdout)


if __name__ == "__main__":
    unittest.main()
