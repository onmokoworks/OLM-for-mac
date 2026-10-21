#!/usr/bin/env python3
"""Validate and preserve the no-retry Batch5 v3 AE one-shot failure."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_raw_20260815.json"
SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_20260815.json"
RECEIPT = ROOT / "handoffs/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_20260815.invocation-receipt.json"
ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_20260815"
WRAPPER = ARTIFACT_DIR / "launch.jsx"
EXCERPT = ARTIFACT_DIR / "plugin_loading_excerpt_lines255_336.txt"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_one_shot_failure_metadata_20260815.json"
MARKDOWN = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_one_shot_failure_metadata_20260815.md"
LIVE_LOG = Path.home() / "Library/Preferences/Adobe/After Effects/26.3/Plugin Loading.log"

PINS = {
    "raw": "4e9013563b5562afdcd2467e058e11775c0cb1355029108be334c13fc23075f0",
    "summary": "7c307f7fa741691d783ce48d48a7f40b5bc42dd7a03747f2fcfb01d351f130a0",
    "receipt": "ff843ef668b4494e61a7e09b05b0ac739d7ff5574f45a2fe494cacf8162617e4",
    "wrapper": "94355c2fb64e366eb20077207d48b7abb5adab0fceb83b1e73462a3f9b56df1c",
    "excerpt": "f5836c3fc4fd94f677a5b4c6ce0aa96e91be6cc34304db1080f1562e5ee16874",
    "identity": "ede4857b810e9f2901561ee8a3a9179c4c508dc2ee058525aa3f46dff4164079",
    "live_log": "25b76bfe1b731955658b949e50cde9b50b7a76b8e770b635d8e63d6b8984d40a",
}
PLUGINS = [
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def artifact(path: Path, pin: str) -> dict:
    assert path.is_file(), path
    actual = sha256(path)
    assert actual == pin, (path, actual, pin)
    return {"path": str(path.relative_to(ROOT)), "sha256": actual, "size": path.stat().st_size}


def validate_excerpt(text: str) -> None:
    ignored = re.findall(
        r"Loading /Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7\.0/MediaCore/([^/]+)\.plugin\n"
        r"The modification date has changed so the plugin will be loaded from disk\.\n"
        r"Loading from disk\.\.\.\n"
        r"No loaders recognized this plugin, so the plugin is set to Ignore\.",
        text,
    )
    assert ignored == sorted(PLUGINS), ignored
    for plugin in PLUGINS:
        assert text.count(f"PluginNameList::AddFilePath - added /Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/{plugin}.plugin") == 1
        assert text.count(f"LoadPluginList - sorted /Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/{plugin}.plugin") == 1


def build_report(require_live_log: bool = False) -> dict:
    files = {
        "raw": artifact(RAW, PINS["raw"]),
        "summary": artifact(SUMMARY, PINS["summary"]),
        "invocation_receipt": artifact(RECEIPT, PINS["receipt"]),
        "launch_wrapper": artifact(WRAPPER, PINS["wrapper"]),
        "plugin_loading_excerpt": artifact(EXCERPT, PINS["excerpt"]),
    }
    assert sha256(IDENTITY) == PINS["identity"]
    raw = json.loads(RAW.read_text())
    summary = json.loads(SUMMARY.read_text())
    receipt = json.loads(RECEIPT.read_text())
    excerpt = EXCERPT.read_text()
    validate_excerpt(excerpt)

    assert raw["status"] == "fail_closed" and raw["passed"] is False
    assert raw["plugins"] == []
    assert raw["error"] == {"type": "ValueError", "message": "DoScriptFile exited before AE return: rc=0 stderr='' stdout='1\\n'"}
    host = raw["host"]
    assert host["initial_ae_pids"] == [] and host["launch_process_pid"] == 51752
    assert host["script_invocation_pid"] == 51766
    assert host["scriptability_samples"] == [{
        "sampled_at": "2026-08-15T11:50:29.858837+00:00",
        "returncode": 0, "stderr": "", "stdout": "26.3.0",
    }]
    assert raw["cleanup"]["remaining_ae_pids"] == []
    assert raw["cleanup"]["remaining_owned_pids"] == []
    assert raw["cleanup"]["owned_pids"] == [51752]
    assert [x["action"] for x in raw["cleanup"]["actions"]] == ["application_quit", "SIGTERM", "SIGKILL"]
    assert summary["raw_report"]["sha256"] == PINS["raw"]
    assert summary["status"] == "fail_closed" and summary["passed"] is False
    assert [x["plugin"] for x in summary["plugins"]] == PLUGINS
    assert all(x["status"] == "fail_closed" and not x["loaded"] and not x["applied"] for x in summary["plugins"])
    assert receipt == {"created_at": "2026-08-15T11:50:29.480380+00:00", "schema": "olm.all10-fresh-ae-invocation-receipt/1"}
    assert iso(receipt["created_at"]) < iso(raw["host"]["launch_requested_at"]) < iso(raw["cleanup"]["completed_at"])
    assert raw["installed_identity_manifest"]["sha256"] == PINS["identity"]
    assert summary["installed_identity_manifest"]["sha256"] == PINS["identity"]
    wrapper = WRAPPER.read_text()
    assert wrapper.count('$.evalFile(new File(') == 1
    assert 'OLM_ALL10_AE_RUN_NONCE", "f4ba19832fa8a94d0654b64606ba63c4"' in wrapper
    assert str(ARTIFACT_DIR / "ae_return.json") in wrapper
    assert str(ROOT / "scripts/ae_host_all10_batch5_current_identity_live_v3_20260815.jsx") in wrapper
    forbidden = [ARTIFACT_DIR / "ae_return.json", ARTIFACT_DIR / "vmmap_captured.ack"]
    assert all(not p.exists() for p in forbidden), forbidden
    assert (ARTIFACT_DIR / "png").is_dir()
    assert list((ARTIFACT_DIR / "png").iterdir()) == []
    assert sorted(p.name for p in ARTIFACT_DIR.iterdir()) == ["launch.jsx", "plugin_loading_excerpt_lines255_336.txt", "png"]

    log_meta = {
        "original_path": str(LIVE_LOG),
        "original_sha256_at_capture": PINS["live_log"],
        "original_size_at_capture": 333236,
        "original_birthtime_local": "2026-08-15T21:05:10+0900",
        "original_mtime_local": "2026-08-15T21:05:15+0900",
        "captured_line_range": [255, 336],
        "excerpt": files["plugin_loading_excerpt"],
    }
    if require_live_log:
        assert sha256(LIVE_LOG) == PINS["live_log"]
        assert LIVE_LOG.stat().st_size == 333236
        lines = LIVE_LOG.read_text(errors="replace").splitlines(keepends=True)
        assert "".join(lines[254:336]) == excerpt

    return {
        "schema": "olm.all10-batch5-current-identity-v3-one-shot-failure-metadata/1",
        "status": "FAIL_CLOSED_NO_RETRY",
        "attempt": {
            "one_shot": True,
            "retry_authorized": False,
            "owned_after_effects_pid": 51752,
            "script_invocation_pid": 51766,
            "scriptability_probe_succeeded": True,
            "doscriptfile_returncode": 0,
            "doscriptfile_stdout": "1\n",
            "nonce_bound_ae_return_created": False,
            "pngs_created": 0,
            "raw_plugin_rows": 0,
        },
        "artifacts": files,
        "installed_identity": {
            "manifest_path": str(IDENTITY.relative_to(ROOT)),
            "manifest_sha256": PINS["identity"],
            "unchanged_after_failure": True,
        },
        "cleanup": {
            "owned_pid": 51752,
            "exact_term_then_kill": True,
            "remaining_owned_pids": [],
            "remaining_ae_pids": [],
            "broad_kill_used": False,
        },
        "host_breadcrumb": {
            **log_meta,
            "all10_discovered": True,
            "all10_load_from_disk_attempted": True,
            "all10_no_loader_recognized_and_ignored": True,
            "plugins": sorted(PLUGINS),
        },
        "classification": {
            "persisted_protocol_failure": "host_script_dispatch_or_payload_bootstrap_failure_before_nonce_bound_return",
            "independent_startup_breadcrumb": "all10_plugin_loader_recognition_failure_before_any_observed_effect_add_or_render_result",
            "plugin_specific_runtime_observation_available": False,
            "effect_add_attempted": None,
            "render_attempted": None,
            "numerical_behavior_assessed": False,
            "explanation": "AE answered the version probe and DoScriptFile returned rc=0/stdout 1, but no nonce-bound ae_return was written. The separate startup log shows every exact10 bundle was scanned, attempted from disk, then ignored because no loader recognized it. The two facts do not prove that the payload reached any plugin-specific stage.",
        },
        "claim_boundary": "Preserves one Batch5 v3 invocation and read-only startup-log evidence. It proves fail-closed host protocol plus all10 loader non-recognition for this launch; it proves no observed effect-add, render, host-frame, numerical, or plugin-crash result and authorizes no retry. Whether the unreturned payload attempted effect add or render is not observed.",
    }


def validate_report(report: dict) -> None:
    expected = build_report(False)
    assert report == expected


def markdown(report: dict) -> str:
    return f"""# Batch5 current-identity v3 one-shot failure metadata

Status: `{report['status']}`. Retry is not authorized.

The fresh AE process answered the version probe (`26.3.0`). `DoScriptFile` then exited with return code 0 and stdout `1`, but the nonce-bound `ae_return.json` was never created. The raw report therefore contains zero plugin observations; the summary's ten `fail_closed` rows are placeholders, not effect-load or render results.

A read-only startup breadcrumb adds a separate, earlier finding. `Plugin Loading.log` was born at 21:05:10 JST and modified at 21:05:15 JST, inside this attempt's 20:50:29–21:07:20 JST process window. Lines 255–336 enumerate the exact ten installed bundles. For each bundle AE records `Loading from disk...` followed by `No loaders recognized this plugin, so the plugin is set to Ignore.` The exact excerpt is frozen and SHA-bound by the adjacent JSON.

Classification: the persisted one-shot protocol failed at host script dispatch or payload bootstrap before its nonce-bound return. Independently, AE startup failed to recognize a loader for all ten bundles before any observed effect-add or render result. Whether the unreturned payload attempted effect add or render is unknown. There is no evidence that the payload reached a plugin-specific stage, no host-frame or numerical result, and no evidence of a plugin-originated crash.

Cleanup was limited to owned PID 51752 (exact SIGTERM then SIGKILL after application quit returned -128). The raw cleanup record has no remaining owned or AE PIDs. Installed identity remains `{PINS['identity']}`. No retry, install, source, identity, or release action was performed.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        report = build_report(True)
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        MARKDOWN.write_text(markdown(report))
    else:
        validate_report(json.loads(REPORT.read_text()))
        assert MARKDOWN.read_text() == markdown(build_report(False))
    print("PASS: Batch5 v3 one-shot failure is preserved, classified, and no-retry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
