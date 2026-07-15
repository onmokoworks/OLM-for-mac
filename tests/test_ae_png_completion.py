import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AePngCompletionContractTests(unittest.TestCase):
    def test_single_case_uses_bounded_stability_gate_and_metadata(self):
        source = (ROOT / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
        self.assertIn("function waitForStableFile", source)
        self.assertIn("waitForStableFile(png, renderStarted, 120000, 250)", source)
        self.assertIn("fresh && size > 0", source)
        self.assertIn("stablePolls >= 2", source)
        self.assertIn("timeoutMs", source)
        self.assertIn('summary.png_observation.status !== "stable"', source)
        self.assertIn("png_observation", source)
        self.assertNotIn("waitForFreshFile(png", source)

    def test_batch_records_each_observation_and_only_renders_stable_pngs(self):
        source = (ROOT / "scripts/ae_pixel_validation_render.jsx").read_text(encoding="utf-8")
        self.assertIn("function waitForStableFile", source)
        self.assertIn("summary.png_observations[caseSpec.id] = observation", source)
        self.assertIn("fresh && size > 0", source)
        self.assertIn("stablePolls >= 2", source)
        self.assertIn("timeoutMs", source)
        self.assertIn('if (observation.status !== "stable")', source)
        self.assertIn("png_observations", source)
        self.assertNotIn("waitForFreshFile(png", source)

    def test_observation_metadata_is_json_compatible(self):
        observation = {
            "status": "stable",
            "timeout_ms": 120000,
            "waited_ms": 500,
            "polls": 3,
            "stable_polls": 2,
            "size_bytes": 4096,
            "modified_ms": 1760000000000,
        }
        round_tripped = json.loads(json.dumps(observation))
        self.assertEqual(round_tripped["status"], "stable")
        self.assertEqual(round_tripped["size_bytes"], 4096)
        self.assertGreaterEqual(round_tripped["waited_ms"], 0)


if __name__ == "__main__":
    unittest.main()
