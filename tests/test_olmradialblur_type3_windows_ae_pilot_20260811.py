from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "scripts/olmradialblur_type3_pf32_pilot_contract_20260811.py"
PACKAGER = ROOT / "scripts/package_olmradialblur_type3_windows_ae_pilot_20260811.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class Type3PilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load(CONTRACT, "type3_contract")
        cls.packager = load(PACKAGER, "type3_packager")

    def package(self, root: Path) -> tuple[Path, dict]:
        archive = root / "pilot.zip"
        package = root / "package"
        self.packager.build(archive)
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(package)
        return package, json.loads((package / "BATCH_CONTRACT.json").read_text())

    def populate_return(self, package: Path, request: dict, target: Path,
                        *, legacy: bool = False) -> None:
        for index, row in enumerate(request["rows"]):
            directory = target / "outputs" / row["row_id"]
            directory.mkdir(parents=True)
            raw = (row["case_id"] + " exr").encode()
            (directory / "effect_on.exr").write_bytes(raw)
            params = [{"match_name": key, "value": value}
                      for key, value in row["parameters"].items()]
            attestation = {
                "row_id": row["row_id"], "case_id": row["case_id"],
                "repeat": row["repeat"],
                "execution_row_sha256": row["execution_row_sha256"],
                "witness_request_sha256": request["witness_request_sha256"],
                "ae_version": "25.2x131", "ae_pid": 100 + index,
                "renderer": "Software", "depth": 32,
                "aex_sha256": self.contract.AEX_SHA256,
                "source_sha256": request["fixtures"][row["source_member"]]["sha256"],
                "noise_layer_sha256": request["fixtures"][row["noise_layer_member"]]["sha256"],
                "noise_layer_written": 2, "noise_layer_readback": 2,
                "noise_layer_source_name": row["noise_layer_expected_source_name"],
                "parameters_before": params, "parameters_after": params,
                "output_template": "OLM EXR 32 Float", "output_settings": {},
                "output_member": f"outputs/{row['row_id']}/effect_on.exr",
                "output_sha256": self.contract.digest(raw),
            }
            if legacy:
                attestation.pop("witness_request_sha256")
            (directory / "attestation.json").write_text(json.dumps(attestation))

    def test_pilot_is_exact_witness_v2_subset(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            package, request = self.package(Path(raw))
            witness = json.loads((package / "WITNESS_REQUEST.json").read_text())
            self.assertEqual(request["schema"], self.contract.PILOT_SCHEMA)
            self.assertEqual(request["parent_witness_schema"], self.contract.REQUEST_SCHEMA)
            self.assertEqual(request["return_schema"], self.contract.RETURN_SCHEMA)
            self.assertEqual(request["rows"], self.contract.pilot_cases(witness))
            self.assertEqual(len(request["rows"]), 8)
            self.assertEqual({row["case_id"] for row in request["rows"]}, {
                "pf32_zoom_nv25_pattern", "pf32_zoom_nv25_inverse",
                "pf32_rotation_nv25_pattern", "pf32_rotation_nv25_inverse"})
            for row in request["rows"]:
                self.assertEqual(row["parameters"]["OLM RadialBlur-0002"], [4, 3])
                self.assertIs(row["parameters"]["OLM RadialBlur-0026"], True)
                self.assertEqual(row["parameters"]["OLM RadialBlur-0024"], 3)
                self.assertNotIn("OLM RadialBlur-0022", row["parameters"])
                self.assertEqual(row["source_member"], "input/source.png")

    def test_package_is_deterministic_and_self_validating(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); first = root / "a.zip"; second = root / "b.zip"
            self.packager.build(first); self.packager.build(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as zipped:
                names = set(zipped.namelist())
            self.assertIn("WITNESS_REQUEST.json", names)
            self.assertIn("input/source.png", names)
            self.assertIn("layers/pattern.png", names)
            self.assertIn("layers/inverse.png", names)

    def test_validator_accepts_v2_return_and_rejects_legacy_return(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); package, request = self.package(root)
            returned = root / "return"; self.populate_return(package, request, returned)
            self.assertEqual(self.contract.validate_return(package, returned)["rows"], 8)
            legacy = root / "legacy"; self.populate_return(package, request, legacy, legacy=True)
            with self.assertRaisesRegex(ValueError, "witness request mismatch"):
                self.contract.validate_return(package, legacy)

    def test_validator_rejects_embedded_witness_or_parameter_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); package, request = self.package(root)
            witness_path = package / "WITNESS_REQUEST.json"
            witness = json.loads(witness_path.read_text())
            witness["cases"][16]["parameters"]["Center"] = [4.5, 3.5]
            witness_path.write_text(json.dumps(witness))
            with self.assertRaisesRegex(ValueError, "embedded witness request hash mismatch"):
                self.contract.validate_embedded_witness(package, request)

    def test_extracted_verifier_and_layer_fail_close(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); package, request = self.package(root)
            returned = root / "return"; self.populate_return(package, request, returned)
            run = subprocess.run([sys.executable, str(package / "VERIFY_RETURN.py"), str(returned)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('"rows": 8', run.stdout)
        jsx = (ROOT / "scripts/ae_render_olmradialblur_type3_windows_ae_pilot_20260811.jsx").read_text()
        self.assertIn("NOISE_LAYER_BINDING_UNAVAILABLE", jsx)
        self.assertIn("lp.setValue(written)", jsx)
        self.assertIn("Number(lp.value)!==written", jsx)


if __name__ == "__main__":
    unittest.main()
