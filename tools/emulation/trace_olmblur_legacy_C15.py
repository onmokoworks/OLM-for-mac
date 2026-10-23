#!/usr/bin/env python3
"""C15 Legacy public AEX/helper input/output trace paired with Mac helpers.

Uses the retained public ABI fixture and native host libm import callbacks.
Complete output binding to the cached worker is required to interpret stages.
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
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R9,UC_X86_REG_R8,UC_X86_REG_RSP,UC_X86_REG_EAX
WORKER=Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'


def decode(data):
    records=[];at=0
    while at<len(data):
        direction,w,h,columns,rows,offset,radius=struct.unpack_from('<7Q',data,at);at+=56
        n=w*h
        fields={}
        for key,length in [('flags',n),('weights',(radius*2+1)*4),('plane',n*12)]:
            fields[key]=data[at:at+length];at+=length
        records.append(dict(direction=direction,width=w,height=h,columns=columns,rows=rows,offset=offset,radius=radius,**fields))
    assert at==len(data)
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source-revision')
    p.add_argument('--nonfinite-ops', action='store_true', help='Record raw SSE nonfinite operands/results in Legacy helpers')
    p.add_argument('--matrix-depth',type=int,choices=(8,16,32))
    p.add_argument('--seed',type=int,default=1);p.add_argument('--indices',type=int,nargs='+',default=[31,115,141,77,112])
    args=p.parse_args();s=args.scratch.resolve();assert s.is_relative_to(ROOT/'orchestra/state')
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
        helper=cr/'olmblur_fullworker_helper.cpp';body=helper.read_text();body='#include <cstdint>\n#include <cstdio>\n#include <cstdlib>\n'+body
        for direction,function in ((0,'horizontal'),(1,'vertical')):
            begin=body.index('void '+function+'(')
            pos=body.index('    volatile float carry_red',begin)
            observe='''    auto observe = [&](unsigned direction) {
        if (const char* path=std::getenv("OLM_BLUR_STAGES_C12")) {
            FILE* f=std::fopen(path,"ab"); if(f) {
                const std::uint64_t h[]={direction,p.width,p.height,p.columns,p.rows,p.offset,p.radius};
                std::fwrite(h,sizeof(h),1,f);std::fwrite(flags,1,p.width*p.height,f);
                std::fwrite(weights,4,p.radius*2+1,f);
                std::fwrite(direction<2?src:dst,12,p.width*p.height,f);std::fclose(f);
            }
        }
    };
    observe(DIRECTION);
'''.replace('DIRECTION',str(direction))
            body=body[:pos]+observe+body[pos:]
            end=body.index('\n}\n',pos)
            body=body[:end]+f'\n    observe({direction+2});'+body[end:]
        helper.write_text(body)
        for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):shutil.copyfile(source.with_name(name),target/name)
        body=(subprocess.check_output(['git','show',args.source_revision+':mac/OLMBlur/OLMBlur.cpp']).decode() if args.source_revision else source.read_text());anchor=next(l for l in body.splitlines() if 'return "generic-small-fixture";' in l)
        body=body.replace(anchor,'\t// C15 diagnostic gate bypass.').replace('!SmallDefaultPF32Source(input_world)','false')
        olmblur.SOURCE=target/'OLMBlur.cpp';olmblur.SOURCE.write_text(body);olmblur.CORES=[cr/f.name for f in cores]
        a.binary=triage.build_binary(a,work);a.env['OLM_BLUR_STAGES_C12']=str(work/'mac-trace.bin')
        provenance={'source_sha256':sha(subprocess.check_output(['git','show',args.source_revision+':mac/OLMBlur/OLMBlur.cpp']) if args.source_revision else source.read_bytes()),'core_sha256':{f.name:sha((subprocess.check_output(['git','show',args.source_revision+':core/'+f.name]) if args.source_revision else f.read_bytes())) for f in cores},'source_revision':args.source_revision,'aex_sha256':sha(a.aex.read_bytes()),'worker_sha256':sha(WORKER.read_bytes()),'candidate_sha256':sha(a.binary.read_bytes())}
        matrix=None
        if args.matrix_depth:
            from verify_blur_legacy_C15 import cases
            matrix=list(cases(a,args.matrix_depth))
        for index in args.indices:
            c=matrix[index] if matrix is not None else a.generate(args.seed,index);v={p['slot']:p['value'] for p in c['parameters']};assert v[5]==1
            oracle,reference=a.oracle(c,work,time.monotonic()+90,'smart');assert oracle['status']=='ok',oracle
            (work/'input.bin').write_bytes(c['pixels']);(work/'expected.bin').write_bytes(reference)
            stages=[];imports=[];writer=[];nonfinite_ops=[]
            class Traced(original_loader):
                def register_libm_impls(self, *args, **kwargs):
                    super().register_libm_impls(*args, **kwargs)
                    # The base loader installs this table directly, bypassing
                    # register_import_impl. Explicitly bind all observed imports.
                    for name in ('pow', 'powf', 'expf'):
                        self.register_import_impl(name, self.import_impls[name])
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
                    if args.nonfinite_ops:
                        from olmblur_nonfinite_trace_C24 import install_nonfinite_hooks
                        install_nonfinite_hooks(self, stages, nonfinite_ops,
                            ((0x1800014f0,0x180001980),(0x180001ea0,0x180002280)))
                    pending=[]
                    def store(uc,address,size,user):
                        writer.append(dict(address=hex(address),rounded_bits=struct.pack('<f',self.read_xmm_f32(0)).hex(),eax=f"{uc.reg_read(UC_X86_REG_EAX):08x}"))
                    addresses={16:(0x180006cf7,0x180006d0d,0x180006d22),8:(0x180007fe3,0x180007ff8,0x18000800c)}
                    for addr in addresses.get(c['depth'],()):self.uc.hook_add(UC_HOOK_CODE,store,begin=addr,end=addr)

                    def returned(uc,address,size,user):
                        if not pending or address!=pending[-1][0]:return
                        _,record,dest=pending.pop()
                        record=dict(record,direction=record['direction']+2,
                            plane=self.read_bytes(dest,fixture.WIDTH*fixture.HEIGHT*12))
                        stages.append(record)
                    def entry(uc,address,size,user):
                        rsp=uc.reg_read(UC_X86_REG_RSP)
                        w,h,columns,rows,offset,radius=[struct.unpack('<i',self.read_bytes(rsp+x,4))[0] for x in (0x28,0x30,0x38,0x40,0x48,0x50)]
                        if columns==0 or rows==0:return
                        # Horizontal helper ignores its height argument; use the public world.
                        h=fixture.HEIGHT;n=w*h
                        record=dict(direction=int(address==0x180001ea0),width=w,height=h,columns=columns,rows=rows,offset=offset,radius=radius,
                            flags=self.read_bytes(uc.reg_read(UC_X86_REG_RCX),n),weights=self.read_bytes(uc.reg_read(UC_X86_REG_R9),(radius*2+1)*4),plane=self.read_bytes(uc.reg_read(UC_X86_REG_RDX),n*12))
                        stages.append(record)
                        ret=struct.unpack('<Q',self.read_bytes(rsp,8))[0]
                        pending.append((ret,record,uc.reg_read(UC_X86_REG_R8)))
                        if ret not in self.return_hooks:
                            self.return_hooks.add(ret);self.uc.hook_add(UC_HOOK_CODE,returned,begin=ret,end=ret)
                    self.return_hooks=set()
                    for addr in (0x1800014f0,0x180001ea0):self.uc.hook_add(UC_HOOK_CODE,entry,begin=addr,end=addr)
            fixture.AexLoader=Traced;fixture.AEX=a.aex;fixture.FIXTURE=work;fixture.WIDTH,fixture.HEIGHT=c['geometry']
            actual=fixture.run_row(dict(id=f'seed{args.seed}-{index}',depth=c['depth'],legacy=1,amount=v[1],smoothness=v[2],repeat=v[3],bias_direction=v[4],source='input.bin',expected='expected.bin',expected_sha256=sha(reference),expect_exact=False))
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
            writer_boundary=None
            if raw!=reference and c['depth'] in (8,16):
                size=c['depth']//8;word=next(i for i in range(len(raw)//size) if raw[i*size:(i+1)*size]!=reference[i*size:(i+1)*size]);pixel,channel=divmod(word,4)
                writer_boundary=dict(pixel=pixel,channel=channel,original=reference[word*size:(word+1)*size].hex(),mac=raw[word*size:(word+1)*size].hex(),instruction=writer[pixel*3+channel-1] if writer else None)
            rows.append(dict(writer_boundary=writer_boundary,writer_calls=len(writer),seed=args.seed,index=index,case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),trace_output=actual,cached_binding=actual['active_sha256']==sha(reference),candidate_sha256=sha(raw),output_exact=raw==reference,output_diff=None if raw==reference else raw_diff(reference,raw,c['depth']),first_difference=first,stages=comparison,imports=imports))
            if args.nonfinite_ops:rows[-1]['nonfinite_ops']=nonfinite_ops
            print(index,'binding',rows[-1]['cached_binding'],'first',first,flush=True)
    fixture.AexLoader=original_loader;olmblur.SOURCE=source;olmblur.CORES=cores
    args.report.write_text(json.dumps(dict(schema='olmblur-legacy-stages-C15/1',provenance=provenance,rows=rows),indent=2,sort_keys=True)+'\n')
    assert all(r['cached_binding'] for r in rows),'direct AEX output must bind to cached worker'

if __name__=='__main__':main()
