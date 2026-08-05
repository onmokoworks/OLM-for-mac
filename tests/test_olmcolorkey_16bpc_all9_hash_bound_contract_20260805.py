#!/usr/bin/env python3
"""Fail-closed retained-evidence contract for OLMColorKey's 16bpc slice.

This verifies the committed Windows request, Mac AE render inventory, and all
nine pairs of 16-bit PNGs.  It does not rerender AE and, because the historical
render result did not record a loaded-module hash, it does not attest a new Mac
binary.
"""

from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST = (
    ROOT
    / "handoff/ae_pixel_validation_20260618/requests"
    / "ae_pixel_bitdepth16_olmcolorkey_exact_20260625"
)
RESULT = (
    ROOT
    / "handoff/ae_pixel_validation_20260618/results"
    / "bitdepth16_olmcolorkey_exact"
)
CANONICAL = (
    ROOT
    / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625"
    / "OLMbit-depthconformancebatch"
)
CONFORMANCE = ROOT / "refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json"

PINNED = {
    REQUEST / "request_manifest.json": "baea985f4caddb557695d20b0bb06f482c5658c3511100f744f63556b7f5d8b9",
    REQUEST / "reference_manifest.json": "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e",
    RESULT / "AE_PIXEL_VALIDATION_RENDER_RESULT.json": "3a48ba8a4a77c9767fe2eade94d6ed98be7192ef455a9ef7ed0a05d468e8981c",
    CONFORMANCE: "713f4c230050dc129af0acacc00be5abfde8581330a9eaec67d07d9f6e3cd22d",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_ihdr(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()[:33]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"not a PNG with an initial IHDR: {path}")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return width, height, bit_depth, color_type


class OLMColorKey16bpcAll9HashBoundContractTests(unittest.TestCase):
    def test_manifests_and_render_inventory_are_pinned(self):
        for path, expected in PINNED.items():
            with self.subTest(path=path):
                self.assertEqual(sha256(path), expected)

        request = load(REQUEST / "request_manifest.json")
        threshold = request["threshold_groups"][0]
        case_ids = [f"olmcolorkey__case_{number:04d}" for number in range(1, 10)]
        self.assertEqual(threshold, {
            "name": "16bpc_all_exact",
            "case_ids": case_ids,
            "max_diff": 0,
            "mean_diff": 0.0,
            "nonzero_px_percent": 0.0,
        })

        rendered = load(RESULT / "AE_PIXEL_VALIDATION_RENDER_RESULT.json")
        self.assertEqual(rendered["effect_name"], "OLM Color Key")
        self.assertEqual(rendered["warnings"], [])
        self.assertEqual(rendered["errors"], [])
        request_rows = {row["id"]: row for row in request["cases"]}
        self.assertEqual(rendered["rendered"], [request_rows[c]["frame"] for c in case_ids])

    def test_all_nine_windows_mac_png_pairs_are_exact_16bit_rgba(self):
        request = load(REQUEST / "request_manifest.json")
        reference = load(REQUEST / "reference_manifest.json")
        conformance = load(CONFORMANCE)

        request_rows = {row["id"]: row for row in request["cases"]}
        reference_rows = {
            row["id"]: row for row in reference["cases"]
            if row["id"].startswith("olmcolorkey__")
        }
        exact_rows = {
            row["case_id"]: row for row in conformance["cases"]
            if row["plugin"] == "OLMColorKey"
        }
        case_ids = [f"olmcolorkey__case_{number:04d}" for number in range(1, 10)]
        self.assertEqual(sorted(reference_rows), case_ids)
        self.assertEqual(sorted(exact_rows), case_ids)

        for case_id in case_ids:
            with self.subTest(case_id=case_id):
                reference_row = reference_rows[case_id]
                self.assertEqual(reference_row["bits_per_channel"], 16)
                self.assertEqual(reference_row["project_gpu_accel_type"], {
                    "current_name": "SOFTWARE", "raw": 1816
                })
                self.assertEqual(reference_row["requested_effect"]["name"], "OLM Color Key")

                exact = exact_rows[case_id]
                self.assertEqual(exact["result_status"], "AE exact")
                self.assertEqual(exact["reference_kind"], "Windows AE Software")
                self.assertEqual(exact["runner_kind"], "Mac AE plugin")
                self.assertEqual(
                    (exact["max_diff"], exact["mean_diff"], exact["nonzero_px_percent"]),
                    (0, 0.0, 0.0),
                )

                frame = request_rows[case_id]["frame"]
                windows_request = REQUEST / "expected" / frame
                windows_canonical = CANONICAL / frame
                mac_result = RESULT / frame
                digest = sha256(mac_result)
                self.assertEqual(digest, exact["output_sha256"])
                self.assertEqual(digest, sha256(windows_request))
                self.assertEqual(digest, sha256(windows_canonical))
                for path in (windows_request, windows_canonical, mac_result):
                    self.assertEqual(png_ihdr(path), (1920, 1080, 16, 6))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
