#!/usr/bin/env python3
"""Smoke the bounded OLMSmoother2 in-process collector package contract."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/package_windows_witness_olmsmoother2_inprocess_collector_20260716.py"
COLLECTOR_SOURCE = ROOT / "tools/windows_witness/collectors/smoother2/smoother2_collector.cpp"
REQUEST_ID = "olmsmoother2_legacy_upstream_classplane_inprocess_20260716"
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
PLUGIN_SHA = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
EXPECTED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
EXPECTED_PROBES = [
    {"name": "writer_anchor", "rva": "0x350b"},
    {"name": "c280_entry", "rva": "0xc280"},
    {"name": "cardinal_10760", "rva": "0x10760"},
    {"name": "d3b0_entry", "rva": "0xd3b0"},
    {"name": "da50_entry", "rva": "0xda50"},
    {"name": "fef0_entry", "rva": "0xfef0"},
    {"name": "e170_entry", "rva": "0xe170", "return_rva": "0xf284"},
    {"name": "e170_return", "rva": "0xf284"},
    {"name": "f270_entry", "rva": "0xf270", "return_rva": "0xff5b"},
    {"name": "f270_return", "rva": "0xff5b"},
    {"name": "e3a0_entry", "rva": "0xe3a0", "return_rva": "0xff5b"},
    {"name": "e3a0_return0", "rva": "0xe3f4"},
    {"name": "e3a0_return1", "rva": "0xe420"},
]
PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_placeholders(text: str) -> dict[str, object]:
    require(set(PLACEHOLDER_RE.findall(text)) == {"RUN_ID", "AE_PID", "CASE_ID", "OUTPUT_DIR"}, "unexpected config placeholders")
    rendered = (
        text.replace("{{RUN_ID}}", "smoke-run")
        .replace("{{AE_PID}}", "7312")
        .replace("{{CASE_ID}}", CASE_ID)
        .replace("{{OUTPUT_DIR}}", "C:/tmp/collector-output")
    )
    return json.loads(rendered)


def main() -> int:
    collector_source = COLLECTOR_SOURCE.read_text(encoding="utf-8")
    for token in (
        '"c280_entry"', '"cardinal_10760"', '"d3b0_entry"', '"da50_entry"', '"fef0_entry"',
        '0xc280', '0x10760', '0xd3b0', '0xda50', '0xfef0',
        "index_inputs=unavailable", "input_third=unavailable", "upstream origin/descriptor witness incomplete",
    ):
        require(token in collector_source, f"collector lost upstream witness contract: {token}")
    require("(observation.descriptor[2] - 1) + observation.descriptor[5] * 10" in collector_source, "fef0 dispatch key derivation drifted")
    require("InterlockedCompareExchange(&g_upstream_c280, 0, 0) == 1 && InterlockedCompareExchange(&g_upstream_10760, 1, 0) == 0" in collector_source, "10760 is no longer ordered after c280")
    require("InterlockedCompareExchange(&g_upstream_10760, 0, 0) == 1" in collector_source, "scanner probes are no longer ordered after 10760")
    require("InterlockedCompareExchange(&g_upstream_d3b0, 0, 0) == 1 && InterlockedCompareExchange(&g_upstream_da50, 1, 0) == 0" in collector_source, "da50 is no longer ordered after d3b0")
    require("InterlockedCompareExchange(&g_upstream_da50, 0, 0) == 1 && InterlockedCompareExchange(&g_upstream_fef0, 1, 0) == 0" in collector_source, "fef0 is no longer ordered after da50")
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_inprocess_pkg_") as raw:
        temp = Path(raw)
        injector = temp / "real_injector.exe"
        collector = temp / "real_collector.dll"
        injector.write_bytes(b"MZ placeholder injector\n")
        collector.write_bytes(b"MZ placeholder collector\n")

        package_a = temp / "package-a"
        zip_a = temp / "package-a.zip"
        package_b = temp / "package-b"
        zip_b = temp / "package-b.zip"
        for output_dir, archive in ((package_a, zip_a), (package_b, zip_b)):
            completed = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--injector",
                    str(injector),
                    "--collector-dll",
                    str(collector),
                    "--output-dir",
                    str(output_dir),
                    "--zip",
                    str(archive),
                ]
            )
            require(completed.returncode == 0, completed.stderr or completed.stdout)
            payload = json.loads(completed.stdout)
            require(payload["status"] == "ok", "packager did not report success")
            require(payload["request_id"] == REQUEST_ID, "wrong request_id in packager output")
            require(payload["transport"] == "in_process_collector", "wrong transport in packager output")

        require(zip_a.read_bytes() == zip_b.read_bytes(), "collector package zip is not deterministic")

        contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        manifest = json.loads((package_a / "package-manifest.json").read_text(encoding="utf-8"))
        request_manifest = json.loads((package_a / "request/request_manifest.json").read_text(encoding="utf-8"))
        config_text = (package_a / "collector/config.json.in").read_text(encoding="ascii")
        readme = (package_a / "README.md").read_text(encoding="utf-8")
        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        inventory_paths = [item["path"] for item in manifest["files"]]

        require(contract["request_id"] == REQUEST_ID, "contract request_id mismatch")
        require(contract["contract_kind"] == "windows_ae_collector_witness_m0", "wrong collector contract kind")
        require(contract["plugin"]["aex_sha256"] == PLUGIN_SHA, "plugin SHA mismatch")
        require(contract["transport"] == {
            "kind": "in_process_collector",
            "injector_path": "olm_injector.exe",
            "collector_dll": "olm_smoother2_collector.dll",
            "config_template": "collector-config.json.in",
            "required_outputs": ["collector_trace.txt", "collector_status.json", "collector.jsonl"],
            "arm_timeout_seconds": 30,
            "capture_timeout_seconds": 300,
            "package_injector_path": "collector/injector.exe",
            "package_collector_dll": "collector/collector.dll",
            "package_config_template": "collector/config.json.in",
        }, "transport contract drifted")
        require("cdb" not in contract, "collector contract must not expose cdb transport")
        require(contract["cases"][0]["id"] == CASE_ID, "wrong case id")
        require("package_cdb_template" not in contract["cases"][0], "collector case should not include a packaged cdb template")
        require(request_manifest["request_id"] == REQUEST_ID, "request manifest request_id was not rewritten structurally")
        require(manifest["queue"]["profile"] == "olmsmoother2-legacy-upstream-classplane-inprocess", "queue profile mismatch")
        require("bounded same-bitness collector" in manifest["queue"]["command"], "queue command lost collector wording")
        require("collector armed/ok status" in manifest["queue"]["stop_condition"], "queue stop condition lost collector lifecycle wording")
        require("c280/cardinal6/d3b0/da50/fef0" in manifest["queue"]["stop_condition"], "queue stop condition lost upstream witness stages")
        require("do not claim Windows executability" in contract["description"], "description lost host limitation wording")
        require((package_a / "request/HOST_LIMITATION.md").is_file(), "host limitation asset missing")
        require((package_a / "request/input/case_0012_before_effects.png").is_file(), "input asset missing")
        require((package_a / "collector/injector.exe").read_bytes() == injector.read_bytes(), "injector bytes drifted")
        require((package_a / "collector/collector.dll").read_bytes() == collector.read_bytes(), "collector DLL bytes drifted")

        rendered = build_placeholders(config_text)
        require(rendered == {
            "run_id": "smoke-run",
            "ae_pid": 7312,
            "case_id": CASE_ID,
            "project_bpc": 8,
            "renderer": "Software",
            "module": "OLMSmoother2.aex",
            "sha256": PLUGIN_SHA,
            "output_dir": "C:/tmp/collector-output",
            "target_x": 91,
            "target_y": 841,
            "timeout_ms": 300000,
            "probes": EXPECTED_PROBES,
        }, "collector config template drifted")

        require("CDB" not in config_text, "collector config should not mention CDB")
        require("injects the configured collector into the exact AE PID" in readme, "package README lost collector runtime wording")
        require("exact_bind_failure" in readme, "package README lost fail-closed wording")
        for token in (
            "collector_status.json",
            "collector_trace.txt",
            "Wait-CollectorStatus $collectorStatusPath 'armed'",
            "Read-CollectorStatus $collectorStatusPath 'ok'",
            "Validate-CollectorOutputs",
            "collector output missing",
        ):
            require(token in launcher, f"launcher lost collector lifecycle text: {token}")

        require("collector/config.json.in" in inventory_paths, "config template missing from package manifest")
        require("collector/injector.exe" in inventory_paths, "injector missing from package manifest")
        require("collector/collector.dll" in inventory_paths, "collector DLL missing from package manifest")
        require(not any(path.endswith(".cdb.in") for path in inventory_paths), "collector package should not contain CDB templates")
        require(manifest["request_id"] == REQUEST_ID, "manifest request_id mismatch")
        require(manifest["contract"] == "witness-contract.json", "manifest contract path mismatch")
        require(manifest["entrypoint"] == "artifacts/run_witness.ps1", "manifest entrypoint mismatch")
        require(inventory_paths == sorted(inventory_paths), "package manifest inventory is not sorted")

        with zipfile.ZipFile(zip_a) as archive:
            require(archive.namelist() == sorted(archive.namelist()), "zip inventory is not sorted")
            require(all(info.date_time == EXPECTED_ZIP_TIME for info in archive.infolist()), "zip timestamps are not deterministic")
            require("collector/config.json.in" in archive.namelist(), "zip missing collector config")
            require("collector/injector.exe" in archive.namelist(), "zip missing injector")
            require("collector/collector.dll" in archive.namelist(), "zip missing collector DLL")
            require(all(not name.endswith(".cdb.in") for name in archive.namelist()), "zip should not contain CDB templates")

        missing = run(
            [
                sys.executable,
                str(SCRIPT),
                "--injector",
                str(temp / "missing.exe"),
                "--collector-dll",
                str(collector),
                "--output-dir",
                str(temp / "missing-package"),
                "--zip",
                str(temp / "missing-package.zip"),
            ]
        )
        require(missing.returncode != 0, "missing injector should fail closed")
        require("injector is missing" in missing.stderr, "missing injector error text drifted")

        empty_injector = temp / "empty.exe"
        empty_injector.write_bytes(b"")
        empty = run(
            [
                sys.executable,
                str(SCRIPT),
                "--injector",
                str(empty_injector),
                "--collector-dll",
                str(collector),
                "--output-dir",
                str(temp / "empty-package"),
                "--zip",
                str(temp / "empty-package.zip"),
            ]
        )
        require(empty.returncode != 0, "empty injector should fail closed")
        require("must be a non-empty file" in empty.stderr, "empty injector error text drifted")

        wrong_ext = temp / "collector.txt"
        wrong_ext.write_bytes(b"not a dll")
        wrong = run(
            [
                sys.executable,
                str(SCRIPT),
                "--injector",
                str(injector),
                "--collector-dll",
                str(wrong_ext),
                "--output-dir",
                str(temp / "wrong-package"),
                "--zip",
                str(temp / "wrong-package.zip"),
            ]
        )
        require(wrong.returncode != 0, "wrong DLL extension should fail closed")
        require("collector DLL must use the .dll extension" in wrong.stderr, "wrong DLL extension error text drifted")

    print("[OK] OLMSmoother2 in-process collector package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
