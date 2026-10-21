#!/usr/bin/env python3
"""Real-SDK hostless closure for KiraKira WorldSuite lifecycle handling."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_worldsuite_lifecycle_closure_20260814.json"
DOC = REPORT.with_suffix(".md")
SOURCE_SHA256 = "f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2"
ROWS_SHA256 = "069236889432e34fff098766662d308c8c915f0e3e526bb54f05d9110392d625"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


PROBE = r'''
#include "mac/OLMKiraKira/OLMKiraKira.cpp"
#include <cstdio>
#include <new>
enum Mode { OK, ACQ_ERR, ACQ_NULL, ACQ_PF, ACQ_OOM, ACQ_OTHER, GET_NULL,
  GET_ERR1, GET_ERR2, GET_PF, GET_OOM, GET_OTHER, REL_ERR, REL_PF, REL_OOM,
  REL_OTHER, PRIMARY_WINS };
static Mode mode=OK; static int acq_n=0,rel_n=0,get_n=0;
static PF_Err getfmt(const PF_EffectWorld*,PF_PixelFormat*f){
  ++get_n;
  if((mode==GET_ERR1&&get_n==1)||(mode==GET_ERR2&&get_n==2)||
     (mode==PRIMARY_WINS&&get_n==2)) return (PF_Err)92;
  if(mode==GET_PF&&get_n==2) throw (PF_Err)93;
  if(mode==GET_OOM&&get_n==2) throw std::bad_alloc();
  if(mode==GET_OTHER&&get_n==2) throw 7;
  *f=PF_PixelFormat_ARGB128; return PF_Err_NONE;
}
static PF_WorldSuite2 suite{nullptr,nullptr,getfmt};
static SPErr acq(const char*,int32,const void**p){
  ++acq_n; if(mode==ACQ_ERR)return 91; if(mode==ACQ_PF)throw (PF_Err)94;
  if(mode==ACQ_OOM)throw std::bad_alloc(); if(mode==ACQ_OTHER)throw 8;
  *p=mode==ACQ_NULL?nullptr:&suite; return kSPNoError;
}
static SPErr rel(const char*,int32){
  ++rel_n; if(mode==REL_ERR||mode==PRIMARY_WINS)return 95;
  if(mode==REL_PF)throw (PF_Err)96; if(mode==REL_OOM)throw std::bad_alloc();
  if(mode==REL_OTHER)throw 9; return kSPNoError;
}
static void run(const char*n,Mode m,bool no_pica=false,bool no_acq=false,bool no_rel=false){
  mode=m;acq_n=rel_n=get_n=0;suite.PF_GetPixelFormat=m==GET_NULL?nullptr:getfmt;
  SPBasicSuite b{acq,rel};if(no_acq)b.AcquireSuite=nullptr;if(no_rel)b.ReleaseSuite=nullptr;
  PF_InData in{};PF_OutData out{};in.pica_basicP=no_pica?nullptr:&b;
  PF_EffectWorld iw{},ow{};PF_PixelFormat a=PF_PixelFormat_INVALID,c=PF_PixelFormat_INVALID;
  PF_Err e=GetKiraPixelFormats(&in,&iw,&ow,&a,&c);
  std::printf("%s,%d,%d,%d,%d,%d,%d\n",n,(int)e,acq_n,rel_n,get_n,(int)a,(int)c);
}
int main(){
 run("success",OK);run("null_pica",OK,true);run("null_acquire",OK,false,true);
 run("null_release",OK,false,false,true);run("acquire_error",ACQ_ERR);
 run("acquire_success_null",ACQ_NULL);run("acquire_throw_pf",ACQ_PF);
 run("acquire_throw_oom",ACQ_OOM);run("acquire_throw_other",ACQ_OTHER);
 run("get_function_null",GET_NULL);run("get_error_1",GET_ERR1);run("get_error_2",GET_ERR2);
 run("get_throw_pf",GET_PF);run("get_throw_oom",GET_OOM);run("get_throw_other",GET_OTHER);
 run("release_error",REL_ERR);run("release_throw_pf",REL_PF);run("release_throw_oom",REL_OOM);
 run("release_throw_other",REL_OTHER);run("primary_error_wins",PRIMARY_WINS);
}
'''


def run_probe() -> list[dict]:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="kira-worldsuite-") as raw:
        td = Path(raw); cpp = td / "probe.cpp"; exe = td / "probe"
        cpp.write_text(PROBE)
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-ffp-contract=off",
               "-isysroot", sdk, "-I", str(ROOT), "-I", str(ROOT / "Headers"),
               "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
               "-I", str(ROOT / "Resources"), str(cpp),
               str(ROOT / "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"),
               str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
               "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if built.returncode: raise RuntimeError(built.stdout + built.stderr)
        ran = subprocess.run([str(exe)], check=True, text=True, capture_output=True)
    rows=[]
    for line in ran.stdout.splitlines():
        n,e,a,r,g,fi,fo=line.split(",")
        rows.append({"name":n,"err":int(e),"acquire":int(a),"release":int(r),
                     "get":int(g),"formats":[int(fi),int(fo)]})
    return rows


NAMES = ["success","null_pica","null_acquire","null_release","acquire_error",
         "acquire_success_null","acquire_throw_pf","acquire_throw_oom","acquire_throw_other",
         "get_function_null","get_error_1","get_error_2","get_throw_pf","get_throw_oom",
         "get_throw_other","release_error","release_throw_pf","release_throw_oom",
         "release_throw_other","primary_error_wins"]


def generate() -> dict:
    rows=run_probe()
    return {"schema":"olm.kirakira-worldsuite-lifecycle/1","status":"pass",
            "source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE.read_bytes())},
            "rows":rows,"rows_sha256":canonical(rows),
            "claims":{"real_sdk_source_included":True,"two_formats_then_release_once":True,
                      "success_null_and_function_null_fail_closed":True,
                      "returned_errors_and_throws_are_bounded":True,
                      "primary_error_precedes_release_error":True,
                      "numerical_admission_changed":False,"installed_binary":False,"native_ae":False}}


def validate(value: dict) -> None:
    assert set(value)=={"schema","status","source","rows","rows_sha256","claims"}
    assert value["schema"]=="olm.kirakira-worldsuite-lifecycle/1" and value["status"]=="pass"
    assert value["source"]=={"path":"mac/OLMKiraKira/OLMKiraKira.cpp","sha256":SOURCE_SHA256}
    assert sha(SOURCE.read_bytes())==SOURCE_SHA256
    assert [r["name"] for r in value["rows"]]==NAMES
    assert value["rows_sha256"]==canonical(value["rows"])
    if ROWS_SHA256 != "PENDING": assert value["rows_sha256"]==ROWS_SHA256
    by={r["name"]:r for r in value["rows"]}
    assert by["success"]["err"]==0 and by["success"]["acquire"]==1
    assert by["success"]["release"]==1 and by["success"]["get"]==2
    assert by["acquire_error"]["release"]==0
    assert by["acquire_success_null"]["release"]==1
    assert by["get_function_null"]["release"]==1
    assert by["get_error_1"]["get"]==1 and by["get_error_2"]["get"]==2
    assert by["primary_error_wins"]["err"]==by["get_error_2"]["err"]
    assert value["claims"]=={"real_sdk_source_included":True,"two_formats_then_release_once":True,
      "success_null_and_function_null_fail_closed":True,"returned_errors_and_throws_are_bounded":True,
      "primary_error_precedes_release_error":True,"numerical_admission_changed":False,
      "installed_binary":False,"native_ae":False}


def doc(value: dict) -> str:
    return ("# OLMKiraKira WorldSuite lifecycle closure\n\n"
            f"Status: `{value['status']}`\n\nSource: `{SOURCE_SHA256}`\n\n"
            f"Rows: `{value['rows_sha256']}` ({len(value['rows'])} controls)\n\n"
            "A real-SDK source-included probe closes explicit WorldSuite acquire/get/release, "
            "success-null, function-null, returned-error and exception paths without widening "
            "the existing 42-cell numerical admission. This is not installed or native-AE evidence.\n")


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--write",action="store_true");ap.add_argument("--fresh",action="store_true");a=ap.parse_args()
    value=generate() if a.write or a.fresh else json.loads(REPORT.read_text())
    validate(value)
    if a.write:
        REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n");DOC.write_text(doc(value))
    elif not a.fresh:
        assert DOC.read_text()==doc(value)
    print(json.dumps({"status":"pass","rows":len(value["rows"]),"rows_sha256":value["rows_sha256"]}))
    return 0


if __name__=="__main__": raise SystemExit(main())
