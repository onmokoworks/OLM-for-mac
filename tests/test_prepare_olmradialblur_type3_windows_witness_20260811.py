from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/prepare_olmradialblur_type3_windows_witness_20260811.py"


def load_module():
    spec = importlib.util.spec_from_file_location("radial_type3_witness", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialType3WitnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temp = tempfile.TemporaryDirectory(prefix="radial-type3-witness-")
        self.root = Path(self.temp.name)
        self.module.prepare(self.root)
        self.request_path = self.root / "request.json"
        self.request = json.loads(self.request_path.read_text())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def rows(self, *, pilot: bool) -> list[dict]:
        selected = self.module.pilot_case_ids(self.request) if pilot else {
            case["case_id"] for case in self.request["cases"]
        }
        rows = []
        for case in self.request["cases"]:
            if case["case_id"] not in selected:
                continue
            layer = Path(case["noise_layer"]).stem
            for repeat in case["repeats"]:
                output = Path("exports") / f"{case['case_id']}.r{repeat}.exr"
                path = self.root / output
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(case["case_id"].encode())
                rows.append({
                    "case_id": case["case_id"], "repeat": repeat,
                    "ae_pid": repeat, "ae_version": "26.3", "ae_build": "1",
                    "project_bpc": case["project_bpc"], "renderer": "Software",
                    "aex_sha256": self.request["aex_sha256"],
                    "source_sha256": self.request["primary_source"]["sha256"],
                    "noise_layer_sha256": self.request["layers"][layer]["sha256"],
                    "output_path": str(output),
                    "output_sha256": self.module.sha256(path.read_bytes()),
                })
        return rows

    def write_return(self, rows: list[dict]) -> Path:
        path = self.root / "return.json"
        path.write_text(json.dumps({"schema": self.module.RETURN_SCHEMA, "renders": rows}))
        return path

    def test_schema2_has_fixed_source_and_24_public_cases(self) -> None:
        self.assertEqual(self.request["schema"], self.module.REQUEST_SCHEMA)
        self.assertEqual(len(self.request["cases"]), 24)
        self.assertEqual(sum(len(case["repeats"]) for case in self.request["cases"]), 48)
        self.assertEqual(self.request["fixed_hidden_parameters"]["Thickness"], 3)
        self.assertTrue((self.root / self.request["primary_source"]["path"]).is_file())
        self.assertNotEqual(self.request["primary_source"]["sha256"],
                            self.request["layers"]["pattern"]["sha256"])
        self.assertNotEqual(self.request["primary_source"]["sha256"],
                            self.request["layers"]["inverse"]["sha256"])
        self.assertTrue(all(case["parameters"]["Thickness"] == 3 for case in self.request["cases"]))

    def test_pilot_is_exactly_eight_renders_and_validates(self) -> None:
        rows = self.rows(pilot=True)
        self.assertEqual(len(rows), 8)
        self.module.validate(self.request_path, self.write_return(rows), pilot=True)

    def test_validation_fails_closed_on_missing_build_and_wrong_source(self) -> None:
        rows = self.rows(pilot=True)
        rows[0]["ae_build"] = ""
        with self.assertRaisesRegex(SystemExit, "missing AE build"):
            self.module.validate(self.request_path, self.write_return(rows), pilot=True)
        rows[0]["ae_build"] = "1"
        rows[0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(SystemExit, "identity mismatch"):
            self.module.validate(self.request_path, self.write_return(rows), pilot=True)

    def test_full_validator_rejects_pilot_return(self) -> None:
        with self.assertRaisesRegex(SystemExit, "expected 48, got 8"):
            self.module.validate(self.request_path, self.write_return(self.rows(pilot=True)))


if __name__ == "__main__":
    unittest.main()
