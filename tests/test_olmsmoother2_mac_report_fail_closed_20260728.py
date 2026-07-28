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
    tmp_path = tmp_path.resolve()
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
        "run_nonce": "a" * 64,
        "started_at": "2026-07-28T00:00:00Z",
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

            result, case = fixture_tree(tmp_path)
            _, resolved_outputs, resolved_settings, challenge = report.resolve_return_paths(result, tmp_path, case)
            self.assertEqual(challenge["run_nonce"], "a" * 64)
            self.assertEqual(set(resolved_outputs), {"no_effect_control", "effect_on"})
            self.assertEqual(set(resolved_settings), {"no_effect_control", "effect_on"})

            alias = tmp_path / "run_challenge_alias.json"
            alias.hardlink_to(tmp_path / "run_challenge.json")
            with self.assertRaisesRegex(ValueError, "unaliased"):
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
        self.assertIn("raw_float32_exact_artifact_only_missing_windows_process_proof", report)
        self.assertIn('"mac_process_proof_present":mac_process_proof_present', report)
        self.assertIn("process_challenge.json", runner)
        self.assertIn("pre_request.json", runner)
        self.assertIn("post_request.json", runner)
        self.assertIn("mac_process_attestation.json", runner)
        self.assertIn("pre_ok_sha256", runner)
        self.assertIn("attestation_sha256", runner)
        self.assertIn("OLM_AE_MAC_PAYLOAD_SHA256", runner)
        self.assertIn("__olm_hash(payloadPath)", runner)
        self.assertIn("exclusive_bytes(wrapper", runner)
        self.assertIn("windows_same_run_process_proof_present", report)
        self.assertIn("missing_exact_process_proof", report)
        self.assertNotIn('"ae_exact_claim":exact', report)
        self.assertIn("return 2 if exact else 1", report)
        self.assertNotIn("--app-name", runner)
        self.assertNotIn("osascript", runner)
        self.assertIn("p.name!==x.name", runner)
        self.assertLess(runner.index("m.file=new File(p);var s=capture"), runner.index("app.project.renderQueue.render()"))

    def test_protocol_files_fail_closed_on_missing_stale_alias_and_tamper(self):
        report = load_report()
        with tempfile.TemporaryDirectory(prefix="smoother2_protocol_") as raw:
            root=Path(raw)
            missing=root/"missing.json"
            with self.assertRaises(OSError):
                report.strict_protocol_json(missing,"missing")
            stale=root/"stale.json"; stale.write_text('{"kind":"stale"}')
            self.assertEqual(report.strict_protocol_json(stale,"stale"),{"kind":"stale"})
            alias=root/"alias.json"; alias.hardlink_to(stale)
            with self.assertRaisesRegex(ValueError,"unaliased"):
                report.strict_protocol_json(stale,"stale")
            alias.unlink()
            stale.write_text('{"kind":"a","kind":"tampered"}')
            with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
                report.strict_protocol_json(stale,"tampered")


if __name__ == "__main__":
    unittest.main()
