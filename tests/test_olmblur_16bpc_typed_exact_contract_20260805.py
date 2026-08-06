#!/usr/bin/env python3
"""Retained, hash-bound regression for OLMBlur's declared PF16 slice.

This does not run After Effects or promote a new case.  It keeps the existing
seven-case AE-exact claim connected to the retained Windows fixtures and to
the production ARGB64/Smart Render typed dispatch that consumes PF_Pixel16.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ROOT = (
    ROOT
    / "handoff/ae_pixel_validation_20260618/requests/"
    "ae_pixel_bitdepth16_olmblur_exact_20260625"
)
REQUEST = REQUEST_ROOT / "request_manifest.json"
REFERENCE = REQUEST_ROOT / "reference_manifest.json"
EVIDENCE = ROOT / "refs/conformance/olmblur_16bpc_fixed_worker_mac_ae_exact_20260717.json"
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"

REQUEST_SHA256 = "1ff908fca5b733a629ff6a72f107278f94a2510a3a6e192ae969bb90ca070047"
REFERENCE_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
MAC_MACHO_SHA256 = "71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72"
HASH = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OLMBlurPF16TypedExactContract(unittest.TestCase):
    def test_retained_manifests_and_all_seven_reference_frames_are_hash_bound(self):
        self.assertEqual(sha256(REQUEST), REQUEST_SHA256)
        self.assertEqual(sha256(REFERENCE), REFERENCE_SHA256)

        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

        expected_ids = [f"olmblur__case_{number:04d}" for number in range(1, 8)]
        self.assertEqual([row["id"] for row in request["cases"]], expected_ids)
        reference_rows = [row for row in reference["cases"] if row["id"].startswith("olmblur__")]
        self.assertEqual([row["id"] for row in reference_rows], expected_ids)
        self.assertEqual([row["id"] for row in evidence["cases"]], expected_ids)

        self.assertEqual(evidence["status"], "ae_exact")
        self.assertEqual(evidence["ae"]["version"], "26.3x87")
        self.assertEqual(evidence["ae"]["bits_per_channel"], 16)
        self.assertEqual(evidence["ae"]["renderer"], "SOFTWARE")
        self.assertEqual(evidence["ae"]["working_space"], "None")
        self.assertFalse(evidence["ae"]["linear_blending"])
        self.assertEqual(evidence["loaded_plugin"]["sha256"], MAC_MACHO_SHA256)
        self.assertEqual(evidence["summary"], {"exact": 7, "fail": 0, "missing": 0, "total": 7})

        request_by_id = {row["id"]: row for row in request["cases"]}
        reference_by_id = {row["id"]: row for row in reference_rows}
        for row in evidence["cases"]:
            with self.subTest(case=row["id"]):
                self.assertEqual(row["max_diff"], 0)
                self.assertEqual(row["mean_diff"], 0.0)
                self.assertRegex(row["output_sha256"], HASH)

                request_row = request_by_id[row["id"]]
                reference_row = reference_by_id[row["id"]]
                self.assertEqual(request_row["frame"], reference_row["frame"])
                expected = REQUEST_ROOT / "expected" / request_row["frame"]
                source = REQUEST_ROOT / "input" / request_row["before_effects_frame"]
                self.assertTrue(source.is_file())
                self.assertTrue(expected.is_file())
                self.assertEqual(sha256(expected), row["output_sha256"])

    def test_production_entrypoints_reach_the_pf16_typed_adapters(self):
        source = SOURCE.read_text(encoding="utf-8")

        # Classic Render must derive 16bpc from the actual ARGB64 world.
        self.assertRegex(
            source,
            r"case\s+PF_PixelFormat_ARGB64:\s*bpc\s*=\s*16;",
        )
        self.assertIn("short bpc = extra->input->bitdepth;", source)
        self.assertIn("ERR(BlurRender(in_data, input, output, bpc, &bp));", source)
        self.assertIn("ERR(BlurRender(in_data, input_world, output_world, bpc, &bp));", source)

        # The live PF16 lanes are explicit and must not silently fall back to
        # byte or float storage.  Both Legacy states are covered by the seven
        # retained cases and therefore belong to this exact claim boundary.
        self.assertIn("render_16bpc_nonlegacy_adapter", source)
        self.assertIn("render_16bpc_legacy_adapter", source)
        self.assertIn("if (bpc == 16 && !bp->legacy) {", source)
        self.assertIn("return render_16bpc_nonlegacy_adapter(", source)
        self.assertIn("if (bpc == 16 && bp->legacy) {", source)
        self.assertIn("return render_16bpc_legacy_adapter(", source)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
