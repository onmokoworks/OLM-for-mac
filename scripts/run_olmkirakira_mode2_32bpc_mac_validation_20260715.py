#!/usr/bin/env python3
"""Run the single, fail-closed OLMKiraKira Mode 2 Mac AE validation case."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmkirakira_mode2_32bpc_mac_validation_20260715.json"
STEM = "olmkirakira_mode2_32bpc_mac_validation_20260715"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_request() -> dict:
    data = json.loads(REQUEST.read_text(encoding="utf-8"))
    case = data.get("case", {})
    params = case.get("effect", {}).get("params_full")
    if data.get("status") != "sendable_fail_closed_no_ae_exact_claim":
        raise ValueError("request status drifted")
    if case.get("id") != "final_random10_olm_kira_kira_06":
        raise ValueError("selected case drifted")
    if not isinstance(params, list) or len(params) != 42:
        raise ValueError("selected 42-property manifest is missing")
    values = {p.get("name"): p.get("value") for p in params}
    if values.get("Blur Mode") != 2 or values.get("Merge mode") != 1 or values.get("Approximated Input") != 0:
        raise ValueError("request is not the grounded Mode 2 pin")
    return data


def jsx_source(data: dict) -> str:
    case = data["case"]
    contract = data["mac_contract"]
    plugin = data["plugin"]
    case_json = json.dumps(case, separators=(",", ":"), ensure_ascii=True)
    contract_json = json.dumps(contract, separators=(",", ":"), ensure_ascii=True)
    plugin_json = json.dumps(plugin, separators=(",", ":"), ensure_ascii=True)
    return r'''(function () {
    var SPEC = CASE_JSON, CONTRACT = CONTRACT_JSON, PLUGIN = PLUGIN_JSON;
    function env(n) { try { return $.getenv(n) || ""; } catch (e) { return ""; } }
    function fail(m) { throw new Error("FAIL_CLOSED: " + m); }
    function quote(v) { return '"' + String(v).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"'; }
    function stable(v) { if (v === null) return "null"; if (typeof v === "string") return quote(v); if (typeof v === "number") { if (!isFinite(v)) fail("non-finite value"); return String(v); } if (typeof v === "boolean") return v ? "true" : "false"; if (v instanceof Array) { var a=[]; for(var i=0;i<v.length;i++) a.push(stable(v[i])); return "["+a.join(",")+"]"; } if (typeof v === "object") { var k=[],o=[]; for(var n in v) if(v.hasOwnProperty(n)) k.push(n); k.sort(); for(var j=0;j<k.length;j++) o.push(quote(k[j])+":"+stable(v[k[j]])); return "{"+o.join(",")+"}"; } fail("unsupported value"); }
    function write(p, s) { var f=new File(p); f.encoding="UTF-8"; if(!f.open("w")) fail("cannot write "+p); f.write(s); f.close(); }
    function shell(c) { return system.callSystem(c).replace(/[\r\n]+$/g, ""); }
    function shquote(p) { return "'"+String(p).replace(/'/g, "'\\''")+"'"; }
    function hash(p) { var m=shell("/usr/bin/shasum -a 256 "+shquote(p)).match(/^([0-9a-fA-F]{64})\s/); if(!m) fail("cannot hash "+p); return m[1].toLowerCase(); }
    function find(group, name) { for(var i=1;i<=group.numProperties;i++) { var p=group.property(i); if(p.matchName===name) return p; if(p.numProperties>0) { var q=find(p,name); if(q) return q; } } return null; }
    function setParams(effect) { for(var i=0;i<SPEC.effect.params_full.length;i++) { var item=SPEC.effect.params_full[i]; var p=find(effect,item.match_name); if(!p) fail("missing property "+item.match_name); if(item.value !== null) { try { p.setValue(item.value); } catch(e) { fail("cannot set "+item.match_name); } } } }
    function capture(module, output) { if(!module.getSettings || typeof GetSettingsFormat === "undefined" || typeof GetSettingsFormat.STRING === "undefined") fail("Output Module settings API unavailable"); var s=module.getSettings(GetSettingsFormat.STRING); if(!s) fail("empty Output Module settings"); var path=output.replace(/\.exr$/i,"_output_module_settings.json"); write(path,stable({kind:"olm_output_module_settings_capture",schema_version:1,output_template:CONTRACT.output_template,capture_api:"OutputModule.getSettings(GetSettingsFormat.STRING)",settings:s})+"\n"); return {path:path,sha256:hash(path),serialization:stable(s)}; }
    function render(comp,effect,enabled,outDir,name) { effect.enabled=enabled; var item=app.project.renderQueue.items.add(comp); item.timeSpanStart=0; item.timeSpanDuration=1.0/comp.frameRate; var module=item.outputModule(1); module.applyTemplate(CONTRACT.output_template); var out=outDir+"/"+name, settings=capture(module,out); module.file=new File(out); app.project.renderQueue.render(); if(!new File(out).exists) fail("missing output "+out); var result={path:out,sha256:hash(out),output_module_settings:settings}; item.remove(); return result; }
    var inputDir=env("OLM_AE_MAC_INPUT_DIR"), outDir=env("OLM_AE_MAC_OUTPUT_DIR"), resultPath=env("OLM_AE_MAC_RESULT_JSON"), pluginPath=env("OLM_AE_MAC_PLUGIN_PATH"), inputName=env("OLM_AE_MAC_INPUT_NAME"), inputSha=env("OLM_AE_MAC_INPUT_SHA256");
    if(!inputDir||!outDir||!resultPath||!pluginPath||!inputName||!inputSha) fail("required environment missing");
    var pf=new File(pluginPath); if(!pf.exists||pf.name!==PLUGIN.filename) fail("plugin identity mismatch"); var loaded={filename:pf.name,path:pf.fsName,sha256:hash(pf.fsName)}; if(loaded.sha256!==PLUGIN.sha256) fail("plugin SHA-256 mismatch");
    var project=app.newProject(); project.bitsPerChannel=CONTRACT.bits_per_channel; project.linearBlending=false; try { project.gpuAccelType=GpuAccelType.SOFTWARE; } catch(e) { fail("cannot set SOFTWARE renderer"); }
    if(Number(project.bitsPerChannel)!==32||String(project.gpuAccelType).toUpperCase()!==CONTRACT.renderer) fail("project contract drift");
    if(project.workingSpace!=="None") fail("working space drift");
    var input=new File(inputDir+"/"+inputName); if(!input.exists||hash(input.fsName)!==inputSha) fail("input identity mismatch");
    var footage=project.importFile(new ImportOptions(input)), cs=SPEC.comp, comp=project.items.addComp(SPEC.id,cs.width,cs.height,cs.pixel_aspect,cs.duration,cs.frame_rate), layer=comp.layers.add(footage), effect=layer.property("ADBE Effect Parade").addProperty(SPEC.effect.match_name);
    if(!effect||effect.matchName!==SPEC.effect.match_name||effect.name!==SPEC.effect.name) fail("effect identity mismatch"); setParams(effect);
    var control=render(comp,effect,false,outDir,SPEC.id+"__before_effects_control.exr"), on=render(comp,effect,true,outDir,SPEC.id+"__effect_on.exr"); if(control.output_module_settings.serialization!==on.output_module_settings.serialization) fail("Output Module settings differ");
    write(resultPath,stable({kind:"olmkirakira_mode2_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,platform:"macOS",ae_version:app.version,request_id:"olmkirakira_mode2_32bpc_mac_validation_20260715",project:{bits_per_channel:project.bitsPerChannel,renderer:String(project.gpuAccelType),working_space:project.workingSpace,linear_blending:project.linearBlending,frame:0},output_module:{template_name:CONTRACT.output_template,capture_api:"OutputModule.getSettings(GetSettingsFormat.STRING)"},plugin:loaded,input:{name:inputName,sha256:inputSha},case:{id:SPEC.id,source_case_id:SPEC.source_case_id,params_full:SPEC.effect.params_full,params_sha256:SPEC.params_sha256,effect:{name:effect.name,match_name:effect.matchName,enabled:true},outputs:{before_effects_control:control,effect_on:on},same_comp_control:true}})+"\n"); try { project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch(e) {}
}());
'''.replace("CASE_JSON",case_json).replace("CONTRACT_JSON",contract_json).replace("PLUGIN_JSON",plugin_json)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plugin-path", type=Path, required=True)
    ap.add_argument("--input-path", type=Path, required=True)
    ap.add_argument("--support-dir", type=Path)
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--result-json", type=Path)
    ap.add_argument("--dump-js", type=Path)
    ap.add_argument("--app-name", default="Adobe After Effects 2026")
    ap.add_argument("--timeout", type=int, default=7200)
    args = ap.parse_args()
    try:
        data = load_request()
        if args.plugin_path.name != data["plugin"]["filename"] or not args.plugin_path.is_file(): raise ValueError("--plugin-path must name an existing OLMKiraKira.plugin")
        if not args.input_path.is_file(): raise ValueError("--input-path must name an existing source input")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("[FAIL_CLOSED] " + str(exc), file=sys.stderr); return 2
    support = (args.support_dir or Path(tempfile.mkdtemp(prefix=STEM+"_"))).resolve(); input_dir=support/"input"; output_dir=(args.output_dir or support/"return").resolve(); input_dir.mkdir(parents=True,exist_ok=True); output_dir.mkdir(parents=True,exist_ok=True)
    input_name=args.input_path.name; staged=input_dir/input_name; staged.write_bytes(args.input_path.read_bytes()); input_hash=sha256(staged)
    jsx=support/"run_mac_olmkirakira_mode2_32bpc_validation.jsx"; jsx.write_text(jsx_source(data),encoding="utf-8")
    result=(args.result_json or output_dir/"mac_validation_return.json").resolve(); env={"OLM_AE_MAC_INPUT_DIR":str(input_dir),"OLM_AE_MAC_INPUT_NAME":input_name,"OLM_AE_MAC_INPUT_SHA256":input_hash,"OLM_AE_MAC_OUTPUT_DIR":str(output_dir),"OLM_AE_MAC_RESULT_JSON":str(result),"OLM_AE_MAC_PLUGIN_PATH":str(args.plugin_path.resolve())}
    wrapper=support/"run_mac_wrapper.jsx"; wrapper.write_text("\n".join("$.setenv(%s,%s);"%(json.dumps(k),json.dumps(v)) for k,v in env.items())+"\n$.evalFile(new File(%s));\n"%json.dumps(str(jsx)),encoding="utf-8")
    if args.dump_js: args.dump_js.write_text(wrapper.read_text(encoding="utf-8"),encoding="utf-8"); print("[OK] wrote "+str(args.dump_js)); return 0
    proc=subprocess.run(["osascript"],input=f'tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n',text=True,capture_output=True,timeout=args.timeout+30)
    if proc.returncode or not result.is_file(): print("[FAIL_CLOSED] AE did not produce a return",file=sys.stderr); return 1
    report=subprocess.run([sys.executable,str(ROOT/"scripts/report_olmkirakira_mode2_32bpc_mac_validation_20260715.py"),str(result),"--output-dir",str(output_dir)],text=True)
    return report.returncode


if __name__ == "__main__": raise SystemExit(main())
