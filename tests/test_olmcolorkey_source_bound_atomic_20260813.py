from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.emulation.olm_assets import resolve_asset

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmcolorkey_source_bound_atomic_20260813.cpp"
COVER = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_covering_20260812.json"
TRANSFER = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_geometry_transfer_20260812.json"
SECOND_SOURCE = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_second_source_20260814.json"
LAB = ROOT / "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json"
TOGGLE = ROOT / "refs/conformance/olmcolorkey_exported_owner_keep_premult_replace_20260811.json"


class ColorKeySourceBoundAtomic(unittest.TestCase):
    def test_all_public_cells_and_one_aways(self) -> None:
        expected: list[tuple[int, str]] = []
        for report_path in (COVER, TRANSFER):
            report = json.loads(report_path.read_text())
            expected.extend(
                (int(row["bytes"]), str(row["actual_exported_raw_sha256"]))
                for row in report["cases"]
            )
        lab = json.loads(LAB.read_text())
        expected.extend(
            (int(row["raw_pixel_bytes"]), str(row["raw_pixel_sha256"]))
            for row in lab["production_effectmain"]["rows"]
        )
        # The C++ probe emits depth-major order. Reorder the two edge reports
        # from tuple-major and Lab from order-major into that canonical order.
        cover = expected[:18]
        transfer = expected[18:30]
        lab_rows = expected[30:]
        second_source = [
            (int(row["bytes"]), str(row["actual_exported_raw_sha256"]))
            for row in json.loads(SECOND_SOURCE.read_text())["cases"]
        ]
        toggle_rows = json.loads(TOGGLE.read_text())["cases"]
        expected = []
        for depth_index in range(3):
            expected.extend(cover[i] for i in range(depth_index, 18, 3))
            expected.extend(transfer[i] for i in range(depth_index, 12, 3))
            expected.append(second_source[depth_index])
            expected.extend((lab_rows[depth_index], lab_rows[3 + depth_index]))
            depth = ("PF8", "PF16", "PF32")[depth_index]
            expected.extend(
                (int(row["bytes"]), str(row["actual_exported_raw_sha256"]))
                for row in toggle_rows if row["depth"] == depth
            )

        with tempfile.TemporaryDirectory(prefix="olmcolorkey-source-bound.") as raw:
            executable = Path(raw) / "probe"
            sdk = subprocess.run(
                ["xcrun", "--show-sdk-path"], capture_output=True,
                text=True, check=True,
            ).stdout.strip()
            command = [
                "clang++", "-std=c++17", "-arch", "arm64", "-O2",
                "-Wno-pragma-pack", "-Wno-deprecated-declarations",
                "-isysroot", sdk, "-IHeaders", "-IHeaders/SP", "-IUtil",
                "-IResources", "-Imac/OLMColorKey", str(PROBE),
                "mac/OLMColorKey/OLMColorKey_Strings.cpp",
                str(resolve_asset("Util/AEGP_SuiteHandler.cpp")), str(resolve_asset("Util/MissingSuiteError.cpp")),
                "-framework", "Cocoa", "-o", str(executable),
            ]
            subprocess.run(command, cwd=ROOT, check=True)
            run = subprocess.run(
                [str(executable)], cwd=ROOT, capture_output=True, check=True,
            )
        self.assertEqual(
            run.stderr.decode().strip(),
            "SOURCE_BOUND_ATOMIC pass=1 positives=63 negatives=567",
        )
        offset = 0
        for index, (size, digest) in enumerate(expected):
            payload = run.stdout[offset:offset + size]
            self.assertEqual(len(payload), size)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest, f"cell {index}")
            offset += size
        self.assertEqual(offset, len(run.stdout))


if __name__ == "__main__":
    unittest.main()
