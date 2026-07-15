#!/usr/bin/env python3
"""Prepare/run the smallest OLMBlur Mac 32bpc candidate/control request."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmblur_32bpc_mac_validation_20260715.json"
STEM = "olmblur_32bpc_mac_validation_20260715"
TEMPLATE = "OLM EXR 32 Float"
CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_request() -> dict:
    data = json.loads(REQUEST.read_text(encoding="utf-8"))
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
    function setParams(effect) { for (var i=0;i<spec.effect.params.length;i++) { var item=spec.effect.params[i], p=findProperty(effect,item.match_name); if (!p) fail("missing "+item.match_name); p.setValue(item.value); } }
    function capture(module, output) { if (!module.getSettings || typeof GetSettingsFormat === "undefined" || typeof GetSettingsFormat.STRING === "undefined") fail("settings API unavailable"); var s=module.getSettings(GetSettingsFormat.STRING); if (!s) fail("empty settings"); var path=output.replace(/\.exr$/i,"_output_module_settings.json"); write(path, stable({kind:"olm_output_module_settings_capture",output_template:TEMPLATE,capture_api:CAPTURE_API,intent:INTENT,settings:s})+"\n"); return {path:path,sha256:hash(path),serialization:stable(s)}; }
    function render(comp, effect, enabled, outDir, name) { effect.enabled=enabled; var item=app.project.renderQueue.items.add(comp); item.timeSpanStart=0; item.timeSpanDuration=1.0/comp.frameRate; var module=item.outputModule(1); module.applyTemplate(TEMPLATE); var output=outDir+"/"+name, settings=capture(module,output); module.file=new File(output); app.project.renderQueue.render(); if (!new File(output).exists) fail("missing "+output); var result={path:output,sha256:hash(output),output_module_settings:settings}; item.remove(); return result; }
    var inputDir=env("OLM_AE_MAC_INPUT_DIR"), outDir=env("OLM_AE_MAC_OUTPUT_DIR"), resultPath=env("OLM_AE_MAC_RESULT_JSON"), pluginPath=env("OLM_AE_MAC_PLUGIN_PATH");
    if (!inputDir || !outDir || !resultPath || !pluginPath) fail("required environment missing");
    var pluginFile=new File(pluginPath); if (!pluginFile.exists || pluginFile.name!=="OLMBlur.plugin") fail("plugin identity mismatch");
    var loadedPlugin={filename:pluginFile.name,path:pluginFile.fsName,sha256:hash(pluginFile.fsName)};
    var project=app.newProject(); project.bitsPerChannel=32; project.linearBlending=false; try { project.gpuAccelType=GpuAccelType.SOFTWARE; } catch(e) { fail("cannot set SOFTWARE"); }
    if (Number(project.bitsPerChannel)!==32 || String(project.gpuAccelType).toUpperCase()!=="SOFTWARE") fail("project contract mismatch");
    if (project.workingSpace!=="None") fail("working space drift");
    var input=new File(inputDir+"/"+spec.input.filename); if (!input.exists) fail("missing input");
    var footage=project.importFile(new ImportOptions(input)), comp=project.items.addComp(spec.id,spec.comp.width,spec.comp.height,spec.comp.pixel_aspect,spec.comp.duration,spec.comp.frame_rate);
    var layer=comp.layers.add(footage), effect=layer.property("ADBE Effect Parade").addProperty(spec.effect.match_name); if (!effect || effect.matchName!==spec.effect.match_name || effect.name!==spec.effect.name) fail("effect identity mismatch"); setParams(effect);
    var control=render(comp,effect,false,outDir,spec.id+"__no_effect.exr"), enabled=render(comp,effect,true,outDir,spec.id+"__effect_on.exr");
    if (control.output_module_settings.serialization!==enabled.output_module_settings.serialization) fail("settings differ");
    write(resultPath,stable({kind:"olmblur_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,platform:"macOS",ae_version:app.version,project:{bits_per_channel:project.bitsPerChannel,renderer:"SOFTWARE",working_space:project.workingSpace,linear_blending:project.linearBlending},output_module:{template_name:TEMPLATE,capture_api:CAPTURE_API,intent:INTENT},loaded_plugin:loadedPlugin,cases:[{id:spec.id,input:spec.input,params:spec.effect.params,outputs:{no_effect:control,effect_on:enabled},no_effect_control_passed:true} ]})+"\n");
    try { project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch(e) {}
}());
'''.replace("CASE_JSON", case_json).replace("TEMPLATE_JSON", json.dumps(TEMPLATE)).replace("CAPTURE_JSON", json.dumps(CAPTURE_API))


def prepare(support: Path) -> tuple[dict, Path]:
    data = load_request(); case = data["case"]; source = ROOT / case["input"]["path"]
    if not source.exists() or sha256(source) != case["input"]["sha256"]: raise ValueError("input missing or hash mismatch")
    input_dir = support / "input"; input_dir.mkdir(parents=True, exist_ok=True); shutil.copy2(source, input_dir / "case_0001_before_effects.png")
    (support / "request_manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    jsx = support / "run_mac_olmblur_32bpc_validation.jsx"; jsx.write_text(jsx_source({"case": {**case, "input": {**case["input"], "filename": "case_0001_before_effects.png"}}, "ae_contract": data["ae_contract"]}), encoding="utf-8")
    return data, jsx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--plugin-path", type=Path, required=True); parser.add_argument("--support-dir", type=Path); parser.add_argument("--output-dir", type=Path); parser.add_argument("--result-json", type=Path); parser.add_argument("--dump-js", type=Path); parser.add_argument("--app-name", default="Adobe After Effects 2026")
    args = parser.parse_args()
    if args.plugin_path.name != "OLMBlur.plugin" or not args.plugin_path.is_file(): print("[FAIL_CLOSED] --plugin-path must name an existing OLMBlur.plugin"); return 2
    support = args.support_dir or Path(tempfile.mkdtemp(prefix=STEM+"_")); output = args.output_dir or support / "return"; output.mkdir(parents=True, exist_ok=True); result = args.result_json or output / "mac_validation_return.json"
    try: _, jsx = prepare(support)
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(f"[FAIL_CLOSED] {exc}"); return 1
    wrapper = support / "run_mac_wrapper.jsx"; env={"OLM_AE_MAC_INPUT_DIR":str((support/"input").resolve()),"OLM_AE_MAC_OUTPUT_DIR":str(output.resolve()),"OLM_AE_MAC_RESULT_JSON":str(result.resolve()),"OLM_AE_MAC_PLUGIN_PATH":str(args.plugin_path.resolve())}; wrapper.write_text("\n".join("$.setenv(%s, %s);" % (json.dumps(k),json.dumps(v)) for k,v in env.items())+"\n$.evalFile(new File(%s));\n" % json.dumps(str(jsx.resolve())), encoding="utf-8")
    if args.dump_js: args.dump_js.write_text(wrapper.read_text(encoding="utf-8"), encoding="utf-8"); print(f"[OK] wrote {args.dump_js}"); return 0
    script = f'tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n'
    try: proc=subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=7200)
    except (OSError, subprocess.TimeoutExpired): print("[FAIL_CLOSED] AE did not produce a return"); return 1
    if proc.returncode != 0 or not result.exists(): print("[FAIL_CLOSED] AE did not produce a return"); return 1
    checked = subprocess.run([sys.executable, str(ROOT / "scripts/report_olmblur_32bpc_mac_validation_20260715.py"), str(result), "--output-dir", str(output)], text=True)
    if checked.returncode != 0: print("[FAIL_CLOSED] candidate return failed report validation"); return 1
    print(f"[OK] candidate return: {result}"); return 0


if __name__ == "__main__": raise SystemExit(main())
