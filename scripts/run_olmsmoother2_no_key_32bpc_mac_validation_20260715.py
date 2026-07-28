#!/usr/bin/env python3
"""Run the explicit OLMSmoother2 v2/no-key Mac AE candidate request."""
from __future__ import annotations
import argparse, hashlib, json, secrets, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json"; STEM = "olmsmoother2_no_key_32bpc_mac_validation_20260715"
INPUT_TEMPLATE = ROOT / "refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep"
INPUT_TEMPLATE_SHA256 = "51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v: object) -> str: return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
def contained_file(base: Path, candidate: Path, label: str) -> Path:
    if base.is_symlink():
        raise ValueError(f"{label}: symlinks are forbidden")
    base = base.resolve(strict=True)
    if not base.is_dir() or candidate.is_symlink():
        raise ValueError(f"{label}: symlinks are forbidden")
    resolved = candidate.resolve(strict=False)
    if resolved.parent != base:
        raise ValueError(f"{label}: path must be directly inside the dedicated output directory")
    return resolved
def after_effects_processes() -> list[tuple[int, str]]:
    """Return every visible AE process, failing closed if process inspection fails."""
    try:
        p = subprocess.run(
            ["/bin/ps", "-axo", "pid=,comm=,args="],
            text=True, capture_output=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"cannot inspect running processes: {e}") from e
    if p.returncode:
        raise RuntimeError(f"cannot inspect running processes: {p.stderr.strip() or 'ps failed'}")
    found: list[tuple[int, str]] = []
    for line in p.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2 or not fields[0].isdigit():
            continue
        command = fields[1]
        lowered = command.lower()
        if "afterfx" in lowered or "adobe after effects" in lowered:
            found.append((int(fields[0]), command))
    return found
def refuse_unsafe_direct_execution(wrapper: Path) -> int:
    """Never address AE by app name: Apple events cannot bind this run to an owned PID."""
    try:
        running = after_effects_processes()
    except RuntimeError as e:
        print(f"[FAIL_CLOSED] {e}")
        return 1
    if running:
        detail = ", ".join(f"pid {pid}: {command}" for pid, command in running)
        print(f"[FAIL_CLOSED] After Effects is already running ({detail}); no Apple event was sent and no process was terminated.")
        return 1
    print("[FAIL_CLOSED] Direct execution is disabled: macOS osascript addresses After Effects by application name and cannot robustly bind DoScriptFile to a runner-owned PID.")
    print("[SAFE_MANUAL] Keep all existing After Effects instances closed, launch a dedicated validation instance yourself, then use File > Scripts > Run Script File and select:")
    print(f"[SAFE_MANUAL] {wrapper.resolve()}")
    return 1
def jsx_source(case: dict, contract_hash: str, output_template: str, nonce: str) -> str:
    setup = json.loads(REQUEST.read_text(encoding="utf-8"))["common_setup"]
    case = {**case, "run_nonce": nonce, "comp": {"width": setup["comp_width"], "height": setup["comp_height"], "pixel_aspect": 1, "frame_rate": setup["frame_rate"]}}
    c = json.dumps(case, separators=(",", ":"), ensure_ascii=True); return r'''(function(){var spec=CASE_JSON, CONTRACT=CONTRACT_JSON, TEMPLATE=OUTPUT_TEMPLATE_JSON, RUN_NONCE=spec.run_nonce, API="OutputModule.getSettings(GetSettingsFormat.STRING)";
function env(n){try{return $.getenv(n)||"";}catch(e){return "";}} function fail(m){throw new Error("FAIL_CLOSED: "+m);} function q(v){return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"')+'"';} function stable(v){if(v===null)return"null";if(typeof v==="string")return q(v);if(typeof v==="number"){if(!isFinite(v))fail("nonfinite");return String(v);}if(typeof v==="boolean")return v?"true":"false";if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(stable(v[i]));return"["+a.join(",")+"]";}if(typeof v==="object"){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(q(k[j])+":"+stable(v[k[j]]));return"{"+o.join(",")+"}";}fail("unsupported");} function write(p,s){var f=new File(p);if(f.exists)fail("stale/preexisting "+p);f.encoding="UTF-8";if(!f.open("w"))fail("write "+p);f.write(s);f.close();} function sh(p){return system.callSystem("/usr/bin/shasum -a 256 '"+String(p).replace(/'/g,"'\\''")+"'").replace(/[\r\n]+$/g,"");} function hash(p){var m=sh(p).match(/^([0-9a-fA-F]{64})\s/);if(!m)fail("hash "+p);return m[1].toLowerCase();} function prop(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var x=prop(p,n);if(x)return x;}}return null;} function eq(a,b){return stable(a)===stable(b);} function readback(e,on){if(e.matchName!=="OLM Smoother v2"||e.name!=="OLM Smoother v2"||Boolean(e.enabled)!==on)fail("effect identity/enabled readback");var r=[];for(var i=0;i<spec.params_full.length;i++){var x=spec.params_full[i],p=prop(e,x.match_name);if(!p||p.matchName!==x.match_name||p.name!==x.name||Number(p.propertyIndex)!==Number(x.property_index)||!eq(p.value,x.value))fail("parameter readback "+x.match_name);r.push({name:p.name,match_name:p.matchName,property_index:Number(p.propertyIndex),value:p.value});}return{effect:{name:e.name,match_name:e.matchName,enabled:Boolean(e.enabled)},params:r};} function params(e){for(var i=0;i<spec.params_full.length;i++){var x=spec.params_full[i],p=prop(e,x.match_name);if(!p)fail("missing "+x.match_name);p.setValue(x.value);}readback(e,Boolean(e.enabled));} function capture(m,p){if(!m.getSettings||typeof GetSettingsFormat==="undefined")fail("settings API");var s=m.getSettings(GetSettingsFormat.STRING);var path=p.replace(/\.exr$/i,"_output_module_settings.json");write(path,stable({kind:"olm_output_module_settings_capture",run_nonce:RUN_NONCE,output_template:TEMPLATE,capture_api:API,output_path:m.file.fsName,settings:s})+"\n");return{path:path,sha256:hash(path),serialization:stable(s),output_path:m.file.fsName,settings:s};} function renderedFile(p){var t=new File(p);if(t.exists)return t;var matches=t.parent.getFiles(function(x){return x instanceof File&&x.name.indexOf(t.name)===0;});if(matches.length!==1)fail("rendered output cardinality for "+p+": "+matches.length);if(!matches[0].rename(t.name)||!t.exists)fail("cannot normalize rendered output "+matches[0].fsName);return t;} function render(comp,e,on,out,name){e.enabled=on;var before=readback(e,on);var item=app.project.renderQueue.items.add(comp);item.timeSpanStart=0;item.timeSpanDuration=1/comp.frameRate;var m=item.outputModule(1);m.applyTemplate(TEMPLATE);var p=out+"/"+name;if(new File(p).exists||new File(p.replace(/\.exr$/i,"_output_module_settings.json")).exists)fail("stale output");m.file=new File(p);var s=capture(m,p);app.project.renderQueue.render();var after=readback(e,on),rendered=renderedFile(p),r={path:rendered.fsName,sha256:hash(rendered.fsName),output_module_settings:s,effect_enabled:on,readback_before_render:before,readback_after_render:after};item.remove();return r;}
var inputDir=env("OLM_AE_MAC_INPUT_DIR"),out=env("OLM_AE_MAC_OUTPUT_DIR"),result=env("OLM_AE_MAC_RESULT_JSON"),pluginPath=env("OLM_AE_MAC_PLUGIN_PATH"),pluginBinaryPath=env("OLM_AE_MAC_PLUGIN_BINARY_PATH"),projectTemplatePath=env("OLM_AE_MAC_PROJECT_TEMPLATE"),projectTemplateSha256=env("OLM_AE_MAC_PROJECT_TEMPLATE_SHA256"),macosProductVersion=env("OLM_MACOS_PRODUCT_VERSION"),macosBuildVersion=env("OLM_MACOS_BUILD_VERSION");if(!inputDir||!out||!result||!pluginPath||!pluginBinaryPath||!projectTemplatePath||!projectTemplateSha256||!macosProductVersion||!macosBuildVersion)fail("environment");var pf=new Folder(pluginPath),pb=new File(pluginBinaryPath);if(!pf.exists||pf.name!=="OLMSmoother2.plugin"||!pb.exists||pb.name!=="OLMSmoother2")fail("plugin identity");var templateFile=new File(projectTemplatePath);if(!templateFile.exists||hash(templateFile.fsName)!==projectTemplateSha256)fail("Preserve RGB project template identity");var plugin={filename:pf.name,path:pf.fsName,binary_path:pb.fsName,sha256:hash(pb.fsName)},pr=app.open(templateFile);pr.bitsPerChannel=32;pr.linearBlending=false;pr.workingSpace="";try{pr.gpuAccelType=GpuAccelType.SOFTWARE;}catch(e){fail("SOFTWARE");}var workingSpaceRaw=pr.workingSpace,workingSpaceText=String(workingSpaceRaw);if(Number(pr.bitsPerChannel)!==32||Number(pr.gpuAccelType)!==Number(GpuAccelType.SOFTWARE)||(workingSpaceText!==""&&workingSpaceText!=="None"))fail("project contract: bpc="+pr.bitsPerChannel+" renderer="+pr.gpuAccelType+" working_space_raw="+workingSpaceRaw);var f=new File(inputDir+"/"+spec.input.filename);if(!f.exists||hash(f.fsName)!==spec.input.sha256)fail("input identity");var ft=null,co=null;for(var ii=1;ii<=pr.numItems;ii++){var pi=pr.item(ii);if(pi.name==="OLM_COLOR_PROBE_INPUT")ft=pi;if(pi.name==="OLM_COLOR_PROBE_COMP")co=pi;}if(!ft||!co)fail("Preserve RGB template items");ft.replace(f);var cs=spec.comp;if(co.width!==cs.width||co.height!==cs.height||co.pixelAspect!==cs.pixel_aspect||co.frameRate!==cs.frame_rate||co.numLayers!==1)fail("template comp contract");while(pr.renderQueue.numItems)pr.renderQueue.item(pr.renderQueue.numItems).remove();co.name=spec.id;var ly=co.layer(1);if(!ly||ly.source!==ft)fail("template footage binding");var effects=ly.property("ADBE Effect Parade");if(!effects||effects.numProperties!==0)fail("template effect contamination");var e=effects.addProperty("OLM Smoother v2");if(!e||e.matchName!=="OLM Smoother v2"||e.name!=="OLM Smoother v2")fail("effect identity");params(e);var no=render(co,e,false,out,spec.id+"__no_effect.exr"),yes=render(co,e,true,out,spec.id+"__effect_on.exr");if(no.output_module_settings.serialization!==yes.output_module_settings.serialization)fail("settings differ");write(result,stable({kind:"olmsmoother2_no_key_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,ae_exact_claim_reason:"Windows artifact attestation and raw FLOAT32 comparison are pending",platform:"macOS",macos_product_version:macosProductVersion,macos_build_version:macosBuildVersion,ae_version:app.version,case_contract_sha256:CONTRACT,input_interpretation:{method:"hash_bound_aep_template_footage_replace",template_path:templateFile.fsName,template_sha256:projectTemplateSha256,preserve_rgb:true,verification:"no_effect_raw_float32_gate"},project:{bits_per_channel:pr.bitsPerChannel,renderer:"SOFTWARE",working_space:"None",working_space_raw:workingSpaceRaw,linear_blending:pr.linearBlending,comp:{width:cs.width,height:cs.height,frame_rate:cs.frame_rate}},output_module:{template_name:TEMPLATE,capture_api:API,channels:["A","B","G","R"],sample_type:"FLOAT",compression:"none"},plugin:plugin,cases:[{id:spec.id,input:spec.input,params_full:spec.params_full,effect:{name:e.name,match_name:e.matchName,enabled:true},outputs:{no_effect_control:no,effect_on:yes},no_effect_control_passed:true}]})+"\n");try{pr.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}}());'''.replace("CASE_JSON", c).replace("CONTRACT_JSON", json.dumps(contract_hash)).replace("OUTPUT_TEMPLATE_JSON", json.dumps(output_template))
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--plugin-path",type=Path,required=True); ap.add_argument("--support-dir",type=Path); ap.add_argument("--output-dir",type=Path); ap.add_argument("--result-json",type=Path); ap.add_argument("--dump-js",type=Path); ap.add_argument("--app-name",default="Adobe After Effects 2026"); a=ap.parse_args()
    plugin_binary = a.plugin_path / "Contents" / "MacOS" / "OLMSmoother2"
    if a.plugin_path.name!="OLMSmoother2.plugin" or not a.plugin_path.is_dir() or not plugin_binary.is_file(): print("[FAIL_CLOSED] --plugin-path must name an existing OLMSmoother2.plugin bundle"); return 2
    if not INPUT_TEMPLATE.is_file() or sha256(INPUT_TEMPLATE) != INPUT_TEMPLATE_SHA256: print("[FAIL_CLOSED] Preserve RGB project template missing or hash mismatch"); return 1
    data=json.loads(REQUEST.read_text()); case=data["cases"][0]; support=a.support_dir or Path(tempfile.mkdtemp(prefix=STEM+"_")); (support/"input").mkdir(parents=True,exist_ok=True); reference=data["windows_reference"]; src=ROOT/reference["artifact_root"]/reference["before_effects_frame"]; output_template=data["mac_run_contract"]["output_template"]
    if not src.is_file() or sha256(src)!=reference["before_effects_sha256"]: print("[FAIL_CLOSED] Windows input missing or hash mismatch"); return 1
    if not output_template: print("[FAIL_CLOSED] output template is empty"); return 1
    shutil=None
    try:
        macos_product_version=subprocess.check_output(["/usr/bin/sw_vers","-productVersion"],text=True).strip()
        macos_build_version=subprocess.check_output(["/usr/bin/sw_vers","-buildVersion"],text=True).strip()
    except (OSError,subprocess.CalledProcessError) as e:
        print(f"[FAIL_CLOSED] macOS host identity unavailable: {e}"); return 1
    if not macos_product_version or not macos_build_version: print("[FAIL_CLOSED] macOS host identity is empty"); return 1
    import shutil as _shutil
    _shutil.copy2(src,support/"input"/src.name)
    out=(a.output_dir or support/"return")
    out.mkdir(parents=True,exist_ok=True)
    try:
        out=out.resolve(strict=True)
        result=contained_file(out, a.result_json or out/"mac_validation_return.json", "result")
    except (OSError,ValueError) as e:
        print(f"[FAIL_CLOSED] {e}"); return 1
    nonce=secrets.token_hex(32)
    expected_names=[
        "mac_validation_return.json",
        case["id"]+"__no_effect.exr", case["id"]+"__effect_on.exr",
        case["id"]+"__no_effect_output_module_settings.json",
        case["id"]+"__effect_on_output_module_settings.json",
    ]
    expected_paths=[contained_file(out,out/name,name) for name in expected_names]
    if len(set(expected_paths))!=len(expected_paths) or result != expected_paths[0]:
        print("[FAIL_CLOSED] duplicate or basename-alias output paths"); return 1
    if any(path.exists() or path.is_symlink() for path in expected_paths):
        print("[FAIL_CLOSED] stale/preexisting result or output exists"); return 1
    challenge=contained_file(out,out/"run_challenge.json","challenge")
    if challenge.exists() or challenge.is_symlink():
        print("[FAIL_CLOSED] stale/preexisting challenge exists"); return 1
    started=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    challenge.write_text(json.dumps({"kind":"olmsmoother2_mac_run_challenge","run_nonce":nonce,"started_at":started,"result_path":str(result),"output_paths":{"no_effect_control":{"exr":str(expected_paths[1]),"settings":str(expected_paths[3])},"effect_on":{"exr":str(expected_paths[2]),"settings":str(expected_paths[4])}}},indent=2)+"\n",encoding="utf-8")
    jsx=support/"run_mac_olmsmoother2_no_key_32bpc_validation.jsx"
    run_case={**case,"input":{"filename":src.name,"sha256":sha256(src)}}
    ch=canonical({"request_id":data["request_id"],"case":run_case,"common_setup":data["common_setup"],"mac_run_contract":data["mac_run_contract"],"output_template":output_template})
    jsx.write_text(jsx_source(run_case,ch,output_template,nonce),encoding="utf-8")
    wrapper=support/"run_mac_wrapper.jsx"
    env={"OLM_AE_MAC_INPUT_DIR":str((support/"input").resolve()),"OLM_AE_MAC_OUTPUT_DIR":str(out),"OLM_AE_MAC_RESULT_JSON":str(result),"OLM_AE_MAC_RUN_NONCE":nonce,"OLM_AE_MAC_PLUGIN_PATH":str(a.plugin_path.resolve()),"OLM_AE_MAC_PROJECT_TEMPLATE":str(INPUT_TEMPLATE.resolve()),"OLM_AE_MAC_PROJECT_TEMPLATE_SHA256":INPUT_TEMPLATE_SHA256,"OLM_MACOS_PRODUCT_VERSION":macos_product_version,"OLM_MACOS_BUILD_VERSION":macos_build_version}
    env["OLM_AE_MAC_PLUGIN_BINARY_PATH"] = str(plugin_binary.resolve())
    error_path = support/"ae_script_error.txt"
    env["OLM_AE_MAC_ERROR_PATH"] = str(error_path.resolve())
    wrapper.write_text("\n".join("$.setenv(%s,%s);"%(json.dumps(k),json.dumps(v)) for k,v in env.items())+"\nvar __olm_started=(new Date()).toISOString();\ntry {\n  var __olm_eval_result=$.evalFile(new File(%s));\n  if(__olm_eval_result instanceof Error){throw __olm_eval_result;}\n  var __olm_rf=new File($.getenv(\"OLM_AE_MAC_RESULT_JSON\")); if(!__olm_rf.open(\"r\"))throw new Error(\"missing fresh result\"); var __olm_data=JSON.parse(__olm_rf.read()); __olm_rf.close();\n  __olm_data.run_nonce=$.getenv(\"OLM_AE_MAC_RUN_NONCE\"); __olm_data.started_at=__olm_started; __olm_data.ended_at=(new Date()).toISOString();\n  if(!__olm_rf.open(\"w\"))throw new Error(\"cannot bind result challenge\"); __olm_rf.write(JSON.stringify(__olm_data,null,2)+\"\\n\"); __olm_rf.close();\n  __olm_eval_result;\n} catch(__olm_error) {\n  var __olm_error_file=new File($.getenv(\"OLM_AE_MAC_ERROR_PATH\"));\n  __olm_error_file.encoding=\"UTF-8\";\n  if(__olm_error_file.open(\"w\")){__olm_error_file.write(String(__olm_error)+\"\\nline=\"+String(__olm_error.line||\"\")+\"\\nfile=\"+String(__olm_error.fileName||\"\")+\"\\n\");__olm_error_file.close();}\n  throw __olm_error;\n}\n"%json.dumps(str(jsx.resolve())),encoding="utf-8")
    if a.dump_js: a.dump_js.write_text(wrapper.read_text(),encoding="utf-8"); print(f"[OK] wrote {a.dump_js}"); return 0
    return refuse_unsafe_direct_execution(wrapper)
if __name__=="__main__": raise SystemExit(main())
