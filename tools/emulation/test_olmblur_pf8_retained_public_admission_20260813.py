#!/usr/bin/env python3
"""Real-SDK public closure for twelve exact-source PF8 retained cells."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"mac/OLMBlur/OLMBlur.cpp";PROBE=ROOT/"tools/emulation/probe_olmblur_pf8_retained_public_admission_20260813.cpp"
WORKER=ROOT/"core/olmblur_worker_orchestration.cpp";LEGACY=ROOT/"core/olmblur_worker8_legacy.cpp";SHA_HELPER=ROOT/"core/olm_sha256_rows.h"
OWNER=ROOT/"refs/conformance/olmblur_pf8_retained_exported_public_owner_20260813.json"
REPORT=ROOT/"refs/conformance/olmblur_pf8_retained_public_admission_20260813.json";DOC=ROOT/"refs/conformance/olmblur_pf8_retained_public_admission_20260813.md"
EXPECTED={"source":"22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7","probe":"ee0e21390b69d7a766717275b3b6ecd03cce49caae89fccf84f0d7d8b5674b46","worker":"2f896d3e7a838421bb69847f585151da320de1135015b29affa18e8de095caaf","legacy_worker":"537b416da3b3f8fca50a2bdf90ff01f8cdb7d8b7369a439e7bf5ce573cf943a4","sha_helper":"bfdcc9a2f4575aabab692b7b4ca1cf9ddb8188c7fbb1efdae30d197bf0f2d9e5","owner":"789d82aeac5f2385f43360fa7ebb7c27fda46aa0503097911f55a5a0c0f66193"}
CELLS=[
 {"id":"nonlegacy_12x12_repeat2","geometry":[12,12],"amount_f64":3.0,"smoothness_fixed":6553600,"repeat":2,"bias":1,"legacy":0,"active_source_sha256":"cd47374c1febd0b96676975e0ec02e97b62417a54f9d351995a8e356f4953c8c","active_output_sha256":"b76687e43911deaf3add6c025f955ae852d599b264e567f0c1c1201939ed823b"},
 {"id":"nonlegacy_18x18_repeat3","geometry":[18,18],"amount_f64":11.0,"smoothness_fixed":6553600,"repeat":3,"bias":2,"legacy":0,"active_source_sha256":"dda0693f106bc532ef9eb91b3f26c1b257009095e88e3f5e8a1f097a150857bf","active_output_sha256":"069f73793776c475293e72d219b2d43d58319ef68f56e3c79150a3adefcd876e"},
 {"id":"nonlegacy_24x24_repeat1","geometry":[24,24],"amount_f64":129.4,"smoothness_fixed":6553600,"repeat":1,"bias":1,"legacy":0,"active_source_sha256":"d0f15a0688bb1f46d516fd9eda08c670953fcf5dab1cad578e8aa14fe23e37bf","active_output_sha256":"9e1890b407be13fdd1cc546081555060eb741c21d817ef519f7f4321a576dc11"},
 {"id":"nonlegacy_24x24_repeat2","geometry":[24,24],"amount_f64":129.4,"smoothness_fixed":6553600,"repeat":2,"bias":2,"legacy":0,"active_source_sha256":"d0f15a0688bb1f46d516fd9eda08c670953fcf5dab1cad578e8aa14fe23e37bf","active_output_sha256":"2501da9f856ff5d8cc25dac1c12088f8d65eeee4ec5ef40bc58e4d8f3032cf62"},
 {"id":"legacy_12x12_repeat2","geometry":[12,12],"amount_f64":3.0,"smoothness_fixed":6553600,"repeat":2,"bias":1,"legacy":1,"active_source_sha256":"586835578947adf0b3f1a5a5e574398ca66df585766d3af9fd6381ae92225e4a","active_output_sha256":"2d8a58a1fc24f03a2082a2d20ec824ea63f1c7f0f658ea8f3506329e39cac9cd"},
 {"id":"legacy_18x18_repeat3","geometry":[18,18],"amount_f64":11.0,"smoothness_fixed":6553600,"repeat":3,"bias":2,"legacy":1,"active_source_sha256":"dac589013b502bab4b245ab77028a823782f09f5fba333c26f775536b389ba04","active_output_sha256":"286b898d8aa8742573965764088c4d1c7f2835e7214f30f1ffce9e6251ecddef"},
 {"id":"legacy_18x12_mixed_alpha","geometry":[18,12],"amount_f64":3.0,"smoothness_fixed":6553600,"repeat":2,"bias":2,"legacy":1,"active_source_sha256":"aa8120e34bbcffd2b5eab03b01c9df29a073d3d985a8b505612b9b553ca9aae0","active_output_sha256":"663cb730bdaa4cf552fa74e1e18120e74e0efccda17a11f3f29d29095ca94dba"},
 {"id":"legacy_6x6_boundary_repeat10","geometry":[6,6],"amount_f64":248.6,"smoothness_fixed":6553600,"repeat":10,"bias":1,"legacy":1,"active_source_sha256":"680c3cf7dffabc4d4527f3a3698bea01d3a7352786c47e2389891d8f3f19083e","active_output_sha256":"c72f434389bffe31e9164d8c23605657f33b2c421ece6f49b62074afa533a5d7"},
 {"id":"legacy_12x12_boundary_repeat10","geometry":[12,12],"amount_f64":248.6,"smoothness_fixed":6553600,"repeat":10,"bias":1,"legacy":1,"active_source_sha256":"e4dd7db49faf3373caa42916e7c8aad47d0fd5385c4a04f6293f12d13dddd29b","active_output_sha256":"d6dbac193bd935e97a3b944596c1e2439d70d70ea089750feed877873dd68d9a"},
 {"id":"legacy_16x16_repeat1","geometry":[16,16],"amount_f64":5.0,"smoothness_fixed":6553600,"repeat":1,"bias":1,"legacy":1,"active_source_sha256":"2506b82ef7f054d4c7eff5eb6916f98deb18bff118d81366944a4cdf49f51395","active_output_sha256":"2d14e67722a6b7cccb42c4a4429d3a216cfc2079977ec763127da684e3436c14"},
 {"id":"legacy_10x8_boundary_reverse","geometry":[10,8],"amount_f64":1.0,"smoothness_fixed":6553600,"repeat":2,"bias":2,"legacy":1,"active_source_sha256":"21f943c064c606a63f5fd11db556abf61bd8abb022c6e41b164fc8220b9df882","active_output_sha256":"16c35706fddef21394a8ed7f702dbbf6cfae3471edd256a015eaaac05cc3179c"},
]
CELLS.append({"id":"legacy_19x13_smooth43_75","geometry":[19,13],"amount_f64":9.0,"smoothness_fixed":2867200,"repeat":3,"bias":2,"legacy":1,"active_source_sha256":"81a9e964e8e74810d0cc4d4dbf5d3522cfc5f1513f6d50b306c3628ddfda39f3","active_output_sha256":"3b557809537eac30baa547dacba705071b1ad2293d90b73adcad1b8c4e3ec5ab"})
CLAIM="Exactly twelve retained PF8 source/tuple/geometry cells are raw exact from the Windows exported Smart owner through current Mac public SmartRender. The Smoothness43.75 cell reproduces the owner's signed integer-part materialization while retaining the full fixed value in its admission predicate. Twenty-four optional-checkin controls succeed and 744 bounded source/tuple/world/lifecycle controls fail closed without committing output."

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run()->str:
    paths={"source":SOURCE,"probe":PROBE,"worker":WORKER,"legacy_worker":LEGACY,"sha_helper":SHA_HELPER,"owner":OWNER}
    actual={k:sha(v) for k,v in paths.items()}
    if actual!=EXPECTED:raise RuntimeError(f"identity drift {actual}")
    with tempfile.TemporaryDirectory(prefix="olmblur-pf8-retained-") as td:
        exe=Path(td)/"probe";sources=[PROBE,ROOT/"mac/OLMBlur/OLMBlur_Strings.cpp",*[ROOT/"core"/n for n in ("olmblur_helper.cpp","olmblur_fullworker_helper.cpp","olmblur_worker16_nonlegacy.cpp","olmblur_worker16_legacy.cpp","olmblur_worker32_nonlegacy.cpp","olmblur_worker32_legacy.cpp","olmblur_worker8_legacy.cpp","olmblur_worker_orchestration.cpp")],resolve_asset(ROOT/"Util/AEGP_SuiteHandler.cpp"),resolve_asset(ROOT/"Util/MissingSuiteError.cpp")]
        cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1","-Wno-pragma-pack","-Wno-deprecated-declarations",*[x for d in ("Headers","Headers/SP","Util","Resources","core","mac/OLMBlur") for x in ("-I",str(ROOT/d))],*[str(x) for x in sources],"-framework","Cocoa","-o",str(exe)]
        subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True);r=subprocess.run([str(exe)],cwd=ROOT,text=True,capture_output=True)
        if r.returncode or r.stderr:raise RuntimeError(f"probe rc={r.returncode} {r.stdout} {r.stderr}")
        return r.stdout
def build(stdout:str)->dict[str,object]:
    lines=stdout.splitlines();pos=[x for x in lines if x.startswith("PF8 ") and " positive " in x];neg=[x for x in lines if x.startswith("PF8 ") and " positive " not in x]
    if len(pos)!=24 or len(neg)!=744 or lines[-1]!="pf8_retained_all_exact=1 positive=24 negative=744" or any("exact=0" in x for x in lines):raise RuntimeError("run shape")
    identities={k:{"path":p.relative_to(ROOT).as_posix(),"sha256":EXPECTED[k]} for k,p in {"source":SOURCE,"probe":PROBE,"worker":WORKER,"legacy_worker":LEGACY,"sha_helper":SHA_HELPER,"owner":OWNER}.items()}
    return {"schema":"olmblur.pf8-retained-public-admission/2","status":"PASS_12_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT_744_FAIL_CLOSED","identities":identities,"cells":CELLS,"shared_contract":{"depth":"PF8","padding_per_row":13,"pixel_format":"ARGB32","world_flags":0,"origin":[0,0],"downsample":[1,1]},"summary":{"cells":12,"positive_controls":24,"negative_controls":744,"integer_materialization_boundary":1,"all_exact":True},"run_sha256":hashlib.sha256(stdout.encode()).hexdigest(),"run_lines":lines,"claim_boundary":CLAIM,"claims_not_made":["arbitrary source or tuple","fractional internal-worker equality for Smoothness43.75","native AE","current installed binary","PF16 or PF32 expansion"]}
def validate(v:object)->None:
    if not isinstance(v,dict) or set(v)!={"schema","status","identities","cells","shared_contract","summary","run_sha256","run_lines","claim_boundary","claims_not_made"}:raise ValueError("top schema")
    if v["schema"]!="olmblur.pf8-retained-public-admission/2" or v["status"]!="PASS_12_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT_744_FAIL_CLOSED" or v["cells"]!=CELLS or v["claim_boundary"]!=CLAIM:raise ValueError("authority")
    if v["summary"]!={"cells":12,"positive_controls":24,"negative_controls":744,"integer_materialization_boundary":1,"all_exact":True}:raise ValueError("summary")
    if len(v["run_lines"])!=769 or hashlib.sha256(("\n".join(v["run_lines"])+"\n").encode()).hexdigest()!=v["run_sha256"]:raise ValueError("run")
    try:fresh=build("\n".join(v["run_lines"])+"\n")
    except (RuntimeError,KeyError,TypeError) as exc:raise ValueError("recanonicalization") from exc
    if v!=fresh:raise ValueError("recanonicalization")
def markdown(v:dict[str,object])->str:return f"# OLMBlur PF8 retained public admission\n\nStatus: **{v['status']}**\n\n{CLAIM}\n"
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");p.add_argument("--validate-only",action="store_true");a=p.parse_args();fresh=build(run());validate(fresh)
    if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");DOC.write_text(markdown(fresh));print(fresh["status"]);return 0
    saved=json.loads(REPORT.read_text());validate(saved)
    if saved!=fresh:raise RuntimeError("stored report differs from fresh")
    print(saved["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
