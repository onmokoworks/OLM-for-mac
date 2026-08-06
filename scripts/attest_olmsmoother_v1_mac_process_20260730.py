#!/usr/bin/env python3
"""Independent two-phase process/output attestor for the v1 Mac validation."""
from __future__ import annotations
import argparse, contextlib, json, os, re, sys, time
from pathlib import Path
from attest_olmsmoother2_mac_process_20260728 import (
    AttestationError, _held_exact, _native_birth_token, atomic_write_json,
    canonical_sha256, file_sha256, snapshot_from_macos, strict_load_json,
    _command_text, _ps_rows, _run_read_only, _vmmap_paths,
)
HEX64=re.compile(r"[0-9a-f]{64}")
HARNESS_KEYS={
    "runner","reporter","request","manifest","input_template","smoke","boundary_probe",
    "port_source","strings_source","generated_jsx",
}
def object_(v:object,label:str)->dict:
    if not isinstance(v,dict): raise AttestationError(label+" must be object")
    return v
def wait(path:Path,deadline:float)->dict:
    while True:
        if path.is_symlink(): raise AttestationError(path.name+" symlink")
        if path.exists(): return object_(strict_load_json(path,path.name),path.name)
        if time.monotonic()>deadline: raise AttestationError("timeout "+path.name)
        time.sleep(.02)
def assert_absent_outputs(outputs:dict)->None:
    paths=[]; identities=set()
    for case,roles in outputs.items():
        if set(roles)!= {"no_effect_control","effect_on"}: raise AttestationError(case+" roles")
        for role,artifacts_value in roles.items():
            artifacts=object_(artifacts_value,case+"."+role)
            if set(artifacts)!={"exr","settings"}: raise AttestationError(case+"."+role+" artifact schema")
            for raw in artifacts.values():
                p=Path(raw)
                if not p.is_absolute() or p.exists() or p.is_symlink(): raise AttestationError("expected output not fresh")
                parent=p.parent.resolve(strict=True)
                if p.parent!=parent: raise AttestationError("output parent alias")
                stale=[entry.name for entry in parent.iterdir() if entry.name.startswith(p.name)]
                if stale: raise AttestationError(f"stale output sequence-prefix artifacts for {p.name}: {stale!r}")
                paths.append(p)
                st=os.stat(parent,follow_symlinks=False); identities.add((st.st_dev,st.st_ino,p.name))
    if len(paths)!=40 or len(set(paths))!=40 or len(identities)!=40: raise AttestationError("40 output path uniqueness")
def diagnostic_snapshot(expected:dict)->dict:
    try: return snapshot_from_macos(expected)
    except AttestationError as original:
        ae=expected["ae_executable"]["path"]; module=Path(expected["module"]["path"])
        rows=[(pid,cmd) for pid,cmd in _ps_rows(_command_text(_run_read_only,["/bin/ps","-axo","pid=,comm="])) if cmd==ae]
        observed=set()
        if len(rows)==1:
            for raw in _vmmap_paths(_command_text(_run_read_only,["/usr/bin/vmmap",str(rows[0][0])],timeout=120.0)):
                p=Path(raw)
                if p.name==module.name:
                    try: observed.add(str(p.resolve(strict=True)))
                    except OSError: observed.add(str(p))
        raise AttestationError(f"{original}; observed unique {module.name} paths/count={sorted(observed)!r}/{len(observed)}") from original
def warmup_project_matches(actual:object, contract:object)->bool:
    if not isinstance(actual,dict) or not isinstance(contract,dict): return False
    if actual.get("bits_per_channel")!=contract.get("bits_per_channel") or actual.get("renderer_raw")!=contract.get("renderer_raw") or contract.get("named_working_space_allowed") is not False: return False
    kind=actual.get("working_space_raw_type"); raw=actual.get("working_space_raw")
    for allowed in contract.get("working_space_raw_allowed",[]):
        if allowed.get("type")==kind and (allowed.get("value",allowed.get("serialized_value"))==raw):
            return True
    return False
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--challenge",type=Path,required=True); ap.add_argument("--attestor-nonce",required=True); ap.add_argument("--timeout",type=float,required=True); a=ap.parse_args()
    try:
        if not HEX64.fullmatch(a.attestor_nonce): raise AttestationError("attestor nonce")
        challenge_path=a.challenge.resolve(strict=True)
        if a.challenge.is_symlink() or a.challenge!=challenge_path: raise AttestationError("challenge canonical path")
        challenge=object_(strict_load_json(challenge_path,"challenge"),"challenge")
        required={"kind","schema_version","run_nonce","attestor_nonce","started_at","expected","attestor","harness","invocation","diagnostics","input_interpretation","inputs","warmup_contract","result_path","outputs"}
        if set(challenge)!=required or challenge["kind"]!="olmsmoother_v1_mac_process_challenge" or challenge["schema_version"]!=4 or challenge["attestor_nonce"]!=a.attestor_nonce or not HEX64.fullmatch(challenge["run_nonce"]): raise AttestationError("challenge schema/nonce")
        expected=object_(challenge["expected"],"expected")
        if set(expected)!={"ae_executable","module"}: raise AttestationError("expected identity schema")
        attestor_expected=object_(challenge["attestor"],"attestor")
        parent=challenge_path.parent; deadline=time.monotonic()+a.timeout
        harness=object_(challenge["harness"],"harness")
        if set(harness)!=HARNESS_KEYS: raise AttestationError("harness identity schema")
        for name,row_value in harness.items():
            row=object_(row_value,"harness."+name)
            if set(row)!={"path","sha256"}: raise AttestationError("harness."+name+" identity schema")
        invocation=object_(challenge["invocation"],"invocation")
        if invocation!={"platform":"macOS","method":"after_effects_file_scripts_run_script_file","manual_trigger_required":True,"generated_jsx":harness["generated_jsx"]}: raise AttestationError("invocation contract")
        diagnostics=object_(challenge["diagnostics"],"diagnostics")
        expected_diagnostics={
            "started_path":str(parent/"jsx_started.json"),
            "error_path":str(parent/"jsx_error.json"),
        }
        if diagnostics!=expected_diagnostics: raise AttestationError("diagnostic path schema")
        for raw in diagnostics.values():
            path=Path(raw)
            if not path.is_absolute() or path.parent!=parent or path.is_symlink():
                raise AttestationError("diagnostic path alias/symlink")
        interpretation=object_(challenge["input_interpretation"],"input_interpretation")
        interpretation_keys={"method","template_path","template_sha256","footage_item_name","comp_item_name","preserve_rgb","verification"}
        if set(interpretation)!=interpretation_keys or interpretation.get("method")!="hash_bound_aep_template_footage_replace" or interpretation.get("footage_item_name")!="OLM_COLOR_PROBE_INPUT" or interpretation.get("comp_item_name")!="OLM_COLOR_PROBE_COMP" or interpretation.get("preserve_rgb") is not True or interpretation.get("verification")!="all_ten_no_effect_controls_raw_float32_exact" or interpretation.get("template_path")!=harness["input_template"]["path"] or interpretation.get("template_sha256")!=harness["input_template"]["sha256"]: raise AttestationError("input interpretation contract")
        inputs=object_(challenge["inputs"],"inputs")
        outputs=object_(challenge["outputs"],"outputs")
        expected_case_ids={f"final_random10_olm_smoother_{n:02d}" for n in range(1,11)}
        if set(inputs)!=expected_case_ids or set(outputs)!=expected_case_ids: raise AttestationError("exact ten input/output case bindings required")
        for case,row_value in inputs.items():
            row=object_(row_value,"input."+case)
            if set(row)!={"path","sha256"} or not HEX64.fullmatch(row.get("sha256","")): raise AttestationError("input."+case+" identity schema")
        result_path=Path(challenge["result_path"])
        if not result_path.is_absolute() or result_path.parent!=parent or result_path.name!="mac_validation_return.json" or result_path.exists() or result_path.is_symlink(): raise AttestationError("fresh result path binding")
        paths={n:parent/(n+".json") for n in ("pre_request","pre_ok","post_request","post_ok","mac_process_attestation")}
        if any(p.exists() or p.is_symlink() for n,p in paths.items() if n!="pre_request"): raise AttestationError("preexisting protocol file")
        assert_absent_outputs(outputs)
        with contextlib.ExitStack() as held:
            held.enter_context(_held_exact(expected["ae_executable"]["path"],expected["ae_executable"]["sha256"],"AfterFX"))
            held.enter_context(_held_exact(expected["module"]["path"],expected["module"]["sha256"],"module"))
            held.enter_context(_held_exact(attestor_expected["script"]["path"],attestor_expected["script"]["sha256"],"attestor script"))
            held.enter_context(_held_exact(attestor_expected["executable"]["path"],attestor_expected["executable"]["sha256"],"attestor executable"))
            for name in sorted(HARNESS_KEYS):
                row=harness[name]
                held.enter_context(_held_exact(row["path"],row["sha256"],"harness."+name))
            input_identities=set()
            for case,row_value in sorted(inputs.items()):
                row=object_(row_value,"input."+case)
                if set(row)!={"path","sha256"}: raise AttestationError("input."+case+" identity schema")
                bound=held.enter_context(_held_exact(row["path"],row["sha256"],"input."+case))
                p,identity=bound
                key=identity[:2]
                if p in input_identities or key in input_identities: raise AttestationError("input path/inode alias")
                input_identities.update((p,key))
            pre=wait(paths["pre_request"],deadline)
            chash=canonical_sha256(challenge)
            if set(pre)!={"kind","schema_version","run_nonce","attestor_nonce","challenge_sha256","sequence","warmup"} or {k:pre[k] for k in pre if k!="warmup"}!={"kind":"olmsmoother_v1_pre_request","schema_version":1,"run_nonce":challenge["run_nonce"],"attestor_nonce":a.attestor_nonce,"challenge_sha256":chash,"sequence":1}: raise AttestationError("pre request replay/fabrication")
            warmup=object_(pre["warmup"],"warmup")
            contract=object_(challenge["warmup_contract"],"warmup_contract")
            observed=object_(warmup.get("effect"),"warmup.effect")
            if warmup.get("rendered") is not False or warmup.get("removed") is not True or warmup.get("case_id")!=contract.get("case_id") or observed.get("effect")!=contract.get("effect") or observed.get("params")!=contract.get("params") or not warmup_project_matches(observed.get("project"),contract.get("project")): raise AttestationError("warmup complete challenge contract")
            assert_absent_outputs(challenge["outputs"])
            snap_pre=diagnostic_snapshot(expected)
            pre_ok={"kind":"olmsmoother_v1_pre_ok","schema_version":1,"run_nonce":challenge["run_nonce"],"attestor_nonce":a.attestor_nonce,"challenge_sha256":chash,"pre_request_sha256":file_sha256(paths["pre_request"]),"pre_snapshot_sha256":canonical_sha256(snap_pre),"snapshot":snap_pre}
            atomic_write_json(paths["pre_ok"],pre_ok)
            post=wait(paths["post_request"],deadline)
            post_keys={"kind","schema_version","run_nonce","attestor_nonce","challenge_sha256","sequence","pre_request_sha256","pre_ok_sha256","artifacts"}
            if set(post)!=post_keys or post.get("kind")!="olmsmoother_v1_post_request" or post.get("schema_version")!=1 or post.get("run_nonce")!=challenge["run_nonce"] or post.get("attestor_nonce")!=a.attestor_nonce or post.get("challenge_sha256")!=chash or post.get("sequence")!=2 or post.get("pre_request_sha256")!=file_sha256(paths["pre_request"]) or post.get("pre_ok_sha256")!=file_sha256(paths["pre_ok"]): raise AttestationError("post request replay/fabrication")
            snap_post=diagnostic_snapshot(expected)
            if snap_pre!=snap_post: raise AttestationError("process/module interval changed")
            artifacts=object_(post.get("artifacts"),"artifacts"); verified={}; seen=set()
            if set(artifacts)!=set(challenge["outputs"]): raise AttestationError("artifact case set")
            for case,roles in challenge["outputs"].items():
                verified[case]={}
                for role,raw_value in roles.items():
                    raw_artifacts=object_(raw_value,case+"."+role)
                    declared_artifacts=object_(artifacts[case].get(role),case+"."+role+" declared")
                    if set(raw_artifacts)!={"exr","settings"} or set(declared_artifacts)!={"exr","settings"}: raise AttestationError(case+"."+role+" artifact schema")
                    verified[case][role]={}
                    for artifact_kind,raw in raw_artifacts.items():
                        declared=object_(declared_artifacts.get(artifact_kind),case+"."+role+"."+artifact_kind)
                        if set(declared)!={"path","sha256"} or declared.get("path")!=raw or not HEX64.fullmatch(declared.get("sha256","")): raise AttestationError(case+"."+role+"."+artifact_kind+" declared identity")
                        with _held_exact(raw,declared.get("sha256"),case+"."+role+"."+artifact_kind) as bound:
                            p,identity=bound
                            key=identity[:2]
                            if p in seen or key in seen: raise AttestationError("artifact path/inode alias")
                            seen.update((p,key)); verified[case][role][artifact_kind]={"path":str(p),"sha256":declared["sha256"]}
            proof={"kind":"olmsmoother_v1_mac_process_attestation","schema_version":3,"run_nonce":challenge["run_nonce"],"attestor_nonce":a.attestor_nonce,"attestor":{"pid":os.getpid(),"birth_token":_native_birth_token(os.getpid()),"script":attestor_expected["script"],"executable":attestor_expected["executable"]},"challenge_sha256":chash,"input_interpretation":interpretation,"inputs":inputs,"pre":{"request_sha256":canonical_sha256(pre),"snapshot":snap_pre,"snapshot_sha256":canonical_sha256(snap_pre)},"post":{"request_sha256":canonical_sha256(post),"snapshot":snap_post,"snapshot_sha256":canonical_sha256(snap_post)},"outputs":verified}
            atomic_write_json(paths["mac_process_attestation"],proof)
            post_ok={"kind":"olmsmoother_v1_post_ok","schema_version":1,"run_nonce":challenge["run_nonce"],"attestor_nonce":a.attestor_nonce,"challenge_sha256":chash,"post_request_sha256":file_sha256(paths["post_request"]),"attestation_sha256":file_sha256(paths["mac_process_attestation"])}
            atomic_write_json(paths["post_ok"],post_ok)
        return 0
    except (AttestationError,OSError,KeyError,json.JSONDecodeError) as e:
        print("[FAIL_CLOSED]",e); return 2
if __name__=="__main__": raise SystemExit(main())
