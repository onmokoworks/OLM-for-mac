import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HARNESS = ROOT / "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"
AEX_REPORT = ROOT / "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json"
AEX_REPLAY = ROOT / "tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py"
EXPECTED_AEX_SHA256 = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
EXPECTED_PUBLIC_SOURCE_SHA256 = {
    8: "3c024f8074f08c5152ba54c1b79e275eae2c5c2a2b4572a4497303cec836afd0",
    16: "b85a7304ea38b0ae22b142a3a95421a58ac3e1ff179ac53805b47a918a1f5ffb",
    32: "2c8d46d068ef23fe313f151a4b6f4726cffbae6c98a66a5b331096e0eb849556",
}


class KiraKiraMode3UiLengthBetaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(prefix="kira_mode3_ui_beta_")
        cls.directory = Path(cls._temporary.name)
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        common = [
            "clang++", "-std=c++20", "-fno-fast-math", "-ffp-contract=off",
            "-isysroot", sdk, "-w", "-I", str(ROOT / "Headers"),
            "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
            "-I", str(ROOT / "Resources"), f'-DKIRA_SOURCE="{SOURCE}"',
            str(HARNESS), str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"), "-framework", "Cocoa",
        ]
        cls.normal = cls.directory / "mode3_ui"
        normal = subprocess.run(
            [*common, "-O2", "-DNDEBUG", "-o", str(cls.normal)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if normal.returncode:
            raise AssertionError(normal.stderr[-16000:])
        cls.sanitized = cls.directory / "mode3_ui_sanitized"
        sanitized = subprocess.run(
            [*common, "-O1", "-g", "-fno-omit-frame-pointer",
             "-fsanitize=address,undefined", "-o", str(cls.sanitized)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if sanitized.returncode:
            raise AssertionError(sanitized.stderr[-16000:])

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def run_harness(self, executable: Path, option: str, timeout: int) -> str:
        environment = os.environ.copy()
        if executable == self.sanitized:
            environment["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
            environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
        result = subprocess.run(
            [str(executable), option], cwd=ROOT, text=True, capture_output=True,
            env=environment, timeout=timeout,
        )
        self.assertEqual(
            result.returncode, 0,
            f"stdout:\n{result.stdout[-16000:]}\nstderr:\n{result.stderr[-16000:]}",
        )
        return result.stdout

    def test_actual_aex_helper_chain_covers_ui_range_and_boundary(self) -> None:
        report = json.loads(AEX_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "captured")
        self.assertEqual(report["aex_sha256"], EXPECTED_AEX_SHA256)
        self.assertEqual(
            report["boundary"],
            "Hostless checked-in Windows AEX complete helper chains; no native-AE claim.",
        )
        self.assertEqual(len(report["cases"]), 66)
        self.assertEqual(
            {case["length"] for case in report["cases"]},
            {1, 2, 3, 5, 7, 9, 11, 25, 50, 100, 200, 300, 301, 1000},
        )
        self.assertEqual(
            {case["angle_degrees"] for case in report["cases"]},
            {-45, 0, 17, 45},
        )
        replay = subprocess.run(
            ["python3", str(AEX_REPLAY)], cwd=ROOT, text=True,
            capture_output=True, timeout=120,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr[-12000:])
        self.assertIn("cases=66 words=497250 max_ulp=0", replay.stdout)

    def test_every_visible_ui_length_runs_all_depths_through_classic_and_smart(self) -> None:
        output = self.run_harness(self.normal, "--mode3-ui-sweep", 300)
        rows = [line for line in output.splitlines() if line.startswith("GENERIC ")]
        self.assertEqual(len(rows), 300 * 3)
        self.assertTrue(all("ok=1" in row for row in rows))
        self.assertEqual(
            {int(row.split("length=")[1].split()[0]) for row in rows},
            set(range(1, 301)),
        )
        self.assertEqual(
            {int(row.split("depth=")[1].split()[0]) for row in rows},
            {8, 16, 32},
        )
        self.assertTrue(all("callbacks=1/1/1/0" in row for row in rows))
        self.assertIn("MODE3_UI_GUARDS lengths=300 geometry=dci4k rotation=0/1 ok=1", output)

    def test_public_effectmain_matrix_is_complete_and_sanitizer_clean(self) -> None:
        expected = {
            (length, rotation, depth)
            for length in (1, 2, 50, 300)
            for rotation in (0.0, 1.0)
            for depth in (8, 16, 32)
        }
        for executable in (self.normal, self.sanitized):
            with self.subTest(executable=executable.name):
                output = self.run_harness(
                    executable, "--mode3-public-matrix", 300,
                )
                rows = [
                    line for line in output.splitlines()
                    if line.startswith("GENERIC ")
                ]
                self.assertEqual(len(rows), 24)
                actual = {
                    (
                        int(row.split("length=")[1].split()[0]),
                        float(row.split("rotation=")[1].split()[0]),
                        int(row.split("depth=")[1].split()[0]),
                    )
                    for row in rows
                }
                self.assertEqual(actual, expected)
                self.assertTrue(all("size=17x11" in row for row in rows))
                self.assertTrue(all("content=full" in row for row in rows))
                self.assertTrue(all("ok=1" in row for row in rows))
                self.assertTrue(all("callbacks=1/1/1/0" in row for row in rows))
                self.assertTrue(all("params=25/25" in row for row in rows))
                for token in (
                    "lifecycle=1", "headers=1", "mixed_alpha=1",
                    "zero_alpha_rgb=1", "predata=1", "deleted=1", "handles=1",
                ):
                    self.assertTrue(all(token in row for row in rows), token)
                for row in rows:
                    strides = row.split("strides=")[1].split()[0]
                    input_stride, smart_stride, classic_stride = map(
                        int, strides.split("/"),
                    )
                    self.assertEqual(
                        len({input_stride, smart_stride, classic_stride}), 3,
                    )
                    depth = int(row.split("depth=")[1].split()[0])
                    input_active = bytes.fromhex(
                        row.split("input_active_hex=")[1].split()[0]
                    )
                    smart_active = bytes.fromhex(
                        row.split("smart_active_hex=")[1].split()[0]
                    )
                    classic_active = bytes.fromhex(
                        row.split("classic_active_hex=")[1].split()[0]
                    )
                    pixel_size = {8: 4, 16: 8, 32: 16}[depth]
                    expected_size = 17 * 11 * pixel_size
                    self.assertEqual(len(input_active), expected_size)
                    self.assertEqual(len(smart_active), expected_size)
                    self.assertEqual(len(classic_active), expected_size)
                    self.assertEqual(
                        hashlib.sha256(input_active).hexdigest(),
                        EXPECTED_PUBLIC_SOURCE_SHA256[depth],
                    )
                    smart_sha = hashlib.sha256(smart_active).hexdigest()
                    classic_sha = hashlib.sha256(classic_active).hexdigest()
                    self.assertEqual(smart_sha, classic_sha)

    def test_representative_lengths_accept_content_bounds_and_reject_one_away(self) -> None:
        output = self.run_harness(self.normal, "--mode3-ui-matrix", 300)
        rows = [line for line in output.splitlines() if line.startswith("GENERIC ")]
        self.assertTrue(any("rotation=1" in row and "length=300" in row for row in rows))
        self.assertTrue(any("content=partial" in row and "length=300" in row for row in rows))
        self.assertTrue(any("content=partial" in row and "size=32x18" in row for row in rows))
        self.assertTrue(any(
            "content=partial" in row and "size=32x18" in row and "length=50" in row
            for row in rows
        ))
        self.assertTrue(any("size=1920x1080" in row and "length=300" in row for row in rows))
        rejects = [line for line in output.splitlines() if line.startswith("MODE3_UI_REJECT ")]
        self.assertEqual(len(rejects), 6)
        self.assertTrue(all("ok=1" in row for row in rejects))
        self.assertEqual(
            {(int(row.split("length=")[1].split()[0]),
              int(row.split("depth=")[1].split()[0])) for row in rejects},
            {(length, depth) for length in (0, 301) for depth in (8, 16, 32)},
        )

    def test_representative_boundaries_are_clean_under_asan_and_ubsan(self) -> None:
        output = self.run_harness(self.sanitized, "--mode3-ui-sanitizer", 300)
        rows = [line for line in output.splitlines() if line.startswith("GENERIC ")]
        # Five boundary lengths at rotation 0, three representative lengths at
        # rotation 1, one 17x11 content-bound case, and both the legacy exact
        # length and the UI endpoint at 32x18, all at three depths.
        self.assertEqual(len(rows), (5 + 3 + 1 + 2) * 3)
        self.assertTrue(all("ok=1" in row for row in rows))
        self.assertTrue(any("content=partial" in row for row in rows))
        self.assertTrue(any("content=partial" in row and "size=32x18" in row for row in rows))
        self.assertEqual(output.count("MODE3_UI_REJECT "), 6)

    def test_invalid_deep_samples_and_worlds_fail_atomically(self) -> None:
        output = self.run_harness(self.sanitized, "--mode3-ui-failures", 120)
        rows = [line for line in output.splitlines() if line.startswith("MODE3_UI_FAILURE ")]
        self.assertEqual(len(rows), 12)
        self.assertTrue(all("ok=1" in row for row in rows))
        self.assertEqual(
            {row.split("name=")[1].split()[0] for row in rows},
            {
                "pf16_32769", "pf16_65535", "pf32_negative", "pf32_above_one",
                "pf32_nan", "pf32_pos_inf", "pf32_neg_inf", "zero_rowbytes",
                "short_rowbytes", "misaligned_rowbytes", "alias", "partial_overlap",
            },
        )

    def test_every_render_allocation_failure_is_atomic(self) -> None:
        output = self.run_harness(self.normal, "--mode3-ui-allocations", 180)
        rows = [line for line in output.splitlines() if line.startswith("MODE3_UI_ALLOC ")]
        self.assertEqual(len(rows), 6)
        self.assertTrue(all("ok=1" in row for row in rows))
        self.assertEqual(
            {(row.split("route=")[1].split()[0],
              int(row.split("depth=")[1].split()[0])) for row in rows},
            {(route, depth) for route in ("classic", "smart") for depth in (8, 16, 32)},
        )
        self.assertTrue(all(int(row.split("allocations=")[1].split()[0]) > 0 for row in rows))

    def test_smart_request_provenance_separates_full_32x18_from_large_comp_roi(self) -> None:
        output = self.run_harness(
            self.sanitized, "--mode3-ui-roi-provenance", 120,
        )
        rows = [
            line for line in output.splitlines()
            if line.startswith("MODE3_UI_ROI_PROVENANCE ")
        ]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all("ok=1" in row for row in rows))
        self.assertTrue(all(
            "large=1" in row and "downsample=1" in row and "overcap=1" in row
            for row in rows
        ))
        self.assertEqual(
            {int(row.split("depth=")[1].split()[0]) for row in rows},
            {8, 16, 32},
        )
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("bool generic_full_frame_request;", source)
        self.assertIn("pre->generic_full_frame_request = generic_beta_request;", source)
        self.assertIn("pre->generic_full_frame_request &&", source)


if __name__ == "__main__":
    unittest.main()
