from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[1] / "tools/ucrt_cxx.py")

import ast
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERIC = ROOT / "tests/test_olmtoondilate_generic_beta.py"


def test_smart_geometry_bounds_and_ignored_origins() -> None:
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
 if(ValidateToonBetaAdmission<PF_Pixel8>(&data,&in,&out,info,&span)!=PF_Err_NONE)return 8;
 // Expanded allocation: only the input-sized plane is written. Odd stride
 // and bytes outside the active plane must remain untouched.
 uint8_t src[26]{}, dst[69]; std::memset(dst,0xa5,sizeof(dst));
 PF_EffectWorld small{src,13,3,2}, expanded{dst,23,5,3};
 PF_Pixel8 seed{255,11,33,55};WritePixel<PF_Pixel8>(&small,0,0,seed);
 OLMToonDilateInfo expanded_info{2.0,3.0};
 if(RenderTyped<PF_Pixel8>(&small,&expanded,expanded_info,true))return 9;
 for(int y=0;y<3;++y)for(int x=0;x<23;++x){
   if(y<2&&x<12){const uint8_t expected[]={255,11,33,55};
     if(dst[y*23+x]!=expected[x%4])return 10;
   }else if(dst[y*23+x]!=0xa5)return 11;
 }
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
            [_UCRT_CXX, "--compiler", compiler, "-std=c++17", "-O1", "-fsanitize=undefined,address",
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
