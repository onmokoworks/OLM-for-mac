#!/usr/bin/env python3
"""Fail-closed report for the OLMDistanceGradation 32bpc Mac return."""
from __future__ import annotations
import argparse, hashlib, json, math, struct, subprocess
from pathlib import Path
from typing import Any
from scripts.verify_32bpc_float_return import inspect_float_rgba_exr, parse_exr_header, decode_attrs, VerificationError

ROOT=Path(__file__).resolve().parents[1]
REQUEST=ROOT/"refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json"
AUDIT=ROOT/"refs/conformance/olmdistancegradation_32bpc_float_evidence_audit_20260715.json"
def digest(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def path(v:Any, root:Path)->Path:
    p=Path(v or ""); return p if p.is_absolute() else root/p
def words(p:Path)->tuple[tuple[int,...],dict[str,int]]:
    attrs,end=parse_exr_header(p); info=decode_attrs(attrs,p); data=p.read_bytes(); w,h=info["width"],info["height"]; row=w*len(info["channels"])*4; table=end+h*8; offsets=struct.unpack_from("<"+"Q"*h,data,end); result=[]; counts={"nan":0,"+inf":0,"-inf":0}
    for off in offsets:
        y,size=struct.unpack_from("<iI",data,off); payload=data[off+8:off+8+size]
        vals=struct.unpack("<"+"I"*(row//4),payload)
        for bits in vals:
            value=struct.unpack("<f",struct.pack("<I",bits))[0]
            if math.isnan(value): counts["nan"]+=1
            elif math.isinf(value): counts["+inf" if value>0 else "-inf"]+=1
        result.append((y,)+vals)
    return tuple(sorted(result)),counts
def compare(mac:Path, win:Path)->dict:
    mi=inspect_float_rgba_exr(mac); wi=inspect_float_rgba_exr(win)
    if mi["dimensions"]!=wi["dimensions"] or mi["channel_order"]!=wi["channel_order"]: raise VerificationError("dimensions/channel order differ")
    mw,mc=words(mac); ww,wc=words(win); equal=mw==ww
    nonzero=sum(a!=b for (_,*aa),(_, *bb) in zip(mw,ww) for a,b in zip(aa,bb)) if len(mw)==len(ww) else -1
    return {"equal":equal,"max_absolute_error":0 if equal else None,"nonzero_count":nonzero,"nan_inf_policy":"raw FLOAT32 words; NaN and +/-Inf words must match exactly","mac_sample_counts":mc,"windows_sample_counts":wc}
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("return_json",type=Path);ap.add_argument("--output",type=Path);ap.add_argument("--case-id");a=ap.parse_args()
    data=json.loads(a.return_json.read_text(encoding="utf-8")); request=json.loads(REQUEST.read_text(encoding="utf-8")); audit=json.loads(AUDIT.read_text(encoding="utf-8")); failures=[]; accepted=[]; observations=[]
    if data.get("kind")!="olmdistancegradation_32bpc_mac_validation_return" or data.get("ae_exact_claim") is not False: failures.append({"case_id":None,"missing":["return kind or explicit ae_exact_claim=false"]})
    expected_project={"bits_per_channel":32,"renderer_name_and_raw_value":{"name":"SOFTWARE","raw_value":1816},"working_space":"None","linear_blending":False}
    if data.get("project_settings")!=expected_project: failures.append({"case_id":None,"missing":["exact AE/project/color settings"]})
    if data.get("output_module",{}).get("template_name")!="OLM EXR 32 Float" or data.get("output_module",{}).get("format")!="OpenEXR" or data.get("output_module",{}).get("sample_type")!="FLOAT" or data.get("output_module",{}).get("compression")!="none": failures.append({"case_id":None,"missing":["exact output template/format/FLOAT32 contract"]})
    plug=data.get("plugin",{}); pp=path(plug.get("path"),Path("."));
    if plug.get("bundle_name")!="OLMDistanceGradation.plugin" or plug.get("filename")!="OLMDistanceGradation" or len(plug.get("sha256", ""))!=64 or not pp.is_file() or plug.get("sha256")!=digest(pp): failures.append({"case_id":None,"missing":["actual Mac plugin binary identity/hash"]})
    pids=[int(v) for v in subprocess.run(["pgrep","-x","After Effects"],capture_output=True,text=True).stdout.split() if v.isdigit()]
    loaded=subprocess.run(["lsof","-Fn","-p",str(pids[0])],capture_output=True,text=True).stdout.splitlines() if len(pids)==1 else []
    exact_loaded=("n"+str(pp.resolve())) if pp.is_file() else ""
    if len(pids)!=1 or loaded.count(exact_loaded)!=1: failures.append({"case_id":None,"missing":["same single AE PID with sole exact loaded plugin path"]})
    by_id={r.get("id"):r for r in audit["cases"]}; returned={r.get("case_id"):r for r in data.get("cases",[]) if isinstance(r,dict)}
    if a.case_id:
        by_id={k:v for k,v in by_id.items() if k==a.case_id}
        if len(by_id)!=1: failures.append({"case_id":None,"missing":["known unique selected case"]})
    if set(returned)!=set(by_id): failures.append({"case_id":None,"missing":["exact selected Windows case set"]})
    for cid, win in by_id.items():
        row=returned.get(cid); missing=[]
        if not row: failures.append({"case_id":cid,"missing":["case return"]});continue
        if row.get("input_sha256")!=win["input_sha256"]: missing.append("Windows-selected input SHA-256")
        if row.get("windows_reference",{}).get("sha256")!=win["output_sha256"]: missing.append("exact Windows effect artifact SHA-256")
        if row.get("all_12_distancegradation_parameter_match_names_and_values")!=win["effect"]["params"]: missing.append("exact 12 parameter match names/values")
        if row.get("same_context_no_effect_control",{}).get("effect_enabled") is not False or row.get("same_context_no_effect_control",{}).get("output_settings_equal") is not True: missing.append("same-context no-effect control")
        outs=row.get("outputs",{}); comparisons={}
        for branch, ref in (("no_effect",win["input"]),("effect_on",win["output"])):
            item=outs.get(branch,{}); mac=path(item.get("path"),a.return_json.parent); winp=ROOT/"refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"/ref
            if item.get("sha256")!=digest(mac) if mac.is_file() else True: missing.append(branch+" Mac output hash")
            try: comparisons[branch]=compare(mac,winp)
            except (OSError,ValueError,VerificationError,struct.error) as e: missing.append(branch+" raw FLOAT32 comparison: "+str(e));continue
            if branch=="effect_on" and comparisons[branch]["equal"] is not True: missing.append(branch+" raw FLOAT32 words differ")
            settings=item.get("output_module_settings",{}); sp=path(settings.get("path"),a.return_json.parent)
            if not sp.is_file() or settings.get("sha256")!=digest(sp): missing.append(branch+" output settings capture")
        observations.append({"case_id":cid,"no_effect_vs_input":comparisons.get("no_effect"),"effect_on_vs_windows_effect":comparisons.get("effect_on")})
        if missing: failures.append({"case_id":cid,"missing":missing})
        else: accepted.append(cid)
    result={"schema":3,"kind":"olmdistancegradation_32bpc_mac_validation_report","status":"accepted_exact" if len(accepted)==len(by_id) and not failures else "fail_closed_pending","accepted_exact_cases":accepted,"failed_cases":failures,"observations":observations,"host_attestation":{"observed_ae_pids":pids,"loaded_plugin_path":str(pp.resolve()) if pp.is_file() else None,"sole_exact_mapping":len(pids)==1 and loaded.count(exact_loaded)==1},"ae_exact_claim_permitted":len(accepted)==len(by_id) and not failures,"reason":"Exact plugin/project/output bindings, a fresh same-context no-effect control artifact, and raw FLOAT32 equality of effect-on output to the Windows effect reference are required. No Windows AE no-effect export exists, so input-vs-control equality is observational and is not promoted."}
    dest=a.output or a.return_json.with_name("validation_report.json");dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2));return 0 if result["ae_exact_claim_permitted"] else 2
if __name__=="__main__": raise SystemExit(main())
