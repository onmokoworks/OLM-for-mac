#!/usr/bin/env python3
"""FUN_18000cee0 scan-boundary differential against original AEX instructions."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse, json, os, random, struct, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
SCRATCH=ROOT/'orchestra/state/C01-smoother2-smart/scanner'
from aex_loader import AexLoader


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-ref');p.add_argument('--label',default='scanner');p.add_argument('--expect-mismatch',action='store_true');args=p.parse_args()
    SCRATCH.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH))
    source=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
    body=source.read_text() if not args.source_ref else subprocess.check_output(['git','show',args.source_ref+':'+str(source.relative_to(ROOT))],text=True)
    (SCRATCH/'production_under_test.cpp').write_text(body)
    host=SCRATCH/'host.cpp'
    host.write_text('''#include "production_under_test.cpp"
int main() {
 unsigned char data[64];
 while(fread(data,1,64,stdin)==64) {
  GridDesc g{data,4,4,16};
  // Actual cardinal callers require x>0; avoid the original scanner's raw
  // x-1 reads outside that contract. Include y=0 passthrough and y=1 entry.
  for(int y=0;y<4;++y) for(int x=1;x<4;++x) {
   int in[2]={x,y},out[3]; scan_cee0(out,&g,in);
   fwrite(out,4,3,stdout);
  }
 }
}
''')
    binary=SCRATCH/'test'
    subprocess.run([_UCRT_CXX,'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-deprecated-declarations',
        '-fsanitize=address,undefined','-fno-sanitize-recover=all',
        '-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(source.parent),str(host),'-o',str(binary)],check=True)
    rng=random.Random(1901)
    planes=[bytes(rng.choice((0,255)) for _ in range(64)) for _ in range(128)]
    # Independent scan-stop configurations: A=0 stop, R/self stop, R/left
    # stop, and row-zero arrival with row-zero A either clear or set.
    for stop in range(4):
        for row0 in (0,255):
            data=bytearray(64)
            for y in range(1,4): data[y*16+4]=255
            data[4]=row0
            if stop==0:data[2*16+4]=0
            if stop==1:data[2*16+5]=255
            if stop==2:data[2*16+1]=255
            planes.append(bytes(data))
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    raw=subprocess.check_output([str(binary)],input=b''.join(planes),env=env)
    actual=list(struct.iter_unpack('<3i',raw)); assert len(actual)==len(planes)*12
    l=AexLoader(str(MAIN/'plugins_2025/OLMSmoother2.aex'),verbose=False,fast=False)
    cb=l.bump_alloc(64,align=16);desc=l.bump_alloc(24,align=16);coord=l.bump_alloc(8,align=8);out=l.bump_alloc(16,align=16)
    l.write_bytes(desc,struct.pack('<QiiQ',cb,4,4,16));rows=[];index=0
    for pattern,data in enumerate(planes):
        l.write_bytes(cb,data)
        for y in range(4):
            for x in range(1,4):
                l.write_bytes(coord,struct.pack('<ii',x,y))
                l.call_function(0x18000cee0,int_args=[out,desc,coord],max_instructions=10000)
                expected=struct.unpack('<3i',l.read_bytes(out,12))
                if actual[index]!=expected:rows.append({'pattern':pattern,'input_xy':[x,y],'aex':expected,'mac':actual[index],'classes_hex':data.hex()})
                index+=1
    report={'cases':index,'mismatches':len(rows),'sanitizer_errors':0,'rows':rows}
    (SCRATCH/(args.label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    assert bool(rows)==args.expect_mismatch
if __name__=='__main__':main()
