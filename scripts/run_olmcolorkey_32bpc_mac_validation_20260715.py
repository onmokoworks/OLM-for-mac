#!/usr/bin/env python3
"""Run the packaged Mac AE validation request and verify its return."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from package_olmcolorkey_32bpc_mac_validation_20260715 import REQUEST_INDEX, STEM, build


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(result_path: Path, expected_cases: list[dict], output_dir: Path) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("kind") != "olmcolorkey_32bpc_mac_validation_return": raise ValueError("wrong return kind")
    if result.get("ae_exact_claim") is not False: raise ValueError("return must explicitly forbid AE exact")
    if result.get("project") != {"bits_per_channel": 32, "working_space": "None", "linear_blending": False, "renderer": "SOFTWARE"}: raise ValueError("project contract drift")
    if result.get("output_module", {}).get("template_name") != "OLM EXR 32 Float": raise ValueError("output template drift")
    if result.get("output_module", {}).get("capture_api") != "OutputModule.getSettings(GetSettingsFormat.STRING)": raise ValueError("settings API drift")
    returned = result.get("cases")
    if not isinstance(returned, list) or [c.get("id") for c in returned] != [c["id"] for c in expected_cases]: raise ValueError("case set/order mismatch")
    for case in returned:
        plugin = case.get("plugin", {})
        if plugin.get("filename") != "OLMColorKey.plugin" or len(plugin.get("sha256", "")) != 64: raise ValueError(f"plugin identity missing: {case.get('id')}")
        if case.get("no_effect_control_passed") is not True: raise ValueError(f"control not passed: {case.get('id')}")
        outputs = case.get("outputs", {})
        settings_hashes = []
        for branch in ("no_effect", "effect_on"):
            item = outputs.get(branch, {})
            path = output_dir / Path(item.get("path", "")).name
            if path.suffix.lower() != ".exr" or not path.exists(): raise ValueError(f"missing FLOAT EXR: {case.get('id')} {branch}")
            if item.get("sha256") != digest(path): raise ValueError(f"output hash mismatch: {path.name}")
            settings = item.get("output_module_settings", {})
            settings_path = output_dir / Path(settings.get("path", "")).name
            if not settings_path.exists() or len(settings.get("sha256", "")) != 64 or settings["sha256"] != digest(settings_path): raise ValueError(f"settings hash missing: {case.get('id')} {branch}")
            settings_hashes.append(settings["sha256"])
        if settings_hashes[0] != settings_hashes[1]: raise ValueError(f"settings differ: {case.get('id')}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-path", type=Path, required=True)
    parser.add_argument("--support-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--result-json", type=Path, default=None)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--dump-js", type=Path, default=None)
    args = parser.parse_args()
    if args.plugin_path.name != "OLMColorKey.plugin" or not args.plugin_path.exists():
        print("[FAIL_CLOSED] --plugin-path must name an existing OLMColorKey.plugin", file=sys.stderr); return 2
    support = args.support_dir or Path(tempfile.mkdtemp(prefix=STEM + "_"))
    output_dir = (args.output_dir or (support / "return")).resolve(); output_dir.mkdir(parents=True, exist_ok=True)
    result_json = (args.result_json or (output_dir / "mac_validation_return.json")).resolve()
    build(Path(support / f"{STEM}.zip"), support)
    if not REQUEST_INDEX.exists():
        print("[FAIL_CLOSED] Mac request index is missing", file=sys.stderr); return 1
    request = json.loads((support / "request_manifest.json").read_text(encoding="utf-8"))
    cases = request["cases"]
    jsx = support / "run_mac_olmcolorkey_32bpc_validation.jsx"
    wrapper = support / "run_mac_wrapper.jsx"
    expected_plugin_hash = digest(args.plugin_path)
    env = {"OLM_AE_MAC_INPUT_DIR": str((support / "input").resolve()), "OLM_AE_MAC_OUTPUT_DIR": str(output_dir), "OLM_AE_MAC_RESULT_JSON": str(result_json), "OLM_AE_MAC_PLUGIN_PATH": str(args.plugin_path.resolve()), "OLM_AE_MAC_PLUGIN_SHA256": expected_plugin_hash}
    lines = [f"$.setenv({json.dumps(k)}, {json.dumps(v)});" for k, v in env.items()]
    lines.append(f"$.evalFile(new File({json.dumps(str(jsx.resolve()))}));")
    wrapper.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if args.dump_js:
        args.dump_js.write_text(wrapper.read_text(encoding="utf-8"), encoding="utf-8"); print(f"[OK] wrote {args.dump_js}"); return 0
    script = f'tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n'
    proc = subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=args.timeout + 30)
    if proc.returncode != 0 or not result_json.exists():
        print("[FAIL_CLOSED] AE did not produce a return", file=sys.stderr); return 1
    try: result = verify(result_json, cases, output_dir)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL_CLOSED] {exc}", file=sys.stderr); return 1
    expected_plugin_hash = digest(args.plugin_path)
    if result.get("plugin", {}).get("sha256") != expected_plugin_hash or result.get("plugin", {}).get("expected_sha256") != expected_plugin_hash:
        print("[FAIL_CLOSED] returned plugin hash does not match --plugin-path", file=sys.stderr); return 1
    report = {"kind": "olmcolorkey_32bpc_mac_validation_report", "status": "candidate_return_verified", "ae_exact_claim": False, "case_count": len(result["cases"]), "result_json": str(result_json), "next_gate": "compare Mac and Windows raw FLOAT EXR samples"}
    report_path = output_dir / "validation_report.json"; report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] verified candidate return: {report_path}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
