#!/usr/bin/env python3
"""Run or validate the isolated Mac ToonDilate 32bpc request."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, secrets, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (Path(__file__).resolve().parent if Path(__file__).resolve().parent.name == "olmtoondilate_mac_32bpc_validation_20260715"
           else ROOT / "runtime_trace_packages/olmtoondilate_mac_32bpc_validation_20260715")
_here = Path(__file__).resolve().parent
_helper = _here if _here.name == "olmtoondilate_mac_32bpc_validation_20260715" else ROOT / "runtime_trace_packages/olmtoondilate_mac_32bpc_validation_20260715"
REFS = _here.parents[1] if _here.name == "olmtoondilate_mac_32bpc_validation_20260715" else ROOT
sys.path.insert(0, str(_helper))
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr
from compare_float_exr import compare as compare_float_words
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def fail(message): raise SystemExit("FAIL CLOSED: " + message)

def resolve_plugin_binary(path: Path) -> tuple[Path, Path]:
    supplied = path.expanduser().resolve()
    if supplied.is_dir() and supplied.name == "OLMToonDilate.plugin":
        bundle = supplied
        binary = bundle / "Contents/MacOS/OLMToonDilate"
    elif supplied.is_file() and supplied.name == "OLMToonDilate" and supplied.parent.name == "MacOS" and supplied.parent.parent.name == "Contents":
        binary = supplied
        bundle = supplied.parent.parent.parent
    else:
        fail("plugin path must be OLMToonDilate.plugin or its Contents/MacOS/OLMToonDilate executable")
    if bundle.name != "OLMToonDilate.plugin" or not binary.is_file():
        fail("OLMToonDilate plugin executable is unavailable")
    return bundle, binary

def ae_process_proof(plugin_binary: Path) -> dict:
    found = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, timeout=10)
    pids = [int(value) for value in found.stdout.split() if value.isdigit()]
    if found.returncode != 0 or len(pids) != 1: fail(f"expected exactly one After Effects process after render, found {pids!r}")
    pid = pids[0]
    started = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], text=True, capture_output=True, timeout=10)
    if started.returncode != 0 or not started.stdout.strip(): fail("cannot read After Effects process start time")
    started_text = " ".join(started.stdout.split())
    started_at = dt.datetime.strptime(started_text, "%a %b %d %H:%M:%S %Y").timestamp()
    if plugin_binary.stat().st_mtime > started_at + 1: fail("plugin binary was modified after After Effects started")
    mapped = subprocess.run(["vmmap", str(pid)], text=True, capture_output=True, timeout=120)
    resolved = str(plugin_binary.resolve())
    if mapped.returncode != 0 or not any(re.search(r"\s" + re.escape(resolved) + r"$", line) for line in mapped.stdout.splitlines()):
        fail("requested OLMToonDilate binary is not mapped in After Effects")
    return {"method": "vmmap_exact_path", "pid": pid, "module_path": resolved,
            "module_sha256": sha(plugin_binary), "process_started_local": started_text,
            "binary_predates_process_start": True}

def verify_output(path, expected_dimensions=(64, 64)):
    try:
        return inspect_float_rgba_exr(path, expected_dimensions=expected_dimensions)
    except (OSError, ValueError, VerificationError) as exc:
        fail(f"invalid uncompressed FLOAT RGBA EXR: {exc}")

def write_es3_loader(wrapper: Path, trace: Path, payload: Path) -> None:
    header = "(function () {\n  var payloadPath = " + json.dumps(str(payload)) + ";\n  var tracePath = " + json.dumps(str(trace)) + ";\n"
    body = r'''  function esc(v) { return String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\r/g, '\\r').replace(/\n/g, '\\n'); }
  function writeTrace(status, message, fileName, lineNumber) {
    var f = new File(tracePath); f.encoding = 'UTF-8';
    if (!f.open('w')) return;
    f.write('{"status":"' + esc(status) + '","payload":"' + esc(payloadPath) + '","trace":"' + esc(tracePath) + '","message":"' + esc(message || '') + '","file":"' + esc(fileName || '') + '","line":' + (lineNumber || 0) + '}\n');
    f.close();
  }
  try {
    if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    var created = app.newProject();
    if (!created || !app.project) { writeTrace('error', 'app.newProject returned null', '', 0); return; }
    var payload = new File(payloadPath);
    if (!payload.exists) { writeTrace('error', 'payload missing', payloadPath, 0); return; }
    $.evalFile(payload);
    writeTrace('ok', '', payloadPath, 0);
  } catch (e) {
    writeTrace('error', e && e.message ? e.message : String(e), e && e.fileName ? e.fileName : payloadPath, e && e.line ? e.line : 0);
  }
}());
'''
    wrapper.write_text(header + body, encoding="utf-8")

def audit_es3_loader(wrapper: Path, trace: Path, payload: Path) -> dict:
    source = wrapper.read_text(encoding="utf-8")
    required = [str(payload), str(trace), "app.newProject()", "if (!created || !app.project)",
                "$.evalFile(payload)", "catch (e)", "e.fileName", "e.line"]
    missing = [value for value in required if value not in source]
    forbidden = [value for value in ("alert(", "throw ", "JSON.") if value in source]
    if missing or forbidden: fail(f"ES3 loader static audit failed: missing={missing!r} forbidden={forbidden!r}")
    return {"loader": str(wrapper), "loader_sha256": sha(wrapper), "payload": str(payload), "trace": str(trace),
            "absolute_paths": payload.is_absolute() and trace.is_absolute() and wrapper.is_absolute(),
            "new_project_null_guard": True, "eval_error_file_line_trace": True,
            "no_alert_or_rethrow": True, "no_json_global_dependency": True}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--package", type=Path, default=PACKAGE)
    p.add_argument("--execute", action="store_true", help="explicitly invoke AE on macOS")
    p.add_argument("--prepare-loader-only", action="store_true", help="write and statically audit the ES3 loader without invoking AE")
    p.add_argument("--ae-app", default="Adobe After Effects 2026")
    p.add_argument("--plugin-binary", type=Path, help="OLMToonDilate.plugin bundle or its Mach-O executable")
    p.add_argument("--windows-return", type=Path)
    args = p.parse_args(); package = args.package.resolve(); request = read(package / "request_manifest.json")
    expected_plugin_sha = request["case"]["plugin"]["sha256"]
    if not isinstance(expected_plugin_sha, str) or len(expected_plugin_sha) != 64:
        fail("request plugin hash is missing or invalid")
    fixture = package / "fixture/ae_generate_32bpc_olmtoondilate_fixture.jsx"
    if not fixture.is_file(): fail("fixture missing")
    if request.get("fixture_jsx_sha256") != sha(fixture): fail("fixture hash differs from request contract")
    output_dir = package / "mac_run"; output_dir.mkdir(exist_ok=True)
    report = {"kind": "olmtoondilate_mac_32bpc_validation_report", "schema": 1, "status": "blocked", "ae_exact": False,
              "reason": "cross_host_return_compare_required", "request_id": request["request_id"], "fixture_sha256": sha(fixture)}
    wrapper = (output_dir / "run_fixture_es3_loader.jsx").resolve()
    trace = (output_dir / "es3_loader_trace.json").resolve()
    payload = fixture.resolve()
    if args.prepare_loader_only:
        if args.execute: fail("--prepare-loader-only and --execute are mutually exclusive")
        write_es3_loader(wrapper, trace, payload)
        report.update({"status": "prepared", "reason": "loader_static_preflight_only", "loader_static_audit": audit_es3_loader(wrapper, trace, payload)})
    if args.execute:
        if sys.platform != "darwin": fail("--execute requires macOS")
        if subprocess.run(["pgrep", "-x", "After Effects"], stdout=subprocess.DEVNULL).returncode == 0: fail("After Effects is already running; use a fresh process for loaded-module proof")
        supplied = args.plugin_binary or Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin"
        plugin_bundle, plugin = resolve_plugin_binary(supplied)
        if sha(plugin) != expected_plugin_sha: fail("exact ToonDilate plugin binary/hash is unavailable")
        env = dict(os.environ); env.update({"OLM_AE_TYPED_FIXTURE_OUTPUT_DIR": str(output_dir), "OLM_AE_TYPED_FIXTURE_TEMPLATE": "OLM EXR 32 Float",
            "OLM_AE_TYPED_FIXTURE_PROJECT_PATH": str(output_dir / "fixture.aep"), "OLM_AE_TYPED_FIXTURE_EFFECT": "OLM Toon Dilate",
            "OLM_AE_TYPED_FIXTURE_OVERWRITE": "0"})
        if trace.exists(): trace.unlink()
        challenge = {"nonce": secrets.token_hex(32), "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "plugin_sha256": expected_plugin_sha, "fixture_sha256": sha(fixture)}
        (output_dir / "process_challenge.json").write_text(json.dumps(challenge, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_es3_loader(wrapper, trace, payload)
        audit_es3_loader(wrapper, trace, payload)
        subprocess.run([
            "osascript", "-e", "with timeout of 3600 seconds",
            "-e", f'tell application "{args.ae_app}"',
            "-e", f'DoScriptFile POSIX file "{wrapper}" with override',
            "-e", "end tell", "-e", "end timeout",
        ], check=True, env=env)
        if not trace.is_file(): fail("ES3 loader did not write its absolute trace")
        loader_trace = read(trace)
        if loader_trace.get("status") != "ok":
            fail(f"ES3 loader failed: file={loader_trace.get('file')} line={loader_trace.get('line')} message={loader_trace.get('message')}")
        if loader_trace.get("payload") != str(payload) or loader_trace.get("trace") != str(trace):
            fail("ES3 loader absolute path trace drifted")
        loaded_proof = ae_process_proof(plugin)
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
        expected_outputs = request.get("expected_current_installed_output_sha256", {})
        retained = {
            "no_effect": REFS / "conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728/mac_no_effect.exr",
            "effect_on": REFS / "conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728/mac_effect_on.exr",
        }
        if set(expected_outputs) != set(outputs): fail("expected output hash contract missing or drifted")
        raw_repeat = {}
        for name in outputs:
            if not retained[name].is_file() or sha(retained[name]) != expected_outputs[name]:
                fail(f"{name} retained expectation identity drifted")
            raw_repeat[name] = compare_float_words(outputs[name], retained[name])
            if raw_repeat[name].get("mismatched_values") != 0:
                fail(f"{name} raw FLOAT words differ from the pinned current-installed expectation")
        requested = request["case"]["parameters"][0]
        readbacks = result.get("parameters", [])
        if len(readbacks) != 1 or readbacks[0].get("property_index") != 1 or abs(float(readbacks[0].get("actual")) - float(requested["value"])) > float(requested["readback_tolerance"]):
            fail("Search Radius readback differs from the pinned parameter contract")
        record = {"kind": "olm_32bpc_typed_procedural_render_record", "schema": 1, "platform": "macos", "record_role": "reference",
                  "required_ae_major_minor": "26.3", "ae_version": result.get("ae_version", ""), "output_template": "OLM EXR 32 Float",
                  "fixture_jsx_sha256": sha(fixture), "renderer_class": "SOFTWARE", "linear_blending": False,
                  "cases": [{"id": request["case"]["id"], "effect": "OLM Toon Dilate", "plugin": {"name": "OLMToonDilate.plugin", "bundle_path": str(plugin_bundle), "path": str(plugin), "sha256": sha(plugin), "loaded_plugin_proof": loaded_proof},
                             "fixture_contract": request["fixture_contract"], "parameters_requested": request["case"]["parameters"],
                             "outputs": {n: {"path": str(path), "sha256": inspected[n]["sha256"], "exr": inspected[n]} for n, path in outputs.items()},
                             "output_module": {"template_name": "OLM EXR 32 Float", "capture_api": "OutputModule.getSettings(GetSettingsFormat.STRING)",
                                "settings_sha256": sha(settings[0]), "settings": [str(x) for x in settings]}}]}
        (output_dir / "mac_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report.update({"mac_record": str(output_dir / "mac_record.json"), "status": "current_mac_host_pass",
                       "reason": "current_installed_mac_repeat_raw_float_exact",
                       "ae_exact": False, "process_challenge": challenge, "raw_repeat": raw_repeat,
                       "claim_boundary": "Current Mac AE representative host/load/render repeat only; no new Windows exactness claim."})
    if args.windows_return:
        comparator = package / "compare_cross_host.py"
        proc = subprocess.run([sys.executable, str(comparator), str(output_dir / "mac_record.json"), str(args.windows_return), "--json"], text=True, capture_output=True)
        if proc.returncode != 0: fail(proc.stdout + proc.stderr)
        report.update({"status": "pass", "ae_exact": True, "reason": "cross_host_raw_float_bits_exact", "comparison": json.loads(proc.stdout)})
    (output_dir / "validation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
