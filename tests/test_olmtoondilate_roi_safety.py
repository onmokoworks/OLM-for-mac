from __future__ import annotations

import ast
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERIC = ROOT / "tests/test_olmtoondilate_generic_beta.py"


def test_roi_halo_and_rect_arithmetic_fail_closed() -> None:
    tree = ast.parse(GENERIC.read_text())
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == "STUB"
                          for target in node.targets))
    stub = ast.literal_eval(assignment.value)
    source = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
    prefix = stub.split("int main(){", 1)[0]
    main = r'''
int main(){
 A_long halo=-1;
 if(!ToonCheckedHalo(100.0,2,1,&halo)||halo!=200)return 1;
 if(!ToonCheckedHalo(0.01,1,2,&halo)||halo!=1)return 2;
 if(ToonCheckedHalo(std::numeric_limits<double>::quiet_NaN(),1,1,&halo))return 3;
 if(ToonCheckedHalo(std::numeric_limits<double>::infinity(),1,1,&halo))return 4;
 if(ToonCheckedHalo(-1.0,1,1,&halo))return 5;
 if(ToonCheckedHalo(1.0,0,1,&halo))return 6;
 if(ToonCheckedHalo(100.0,std::numeric_limits<A_long>::max(),1,&halo))return 7;

 uint8_t in_bytes[64]{},out_bytes[64]{};PF_InData data{};
 data.downsample_x={1,1};data.downsample_y={1,1};
 PF_EffectWorld in{in_bytes,4,1,1,0,
   {std::numeric_limits<A_long>::min(),0,std::numeric_limits<A_long>::min()+1,1}};
 PF_EffectWorld out{out_bytes,4,1,1,0,
   {std::numeric_limits<A_long>::max()-1,0,std::numeric_limits<A_long>::max(),1}};
 in.origin_x=std::numeric_limits<A_long>::min();
 out.origin_x=std::numeric_limits<A_long>::max();
 OLMToonDilateInfo info{1.0,1.0};size_t span=0;
 if(ValidateToonBetaAdmission<PF_Pixel8>(&data,&in,&out,info,&span)!=PF_Err_BAD_CALLBACK_PARAM)return 8;
 return 0;
}
'''
    compiler = shutil.which("clang++")
    assert compiler
    with tempfile.TemporaryDirectory(prefix="toondilate-roi-safety-") as raw:
        temp = Path(raw)
        (temp / "AEFX_SuiteHelper.h").write_text("#pragma once\n")
        probe = temp / "probe.cpp"
        exe = temp / "probe"
        probe.write_text(prefix.replace("SOURCE_PATH", str(source)) + main)
        built = subprocess.run(
            [compiler, "-std=c++17", "-O1", "-fsanitize=undefined,address",
             "-fno-omit-frame-pointer", "-I", str(temp), str(probe), "-o", str(exe)],
            cwd=ROOT, text=True, capture_output=True,
        )
        assert built.returncode == 0, built.stderr
        ran = subprocess.run(
            [str(exe)], cwd=ROOT, text=True, capture_output=True,
            env={"ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1",
                 "UBSAN_OPTIONS": "halt_on_error=1"},
        )
        assert ran.returncode == 0, f"returncode={ran.returncode}\n{ran.stdout}{ran.stderr}"
