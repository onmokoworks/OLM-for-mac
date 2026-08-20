import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"


class KiraKiraGenericBetaSanitizerTests(unittest.TestCase):
    def test_production_entries_are_clean_and_deterministic(self) -> None:
        extended = os.environ.get("OLM_KIRA_EXTENDED_SANITIZERS") == "1"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        with tempfile.TemporaryDirectory(prefix="kira_generic_san_") as raw:
            executable = Path(raw) / "generic"
            command = [
                "clang++", "-std=c++20", "-O1", "-g", "-fno-omit-frame-pointer",
                "-fno-fast-math", "-ffp-contract=off",
                "-fsanitize=address,undefined", "-isysroot", sdk, "-w",
                "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
                f'-DKIRA_SOURCE="{SOURCE}"', str(HARNESS),
                str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
                str(ROOT / "Util/MissingSuiteError.cpp"),
                "-framework", "Cocoa", "-o", str(executable),
            ]
            built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(built.returncode, 0, built.stderr[-12000:])
            environment = os.environ.copy()
            environment["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
            environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
            ran = subprocess.run(
                [str(executable), *(["--extended"] if extended else [])],
                cwd=ROOT, text=True, capture_output=True,
                env=environment, timeout=1200 if extended else 300,
            )
            self.assertEqual(
                ran.returncode, 0,
                f"stdout:\n{ran.stdout[-12000:]}\nstderr:\n{ran.stderr[-12000:]}",
            )
            rows = [line for line in ran.stdout.splitlines() if line.startswith("GENERIC ")]
            self.assertEqual(len(rows), 54)
            self.assertTrue(all("ok=1" in row for row in rows))
            self.assertTrue(any("size=17x11" in row for row in rows))
            self.assertTrue(any("size=1920x1080" in row for row in rows))
            self.assertEqual(
                any("size=3840x2160" in row for row in rows), extended
            )
            self.assertEqual({int(row.split("depth=")[1].split()[0]) for row in rows}, {8, 16, 32})
            self.assertTrue(all("callbacks=1/1/1/0" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
