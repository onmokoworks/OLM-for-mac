#!/usr/bin/env python3
"""Verify all ten OLMSmoother v1 Mac returns and classify AE exactness."""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from datetime import datetime
from pathlib import Path
from report_olmsmoother2_no_key_32bpc_mac_validation_20260715 import compare, inspect_float_rgba_exr, VerificationError
from compare_float_exr import read_planes

ROOT=Path(__file__).resolve().parents[1]
REQUEST=ROOT/"refs/mac_validation_requests/olmsmoother_v1_32bpc_mac_validation_20260730.json"
MANIFEST=ROOT/"refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMSmoother/reference_manifest.json"
RUNNER=ROOT/"scripts/run_olmsmoother_v1_32bpc_mac_validation_20260730.py"
INPUT_TEMPLATE=ROOT/"refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep"
SMOKE=ROOT/"refs/scripts/smoke_olmsmoother_v1_32bpc_mac_validation_20260730.py"
BOUNDARY_PROBE=ROOT/"tools/emulation/probe_olmsmoother_v1_pf16_mainkernel_boundary_20260731.py"
PORT_SOURCE=ROOT/"mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
STRINGS_SOURCE=ROOT/"mac/OLMSmoother/OLMSmoother_Strings.cpp"
AE_VERSION="26.3x87"
HARNESS_PATHS={
    "runner":RUNNER,
    "reporter":Path(__file__).resolve(),
    "request":REQUEST,
    "manifest":MANIFEST,
    "input_template":INPUT_TEMPLATE,
    "smoke":SMOKE,
    "boundary_probe":BOUNDARY_PROBE,
    "port_source":PORT_SOURCE,
    "strings_source":STRINGS_SOURCE,
}
ALLOWED=("OLM Smoother-0001","OLM Smoother-0002","OLM Smoother-0003")
INPUT_TEMPLATE_SHA256="51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
def digest(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v:object)->str: return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
def direct(base:Path,value:str,label:str)->Path:
    raw=Path(value)
    if raw.is_symlink(): raise ValueError(label+" symlink forbidden")
    p=raw.resolve(strict=True)
    if p.parent!=base: raise ValueError(label+" must be directly inside output directory")
    return p
def project_evidence(value:object)->bool:
    if not isinstance(value,dict): return False
    if value.get("bits_per_channel")!=32 or value.get("renderer_raw")!=1816: return False
    kind=value.get("working_space_raw_type"); raw=value.get("working_space_raw")
    return (kind in ("null","undefined") and raw is None) or (kind=="string" and raw in ("","None"))
def runtime_input_interpretation(req:dict)->dict:
    raw=req["mac_run_contract"]["input_interpretation"]
    return {**raw,"template_path":str(INPUT_TEMPLATE.resolve(strict=True))}
def alpha_is_exact_one(path:Path)->bool:
    planes,width,height=read_planes(path)
    return planes["A"]==struct.pack("<f",1.0)*(width*height)
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("result",type=Path); ap.add_argument("--output-dir",type=Path); a=ap.parse_args()
    try:
        req=json.loads(REQUEST.read_text()); manifest_path=ROOT/req["windows_reference"]["manifest"]
        if REQUEST.is_symlink() or manifest_path.is_symlink(): raise ValueError("request/manifest symlink forbidden")
        if manifest_path.resolve(strict=True)!=MANIFEST: raise ValueError("request manifest identity drift")
        manifest=json.loads(manifest_path.read_text())
        refroot_raw=ROOT/req["windows_reference"]["artifact_root"]
        if refroot_raw.is_symlink() or any(parent.is_symlink() for parent in [refroot_raw,*refroot_raw.parents] if parent.exists()): raise ValueError("Windows reference root/parent symlink forbidden")
        refroot=refroot_raw.resolve(strict=True)
        if manifest_path.resolve(strict=True).parent!=refroot: raise ValueError("manifest containment")
        if req.get("windows_reference",{}).get("ae_version")!=AE_VERSION or manifest.get("ae_version")!=AE_VERSION or manifest.get("project",{}).get("bits_per_channel")!=32 or manifest["project"].get("working_space") is not None or manifest["project"].get("project_gpu_accel_type")!={"current_name":"SOFTWARE","raw":1816}: raise ValueError("Windows manifest host contract")
        expected_input_request={"method":"hash_bound_aep_template_footage_replace","template_path":"refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep","template_sha256":INPUT_TEMPLATE_SHA256,"footage_item_name":"OLM_COLOR_PROBE_INPUT","comp_item_name":"OLM_COLOR_PROBE_COMP","preserve_rgb":True,"verification":"all_ten_no_effect_controls_raw_float32_exact"}
        if req.get("mac_run_contract",{}).get("input_interpretation")!=expected_input_request or INPUT_TEMPLATE.is_symlink() or digest(INPUT_TEMPLATE.resolve(strict=True))!=INPUT_TEMPLATE_SHA256: raise ValueError("Preserve RGB input template contract")
        expected_output_settings={"api":"OutputModule.getSettings(GetSettingsFormat.STRING)","one_sidecar_per_role":True,"no_effect_and_effect_settings_must_match":True}
        if req["mac_run_contract"].get("output_settings_capture")!=expected_output_settings: raise ValueError("output settings capture contract")
        if req["mac_run_contract"].get("cache_policy")!={"after_each_footage_replace":"app.purge(PurgeTarget.ALL_CACHES)","between_no_effect_and_effect":"forbidden"}: raise ValueError("cache policy contract")
        manifest_cases=manifest.get("cases",[])
        if [c.get("id") for c in manifest_cases]!=[c["id"] for c in req["cases"]]: raise ValueError("Windows manifest case/order mismatch")
        for spec,source in zip(req["cases"],manifest_cases):
            if source.get("before_effects_frame")!=spec["before_effects_frame"] or source.get("frame")!=spec["effect_frame"]: raise ValueError(spec["id"]+": Windows manifest filename binding")
            expected=[{"name":p["name"],"match_name":p["match_name"],"property_index":p["property_index"],"value":p["value"]} for p in source["effects"][0]["params"] if p["match_name"] in ALLOWED]
            if expected!=spec["params"]: raise ValueError(spec["id"]+": Windows manifest parameter binding")
            for key,hashkey in (("before_effects_frame","before_effects_sha256"),("effect_frame","effect_sha256")):
                raw=refroot/spec[key]
                if raw.is_symlink() or raw.resolve(strict=True).parent!=refroot or digest(raw)!=spec[hashkey]: raise ValueError(spec["id"]+": Windows reference path/hash")
        out=(a.output_dir or a.result.parent).resolve(strict=True)
        if out.is_symlink() or a.result.is_symlink(): raise ValueError("output/result symlink forbidden")
        result=a.result.resolve(strict=True)
        if result.parent!=out or result.name!="mac_validation_return.json": raise ValueError("result path/name contract")
        data=json.loads(result.read_text())
        result_keys={"kind","schema_version","run_nonce","process_attestation_sha256","ae_exact_claim","callback_claim","ae_version","input_interpretation","project","warmup_contract","warmup_evidence","plugin","cases"}
        if set(data)!=result_keys or data.get("kind")!="olmsmoother_v1_32bpc_mac_validation_return" or data.get("schema_version")!=2 or data.get("ae_exact_claim") is not False: raise ValueError("return schema/kind/claim boundary")
        if data.get("callback_claim")!="classic_host_conversion_hypothesis_only": raise ValueError("native PF32 callback must not be claimed")
        if data.get("ae_version")!=AE_VERSION: raise ValueError("Mac/Windows AE version contract")
        expected_input_interpretation=runtime_input_interpretation(req)
        if data.get("input_interpretation")!=expected_input_interpretation: raise ValueError("Preserve RGB result input interpretation")
        project=data.get("project",{})
        if project.get("renderer")!="SOFTWARE" or project.get("working_space")!="None" or not project_evidence(project): raise ValueError("AE project raw contract drift/named working space")
        plugin=data.get("plugin",{}); bundle=Path(plugin.get("bundle_path","")); macho=Path(plugin.get("macho_path",""))
        if bundle.name!="OLMSmoother.plugin" or bundle.is_symlink() or macho.is_symlink() or macho.resolve(strict=True)!=bundle.resolve(strict=True)/"Contents/MacOS/OLMSmoother" or digest(macho)!=plugin.get("macho_sha256"): raise ValueError("bundle/Mach-O path or hash invalid")
        att_path=out/"mac_process_attestation.json"
        if att_path.is_symlink(): raise ValueError("attestation symlink")
        att=json.loads(att_path.read_text())
        nonce=data.get("run_nonce")
        if not re.fullmatch(r"[0-9a-f]{64}",nonce or ""): raise ValueError("run nonce")
        if att.get("kind")!="olmsmoother_v1_mac_process_attestation" or att.get("schema_version")!=3 or att.get("run_nonce")!=nonce or data.get("process_attestation_sha256")!=digest(att_path): raise ValueError("independent attestation/result binding")
        challenge_path=out/"process_challenge.json"
        if challenge_path.is_symlink(): raise ValueError("challenge symlink")
        challenge=json.loads(challenge_path.read_text())
        expected_inputs={c["id"]:{"path":str((refroot/c["before_effects_frame"]).resolve(strict=True)),"sha256":c["before_effects_sha256"]} for c in req["cases"]}
        expected_outputs={
            c["id"]:{
                role:{
                    "exr":str(out/(c["id"]+"__"+role+".exr")),
                    "settings":str(out/(c["id"]+"__"+role+"__output_module_settings.json")),
                }
                for role in ("no_effect_control","effect_on")
            }
            for c in req["cases"]
        }
        challenge_keys={"kind","schema_version","run_nonce","attestor_nonce","started_at","expected","attestor","harness","invocation","diagnostics","input_interpretation","inputs","warmup_contract","result_path","outputs"}
        if set(challenge)!=challenge_keys or challenge["kind"]!="olmsmoother_v1_mac_process_challenge" or challenge["schema_version"]!=4 or challenge["run_nonce"]!=nonce or challenge["result_path"]!=str(result) or challenge["input_interpretation"]!=expected_input_interpretation or challenge["inputs"]!=expected_inputs or challenge["outputs"]!=expected_outputs: raise ValueError("challenge binding")
        if challenge["expected"]["module"]!={"path":str(macho.resolve()),"sha256":digest(macho)} or att.get("challenge_sha256")!=canonical(challenge) or att.get("attestor_nonce")!=challenge["attestor_nonce"]: raise ValueError("attestation challenge identity")
        if att.get("input_interpretation")!=expected_input_interpretation or att.get("inputs")!=expected_inputs: raise ValueError("attested Preserve RGB inputs")
        ae_expected=challenge["expected"]["ae_executable"]
        if digest(Path(ae_expected["path"]))!=ae_expected["sha256"]: raise ValueError("AfterFX identity")
        if att.get("attestor",{}).get("script")!=challenge["attestor"]["script"] or att.get("attestor",{}).get("executable")!=challenge["attestor"]["executable"] or any(digest(Path(row["path"]))!=row["sha256"] for row in challenge["attestor"].values()): raise ValueError("independent attestor executable/script identity")
        harness=challenge.get("harness",{})
        if set(harness)!=set(HARNESS_PATHS)|{"generated_jsx"}: raise ValueError("harness identity schema")
        for name,path in HARNESS_PATHS.items():
            if path.is_symlink():
                raise ValueError("harness symlink: "+name)
            expected_path=path.resolve(strict=True)
            if harness.get(name)!={"path":str(expected_path),"sha256":digest(expected_path)}:
                raise ValueError("harness path/hash: "+name)
        jsx_row=harness.get("generated_jsx",{})
        if not isinstance(jsx_row,dict) or set(jsx_row)!={"path","sha256"}: raise ValueError("generated JSX identity schema")
        generated_jsx=direct(out,jsx_row["path"],"generated JSX")
        if generated_jsx.name!="olmsmoother_v1_32bpc_mac_validation.jsx" or digest(generated_jsx)!=jsx_row["sha256"]: raise ValueError("generated JSX path/hash")
        expected_invocation={"platform":"macOS","method":"after_effects_file_scripts_run_script_file","manual_trigger_required":True,"generated_jsx":jsx_row}
        if challenge.get("invocation")!=expected_invocation: raise ValueError("Mac JSX invocation contract")
        expected_diagnostics={"started_path":str(out/"jsx_started.json"),"error_path":str(out/"jsx_error.json")}
        if challenge.get("diagnostics")!=expected_diagnostics: raise ValueError("diagnostic path binding")
        started_path=out/"jsx_started.json"; error_path=out/"jsx_error.json"
        if started_path.is_symlink() or error_path.is_symlink() or error_path.exists(): raise ValueError("JSX diagnostic error/symlink")
        started=json.loads(started_path.read_text())
        if set(started)!={"kind","schema_version","run_nonce","jsx_path","jsx_sha256"} or started!={"kind":"olmsmoother_v1_jsx_started","schema_version":1,"run_nonce":nonce,"jsx_path":str(generated_jsx),"jsx_sha256":digest(generated_jsx)}: raise ValueError("JSX start identity")
        protocol_names=("pre_request.json","pre_ok.json","post_request.json","post_ok.json")
        protocol_paths={name:out/name for name in protocol_names}
        if any(p.is_symlink() for p in protocol_paths.values()): raise ValueError("protocol symlink")
        preq,preok,postq,postok=[json.loads(protocol_paths[name].read_text()) for name in protocol_names]
        chash=canonical(challenge); anonce=challenge["attestor_nonce"]
        if set(preq)!={"kind","schema_version","run_nonce","attestor_nonce","challenge_sha256","sequence","warmup"} or {k:preq[k] for k in preq if k!="warmup"}!={"kind":"olmsmoother_v1_pre_request","schema_version":1,"run_nonce":nonce,"attestor_nonce":anonce,"challenge_sha256":chash,"sequence":1}: raise ValueError("pre request")
        warmup=preq["warmup"]; first=req["cases"][0]
        expected_warmup={"effect":{"name":"OLM Smoother","match_name":"OLM Smoother","enabled":True},"params":first["params"],"project":{k:project[k] for k in ("bits_per_channel","renderer_raw","working_space_raw","working_space_raw_type")}}
        expected_warmup_contract={"case_id":first["id"],"effect":{"name":"OLM Smoother","match_name":"OLM Smoother","enabled":True},"params":first["params"],"project":{"bits_per_channel":32,"renderer_raw":1816,"working_space_raw_allowed":req["common_setup"]["working_space_raw_allowed"],"named_working_space_allowed":False}}
        if challenge["warmup_contract"]!=expected_warmup_contract or data.get("warmup_contract")!=expected_warmup_contract or warmup!={"rendered":False,"removed":True,"effect":expected_warmup,"case_id":first["id"]} or data.get("warmup_evidence")!=warmup: raise ValueError("warmup complete challenge/result contract equality")
        if preok.get("kind")!="olmsmoother_v1_pre_ok" or preok.get("run_nonce")!=nonce or preok.get("attestor_nonce")!=anonce or preok.get("challenge_sha256")!=chash or preok.get("pre_request_sha256")!=digest(protocol_paths["pre_request.json"]): raise ValueError("pre ok")
        if postq.get("kind")!="olmsmoother_v1_post_request" or postq.get("run_nonce")!=nonce or postq.get("attestor_nonce")!=anonce or postq.get("challenge_sha256")!=chash or postq.get("sequence")!=2 or postq.get("pre_request_sha256")!=digest(protocol_paths["pre_request.json"]) or postq.get("pre_ok_sha256")!=digest(protocol_paths["pre_ok.json"]): raise ValueError("post request")
        if postok.get("kind")!="olmsmoother_v1_post_ok" or postok.get("run_nonce")!=nonce or postok.get("attestor_nonce")!=anonce or postok.get("challenge_sha256")!=chash or postok.get("post_request_sha256")!=digest(protocol_paths["post_request.json"]) or postok.get("attestation_sha256")!=digest(att_path): raise ValueError("post ok")
        mt=[protocol_paths[n].stat().st_mtime_ns for n in protocol_names]
        if not challenge_path.stat().st_mtime_ns <= started_path.stat().st_mtime_ns <= mt[0] <= mt[1] <= mt[2] <= att_path.stat().st_mtime_ns <= mt[3] <= result.stat().st_mtime_ns: raise ValueError("protocol causal ordering/timestamps")
        pre,post=att.get("pre",{}).get("snapshot",{}),att.get("post",{}).get("snapshot",{})
        if pre!=post or pre.get("process",{}).get("pid")==att.get("attestor",{}).get("pid") or pre.get("process",{}).get("executable_path")!=ae_expected["path"] or pre.get("process",{}).get("executable_sha256")!=ae_expected["sha256"] or pre.get("module",{}).get("path")!=str(macho.resolve()) or pre.get("module",{}).get("sha256")!=digest(macho) or pre.get("module",{}).get("vmmap_match_count")!=1 or not att.get("attestor",{}).get("birth_token"): raise ValueError("independent attestor/pre-post process identity")
        returned=data.get("cases",[])
        if [x.get("id") for x in returned]!=[x["id"] for x in req["cases"]]: raise ValueError("case/order/case mismatch")
        comparisons=[]; working_space_readbacks=[]; controls=True; effects=True; opaque_inputs=True
        for spec,row in zip(req["cases"],returned):
            if set(row)!={"id","input","params","outputs"} or set(row.get("outputs",{}))!={"no_effect_control","effect_on"}: raise ValueError(spec["id"]+": case/output schema")
            if row.get("params")!=spec["params"] or tuple(p.get("match_name") for p in row.get("params",[]))!=ALLOWED: raise ValueError(spec["id"]+": parameter contract")
            if row.get("input")!=expected_inputs[spec["id"]]: raise ValueError(spec["id"]+": attested input path/hash")
            opaque_inputs=opaque_inputs and alpha_is_exact_one(refroot/spec["before_effects_frame"])
            entry={"id":spec["id"]}
            role_settings={}
            for role,refkey in (("no_effect_control","before_effects_frame"),("effect_on","effect_frame")):
                item=row.get("outputs",{}).get(role,{})
                expected_item_keys={"path","sha256","output_module_settings","effect_enabled","effect","params_readback","readback_before_render","readback_after_render"}
                if set(item)!=expected_item_keys or set(item.get("output_module_settings",{}))!={"path","sha256","serialization","settings"}: raise ValueError(spec["id"]+": "+role+" output schema")
                p=direct(out,item.get("path",""),spec["id"]+" "+role)
                if item.get("sha256")!=digest(p) or item.get("effect_enabled") is not (role=="effect_on") or item.get("effect")!={"name":"OLM Smoother","match_name":"OLM Smoother"} or item.get("params_readback")!=spec["params"]: raise ValueError(spec["id"]+": hash/effect/readback")
                settings_item=item.get("output_module_settings",{})
                settings_path=direct(out,settings_item.get("path",""),spec["id"]+" "+role+" output settings")
                if settings_path.name!=spec["id"]+"__"+role+"__output_module_settings.json" or settings_item.get("sha256")!=digest(settings_path): raise ValueError(spec["id"]+": output settings path/hash")
                settings_payload=json.loads(settings_path.read_text())
                expected_settings_keys={"kind","schema_version","run_nonce","case_id","role","output_template","capture_api","output_path","settings"}
                if set(settings_payload)!=expected_settings_keys or settings_payload.get("kind")!="olmsmoother_v1_output_module_settings" or settings_payload.get("schema_version")!=1 or settings_payload.get("run_nonce")!=nonce or settings_payload.get("case_id")!=spec["id"] or settings_payload.get("role")!=role or settings_payload.get("output_template")!="OLM EXR 32 Float" or settings_payload.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or settings_payload.get("output_path")!=str(p): raise ValueError(spec["id"]+": output settings payload")
                serialized=json.dumps(settings_payload["settings"],sort_keys=True,separators=(",",":"),ensure_ascii=False)
                if settings_item.get("serialization")!=serialized or settings_item.get("settings")!=settings_payload["settings"]: raise ValueError(spec["id"]+": output settings serialization")
                role_settings[role]=serialized
                before=item.get("readback_before_render",{}); after=item.get("readback_after_render",{})
                expected_effect={"name":"OLM Smoother","match_name":"OLM Smoother","enabled":role=="effect_on"}
                if before!=after or before.get("effect")!=expected_effect or before.get("params")!=spec["params"] or not project_evidence(before.get("project")) or before.get("project")!={k:project[k] for k in ("bits_per_channel","renderer_raw","working_space_raw","working_space_raw_type")}: raise ValueError(spec["id"]+": pre/post render/project readback")
                working_space_readbacks.append({"case_id":spec["id"],"role":role,"before":before["project"],"after":after["project"]})
                expected_artifacts={"exr":{"path":str(p),"sha256":digest(p)},"settings":{"path":str(settings_path),"sha256":digest(settings_path)}}
                if att.get("outputs",{}).get(spec["id"],{}).get(role)!=expected_artifacts: raise ValueError(spec["id"]+": attestation output binding")
                if postq.get("artifacts",{}).get(spec["id"],{}).get(role)!=expected_artifacts: raise ValueError(spec["id"]+": post request artifact binding")
                info=inspect_float_rgba_exr(p,(1920,1080))
                counts=info["sample_counts"]
                if info["channel_order"]!=["A","B","G","R"] or info["sample_types"]!=[2,2,2,2] or info["compression"]!=0 or any(counts.get(k,0) for k in ("nan","+inf","-inf")): raise ValueError(spec["id"]+": EXR contract")
                cmp=compare(refroot/spec[refkey],p); entry[role]=cmp
                exact=cmp["mismatched_values"]==0
                if role=="no_effect_control": controls=controls and exact
                else: effects=effects and exact
            if role_settings.get("no_effect_control")!=role_settings.get("effect_on"): raise ValueError(spec["id"]+": output settings differ by role")
            comparisons.append(entry)
        artifact_exact=controls and effects
        coverage=[row["case_id"]+":"+row["role"] for row in working_space_readbacks]
        if len(working_space_readbacks)!=20 or len(set(coverage))!=20: raise ValueError("working-space evidence coverage")
        if not controls:
            status="blocked_mac_preserve_rgb_roundtrip"
        elif not effects:
            status="mac_roundtrip_exact_legacy_effect_mismatch_unattributed"
        else:
            status="raw_float32_exact_artifact_only_missing_windows_provenance"
        missing_exact_proof=[
            "fresh Windows effect-off/effect-on recapture from the identical hash-bound Preserve RGB EXR source contract, or an equivalent same-run PF16 entry witness",
            "Windows source hashes and footage interpretation/alpha-mode attestation",
            "Windows output-module settings and output-profile readback",
            "Windows loaded AEX/process/module identity spanning the capture",
            "fractional-alpha source coverage",
        ]
        report={
            "kind":"olmsmoother_v1_32bpc_mac_validation_report",
            "schema_version":7,
            "status":status,
            "ae_exact_claim":False,
            "ae_exact_scope":"not promoted: retained Windows effect artifacts lack the identical hash-bound Preserve RGB source/process contract",
            "ae_version_contract":{"windows_reference":AE_VERSION,"mac_return":data["ae_version"],"version_strings_equal":True},
            "case_count":10,
            "input_interpretation":expected_input_interpretation,
            "project_raw_contract":project,
            "harness_provenance":harness,
            "jsx_invocation_contract":expected_invocation,
            "jsx_start_evidence":started,
            "warmup_contract":expected_warmup_contract,
            "warmup_evidence":warmup,
            "causal_boundary":"challenge pins the full harness, Preserve RGB template, all ten input EXRs, generated JSX, and explicit macOS File > Scripts invocation; JSX start, project setup, and a disposable non-rendered effect warmup precede pre_request; pre_ok/post_request bracket all 20 actual renders and 20 output-settings sidecars",
            "working_space_evidence":{"assertion":"all 20 render gates have pre/post project raw value and type identical to the bound top-level project contract","gate_count":20,"readback_count":40,"coverage":coverage,"gates":working_space_readbacks},
            "mac_preserve_rgb_roundtrip_all_exact":controls,
            "legacy_windows_effect_artifact_all_exact":effects,
            "effect_gate_all_exact":False,
            "raw_float32_exact_artifact_classification":artifact_exact,
            "same_source_cross_host_proven":False,
            "windows_source_interpretation_attested":False,
            "windows_output_settings_attested":False,
            "windows_pf16_entry_attested":False,
            "windows_process_module_proof":False,
            "effect_attribution_gate_passed":False,
            "alpha_coverage":"opaque_only" if opaque_inputs else "includes_nonopaque",
            "partial_alpha_interpretation_proven":False,
            "raw_float32_comparisons":comparisons,
            "loaded_process_attestation":att,
            "callback_classification":"classic_host_conversion_hypothesis_only",
            "native_pf32_callback_claim":False,
            "missing_exact_proof":missing_exact_proof,
            "next_gate":"Perform one consolidated Windows recapture from these exact ten EXR hashes with Preserve RGB, effect-off/on, output settings, and AEX/process identity; alternatively attest the same-run PF16 entry words.",
            "reason":"Mac Preserve RGB no-effect round-trip is exact, but historical Windows effect artifacts remain diagnostic only" if controls else "Mac Preserve RGB no-effect round-trip is not exact; effect comparisons are not attributable",
        }
        target=out/"validation_report.json"
        if target.exists() or target.is_symlink(): raise ValueError("stale validation report")
        target.write_text(json.dumps(report,indent=2)+"\n")
        print(("[MAC_INPUT_EXACT] " if controls else "[NOT_EXACT] ")+str(target)); return 0 if controls else 1
    except (OSError,KeyError,ValueError,json.JSONDecodeError,struct.error,VerificationError) as e:
        print("[FAIL_CLOSED]",e); return 1
if __name__=="__main__": raise SystemExit(main())
