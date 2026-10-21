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
ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
PACKAGES = ROOT / "refs/runtime_trace_packages"


def load_module():
    spec = importlib.util.spec_from_file_location("olm_math_ucrt_return", ANALYZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OLMUcrtMathBatchReturnTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def build_valid_return(self, root: Path) -> Path:
        batch = root / self.module.BATCH_ID
        directional_dir = batch / "directional"
        directional_powf_dir = batch / "directional_powf"
        distance_dir = batch / "distance"
        directional_dir.mkdir(parents=True)
        directional_powf_dir.mkdir(parents=True)
        distance_dir.mkdir(parents=True)
        ucrt = {
            "path": r"C:\Windows\System32\ucrtbase.dll",
            "file_version": "10.0.test",
            "product_version": "10.0.test",
            "sha256": "1" * 64,
        }

        directional_package = PACKAGES / self.module.DIRECTIONAL_ID
        directional_vectors_bytes = (directional_package / "expf_vectors.json").read_bytes()
        directional_vectors = json.loads(directional_vectors_bytes)
        directional_rows = []
        for vector in directional_vectors:
            argument = struct.unpack("<f", int(vector["argument_bits"], 16).to_bytes(4, "little"))[0]
            result_bits = struct.unpack("<I", struct.pack("<f", math.exp(argument)))[0]
            directional_rows.append({
                **vector,
                "native_ucrt_result_bits": f"0x{result_bits:08x}",
                "ucrtbase_path": ucrt["path"],
                "ucrtbase_file_version": ucrt["file_version"],
                "ucrtbase_product_version": ucrt["product_version"],
                "ucrtbase_sha256": ucrt["sha256"],
            })
        directional = {
            "schema": "olmdirectionalblur.remaining6-ucrt-expf-return/1",
            "request_id": self.module.DIRECTIONAL_ID,
            "status": "answered_native_windows_ucrt_expf",
            "process_bitness": 64,
            "processor_architecture": "AMD64",
            "ucrtbase": ucrt,
            "counts": [8, 50, 96, 100, 240],
            "vector_count": 494,
            "vectors_sha256": hashlib.sha256(directional_vectors_bytes).hexdigest(),
            "rows": directional_rows,
        }
        directional_summary = self.module.canonical(directional)
        (directional_dir / "run_summary.json").write_bytes(directional_summary)
        (directional_dir / "request_manifest.json").write_bytes((directional_package / "request_manifest.json").read_bytes())
        (directional_dir / "expf_vectors.json").write_bytes(directional_vectors_bytes)

        directional_powf_package = PACKAGES / self.module.DIRECTIONAL_POWF_ID
        directional_powf_vectors_bytes = (directional_powf_package / "powf_vectors.json").read_bytes()
        directional_powf_vectors = json.loads(directional_powf_vectors_bytes)
        directional_powf_rows = []
        for vector in directional_powf_vectors:
            left = struct.unpack("<f", int(vector["input_bits"], 16).to_bytes(4, "little"))[0]
            right = struct.unpack("<f", int(vector["exponent_bits"], 16).to_bytes(4, "little"))[0]
            result_bits = struct.unpack("<I", struct.pack("<f", math.pow(left, right)))[0]
            directional_powf_rows.append({
                **vector,
                "native_ucrt_result_bits": f"0x{result_bits:08x}",
                "ucrtbase_path": ucrt["path"],
                "ucrtbase_file_version": ucrt["file_version"],
                "ucrtbase_product_version": ucrt["product_version"],
                "ucrtbase_sha256": ucrt["sha256"],
            })
        directional_powf = {
            "schema": "olmdirectionalblur.remaining6-ucrt-powf-return/1",
            "request_id": self.module.DIRECTIONAL_POWF_ID,
            "status": "answered_native_windows_ucrt_powf",
            "process_bitness": 64,
            "processor_architecture": "AMD64",
            "ucrtbase": ucrt,
            "vector_count": 787,
            "vectors_sha256": hashlib.sha256(directional_powf_vectors_bytes).hexdigest(),
            "rows": directional_powf_rows,
        }
        directional_powf_summary = self.module.canonical(directional_powf)
        (directional_powf_dir / "run_summary.json").write_bytes(directional_powf_summary)
        (directional_powf_dir / "request_manifest.json").write_bytes((directional_powf_package / "request_manifest.json").read_bytes())
        (directional_powf_dir / "powf_vectors.json").write_bytes(directional_powf_vectors_bytes)

        distance_package = PACKAGES / self.module.DISTANCE_ID
        distance_vectors_bytes = (distance_package / "powf_vectors.json").read_bytes()
        distance_vectors = json.loads(distance_vectors_bytes)
        distance_rows = []
        for vector in distance_vectors:
            distance_rows.append({
                "input_bits": vector["input_bits"],
                "exponent_bits": vector["exponent_bits"],
                "native_ucrt_result_bits": vector["host_result_bits"],
                "occurrences": vector["occurrences"],
                "ucrtbase_path": ucrt["path"],
                "ucrtbase_file_version": ucrt["file_version"],
                "ucrtbase_product_version": ucrt["product_version"],
                "ucrtbase_sha256": ucrt["sha256"],
            })
        distance = {
            "schema": "olmdistancegradation.pf32-power-ucrt-powf-return/1",
            "request_id": self.module.DISTANCE_ID,
            "status": "answered_native_windows_ucrt_powf",
            "process_bitness": 64,
            "processor_architecture": "AMD64",
            "ucrtbase": ucrt,
            "vector_count": 63,
            "vectors_sha256": hashlib.sha256(distance_vectors_bytes).hexdigest(),
            "rows": distance_rows,
        }
        distance_summary = self.module.canonical(distance)
        (distance_dir / "run_summary.json").write_bytes(distance_summary)
        (distance_dir / "request_manifest.json").write_bytes((distance_package / "request_manifest.json").read_bytes())
        (distance_dir / "powf_vectors.json").write_bytes(distance_vectors_bytes)

        batch_summary = {
            "schema": "olm.math-ucrt-batch-return/1",
            "request_id": self.module.BATCH_ID,
            "status": "answered_native_windows_ucrt_expf_powf",
            "process_bitness": 64,
            "processor_architecture": "AMD64",
            "ucrtbase": ucrt,
            "vectors": {"directional_expf": 494, "directional_powf": 787, "distance_powf": 63, "total": 1344},
            "children": {
                "directional": {
                    "request_id": self.module.DIRECTIONAL_ID,
                    "summary_sha256": hashlib.sha256(directional_summary).hexdigest(),
                },
                "directional_powf": {
                    "request_id": self.module.DIRECTIONAL_POWF_ID,
                    "summary_sha256": hashlib.sha256(directional_powf_summary).hexdigest(),
                },
                "distance": {
                    "request_id": self.module.DISTANCE_ID,
                    "summary_sha256": hashlib.sha256(distance_summary).hexdigest(),
                },
            },
        }
        (batch / "run_summary.json").write_bytes(self.module.canonical(batch_summary))
        (batch / "request_manifest.json").write_bytes((self.module.BATCH_PACKAGE / "request_manifest.json").read_bytes())
        return root

    def mutate_summary(self, root: Path, relative: str, mutator) -> None:
        path = root / self.module.BATCH_ID / relative
        value = json.loads(path.read_bytes())
        mutator(value)
        path.write_bytes(self.module.canonical(value))

    def test_valid_synthetic_return_is_accepted_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            path = self.build_valid_return(Path(temp))
            report = self.module.analyze(path)
        self.assertEqual(report["status"], "PASS_NATIVE_WINDOWS_UCRT_BATCH_RETURN_VALIDATED_NO_PROMOTION")
        self.assertEqual(report["vectors"]["total"], 1344)
        self.assertTrue(all(report["result_semantics"].values()))
        self.assertIn("fail_closed", report["production_policy"]["directional_six"])

    def test_real_windows_backslash_zip_members_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            batch = root / self.module.BATCH_ID
            returned = root / "windows-return.zip"
            with zipfile.ZipFile(returned, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for item in sorted(batch.rglob("*")):
                    if item.is_file():
                        relative = item.relative_to(batch).as_posix()
                        archive.write(item, relative.replace("/", "\\"))
            report = self.module.analyze(returned)
        self.assertEqual(report["status"],
                         "PASS_NATIVE_WINDOWS_UCRT_BATCH_RETURN_VALIDATED_NO_PROMOTION")

    def test_separator_normalization_collision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            returned = Path(temp) / "collision.zip"
            with zipfile.ZipFile(returned, "w") as archive:
                archive.writestr("directional/run_summary.json", b"{}")
                archive.writestr("directional\\run_summary.json", b"{}")
            with self.assertRaisesRegex(ValueError, "normalized duplicate"):
                self.module.load_members(returned)

    def test_cross_child_ucrt_identity_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "distance/run_summary.json",
                                lambda value: value["ucrtbase"].update({"sha256": "2" * 64}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_directional_argument_or_order_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional/run_summary.json",
                                lambda value: value["rows"].__setitem__(1, dict(value["rows"][0])))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_distance_input_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "distance/run_summary.json",
                                lambda value: value["rows"][0].update({"input_bits": "0x7fc00000"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_directional_powf_input_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional_powf/run_summary.json",
                                lambda value: value["rows"][2].update({"input_bits": "0x7fc00000"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_manifest_extra_member_and_parent_hash_tamper_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            (root / self.module.BATCH_ID / "extra.txt").write_text("not evidence\n")
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "run_summary.json",
                                lambda value: value["children"]["directional"].update({"summary_sha256": "0" * 64}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_row_unknown_key_and_result_shape_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional/run_summary.json",
                                lambda value: value["rows"][4].update({"unexpected": True}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_semantically_impossible_math_returns_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional/run_summary.json",
                                lambda value: value["rows"][7].update({"native_ucrt_result_bits": "0x7fc00000"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_missing_extra_duplicate_rows_and_stale_request_id_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional/run_summary.json", lambda value: value["rows"].pop())
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "distance/run_summary.json",
                                lambda value: value["rows"].append(dict(value["rows"][-1])))
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional_powf/run_summary.json",
                                lambda value: value["rows"].__setitem__(4, dict(value["rows"][3])))
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "run_summary.json",
                                lambda value: value.update({"request_id": self.module.BATCH_ID + "_stale"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_wrong_ucrt_path_hash_and_child_request_id_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "run_summary.json",
                                lambda value: value["ucrtbase"].update({"path": r"C:\Temp\ucrtbase.dll"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)

    def test_duplicate_json_object_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            summary = root / self.module.BATCH_ID / "run_summary.json"
            raw = summary.read_text()
            summary.write_text(raw.replace('{\n  "children"',
                                           '{\n  "request_id": "duplicate",\n  "children"', 1))
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "run_summary.json",
                                lambda value: value["ucrtbase"].update({"sha256": "not-a-sha"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "directional/run_summary.json",
                                lambda value: value.update({"request_id": self.module.DIRECTIONAL_ID + "_stale"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "distance/run_summary.json",
                                lambda value: value["rows"][0].update({"native_ucrt_result_bits": "0x3f800000"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-return-") as temp:
            root = self.build_valid_return(Path(temp))
            self.mutate_summary(root, "distance/run_summary.json",
                                lambda value: value["rows"][4].update({"native_ucrt_result_bits": "0x0"}))
            with self.assertRaises(ValueError):
                self.module.analyze(root)


if __name__ == "__main__":
    unittest.main()
