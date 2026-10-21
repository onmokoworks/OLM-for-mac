#!/usr/bin/env python3
"""Pair original exported Smart worker contexts with the real-SDK Mac route.

The original public-chain fixture supplies the ABI. Read-only hooks observe
worker entry; all original numeric instructions execute. Full output hashes
must bind to the separately cached public AEX worker before interpreting stages.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
import run
import triage_olmblur as triage
from adapters import olmblur
from core import sha, raw_diff
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as fixture
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_R9

WORKER = Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'
ENTRIES = {(8,0):0x180003710,(8,1):0x180007300,(16,0):0x180002280,
           (16,1):0x180005f20,(32,0):0x180004b80,(32,1):0x1800086d0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--indices', type=int, nargs='+', default=[29,31,33,115,141,157,210])
    p.add_argument('--source-revision')
    p.add_argument('--boundaries', action='store_true')
    args = p.parse_args(); args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C05-olmblur-smart')
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    original = olmblur.SOURCE
    source = (subprocess.check_output(['git','show',args.source_revision+':mac/OLMBlur/OLMBlur.cpp']).decode()
              if args.source_revision else original.read_text())
    uninstrumented_sha = sha(source.encode())
    anchor='           short bpc, const BlurParams *bp)\n{'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+r'''
    if (const char *path = getenv("OLM_BLUR_CONTEXT_C05")) {
        FILE *f = fopen(path,"wb");
        if (f) { const float v[2]={bp->blur_amount,bp->blur_smoothness};
            fwrite(v,sizeof(v),1,f); fclose(f); }
    }
''')
    gate='\tif (width <= 24 && height <= 24 && !integer_small) return "generic-small-fixture";'
    assert source.count(gate)==1
    source=source.replace(gate,'\t// C05 trace: bypass only the small-fixture admission.')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='trace_',dir=args.scratch) as td:
        work=Path(td); target=work/'variant/mac/OLMBlur';target.mkdir(parents=True)
        (work/'variant/core').symlink_to(ROOT/'core',target_is_directory=True)
        for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):
            shutil.copyfile(original.with_name(name),target/name)
        olmblur.SOURCE=target/'OLMBlur.cpp';olmblur.SOURCE.write_text(source)
        a=olmblur.Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=run.main_checkout(),worker=WORKER))
        a.binary=triage.build_binary(a,work)
        a.env['OLM_BLUR_CONTEXT_C05']=str(work/'context.bin')
        provenance={'source_sha256':uninstrumented_sha,'instrumented_source_sha256':sha(source.encode()),
                    'candidate_sha256':sha(a.binary.read_bytes()),'aex_sha256':sha(a.aex.read_bytes()),
                    'worker_sha256':sha(WORKER.read_bytes())}
        original_loader=fixture.AexLoader
        if args.boundaries:
            cases=[]
            for depth in (8,16,32):
                for legacy in (0,1):
                    for smooth in (1.,1.+1/65536,62.5,100.-1/65536,100.):
                        c=a.generate(args.seed,len(cases))
                        c.update(geometry=[1,1],depth=depth,parameters=a.defaults(1,1),
                                 pixels=struct.pack('<4B',255,0,127,255) if depth==8 else
                                        struct.pack('<4H',32768,0,16384,32768) if depth==16 else
                                        struct.pack('<4f',1.,0.,.5,1.))
                        for param in c['parameters']:param['value']={1:3.,2:smooth,3:2,4:2,5:legacy}[param['slot']]
                        cases.append((len(cases),c))
        else:cases=[(index,a.generate(args.seed,index)) for index in args.indices]
        for index,c in cases:
            params={p['slot']:p['value'] for p in c['parameters']}
            oracle,reference=a.oracle(c,work,time.monotonic()+60,'smart');assert oracle['status']=='ok',oracle
            (work/'input.bin').write_bytes(c['pixels']);(work/'expected.bin').write_bytes(reference)
            observed=[]
            class TracedLoader(original_loader):
                def __init__(self,*args,**kwargs):
                    super().__init__(*args,**kwargs)
                    def entry(uc,address,size,user):
                        ctx=uc.reg_read(UC_X86_REG_R9)
                        b=self.read_bytes(ctx+0x20,8)
                        observed.append({'entry':hex(address),'bits':b.hex(),'values':list(struct.unpack('<2f',b))})
                    address=ENTRIES[c['depth'],params[5]]
                    self.uc.hook_add(UC_HOOK_CODE,entry,begin=address,end=address)
            fixture.AexLoader=TracedLoader;fixture.AEX=a.aex;fixture.FIXTURE=work
            fixture.WIDTH,fixture.HEIGHT=c['geometry']
            row={'id':f'seed{args.seed}-{index}','depth':c['depth'],'legacy':params[5],
                 'amount':params[1],'smoothness':params[2],'repeat':params[3],'bias_direction':params[4],
                 'source':'input.bin','expected':'expected.bin','expected_sha256':sha(reference)}
            actual=fixture.run_row(row)
            assert len(observed)==1 and actual['active_sha256']==sha(reference)
            result,raw,guards=a.candidate(c,work,'smart',time.monotonic()+60)
            assert result['status']=='ok',result
            context=(work/'context.bin').read_bytes()
            rows.append({'seed':args.seed,'index':index,'case':{k:v for k,v in c.items() if k!='pixels'},
                         'input_sha256':sha(c['pixels']),'original_context':observed[0],
                         'mac_context':{'bits':context.hex(),'values':list(struct.unpack('<2f',context))},
                         'first_stage':'worker_context' if context.hex()!=observed[0]['bits'] else None,
                         'original_public_trace':actual,'candidate':result,'candidate_sha256':sha(raw),
                         'output_exact':reference==raw,'diff':None if reference==raw else raw_diff(reference,raw,c['depth'])})
        fixture.AexLoader=original_loader
    report={'schema':'olmblur-smart-context-C05/1','provenance':provenance,'rows':rows}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print([(r['index'],r['original_context']['values'],r['mac_context']['values'],r['output_exact']) for r in rows])


if __name__=='__main__':main()
