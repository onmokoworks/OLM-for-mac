#!/usr/bin/env python3
"""Run or validate the isolated Mac ToonDilate 32bpc request."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (Path(__file__).resolve().parent if Path(__file__).resolve().parent.name == "olmtoondilate_mac_32bpc_validation_20260715"
           else ROOT / "refs/runtime_trace_packages/olmtoondilate_mac_32bpc_validation_20260715")
_here = Path(__file__).resolve().parent
_helper = _here if _here.name == "olmtoondilate_mac_32bpc_validation_20260715" else ROOT / "runtime_trace_packages/olmtoondilate_mac_32bpc_validation_20260715"
sys.path.insert(0, str(_helper))
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr
PLUGIN_SHA = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def fail(message): raise SystemExit("FAIL CLOSED: " + message)

def verify_output(path, expected_dimensions=(64, 64)):
    try:
        return inspect_float_rgba_exr(path, expected_dimensions=expected_dimensions)
    except (OSError, ValueError, VerificationError) as exc:
        fail(f"invalid uncompressed FLOAT RGBA EXR: {exc}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--package", type=Path, default=PACKAGE)
    p.add_argument("--execute", action="store_true", help="explicitly invoke AE on macOS")
    p.add_argument("--ae-app", default="Adobe After Effects 2025")
    p.add_argument("--plugin-binary", type=Path)
    p.add_argument("--windows-return", type=Path)
    args = p.parse_args(); package = args.package.resolve(); request = read(package / "request_manifest.json")
    if request["case"]["plugin"]["sha256"] != PLUGIN_SHA: fail("request plugin hash drifted")
    fixture = package / "fixture/ae_generate_32bpc_olmtoondilate_fixture.jsx"
    if not fixture.is_file(): fail("fixture missing")
    output_dir = package / "mac_run"; output_dir.mkdir(exist_ok=True)
    report = {"kind": "olmtoondilate_mac_32bpc_validation_report", "schema": 1, "status": "blocked", "ae_exact": False,
              "reason": "cross_host_return_compare_required", "request_id": request["request_id"], "fixture_sha256": sha(fixture)}
    if args.execute:
        if sys.platform != "darwin": fail("--execute requires macOS")
        if subprocess.run(["pgrep", "-x", "AfterFX"], stdout=subprocess.DEVNULL).returncode == 0: fail("AfterFX is already running")
        plugin = args.plugin_binary.resolve() if args.plugin_binary else Path("/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin")
        if not plugin.is_file() or sha(plugin) != PLUGIN_SHA: fail("exact ToonDilate plugin binary/hash is unavailable")
        env = dict(os.environ); env.update({"OLM_AE_TYPED_FIXTURE_OUTPUT_DIR": str(output_dir), "OLM_AE_TYPED_FIXTURE_TEMPLATE": "OLM EXR 32 Float",
            "OLM_AE_TYPED_FIXTURE_PROJECT_PATH": str(output_dir / "fixture.aep"), "OLM_AE_TYPED_FIXTURE_EFFECT": "OLM Toon Dilate",
            "OLM_AE_TYPED_FIXTURE_OVERWRITE": "0"})
        subprocess.run(["osascript", "-e", "with timeout of 3600 seconds", "-e", f'tell application "{args.ae_app}" to DoScriptFile POSIX file "{fixture}" with override', "-e", "end timeout"], check=True, env=env)
        result = read(output_dir / "fixture_result.json")
        if result.get("status") != "ok": fail("AE fixture did not report ok")
        manifest = read(output_dir / "fixture_manifest.json")
        if manifest.get("project_bits_per_channel") != 32 or manifest.get("working_space") != "None" or manifest.get("linear_blending") is not False:
            fail("AE/project/color contract drifted")
        if manifest.get("render_policy") != "same comp, only branch enabled state changes" or manifest.get("source_policy") != "AE-generated solids only; no footage imported":
            fail("same-context procedural control contract drifted")
        settings = list(output_dir.glob("*_output_module_settings.json"))
        if len(settings) != 2 or sha(settings[0]) != sha(settings[1]): fail("settings captures missing or unequal")
        outputs = {n: output_dir / fn for n, fn in request["case"]["outputs"].items()}
        inspected = {n: verify_output(path) for n, path in outputs.items()}
        record = {"kind": "olm_32bpc_typed_procedural_render_record", "schema": 1, "platform": "macos", "record_role": "reference",
                  "required_ae_major_minor": "26.3", "ae_version": result.get("ae_version", ""), "output_template": "OLM EXR 32 Float",
                  "fixture_jsx_sha256": sha(fixture), "renderer_class": "SOFTWARE", "linear_blending": False,
                  "cases": [{"id": request["case"]["id"], "effect": "OLM Toon Dilate", "plugin": {"name": "OLMToonDilate.plugin", "path": str(plugin), "sha256": sha(plugin)},
                             "fixture_contract": request["fixture_contract"], "parameters_requested": request["case"]["parameters"],
                             "outputs": {n: {"path": str(path), "sha256": inspected[n]["sha256"], "exr": inspected[n]} for n, path in outputs.items()},
                             "output_module": {"template_name": "OLM EXR 32 Float", "capture_api": "OutputModule.getSettings(GetSettingsFormat.STRING)",
                                "settings_sha256": sha(settings[0]), "settings": [str(x) for x in settings]}}]}
        (output_dir / "mac_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report.update({"mac_record": str(output_dir / "mac_record.json"), "status": "blocked", "reason": "cross_host_return_compare_required"})
    if args.windows_return:
        comparator = package / "compare_cross_host.py"
        proc = subprocess.run([sys.executable, str(comparator), str(output_dir / "mac_record.json"), str(args.windows_return), "--json"], text=True, capture_output=True)
        if proc.returncode != 0: fail(proc.stdout + proc.stderr)
        report.update({"status": "pass", "ae_exact": True, "reason": "cross_host_raw_float_bits_exact", "comparison": json.loads(proc.stdout)})
    (output_dir / "validation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
