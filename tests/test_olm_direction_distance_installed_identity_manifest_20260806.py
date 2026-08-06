#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.emulation import olm_installed_identity


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstalledIdentityManifestTests(unittest.TestCase):
    def test_directionalblur_rejects_manifest_without_unique_attested_row(self) -> None:
        module = load(
            "dblur_identity",
            ROOT / "tools/emulation/test_olmdirectionalblur_installed_completion_route_20260805.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "identity.json"
            bad.write_text(json.dumps({"schema": "olm.installed-identity-manifest/1", "plugins": []}))
            original = olm_installed_identity.MANIFEST
            olm_installed_identity.MANIFEST = bad
            try:
                with self.assertRaisesRegex(RuntimeError, "exactly one OLMDirectionalBlur row"):
                    olm_installed_identity.accepted_plugin("OLMDirectionalBlur")
            finally:
                olm_installed_identity.MANIFEST = original

    def test_distancegradation_rejects_unattested_manifest_row(self) -> None:
        module = load(
            "distance_identity",
            ROOT / "tools/emulation/test_olmdistancegradation_installed_identity_20260806.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "identity.json"
            bad.write_text(json.dumps({
                "schema": "olm.installed-identity-manifest/1",
                "plugins": [{
                    "plugin": "OLMDistanceGradation",
                    "installed_bundle": str(module.INSTALLED),
                    "sha256": "0" * 64,
                    "source_installed_exact": False,
                    "universal_exact": True,
                    "codesign_exact": True,
                    "installed_bundle_count": 1,
                }],
            }))
            original = olm_installed_identity.MANIFEST
            olm_installed_identity.MANIFEST = bad
            try:
                with self.assertRaisesRegex(RuntimeError, "source_installed_exact is not true"):
                    module.main()
            finally:
                olm_installed_identity.MANIFEST = original


if __name__ == "__main__":
    unittest.main()
