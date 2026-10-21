#!/usr/bin/env python3
"""Paired original-AEX/public-Mac stage witnesses for C02 (scratch instrumentation)."""
import argparse
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from adapters.public import replace_once
from core import load_corpus, sha
from aex_loader import AexLoader
from aex_witness import leaf_check
from probe_directionalblur_f16_allocator import compare
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP

SCRATCH = ROOT/'orchestra/state/C02-dblur-smart'
FIXTURE = ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'


class TracedAdapter(Adapter):
    def __init__(self,args):
        super().__init__(args)
        self.core_ref=args.core_ref

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            original = ROOT/'core/dblur_frontonly.cpp'
            target = Path(next(str(x) for x in argv if str(x).endswith('/host.cpp'))).with_name('trace_core.cpp')
            body = (subprocess.check_output(['git','show',f'{self.core_ref}:core/dblur_frontonly.cpp'],cwd=ROOT).decode()
                    if self.core_ref else original.read_text())
            self.traced_core_sha256=sha(body.encode())
            prefix = '''#include <cstdio>
#include <cstdlib>
static void c02_dump(const char* name, const float* data, size_t count) {
 if (const char* dir = std::getenv("OLM_C02_TRACE")) {
  char path[4096]; std::snprintf(path,sizeof(path),"%s/%s",dir,name);
  if(FILE* f=std::fopen(path,"wb")){std::fwrite(data,4,count,f);std::fclose(f);}
 }
}
'''
            body = replace_once(body, '    return maximum_area;',
                '    c02_dump("rotated",image.data(),image.size());\n'
                '    c02_dump("map",records->data(),records->size());\n'
                '    c02_dump("divisor",&maximum_area,1);\n    return maximum_area;')
            body = replace_once(body, '    return weights;',
                '    char name[80]; std::snprintf(name,sizeof(name),"weights-%d",count);\n'
                '    c02_dump(name,weights.data(),weights.size());\n    return weights;')
            body = body.replace('        a = b;', '        a = b;\n        c02_dump("rotated",a.data(),a.size());')
            target.write_text(prefix+body)
            argv = [target if x == original else x for x in argv]+['-I',ROOT/'core']
        return super().compile(argv, deadline)


def run_fixture(case, directory, aex, expf_leaf='double-round'):
    body = FIXTURE.read_text().replace(
        '(row_width // 2, 73), (row_width // 2, row_width - 72)',
        '(row_width // 2, 0), (row_width // 2, row_width - 1)')
    # Raw typed input bypasses only the PNG transport, before world allocation.
    body = replace_once(body, '    left, top, right, bottom = args.world_area',
                        '    source = C02_PIXELS\n    left, top, right, bottom = args.world_area')
    fixture = types.ModuleType('c02_fixture')
    fixture.__file__ = str(FIXTURE)
    exec(compile(body, str(FIXTURE), 'exec'), fixture.__dict__)
    w,h = case['geometry']
    fixture.C02_PIXELS = case['pixels']
    fixture.load_argb = lambda _: (w,h,bytes(w*h*4),bytes(w*h*4))
    fixture.TARGETS = ((0,0),)
    trace, stages = {}, {}

    class TracedLoader(AexLoader):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw)
            ptrs = [self.host_alloc(16) for _ in range(4)]
            self.write_bytes(ptrs[0], bytes(16))
            for p in ptrs[1:]: self.write_bytes(p,b'\xa5'*16)
            checked = leaf_check(self,0x180001000,[0,0,*ptrs,0,0,0,0,1,0])
            assert self.read_bytes(ptrs[1],16)==bytes(16)
            assert all(self.read_bytes(p,16)==bytes(4)+b'\xa5'*12 for p in ptrs[2:])
            trace['abi_leaf_instructions']=checked['instructions']
            def rowdriver(ld,address,size):
                if stages: return
                sp=ld.uc.reg_read(UC_X86_REG_RSP)
                ctx=fixture.u64(ld,sp+0x38)
                ww,wh=fixture.u32(ld,ctx+0x80a0),fixture.u32(ld,ctx+0x80a4)
                src=fixture.u64(ld,ld.uc.reg_read(UC_X86_REG_R8))
                stages['rotated']=ld.read_bytes(src,ww*wh*16)
                stages['map']=ld.read_bytes(fixture.u64(ld,ctx+0x8118),ww*wh*16)
                stages['divisor']=ld.read_bytes(ctx+0x38,4)
                for count_offset,table_offset in ((0x48,0x58),(0x50,0x4068),(0x4c,0x3ed8),(0x54,0x7ee8)):
                    count=fixture.u32(ld,ctx+count_offset)
                    if count: stages[f'weights-{count}']=ld.read_bytes(ctx+table_offset,count*4)
                trace['work_geometry']=[ww,wh]
            self.add_code_hook(0x1800038d0,rowdriver)

        def register_import_impl(self,name,impl):
            if name=='expf':
                original=impl
                def impl(uc,args):
                    argument=struct.pack('<f',self.read_xmm_f32(0)).hex()
                    result=original(uc,args)
                    trace.setdefault('expf_calls',[]).append({'argument':argument,
                        'result':struct.pack('<f',self.read_xmm_f32(0)).hex()})
                    return result
            return super().register_import_impl(name,impl)
    fixture.AexLoader=TracedLoader
    source,output,raw=directory/'input.raw',directory/'fixture.json',directory/'aex.raw'
    source.write_bytes(case['pixels'])
    names={1:'angle',2:'brightness-gain',3:'size-variation',5:'front-strength',6:'front-alpha-fade',
        7:'front-sharp-tail',10:'back-strength',11:'back-alpha-fade',12:'back-sharp-tail',
        15:'noise-variation',16:'noise-type',18:'seed',19:'noise-offset',20:'thickness'}
    sys.argv=[str(FIXTURE),'--aex',str(aex),'--source',str(source),'--output',str(output),
        '--host-output-raw',str(raw),'--bitdepth',str(case['depth']),
        '--actual-iterate-callbacks','--no-detour-rotate','--no-detour-rowdriver',
        '--downsample-num','1','--downsample-den','1','--world-area','0','0',str(w),str(h),
        '--max-instructions','200000000']
    sys.argv+=['--expf-leaf',expf_leaf]
    for p in case['parameters']:
        slot,value=p['slot'],p['value']
        if slot not in names: continue
        if slot not in (2,20): value=math.floor(value)
        sys.argv+=['--'+names[slot],str(value)]
    fixture.main()
    result=json.loads(output.read_text())
    assert result['status']=='ok',result.get('blocked')
    trace['builder']=result['execution']['param_context']
    trace['rowdriver_calls']=result['execution']['rowdriver_calls']
    return trace,stages,raw.read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--clusters',type=int,nargs='+',default=[2,3,8,9,10,11,12,13,14,18])
    p.add_argument('--expf-leaf',choices=['double-round','native-f32'],default='double-round')
    p.add_argument('--allow-fixture-difference',action='store_true')
    p.add_argument('--core-ref',help='Read the traced core from this git revision (no checkout)')
    args=p.parse_args()
    args.main,args.max_size,args.case_timeout=ROOT.parent.parent,256,30
    SCRATCH.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH))
    tempfile.tempdir=str(SCRATCH)
    triage=json.loads((ROOT/'reports/fuzz/olmdirectionalblur_triage_20261022.json').read_text())
    report={'cases':[]}
    with tempfile.TemporaryDirectory(prefix='stages_',dir=SCRATCH) as tmp:
        tmp=Path(tmp);adapter=TracedAdapter(args)
        report['provenance']=adapter.prepare(tmp,time.monotonic()+180)
        for target in triage['clusters']:
            if target['cluster'] not in args.clusters: continue
            directory=tmp/str(target['cluster']);directory.mkdir()
            case,_=load_corpus(ROOT/target['corpus'],adapter)
            trace,stages,native=run_fixture(case,directory,adapter.aex,args.expf_leaf)
            oracle,reference=adapter.oracle(case,directory,time.monotonic()+60)
            assert oracle['status']=='ok'
            adapter.env['OLM_C02_TRACE']=str(directory)
            result,mac,_=adapter.candidate(case,directory,'smart',time.monotonic()+60)
            assert result['status']=='ok'
            row={'cluster':target['cluster'],'corpus':target['corpus'],'trace':trace,
                'fixture_session':compare(native,reference),'final':compare(reference,mac),
                'stages':{name:compare(raw,(directory/name).read_bytes(),4) for name,raw in stages.items() if (directory/name).is_file()}}
            # Exact words around each stage's first divergence are reviewable.
            for name,raw in stages.items():
                if name not in row['stages']: continue
                row['stages'][name]['aex_hex']=raw.hex()
                row['stages'][name]['mac_hex']=(directory/name).read_bytes().hex()
            report['cases'].append(row)
            args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
            if not args.allow_fixture_difference: assert native==reference, row['fixture_session']
            print('CLUSTER',target['cluster'],'FINAL',row['final']['different_units'],
                  'STAGES',{k:v['different_units'] for k,v in row['stages'].items()},flush=True)
    report['probe_sha256']=sha(Path(__file__).read_bytes())
    report['fixture_sha256']=sha(FIXTURE.read_bytes())
    report['expf_leaf']=args.expf_leaf
    report['core_ref']=args.core_ref
    report['traced_core_sha256']=adapter.traced_core_sha256
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__': main()
