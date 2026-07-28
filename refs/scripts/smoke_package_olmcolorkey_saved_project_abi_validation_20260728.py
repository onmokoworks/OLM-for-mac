#!/usr/bin/env python3
"""Smoke the saved-project ABI harness without launching or controlling AE."""

from __future__ import annotations

import importlib.util
import json
import plistlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_olmcolorkey_saved_project_abi_validation_20260728.py"


def load_runner(path: Path):
    spec = importlib.util.spec_from_file_location("saved_project_abi_runner_smoke", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmcolorkey_saved_abi_smoke_") as raw:
        temp = Path(raw)
        support, archive = temp / "support", temp / "request.zip"
        subprocess.run(
            [sys.executable, str(GENERATOR), "--support-dir", str(support), "--output", str(archive)],
            cwd=ROOT, check=True,
        )
        manifest = json.loads((support / "request_manifest.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "request_only_no_abi_exact_claim"
        assert manifest["abi_exact_claim"] is False
        assert [x["role"] for x in manifest["inputs"]] == [
            "windows_saved_distinctive_values", "prefix_mac_saved"
        ]
        assert len(manifest["capture_contract"]["structural_rows"]) == 23
        assert manifest["capture_contract"]["structural_rows"][2] == {
            "ordinal": 3, "symbol": "THRESHOLD_GROUP_START_DISK_ID", "disk_id": 3, "kind": "structural"
        }
        assert manifest["capture_contract"]["structural_rows"][20]["disk_id"] == 1016
        assert manifest["safety"]["launches_ae_by_default"] is False
        assert manifest["verdict_gate"]["execution_supported"] is False
        assert set(manifest["verdict_gate"]["required_for_any_future_claim"]) == {
            "exact_target_process", "per_run_nonce", "exact_plugin_loaded",
            "exact_project_roles_paths_hashes", "fresh_outputs",
            "full_explicit_match_name_value_keyframe_contract", "all_effects_and_cases_validate",
        }
        jsx = (support / "run_saved_project_abi_validation.jsx").read_text(encoding="utf-8")
        for token in ("Execution intentionally disabled", "cannot bind", "FAIL_CLOSED"):
            assert token in jsx, token
        runner_text = (support / "run_saved_project_abi_validation.py").read_text(encoding="utf-8")
        for forbidden in ("osascript", "subprocess", "--execute", "--ae-pid", "abi_exact_claim\": True"):
            assert forbidden not in runner_text, forbidden
        for required in ("run_nonce", "created_utc", "distinct content hashes",
                         "required_return_nonce", "preexisting_result_or_png_accepted",
                         "all effects/cases exact match-name/value/keyframe comparison"):
            assert required in runner_text, required
        win, old = temp / "windows.aep", temp / "prefix_mac.aep"
        win.write_bytes(b"distinctive windows saved project")
        old.write_bytes(b"pre-fix mac saved project")
        bundle = temp / "OLMColorKey.plugin"
        binary = bundle / "Contents/MacOS/OLMColorKey"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"smoke Mach-O")
        with (bundle / "Contents/Info.plist").open("wb") as handle:
            plistlib.dump({"CFBundleExecutable": "OLMColorKey"}, handle)
        runner = load_runner(support / "run_saved_project_abi_validation.py")
        output = temp / "return"
        # Adversarial isolation: if runner ever imports process execution, fail.
        with mock.patch("subprocess.run", side_effect=AssertionError("runner attempted subprocess")):
            rc = runner.main([
                "--windows-saved-project", str(win),
                "--prefix-mac-saved-project", str(old),
                "--plugin-path", str(bundle),
                "--output-dir", str(output),
            ])
        assert rc == 0
        run_dirs = list(output.glob("preflight-*"))
        assert len(run_dirs) == 1
        preflight = json.loads((run_dirs[0] / "preflight.json").read_text(encoding="utf-8"))
        assert preflight["abi_exact_claim"] is False
        assert preflight["status"] == "preflight_only_no_abi_exact_claim"
        assert len(preflight["run_nonce"]) == 32
        assert run_dirs[0].name == "preflight-" + preflight["run_nonce"]
        assert preflight["freshness_policy"]["preexisting_result_or_png_accepted"] is False
        assert preflight["expected_contract"] is None
        assert len(preflight["plugin"]["macho_sha256"]) == 64
        assert len(preflight["plugin"]["bundle_tree_sha256"]) == 64
        assert [p["sha256"] for p in preflight["projects"]]
        try:
            runner.main([
                "--windows-saved-project", str(temp / "missing.aep"),
                "--prefix-mac-saved-project", str(old),
                "--plugin-path", str(bundle),
            ])
        except SystemExit as exc:
            assert "FAIL_CLOSED" in str(exc)
        else:
            raise AssertionError("missing project did not fail closed")
        # Different paths with byte-identical projects are not independent evidence.
        clone = temp / "clone.aep"
        clone.write_bytes(win.read_bytes())
        try:
            runner.main([
                "--windows-saved-project", str(win),
                "--prefix-mac-saved-project", str(clone),
                "--plugin-path", str(bundle),
            ])
        except SystemExit as exc:
            assert "distinct content hashes" in str(exc)
        else:
            raise AssertionError("byte-identical projects were accepted")
        # A partial contract cannot turn ordinal observations into semantic proof.
        bad_contract = temp / "bad-contract.json"
        bad_contract.write_text(json.dumps({
            "schema_version": 1,
            "cases": [
                {"role": "windows_saved_distinctive_values", "effects": [
                    {"selector": {}, "properties": [{"property_index": 1, "match_name": "x"}]}
                ]},
                {"role": "prefix_mac_saved", "effects": []},
            ],
        }), encoding="utf-8")
        try:
            runner.main([
                "--windows-saved-project", str(win),
                "--prefix-mac-saved-project", str(old),
                "--plugin-path", str(bundle),
                "--expected-contract", str(bad_contract),
            ])
        except SystemExit as exc:
            assert "value, and keyframes" in str(exc) or "requires effects" in str(exc)
        else:
            raise AssertionError("partial expected contract was accepted")
        # Unknown execute flags fail argparse before any process dispatch.
        try:
            with mock.patch("subprocess.run", side_effect=AssertionError("dispatch attempted")):
                runner.main([
                    "--windows-saved-project", str(win),
                    "--prefix-mac-saved-project", str(old),
                    "--plugin-path", str(bundle), "--execute",
                ])
        except SystemExit as exc:
            assert exc.code != 0
        else:
            raise AssertionError("removed execute path was accepted")
        with zipfile.ZipFile(archive) as zipped:
            assert set(zipped.namelist()) == {
                "README.md", "request_manifest.json",
                "run_saved_project_abi_validation.jsx", "run_saved_project_abi_validation.py",
            }
    print("[OK] saved-project ABI package smoke passed; osascript forbidden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
