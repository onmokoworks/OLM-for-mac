from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts/analyze_olmradialblur_strength290_ucrt_math_return_20260814.py"


def load_module():
    spec = importlib.util.spec_from_file_location("radial_strength290_return", ANALYZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialStrength290UcrtReturnTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def build_valid_return(self, root: Path) -> Path:
        target = root / self.module.REQUEST_ID
        target.mkdir(parents=True)
        manifest_bytes = (self.module.PACKAGE / "request_manifest.json").read_bytes()
        vectors_bytes = (self.module.PACKAGE / "math_vectors.json").read_bytes()
        vectors = json.loads(vectors_bytes)
        rows = []
        for vector in vectors:
            if vector["function"] == "log2f":
                result = math.log2(struct.unpack("<f", int(vector["argument_bits"], 16).to_bytes(4, "little"))[0])
            else:
                left = struct.unpack("<f", int(vector["left_bits"], 16).to_bytes(4, "little"))[0]
                right = struct.unpack("<f", int(vector["right_bits"], 16).to_bytes(4, "little"))[0]
                result = math.atan2(left, right)
            result_bits = struct.unpack("<I", struct.pack("<f", result))[0]
            rows.append({**vector, "native_ucrt_result_bits": f"0x{result_bits:08x}"})
        summary = {
            "schema": "olmradialblur.strength290-ucrt-math-return/1",
            "request_id": self.module.REQUEST_ID,
            "status": "answered_native_windows_ucrt_atan2f_log2f",
            "process_bitness": 64,
            "processor_architecture": "AMD64",
            "ucrtbase": {
                "requested_path": r"C:\Windows\System32\ucrtbase.dll",
                "loaded_path": r"C:\Windows\System32\ucrtbase.dll",
                "file_version": "10.0.test",
                "product_version": "10.0.test",
                "sha256": "1" * 64,
            },
            "vector_count": 577,
            "original_call_count": 725,
            "vectors_sha256": hashlib.sha256(vectors_bytes).hexdigest(),
            "rows": rows,
        }
        (target / "request_manifest.json").write_bytes(manifest_bytes)
        (target / "math_vectors.json").write_bytes(vectors_bytes)
        (target / "run_summary.json").write_bytes(self.module.canonical(summary))
        return target

    def mutate(self, root: Path, mutator) -> None:
        path = root / "run_summary.json"
        value = json.loads(path.read_bytes())
        mutator(value)
        path.write_bytes(self.module.canonical(value))

    def assert_rejected(self, mutator) -> None:
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate(root, mutator)
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_valid_synthetic_return_is_accepted_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            report = self.module.analyze(self.build_valid_return(Path(temp)))
        self.assertEqual(report["status"], "PASS_NATIVE_WINDOWS_UCRT_RADIAL_577_RETURN_VALIDATED_NO_PROMOTION")
        self.assertIn("fail-closed", report["production_policy"])

    def test_missing_extra_and_duplicate_rows_are_rejected(self) -> None:
        self.assert_rejected(lambda value: value["rows"].pop())
        self.assert_rejected(lambda value: value["rows"].append(dict(value["rows"][-1])))
        self.assert_rejected(lambda value: value["rows"].__setitem__(4, dict(value["rows"][3])))

    def test_stale_request_id_and_schema_are_rejected(self) -> None:
        self.assert_rejected(lambda value: value.update({"request_id": self.module.REQUEST_ID + "_stale"}))
        self.assert_rejected(lambda value: value.update({"schema": "olmradialblur.strength290-ucrt-math-return/0"}))

    def test_wrong_ucrt_path_or_hash_is_rejected(self) -> None:
        self.assert_rejected(lambda value: value["ucrtbase"].update({"loaded_path": r"C:\Temp\ucrtbase.dll"}))
        self.assert_rejected(lambda value: value["ucrtbase"].update({"sha256": "not-a-sha"}))

    def test_identity_architecture_and_input_drift_are_rejected(self) -> None:
        self.assert_rejected(lambda value: value.update({"processor_architecture": "ARM64"}))
        self.assert_rejected(lambda value: value["rows"][1].update({"left_bits": "0x00000001"}))

    def test_extra_member_and_manifest_drift_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            (root / "extra.txt").write_text("not evidence\n")
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            manifest = root / "request_manifest.json"
            manifest.write_bytes(manifest.read_bytes() + b"\n")
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_flat_zip_is_accepted_and_wrapped_zip_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            folder = self.build_valid_return(Path(temp))
            archive_path = Path(temp) / "return.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for item in folder.iterdir():
                    archive.write(item, item.name)
            report = self.module.analyze(archive_path)
            self.assertEqual(report["vectors"]["unique"], 577)
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            folder = self.build_valid_return(Path(temp))
            archive_path = Path(temp) / "wrapped.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for item in folder.iterdir():
                    archive.write(item, f"{self.module.REQUEST_ID}/{item.name}")
            with self.assertRaises(ValueError):
                self.module.analyze(archive_path)

    def test_duplicate_json_key_and_case_collision_zip_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            folder = self.build_valid_return(Path(temp))
            summary = folder / "run_summary.json"
            raw = summary.read_text()
            summary.write_text(raw.replace('{\n  "original_call_count"',
                                           '{\n  "request_id": "duplicate",\n  "original_call_count"', 1))
            with self.assertRaises(ValueError):
                self.module.analyze(folder)
        with tempfile.TemporaryDirectory(prefix="radial-ucrt-return-") as temp:
            folder = self.build_valid_return(Path(temp))
            archive_path = Path(temp) / "collision.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for item in folder.iterdir():
                    archive.write(item, item.name)
                archive.writestr("RUN_SUMMARY.JSON", b"collision")
            with self.assertRaises(ValueError):
                self.module.analyze(archive_path)


if __name__ == "__main__":
    unittest.main()
