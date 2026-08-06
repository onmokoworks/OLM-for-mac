#!/usr/bin/env python3
"""Prepare (or explicitly execute) the fail-closed OLMSmoother v1 Mac AE run."""
from __future__ import annotations
import argparse, hashlib, json, os, secrets, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQUEST=ROOT/"refs/mac_validation_requests/olmsmoother_v1_32bpc_mac_validation_20260730.json"
MANIFEST=ROOT/"refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMSmoother/reference_manifest.json"
INPUT_TEMPLATE=ROOT/"refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep"
REPORTER=ROOT/"scripts/report_olmsmoother_v1_32bpc_mac_validation_20260730.py"
SMOKE=ROOT/"refs/scripts/smoke_olmsmoother_v1_32bpc_mac_validation_20260730.py"
BOUNDARY_PROBE=ROOT/"tools/emulation/probe_olmsmoother_v1_pf16_mainkernel_boundary_20260731.py"
PORT_SOURCE=ROOT/"mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
STRINGS_SOURCE=ROOT/"mac/OLMSmoother/OLMSmoother_Strings.cpp"
AE_VERSION="26.3x87"
ALLOWED=("OLM Smoother-0001","OLM Smoother-0002","OLM Smoother-0003")
INPUT_TEMPLATE_SHA256="51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
def digest(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p:Path)->dict[str,str]:
    if p.is_symlink(): fail("harness symlink forbidden: "+str(p))
    q=p.resolve(strict=True)
    if q!=p: fail("harness path must be canonical: "+str(p))
    return {"path":str(q),"sha256":digest(q)}
def parent_symlink(path:Path)->bool:
    return any(p.exists() and p.is_symlink() for p in (path,*path.parents))
def exclusive_bytes(path:Path,value:bytes)->None:
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o444)
    try:
        view=memoryview(value)
        while view:
            written=os.write(fd,view)
            if written<=0: raise OSError("short exclusive write")
            view=view[written:]
        os.fsync(fd)
    finally: os.close(fd)
def exclusive_json(path:Path,value:object)->None:
    exclusive_bytes(path,json.dumps(value,sort_keys=True,separators=(",",":")).encode())
def preflight_outputs(paths:list[Path],expected_count:int=40)->None:
    seen_paths=set(); seen_targets=set()
    for p in paths:
        try: os.lstat(p)
        except FileNotFoundError: pass
        else: fail("declared output already exists")
        parent=p.parent.resolve(strict=True)
        if p.parent!=parent or parent.is_symlink(): fail("output parent must be canonical non-symlink")
        if any(entry.name.startswith(p.name) for entry in parent.iterdir()): fail("stale output sequence-prefix artifact: "+p.name)
        st=os.stat(parent,follow_symlinks=False); target=(st.st_dev,st.st_ino,p.name)
        if p in seen_paths or target in seen_targets: fail("output pathname/parent-inode alias")
        seen_paths.add(p); seen_targets.add(target)
    if len(paths)!=expected_count: fail(f"exactly {expected_count} outputs required")
def fail(message:str)->None: raise ValueError(message)
def replace_once(source:str,old:str,new:str,label:str)->str:
    if source.count(old)!=1: fail("generated JSX replacement drift: "+label)
    return source.replace(old,new,1)
def runtime_input_interpretation(request:dict)->dict:
    raw=request["mac_run_contract"]["input_interpretation"]
    return {**raw,"template_path":str(INPUT_TEMPLATE.resolve(strict=True))}
def load_contract()->dict:
    request=json.loads(REQUEST.read_text()); manifest=json.loads(MANIFEST.read_text())
    if request["effect"]!={"name":"OLM Smoother","match_name":"OLM Smoother"}: fail("effect identity drift")
    if len(request["cases"])!=10 or [c["id"][-2:] for c in request["cases"]] != [f"{n:02d}" for n in range(1,11)]: fail("case/order/case-sensitive identity drift")
    if request.get("windows_reference",{}).get("ae_version")!=AE_VERSION or manifest.get("ae_version")!=AE_VERSION or manifest.get("project",{}).get("bits_per_channel")!=32 or manifest["project"].get("working_space") is not None or manifest["project"].get("project_gpu_accel_type")!={"current_name":"SOFTWARE","raw":1816}: fail("Windows host contract drift")
    expected_input={"method":"hash_bound_aep_template_footage_replace","template_path":"refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep","template_sha256":INPUT_TEMPLATE_SHA256,"footage_item_name":"OLM_COLOR_PROBE_INPUT","comp_item_name":"OLM_COLOR_PROBE_COMP","preserve_rgb":True,"verification":"all_ten_no_effect_controls_raw_float32_exact"}
    if request.get("mac_run_contract",{}).get("input_interpretation")!=expected_input: fail("Preserve RGB input contract drift")
    if request["mac_run_contract"].get("output_settings_capture")!={"api":"OutputModule.getSettings(GetSettingsFormat.STRING)","one_sidecar_per_role":True,"no_effect_and_effect_settings_must_match":True}: fail("output settings capture contract drift")
    if request["mac_run_contract"].get("cache_policy")!={"after_each_footage_replace":"app.purge(PurgeTarget.ALL_CACHES)","between_no_effect_and_effect":"forbidden"}: fail("cache policy contract drift")
    if INPUT_TEMPLATE.is_symlink() or parent_symlink(INPUT_TEMPLATE) or digest(INPUT_TEMPLATE.resolve(strict=True))!=INPUT_TEMPLATE_SHA256: fail("Preserve RGB template path/hash")
    root_raw=ROOT/request["windows_reference"]["artifact_root"]
    if parent_symlink(root_raw) or parent_symlink(MANIFEST): fail("reference root/manifest parent-chain symlink forbidden")
    root=root_raw.resolve(strict=True)
    if MANIFEST.resolve(strict=True).parent!=root: fail("reference manifest containment")
    if len(manifest.get("cases",[]))!=10 or [c.get("id") for c in manifest["cases"]]!=[c["id"] for c in request["cases"]]: fail("exact manifest case count/order/id drift")
    by_id={c["id"]:c for c in manifest["cases"]}
    for case in request["cases"]:
        source=by_id.get(case["id"]); params=source["effects"][0]["params"] if source else []
        expected=[{"name":p["name"],"match_name":p["match_name"],"property_index":p["property_index"],"value":p["value"]} for p in params if p["match_name"] in ALLOWED]
        if case["params"]!=expected or tuple(p["match_name"] for p in case["params"])!=ALLOWED: fail(case["id"]+": v1 parameter/readback contract drift")
        if any(p["match_name"].startswith("ADBE ") for p in case["params"]): fail("AE compositing control leaked")
        for key,hashkey,manifest_key in (("before_effects_frame","before_effects_sha256","before_effects_frame"),("effect_frame","effect_sha256","frame")):
            p=root/case[key]
            if p.is_symlink() or p.resolve(strict=True).parent!=root or digest(p)!=case[hashkey] or source[manifest_key]!=case[key]: fail(case["id"]+": path/hash/manifest mismatch")
    return request
def jsx_source(request:dict, plugin:Path, out:Path, result:Path, nonce:str, attestor_nonce:str|None=None, started:Path|None=None, error:Path|None=None)->str:
    spec=json.dumps(request,separators=(",",":"))
    started=started or out/"jsx_started.json"
    error=error or out/"jsx_error.json"
    source=r"""(function(){
var S=%s,TEMPLATE_PATH=%s;
function F(m){throw Error('FAIL_CLOSED: '+m)}
function Q(p){var s=String(p),q=String.fromCharCode(39);return q+s.split(q).join(q+String.fromCharCode(92)+q+q)+q}
function H(p){var x=system.callSystem('/usr/bin/shasum -a 256 '+Q(p));var m=x.match(/^([0-9a-f]{64})/i);if(!m)F('hash');return m[1].toLowerCase()}
function W(p,v){var f=new File(p),t=new File(p+'.publishing');if(f.exists||t.exists)F('stale '+p);t.encoding='UTF-8';if(!t.open('w'))F('write');if(!t.write(JSON.stringify(v,null,2)+'\n')){t.close();F('write')}if(!t.close())F('close');if(f.exists){t.remove();F('publish collision '+p)}if(!t.rename(f.name)||!f.exists)F('publish '+p)}
function ST(v){if(v===null)return 'null';var t=typeof v;if(t==='string'||t==='number'||t==='boolean')return JSON.stringify(v);if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(ST(v[i]));return '['+a.join(',')+']'}if(t==='object'){var k=[],o=[];for(var n in v)if(v.hasOwnProperty(n))k.push(n);k.sort();for(var j=0;j<k.length;j++)o.push(JSON.stringify(k[j])+':'+ST(v[k[j]]));return '{'+o.join(',')+'}'}F('unsupported stable serialization')}
function OS(m,p,cid,role){if(!m.getSettings||typeof GetSettingsFormat==='undefined'||typeof GetSettingsFormat.STRING==='undefined')F('output settings API');if(!m.file||m.file.fsName!==p)F('output settings file binding');var s=m.getSettings(GetSettingsFormat.STRING),ss=ST(s);if(!s||typeof s!=='object'||!ss||ss==='{}')F('empty output settings');var sp=p.replace(/\.exr$/i,'__output_module_settings.json'),v={kind:'olmsmoother_v1_output_module_settings',schema_version:1,run_nonce:NONCE,case_id:cid,role:role,output_template:'OLM EXR 32 Float',capture_api:'OutputModule.getSettings(GetSettingsFormat.STRING)',output_path:m.file.fsName,settings:s};W(sp,v);return {path:new File(sp).fsName,sha256:H(sp),serialization:ss,settings:s}}
function P(e,x){var p=e.property(x.match_name);if(!p||p.name!==x.name||p.propertyIndex!==x.property_index)F('parameter identity');p.setValue(x.value);if(JSON.stringify(p.value)!==JSON.stringify(x.value))F('parameter readback')}
function R(e,c,on){if(e.name!=='OLM Smoother'||e.matchName!=='OLM Smoother'||Boolean(e.enabled)!==on)F('effect readback');var a=[];for(var z=0;z<c.params.length;z++){var x=c.params[z],p=e.property(x.match_name);if(!p||p.name!==x.name||p.matchName!==x.match_name||p.propertyIndex!==x.property_index||JSON.stringify(p.value)!==JSON.stringify(x.value))F('render readback');a.push({name:p.name,match_name:p.matchName,property_index:p.propertyIndex,value:p.value})}return {effect:{name:e.name,match_name:e.matchName,enabled:Boolean(e.enabled)},params:a}}
var TI=S.mac_run_contract.input_interpretation;
var tf=new File(TEMPLATE_PATH);
if(!tf.exists||tf.fsName!==TEMPLATE_PATH||H(tf.fsName)!==TI.template_sha256)F('Preserve RGB template identity');
var pr=app.open(tf);
if(!pr||pr!==app.project||!pr.file||pr.file.fsName!==tf.fsName)F('Preserve RGB opened-project identity');
pr.bitsPerChannel=32;pr.workingSpace='';pr.linearBlending=false;
try{pr.gpuAccelType=GpuAccelType.SOFTWARE}catch(e){F('SOFTWARE')}
if(pr.bitsPerChannel!==32||Number(pr.gpuAccelType)!==1816||String(pr.workingSpace)!=='')F('project raw contract');
var ft=null,co=null,ftc=0,coc=0;
for(var ii=1;ii<=pr.numItems;ii++){var pi=pr.item(ii);if(pi.name===TI.footage_item_name){if(!(pi instanceof FootageItem))F('Preserve RGB footage item type');ft=pi;ftc++}if(pi.name===TI.comp_item_name){if(!(pi instanceof CompItem))F('Preserve RGB comp item type');co=pi;coc++}}
if(ftc!==1||coc!==1||!ft||!co)F('Preserve RGB template item cardinality');
if(co.width!==1920||co.height!==1080||co.pixelAspect!==1||co.frameRate!==24||co.numLayers!==1)F('Preserve RGB template comp contract');
while(pr.renderQueue.numItems)pr.renderQueue.item(pr.renderQueue.numItems).remove();
if(pr.renderQueue.numItems!==0)F('Preserve RGB template render queue cleanup');
var ly=co.layer(1),g=ly&&ly.property('ADBE Effect Parade');
if(!ly||ly.source!==ft||!g||g.numProperties!==0)F('Preserve RGB template layer/effect contamination');
var BASE_ITEMS=pr.numItems;
var INPUT_EVIDENCE={method:TI.method,template_path:tf.fsName,template_sha256:H(tf.fsName),footage_item_name:TI.footage_item_name,comp_item_name:TI.comp_item_name,preserve_rgb:TI.preserve_rgb,verification:TI.verification};
var rows=[];
for(var i=0;i<S.cases.length;i++){
  var c=S.cases[i],bound=ch.inputs[c.id];
  if(!bound||typeof bound.path!=='string'||typeof bound.sha256!=='string'||bound.sha256!==c.before_effects_sha256)F('input binding');
  var f=new File(bound.path);
  if(!f.exists||f.fsName!==bound.path||H(f.fsName)!==bound.sha256)F('input');
  if(g.numProperties!==0||pr.renderQueue.numItems!==0)F('case preflight contamination');
  ft.replace(f);
  if(typeof PurgeTarget==='undefined'||typeof PurgeTarget.ALL_CACHES==='undefined'||!app.purge)F('cache purge API');
  app.purge(PurgeTarget.ALL_CACHES);
  if(!ft.file||ft.file.fsName!==f.fsName||ft.width!==1920||ft.height!==1080||co.width!==1920||co.height!==1080||co.frameRate!==24||co.numLayers!==1)F('replacement footage/comp contract');
  ly=co.layer(1);g=ly&&ly.property('ADBE Effect Parade');
  if(!ly||ly.source!==ft||!g||g.numProperties!==0)F('replacement footage binding');
  var e=g.addProperty('OLM Smoother');
  if(!e||e.name!=='OLM Smoother'||e.matchName!=='OLM Smoother')F('effect identity');
  for(var j=0;j<c.params.length;j++)P(e,c.params[j]);
  var outs={};
  for(var k=0;k<2;k++){
    var role=k?'effect_on':'no_effect_control';
    if(pr.renderQueue.numItems!==0)F('render queue preflight');
    e.enabled=!!k;
    var before=R(e,c,!!k),q=pr.renderQueue.items.add(co),om=q.outputModule(1);
    if(pr.renderQueue.numItems!==1)F('render queue cardinality');
    om.applyTemplate('OLM EXR 32 Float');
    var path=%s+'/'+c.id+'__'+role+'.exr';
    om.file=new File(path);
    if(!om.file||om.file.fsName!==path||typeof PostRenderAction==='undefined'||typeof PostRenderAction.NONE==='undefined'||om.postRenderAction!==PostRenderAction.NONE)F('output module file/post-render contract');
    var settings=OS(om,path,c.id,role);
    pr.renderQueue.render();
    var rly=co.layer(1),rg=rly&&rly.property('ADBE Effect Parade');
    if(pr.numItems!==BASE_ITEMS||!rly||rly.source!==ft||!rg||rg.numProperties!==1)F('post-render project/template stability');
    var after=R(e,c,!!k);
    outs[role]={path:path,sha256:H(path),output_module_settings:settings,effect_enabled:!!k,effect:{name:e.name,match_name:e.matchName},params_readback:after.params,readback_before_render:before,readback_after_render:after};
    q.remove();
    if(pr.renderQueue.numItems!==0)F('render queue cleanup')
  }
  if(outs.no_effect_control.output_module_settings.serialization!==outs.effect_on.output_module_settings.serialization)F('output settings differ');
  rows.push({id:c.id,input:{path:f.fsName,sha256:H(f.fsName)},params:c.params,outputs:outs});
  e.remove();
  ly=co.layer(1);g=ly&&ly.property('ADBE Effect Parade');
  if(pr.numItems!==BASE_ITEMS||!ly||ly.source!==ft||!g||g.numProperties!==0||pr.renderQueue.numItems!==0)F('case cleanup contamination')
}
W(%s,{kind:'olmsmoother_v1_32bpc_mac_validation_return',schema_version:2,run_nonce:%s,ae_exact_claim:false,callback_claim:'classic_host_conversion_hypothesis_only',ae_version:app.version,input_interpretation:INPUT_EVIDENCE,project:{bits_per_channel:pr.bitsPerChannel,renderer:'SOFTWARE',renderer_raw:Number(pr.gpuAccelType),working_space:null},plugin:{bundle_path:%s,macho_path:%s,macho_sha256:H(%s)},cases:rows});
try{pr.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(__close_error){}
})();"""%(spec,json.dumps(str(INPUT_TEMPLATE.resolve(strict=True))),json.dumps(str(out)),json.dumps(str(result)),json.dumps(nonce),json.dumps(str(plugin)),json.dumps(str(plugin/"Contents/MacOS/OLMSmoother")),json.dumps(str(plugin/"Contents/MacOS/OLMSmoother")))
    protocol="""var RJ=function(p){var f=new File(p);if(!f.open('r'))F('read '+p);var v=JSON.parse(f.read());f.close();return v};var WT=function(p){var d=(new Date()).getTime()+900000,f=new File(p);while(!f.exists){if((new Date()).getTime()>d)F('timeout '+p);$.sleep(50)}return RJ(p)};var NONCE=%s,ANONCE=%s,CH=%s,PRE=%s,PREOK=%s,POST=%s,POSTOK=%s;var ch=RJ(CH),chh=H(CH);if(ch.kind!=='olmsmoother_v1_mac_process_challenge'||ch.schema_version!==4||ch.run_nonce!==NONCE||ch.attestor_nonce!==ANONCE)F('challenge schema/nonce');PHASE='project';"""%(json.dumps(nonce),json.dumps(attestor_nonce or "0"*64),json.dumps(str(out/"process_challenge.json")),json.dumps(str(out/"pre_request.json")),json.dumps(str(out/"pre_ok.json")),json.dumps(str(out/"post_request.json")),json.dumps(str(out/"post_ok.json")))
    diagnostic_start="var PHASE='bootstrap';try{var SELF=new File($.fileName),SELFPATH=SELF.fsName;W(%s,{kind:'olmsmoother_v1_jsx_started',schema_version:1,run_nonce:%s,jsx_path:SELFPATH,jsx_sha256:H(SELFPATH)});PHASE='challenge';"%(json.dumps(str(started)),json.dumps(nonce))
    source=replace_once(source,"var TI=S.mac_run_contract.input_interpretation;","var TI=S.mac_run_contract.input_interpretation;"+diagnostic_start+protocol,"diagnostic/protocol injection")
    source=replace_once(source,"var INPUT_EVIDENCE={method:TI.method,template_path:tf.fsName,template_sha256:H(tf.fsName),footage_item_name:TI.footage_item_name,comp_item_name:TI.comp_item_name,preserve_rgb:TI.preserve_rgb,verification:TI.verification};","var INPUT_EVIDENCE={method:TI.method,template_path:tf.fsName,template_sha256:H(tf.fsName),footage_item_name:TI.footage_item_name,comp_item_name:TI.comp_item_name,preserve_rgb:TI.preserve_rgb,verification:TI.verification};var CI=ch.input_interpretation,CIK=0;if(!CI)F('challenge input interpretation');for(var cik in CI)if(CI.hasOwnProperty(cik))CIK++;if(CIK!==7||CI.method!==INPUT_EVIDENCE.method||CI.template_path!==INPUT_EVIDENCE.template_path||CI.template_sha256!==INPUT_EVIDENCE.template_sha256||CI.footage_item_name!==INPUT_EVIDENCE.footage_item_name||CI.comp_item_name!==INPUT_EVIDENCE.comp_item_name||CI.preserve_rgb!==true||CI.verification!==INPUT_EVIDENCE.verification)F('challenge input interpretation');","input interpretation challenge")
    source=replace_once(source,"if(pr.bitsPerChannel!==32||Number(pr.gpuAccelType)!==1816||String(pr.workingSpace)!=='')F('project raw contract');","var WSRAW=pr.workingSpace,WSTYPE=(WSRAW===null?'null':typeof WSRAW),WSVALUE=(WSRAW===null?null:(typeof WSRAW==='undefined'?null:String(WSRAW))),WSNONE=(WSRAW===null||typeof WSRAW==='undefined'||String(WSRAW)===''||String(WSRAW)==='None');if(pr.bitsPerChannel!==32||Number(pr.gpuAccelType)!==1816||!WSNONE)F('project raw contract: bits='+String(pr.bitsPerChannel)+' renderer_raw='+String(Number(pr.gpuAccelType))+' workingSpace_raw='+String(WSRAW)+' workingSpace_type='+WSTYPE);","project raw contract")
    source=replace_once(source,"return {effect:{name:e.name,match_name:e.matchName,enabled:Boolean(e.enabled)},params:a}","return {effect:{name:e.name,match_name:e.matchName,enabled:Boolean(e.enabled)},params:a,project:{bits_per_channel:Number(pr.bitsPerChannel),renderer_raw:Number(pr.gpuAccelType),working_space_raw:WSVALUE,working_space_raw_type:WSTYPE}}","render readback")
    source=replace_once(source,"function P(e,x){","function RF(p){var exact=new File(p);if(exact.exists)return exact;var matches=exact.parent.getFiles(function(x){return x instanceof File&&x.name.indexOf(exact.name)===0;});if(matches.length!==1)F('rendered output prefix cardinality '+p+': '+matches.length);if(!matches[0].rename(exact.name)||!exact.exists)F('rendered output normalization '+p);return exact}function P(e,x){","render output normalization")
    warmup="""PHASE='warmup';var wc=pr.items.addComp('__OLM_SMOOTHER_MODULE_WARMUP__',16,16,1,1/24,24),wl=wc.layers.add(ft),wg=wl.property('ADBE Effect Parade'),we=wg.addProperty('OLM Smoother'),wcase=S.cases[0];if(!we||we.name!=='OLM Smoother'||we.matchName!=='OLM Smoother')F('warmup effect identity');for(var wi=0;wi<wcase.params.length;wi++)P(we,wcase.params[wi]);we.enabled=true;var WARMUP={rendered:false,removed:false,effect:R(we,wcase,true),case_id:wcase.id};wc.remove();wc=null;var aft=null,aco=null,aftc=0,acoc=0;for(var aii=1;aii<=pr.numItems;aii++){var api=pr.item(aii);if(api.name===TI.footage_item_name){if(!(api instanceof FootageItem))F('warmup restored footage type');aft=api;aftc++}if(api.name===TI.comp_item_name){if(!(api instanceof CompItem))F('warmup restored comp type');aco=api;acoc++}}if(aftc!==1||acoc!==1||!aft||!aco)F('warmup restored item cardinality');ft=aft;co=aco;ly=co.layer(1);g=ly&&ly.property('ADBE Effect Parade');if(pr.numItems!==BASE_ITEMS)F('warmup restoration items expected='+String(BASE_ITEMS)+' actual='+String(pr.numItems));if(pr.renderQueue.numItems!==0)F('warmup restoration render_queue expected=0 actual='+String(pr.renderQueue.numItems));if(!ly)F('warmup restoration layer missing');if(ly.source!==ft)F('warmup restoration source expected_id='+String(ft.id)+' actual_id='+String(ly.source?ly.source.id:null));if(!g)F('warmup restoration effect_parade missing');if(g.numProperties!==0)F('warmup restoration effects expected=0 actual='+String(g.numProperties));WARMUP.removed=true;W(PRE,{kind:'olmsmoother_v1_pre_request',schema_version:1,run_nonce:NONCE,attestor_nonce:ANONCE,challenge_sha256:chh,sequence:1,warmup:WARMUP});var pok=WT(PREOK);if(pok.kind!=='olmsmoother_v1_pre_ok'||pok.run_nonce!==NONCE||pok.attestor_nonce!==ANONCE||pok.challenge_sha256!==chh||pok.pre_request_sha256!==H(PRE))F('pre ok');"""
    source=replace_once(source,"var rows=[];",warmup+"PHASE='cases';var rows=[];","warmup")
    source=replace_once(source,"project:{bits_per_channel:pr.bitsPerChannel,renderer:'SOFTWARE',renderer_raw:Number(pr.gpuAccelType),working_space:null}","project:{bits_per_channel:Number(pr.bitsPerChannel),renderer:'SOFTWARE',renderer_raw:Number(pr.gpuAccelType),working_space:'None',working_space_raw:WSVALUE,working_space_raw_type:WSTYPE}","result project")
    source=replace_once(source,"plugin:{bundle_path:","warmup_contract:ch.warmup_contract,warmup_evidence:WARMUP,plugin:{bundle_path:","warmup evidence")
    source=replace_once(source,"om.file=new File(path);","if(new File(path).exists)F('stale output '+path);om.file=new File(path);q.timeSpanStart=0;q.timeSpanDuration=1/co.frameRate;","single frame render")
    source=replace_once(source,"pr.renderQueue.render();","pr.renderQueue.render();var rendered=RF(path);","render output normalization")
    source=replace_once(source,"var role=k?'effect_on':'no_effect_control';","var role=k?'effect_on':'no_effect_control';PHASE='render:'+c.id+':'+role;","render phase")
    source=replace_once(source,"outs[role]={path:path,sha256:H(path),","outs[role]={path:rendered.fsName,sha256:H(rendered.fsName),","render output identity")
    post="""PHASE='post_request';var ah={};for(var ai=0;ai<rows.length;ai++){ah[rows[ai].id]={};for(var ar in rows[ai].outputs){var ao=rows[ai].outputs[ar];ah[rows[ai].id][ar]={exr:{path:ao.path,sha256:ao.sha256},settings:{path:ao.output_module_settings.path,sha256:ao.output_module_settings.sha256}}}}W(POST,{kind:'olmsmoother_v1_post_request',schema_version:1,run_nonce:NONCE,attestor_nonce:ANONCE,challenge_sha256:chh,sequence:2,pre_request_sha256:H(PRE),pre_ok_sha256:H(PREOK),artifacts:ah});var qok=WT(POSTOK);if(qok.kind!=='olmsmoother_v1_post_ok'||qok.run_nonce!==NONCE||qok.attestor_nonce!==ANONCE||qok.challenge_sha256!==chh||qok.post_request_sha256!==H(POST)||!qok.attestation_sha256)F('post ok');var PROCESS_ATTESTATION_SHA256=qok.attestation_sha256;PHASE='result';"""
    source=replace_once(source,"ae_exact_claim:false,","process_attestation_sha256:PROCESS_ATTESTATION_SHA256,ae_exact_claim:false,","attestation result binding")
    source=replace_once(source,"W("+json.dumps(str(result))+",",post+"W("+json.dumps(str(result))+",","post protocol")
    if not source.endswith("})();"): fail("generated JSX wrapper boundary drift")
    catch="}catch(__olm_error){try{W(%s,{kind:'olmsmoother_v1_jsx_error',schema_version:1,run_nonce:%s,attestor_nonce:%s,phase:PHASE,error:String(__olm_error),line:__olm_error.line||null,file_name:__olm_error.fileName||null,stack:__olm_error.stack||null})}catch(__sidecar_error){}throw __olm_error;}})();"%(json.dumps(str(error)),json.dumps(nonce),json.dumps(attestor_nonce or "0"*64))
    return source[:-5]+catch
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--plugin-path",type=Path); ap.add_argument("--output-dir",type=Path); ap.add_argument("--result-json",type=Path); ap.add_argument("--dump-js",type=Path); ap.add_argument("--execute",action="store_true"); ap.add_argument("--ae-executable",type=Path,default=Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects")); a=ap.parse_args()
    try: request=load_contract()
    except (OSError,KeyError,json.JSONDecodeError,ValueError) as e: print("[FAIL_CLOSED]",e); return 1
    if not a.execute:
        if a.dump_js:
            if not a.plugin_path or not a.output_dir: print("[FAIL_CLOSED] --dump-js requires --plugin-path and --output-dir"); return 2
            a.dump_js.write_text(jsx_source(request,a.plugin_path.resolve(),a.output_dir.resolve(),(a.result_json or a.output_dir/"mac_validation_return.json").resolve(),"0"*64))
        print("[SAFE] contract verified; direct AE execution disabled (pass --execute explicitly)")
        return 0
    if not a.plugin_path or not a.output_dir: print("[FAIL_CLOSED] --execute requires --plugin-path and --output-dir"); return 2
    plugin=a.plugin_path; binary=plugin/"Contents/MacOS/OLMSmoother"
    try:
        if plugin.name!="OLMSmoother.plugin" or plugin.is_symlink() or binary.is_symlink() or not binary.is_file(): fail("canonical OLMSmoother.plugin/Mach-O required")
        ae=a.ae_executable.resolve(strict=True); out=a.output_dir.resolve(strict=True)
        if a.ae_executable.is_symlink() or a.ae_executable!=ae or out.is_symlink(): fail("canonical non-symlink AE/output required")
        result=(a.result_json or out/"mac_validation_return.json").resolve()
        if result.parent!=out or result.name!="mac_validation_return.json" or result.exists(): fail("fresh result must be the canonical mac_validation_return.json directly inside output")
        jsx=out/"olmsmoother_v1_32bpc_mac_validation.jsx"
        started_path=out/"jsx_started.json"; error_path=out/"jsx_error.json"
        if any(p.exists() or p.is_symlink() for p in (jsx,started_path,error_path)): fail("stale JSX/diagnostic")
        nonce=secrets.token_hex(32)
        refroot=(ROOT/request["windows_reference"]["artifact_root"]).resolve(strict=True)
        expected_inputs={c["id"]:{"path":str((refroot/c["before_effects_frame"]).resolve(strict=True)),"sha256":c["before_effects_sha256"]} for c in request["cases"]}
        expected_outputs={
            c["id"]:{
                role:{
                    "exr":str(out/(c["id"]+"__"+role+".exr")),
                    "settings":str(out/(c["id"]+"__"+role+"__output_module_settings.json")),
                }
                for role in ("no_effect_control","effect_on")
            }
            for c in request["cases"]
        }
        output_paths=[Path(p) for roles in expected_outputs.values() for artifacts in roles.values() for p in artifacts.values()]
        preflight_outputs(output_paths)
        attestor_nonce=secrets.token_hex(32)
        attestor_path=ROOT/"scripts/attest_olmsmoother_v1_mac_process_20260730.py"; python_executable=Path(sys.executable).resolve(strict=True)
        jsx_text=jsx_source(request,plugin.resolve(strict=True),out,result,nonce,attestor_nonce,started_path,error_path)
        exclusive_bytes(jsx,jsx_text.encode())
        harness_paths={"runner":Path(__file__).resolve(),"reporter":REPORTER,"request":REQUEST,"manifest":MANIFEST,"input_template":INPUT_TEMPLATE,"smoke":SMOKE,"boundary_probe":BOUNDARY_PROBE,"port_source":PORT_SOURCE,"strings_source":STRINGS_SOURCE,"generated_jsx":jsx}
        invocation={"platform":"macOS","method":"after_effects_file_scripts_run_script_file","manual_trigger_required":True,"generated_jsx":{"path":str(jsx),"sha256":digest(jsx)}}
        challenge={"kind":"olmsmoother_v1_mac_process_challenge","schema_version":4,"run_nonce":nonce,"attestor_nonce":attestor_nonce,"started_at":time.time(),"expected":{"ae_executable":{"path":str(ae),"sha256":digest(ae)},"module":{"path":str(binary.resolve(strict=True)),"sha256":digest(binary)}},"attestor":{"script":{"path":str(attestor_path.resolve(strict=True)),"sha256":digest(attestor_path)},"executable":{"path":str(python_executable),"sha256":digest(python_executable)}},"harness":{name:identity(path) for name,path in harness_paths.items()},"invocation":invocation,"diagnostics":{"started_path":str(started_path),"error_path":str(error_path)},"input_interpretation":runtime_input_interpretation(request),"inputs":expected_inputs,"warmup_contract":{"case_id":request["cases"][0]["id"],"effect":{"name":"OLM Smoother","match_name":"OLM Smoother","enabled":True},"params":request["cases"][0]["params"],"project":{"bits_per_channel":32,"renderer_raw":1816,"working_space_raw_allowed":request["common_setup"]["working_space_raw_allowed"],"named_working_space_allowed":False}},"result_path":str(result),"outputs":expected_outputs}
        challenge_path=out/"process_challenge.json"
        if challenge_path.exists() or challenge_path.is_symlink(): fail("stale challenge")
        exclusive_json(challenge_path,challenge)
        attestor=subprocess.Popen([str(python_executable),str(attestor_path),"--challenge",str(challenge_path),"--attestor-nonce",attestor_nonce,"--timeout","900"])
        preflight_outputs(output_paths)
        proc=subprocess.Popen([str(ae)])
        deadline=time.monotonic()+900
        while True:
            if error_path.is_file():
                error_data=json.loads(error_path.read_text())
                if error_data.get("kind")!="olmsmoother_v1_jsx_error" or error_data.get("schema_version")!=1 or error_data.get("run_nonce")!=nonce or error_data.get("attestor_nonce")!=attestor_nonce: fail("unbound JSX error sidecar")
                fail("JSX error sidecar: "+json.dumps(error_data,sort_keys=True)[:4096])
            if result.is_file(): break
            proc_rc=proc.poll(); attestor_rc=attestor.poll()
            if result.is_file(): break
            if error_path.is_file(): continue
            if proc_rc is not None or (attestor_rc is not None and attestor_rc!=0) or time.monotonic()>deadline: fail("independent attestor/AfterFX failed before result")
            time.sleep(.05)
        if error_path.is_file(): fail("JSX error sidecar coexists with result")
        if attestor.wait(timeout=max(.1,deadline-time.monotonic()))!=0: fail("independent attestor rejected run")
        returned=json.loads(result.read_text())
        attestation_path=out/"mac_process_attestation.json"
        if returned.get("run_nonce")!=nonce or returned.get("ae_version")!=AE_VERSION or returned.get("input_interpretation")!=runtime_input_interpretation(request) or returned.get("process_attestation_sha256")!=digest(attestation_path): fail("result nonce/AE-version/input-interpretation/independent-attestation binding")
    except (OSError,subprocess.SubprocessError,ValueError) as e: print("[FAIL_CLOSED]",e); return 1
    print(result); return 0
if __name__=="__main__": raise SystemExit(main())
