from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_aexcompat_oracle_campaign.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_aexcompat_oracle_campaign", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerateAexcompatOracleCampaignTests(unittest.TestCase):
    def test_cross_product_and_premultiplied_boundary(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.png"
            Image.new("RGBA", (2, 2), (200, 100, 50, 135)).save(source)
            output = root / "campaign"
            manifest_path = module.build_campaign(
                [source], [(3, 2), (5, 4)],
                [[{"name": "Amount", "property_index": 1, "value": 0}],
                 [{"name": "Amount", "property_index": 1, "value": 100}]],
                "OLM Test", output,
            )

            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(len(manifest["source_inputs"]), 2)
            self.assertEqual(len(manifest["cases"]), 4)
            self.assertNotIn("frame", manifest["cases"][0])
            with Image.open(output / "input" / "input_000_g000.png") as image:
                self.assertEqual(image.size, (3, 2))
                self.assertEqual(image.getpixel((0, 0)), (106, 53, 26, 135))

    def test_invalid_geometry_fails(self) -> None:
        module = load_module()
        with self.assertRaisesRegex(ValueError, "expected WIDTHxHEIGHT"):
            module.parse_geometry("1920,1080")


if __name__ == "__main__":
    unittest.main()
