from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_reference_request_status import load_json, score_request  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
REQUESTS = ROOT / "refs" / "reference_requests"
MANIFEST_PATH = (
    ROOT
    / "refs"
    / "win_references"
    / "20260710_190500__ae26_3_32bpc_recap"
    / "OLMbit-depthconformancebatch"
    / "reference_manifest.json"
)


class HistoricalAliasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(MANIFEST_PATH)
        self.manifests = [(MANIFEST_PATH, self.manifest)]

    def request(self, plugin: str) -> dict:
        path = REQUESTS / f"olm_bitdepth_32bpc_{plugin}_float_20260710.json"
        return load_json(path)

    def test_explicit_alias_covers_both_historical_slices(self) -> None:
        for plugin in ("colorkey", "toondilate"):
            with self.subTest(plugin=plugin):
                row = score_request(self.request(plugin), self.manifests)
                self.assertEqual(row["status"], "covered")
                self.assertEqual(row["best"]["matched_cases"], row["required_cases"])

    def assert_alias_rejected(self, mutate) -> None:
        request = self.request("toondilate")
        mutate(request["historical_request_aliases"][0])
        row = score_request(request, self.manifests)
        self.assertEqual(row["status"], "pending")
        self.assertIsNone(row["best"])

    def test_no_alias_is_not_inferred_from_case_ids_or_files(self) -> None:
        request = self.request("toondilate")
        request.pop("historical_request_aliases")
        row = score_request(request, self.manifests)
        self.assertEqual(row["status"], "pending")

    def test_case_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(
            lambda alias: alias["case_bindings"][0].__setitem__("historical_case_id", "olmtoondilate__case_0009")
        )

    def test_render_set_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(lambda alias: alias.__setitem__("render_set_id", "cuda"))

    def test_settings_mismatch_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["project"]["bits_per_channel"] = 16
        request = self.request("toondilate")
        row = score_request(request, [(MANIFEST_PATH, manifest)])
        self.assertEqual(row["status"], "pending")

    def test_file_binding_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(
            lambda alias: alias["case_bindings"][0].__setitem__("frame", "wrong.exr")
        )

    def test_manifest_hash_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(lambda alias: alias.__setitem__("manifest_sha256", "0" * 64))

    def test_effect_artifact_hash_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(
            lambda alias: alias["case_bindings"][0].__setitem__("frame_sha256", "0" * 64)
        )

    def test_before_effects_artifact_hash_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(
            lambda alias: alias["case_bindings"][0].__setitem__("before_effects_frame_sha256", "0" * 64)
        )

    def test_artifact_byte_drift_is_rejected(self) -> None:
        request = self.request("toondilate")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path = root / "reference_manifest.json"
            shutil.copy2(MANIFEST_PATH, manifest_path)
            for case in self.manifest["cases"]:
                if case["id"].startswith("olmtoondilate__"):
                    for key in ("frame", "before_effects_frame"):
                        shutil.copy2(MANIFEST_PATH.parent / case[key], root / case[key])
            request["historical_request_aliases"][0]["manifest_sha256"] = hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest()
            first_frame = root / request["historical_request_aliases"][0]["case_bindings"][0]["frame"]
            first_frame.write_bytes(first_frame.read_bytes() + b"drift")
            row = score_request(request, [(manifest_path, self.manifest)])
        self.assertEqual(row["status"], "pending")

    def test_output_template_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(
            lambda alias: alias["output_capabilities"].__setitem__("output_template", "wrong")
        )

    def test_ae_version_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(lambda alias: alias.__setitem__("ae_version", "wrong"))

    def test_project_color_metadata_mismatch_is_rejected(self) -> None:
        self.assert_alias_rejected(
            lambda alias: alias["project"].__setitem__("working_space", False)
        )


if __name__ == "__main__":
    unittest.main()
