#!/usr/bin/env python3
"""Materialize the OLMDistanceGradation 32bpc Mac request; AE execution is explicit."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json"
AUDIT = ROOT / "refs/conformance/olmdistancegradation_32bpc_float_evidence_audit_20260715.json"
PLUGIN = "OLMDistanceGradation.plugin"

def load() -> tuple[dict, dict]:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if request["status"] != "sendable_fail_closed_no_ae_exact_claim":
        raise ValueError("request is not fail-closed")
    if request["candidate_case_count"] != audit["candidate_subset"]["case_count"]:
        raise ValueError("candidate count does not match Windows audit")
    return request, audit

def jsx_source(request: dict, audit: dict) -> str:
    cases = []
    for row in audit["cases"]:
        cases.append({"id": row["id"], "input": row["input"], "input_sha256": row["input_sha256"],
                      "windows_output": row["output"], "windows_output_sha256": row["output_sha256"],
                      "comp": row["comp"], "effect": row["effect"]})
    return r'''(function(){
var CASES=CASES_JSON, TEMPLATE="OLM EXR 32 Float", CAPTURE="OutputModule.getSettings(GetSettingsFormat.STRING)";
function fail(m){throw new Error("FAIL_CLOSED: "+m);} function env(n){try{return $.getenv(n)||"";}catch(e){return "";}}
function write(p,s){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))fail("cannot write "+p);f.write(s);f.close();}
function shell(c){return system.callSystem(c).replace(/[\r\n]+$/g,"");} function q(p){return "'"+String(p).replace(/'/g,"'\\''")+"'";}
function hash(p){var m=shell("/usr/bin/shasum -a 256 "+q(p)).match(/^([0-9a-fA-F]{64})\s/);if(!m)fail("cannot hash "+p);return m[1].toLowerCase();}
function stable(v){if(v===null)return"null";if(typeof v==="string")return JSON.stringify(v);if(typeof v==="number"||typeof v==="boolean")return String(v);if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(stable(v[i]));return"["+a.join(",")+"]";}if(typeof v==="object"){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(JSON.stringify(k[j])+":"+stable(v[k[j]]));return"{"+o.join(",")+"}";}fail("unsupported value");}
function find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties>0){var x=find(p,n);if(x)return x;}}return null;}
function setParams(e,ps){for(var i=0;i<ps.length;i++){var p=find(e,ps[i].match_name);if(!p)fail("missing "+ps[i].match_name);p.setValue(ps[i].value);}}
function settings(m,out){if(!m.getSettings||typeof GetSettingsFormat==="undefined")fail("settings API unavailable");var s=m.getSettings(GetSettingsFormat.STRING);if(!s)fail("empty output settings");var p=out.replace(/\.exr$/i,"_output_module_settings.json");write(p,stable({template_name:TEMPLATE,capture_api:CAPTURE,settings:s})+"\n");return{path:p,sha256:hash(p),serialization:stable(s)};}
function render(comp,e,on,dir,name){e.enabled=on;var item=app.project.renderQueue.items.add(comp);var m=item.outputModule(1);m.applyTemplate(TEMPLATE);var out=dir+"/"+name,st=settings(m,out);m.file=new File(out);app.project.renderQueue.render();if(!new File(out).exists)fail("missing "+out);item.remove();return{path:out,sha256:hash(out),output_module_settings:st,effect_enabled:on};}
var inputDir=env("OLM_AE_MAC_INPUT_DIR"),outDir=env("OLM_AE_MAC_OUTPUT_DIR"),result=env("OLM_AE_MAC_RESULT_JSON"),plugin=env("OLM_AE_MAC_PLUGIN_PATH");if(!inputDir||!outDir||!result||!plugin)fail("required environment missing");
var pf=new File(plugin);if(!pf.exists||pf.name!=="OLMDistanceGradation.plugin")fail("plugin identity mismatch");var loaded={filename:pf.name,path:pf.fsName,sha256:hash(pf.fsName)};
var project=app.newProject();project.bitsPerChannel=32;project.linearBlending=false;try{project.gpuAccelType=GpuAccelType.SOFTWARE;}catch(e){fail("cannot set SOFTWARE");}if(Number(project.bitsPerChannel)!==32||String(project.gpuAccelType).toUpperCase()!=="SOFTWARE"||project.workingSpace!=="None")fail("project/color contract mismatch");
var rows=[];for(var c=0;c<CASES.length;c++){var s=CASES[c],f=new File(inputDir+"/"+s.id+".exr");if(!f.exists||hash(f.fsName)!==s.input_sha256)fail(s.id+" input identity mismatch");var ft=project.importFile(new ImportOptions(f)),co=project.items.addComp(s.id,s.comp.width,s.comp.height,s.comp.pixel_aspect,s.comp.duration,s.comp.frame_rate),ly=co.layers.add(ft),e=ly.property("ADBE Effect Parade").addProperty(s.effect.match_name);if(!e||e.matchName!=="OLM Distance Gradation"||e.name!==s.effect.name)fail(s.id+" effect identity mismatch");setParams(e,s.effect.params);var control=render(co,e,false,outDir,s.id+"__no_effect.exr"),on=render(co,e,true,outDir,s.id+"__effect_on.exr");if(control.output_module_settings.serialization!==on.output_module_settings.serialization)fail(s.id+" output settings differ");rows.push({case_id:s.id,input_path:f.fsName,input_sha256:s.input_sha256,windows_reference:{path:s.windows_output,sha256:s.windows_output_sha256},outputs:{no_effect:control,effect_on:on},same_context_no_effect_control:{effect_enabled:false,project_id:s.id,output_settings_equal:true},all_12_distancegradation_parameter_match_names_and_values:s.effect.params});}
write(result,stable({kind:"olmdistancegradation_32bpc_mac_validation_return",schema:1,status:"candidate_return_only",ae_exact_claim:false,platform:"macOS",ae_version:app.version,project_settings:{bits_per_channel:project.bitsPerChannel,renderer_name_and_raw_value:{name:"SOFTWARE",raw_value:project.gpuAccelType},working_space:project.workingSpace,linear_blending:project.linearBlending},output_module:{template_name:TEMPLATE,capture_api:CAPTURE,format:"OpenEXR",sample_type:"FLOAT",compression:"none"},plugin:loaded,cases:rows})+"\n");try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}}());
'''.replace("CASES_JSON", json.dumps(cases, separators=(",", ":"), ensure_ascii=True))

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--plugin-path",type=Path,required=True);ap.add_argument("--support-dir",type=Path);ap.add_argument("--output-dir",type=Path);ap.add_argument("--result-json",type=Path);ap.add_argument("--dump-js",type=Path);ap.add_argument("--app-name",default="Adobe After Effects 2026");a=ap.parse_args()
    if a.plugin_path.name!=PLUGIN or not a.plugin_path.is_file(): print("[FAIL_CLOSED] --plugin-path must name an existing OLMDistanceGradation.plugin");return 2
    try: request,audit=load()
    except (OSError,ValueError,json.JSONDecodeError) as e: print("[FAIL_CLOSED] "+str(e));return 1
    support=a.support_dir or Path(tempfile.mkdtemp(prefix="olmdistancegradation_32bpc_mac_validation_20260715_")); output=a.output_dir or support/"return";support.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True);result=a.result_json or output/"mac_validation_return.json"
    inp=support/"input";inp.mkdir(exist_ok=True)
    for row in audit["cases"]:
        src=ROOT/"refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"/row["input"]
        if not src.is_file(): print("[FAIL_CLOSED] missing Windows input "+row["input"]);return 1
        shutil.copy2(src,inp/(row["id"]+".exr"))
    (support/"request_manifest.json").write_text(json.dumps(request,indent=2)+"\n",encoding="utf-8");jsx=support/"run_mac_olmdistancegradation_32bpc_validation.jsx";jsx.write_text(jsx_source(request,audit),encoding="utf-8")
    wrapper=support/"run_mac_wrapper.jsx";env={"OLM_AE_MAC_INPUT_DIR":str(inp.resolve()),"OLM_AE_MAC_OUTPUT_DIR":str(output.resolve()),"OLM_AE_MAC_RESULT_JSON":str(result.resolve()),"OLM_AE_MAC_PLUGIN_PATH":str(a.plugin_path.resolve())};wrapper.write_text("\n".join("$.setenv(%s,%s);"%(json.dumps(k),json.dumps(v)) for k,v in env.items())+"\n$.evalFile(new File(%s));\n"%json.dumps(str(jsx.resolve())),encoding="utf-8")
    if a.dump_js: a.dump_js.write_text(wrapper.read_text(encoding="utf-8"),encoding="utf-8");print("[OK] wrote "+str(a.dump_js));return 0
    try: p=subprocess.run(["osascript"],input=f'tell application {json.dumps(a.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n',text=True,capture_output=True,timeout=7200)
    except (OSError,subprocess.TimeoutExpired): print("[FAIL_CLOSED] AE did not produce a return");return 1
    if p.returncode or not result.exists(): print("[FAIL_CLOSED] AE did not produce a return");return 1
    check=subprocess.run([sys.executable,str(ROOT/"scripts/report_olmdistancegradation_32bpc_mac_validation_20260715.py"),str(result)],text=True);return check.returncode
if __name__=="__main__": raise SystemExit(main())
