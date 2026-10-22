#!/usr/bin/env python3
"""Read-only public AEX/helper boundary trace paired with instrumented Mac helpers.

Uses the retained public ABI fixture. Native host libm imports match the cached
worker, with complete output binding required before interpreting stages.
No AEX instructions are patched and no numerical implementation is changed.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
import run
import triage_olmblur as triage
from adapters import olmblur
from core import sha,raw_diff
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as fixture
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R9,UC_X86_REG_RSP
WORKER=Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'


def decode(data):
    rows=[];at=0
    while at<len(data):
        direction,w,h,passes,offset,radius=struct.unpack_from('<6Q',data,at);at+=48
        n=w*h
        fields={}
        for key,length in [('flags',n),('weights',(radius+1)*4),('plane',n*12)]:
            fields[key]=data[at:at+length];at+=length
        rows.append(dict(direction=direction,width=w,height=h,passes=passes,offset=offset,radius=radius,**fields))
    assert at==len(data)
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source-revision')
    p.add_argument('--matrix-depth',type=int,choices=(8,16,32))
    p.add_argument('--seed',type=int,default=1);p.add_argument('--indices',type=int,nargs='+',default=[19,13,66,196])
    args=p.parse_args();s=args.scratch.resolve();assert s.is_relative_to(ROOT/'orchestra/state/C12-olmblur-smart-r3')
    s.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    a=olmblur.Adapter(argparse.Namespace(max_size=256,case_timeout=60,main=run.main_checkout(),worker=WORKER))
    libm=ctypes.CDLL('/usr/lib/libSystem.B.dylib')
    for name,argspec,result in [('powf',[ctypes.c_float]*2,ctypes.c_float),('pow',[ctypes.c_double]*2,ctypes.c_double),('expf',[ctypes.c_float],ctypes.c_float)]:
        f=getattr(libm,name);f.argtypes=argspec;f.restype=result
    original_loader=fixture.AexLoader;source=olmblur.SOURCE;cores=olmblur.CORES
    rows=[]
    with tempfile.TemporaryDirectory(prefix='stages_',dir=s) as td:
        work=Path(td);target=work/'variant/mac/OLMBlur';target.mkdir(parents=True);cr=work/'variant/core';cr.mkdir()
        for f in (ROOT/'core').iterdir():
            if f.suffix in ('.h','.cpp'):
                shutil.copyfile(f,cr/f.name)
                if args.source_revision and f in cores:
                    (cr/f.name).write_bytes(subprocess.check_output(['git','show',args.source_revision+':core/'+f.name]))
        helper=cr/'olmblur_helper.cpp';body=helper.read_text();body='#include <cstdio>\n#include <cstdlib>\n'+body
        for direction,loop in ((0,'    for (std::size_t row = p.offset;'),(1,'    for (std::size_t y = 0;')):
            # Preserve all arithmetic; observe the validated helper inputs.
            if loop not in body and direction==1:loop='    for (std::size_t x = p.offset;'
            assert body.count(loop)==1,loop
            pos=body.index(loop)
            observe='''    if (const char* path=std::getenv("OLM_BLUR_STAGES_C12")) {
        FILE* f=std::fopen(path,"ab"); if(f) {
            const std::uint64_t h[]={DIRECTION,p.width,p.height,p.passes,p.offset,p.radius};
            std::fwrite(h,sizeof(h),1,f);std::fwrite(flags,1,p.width*p.height,f);
            std::fwrite(weights,4,p.radius+1,f);std::fwrite(src,12,p.width*p.height,f);std::fclose(f);
        }
    }
'''.replace('DIRECTION',str(direction))
            body=body[:pos]+observe+body[pos:]
        helper.write_text(body)
        for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):shutil.copyfile(source.with_name(name),target/name)
        body=(subprocess.check_output(['git','show',args.source_revision+':mac/OLMBlur/OLMBlur.cpp']).decode() if args.source_revision else source.read_text());anchor=next(l for l in body.splitlines() if 'return "generic-small-fixture";' in l)
        body=body.replace(anchor,'\t// C12 diagnostic gate bypass.').replace('!SmallDefaultPF32Source(input_world)','false')
        olmblur.SOURCE=target/'OLMBlur.cpp';olmblur.SOURCE.write_text(body);olmblur.CORES=[cr/f.name for f in cores]
        a.binary=triage.build_binary(a,work);a.env['OLM_BLUR_STAGES_C12']=str(work/'mac-trace.bin')
        provenance={'source_sha256':sha(subprocess.check_output(['git','show',args.source_revision+':mac/OLMBlur/OLMBlur.cpp']) if args.source_revision else source.read_bytes()),'core_sha256':{f.name:sha((subprocess.check_output(['git','show',args.source_revision+':core/'+f.name]) if args.source_revision else f.read_bytes())) for f in cores},'source_revision':args.source_revision,'aex_sha256':sha(a.aex.read_bytes()),'worker_sha256':sha(WORKER.read_bytes()),'candidate_sha256':sha(a.binary.read_bytes())}
        matrix=None
        if args.matrix_depth:
            from verify_blur_radius_C12 import cases
            matrix=list(cases(a,args.matrix_depth))
        for index in args.indices:
            c=matrix[index] if matrix is not None else a.generate(args.seed,index);v={p['slot']:p['value'] for p in c['parameters']};assert v[5]==0
            oracle,reference=a.oracle(c,work,time.monotonic()+90,'smart');assert oracle['status']=='ok',oracle
            (work/'input.bin').write_bytes(c['pixels']);(work/'expected.bin').write_bytes(reference)
            stages=[];imports=[]
            class Traced(original_loader):
                def register_import_impl(self,name,impl):
                    if name in ('pow','powf','expf'):
                        def observed(uc,unused):
                            read=self.read_xmm_f64 if name=='pow' else self.read_xmm_f32
                            write=self.write_xmm_f64 if name=='pow' else self.write_xmm_f32
                            vals=[read(i) for i in range(1 if name=='expf' else 2)]
                            result=getattr(libm,name)(*vals);write(0,result)
                            imports.append({'name':name,'arguments':vals,'result':result})
                            return 0
                        impl=observed
                    return super().register_import_impl(name,impl)
                def __init__(self,*aa,**kw):
                    super().__init__(*aa,**kw)
                    def entry(uc,address,size,user):
                        rsp=uc.reg_read(UC_X86_REG_RSP)
                        w,h,passes,offset,radius=[struct.unpack('<i',self.read_bytes(rsp+x,4))[0] for x in (0x28,0x30,0x38,0x40,0x48)]
                        if passes==0:return
                        n=w*h
                        stages.append(dict(direction=int(address==0x180001980),width=w,height=h,passes=passes,offset=offset,radius=radius,
                            flags=self.read_bytes(uc.reg_read(UC_X86_REG_RCX),n),weights=self.read_bytes(uc.reg_read(UC_X86_REG_R9),(radius+1)*4),plane=self.read_bytes(uc.reg_read(UC_X86_REG_RDX),n*12)))
                    for addr in (0x180001000,0x180001980):self.uc.hook_add(UC_HOOK_CODE,entry,begin=addr,end=addr)
            fixture.AexLoader=Traced;fixture.AEX=a.aex;fixture.FIXTURE=work;fixture.WIDTH,fixture.HEIGHT=c['geometry']
            actual=fixture.run_row(dict(id=f'seed{args.seed}-{index}',depth=c['depth'],legacy=0,amount=v[1],smoothness=v[2],repeat=v[3],bias_direction=v[4],source='input.bin',expected='expected.bin',expected_sha256=sha(reference),expect_exact=False))
            path=work/'mac-trace.bin';path.unlink(missing_ok=True)
            result,raw,guards=a.candidate(c,work,'smart',time.monotonic()+90);assert result['status']=='ok',result
            mac=decode(path.read_bytes());assert len(stages)==len(mac),(index,len(stages),len(mac))
            comparison=[];first=None
            for j,(orig,port) in enumerate(zip(stages,mac)):
                record={'index':j,'original':{},'mac':{}}
                for key in orig:
                    if isinstance(orig[key],bytes):
                        for name,side in [('original',orig),('mac',port)]:record[name][key+'_sha256']=sha(side[key])
                        if orig[key]!=port[key]:
                            d=raw_diff(orig[key],port[key],8 if key=='flags' else 32);record[key+'_diff']=d
                            if first is None:first={'stage':j,'field':key,'diff':d}
                    else:
                        record['original'][key]=orig[key];record['mac'][key]=port[key]
                        if orig[key]!=port[key] and first is None:first={'stage':j,'field':key,'original':orig[key],'mac':port[key]}
                comparison.append(record)
            rows.append(dict(seed=args.seed,index=index,case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),trace_output=actual,cached_binding=actual['active_sha256']==sha(reference),candidate_sha256=sha(raw),output_exact=raw==reference,output_diff=None if raw==reference else raw_diff(reference,raw,c['depth']),first_difference=first,stages=comparison,imports=imports))
            print(index,'binding',rows[-1]['cached_binding'],'first',first,flush=True)
    fixture.AexLoader=original_loader;olmblur.SOURCE=source;olmblur.CORES=cores
    args.report.write_text(json.dumps(dict(schema='olmblur-stages-C12/1',provenance=provenance,rows=rows),indent=2,sort_keys=True)+'\n')
    assert all(r['cached_binding'] for r in rows),'direct AEX output must bind to cached worker'

if __name__=='__main__':main()
