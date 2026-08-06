#!/usr/bin/env python3
"""Verify the built test-only PF16 source through its exported EffectMain."""
from __future__ import annotations
import argparse, hashlib, json, struct, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PIXELS=((32768,32768,32768,32768),(32768,8192,24576,32768),(32768,0,0,0),(32768,32769,32768,32768),(32768,32768,32769,32768),(32768,32768,32768,32769),(32768,65535,65535,65535),(32769,32768,32768,32768),(65535,8192,24576,32768),(16384,65535,32769,49152),(1,32769,1,65535),(32768,12345,23456,34567))
def main():
 p=argparse.ArgumentParser();p.add_argument("bundle",type=Path);a=p.parse_args();binary=a.bundle/"Contents/MacOS/OLMPF16FixtureSource"
 code=r'''#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include "AE_Effect.h"
using Fn=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
int main(int n,char**v){void*h=dlopen(v[1],RTLD_NOW);if(!h)return 2;auto f=(Fn)dlsym(h,"EffectMain");if(!f)return 3;unsigned char raw[3*40];memset(raw,0xee,sizeof(raw));PF_LayerDef w{};w.data=reinterpret_cast<PF_PixelPtr>(raw);w.width=4;w.height=3;w.rowbytes=40;w.world_flags=PF_WorldFlag_DEEP;PF_OutData o{};if(f(PF_Cmd_GLOBAL_SETUP,nullptr,&o,nullptr,nullptr,nullptr)||!(o.out_flags&PF_OutFlag_DEEP_COLOR_AWARE))return 4;if(f(PF_Cmd_RENDER,nullptr,&o,nullptr,&w,nullptr))return 5;fwrite(raw,1,sizeof(raw),stdout);return 0;}'''
 with tempfile.TemporaryDirectory(prefix="ck_pf16_source_test_") as raw:
  d=Path(raw);src=d/"test.cpp";exe=d/"test";src.write_text(code)
  subprocess.run(["clang++","-std=c++17","-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),str(src),"-o",str(exe)],check=True)
  got=subprocess.run([str(exe),str(binary)],check=True,capture_output=True).stdout
 expected=b"".join(b"".join(struct.pack("<4H",*PIXELS[y*4+x]) for x in range(4))+b"\xee"*8 for y in range(3))
 if got!=expected: raise RuntimeError("exported PF16 payload mismatch")
 report={"status":"exported_effectmain_pf16_exact","binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),"bytes":len(got),"payload_sha256":hashlib.sha256(got).hexdigest(),"padding_exact":True};print(json.dumps(report,indent=2));return 0
if __name__=="__main__": raise SystemExit(main())
