#!/usr/bin/env python3
"""Validate an OLMSmoother2 v2/no-key Mac candidate return, fail closed."""
from __future__ import annotations
import argparse, email.utils, hashlib, json, os, re, stat, struct, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import compare
from compare_pf32_entry_to_exr import compare_pf32_entry
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr
REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json"
def digest(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v: object) -> str: return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
def same_ae_float32_value(actual: object, expected: object) -> bool:
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual)==len(expected) and all(
            struct.pack("<f", float(a)) == struct.pack("<f", float(e)) for a,e in zip(actual,expected)
        )
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and struct.pack("<f", float(actual)) == struct.pack("<f", float(expected))
    return actual == expected
def valid_ae_readback(readback: object, enabled: bool, expected_params: list[dict]) -> bool:
    if not isinstance(readback, dict) or readback.get("effect") != {"name":"OLM Smoother v2","match_name":"OLM Smoother v2","enabled":enabled}:
        return False
    actual_params=readback.get("params")
    if not isinstance(actual_params, list) or len(actual_params)!=len(expected_params):
        return False
    for actual,expected in zip(actual_params,expected_params):
        if not isinstance(actual,dict) or {k:actual.get(k) for k in ("name","match_name","property_index")} != {k:expected[k] for k in ("name","match_name","property_index")}:
            return False
        if not same_ae_float32_value(actual.get("value"),expected["value"]):
            return False
    return True
def strict_protocol_json(path: Path, label: str) -> dict:
    if path.is_symlink(): raise ValueError(f"{label} symlink forbidden")
    st=os.stat(path,follow_symlinks=False)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1: raise ValueError(f"{label} must be one unaliased regular file")
    raw=path.read_bytes()
    if not raw or len(raw)>1024*1024: raise ValueError(f"{label} invalid size")
    def pairs(items):
        value={}
        for key,item in items:
            if key in value: raise ValueError(f"{label} duplicate JSON key")
            value[key]=item
        return value
    value=json.loads(raw.decode("utf-8"),object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"{label} invalid number")))
    if not isinstance(value,dict): raise ValueError(f"{label} must be an object")
    return value
def validate_mac_process_proof(base: Path, result: Path, outputs: dict[str,Path], settings: dict[str,Path], plugin_binary: Path, nonce: str) -> bool:
    names={"challenge":"process_challenge.json","pre":"pre_request.json","pre_ok":"pre_ok.json","post":"post_request.json","attestation":"mac_process_attestation.json","post_ok":"post_ok.json"}
    rows={key:strict_protocol_json(base/name,name) for key,name in names.items()}
    c,pre,pre_ok,post,att,post_ok=(rows[k] for k in ("challenge","pre","pre_ok","post","attestation","post_ok"))
    if set(c)!={"kind","schema_version","run_nonce","started_at","run_challenge_sha256","wrapper_sha256","expected","result_path","outputs"} or c.get("kind")!="olmsmoother2_mac_process_challenge" or c.get("schema_version")!=1 or c.get("run_nonce")!=nonce: raise ValueError("process challenge schema/nonce mismatch")
    run_challenge_path=base/"run_challenge.json"
    run_challenge=strict_protocol_json(run_challenge_path,"run_challenge.json")
    if c.get("run_challenge_sha256")!=digest(run_challenge_path) or c.get("started_at")!=run_challenge.get("started_at"): raise ValueError("freshness challenge is not bound to process challenge")
    expected=c.get("expected",{}); ae=expected.get("ae_executable",{}); module=expected.get("module",{})
    if set(expected)!={"ae_executable","module"} or set(ae)!={"path","sha256"} or set(module)!={"path","sha256"}: raise ValueError("process executable/module schema mismatch")
    ae_path=Path(ae.get("path","")); module_path=Path(module.get("path",""))
    if not ae_path.is_absolute() or ae_path.is_symlink() or ae_path.resolve(strict=True)!=ae_path or digest(ae_path)!=ae.get("sha256"): raise ValueError("AE executable identity/hash mismatch")
    if module_path!=plugin_binary or module_path.is_symlink() or module_path.resolve(strict=True)!=module_path or digest(module_path)!=module.get("sha256"): raise ValueError("plugin module identity/hash mismatch")
    expected_outputs={role:{"exr":str(outputs[role]),"settings":str(settings[role])} for role in ("no_effect_control","effect_on")}
    if c.get("result_path")!=str(result) or c.get("outputs")!=expected_outputs: raise ValueError("process challenge result/artifact path split")
    wrapper=base/"run_mac_wrapper.jsx"
    if not wrapper.is_file() or wrapper.is_symlink() or digest(wrapper)!=c.get("wrapper_sha256"): raise ValueError("wrapper identity/hash mismatch")
    csha=canonical(c)
    if set(pre)!={"kind","schema_version","run_nonce","challenge_sha256","sequence"} or pre!={"kind":"olmsmoother2_mac_process_pre_request","schema_version":1,"run_nonce":nonce,"challenge_sha256":csha,"sequence":1}: raise ValueError("pre request chain mismatch")
    if set(pre_ok)!={"kind","schema_version","run_nonce","challenge_sha256","pre_request_sha256","pre_snapshot_sha256","snapshot"} or pre_ok.get("kind")!="olmsmoother2_mac_process_pre_ok" or pre_ok.get("schema_version")!=1 or pre_ok.get("run_nonce")!=nonce or pre_ok.get("challenge_sha256")!=csha or pre_ok.get("pre_request_sha256")!=canonical(pre) or pre_ok.get("pre_snapshot_sha256")!=canonical(pre_ok.get("snapshot")): raise ValueError("pre acknowledgement chain mismatch")
    def validate_snapshot(snapshot: object, label: str) -> dict:
        if not isinstance(snapshot,dict) or set(snapshot)!={"process","module"}: raise ValueError(f"{label} snapshot schema mismatch")
        process=snapshot.get("process"); loaded=snapshot.get("module")
        if not isinstance(process,dict) or set(process)!={"pid","birth_token","executable_path","executable_sha256","dev","ino","size","mtime_ns"}: raise ValueError(f"{label} process schema mismatch")
        if not isinstance(loaded,dict) or set(loaded)!={"path","sha256","dev","ino","size","mtime_ns","vmmap_match_count"}: raise ValueError(f"{label} module schema mismatch")
        if type(process.get("pid")) is not int or process["pid"]<=0 or not isinstance(process.get("birth_token"),str) or not process["birth_token"] or process.get("executable_path")!=str(ae_path) or process.get("executable_sha256")!=ae["sha256"]: raise ValueError(f"{label} process identity mismatch")
        if loaded.get("path")!=str(module_path) or loaded.get("sha256")!=module["sha256"] or loaded.get("vmmap_match_count")!=1: raise ValueError(f"{label} module identity mismatch")
        for row in (process,loaded):
            if any(type(row.get(key)) is not int or row[key]<0 for key in ("dev","ino","size","mtime_ns")): raise ValueError(f"{label} stat identity mismatch")
        return snapshot
    pre_snapshot=validate_snapshot(pre_ok["snapshot"],"pre")
    expected_artifacts={role:{"exr_sha256":digest(outputs[role]),"settings_sha256":digest(settings[role])} for role in ("no_effect_control","effect_on")}
    if set(post)!={"kind","schema_version","run_nonce","challenge_sha256","sequence","pre_request_sha256","pre_snapshot_sha256","pre_ok_sha256","result_sha256","artifacts"} or post.get("kind")!="olmsmoother2_mac_process_post_request" or post.get("schema_version")!=1 or post.get("run_nonce")!=nonce or post.get("challenge_sha256")!=csha or post.get("sequence")!=2 or post.get("pre_request_sha256")!=canonical(pre) or post.get("pre_snapshot_sha256")!=pre_ok.get("pre_snapshot_sha256") or post.get("pre_ok_sha256")!=digest(base/"pre_ok.json") or post.get("result_sha256")!=digest(result) or post.get("artifacts")!=expected_artifacts: raise ValueError("post request result/artifact chain mismatch")
    invariants={"same_pid_birth":True,"same_executable":True,"same_module_file":True,"exact_vmmap_pre":True,"exact_vmmap_post":True,"pre_nonce_digest_chain":True,"post_snapshot_observed_by_attestor":True}
    if set(att)!={"kind","schema_version","status","run_nonce","challenge_sha256","pre","post","artifacts","result","invariants"} or att.get("kind")!="olmsmoother2_mac_process_attestation" or att.get("schema_version")!=1 or att.get("status")!="attested" or att.get("run_nonce")!=nonce or att.get("challenge_sha256")!=csha or att.get("invariants")!=invariants: raise ValueError("attestation schema/invariants mismatch")
    if att.get("pre")!={"request_sha256":canonical(pre),"snapshot":pre_ok["snapshot"],"snapshot_sha256":pre_ok["pre_snapshot_sha256"]}: raise ValueError("attestation pre binding mismatch")
    apost=att.get("post",{})
    post_snapshot=validate_snapshot(apost.get("snapshot"),"post")
    if set(apost)!={"request_sha256","snapshot","snapshot_sha256"} or apost.get("request_sha256")!=canonical(post) or apost.get("snapshot_sha256")!=canonical(post_snapshot): raise ValueError("attestation post binding mismatch")
    for section,keys in (("process",("pid","birth_token","executable_path","executable_sha256","dev","ino","size","mtime_ns")),("module",("path","sha256","dev","ino","size","mtime_ns"))):
        if any(pre_snapshot[section][key]!=post_snapshot[section][key] for key in keys): raise ValueError("attestation process/module interval changed")
    verified={role:{"exr":str(outputs[role]),"exr_sha256":expected_artifacts[role]["exr_sha256"],"settings":str(settings[role]),"settings_sha256":expected_artifacts[role]["settings_sha256"]} for role in expected_artifacts}
    if att.get("artifacts")!=verified or att.get("result")!={"path":str(result),"sha256":digest(result)}: raise ValueError("attestation result/artifact binding mismatch")
    if set(post_ok)!={"kind","schema_version","run_nonce","challenge_sha256","post_request_sha256","attestation_sha256"} or post_ok!={"kind":"olmsmoother2_mac_process_post_ok","schema_version":1,"run_nonce":nonce,"challenge_sha256":csha,"post_request_sha256":canonical(post),"attestation_sha256":digest(base/"mac_process_attestation.json")}: raise ValueError("post acknowledgement/attestation hash mismatch")
    return True
def parse_time(value: object) -> datetime:
    if not isinstance(value,str): raise ValueError("timestamp missing")
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:
        parsed=email.utils.parsedate_to_datetime(value)
    if parsed.tzinfo is None: raise ValueError("timestamp timezone missing")
    return parsed.astimezone(timezone.utc)
def resolve_return_paths(result: Path, output_dir: Path, case: dict) -> tuple[Path,dict[str,Path],dict[str,Path],dict]:
    if output_dir.is_symlink() or result.is_symlink(): raise ValueError("result/output directory symlink forbidden")
    base=output_dir.resolve(strict=True)
    result=result.resolve(strict=True)
    if result.parent != base: raise ValueError("result must be a non-symlink file directly in dedicated output directory")
    challenge_path=base/"run_challenge.json"
    challenge=strict_protocol_json(challenge_path,"run_challenge.json")
    paths=[]; outputs={}; settings={}
    for branch in ("no_effect_control","effect_on"):
        item=case.get("outputs",{}).get(branch,{})
        raw=Path(item.get("path",""))
        p=raw.resolve(strict=True)
        sp=Path(item.get("output_module_settings",{}).get("path","")).resolve(strict=True)
        if raw.is_symlink() or sp.is_symlink() or p.parent != base or sp.parent != base:
            raise ValueError(f"{branch} path escapes output directory or is symlink")
        paths += [p,sp]; outputs[branch]=p; settings[branch]=sp
    if len(set(paths+[result,challenge_path.resolve(strict=True)])) != 6:
        raise ValueError("duplicate/basename-alias result, output, settings, or challenge path")
    expected_roles={branch:{"exr":str(outputs[branch]),"settings":str(settings[branch])} for branch in ("no_effect_control","effect_on")}
    if set(challenge)!={"kind","run_nonce","started_at","result_path","output_paths"} or challenge.get("kind")!="olmsmoother2_mac_run_challenge" or challenge.get("result_path") != str(result) or challenge.get("output_paths") != expected_roles:
        raise ValueError("challenge/output path split")
    return result,outputs,settings,challenge
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("result",type=Path); ap.add_argument("--output-dir",type=Path); a=ap.parse_args()
    request=json.loads(REQUEST.read_text()); fail=[]
    try: d=json.loads(a.result.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: print(f"[FAIL_CLOSED] {e}"); return 1
    if d.get("kind")!="olmsmoother2_no_key_32bpc_mac_validation_return": fail.append("wrong return kind")
    out=a.output_dir or a.result.parent
    cases=d.get("cases",[]); case=cases[0] if len(cases)==1 else {}
    try:
        result_path,resolved_outputs,resolved_settings,challenge=resolve_return_paths(a.result,out,case)
        nonce=d.get("run_nonce")
        if not isinstance(nonce,str) or not re.fullmatch(r"[0-9a-f]{64}",nonce) or nonce!=challenge.get("run_nonce"): raise ValueError("run nonce/challenge mismatch")
        challenge_start=parse_time(challenge.get("started_at")); started=parse_time(d.get("started_at")); ended=parse_time(d.get("ended_at"))
        if not challenge_start <= started <= ended: raise ValueError("invalid run timestamp ordering")
        for p in [result_path,*resolved_outputs.values(),*resolved_settings.values()]:
            m=datetime.fromtimestamp(p.stat().st_mtime,tz=timezone.utc)
            if m < challenge_start: raise ValueError(f"stale preexisting artifact: {p.name}")
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f"[FAIL_CLOSED] output path/freshness binding failed: {e}"); return 1
    if d.get("ae_exact_claim") is not False: fail.append("ae_exact_claim must be false")
    if d.get("platform")!="macOS" or not d.get("macos_product_version") or not d.get("macos_build_version") or not d.get("ae_version"): fail.append("host OS/AE identity missing")
    expected_project={"bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False}
    if {k:d.get("project",{}).get(k) for k in expected_project} != expected_project: fail.append("project/renderer/color contract drift")
    expected_interpretation=request["mac_run_contract"]["input_interpretation"]; template=ROOT/expected_interpretation["template"]; interpretation=d.get("input_interpretation",{})
    if interpretation.get("method")!="hash_bound_aep_template_footage_replace" or interpretation.get("preserve_rgb") is not True or interpretation.get("verification")!="no_effect_raw_float32_gate": fail.append("input Preserve RGB interpretation contract drift")
    if interpretation.get("template_path")!=str(template.resolve()) or interpretation.get("template_sha256")!=expected_interpretation["template_sha256"] or not template.is_file() or (template.is_file() and digest(template)!=expected_interpretation["template_sha256"]): fail.append("input Preserve RGB template identity missing/mismatched")
    om=d.get("output_module",{})
    expected_output_template=request["mac_run_contract"]["output_template"]
    if om.get("template_name")!=expected_output_template or om.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or om.get("sample_type")!="FLOAT" or om.get("compression")!="none" or om.get("channels")!= ["A","B","G","R"]: fail.append("output contract drift")
    plugin=d.get("plugin",{}); pp=Path(plugin.get("path","")); pb=Path(plugin.get("binary_path",""))
    if plugin.get("filename")!="OLMSmoother2.plugin" or not pp.is_dir() or pb != pp/"Contents"/"MacOS"/"OLMSmoother2" or len(plugin.get("sha256",""))!=64 or not pb.is_file() or (pb.is_file() and plugin.get("sha256")!=digest(pb)): fail.append("loaded plugin bundle/binary identity or hash missing/mismatched")
    try:
        mac_process_proof_present=validate_mac_process_proof(out.resolve(strict=True),result_path,resolved_outputs,resolved_settings,pb.resolve(strict=True),nonce)
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f"[FAIL_CLOSED] macOS process proof invalid: {e}"); return 1
    reference=request["windows_reference"]; expected_input={"filename":reference["before_effects_frame"],"sha256":reference["before_effects_sha256"]}; expected_case={**request["cases"][0],"input":expected_input}
    expected_contract=canonical({"request_id":request["request_id"],"case":expected_case,"common_setup":request["common_setup"],"mac_run_contract":request["mac_run_contract"],"output_template":expected_output_template})
    if d.get("case_contract_sha256")!=expected_contract: fail.append("case/parameter contract hash missing or mismatched")
    if case.get("id")!=request["cases"][0]["id"] or case.get("input")!=expected_input or case.get("no_effect_control_passed") is not True: fail.append("case/input/control missing")
    expected_params=request["cases"][0]["params_full"]
    if case.get("params_full")!=expected_params: fail.append("full parameter binding drift")
    for p in case.get("params_full",[]):
        if p.get("match_name")=="OLM Smoother v2-0001" and p.get("value")!=0: fail.append("Enable Color Key is not exactly 0")
        if p.get("match_name")=="OLM Smoother v2-0006" and p.get("value")!=2: fail.append("Smoother Version is not exactly 2")
    outputs=case.get("outputs",{}); setting_contracts=[]
    for branch in ("no_effect_control","effect_on"):
        item=outputs.get(branch,{}); path=resolved_outputs[branch]
        if path.suffix.lower()!=".exr" or not path.is_file(): fail.append(f"missing {branch} FLOAT EXR"); continue
        if item.get("sha256")!=digest(path): fail.append(f"{branch} hash mismatch")
        try:
            info=inspect_float_rgba_exr(path,(1920,1080)); counts=info.get("sample_counts",{})
            if counts.get("nan",0) or counts.get("+inf",0) or counts.get("-inf",0): fail.append(f"{branch} contains non-finite samples")
        except (VerificationError,OSError,ValueError) as e: fail.append(f"{branch} is not uncompressed FLOAT RGBA EXR: {e}")
        settings=item.get("output_module_settings",{}); sp=resolved_settings[branch]
        if not sp.is_file() or len(settings.get("sha256",""))!=64 or (sp.is_file() and settings["sha256"]!=digest(sp)): fail.append(f"{branch} settings capture missing/hash mismatch")
        setting_contracts.append(canonical({k:v for k,v in settings.get("settings",{}).items() if k!="Output File Info"}))
        try:
            captured=json.loads(sp.read_text(encoding="utf-8"))
            if captured.get("kind")!="olm_output_module_settings_capture" or captured.get("run_nonce")!=nonce or captured.get("output_template")!=expected_output_template or captured.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or captured.get("output_path")!=str(path) or settings.get("output_path")!=str(path) or canonical(captured.get("settings"))!=canonical(settings.get("settings")): fail.append(f"{branch} settings capture semantics drift")
        except (OSError,json.JSONDecodeError): fail.append(f"{branch} settings capture is not valid JSON")
        if item.get("effect_enabled") is not (branch=="effect_on"): fail.append(f"{branch} enabled-state drift")
        if not valid_ae_readback(item.get("readback_before_render"),branch=="effect_on",expected_params) or not valid_ae_readback(item.get("readback_after_render"),branch=="effect_on",expected_params): fail.append(f"{branch} AE effect/parameter/enabled readback missing or forged")
    if len(setting_contracts)==2 and setting_contracts[0]!=setting_contracts[1]: fail.append("control/effect settings differ outside Output File Info")
    if fail: print("[FAIL_CLOSED] "+"; ".join(fail)); return 1
    ref=request["windows_preserve_rgb_reference"]; manifest=ROOT/ref["manifest"]; ref_root=ROOT/ref["artifact_root"]
    try: md=json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: print(f"[FAIL_CLOSED] Windows Preserve RGB manifest missing/invalid: {e}"); return 1
    source=ROOT/ref["source_input"]; win_control=ref_root/ref["no_effect_frame"]; win_effect=ref_root/ref["effect_frame"]; effect_aep=ROOT/ref["effect_aep_path"]; entry_path=ROOT/ref["pf32_input_entry_path"]
    for label,path,expected in (
        ("source",source,ref["source_input_sha256"]),
        ("no-effect",win_control,ref["no_effect_sha256"]),
        ("effect-on",win_effect,ref["effect_sha256"]),
        ("effect AEP",effect_aep,ref["effect_aep_sha256"]),
        ("PF32 entry",entry_path,ref["pf32_input_entry_stored_sha256"]),
    ):
        if not path.is_file() or digest(path)!=expected: print(f"[FAIL_CLOSED] Windows Preserve RGB {label} missing/hash mismatch"); return 1
    if md.get("kind")!="olmsmoother2_case07_windows_ae_preserve_rgb_reference" or md.get("ae_exact_claim") is not False or md.get("case_id")!=case["id"] or md.get("case_contract_sha256")!=d.get("case_contract_sha256"): print("[FAIL_CLOSED] Windows Preserve RGB manifest identity/contract drift"); return 1
    host=md.get("host",{})
    if host.get("ae_version")!="26.3x87" or host.get("renderer")!="SOFTWARE" or host.get("bits_per_channel")!=32 or host.get("working_space")!="None" or host.get("linear_blending") is not False or host.get("comp")!={"width":1920,"height":1080,"frame_rate":24,"frame":0}: print("[FAIL_CLOSED] Windows Preserve RGB host contract drift"); return 1
    binaries=md.get("binaries",{})
    if binaries.get("aex",{}).get("sha256")!="7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7" or binaries.get("aerender",{}).get("sha256")!="711859d183bdabec7c358a344208323bbbd665fffd7e88e42b9b234f9b99692a" or binaries.get("cdb",{}).get("sha256")!="b806eaea373d6add99fd9825a34820eb0779b9045cf71eecd7d070d58b8b6f6d": print("[FAIL_CLOSED] Windows binary identity drift"); return 1
    if md.get("source",{}).get("path")!=ref["source_input"] or md.get("source",{}).get("sha256")!=ref["source_input_sha256"] or md.get("source",{}).get("interpretation")!="Preserve RGB": print("[FAIL_CLOSED] Windows Preserve RGB source binding drift"); return 1
    project=md.get("project",{})
    if project.get("path")!=ref["effect_aep_path"] or project.get("sha256")!=ref["effect_aep_sha256"] or project.get("effect_enabled") is not True or project.get("full_parameter_binding") is not True: print("[FAIL_CLOSED] Windows Preserve RGB AEP binding drift"); return 1
    for support in md.get("support",{}).values():
        support_path=ROOT/support.get("path","")
        if not support_path.is_file() or support.get("sha256")!=digest(support_path): print("[FAIL_CLOSED] Windows PF32 support artifact missing/hash mismatch"); return 1
    output_module=md.get("output_module",{}); capture=ref["capture_contract"]
    if output_module.get("source")!="AEP-embedded settings" or output_module.get("aerender_omtemplate_override") is not False or output_module.get("profile_observed")!=capture["output_profile"] or capture.get("same_effect_render_entry_and_output") is not True or capture.get("raw_float32_epsilon")!=0: print("[FAIL_CLOSED] Windows Preserve RGB output-module contract drift"); return 1
    expected_header={"dimensions":[1920,1080],"physical_channel_order":["A","B","G","R"],"sample_types":[2,2,2,2],"compression":0,"finite_sample_count":8294400,"nonfinite_sample_count":0,"alpha_mode":"premultiplied","color_profile":"Preserve RGB"}
    artifacts=md.get("artifacts",{})
    for branch,path,expected in (("no_effect_control",win_control,ref["no_effect_sha256"]),("effect_on",win_effect,ref["effect_sha256"])):
        artifact=artifacts.get(branch,{})
        if artifact.get("path")!=path.name or artifact.get("sha256")!=expected or artifact.get("header_metadata")!=expected_header: print(f"[FAIL_CLOSED] Windows {branch} manifest attestation drift"); return 1
        try:
            inspected=inspect_float_rgba_exr(path,(1920,1080)); counts=inspected["sample_counts"]
            if inspected["channel_order"]!=["A","B","G","R"] or inspected["sample_types"]!=[2,2,2,2] or inspected["compression"]!=0 or counts.get("finite")!=8294400 or any(counts.get(k,0) for k in ("nan","+inf","-inf")): raise VerificationError("header/sample contract drift")
        except (VerificationError,OSError,ValueError) as e: print(f"[FAIL_CLOSED] Windows {branch} EXR contract failed: {e}"); return 1
    entry=md.get("pf32_input_entry",{})
    entry_attested=bool(
        entry.get("path")==ref["pf32_input_entry_path"] and
        entry.get("stored_sha256")==ref["pf32_input_entry_stored_sha256"] and
        entry.get("uncompressed_sha256")==ref["pf32_input_entry_uncompressed_sha256"] and
        entry.get("uncompressed_size")==33177600 and
        entry.get("same_run") is True and
        entry.get("same_run_effect_sha256")==ref["effect_sha256"] and
        entry.get("channel_order")==["A","R","G","B"] and
        entry.get("width")==1920 and entry.get("height")==1080 and entry.get("rowbytes")==30720
    )
    try: entry_comparison=compare_pf32_entry(entry_path,source)
    except (OSError,ValueError,VerificationError) as e: print(f"[FAIL_CLOSED] PF32 entry comparison failed: {e}"); return 1
    entry_attested=entry_attested and entry_comparison["raw"]["uncompressed_sha256"]==ref["pf32_input_entry_uncompressed_sha256"] and entry_comparison["mismatched_words"]==0 and entry_comparison["max_raw_u32_delta"]==0
    attested=entry_attested
    mac_control=resolved_outputs["no_effect_control"]; mac_effect=resolved_outputs["effect_on"]
    try:
        comparisons={"no_effect_control":compare(win_control,mac_control),"effect_on":compare(win_effect,mac_effect)}
    except (VerificationError,OSError,ValueError) as e: print(f"[FAIL_CLOSED] raw FLOAT32 comparison failed: {e}"); return 1
    control_exact=comparisons["no_effect_control"]["mismatched_values"]==0
    effect_exact=comparisons["effect_on"]["mismatched_values"]==0
    exact=attested and entry_attested and control_exact and effect_exact
    if not control_exact: status="blocked_no_effect_control_mismatch"
    elif not entry_attested: status="blocked_input_entry_identity"
    elif not attested: status="blocked_pending_windows_artifact_attestation"
    elif not effect_exact: status="candidate_return_verified_effect_mismatch"
    else: status="raw_float32_exact_artifact_only_missing_windows_process_proof"
    reasons=[]
    if not attested: reasons.append("Windows Preserve RGB manifest or same-run PF32 entry attestation is not admissible")
    if not entry_attested: reasons.append("Windows Preserve RGB effect run lacks an exact same-run PF32 input-entry witness")
    if not control_exact: reasons.append("Windows before-effects vs Mac no-effect raw FLOAT32 control mismatch blocks effect attribution")
    if control_exact and not effect_exact: reasons.append("no-effect control is exact but effect-on raw FLOAT32 words differ")
    if exact: reasons.append("both raw FLOAT32 gates and Windows artifact attestation pass")
    if not control_exact: next_gate="repair/aligned-capture the no-effect host/export path before attributing the effect output"
    elif not entry_attested: next_gate="repair the same-run Windows PF32 input-entry witness before attributing effect residuals"
    elif not effect_exact: next_gate="eliminate the attributable 32bpc effect-on raw FLOAT32 residual without changing the frozen 8bpc core"
    else: next_gate="capture exact same-run loaded-process/module proof on Windows; macOS proof alone and raw artifact equality are not AE exact"
    report={"kind":"olmsmoother2_no_key_32bpc_mac_validation_report","schema_version":2,"status":status,"ae_exact_claim":False,"raw_float32_exact_artifact_classification":exact,"case_count":1,"result_json":str(result_path),"mac_candidate_return_verified":True,"mac_process_proof_present":mac_process_proof_present,"windows_reference_manifest":str(manifest),"windows_artifact_manifest_checks_passed":attested,"windows_same_run_process_proof_present":False,"windows_pf32_input_entry_attestation_present":entry_attested,"windows_pf32_input_entry_comparison":entry_comparison,"raw_float32_comparisons":comparisons,"control_gate_passed":control_exact,"effect_gate_passed":effect_exact,"missing_exact_process_proof":["Windows same-run AfterFX process and loaded OLMSmoother2.aex module identity bound to both compared renders"],"reason":"; ".join(reasons+["macOS same-run process/module proof passes; AE exact remains forbidden without Windows same-run process/module proof"]),"next_gate":next_gate}
    target=out/"validation_report.json"; target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(f"[INTERMEDIATE] wrote {target}; AE exact remains unproven"); return 2 if exact else 1
if __name__=="__main__": raise SystemExit(main())
