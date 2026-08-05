#!/usr/bin/env python3
"""Run the explicit OLMSmoother2 v2/no-key Mac AE candidate request."""
from __future__ import annotations
import argparse, hashlib, json, os, secrets, struct, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json"; STEM = "olmsmoother2_no_key_32bpc_mac_validation_20260715"
INPUT_TEMPLATE = ROOT / "refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep"
INPUT_TEMPLATE_SHA256 = "51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
EXPECTED_PLUGIN_SHA256 = "fe782f344dcaf8865b778198b0faeb8cecd525062a83f38aca8dc1db74442c34"
def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v: object) -> str: return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
def ae_readback_value(value: object) -> object:
    if isinstance(value, list):
        return [struct.unpack("<f", struct.pack("<f", float(component)))[0] for component in value]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return struct.unpack("<f", struct.pack("<f", float(value)))[0]
    return value
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
def exclusive_bytes(path: Path, payload: bytes) -> None:
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0)
    fd=os.open(path,flags,0o444)
    try:
        view=memoryview(payload)
        while view:
            written=os.write(fd,view)
            if written <= 0: raise OSError("short exclusive write")
            view=view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
def exclusive_json(path: Path, value: object) -> None:
    exclusive_bytes(path,json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode())
def loader_source(payload: Path, trace: Path) -> str:
    return r'''(function(){
var TRACE=TRACE_PATH,PAYLOAD=PAYLOAD_PATH;
function L(m){var f=new File(TRACE);f.encoding="UTF-8";if(f.open("a")){f.write(String(m)+"\n");f.close();}}
L("loader entered");
try{var r=$.evalFile(new File(PAYLOAD));if(r instanceof Error)L("loader eval Error "+String(r)+" line="+String(r.line||"")+" file="+String(r.fileName||""));else L("loader eval returned");}
catch(e){L("loader catch "+String(e)+" line="+String(e.line||"")+" file="+String(e.fileName||""));}
}());'''.replace("TRACE_PATH",json.dumps(str(trace.resolve()))).replace("PAYLOAD_PATH",json.dumps(str(payload.resolve())))
def wrapper_source(env: dict[str,str], jsx: Path) -> str:
    prefix="\n".join("$.setenv(%s,%s);"%(json.dumps(k),json.dumps(v)) for k,v in env.items())
    return prefix+r'''
function __olm_fail(m){throw new Error("FAIL_CLOSED: "+m);}
function __olm_stable(v){function q(x){return '"'+String(x).replace(/\\/g,"\\\\").replace(/"/g,'\\"')+'"';}if(v===null)return"null";if(typeof v==="string")return q(v);if(typeof v==="number"){if(!isFinite(v))__olm_fail("nonfinite JSON");return String(v);}if(typeof v==="boolean")return v?"true":"false";if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(__olm_stable(v[i]));return"["+a.join(",")+"]";}if(typeof v==="object"){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(q(k[j])+":"+__olm_stable(v[k[j]]));return"{"+o.join(",")+"}";}__olm_fail("unsupported JSON");}
function __olm_hash(p){var s=system.callSystem("/usr/bin/shasum -a 256 "+__olm_shell(p)).replace(/[\r\n]+$/g,""),m=s.match(/^([0-9a-fA-F]{64})\s/);if(!m)__olm_fail("hash "+p);return m[1].toLowerCase();}
function __olm_shell(p){var q=String.fromCharCode(39),b=String.fromCharCode(92);return q+String(p).split(q).join(q+b+q+q)+q;}
function __olm_trace(m){var p=$.getenv("OLM_AE_MAC_OUTPUT_DIR")+"/host_trace.log",f=new File(p);f.encoding="UTF-8";if(f.open("a")){f.write(String(m)+"\n");f.close();}}
function __olm_read(p){var f=new File(p);f.encoding="UTF-8";if(!f.open("r"))__olm_fail("cannot read "+p);var s=f.read();f.close();try{return eval("("+s+")");}catch(e){__olm_fail("malformed JSON "+p);}}
function __olm_publish(p,v){var tmp=p+"."+String((new Date()).getTime())+"."+String(Math.random()).replace(".","")+".tmp",f=new File(tmp);f.encoding="UTF-8";if(!f.open("w"))__olm_fail("cannot create temp request");f.write(__olm_stable(v));f.close();var r=system.callSystem("/bin/ln "+__olm_shell(tmp)+" "+__olm_shell(p)+" 2>&1; x=$?; /bin/rm -f "+__olm_shell(tmp)+"; exit $x");if(r!=="")__olm_fail("exclusive publish failed "+p+": "+r);}
function __olm_wait(p){var deadline=(new Date()).getTime()+Number($.getenv("OLM_AE_MAC_PROTOCOL_TIMEOUT_MS"));while(!(new File(p)).exists){if((new Date()).getTime()>deadline)__olm_fail("timeout waiting for "+p);$.sleep(50);}return __olm_read(p);}
function __olm_keys(v,w){var a=[],b=w.slice(0),n;for(n in v)if(v.hasOwnProperty(n))a.push(n);a.sort();b.sort();if(__olm_stable(a)!==__olm_stable(b))__olm_fail("schema mismatch");}
var __olm_started=(new Date()).toUTCString();__olm_trace("wrapper entered");
try {
  var C=$.getenv("OLM_AE_MAC_PROCESS_CHALLENGE"),PRE=$.getenv("OLM_AE_MAC_PRE_REQUEST"),PREOK=$.getenv("OLM_AE_MAC_PRE_OK"),POST=$.getenv("OLM_AE_MAC_POST_REQUEST"),POSTOK=$.getenv("OLM_AE_MAC_POST_OK"),ATT=$.getenv("OLM_AE_MAC_ATTESTATION"),N=$.getenv("OLM_AE_MAC_RUN_NONCE");
  var challenge=__olm_read(C),challengeHash=__olm_hash(C);
  __olm_keys(challenge,["kind","schema_version","run_nonce","started_at","run_challenge_sha256","wrapper_sha256","expected","result_path","outputs"]);
  var expectedWrapper=new File($.getenv("OLM_AE_MAC_WRAPPER_PATH")),actualWrapper=expectedWrapper;
  if(!actualWrapper.exists||challenge.kind!=="olmsmoother2_mac_process_challenge"||challenge.schema_version!==1||challenge.run_nonce!==N||challenge.wrapper_sha256!==$.getenv("OLM_AE_MAC_WRAPPER_SHA256")||challenge.wrapper_sha256!==__olm_hash(actualWrapper.fsName))__olm_fail("challenge/wrapper identity");
  if(app.project){try{app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){__olm_fail("close previous project "+e);}}
  app.newProject();var __olm_prewarm_project=app.project;if(!__olm_prewarm_project)__olm_fail("prewarm new project");var __olm_prewarm_comp=__olm_prewarm_project.items.addComp("OLMSmoother2_PREWARM",16,16,1,1,24),__olm_prewarm_layer=__olm_prewarm_comp.layers.addSolid([0,0,0],"PREWARM",16,16,1),__olm_prewarm_effect=__olm_prewarm_layer.property("ADBE Effect Parade").addProperty("OLM Smoother v2");if(!__olm_prewarm_effect||__olm_prewarm_effect.matchName!=="OLM Smoother v2")__olm_fail("prewarm effect identity");
  var pre={kind:"olmsmoother2_mac_process_pre_request",schema_version:1,run_nonce:N,challenge_sha256:challengeHash,sequence:1};__olm_publish(PRE,pre);
  var preOk=__olm_wait(PREOK);__olm_keys(preOk,["kind","schema_version","run_nonce","challenge_sha256","pre_request_sha256","pre_snapshot_sha256","snapshot"]);
  if(preOk.kind!=="olmsmoother2_mac_process_pre_ok"||preOk.schema_version!==1||preOk.run_nonce!==N||preOk.challenge_sha256!==challengeHash||preOk.pre_request_sha256!==__olm_hash(PRE)||!/^[0-9a-f]{64}$/.test(preOk.pre_snapshot_sha256))__olm_fail("pre acknowledgement chain");
  __olm_keys(preOk.snapshot,["process","module"]);__olm_keys(preOk.snapshot.process,["pid","birth_token","executable_path","executable_sha256","dev","ino","size","mtime_ns"]);__olm_keys(preOk.snapshot.module,["path","sha256","dev","ino","size","mtime_ns","vmmap_match_count"]);
  if(preOk.snapshot.process.executable_path!==challenge.expected.ae_executable.path||preOk.snapshot.process.executable_sha256!==challenge.expected.ae_executable.sha256||preOk.snapshot.module.path!==challenge.expected.module.path||preOk.snapshot.module.sha256!==challenge.expected.module.sha256||preOk.snapshot.module.vmmap_match_count!==1)__olm_fail("pre snapshot identity");
  var payloadPath=%s;if(__olm_hash(payloadPath)!==$.getenv("OLM_AE_MAC_PAYLOAD_SHA256"))__olm_fail("payload identity");if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
  var __olm_eval_result=$.evalFile(new File(payloadPath));if(__olm_eval_result instanceof Error)throw __olm_eval_result;
  var rf=new File($.getenv("OLM_AE_MAC_RESULT_JSON"));if(!rf.open("r"))__olm_fail("missing fresh result");var dataText=rf.read();rf.close();var data;try{data=eval("("+dataText+")");}catch(e){__olm_fail("malformed fresh result");}data.run_nonce=N;data.started_at=__olm_started;data.ended_at=(new Date()).toUTCString();if(!rf.open("w"))__olm_fail("cannot bind result challenge");rf.write(__olm_stable(data)+"\n");rf.close();
  var arts={},roles=["no_effect_control","effect_on"];for(var i=0;i<roles.length;i++){var role=roles[i],item=data.cases[0].outputs[role];arts[role]={exr_sha256:__olm_hash(item.path),settings_sha256:__olm_hash(item.output_module_settings.path)};}
  var post={kind:"olmsmoother2_mac_process_post_request",schema_version:1,run_nonce:N,challenge_sha256:challengeHash,sequence:2,pre_request_sha256:__olm_hash(PRE),pre_snapshot_sha256:preOk.pre_snapshot_sha256,pre_ok_sha256:__olm_hash(PREOK),result_sha256:__olm_hash($.getenv("OLM_AE_MAC_RESULT_JSON")),artifacts:arts};__olm_publish(POST,post);
  var postOk=__olm_wait(POSTOK);__olm_keys(postOk,["kind","schema_version","run_nonce","challenge_sha256","post_request_sha256","attestation_sha256"]);
  if(postOk.kind!=="olmsmoother2_mac_process_post_ok"||postOk.schema_version!==1||postOk.run_nonce!==N||postOk.challenge_sha256!==challengeHash||postOk.post_request_sha256!==__olm_hash(POST)||postOk.attestation_sha256!==__olm_hash(ATT))__olm_fail("post acknowledgement chain");
  __olm_eval_result;
} catch(__olm_error) {__olm_trace("ERROR "+String(__olm_error)+" line="+String(__olm_error.line||""));var ef=new File($.getenv("OLM_AE_MAC_ERROR_PATH"));ef.encoding="UTF-8";if(ef.open("w")){ef.write(String(__olm_error)+"\nline="+String(__olm_error.line||"")+"\nfile="+String(__olm_error.fileName||"")+"\n");ef.close();}}
function __olm_hash_value(v){var p=$.getenv("OLM_AE_MAC_OUTPUT_DIR")+"/.olm-hash-value-"+String((new Date()).getTime())+"-"+String(Math.random()).replace(".",""),f=new File(p);f.encoding="UTF-8";if(!f.open("w"))__olm_fail("hash value temp");f.write(__olm_stable(v));f.close();var h=__olm_hash(p);f.remove();return h;}
'''%json.dumps(str(jsx.resolve()))
def jsx_source(case: dict, contract_hash: str, output_template: str, nonce: str) -> str:
    setup = json.loads(REQUEST.read_text(encoding="utf-8"))["common_setup"]
    case = {**case, "run_nonce": nonce, "comp": {"width": setup["comp_width"], "height": setup["comp_height"], "pixel_aspect": 1, "frame_rate": setup["frame_rate"]}}
    c = json.dumps(case, separators=(",", ":"), ensure_ascii=True); return r'''(function(){var spec=CASE_JSON, CONTRACT=CONTRACT_JSON, TEMPLATE=OUTPUT_TEMPLATE_JSON, RUN_NONCE=spec.run_nonce, API="OutputModule.getSettings(GetSettingsFormat.STRING)";
function env(n){try{return $.getenv(n)||"";}catch(e){return "";}} function fail(m){throw new Error("FAIL_CLOSED: "+m);} function q(v){return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"')+'"';} function stable(v){if(v===null)return"null";if(typeof v==="string")return q(v);if(typeof v==="number"){if(!isFinite(v))fail("nonfinite");return String(v);}if(typeof v==="boolean")return v?"true":"false";if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(stable(v[i]));return"["+a.join(",")+"]";}if(typeof v==="object"){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(q(k[j])+":"+stable(v[k[j]]));return"{"+o.join(",")+"}";}fail("unsupported");} function write(p,s){var f=new File(p);if(f.exists)fail("stale/preexisting "+p);f.encoding="UTF-8";if(!f.open("w"))fail("write "+p);f.write(s);f.close();} function sh(p){return system.callSystem("/usr/bin/shasum -a 256 '"+String(p).replace(/'/g,"'\\''")+"'").replace(/[\r\n]+$/g,"");} function hash(p){var m=sh(p).match(/^([0-9a-fA-F]{64})\s/);if(!m)fail("hash "+p);return m[1].toLowerCase();} function prop(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var x=prop(p,n);if(x)return x;}}return null;} function eq(a,b){return stable(a)===stable(b);} function readback(e,on){if(e.matchName!=="OLM Smoother v2"||e.name!=="OLM Smoother v2"||Boolean(e.enabled)!==on)fail("effect identity/enabled readback");var r=[];for(var i=0;i<spec.params_full.length;i++){var x=spec.params_full[i],p=prop(e,x.match_name),expected=spec.params_readback[x.match_name];if(!p||p.matchName!==x.match_name||p.name!==x.name||Number(p.propertyIndex)!==Number(x.property_index)||!eq(p.value,expected))fail("parameter readback "+x.match_name+" actual="+(p?stable(p.value):"missing")+" expected="+stable(expected)+" name="+(p?p.name:"")+" index="+(p?String(p.propertyIndex):""));r.push({name:p.name,match_name:p.matchName,property_index:Number(p.propertyIndex),value:p.value});}return{effect:{name:e.name,match_name:e.matchName,enabled:Boolean(e.enabled)},params:r};} function params(e){for(var i=0;i<spec.params_full.length;i++){var x=spec.params_full[i],p=prop(e,x.match_name);if(!p)fail("missing "+x.match_name);p.setValue(x.value);}readback(e,Boolean(e.enabled));} function settingsContract(s){var o={};for(var k in s)if(s.hasOwnProperty(k)&&k!=="Output File Info")o[k]=s[k];return stable(o);} function capture(m,p){if(!m.getSettings||typeof GetSettingsFormat==="undefined")fail("settings API");var s=m.getSettings(GetSettingsFormat.STRING);var path=p.replace(/\.exr$/i,"_output_module_settings.json");write(path,stable({kind:"olm_output_module_settings_capture",run_nonce:RUN_NONCE,output_template:TEMPLATE,capture_api:API,output_path:m.file.fsName,settings:s})+"\n");return{path:path,sha256:hash(path),serialization:stable(s),contract_serialization:settingsContract(s),output_path:m.file.fsName,settings:s};} function renderedFile(p){var t=new File(p);if(t.exists)return t;var matches=t.parent.getFiles(function(x){return x instanceof File&&x.name.indexOf(t.name)===0;});if(matches.length!==1)fail("rendered output cardinality for "+p+": "+matches.length);if(!matches[0].rename(t.name)||!t.exists)fail("cannot normalize rendered output "+matches[0].fsName);return t;} function render(comp,e,on,out,name){e.enabled=on;var before=readback(e,on);var item=app.project.renderQueue.items.add(comp);item.timeSpanStart=0;item.timeSpanDuration=1/comp.frameRate;var m=item.outputModule(1);m.applyTemplate(TEMPLATE);var p=out+"/"+name;if(new File(p).exists||new File(p.replace(/\.exr$/i,"_output_module_settings.json")).exists)fail("stale output");m.file=new File(p);var s=capture(m,p);app.project.renderQueue.render();var after=readback(e,on),rendered=renderedFile(p),r={path:rendered.fsName,sha256:hash(rendered.fsName),output_module_settings:s,effect_enabled:on,readback_before_render:before,readback_after_render:after};item.remove();return r;}
var inputDir=env("OLM_AE_MAC_INPUT_DIR"),out=env("OLM_AE_MAC_OUTPUT_DIR"),result=env("OLM_AE_MAC_RESULT_JSON"),pluginPath=env("OLM_AE_MAC_PLUGIN_PATH"),pluginBinaryPath=env("OLM_AE_MAC_PLUGIN_BINARY_PATH"),projectTemplatePath=env("OLM_AE_MAC_PROJECT_TEMPLATE"),projectTemplateSha256=env("OLM_AE_MAC_PROJECT_TEMPLATE_SHA256"),macosProductVersion=env("OLM_MACOS_PRODUCT_VERSION"),macosBuildVersion=env("OLM_MACOS_BUILD_VERSION");if(!inputDir||!out||!result||!pluginPath||!pluginBinaryPath||!projectTemplatePath||!projectTemplateSha256||!macosProductVersion||!macosBuildVersion)fail("environment");var pf=new Folder(pluginPath),pb=new File(pluginBinaryPath);if(!pf.exists||pf.name!=="OLMSmoother2.plugin"||!pb.exists||pb.name!=="OLMSmoother2")fail("plugin identity");var templateFile=new File(projectTemplatePath);if(!templateFile.exists||hash(templateFile.fsName)!==projectTemplateSha256)fail("Preserve RGB project template identity");var plugin={filename:pf.name,path:pf.fsName,binary_path:pb.fsName,sha256:hash(pb.fsName)},pr=app.open(templateFile);pr.bitsPerChannel=32;pr.linearBlending=false;pr.workingSpace="";try{pr.gpuAccelType=GpuAccelType.SOFTWARE;}catch(e){fail("SOFTWARE");}var workingSpaceRaw=pr.workingSpace,workingSpaceText=String(workingSpaceRaw);if(Number(pr.bitsPerChannel)!==32||Number(pr.gpuAccelType)!==Number(GpuAccelType.SOFTWARE)||(workingSpaceText!==""&&workingSpaceText!=="None"))fail("project contract: bpc="+pr.bitsPerChannel+" renderer="+pr.gpuAccelType+" working_space_raw="+workingSpaceRaw);var f=new File(inputDir+"/"+spec.input.filename);if(!f.exists||hash(f.fsName)!==spec.input.sha256)fail("input identity");var ft=null,co=null;for(var ii=1;ii<=pr.numItems;ii++){var pi=pr.item(ii);if(pi.name==="OLM_COLOR_PROBE_INPUT")ft=pi;if(pi.name==="OLM_COLOR_PROBE_COMP")co=pi;}if(!ft||!co)fail("Preserve RGB template items");ft.replace(f);var cs=spec.comp;if(co.width!==cs.width||co.height!==cs.height||co.pixelAspect!==cs.pixel_aspect||co.frameRate!==cs.frame_rate||co.numLayers!==1)fail("template comp contract");while(pr.renderQueue.numItems)pr.renderQueue.item(pr.renderQueue.numItems).remove();co.name=spec.id;var ly=co.layer(1);if(!ly||ly.source!==ft)fail("template footage binding");var effects=ly.property("ADBE Effect Parade");if(!effects||effects.numProperties!==0)fail("template effect contamination");var e=effects.addProperty("OLM Smoother v2");if(!e||e.matchName!=="OLM Smoother v2"||e.name!=="OLM Smoother v2")fail("effect identity");params(e);var no=render(co,e,false,out,spec.id+"__no_effect.exr"),yes=render(co,e,true,out,spec.id+"__effect_on.exr");if(no.output_module_settings.contract_serialization!==yes.output_module_settings.contract_serialization)fail("settings differ outside Output File Info");write(result,stable({kind:"olmsmoother2_no_key_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,ae_exact_claim_reason:"Windows artifact attestation and raw FLOAT32 comparison are pending",platform:"macOS",macos_product_version:macosProductVersion,macos_build_version:macosBuildVersion,ae_version:app.version,case_contract_sha256:CONTRACT,input_interpretation:{method:"hash_bound_aep_template_footage_replace",template_path:templateFile.fsName,template_sha256:projectTemplateSha256,preserve_rgb:true,verification:"no_effect_raw_float32_gate"},project:{bits_per_channel:pr.bitsPerChannel,renderer:"SOFTWARE",working_space:"None",working_space_raw:workingSpaceRaw,linear_blending:pr.linearBlending,comp:{width:cs.width,height:cs.height,frame_rate:cs.frame_rate}},output_module:{template_name:TEMPLATE,capture_api:API,channels:["A","B","G","R"],sample_type:"FLOAT",compression:"none"},plugin:plugin,cases:[{id:spec.id,input:spec.input,params_full:spec.params_full,effect:{name:e.name,match_name:e.matchName,enabled:true},outputs:{no_effect_control:no,effect_on:yes},no_effect_control_passed:true}]})+"\n");try{pr.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}}());'''.replace("CASE_JSON", c).replace("CONTRACT_JSON", json.dumps(contract_hash)).replace("OUTPUT_TEMPLATE_JSON", json.dumps(output_template))
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--plugin-path",type=Path,required=True); ap.add_argument("--ae-executable",type=Path,default=Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects")); ap.add_argument("--support-dir",type=Path); ap.add_argument("--output-dir",type=Path); ap.add_argument("--result-json",type=Path); ap.add_argument("--dump-js",type=Path); ap.add_argument("--protocol-timeout",type=float,default=900.0); a=ap.parse_args()
    plugin_binary = a.plugin_path / "Contents" / "MacOS" / "OLMSmoother2"
    if a.plugin_path.name!="OLMSmoother2.plugin" or not a.plugin_path.is_dir() or not plugin_binary.is_file(): print("[FAIL_CLOSED] --plugin-path must name an existing OLMSmoother2.plugin bundle"); return 2
    if sha256(plugin_binary) != EXPECTED_PLUGIN_SHA256: print("[FAIL_CLOSED] installed OLMSmoother2 binary hash is not the current host-phase target"); return 2
    try:
        ae_executable=a.ae_executable.resolve(strict=True)
        plugin_binary=plugin_binary.resolve(strict=True)
    except OSError as e:
        print(f"[FAIL_CLOSED] executable/module identity unavailable: {e}"); return 2
    if a.ae_executable.is_symlink() or a.ae_executable != ae_executable or not ae_executable.is_file():
        print("[FAIL_CLOSED] --ae-executable must be the canonical existing AfterFX executable path"); return 2
    if not a.protocol_timeout > 0:
        print("[FAIL_CLOSED] --protocol-timeout must be positive"); return 2
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
    protocol_names=("process_challenge.json","pre_request.json","pre_ok.json","post_request.json","post_ok.json","mac_process_attestation.json","run_challenge.json","run_mac_wrapper.jsx","run_mac_loader.jsx","loader_trace.log")
    protocol_paths={name:contained_file(out,out/name,name) for name in protocol_names}
    if any(path.exists() or path.is_symlink() for path in protocol_paths.values()):
        print("[FAIL_CLOSED] stale/preexisting process protocol file exists"); return 1
    jsx=support/"run_mac_olmsmoother2_no_key_32bpc_validation.jsx"
    contract_case={**case,"input":{"filename":src.name,"sha256":sha256(src)}}
    ch=canonical({"request_id":data["request_id"],"case":contract_case,"common_setup":data["common_setup"],"mac_run_contract":data["mac_run_contract"],"output_template":output_template})
    run_case={**contract_case,"params_readback":{param["match_name"]:ae_readback_value(param["value"]) for param in case["params_full"]}}
    payload_source=jsx_source(run_case,ch,output_template,nonce)
    payload_source=payload_source.replace(",pr=app.open(templateFile);pr.bitsPerChannel=32;", ";app.open(templateFile);var pr=app.project;if(!pr)fail(\"open Preserve RGB template\");pr.bitsPerChannel=32;")
    jsx.write_text(payload_source,encoding="utf-8")
    wrapper=protocol_paths["run_mac_wrapper.jsx"]
    env={"OLM_AE_MAC_INPUT_DIR":str((support/"input").resolve()),"OLM_AE_MAC_OUTPUT_DIR":str(out),"OLM_AE_MAC_RESULT_JSON":str(result),"OLM_AE_MAC_RUN_NONCE":nonce,"OLM_AE_MAC_PLUGIN_PATH":str(a.plugin_path.resolve()),"OLM_AE_MAC_PROJECT_TEMPLATE":str(INPUT_TEMPLATE.resolve()),"OLM_AE_MAC_PROJECT_TEMPLATE_SHA256":INPUT_TEMPLATE_SHA256,"OLM_MACOS_PRODUCT_VERSION":macos_product_version,"OLM_MACOS_BUILD_VERSION":macos_build_version}
    env["OLM_AE_MAC_PLUGIN_BINARY_PATH"] = str(plugin_binary.resolve())
    error_path = support/"ae_script_error.txt"
    env["OLM_AE_MAC_ERROR_PATH"] = str(error_path.resolve())
    env.update({"OLM_AE_MAC_PROCESS_CHALLENGE":str(protocol_paths["process_challenge.json"]),"OLM_AE_MAC_PRE_REQUEST":str(protocol_paths["pre_request.json"]),"OLM_AE_MAC_PRE_OK":str(protocol_paths["pre_ok.json"]),"OLM_AE_MAC_POST_REQUEST":str(protocol_paths["post_request.json"]),"OLM_AE_MAC_POST_OK":str(protocol_paths["post_ok.json"]),"OLM_AE_MAC_ATTESTATION":str(protocol_paths["mac_process_attestation.json"]),"OLM_AE_MAC_PROTOCOL_TIMEOUT_MS":str(int(a.protocol_timeout*1000)),"OLM_AE_MAC_PAYLOAD_SHA256":sha256(jsx)})
    started=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    run_challenge={"kind":"olmsmoother2_mac_run_challenge","run_nonce":nonce,"started_at":started,"result_path":str(result),"output_paths":{"no_effect_control":{"exr":str(expected_paths[1]),"settings":str(expected_paths[3])},"effect_on":{"exr":str(expected_paths[2]),"settings":str(expected_paths[4])}}}
    exclusive_json(protocol_paths["run_challenge.json"],run_challenge)
    # The wrapper is finalized before the process challenge so its hash cannot
    # depend on a challenge digest embedded back into the wrapper.
    env["OLM_AE_MAC_WRAPPER_SHA256"]="WRAPPER_SHA256_NOT_EMBEDDED"
    source=wrapper_source(env,jsx)
    # The wrapper verifies the challenge against $.fileName, so a copied script
    # cannot authenticate by hashing the untouched canonical wrapper.
    source=source.replace('challenge.wrapper_sha256!==$.getenv("OLM_AE_MAC_WRAPPER_SHA256")','challenge.wrapper_sha256!==__olm_hash(actualWrapper.fsName)')
    source='$.setenv("OLM_AE_MAC_WRAPPER_PATH",%s);\n'%json.dumps(str(wrapper))+source
    exclusive_bytes(wrapper,source.encode("utf-8"))
    wrapper_hash=sha256(wrapper)
    process_challenge={"kind":"olmsmoother2_mac_process_challenge","schema_version":1,"run_nonce":nonce,"started_at":started,"run_challenge_sha256":sha256(protocol_paths["run_challenge.json"]),"wrapper_sha256":wrapper_hash,"expected":{"ae_executable":{"path":str(ae_executable),"sha256":sha256(ae_executable)},"module":{"path":str(plugin_binary),"sha256":sha256(plugin_binary)}},"result_path":str(result),"outputs":run_challenge["output_paths"]}
    exclusive_json(protocol_paths["process_challenge.json"],process_challenge)
    loader=protocol_paths["run_mac_loader.jsx"]
    exclusive_bytes(loader,loader_source(wrapper,protocol_paths["loader_trace.log"]).encode("utf-8"))
    if a.dump_js:
        a.dump_js.write_text(wrapper.read_text(),encoding="utf-8"); print(f"[OK] wrote {a.dump_js}")
    print("[SAFE_MANUAL] Start the attestor in a separate Terminal:")
    print(f"[SAFE_MANUAL] {sys.executable} {ROOT/'scripts/attest_olmsmoother2_mac_process_20260728.py'} --challenge {protocol_paths['process_challenge.json']} --watch --timeout {a.protocol_timeout:g}")
    print("[SAFE_MANUAL] Then use After Effects File > Scripts > Run Script File and select:")
    print(f"[SAFE_MANUAL] {loader}")
    return 0
if __name__=="__main__": raise SystemExit(main())
