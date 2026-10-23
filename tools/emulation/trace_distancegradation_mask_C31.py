#!/usr/bin/env python3
"""Pair PF16 Smart mask conversion with its original import-free OpenCV leaf."""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter, SOURCE
from core import sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant
from aex_loader import AexLoader
from cv_bridge import build_ipl, read_ipl
from windows_runtime import WindowsOpenCVRuntime
import numpy as np


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    deadline=time.monotonic()+600
    report={'schema':'olm.dg-C31-mask/1'}
    with tempfile.TemporaryDirectory(dir=args.scratch) as tmp:
        td=Path(tmp);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        source=SOURCE.read_text()
        anchor='// d_alpha: source ownership follows'
        assert source.count(anchor)==1
        source=source.replace(anchor, 'if(const char *mp=getenv("OLM_DG_C31_MASK")){FILE *f=fopen(mp,"wb");if(f){fwrite(mask.data(),1,mask.size(),f);fclose(f);}}\n\t'+anchor)
        a=variant(a,td/'candidate',deadline,source)
        ld=AexLoader(str(a.aex),verbose=False,fast=True)
        ld.register_libm_impls(max_threads=1)
        WindowsOpenCVRuntime(ld).install();ld.enable_crt_initializer_imports()
        constants={hex(addr):{'hex':ld.read_bytes(addr,8).hex(),'value':struct.unpack('<d',ld.read_bytes(addr,8))[0]} for addr in (0x181504a98,0x181504aa0,0x181504ab0)}
        report['constants']=constants
        scale=constants['0x181504a98']['value']
        c=a.generate(32,96);w,h=c['geometry']
        alpha=np.frombuffer(c['pixels'],dtype='<u2').reshape(h,w,4)[:,:,0].copy()
        def convert(alpha):
            ip=build_ipl(ld,alpha);op=build_ipl(ld,np.zeros(alpha.shape,dtype=np.uint8))
            ld.call_function(0x18117c580,[ip,op],float_args={2:(scale,'d'),3:(0.,'d')},max_instructions=200_000_000)
            return read_ipl(ld,op).tobytes()
        converted=convert(alpha);expected=bytes(int(v>1) for v in converted)
        a.env['OLM_DG_C31_MASK']=str(td/'mask.bin')
        status,raw,_=a.candidate(c,td,'smart',deadline)
        oracle,ref=a.oracle(c,td,deadline,'smart')
        actual=(td/'mask.bin').read_bytes()
        report['campaign']={'seed':32,'index':96,'geometry':[w,h],'input_sha256':sha(c['pixels']),
                            'oracle':oracle,'candidate':status,'output_diff':raw_diff(ref,raw,16),
                            'mask_diff':raw_diff(expected,actual,8),'original_mask_sha256':sha(expected),'mac_mask_sha256':sha(actual),
                            'mismatching_alpha_values':sorted(set(int(alpha.flat[i]) for i in range(w*h) if expected[i]!=actual[i]))}
        report['boundaries']=[]
        for width in (1,7,8,16,17):
            arr=np.array([(188+i%10) for i in range(width)],dtype='<u2').reshape(1,width)
            report['boundaries'].append({'width':width,'input':arr.tolist()[0],'converted':list(convert(arr))})
        report['imports']=sorted(set(x.name for x in ld.import_log))
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'constants':report['constants'],'campaign':report['campaign'],'boundaries':report['boundaries'],'imports':report['imports']},sort_keys=True))

if __name__=='__main__':main()
