#!/usr/bin/env python3
"""Bitwise original palette-worker boundary, including unordered comparisons."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse, itertools, json, os, struct, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
from aex_loader import AexLoader
from test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 import SmallStatic, desc

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scratch',type=Path,default=ROOT/'orchestra/state/C23-smoother2-colorkeep-toondilate-fresh/palette')
    parser.add_argument('--report',type=Path,default=ROOT/'orchestra/reports/C23-palette-boundary.json')
    args=parser.parse_args(); s=args.scratch.resolve(); s.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    source=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
    host=s/'host.cpp'
    host.write_text('#include "'+str(source)+'"\n'+r'''
int main() {
 unsigned r,g,b,a; PF_PixelFloat palette{};
 while (scanf("%x %x %x %x",&r,&g,&b,&a)==4) {
   FPix p; unsigned words[4]={r,g,b,a}; memcpy(&p,words,16);
   win_FUN_180002930_palette_filter(&p,1,1,&palette,1);
   memcpy(words,&p,16);
   printf("%08x %08x %08x %08x\n",words[0],words[1],words[2],words[3]);
 }
}
''')
    # +/- threshold and adjacent FLOAT32 values, signed zeros, infinities,
    # and quiet/signaling NaNs of both signs. Cross all three RGB channels.
    values=[0,0x80000000,0x3b008080,0x3b008081,0x3b008082,
            0xbb008080,0xbb008081,0xbb008082,0x7f800000,0xff800000,
            0x7fc12345,0xffc12345,0x7f812346,0xff812346]
    words=[(*rgb,0x3f000000) for rgb in itertools.product(values,repeat=3)]
    data=''.join(' '.join(f'{v:x}' for v in p)+'\n' for p in words)
    l=AexLoader(str(MAIN/'plugins_2025/OLMSmoother2.aex'),verbose=False,fast=False)
    l.register_libm_impls(max_threads=1)
    def alloc(data):
        p=l.bump_alloc(max(16,len(data)),align=16); l.write_bytes(p,bytes(data)); return p
    raw=b''.join(struct.pack('<4I',*p) for p in words)
    buf=alloc(raw); descriptor=desc(l,buf,len(raw),len(words),1)
    cfg=bytearray(0x80); struct.pack_into('<QQ',cfg,0x60,1,alloc(b'\0'*16))
    ptrs=[alloc(struct.pack('<i',v)) for v in (len(words),0,1,0)]
    SmallStatic(l,1)
    l.call_function(0x180002930,int_args=[*ptrs,descriptor,alloc(cfg)],max_instructions=10_000_000)
    expected=l.read_bytes(buf,len(raw)); results={}
    for name,flags in [('optimized',[]),('sanitized',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
        binary=s/name
        subprocess.run([_UCRT_CXX,'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-deprecated-declarations',*flags,'-I',str(ROOT/'cli/OLMSmoother2/shim'),str(host),'-o',str(binary)],check=True)
        result=subprocess.run([str(binary)],input=data,text=True,capture_output=True,check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
        assert not result.stderr,result.stderr
        observed=b''.join(struct.pack('<4I',*(int(v,16) for v in line.split())) for line in result.stdout.splitlines())
        mismatch=[i for i in range(len(words)) if observed[i*16:i*16+16]!=expected[i*16:i*16+16]]
        results[name]={'cases':len(words),'mismatches':len(mismatch),'first_case':mismatch[0] if mismatch else None}
        assert observed==expected,results[name]
    import hashlib
    report={'scope':'original FUN_180002930 versus production helper; key RGB zero; not native AE',
            'values':[f'{v:08x}' for v in values],'results':results,
            'aex_sha256':hashlib.sha256((MAIN/'plugins_2025/OLMSmoother2.aex').read_bytes()).hexdigest(),
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'oracle_output_sha256':hashlib.sha256(expected).hexdigest()}
    args.report.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(results))
if __name__=='__main__':main()
