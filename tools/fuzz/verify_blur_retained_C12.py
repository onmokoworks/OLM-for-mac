#!/usr/bin/env python3
"""Replay all retained typed Smart positive cells on the current source, sanitized.

Reuses the original hash-pinned public fixture hosts, retaining their source,
output, padding, callback and guard assertions. Omits obsolete negative source-
mutation refusals, which deliberately conflict with arbitrary-source admission.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.dont_write_bytecode=True
import run
from adapters import olmblur
from core import command,sha
WORKER=Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'


def verify(s):
    class Sanitized(olmblur.Adapter):
        def compile(self,argv,deadline):
            if argv[0]=='clang++':argv=[argv[0],'-fsanitize=address,undefined','-fno-sanitize-recover=all',*argv[1:]]
            return super().compile(argv,deadline)
    a=Sanitized(argparse.Namespace(max_size=256,case_timeout=30,main=run.main_checkout(),worker=WORKER))
    a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    names=['probe_olmblur_smart_public_admission_20260813.cpp','probe_olmblur_pf16_7x5_public_admission_20260813.cpp','probe_olmblur_pf16_worker_sources_public_admission_20260813.cpp','probe_olmblur_pf8_retained_public_admission_20260813.cpp','probe_olmblur_pf32_retained_public_admission_20260813.cpp']
    with tempfile.TemporaryDirectory(prefix='retained_',dir=s) as td:
        w=Path(td)
        for name in names:
            text=(run.ROOT/'tools/emulation'/name).read_text().replace('../../mac/',str(run.ROOT/'mac')+'/').replace('../../core/',str(run.ROOT/'core')+'/')
            if name==names[-1]:
                text=text.rsplit('int main(){',1)[0]+'''int main(){
 g_world_suite.PF_GetPixelFormat=get_format;bool ok=true;
 const SmallSpec positive={"positive",S_OK,NORMAL,0,PF_Err_NONE};
 for(const auto& c:kWorkerCells){ok&=run_worker_cell(c,positive,true);ok&=run_worker_cell(c,positive,false);}
 for(const auto& c:kPF8Cells){ok&=run_pf8_cell(c,positive,true);ok&=run_pf8_cell(c,positive,false);}
 for(const auto& c:kPF32Exact){ok&=run32(c,OK32,true);ok&=run32(c,OK32,false);}
 return ok?0:4;
}
'''
            (w/name).write_text(text)
        binary=a.compile_sdk(w,(w/names[-1]).read_text(),olmblur.SOURCE,time.monotonic()+120,olmblur.CORES)
        status,out,err=command([binary],timeout=120,deadline=time.monotonic()+120,env=a.env)
        report={'source_sha256':sha(olmblur.SOURCE.read_bytes()),'core_sha256':{f.name:sha(f.read_bytes()) for f in olmblur.CORES},'candidate_sha256':sha(binary.read_bytes()),'host_sha256':{n:sha((run.ROOT/'tools/emulation'/n).read_bytes()) for n in names},'status':status,'lines':out.decode().splitlines(),'stderr':err.decode()}
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    s=args.scratch.resolve();assert s.is_relative_to(run.ROOT/'orchestra/state/C12-olmblur-smart-r3')
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    r=verify(s);args.report.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    bad=[x for x in r['lines'] if 'exact=1' not in x]
    print('retained positives',len(r['lines']),'status',r['status'],'bad',bad)
    assert r['status']['status']=='ok' and not r['stderr'] and not bad

if __name__=='__main__':main()
