from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
RAW = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_raw_20260813.json"
SUMMARY = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json"

spec = importlib.util.spec_from_file_location("all10_fresh_smoke", RUNNER)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def synthetic() -> tuple[dict, dict]:
    accepted_at = "2026-08-12T08:00:00+00:00"
    started_at = "2026-08-12T08:01:00+00:00"
    captured_at = "2026-08-12T08:02:00+00:00"
    pid = 12345
    manifest = {
        "path": "refs/conformance/olm_installed_identity_manifest_20260806.json",
        "sha256": "a" * 64,
        "accepted_at": accepted_at,
        "accepted_manifest_status": "verified_before_launch",
    }
    raw_plugins = []
    returns = []
    summary_plugins = []
    for index, name in enumerate(runner.EXPECTED_PLUGINS):
        enabled_host = name in runner.ENABLED_HOST_FRAME_PLUGINS
        expectation = "enabled_host_frame_render" if enabled_host else "disabled_host_frame_render"
        executable = f"/installed/{name}.plugin/Contents/MacOS/{name}"
        digest = (name.encode().hex() + "0" * 64)[:64]
        png = {"path": f"handoffs/test/png/{name}.png", "sha256": f"{index + 1:064x}", "size": 1, "fresh_after_launch": True}
        raw_plugins.append({
            "plugin": name,
            "ae_pid": pid,
            "executable_path": executable,
            "loaded_module_count": 1,
            "post_render_mapping_exact": True,
            "accepted_executable_sha256": digest,
            "pre_launch_executable_sha256": digest,
            "post_render_on_disk_sha256": digest,
            "installed_hash_unchanged": True,
            "png": png,
        })
        returns.append({
            "plugin": name,
            "loaded": True,
            "applied": True,
            "effect_can_enable_after_add": True,
            "effect_enabled_during_render": enabled_host,
            "effect_enabled_host_frame_attempted": enabled_host,
            "effect_enabled_host_frame_succeeded": enabled_host,
            "host_smoke_expectation": expectation,
            "numerical_render_expected": False,
            "numerical_render_supported": False,
            "numerical_render_attempted": False,
            "effect_enabled_numerical_render_attempted": False,
            "numerical_render_succeeded": None,
            "host_frame_render_succeeded": True,
            "effect_disabled_during_host_frame": not enabled_host,
            "render_succeeded": True,
        })
        summary_plugins.append({
            "plugin": name,
            "status": "pass",
            "loaded": True,
            "applied": True,
            "render_succeeded": True,
            "host_frame_render_succeeded": True,
            "host_smoke_expectation": expectation,
            "effect_enabled_host_frame_attempted": enabled_host,
            "effect_enabled_host_frame_succeeded": enabled_host,
            "numerical_render_expected": False,
            "numerical_render_supported": False,
            "effect_enabled_numerical_render_attempted": False,
            "numerical_render_succeeded": None,
            "effect_disabled_during_host_frame": not enabled_host,
            "ae_pid": pid,
            "loaded_module_path": executable,
            "loaded_module_count": 1,
            "post_render_mapping_exact": True,
            "accepted_executable_sha256": digest,
            "post_render_on_disk_sha256": digest,
            "png": png,
        })
    raw = {
        "schema": "olm.all10-current-install-fresh-ae-smoke-raw/1",
        "status": "pass",
        "installed_identity_manifest": manifest,
        "host": {
            "pid": pid,
            "started_at": started_at,
            "captured_at": captured_at,
            "initial_ae_pids": [],
            "initial_process_count": 0,
            "process_exit_returncode": 0,
            "script_invocation": {"returncode": 0},
        },
        "vmmap": {"captured_at": captured_at, "returncode": 0},
        "ae_return": {
            "schema": "olm.all10-fresh-ae-host-return/1",
            "status": "ok",
            "ae_version": "26.3x87",
            "project": {"renderer": "SOFTWARE", "renderer_raw": 1816},
            "plugins": returns,
        },
        "plugins": raw_plugins,
        "cleanup": {"owned_pids": [pid], "remaining_owned_pids": [], "remaining_ae_pids": []},
        "claim_boundary": runner.CLAIM_BOUNDARY,
    }
    summary = {
        "schema": "olm.all10-current-install-fresh-ae-smoke/1",
        "status": "pass",
        "passed": True,
        "installed_identity_manifest": manifest,
        "host": {
            "initial_process_count": 0,
            "process_count": 1,
            "fresh_process": True,
            "started_after_identity_acceptance": True,
            "pid": pid,
            "started_at": started_at,
            "captured_at": captured_at,
            "renderer": "SOFTWARE",
            "renderer_raw": 1816,
            "quit_succeeded": True,
            "residual_process_count": 0,
        },
        "plugins": summary_plugins,
        "claim_boundary": runner.CLAIM_BOUNDARY,
    }
    return summary, raw


class All10FreshSmokeContractTests(unittest.TestCase):
    def test_payload_is_effect_enabled_fresh_png_and_software_fail_closed(self) -> None:
        text = PAYLOAD.read_text(encoding="utf-8")
        self.assertEqual(text.count('plugin: "'), 10)
        self.assertIn("project.gpuAccelType = GpuAccelType.SOFTWARE", text)
        self.assertIn("effect.enabled = true", text)
        self.assertIn("effect_enabled_during_render", text)
        self.assertIn("removeStale(png)", text)
        self.assertIn("comp.saveFrameToPng(0.0, png)", text)
        self.assertIn("PNG is older than this host payload", text)
        self.assertIn("waitForFile(ack, 720, 250)", text)
        self.assertIn("No pixel-exact, Windows-equivalence, typed-plane, padding", text)

    def test_runner_binds_fresh_pid_vmmap_identity_and_cleanup(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        for token in (
            "verify_identity()",
            "process_started_at(pid)",
            "capture_vmmap(pid, vmmap_path)",
            'parsed_map["exact"]',
            'sha256(IDENTITY) == identity_digest',
            'stop_owned_ae(owned)',
            '"remaining_ae_pids": ae_pids()',
        ):
            self.assertIn(token, text)
        self.assertNotIn("rm -rf", text)
        self.assertNotIn("killall", text)

    def test_semantic_validator_rejects_tampering(self) -> None:
        summary, raw = synthetic()
        self.assertTrue(runner.validate_summary_data(summary, raw))
        mutations = []
        for path, value in (
            (("host", "pid"), 54321),
            (("host", "renderer"), "METAL"),
            (("host", "started_at"), "2026-08-12T07:59:00+00:00"),
            (("host", "residual_process_count"), 1),
            (("plugins", 0, "loaded_module_count"), 2),
            (("plugins", 0, "post_render_mapping_exact"), False),
            (("plugins", 0, "post_render_on_disk_sha256"), "f" * 64),
            (("plugins", 0, "render_succeeded"), False),
        ):
            mutated = copy.deepcopy(summary)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            mutations.append(mutated)
        duplicate = copy.deepcopy(summary)
        duplicate["plugins"][1]["plugin"] = duplicate["plugins"][0]["plugin"]
        mutations.append(duplicate)
        duplicate_png = copy.deepcopy(summary)
        duplicate_png["plugins"][1]["png"]["path"] = duplicate_png["plugins"][0]["png"]["path"]
        mutations.append(duplicate_png)
        for mutated in mutations:
            self.assertFalse(runner.validate_summary_data(mutated, raw))
        raw_mutations = []
        for path, value in (
            (("schema",), "evil"),
            (("ae_return", "status"), "fail_closed"),
            (("ae_return", "project", "renderer"), "METAL"),
            (("ae_return", "plugins", 0, "effect_enabled_during_render"), False),
            (("ae_return", "plugins", 1, "effect_enabled_during_render"), True),
            (("ae_return", "plugins", 1, "effect_disabled_during_host_frame"), False),
            (("ae_return", "plugins", 1, "effect_enabled_numerical_render_attempted"), True),
            (("ae_return", "plugins", 1, "numerical_render_supported"), True),
            (("plugins", 0, "pre_launch_executable_sha256"), "e" * 64),
            (("host", "script_invocation", "returncode"), 9),
            (("vmmap", "returncode"), 9),
            (("claim_boundary",), "expanded claim"),
        ):
            mutated = copy.deepcopy(raw)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            raw_mutations.append(mutated)
        for mutated in raw_mutations:
            self.assertFalse(runner.validate_summary_data(summary, mutated))
        duplicate_raw_png = copy.deepcopy(raw)
        duplicate_raw_png["plugins"][1]["png"]["path"] = duplicate_raw_png["plugins"][0]["png"]["path"]
        self.assertFalse(runner.validate_summary_data(summary, duplicate_raw_png))

    def test_vmmap_parser_rejects_competing_same_name_path(self) -> None:
        executable = Path("/expected/OLMBlur.plugin/Contents/MacOS/OLMBlur")
        base = "Process: After Effects [12345]\nCode Type: ARM64\n"
        exact = base + (
            "__TEXT 1000-2000 [ 4K] r-x/rwx SM=COW          "
            "/expected/OLMBlur.plugin/Contents/MacOS/OLMBlur\n"
        )
        parsed = runner.parse_vmmap_identity(exact, 12345, executable)
        self.assertTrue(parsed["exact"])
        conflict = exact + "__TEXT  /other/OLMBlur.plugin/Contents/MacOS/OLMBlur\n"
        self.assertFalse(runner.parse_vmmap_identity(conflict, 12345, executable)["exact"])
        self.assertFalse(runner.parse_vmmap_identity(exact, 99999, executable)["exact"])
        translated = exact.replace("Code Type: ARM64", "Code Type: X86-64 (Translated)")
        self.assertFalse(runner.parse_vmmap_identity(translated, 12345, executable)["exact"])

    def test_current_persisted_artifacts_validate_when_present(self) -> None:
        if not (RAW.is_file() and SUMMARY.is_file()):
            self.skipTest("fresh AE artifacts have not been captured yet")
        raw = json.loads(RAW.read_text(encoding="utf-8"))
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        self.assertTrue(runner.validate_persisted_summary(summary, raw, RAW))
        producer = copy.deepcopy(summary)
        producer["producer_runner"]["sha256"] = "0" * 64
        self.assertFalse(runner.validate_persisted_summary(producer, raw, RAW))
        validator = copy.deepcopy(summary)
        validator["validator_runner"]["sha256"] = "0" * 64
        self.assertFalse(runner.validate_persisted_summary(validator, raw, RAW))
        receipt = copy.deepcopy(summary)
        receipt["artifacts"]["invocation_receipt"]["sha256"] = "0" * 64
        self.assertFalse(runner.validate_persisted_summary(receipt, raw, RAW))


if __name__ == "__main__":
    unittest.main()
