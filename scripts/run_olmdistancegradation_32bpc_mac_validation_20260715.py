#!/usr/bin/env python3
"""Materialize the OLMDistanceGradation 32bpc Mac request; AE execution is explicit."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json"
AUDIT = ROOT / "refs/conformance/olmdistancegradation_32bpc_float_evidence_audit_20260715.json"
PLUGIN = "OLMDistanceGradation.plugin"
PLUGIN_SHA256 = "656537d052f67a9e7eb4d4ba2c6f5c890fe34e3d2c47069bcfba01854d96055e"

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
function quote(v){return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r/g,"\\r").replace(/\n/g,"\\n").replace(/\t/g,"\\t")+'"';}
function stable(v){if(v===null)return"null";if(typeof v==="string")return quote(v);if(typeof v==="number"||typeof v==="boolean")return String(v);if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(stable(v[i]));return"["+a.join(",")+"]";}if(typeof v==="object"){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(quote(k[j])+":"+stable(v[k[j]]));return"{"+o.join(",")+"}";}fail("unsupported value");}
function find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties>0){var x=find(p,n);if(x)return x;}}return null;}
function setParams(e,ps){for(var i=0;i<ps.length;i++){var p=find(e,ps[i].match_name);if(!p)fail("missing "+ps[i].match_name);p.setValue(ps[i].value);}}
function settings(m,out){if(!m.getSettings||typeof GetSettingsFormat==="undefined")fail("settings API unavailable");var s=m.getSettings(GetSettingsFormat.STRING);if(!s)fail("empty output settings");var p=out.replace(/\.exr$/i,"_output_module_settings.json");write(p,stable({template_name:TEMPLATE,capture_api:CAPTURE,settings:s})+"\n");return{path:p,sha256:hash(p),serialization:stable(s)};}
function render(comp,e,on,dir,name){e.enabled=on;var item=app.project.renderQueue.items.add(comp);item.timeSpanStart=0;item.timeSpanDuration=1/comp.frameRate;var m=item.outputModule(1);m.applyTemplate(TEMPLATE);var nominal=dir+"/"+name,st=settings(m,nominal);m.file=new File(nominal);app.project.renderQueue.render();var candidates=new Folder(dir).getFiles(name+"*"),produced=[];for(var i=0;i<candidates.length;i++){if(candidates[i] instanceof File&&candidates[i].name.indexOf("_output_module_settings.json")<0)produced.push(candidates[i]);}if(produced.length!==1)fail("expected one output for "+nominal+", got "+produced.length);var out=produced[0].fsName;item.remove();return{path:out,sha256:hash(out),output_module_settings:st,effect_enabled:on};}
var tracePath=env("OLM_AE_MAC_TRACE_PATH");function trace(s){if(tracePath){var f=new File(tracePath);f.encoding="UTF-8";if(f.open("a")){f.writeln(s);f.close();}}}
try{
var inputDir=env("OLM_AE_MAC_INPUT_DIR"),outDir=env("OLM_AE_MAC_OUTPUT_DIR"),result=env("OLM_AE_MAC_RESULT_JSON"),bundle=env("OLM_AE_MAC_PLUGIN_BUNDLE"),plugin=env("OLM_AE_MAC_PLUGIN_EXECUTABLE");if(!inputDir||!outDir||!result||!bundle||!plugin)fail("required environment missing");trace("PRE pid-bound wrapper entered");
var bd=new Folder(bundle),pf=new File(plugin);if(!bd.exists||bd.name!=="OLMDistanceGradation.plugin"||!pf.exists||pf.name!=="OLMDistanceGradation")fail("plugin identity mismatch");var ph=hash(pf.fsName);if(ph!=="PLUGIN_SHA256")fail("plugin sha256 mismatch");var loaded={bundle_name:bd.name,bundle_path:bd.fsName,filename:pf.name,path:pf.fsName,sha256:ph,identity_kind:"unique installed candidate plus successful effect match-name load"};
app.newProject();var project=app.project;if(!project)fail("app.newProject produced no app.project");project.bitsPerChannel=32;project.linearBlending=false;try{project.gpuAccelType=GpuAccelType.SOFTWARE;}catch(e){fail("cannot set SOFTWARE");}if(Number(project.bitsPerChannel)!==32||project.gpuAccelType!==GpuAccelType.SOFTWARE||project.workingSpace!=="None")fail("project/color contract mismatch");
var rows=[];for(var c=0;c<CASES.length;c++){var s=CASES[c],f=new File(inputDir+"/"+s.id+".exr");if(!f.exists||hash(f.fsName)!==s.input_sha256)fail(s.id+" input identity mismatch");var ft=project.importFile(new ImportOptions(f)),co=project.items.addComp(s.id,s.comp.width,s.comp.height,s.comp.pixel_aspect,s.comp.duration,s.comp.frame_rate),ly=co.layers.add(ft),e=ly.property("ADBE Effect Parade").addProperty(s.effect.match_name);if(!e||e.matchName!=="OLM Distance Gradation"||e.name!==s.effect.name)fail(s.id+" effect identity mismatch");trace("EFFECT_ADD "+e.matchName);setParams(e,s.effect.params);var control=render(co,e,false,outDir,s.id+"__no_effect.exr"),on=render(co,e,true,outDir,s.id+"__effect_on.exr");trace("RAW_FLOAT_OUTPUT no_effect="+control.sha256+" effect_on="+on.sha256);if(control.output_module_settings.serialization!==on.output_module_settings.serialization)fail(s.id+" output settings differ");rows.push({case_id:s.id,input_path:f.fsName,input_sha256:s.input_sha256,windows_reference:{path:s.windows_output,sha256:s.windows_output_sha256},outputs:{no_effect:control,effect_on:on},same_context_no_effect_control:{effect_enabled:false,project_id:s.id,output_settings_equal:true},all_12_distancegradation_parameter_match_names_and_values:s.effect.params});}
write(result,stable({kind:"olmdistancegradation_32bpc_mac_validation_return",schema:1,status:"candidate_return_only",ae_exact_claim:false,platform:"macOS",ae_version:app.version,project_settings:{bits_per_channel:project.bitsPerChannel,renderer_name_and_raw_value:{name:"SOFTWARE",raw_value:project.gpuAccelType},working_space:project.workingSpace,linear_blending:project.linearBlending},output_module:{template_name:TEMPLATE,capture_api:CAPTURE,format:"OpenEXR",sample_type:"FLOAT",compression:"none"},plugin:loaded,cases:rows})+"\n");trace("POST identity="+ph+" return="+result);try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}
}catch(e){trace("PAYLOAD_FAIL error="+e.toString()+" line="+(e.line||0)+" file="+(e.fileName||""));}}());
'''.replace("CASES_JSON", json.dumps(cases, separators=(",", ":"), ensure_ascii=True)).replace("PLUGIN_SHA256", PLUGIN_SHA256)

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--plugin-path",type=Path,required=True);ap.add_argument("--support-dir",type=Path);ap.add_argument("--output-dir",type=Path);ap.add_argument("--result-json",type=Path);ap.add_argument("--dump-js",type=Path);ap.add_argument("--case-id");ap.add_argument("--app-name",default="Adobe After Effects 2026");a=ap.parse_args()
    executable=a.plugin_path/"Contents/MacOS/OLMDistanceGradation"
    if a.plugin_path.name!=PLUGIN or not a.plugin_path.is_dir() or not executable.is_file(): print("[FAIL_CLOSED] --plugin-path must name an existing OLMDistanceGradation.plugin bundle");return 2
    actual_sha=hashlib.sha256(executable.read_bytes()).hexdigest()
    if not a.dump_js and actual_sha!=PLUGIN_SHA256: print("[FAIL_CLOSED] installed executable sha256 mismatch");return 2
    try: request,audit=load()
    except (OSError,ValueError,json.JSONDecodeError) as e: print("[FAIL_CLOSED] "+str(e));return 1
    if a.case_id:
        selected=[row for row in audit["cases"] if row["id"]==a.case_id]
        if len(selected)!=1: print("[FAIL_CLOSED] unknown or duplicate --case-id");return 2
        audit=dict(audit);audit["cases"]=selected
    support=a.support_dir or Path(tempfile.mkdtemp(prefix="olmdistancegradation_32bpc_mac_validation_20260715_")); output=a.output_dir or support/"return";support.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True);result=a.result_json or output/"mac_validation_return.json"
    inp=support/"input";inp.mkdir(exist_ok=True)
    for row in audit["cases"]:
        src=ROOT/"refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"/row["input"]
        if not src.is_file(): print("[FAIL_CLOSED] missing Windows input "+row["input"]);return 1
        shutil.copy2(src,inp/(row["id"]+".exr"))
    (support/"request_manifest.json").write_text(json.dumps(request,indent=2)+"\n",encoding="utf-8");jsx=support/"run_mac_olmdistancegradation_32bpc_validation.jsx";jsx.write_text(jsx_source(request,audit),encoding="utf-8")
    wrapper=support/"run_mac_wrapper.jsx";trace=(output/"host_trace.log").resolve();env={"OLM_AE_MAC_INPUT_DIR":str(inp.resolve()),"OLM_AE_MAC_OUTPUT_DIR":str(output.resolve()),"OLM_AE_MAC_RESULT_JSON":str(result.resolve()),"OLM_AE_MAC_TRACE_PATH":str(trace),"OLM_AE_MAC_PLUGIN_BUNDLE":str(a.plugin_path.resolve()),"OLM_AE_MAC_PLUGIN_EXECUTABLE":str(executable.resolve())}
    env_lines="\n".join("$.setenv(%s,%s);"%(json.dumps(k),json.dumps(v)) for k,v in env.items())
    loader=("(function(){\n"+env_lines+"\n"
            "var traceFile=new File("+json.dumps(str(trace))+"),payloadFile=new File("+json.dumps(str(jsx.resolve()))+");\n"
            "function append(s){traceFile.encoding=\"UTF-8\";if(traceFile.open(\"a\")){traceFile.writeln(s);traceFile.close();}}\n"
            "append(\"LOADER_ENTER payload=\"+payloadFile.fsName);\n"
            "try{$.evalFile(payloadFile);append(\"LOADER_RETURN\");}catch(e){append(\"LOADER_FAIL error=\"+e.toString()+\" line=\"+(e.line||0)+\" file=\"+(e.fileName||\"\"));}\n"
            "}());\n")
    wrapper.write_text(loader,encoding="utf-8")
    if a.dump_js: a.dump_js.write_text(wrapper.read_text(encoding="utf-8"),encoding="utf-8");print("[OK] wrote "+str(a.dump_js));return 0
    try: p=subprocess.run(["osascript"],input=f'tell application {json.dumps(a.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n',text=True,capture_output=True,timeout=7200)
    except (OSError,subprocess.TimeoutExpired): print("[FAIL_CLOSED] AE did not produce a return");return 1
    if p.returncode or not result.exists(): print("[FAIL_CLOSED] AE did not produce a return");return 1
    check_cmd=[sys.executable,"-m","scripts.report_olmdistancegradation_32bpc_mac_validation_20260715",str(result)]
    if a.case_id: check_cmd.extend(["--case-id",a.case_id])
    check=subprocess.run(check_cmd,text=True);return check.returncode
if __name__=="__main__": raise SystemExit(main())
