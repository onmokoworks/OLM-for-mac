from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmcolorkey_public_entries_real_sdk_20260813.cpp"
COVER = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_covering_20260812.json"
TRANSFER = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_geometry_transfer_20260812.json"
SECOND_SOURCE = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_second_source_20260814.json"
LAB = ROOT / "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json"
TOGGLE = ROOT / "refs/conformance/olmcolorkey_exported_owner_keep_premult_replace_20260811.json"


def expected_depth_major() -> list[tuple[int, str]]:
    cover_rows = json.loads(COVER.read_text())["cases"]
    transfer_rows = json.loads(TRANSFER.read_text())["cases"]
    second_source_rows = json.loads(SECOND_SOURCE.read_text())["cases"]
    lab_rows = json.loads(LAB.read_text())["production_effectmain"]["rows"]
    toggle_rows = json.loads(TOGGLE.read_text())["cases"]
    expected: list[tuple[int, str]] = []
    for depth_index in range(3):
        edge = [
            *[cover_rows[i] for i in range(depth_index, 18, 3)],
            *[transfer_rows[i] for i in range(depth_index, 12, 3)],
            second_source_rows[depth_index],
        ]
        lab = [lab_rows[depth_index], lab_rows[3 + depth_index]]
        depth = ("PF8", "PF16", "PF32")[depth_index]
        toggles = [row for row in toggle_rows if row["depth"] == depth]
        for row in [*edge, *lab, *toggles]:
            size = int(row.get("bytes", row.get("raw_pixel_bytes")))
            digest = str(row.get("actual_exported_raw_sha256", row.get("raw_pixel_sha256")))
            expected.extend([(size, digest), (size, digest)])
    return expected


class ColorKeyPublicEntriesRealSdk(unittest.TestCase):
    def test_classic_and_smart_entries_match_oracle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olmcolorkey-public-entries.") as raw:
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
                "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp",
                "-framework", "Cocoa", "-o", str(executable),
            ]
            subprocess.run(command, cwd=ROOT, check=True)
            run = subprocess.run(
                [str(executable)], cwd=ROOT, capture_output=True, check=True,
            )
        self.assertEqual(
            run.stderr.decode().strip(),
            "COLORKEY_PUBLIC_ENTRIES pass=1 classic=63 smart=63 callback_negatives=13",
        )
        offset = 0
        for index, (size, digest) in enumerate(expected_depth_major()):
            payload = run.stdout[offset:offset + size]
            self.assertEqual(len(payload), size, f"cell {index}")
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest, f"cell {index}")
            offset += size
        self.assertEqual(offset, len(run.stdout))


if __name__ == "__main__":
    unittest.main()
