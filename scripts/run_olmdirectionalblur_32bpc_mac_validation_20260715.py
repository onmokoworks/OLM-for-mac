#!/usr/bin/env python3
"""Prepare and run the pinned, one-case OLMDirectionalBlur Mac AE request."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json"
STEM = "olmdirectionalblur_32bpc_mac_validation_20260715"
TEMPLATE = "OLM EXR 32 Float"
CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_request() -> dict:
    data = json.loads(REQUEST.read_text(encoding="utf-8"))
    if data.get("status") != "request_only_no_ae_exact_claim":
        raise ValueError("request is not request-only")
    if data.get("case", {}).get("id") != "final_random10_olm_directionalblur_01":
        raise ValueError("case identity drifted")
    if data.get("plugin_identity", {}).get("filename") != "OLMDirectionalBlur.plugin":
        raise ValueError("plugin identity drifted")
    contract = data.get("ae_contract", {})
    if contract != {"major_minor": "26.3", "bits_per_channel": 32, "renderer": "SOFTWARE", "working_space": "None", "linear_blending": False, "frame": 0, "output_template": TEMPLATE, "output_format": "OpenEXR", "channels": ["A", "B", "G", "R"], "sample_type": "FLOAT", "compression": "none", "outputs": ["no_effect", "effect_on"]}:
        raise ValueError("AE contract drifted")
    return data


def jsx_source(case: dict, expected_plugin_hash: str) -> str:
    spec = json.dumps(case, separators=(",", ":"), ensure_ascii=True)
    return r'''(function () {
    var spec = CASE_JSON, TEMPLATE = "OLM EXR 32 Float", CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)", EXPECTED_PLUGIN_SHA256 = "PLUGIN_SHA256";
    var INTENT = {channels:["A","B","G","R"],sample_type:"FLOAT",compression:"none"};
    function env(n){try{return $.getenv(n)||"";}catch(e){return "";}}
    function fail(m){throw new Error("FAIL_CLOSED: "+m);}
    function quote(v){return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r/g,"\\r").replace(/\n/g,"\\n")+'"';}
    function stable(v){if(v===null)return "null";if(typeof v==="string")return quote(v);if(typeof v==="number"){if(!isFinite(v))fail("non-finite setting");return String(v);}if(typeof v==="boolean")return v?"true":"false";if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(stable(v[i]));return "["+a.join(",")+"]";}if(typeof v==="object"){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(quote(k[j])+":"+stable(v[k[j]]));return "{"+o.join(",")+"}";}fail("unsupported setting");}
    function write(path,text){var f=new File(path);f.encoding="UTF-8";if(!f.open("w"))fail("cannot write "+path);f.write(text);f.close();}
    function shell(c){return system.callSystem(c).replace(/[\r\n]+$/g,"");}
    function shquote(p){return "'"+String(p).replace(/'/g,"'\\''")+"'";}
    function hash(p){var m=shell("/usr/bin/shasum -a 256 "+shquote(p)).match(/^([0-9a-fA-F]{64})\s/);if(!m)fail("cannot hash "+p);return m[1].toLowerCase();}
    function findProperty(group,name){for(var i=1;i<=group.numProperties;i++){var p=group.property(i);if(p.matchName===name)return p;if(p.numProperties>0){var q=findProperty(p,name);if(q)return q;}}return null;}
    function setParams(effect){for(var name in spec.effect.params){if(!spec.effect.params.hasOwnProperty(name))continue;var p=findProperty(effect,name);if(!p)fail("missing parameter "+name);p.setValue(spec.effect.params[name]);}}
    function capture(module,output){if(!module.getSettings||typeof GetSettingsFormat==="undefined"||typeof GetSettingsFormat.STRING==="undefined")fail("settings API unavailable");var settings=module.getSettings(GetSettingsFormat.STRING);if(!settings)fail("empty settings");var path=output.replace(/\.exr$/i,"_output_module_settings.json");write(path,stable({kind:"olm_output_module_settings_capture",output_template:TEMPLATE,capture_api:CAPTURE_API,intent:INTENT,settings:settings})+"\n");return {path:path,sha256:hash(path),serialization:stable(settings)};}
    function render(comp,effect,enabled,outDir,name){effect.enabled=enabled;var item=app.project.renderQueue.items.add(comp);item.timeSpanStart=0;item.timeSpanDuration=1.0/comp.frameRate;var module=item.outputModule(1);module.applyTemplate(TEMPLATE);var output=outDir+"/"+name,settings=capture(module,output);module.file=new File(output);app.project.renderQueue.render();if(!new File(output).exists)fail("missing "+output);var result={path:output,sha256:hash(output),output_module_settings:settings,effect_enabled:enabled};item.remove();return result;}
    var inputDir=env("OLM_AE_MAC_INPUT_DIR"),outDir=env("OLM_AE_MAC_OUTPUT_DIR"),resultPath=env("OLM_AE_MAC_RESULT_JSON"),pluginPath=env("OLM_AE_MAC_PLUGIN_PATH");
    if(!inputDir||!outDir||!resultPath||!pluginPath)fail("required environment missing");
    var pluginFile=new File(pluginPath);if(!pluginFile.exists||pluginFile.name!=="OLMDirectionalBlur.plugin")fail("plugin identity mismatch");
    var loadedHash=hash(pluginFile.fsName);if(loadedHash!==EXPECTED_PLUGIN_SHA256)fail("plugin changed after preflight hash");
    var loadedPlugin={filename:pluginFile.name,path:pluginFile.fsName,sha256:loadedHash,expected_sha256:EXPECTED_PLUGIN_SHA256};
    var project=app.newProject();project.bitsPerChannel=32;project.linearBlending=false;try{project.gpuAccelType=GpuAccelType.SOFTWARE;}catch(e){fail("cannot set SOFTWARE");}
    if(Number(project.bitsPerChannel)!==32||String(project.gpuAccelType).toUpperCase()!=="SOFTWARE")fail("project contract mismatch");if(project.workingSpace!=="None")fail("working space drift");
    var input=new File(inputDir+"/input_before_effects.png");if(!input.exists||hash(input.fsName)!==spec.input.sha256)fail("input identity mismatch");
    var footage=project.importFile(new ImportOptions(input)),comp=project.items.addComp(spec.id,spec.comp.width,spec.comp.height,spec.comp.pixel_aspect,spec.comp.duration,spec.comp.frame_rate);comp.time=spec.comp.frame/comp.frameRate;
    var layer=comp.layers.add(footage),effect=layer.property("ADBE Effect Parade").addProperty(spec.effect.match_name);if(!effect||effect.matchName!==spec.effect.match_name||effect.name!==spec.effect.name)fail("effect identity mismatch");setParams(effect);
    var control=render(comp,effect,false,outDir,spec.id+"__no_effect.exr"),enabled=render(comp,effect,true,outDir,spec.id+"__effect_on.exr");if(control.output_module_settings.serialization!==enabled.output_module_settings.serialization)fail("Output Module settings differ");
    write(resultPath,stable({kind:"olmdirectionalblur_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,request_id:env("OLM_AE_MAC_REQUEST_ID"),platform:"macOS",ae_version:app.version,project:{bits_per_channel:project.bitsPerChannel,renderer:"SOFTWARE",working_space:project.workingSpace,linear_blending:project.linearBlending},output_module:{template_name:TEMPLATE,capture_api:CAPTURE_API,intent:INTENT},loaded_plugin:loadedPlugin,cases:[{id:spec.id,source_case_id:spec.source_case_id,input:spec.input,params:spec.effect.params,outputs:{no_effect:control,effect_on:enabled},no_effect_control_passed:true} ]})+"\n");
    try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}
}());
'''.replace("CASE_JSON", spec).replace("PLUGIN_SHA256", expected_plugin_hash)


def prepare(support: Path, plugin_hash: str) -> tuple[dict, Path]:
    data = load_request()
    source = ROOT / data["case"]["input"]["path"]
    if not source.is_file() or sha256(source) != data["case"]["input"]["sha256"]:
        raise ValueError("input missing or hash mismatch")
    input_dir = support / "input"; input_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, input_dir / "input_before_effects.png")
    (support / "request_manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    jsx = support / "run_mac_olmdirectionalblur_32bpc_validation.jsx"
    jsx.write_text(jsx_source({**data["case"], "input": {**data["case"]["input"], "filename": "input_before_effects.png"}}, plugin_hash), encoding="utf-8")
    return data, jsx


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plugin-path", type=Path, required=True); ap.add_argument("--support-dir", type=Path)
    ap.add_argument("--output-dir", type=Path); ap.add_argument("--result-json", type=Path); ap.add_argument("--dump-js", type=Path)
    ap.add_argument("--app-name", default="Adobe After Effects 2026"); ap.add_argument("--timeout", type=int, default=7200)
    args = ap.parse_args()
    if args.plugin_path.name != "OLMDirectionalBlur.plugin" or not args.plugin_path.is_file():
        print("[FAIL_CLOSED] --plugin-path must name an existing OLMDirectionalBlur.plugin", file=sys.stderr); return 2
    support = args.support_dir or Path(tempfile.mkdtemp(prefix=STEM + "_")); output = (args.output_dir or support / "return").resolve(); output.mkdir(parents=True, exist_ok=True)
    result = (args.result_json or output / "mac_validation_return.json").resolve()
    try: _, jsx = prepare(support, sha256(args.plugin_path))
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(f"[FAIL_CLOSED] {exc}", file=sys.stderr); return 1
    env = {"OLM_AE_MAC_INPUT_DIR": str((support / "input").resolve()), "OLM_AE_MAC_OUTPUT_DIR": str(output), "OLM_AE_MAC_RESULT_JSON": str(result), "OLM_AE_MAC_PLUGIN_PATH": str(args.plugin_path.resolve()), "OLM_AE_MAC_REQUEST_ID": "olmdirectionalblur_32bpc_mac_validation_20260715"}
    wrapper = support / "run_mac_wrapper.jsx"; wrapper.write_text("\n".join("$.setenv(%s, %s);" % (json.dumps(k), json.dumps(v)) for k, v in env.items()) + "\n$.evalFile(new File(%s));\n" % json.dumps(str(jsx.resolve())), encoding="utf-8")
    if args.dump_js:
        args.dump_js.parent.mkdir(parents=True, exist_ok=True); args.dump_js.write_text(wrapper.read_text(encoding="utf-8"), encoding="utf-8"); print(f"[OK] wrote {args.dump_js}"); return 0
    script = f'tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n'
    try: proc = subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=args.timeout)
    except (OSError, subprocess.TimeoutExpired): print("[FAIL_CLOSED] AE did not produce a return", file=sys.stderr); return 1
    if proc.returncode != 0 or not result.is_file(): print("[FAIL_CLOSED] AE did not produce a return", file=sys.stderr); return 1
    print(f"[OK] candidate return: {result}"); return 0


if __name__ == "__main__": raise SystemExit(main())
