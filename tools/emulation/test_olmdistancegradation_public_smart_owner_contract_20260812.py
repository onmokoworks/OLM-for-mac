#!/usr/bin/env python3
"""Corrected actual-owner and bounded public Smart contract for DistanceGradation."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse, copy, hashlib, json, subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
AEX=resolve_asset(ROOT/"aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex")
SOURCE=ROOT/"mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
HARNESS=ROOT/"tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp"
SHIM=ROOT/"tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h"
FIELDGEN=ROOT/"core/olmdistancegradation_fieldgen.cpp"
AUDIT=ROOT/"tools/emulation/audit_olmdistancegradation_pf32_smartrender_boundary_20260805.py"
MATRIX=ROOT/"refs/conformance/olmdistancegradation_exported_typed_owner_matrix_20260811.json"
REPORT=ROOT/"refs/conformance/olmdistancegradation_public_smart_owner_contract_20260812.json"
DOC=REPORT.with_suffix(".md")
WORKER=Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker")
AEXCOMPAT=WORKER.parents[3]
X64_IMPORTS=AEXCOMPAT/"guest/crates/aex-guest-worker/src/x64/imports.rs"
BUILD_REV="94210e518ffef47866f017c723b52a7d0914bae8"
CHECKOUT_HEAD="28d535469f84f67236ef3425afe4291ea2fb0991"
PRE_SHA="6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c"
POST_SHA="7aaab7918d72d64fc2c426c7a52748409294bcab8c473bb5a55cbd4d19e037a6"
OUTPUT_SHA="50934ac830542ca73fee4a11b924b746a0ae93f97f34b0d2868170bc371dd387"
AEX_SHA="a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
ASM_SHA="b830129adaf05dc2e32a357902b0a60d6cf8f0429340f8cbf869b8287507229c"
ASM=resolve_asset(ROOT/"disasm/DistanceGradation.aex.asm.txt")

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def require(cond,msg):
    if not cond: raise AssertionError(msg)

def validate_report(report:dict)->None:
    require(report.get("schema")=="olmdistancegradation.public-smart-owner-contract/1","schema")
    require(report.get("status")=="PASS_ACTUAL_PUBLIC_PF32_SMART_OWNER_BOUNDED_56_RAW_EXACT_8_POWER_FAIL_CLOSED","status")
    for key,path in (("aex_sha256",AEX),("worker_sha256",WORKER),("production_source_sha256",SOURCE),
                     ("harness_sha256",HARNESS),("shim_sha256",SHIM),("static_audit_sha256",AUDIT),
                     ("matrix_report_sha256",MATRIX),("aexcompat_x64_imports_sha256",X64_IMPORTS)):
        require(report.get(key)==sha(path),key)
    require(report["aex_sha256"]==AEX_SHA,"known AEX identity")
    require(report.get("disassembly_sha256")==ASM_SHA==sha(ASM),"known disassembly identity")
    require(report["actual_public_owner"]["selector"]=="PF_Cmd_SMART_RENDER (0x18)","selector")
    require(report["actual_public_owner"]["chain"]==["entryPointFunc","FUN_181173d20","bitdepth 0x20","FUN_181172a10","PF iterateFloat Suite v1","FUN_181170c90"],"chain")
    require(report.get("aexcompat_checkout_head")==CHECKOUT_HEAD,"checkout head")
    require(report.get("worker_build_revision")==BUILD_REV,"worker build revision")
    trace=report["natural_public_trace"]
    require(trace["input_png_sha256"]=="683259bea613463bb22679f36a78e6d7b4c26dabdbc90e4da480cf76e9eb626a","input")
    require(trace["pre_field_sha256"]==PRE_SHA and trace["post_ipp_field_sha256"]==POST_SHA,"fields")
    require(trace["output_sha256"]==OUTPUT_SHA and trace["render_error"]==0 and trace["guards_intact"],"output")
    require(trace["watch"]=="rva=0x12c97d3 rcx/rdx deref=16 size=748","watch")
    require(trace["selectors"]==["SEQUENCE_SETUP","FRAME_SETUP","FRAME_SETDOWN","SMART_PRE_RENDER","SMART_RENDER","SEQUENCE_SETDOWN"],"public selectors")
    matrix=report["bounded_matrix"]
    require(matrix=={"actual_cells":64,"exact_admitted":56,"pf16_exact":32,"pf32_exact":24,
                    "pf32_power_fail_closed":8,"pf32_mode5_exact":6,"pf32_mode5_fail_closed":2},"matrix")
    public=report["production_public_contract"]
    require(public["positive_depths"]==[8,16,32] and public["negative_cases"]==21,"public cases")
    require(public["pf32_mode5_positive_cases"]==6 and public["pf32_power_fail_closed_cases"]==8,"public cases")
    require(public["parameter_checkouts"]==12 and public["parameter_checkins"]==12,"param lifecycle")
    require(public["layer_checkouts"]==1 and public["layer_checkins"]==1,"layer lifecycle")
    require(public.get("exception_cleanup") is True,"exception cleanup")
    require(public.get("full_extent_and_zero_origin") is True,"layout boundary")
    require(public.get("canonical_alpha_bits") is True,"canonical alpha bits")
    require(public.get("color_suite_error_propagation") is True,"color suite error")
    require(public["classic_guard_cases"]==4 and public["input_immutable"] is True and
            public["padding_preserved"] is True and public["format_matches_declared_depth"] is True,"public guarantees")
    boundary=report["power_oracle_boundary"]
    require(boundary=={
        "aex_import_module":"api-ms-win-crt-math-l1-1-0.dll",
        "aex_import_symbol":"powf",
        "aex_pf32_callsite":"0x181170ea3",
        "aexcompat_substitution":"LegacyWin64Import::PowF -> install_float_binary_import(..., f32::powf)",
        "native_windows_ucrt_capture_available":False,
        "production_policy":"PF32 Power fail-closed on both arm64 and x86_64",
    },"Power oracle boundary")
    require(report["not_promoted"]==["unlisted PF32 Smart tuple or geometry","partial-world/origin layouts","native After Effects pixels","CLI Mode 4/5 as an oracle"],"boundary")

def natural_trace(td:Path)->dict:
    image=Image.new("RGBA",(17,11));image.putdata([((x*613+y*1231)%256,(x*997+y*211)%256,(x*1499+y*307)%256,255) if not (4<=x<13 and 2<=y<9) else (0,0,0,0) for y in range(11) for x in range(17)])
    source=td/"input.png";output=td/"output.png";image.save(source)
    params=["Invert=1","In/Out=1","Inside Threshold=4","Outside Threshold=4","Render Mode=1","Use Background Color=0","Gradation Color=255,28,0,238","BG Color =255,16,160,48","Interpolation Mode=2","Power=2.25","Blur Mode=5","Blur Size=1"]
    cmd=[str(WORKER),"render-trace-png",str(AEX),str(source),str(output),"--pixel-format","argb32f",
         "--watch","rva=0x12c97d3,arg=rcx,deref=16,size=748","--watch","rva=0x12c97d3,arg=rdx,deref=16,size=748",*params]
    run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=30);require(run.returncode==0,run.stderr)
    trace=json.loads(run.stdout);smart=next(t for t in trace["execution_traces"] if t["selector"]=="SMART_RENDER")
    require(len(smart["memory_witnesses"])==2,"witness count")
    src,dst=smart["memory_witnesses"]
    require(src["before"]["sha256"]==src["after"]["sha256"]==PRE_SHA,"source plane")
    require(dst["before"]["sha256"]==PRE_SHA and dst["after"]["sha256"]==POST_SHA,"destination plane")
    require(trace["raw_pixel_sha256"]==OUTPUT_SHA,"trace output")
    return {"input_png_sha256":sha(source),"output_sha256":trace["raw_pixel_sha256"],"pre_field_sha256":PRE_SHA,
            "post_ipp_field_sha256":POST_SHA,"render_error":trace["render_error"],"guards_intact":trace["guards_intact"],
            "watch":"rva=0x12c97d3 rcx/rdx deref=16 size=748","selectors":[t["selector"] for t in trace["execution_traces"]]}

def generate()->dict:
    require(sha(AEX)==AEX_SHA and sha(ASM)==ASM_SHA,"known owner artifacts")
    matrix=json.loads(MATRIX.read_text());require(matrix["status"]=="PASS_56_ADMITTED_RAW_EXACT_8_PF32_POWER_FAIL_CLOSED","matrix status")
    require(matrix["actual_aex_sha256"]==AEX_SHA and matrix["worker_sha256"]==sha(WORKER),"matrix identities")
    require(matrix["summary"]=={"actual_aex_cells":64,"exact_admitted":56,"pf16_exact":32,"pf32_exact":24,
            "pf32_power_fail_closed":8,"pf32_mode5_exact":6,"pf32_mode5_fail_closed":2},"matrix summary")
    require(len(matrix["rows"])==64 and sum(bool(row.get("exact")) for row in matrix["rows"])==56 and
            sum(bool(row.get("fail_closed")) for row in matrix["rows"])==8,"matrix row recount")
    with tempfile.TemporaryDirectory(prefix="dg_public_owner_contract_") as raw:
        td=Path(raw);exe=td/"harness"
        build=subprocess.run(["clang++","-std=c++17","-O0","-I",str(ROOT/"tools/emulation/dg_renderbits_real_harness_20260716"),str(HARNESS),str(FIELDGEN),"-o",str(exe)],cwd=ROOT,text=True,capture_output=True)
        require(build.returncode==0,build.stderr);run=subprocess.run([str(exe)],text=True,capture_output=True);require(run.returncode==0,run.stderr);require("positive=9 mode5_positive=6 power_fail_closed=8 negative=21 classic_guards=4" in run.stdout,"harness marker")
        trace=natural_trace(td)
    static=json.loads(subprocess.run(["python3",str(AUDIT)],cwd=ROOT,text=True,capture_output=True,check=True).stdout)
    require(static["status"]=="PASS_ACTUAL_PUBLIC_PF32_SMART_OWNER_STATIC_AND_BOUNDED_PRODUCTION","static")
    require(static["aex_sha256"]==AEX_SHA and static["disassembly_sha256"]==ASM_SHA and
            static["production_source_sha256"]==sha(SOURCE) and all(static["facts"].values()),"static identities")
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=AEXCOMPAT,text=True,capture_output=True,check=True).stdout.strip()
    require(head==CHECKOUT_HEAD,"checkout head drift")
    require(subprocess.run(["git","merge-base","--is-ancestor",BUILD_REV,head],cwd=AEXCOMPAT).returncode==0,"build rev lineage")
    require(b"aex-guest-worker/0.1.0 rev=94210e518ffe" in WORKER.read_bytes(),"worker embedded build revision")
    imports_source=X64_IMPORTS.read_text()
    require('"powf" => LegacyWin64Import::PowF' in imports_source and
            'install_float_binary_import(unicorn, stub, "powf", f32::powf)' in imports_source,"AEXCompat powf substitution")
    pe=subprocess.run(["objdump","-p",str(AEX)],text=True,capture_output=True,check=True).stdout
    require("DLL Name: api-ms-win-crt-math-l1-1-0.dll" in pe and "powf" in pe,"AEX UCRT import")
    report={"schema":"olmdistancegradation.public-smart-owner-contract/1","status":"PASS_ACTUAL_PUBLIC_PF32_SMART_OWNER_BOUNDED_56_RAW_EXACT_8_POWER_FAIL_CLOSED",
      "aex_sha256":sha(AEX),"worker_sha256":sha(WORKER),"aexcompat_checkout_head":head,"worker_build_revision":BUILD_REV,
      "disassembly_sha256":sha(ASM),
      "production_source_sha256":sha(SOURCE),"harness_sha256":sha(HARNESS),"shim_sha256":sha(SHIM),"static_audit_sha256":sha(AUDIT),"matrix_report_sha256":sha(MATRIX),"aexcompat_x64_imports_sha256":sha(X64_IMPORTS),
      "actual_public_owner":{"selector":"PF_Cmd_SMART_RENDER (0x18)","chain":["entryPointFunc","FUN_181173d20","bitdepth 0x20","FUN_181172a10","PF iterateFloat Suite v1","FUN_181170c90"]},
      "natural_public_trace":trace,"bounded_matrix":{"actual_cells":64,"exact_admitted":56,"pf16_exact":32,"pf32_exact":24,"pf32_power_fail_closed":8,"pf32_mode5_exact":6,"pf32_mode5_fail_closed":2},
      "production_public_contract":{"positive_depths":[8,16,32],"pf32_mode5_positive_cases":6,"pf32_power_fail_closed_cases":8,"negative_cases":21,"classic_guard_cases":4,"parameter_checkouts":12,"parameter_checkins":12,"layer_checkouts":1,"layer_checkins":1,"input_immutable":True,"padding_preserved":True,"format_matches_declared_depth":True,"exception_cleanup":True,"full_extent_and_zero_origin":True,"canonical_alpha_bits":True,"color_suite_error_propagation":True},
      "power_oracle_boundary":{"aex_import_module":"api-ms-win-crt-math-l1-1-0.dll","aex_import_symbol":"powf","aex_pf32_callsite":"0x181170ea3","aexcompat_substitution":"LegacyWin64Import::PowF -> install_float_binary_import(..., f32::powf)","native_windows_ucrt_capture_available":False,"production_policy":"PF32 Power fail-closed on both arm64 and x86_64"},
      "not_promoted":["unlisted PF32 Smart tuple or geometry","partial-world/origin layouts","native After Effects pixels","CLI Mode 4/5 as an oracle"]}
    validate_report(report);return report

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--validate-only",action="store_true");args=parser.parse_args()
    if args.validate_only:validate_report(json.loads(REPORT.read_text()))
    else:
        report=generate();REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        DOC.write_text("# OLMDistanceGradation public Smart owner contract\n\nStatus: **"+report["status"]+"**.\n\nThe corrected actual-AEX public chain is command 0x18 → `FUN_181173d20` → PF32 `FUN_181172a10` → iterateFloat/`FUN_181170c90`. Production admits 56 fixed 17×11 cells: PF16 32 and non-Power PF32 24. The eight PF32 Power cells fail closed on both architectures because the AEX imports Windows UCRT `powf` while AEXCompat substitutes host `f32::powf`; no native Windows UCRT result is retained. Public EffectMain tests cover six admitted PF32 Mode 5 positives, eight Power rejects with input/output/padding unchanged, balanced world/parameter lifecycle including exception cleanup, suite-error propagation, format and layout guards, twenty-one other negative cases, and four classic guards. Unlisted tuples, partial worlds, native AE pixels, and the CLI Mode 4/5 path remain unpromoted.\n")
    print("PASS_OLMDISTANCEGRADATION_PUBLIC_SMART_OWNER_CONTRACT_20260812");return 0
if __name__=="__main__":raise SystemExit(main())
