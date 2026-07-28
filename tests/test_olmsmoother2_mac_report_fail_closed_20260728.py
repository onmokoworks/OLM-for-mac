from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "scripts/report_olmsmoother2_no_key_32bpc_mac_validation_20260715.py"
RUNNER = ROOT / "scripts/run_olmsmoother2_no_key_32bpc_mac_validation_20260715.py"


def load_report():
    spec = importlib.util.spec_from_file_location("smoother2_report_fail_closed", REPORT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_tree(tmp_path: Path):
    result = tmp_path / "mac_validation_return.json"
    challenge = tmp_path / "run_challenge.json"
    result.write_text("{}")
    outputs = {}
    ordered = []
    for branch, stem in (("no_effect_control", "no"), ("effect_on", "yes")):
        exr = tmp_path / f"{stem}.exr"
        settings = tmp_path / f"{stem}_output_module_settings.json"
        exr.write_bytes(b"exr")
        settings.write_text("{}")
        outputs[branch] = {
            "path": str(exr),
            "output_module_settings": {"path": str(settings)},
        }
        ordered.extend((str(exr), str(settings)))
    challenge.write_text(json.dumps({
        "kind": "olmsmoother2_mac_run_challenge",
        "result_path": str(result),
        "output_paths": {
            "no_effect_control": {"exr": ordered[0], "settings": ordered[1]},
            "effect_on": {"exr": ordered[2], "settings": ordered[3]},
        },
    }))
    return result, {"outputs": outputs}


class Smoother2ReportFailClosedTests(unittest.TestCase):
    def test_resolver_rejects_path_split_and_duplicate_alias(self):
        report = load_report()
        with tempfile.TemporaryDirectory(prefix="smoother2_report_paths_") as raw:
            tmp_path = Path(raw)
            result, case = fixture_tree(tmp_path)
            outside = tmp_path.parent / (tmp_path.name + "_outside.exr")
            outside.write_bytes(b"x")
            try:
                case["outputs"]["effect_on"]["path"] = str(outside)
                with self.assertRaisesRegex(ValueError, "escapes"):
                    report.resolve_return_paths(result, tmp_path, case)
            finally:
                outside.unlink(missing_ok=True)

            result, case = fixture_tree(tmp_path)
            case["outputs"]["effect_on"]["path"] = case["outputs"]["no_effect_control"]["path"]
            with self.assertRaisesRegex(ValueError, "duplicate"):
                report.resolve_return_paths(result, tmp_path, case)

            result, case = fixture_tree(tmp_path)
            control = case["outputs"]["no_effect_control"]["path"]
            effect = case["outputs"]["effect_on"]["path"]
            case["outputs"]["no_effect_control"]["path"] = effect
            case["outputs"]["effect_on"]["path"] = control
            with self.assertRaisesRegex(ValueError, "path split"):
                report.resolve_return_paths(result, tmp_path, case)

    def test_static_nonce_freshness_readback_and_no_ae_exact(self):
        runner = RUNNER.read_text(encoding="utf-8")
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("secrets.token_hex(32)", runner)
        self.assertIn("stale/preexisting result or output exists", runner)
        self.assertIn("started_at", runner)
        self.assertIn("ended_at", runner)
        self.assertIn("readback_before_render", runner)
        self.assertIn("readback_after_render", runner)
        self.assertIn("parameter readback", runner)
        self.assertIn('item.get("readback_before_render")!=expected_readback', report)
        self.assertIn("stale preexisting artifact", report)
        self.assertIn('"ae_exact_claim":False', report)
        self.assertIn('"raw_float32_exact_artifact_classification":exact', report)
        self.assertIn("raw_float32_exact_artifact_only_missing_process_proof", report)
        self.assertIn("windows_same_run_process_proof_present", report)
        self.assertIn("missing_exact_process_proof", report)
        self.assertNotIn('"ae_exact_claim":exact', report)
        self.assertIn("return 2 if exact else 1", report)
        self.assertIn("p.name!==x.name", runner)
        self.assertLess(runner.index("m.file=new File(p);var s=capture"), runner.index("app.project.renderQueue.render()"))


if __name__ == "__main__":
    unittest.main()
