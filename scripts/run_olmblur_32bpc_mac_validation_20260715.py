#!/usr/bin/env python3
"""Prepare/run the smallest OLMBlur Mac 32bpc candidate/control request."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "refs/mac_validation_requests/olmblur_32bpc_mac_validation_20260715.json"
STEM = "olmblur_32bpc_mac_validation_20260715"
TEMPLATE = "OLM EXR 32 Float"
CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_request(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["status"] != "request_only_no_ae_exact_claim" or data["case"]["id"] != "olmblur__case_0001":
        raise ValueError("request metadata drifted")
    return data


def jsx_source(data: dict) -> str:
    case = data["case"]
    contract = data["ae_contract"]
    case_json = json.dumps(case, separators=(",", ":"), ensure_ascii=True)
    return r'''(function () {
    var spec = CASE_JSON, TEMPLATE = TEMPLATE_JSON, CAPTURE_API = CAPTURE_JSON;
    var INTENT = {channels: ["A", "B", "G", "R"], sample_type: "FLOAT", compression: "none"};
    function env(n) { try { return $.getenv(n) || ""; } catch (e) { return ""; } }
    function fail(m) { throw new Error("FAIL_CLOSED: " + m); }
    function quote(v) { return '"' + String(v).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"'; }
    function stable(v) {
        if (v === null) return "null"; if (typeof v === "string") return quote(v);
        if (typeof v === "number") { if (!isFinite(v)) fail("non-finite setting"); return String(v); }
        if (typeof v === "boolean") return v ? "true" : "false";
        if (v instanceof Array) { var a=[]; for (var i=0;i<v.length;i++) a.push(stable(v[i])); return "["+a.join(",")+"]"; }
        if (typeof v === "object") { var k=[],o=[]; for (var n in v) if (v.hasOwnProperty(n)) k.push(n); k.sort(); for (var j=0;j<k.length;j++) o.push(quote(k[j])+":"+stable(v[k[j]])); return "{"+o.join(",")+"}"; }
        fail("unsupported setting");
    }
    function write(path, text) { var f=new File(path); f.encoding="UTF-8"; if (!f.open("w")) fail("cannot write "+path); f.write(text); f.close(); }
    function shell(c) { return system.callSystem(c).replace(/[\r\n]+$/g, ""); }
    function shquote(p) { return "'"+String(p).replace(/'/g, "'\\''")+"'"; }
    function hash(p) { var m=shell("/usr/bin/shasum -a 256 "+shquote(p)).match(/^([0-9a-fA-F]{64})\s/); if (!m) fail("cannot hash "+p); return m[1].toLowerCase(); }
    function findProperty(group, name) { for (var i=1;i<=group.numProperties;i++) { var p=group.property(i); if (p.matchName===name) return p; if (p.numProperties>0) { var q=findProperty(p,name); if (q) return q; } } return null; }
    function setParams(effect) { var readback=[]; for (var i=0;i<spec.effect.params.length;i++) { var item=spec.effect.params[i], p=findProperty(effect,item.match_name); if (!p) fail("missing "+item.match_name); p.setValue(item.value); readback.push({name:item.name,match_name:item.match_name,property_index:item.property_index,value:p.value}); } return readback; }
    function capture(module, output) { if (!module.getSettings || typeof GetSettingsFormat === "undefined" || typeof GetSettingsFormat.STRING === "undefined") fail("settings API unavailable"); var s=module.getSettings(GetSettingsFormat.STRING); if (!s) fail("empty settings"); var path=output.replace(/\.exr$/i,"_output_module_settings.json"); write(path, stable({kind:"olm_output_module_settings_capture",output_template:TEMPLATE,capture_api:CAPTURE_API,intent:INTENT,settings:s})+"\n"); return {path:path,sha256:hash(path),serialization:stable(s)}; }
    function clearRenderedFiles(output) { var target=new File(output), prefix=target.name, matches=target.parent.getFiles(function (entry) { return entry instanceof File && entry.name.indexOf(prefix)===0; }); for (var i=0;i<matches.length;i++) { if (!matches[i].remove()) fail("cannot remove stale output "+matches[i].fsName); } }
    function renderedFile(output) { var target=new File(output); if (target.exists) return target; var matches=target.parent.getFiles(function (entry) { return entry instanceof File && entry.name.indexOf(target.name)===0; }); if (matches.length!==1) fail("rendered output cardinality for "+output+": "+matches.length); if (!matches[0].rename(target.name) || !target.exists) fail("cannot normalize rendered output "+matches[0].fsName); return target; }
    function render(comp, effect, enabled, outDir, name) { effect.enabled=enabled; var item=app.project.renderQueue.items.add(comp); item.timeSpanStart=0; item.timeSpanDuration=1.0/comp.frameRate; var module=item.outputModule(1); module.applyTemplate(TEMPLATE); var output=outDir+"/"+name; clearRenderedFiles(output); var settings=capture(module,output); module.file=new File(output); app.project.renderQueue.render(); var rendered=renderedFile(output); var result={path:rendered.fsName,sha256:hash(rendered.fsName),output_module_settings:settings}; item.remove(); return result; }
    var inputDir=env("OLM_AE_MAC_INPUT_DIR"), outDir=env("OLM_AE_MAC_OUTPUT_DIR"), resultPath=env("OLM_AE_MAC_RESULT_JSON"), pluginPath=env("OLM_AE_MAC_PLUGIN_PATH"), pluginBinaryPath=env("OLM_AE_MAC_PLUGIN_BINARY");
    if (!inputDir || !outDir || !resultPath || !pluginPath || !pluginBinaryPath) fail("required environment missing");
    var pluginFolder=new Folder(pluginPath), pluginBinary=new File(pluginBinaryPath);
    if (!pluginFolder.exists || pluginFolder.name!=="OLMBlur.plugin" || !pluginBinary.exists || pluginBinary.name!=="OLMBlur") fail("plugin identity mismatch");
    var loadedPlugin={filename:pluginFolder.name,bundle_path:pluginFolder.fsName,path:pluginBinary.fsName,sha256:hash(pluginBinary.fsName)};
    var project=app.newProject(); project.bitsPerChannel=32; project.linearBlending=false; try { project.gpuAccelType=GpuAccelType.SOFTWARE; } catch(e) { fail("cannot set SOFTWARE"); }
    if (Number(project.bitsPerChannel)!==32 || project.gpuAccelType!==GpuAccelType.SOFTWARE) fail("project contract mismatch: bpc="+project.bitsPerChannel+" renderer="+project.gpuAccelType+" software="+GpuAccelType.SOFTWARE);
    if (project.workingSpace!=="None") fail("working space drift");
    var input=new File(inputDir+"/"+spec.input.filename); if (!input.exists) fail("missing input");
    var footage=project.importFile(new ImportOptions(input)), comp=project.items.addComp(spec.id,spec.comp.width,spec.comp.height,spec.comp.pixel_aspect,spec.comp.duration,spec.comp.frame_rate);
    var layer=comp.layers.add(footage), effect=layer.property("ADBE Effect Parade").addProperty(spec.effect.match_name); if (!effect || effect.matchName!==spec.effect.match_name || effect.name!==spec.effect.name) fail("effect identity mismatch"); var parameterReadback=setParams(effect);
    var control=render(comp,effect,false,outDir,spec.id+"__no_effect.exr"), enabled=render(comp,effect,true,outDir,spec.id+"__effect_on.exr");
    if (control.output_module_settings.serialization!==enabled.output_module_settings.serialization) fail("settings differ");
    write(resultPath,stable({kind:"olmblur_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,platform:"macOS",ae_version:app.version,project:{bits_per_channel:project.bitsPerChannel,renderer:"SOFTWARE",working_space:project.workingSpace,linear_blending:project.linearBlending},output_module:{template_name:TEMPLATE,capture_api:CAPTURE_API,intent:INTENT},loaded_plugin:loadedPlugin,cases:[{id:spec.id,input:spec.input,requested_params:spec.effect.params,params:parameterReadback,outputs:{no_effect:control,effect_on:enabled},no_effect_control_passed:true} ]})+"\n");
    try { project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch(e) {}
}());
'''.replace("CASE_JSON", case_json).replace("TEMPLATE_JSON", json.dumps(TEMPLATE)).replace("CAPTURE_JSON", json.dumps(CAPTURE_API))


def prepare(support: Path, request_path: Path) -> tuple[dict, Path]:
    data = load_request(request_path); case = data["case"]; source = ROOT / case["input"]["path"]
    if not source.exists() or sha256(source) != case["input"]["sha256"]: raise ValueError("input missing or hash mismatch")
    input_dir = support / "input"; input_dir.mkdir(parents=True, exist_ok=True); shutil.copy2(source, input_dir / "case_0001_before_effects.png")
    (support / "request_manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    jsx = support / "run_mac_olmblur_32bpc_validation.jsx"; jsx.write_text(jsx_source({"case": {**case, "input": {**case["input"], "filename": "case_0001_before_effects.png"}}, "ae_contract": data["ae_contract"]}), encoding="utf-8")
    return data, jsx


def ae_process_proof(plugin_binary: Path) -> dict[str, object]:
    found = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, timeout=10)
    pids = [int(value) for value in found.stdout.split() if value.isdigit()]
    if found.returncode != 0 or len(pids) != 1:
        raise RuntimeError(f"expected exactly one After Effects process, found {pids!r}")
    pid = pids[0]
    started = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], text=True, capture_output=True, timeout=10)
    if started.returncode != 0 or not started.stdout.strip():
        raise RuntimeError("cannot read After Effects process start time")
    started_text = " ".join(started.stdout.split())
    started_at = dt.datetime.strptime(started_text, "%a %b %d %H:%M:%S %Y").timestamp()
    if plugin_binary.stat().st_mtime > started_at + 1:
        raise RuntimeError("plugin binary was modified after After Effects started; restart AE before validation")
    mapped = subprocess.run(["vmmap", str(pid)], text=True, capture_output=True, timeout=120)
    resolved = str(plugin_binary.resolve())
    exact_mapping = any(re.search(r"\s" + re.escape(resolved) + r"$", line) for line in mapped.stdout.splitlines())
    if mapped.returncode != 0 or not exact_mapping:
        raise RuntimeError("requested OLMBlur binary is not mapped in the After Effects process")
    return {
        "method": "vmmap_exact_path",
        "pid": pid,
        "process_started_local": started_text,
        "module_path": resolved,
        "module_sha256": hashlib.sha256(plugin_binary.read_bytes()).hexdigest(),
        "binary_predates_process_start": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--plugin-path", type=Path, required=True); parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST); parser.add_argument("--support-dir", type=Path); parser.add_argument("--output-dir", type=Path); parser.add_argument("--result-json", type=Path); parser.add_argument("--dump-js", type=Path); parser.add_argument("--app-name", default="Adobe After Effects 2026")
    args = parser.parse_args()
    plugin_binary = args.plugin_path / "Contents" / "MacOS" / "OLMBlur"
    if args.plugin_path.name != "OLMBlur.plugin" or not args.plugin_path.is_dir() or not plugin_binary.is_file():
        print("[FAIL_CLOSED] --plugin-path must name an existing OLMBlur.plugin bundle")
        return 2
    support = args.support_dir or Path(tempfile.mkdtemp(prefix=STEM+"_")); output = args.output_dir or support / "return"; output.mkdir(parents=True, exist_ok=True); result = args.result_json or output / "mac_validation_return.json"
    try: _, jsx = prepare(support, args.request.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(f"[FAIL_CLOSED] {exc}"); return 1
    wrapper = support / "run_mac_wrapper.jsx"; env={"OLM_AE_MAC_INPUT_DIR":str((support/"input").resolve()),"OLM_AE_MAC_OUTPUT_DIR":str(output.resolve()),"OLM_AE_MAC_RESULT_JSON":str(result.resolve()),"OLM_AE_MAC_PLUGIN_PATH":str(args.plugin_path.resolve()),"OLM_AE_MAC_PLUGIN_BINARY":str(plugin_binary.resolve())}
    error_path = result.with_suffix(result.suffix + ".error.txt")
    wrapper.write_text(
        "\n".join("$.setenv(%s, %s);" % (json.dumps(k), json.dumps(v)) for k, v in env.items())
        + "\ntry { $.evalFile(new File(%s)); } catch (e) {\n" % json.dumps(str(jsx.resolve()))
        + "  var f = new File(%s); f.encoding = 'UTF-8';\n" % json.dumps(str(error_path.resolve()))
        + "  if (f.open('w')) { f.write(String(e) + '\\nline=' + String(e.line || '') + '\\n'); f.close(); }\n"
        + "  throw e;\n}\n",
        encoding="utf-8",
    )
    if args.dump_js: args.dump_js.write_text(wrapper.read_text(encoding="utf-8"), encoding="utf-8"); print(f"[OK] wrote {args.dump_js}"); return 0
    script = f'tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper.resolve()))} with override\n'
    try: proc=subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=7200)
    except (OSError, subprocess.TimeoutExpired): print("[FAIL_CLOSED] AE did not produce a return"); return 1
    if proc.returncode != 0 or not result.exists():
        detail = error_path.read_text(encoding="utf-8", errors="replace").strip() if error_path.exists() else "no JSX error log"
        print(f"[FAIL_CLOSED] AE did not produce a return: {detail}")
        return 1
    try:
        proof = ae_process_proof(plugin_binary)
        returned = json.loads(result.read_text(encoding="utf-8"))
        plugin = returned.get("loaded_plugin", {})
        if plugin.get("path") != proof["module_path"] or plugin.get("sha256") != proof["module_sha256"]:
            raise RuntimeError("AE return plugin identity disagrees with mapped-module proof")
        returned["loaded_plugin_proof"] = proof
        result.write_text(json.dumps(returned, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"[FAIL_CLOSED] loaded plug-in proof failed: {exc}")
        return 1
    checked = subprocess.run([sys.executable, str(ROOT / "scripts/report_olmblur_32bpc_mac_validation_20260715.py"), str(result), "--output-dir", str(output)], text=True)
    if checked.returncode != 0: print("[FAIL_CLOSED] candidate return failed report validation"); return 1
    print(f"[OK] candidate return: {result}"); return 0


if __name__ == "__main__": raise SystemExit(main())
