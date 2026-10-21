from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_remaining6_ucrt_powf_request_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_powf_request_20260814.json"


def load_module():
    spec = importlib.util.spec_from_file_location("directional_powf_request", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalPowfRequestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_live_request_is_exact_and_ae_free(self) -> None:
        self.assertEqual(self.module.build_report(), self.report)
        self.assertEqual(self.report["vectors"]["count"], 787)
        script = (self.module.PACKAGE / "run_olmdirectionalblur_remaining6_ucrt_powf.ps1").read_text().lower()
        for forbidden in ("afterfx", "aerender", "doscript", "start-process"):
            self.assertNotIn(forbidden, script)

    def test_vector_and_manifest_tamper_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="directional-powf-request-") as raw:
            original = self.module.PACKAGE
            copy = Path(raw) / "package"
            shutil.copytree(original, copy)
            vectors = copy / "powf_vectors.json"
            value = json.loads(vectors.read_text())
            value[0]["input_bits"] = "0x00000001"
            vectors.write_text(json.dumps(value, indent=2) + "\n")
            saved = self.module.PACKAGE
            self.module.PACKAGE = copy
            try:
                with self.assertRaises(RuntimeError):
                    self.module.validate_package()
            finally:
                self.module.PACKAGE = saved


if __name__ == "__main__":
    unittest.main()
