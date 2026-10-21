from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DistancePowerUcrtRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_module(
            "dg_power_request",
            ROOT / "tools/emulation/test_olmdistancegradation_pf32_power_ucrt_request_20260813.py",
        )
        cls.analyzer = load_module(
            "dg_power_analyzer",
            ROOT / "scripts/analyze_olmdistancegradation_pf32_power_ucrt_return_20260813.py",
        )

    def valid_return_files(self) -> dict[str, bytes]:
        vectors_bytes = (self.generator.PACKAGE_DIR / "powf_vectors.json").read_bytes()
        request_bytes = (self.generator.PACKAGE_DIR / "request_manifest.json").read_bytes()
        vectors = json.loads(vectors_bytes)
        ucrt = {
            "path": r"C:\Windows\System32\ucrtbase.dll",
            "file_version": "10.0.test",
            "product_version": "10.0.test",
            "sha256": "1" * 64,
        }
        rows = [
            {
                "input_bits": vector["input_bits"],
                "exponent_bits": vector["exponent_bits"],
                "native_ucrt_result_bits": vector["host_result_bits"],
                "occurrences": vector["occurrences"],
                "ucrtbase_path": ucrt["path"],
                "ucrtbase_file_version": ucrt["file_version"],
                "ucrtbase_product_version": ucrt["product_version"],
                "ucrtbase_sha256": ucrt["sha256"],
            }
            for vector in vectors
        ]
        summary = {
            "schema": "olmdistancegradation.pf32-power-ucrt-powf-return/1",
            "request_id": self.generator.REQUEST_ID,
            "status": "answered_native_windows_ucrt_powf",
            "process_bitness": 64,
            "processor_architecture": "AMD64",
            "ucrtbase": ucrt,
            "vector_count": 63,
            "vectors_sha256": self.generator.sha_bytes(vectors_bytes),
            "rows": rows,
        }
        return {
            f"{self.generator.REQUEST_ID}/run_summary.json": self.generator.canonical(summary),
            f"{self.generator.REQUEST_ID}/request_manifest.json": request_bytes,
            f"{self.generator.REQUEST_ID}/powf_vectors.json": vectors_bytes,
        }

    def write_return(self, directory: Path, files: dict[str, bytes]) -> Path:
        path = directory / "return.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        return path

    def test_persisted_request_is_live_source_exact(self) -> None:
        report = self.generator.generate(False)
        self.assertEqual(report["production_census"]["powf_calls"], 1496)
        self.assertEqual(report["production_census"]["unique_vectors"], 63)
        self.assertEqual(report["host_substituted_relation"]["exported_aex_cells_matching_production"], 8)
        self.assertEqual(report["production_policy"]["behavior"], "fail_closed_on_arm64_and_x86_64")

    def test_valid_native_return_is_accepted_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), self.valid_return_files())
            report = self.analyzer.analyze(path)
        self.assertEqual(report["status"], "PASS_NATIVE_UCRT_RETURN_VALIDATED_POWER_STILL_NOT_PROMOTED")
        self.assertEqual(report["native_vs_host_substituted"]["equal_vectors"], 63)
        self.assertIn("remains fail-closed", report["production_policy"])

    def test_return_unknown_row_key_is_rejected(self) -> None:
        files = self.valid_return_files()
        summary_name = next(name for name in files if name.endswith("run_summary.json"))
        summary = json.loads(files[summary_name])
        summary["rows"][0]["forged"] = True
        files[summary_name] = self.generator.canonical(summary)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_duplicate_vector_is_rejected(self) -> None:
        files = self.valid_return_files()
        summary_name = next(name for name in files if name.endswith("run_summary.json"))
        summary = json.loads(files[summary_name])
        summary["rows"][1] = dict(summary["rows"][0])
        files[summary_name] = self.generator.canonical(summary)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_request_bytes_are_bound(self) -> None:
        files = self.valid_return_files()
        request_name = next(name for name in files if name.endswith("request_manifest.json"))
        files[request_name] += b" "
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_ucrt_identity_is_bound_per_row(self) -> None:
        files = self.valid_return_files()
        summary_name = next(name for name in files if name.endswith("run_summary.json"))
        summary = json.loads(files[summary_name])
        summary["rows"][17]["ucrtbase_sha256"] = "2" * 64
        files[summary_name] = self.generator.canonical(summary)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_unknown_summary_key_is_rejected(self) -> None:
        files = self.valid_return_files()
        summary_name = next(name for name in files if name.endswith("run_summary.json"))
        summary = json.loads(files[summary_name])
        summary["forged"] = True
        files[summary_name] = self.generator.canonical(summary)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_extra_member_is_rejected(self) -> None:
        files = self.valid_return_files()
        files[f"{self.generator.REQUEST_ID}/extra.txt"] = b"not evidence\n"
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_forged_system32_suffix_is_rejected(self) -> None:
        files = self.valid_return_files()
        summary_name = next(name for name in files if name.endswith("run_summary.json"))
        summary = json.loads(files[summary_name])
        forged = r"C:\\fake\\System32\\ucrtbase.dll"
        summary["ucrtbase"]["path"] = forged
        for row in summary["rows"]:
            row["ucrtbase_path"] = forged
        files[summary_name] = self.generator.canonical(summary)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)

    def test_return_noncanonical_vector_bits_are_rejected(self) -> None:
        files = self.valid_return_files()
        summary_name = next(name for name in files if name.endswith("run_summary.json"))
        summary = json.loads(files[summary_name])
        summary["rows"][0]["input_bits"] = summary["rows"][0]["input_bits"].upper()
        files[summary_name] = self.generator.canonical(summary)
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_return(Path(temporary), files)
            with self.assertRaises(ValueError):
                self.analyzer.analyze(path)


if __name__ == "__main__":
    unittest.main()
