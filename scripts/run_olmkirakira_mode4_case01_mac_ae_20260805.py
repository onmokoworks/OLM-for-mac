#!/usr/bin/env python3
"""Hash-bound Mac AE Software/32bpc runner for canonical KiraKira Mode4 case01.

Without --run this performs preparation/preflight only and never launches AE.
With --run it requires one already-running AE process and fails closed on a
conflicting loaded Kira module; effect application may load the exact installed
binary during the run.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.report_olmdistancegradation_32bpc_mac_validation_20260715 import compare
CASE_ID = "final_random10_olm_kira_kira_01"
REFDIR = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira"
MANIFEST = REFDIR / "reference_manifest.json"
INPUT = REFDIR / "olm_bitdepth_32bpc_olmkirakira_exr_20260710__software_32bpc__fr24__final_random10_olm_kira_kira_01_before_effects.exr"
EXPECTED = REFDIR / "olm_bitdepth_32bpc_olmkirakira_exr_20260710__software_32bpc__fr24__final_random10_olm_kira_kira_01.exr"
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
PLUGIN_SHA = "cd97c6f328bf6a4adbe001662f35c12af405f89a2374046f185f68673df96719"
INPUT_SHA = "8c1d418c7b853cc6f79087215ee86ab0b9eac423953c1a3409af3e120891a7f0"
EXPECTED_SHA = "810b76cde27a6590f0f2913d2e4f7bc2c1649c77b128a7c174d46b0088215c1d"
MANIFEST_SHA = "638cb66a60a52f4f9877f0f74937a891d447dc85673c8cca48c0780acf3ec9e7"

def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def case_contract():
    doc=json.loads(MANIFEST.read_text(encoding="utf-8")); cases=[c for c in doc["cases"] if c["id"]==CASE_ID]
    if len(cases)!=1: raise ValueError("canonical case cardinality")
    case=cases[0]; effect=case["effects"][0]
    params=[[p["match_name"],p["value"]] for p in effect["params"] if p.get("value_read_method")]
    values={p[0]:p[1] for p in params}
    if effect["match_name"]!="OLM OLM Kira Kira" or values.get("OLM OLM Kira Kira-0009")!=4:
        raise ValueError("not canonical Mode4 effect")
    if case["project_gpu_accel_type"]!={"current_name":"SOFTWARE","raw":1816} or case["comp"]["resolution_factor"]!=[1,1]:
        raise ValueError("project renderer/resolution drift")
    return case,params

def ae_pids():
    r=subprocess.run(["pgrep","-x","After Effects"],capture_output=True,text=True)
    return [int(x) for x in r.stdout.split() if x.isdigit()]

def loaded(pid:int):
    r=subprocess.run(["lsof","-Fn","-p",str(pid)],capture_output=True,text=True)
    return sorted({x[1:] for x in r.stdout.splitlines() if x.startswith("n/") and x.endswith("/Contents/MacOS/OLMKiraKira")})

def jsx(params, output:Path, returned:Path):
    return r'''(function(){
function Q(s){return '"'+String(s).replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\r/g,'\\r').replace(/\n/g,'\\n')+'"'}
function J(v){if(v===null)return "null";var t=typeof v;if(t==="string")return Q(v);if(t==="number"||t==="boolean")return String(v);if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(J(v[i]));return "["+a.join(",")+"]"}var z=[];for(var k in v)if(v.hasOwnProperty(k))z.push(Q(k)+":"+J(v[k]));return "{"+z.join(",")+"}"}
function W(p,o){var f=new File(p);f.encoding="UTF-8";if(f.open("w")){f.write(J(o));f.close()}}
function F(x){throw new Error("FAIL_CLOSED:"+x)}
function Find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var q=Find(p,n);if(q)return q}}return null}
if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.newProject();var project=app.project;if(!project)F("new project");project.bitsPerChannel=32;project.linearBlending=false;project.workingSpace="";project.gpuAccelType=GpuAccelType.SOFTWARE;
if(Number(project.bitsPerChannel)!==32||Number(project.gpuAccelType)!==1816)F("project");
var footage=project.importFile(new ImportOptions(new File(INPUT))),comp=project.items.addComp(CASE,1920,1080,1,1,24),layer=comp.layers.add(footage);comp.resolutionFactor=[1,1];comp.time=0;
var fx=layer.property("ADBE Effect Parade").addProperty("OLM OLM Kira Kira");if(!fx||fx.matchName!=="OLM OLM Kira Kira")F("effect");
var ps=PARAMS,rb=[];for(var i=0;i<ps.length;i++){var p=Find(fx,ps[i][0]);if(!p)F("param "+ps[i][0]);p.setValue(ps[i][1]);rb.push([p.matchName,p.value])}
var rq=project.renderQueue.items.add(comp),om=rq.outputModule(1);rq.timeSpanStart=0;rq.timeSpanDuration=1/comp.frameRate;om.applyTemplate("OLM EXR 32 Float");om.file=new File(OUTPUT);app.project.renderQueue.render();var nominal=new File(OUTPUT);if(!nominal.exists){var candidates=nominal.parent.getFiles(nominal.name+"*"),produced=[];for(var n=0;n<candidates.length;n++)if(candidates[n] instanceof File)produced.push(candidates[n]);if(produced.length!==1||!produced[0].copy(nominal.fsName))F("single EXR output");produced[0].remove();}if(!nominal.exists)F("output missing");
W(RETURNED,{status:"ok",ae_version:app.version,project:{bpc:project.bitsPerChannel,renderer:"SOFTWARE",resolution:comp.resolutionFactor},effect:{name:fx.name,match_name:fx.matchName},params:ps,readback:rb,output:om.file.fsName});
}());'''.replace("INPUT",json.dumps(str(INPUT))).replace("CASE",json.dumps(CASE_ID)).replace("PARAMS",json.dumps(params,separators=(",",":"))).replace("OUTPUT",json.dumps(str(output))).replace("RETURNED",json.dumps(str(returned)))

def loader_jsx(payload: Path, trace: Path) -> str:
    return (
        "(function(){\n"
        "var traceFile=new File(" + json.dumps(str(trace.resolve())) + "),payloadFile=new File(" + json.dumps(str(payload.resolve())) + ");\n"
        "function append(m){traceFile.encoding=\"UTF-8\";if(traceFile.open(\"a\")){traceFile.write(String(m)+\"\\n\");traceFile.close();}}\n"
        "append(\"LOADER_ENTER payload=\"+payloadFile.fsName);\n"
        "try{$.evalFile(payloadFile);append(\"LOADER_RETURN\");}"
        "catch(e){append(\"LOADER_FAIL error=\"+String(e)+\" line=\"+String(e.line||0)+\" file=\"+String(e.fileName||\"\"));}\n"
        "}());\n"
    )

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run",action="store_true");ap.add_argument("--report",type=Path,default=ROOT/"refs/reports/olmkirakira_mode4_case01_mac_preflight_20260805.json");a=ap.parse_args()
    error=None
    try: case,params=case_contract()
    except Exception as e: case,params,error=None,[],str(e)
    pids=ae_pids(); modules={str(p):loaded(p) for p in pids}; expected_path=str(PLUGIN.resolve()) if PLUGIN.exists() else None
    mapped=modules.get(str(pids[0]),[]) if len(pids)==1 else []
    checks={"installed_sha":sha(PLUGIN),"installed_sha_matches":sha(PLUGIN)==PLUGIN_SHA,"input_sha_matches":sha(INPUT)==INPUT_SHA,"expected_sha_matches":sha(EXPECTED)==EXPECTED_SHA,"manifest_sha_matches":sha(MANIFEST)==MANIFEST_SHA,"case_contract_exact":error is None,"case_error":error,"mode4_value":dict(params).get("OLM OLM Kira Kira-0009"),"software_renderer":bool(case and case["project_gpu_accel_type"]["current_name"]=="SOFTWARE"),"bpc":32,"ae_pids":pids,"loaded_modules":modules,"loaded_identity_exact":len(pids)==1 and mapped==[expected_path],"clean_single_ae_without_conflicting_kira_module":len(pids)==1 and mapped in ([],[expected_path])}
    static_ready=all(checks[k] for k in ("installed_sha_matches","input_sha_matches","expected_sha_matches","manifest_sha_matches","case_contract_exact","software_renderer"))
    host_ready=static_ready and checks["clean_single_ae_without_conflicting_kira_module"]
    report={"schema":"olmkirakira-mode4-mac-ae-runner/1","case_id":CASE_ID,"status":"ready_to_bind_after_user_starts_ae" if static_ready and not host_ready else "ready" if host_ready else "blocked","run_requested":a.run,"run_executed":False,"checks":checks,"contract":{"renderer":"Software","bits_per_channel":32,"resolution_factor":[1,1],"working_space":"None","linear_blending":False,"effect_match_name":"OLM OLM Kira Kira","params":params,"expected_exr_sha256":EXPECTED_SHA,"installed_binary_sha256":PLUGIN_SHA}}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    if not a.run or not host_ready:
        a.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":report["status"],"report":str(a.report)}));return 0 if static_ready and not a.run else 2
    out=a.report.parent/(CASE_ID+"_mac.exr");returned=a.report.parent/(CASE_ID+"_ae_return.json");trace=a.report.parent/(CASE_ID+"_loader_trace.log")
    with tempfile.TemporaryDirectory(prefix="olmkira-mode4-ae-") as td:
        payload=Path(td)/"payload.jsx";loader=Path(td)/"loader.jsx"
        payload.write_text(jsx(params,out,returned),encoding="utf-8");loader.write_text(loader_jsx(payload,trace),encoding="utf-8")
        cmd=f'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file {json.dumps(str(loader))} with override\n';cp=subprocess.run(["osascript"],input=cmd,text=True,capture_output=True)
    post_pids=ae_pids();post_modules={str(p):loaded(p) for p in post_pids}
    post_identity=len(post_pids)==1 and post_pids==pids and post_modules.get(str(post_pids[0]))==[expected_path] and sha(PLUGIN)==PLUGIN_SHA
    returned_payload=None
    if returned.is_file():
        try: returned_payload=json.loads(returned.read_text(encoding="utf-8"))
        except Exception as e: returned_payload={"status":"invalid_json","trace":str(e)}
    report["run_executed"]=True;report["osascript"]={"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr}
    report["ae_return"]=returned_payload;report["post_identity"]={"ae_pids":post_pids,"loaded_modules":post_modules,"exact_same_pid_and_module":post_identity}
    report["loader_trace"]={"path":str(trace),"text":trace.read_text(encoding="utf-8",errors="replace") if trace.is_file() else None}
    report["output_sha256"]=sha(out)
    try: raw_compare=compare(out,EXPECTED) if out.is_file() else None
    except Exception as e: raw_compare={"equal":False,"error":str(e)}
    report["raw_float32_compare"]=raw_compare
    report["status"]="exact" if cp.returncode==0 and returned_payload and returned_payload.get("status")=="ok" and post_identity and raw_compare and raw_compare.get("equal") is True else "mismatch"
    a.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":report["status"],"report":str(a.report)}));return 0 if report["status"]=="exact" else 1
if __name__=="__main__": raise SystemExit(main())
