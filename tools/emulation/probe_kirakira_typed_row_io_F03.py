#!/usr/bin/env python3
"""F03: original AEX address/read/write leaves and public layout metamorphism.

All generated files stay in --scratch. No emulator worker is built or modified.
The public oracle is packed; the independent leaf probe exercises odd AEX strides.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters import olmkirakira
from core import command, sha, raw_diff
from run import default_worker, main_checkout

IO_MAIN = r'''
namespace {
static int io_probe(int depth, int pad, int offset) {
    const int w=3,h=3,ps=depth/8*4,rb=w*ps+pad;
    std::vector<unsigned char> bytes(offset+rb*h+16,0xa5);
    for(int y=0;y<h;++y)
        if(fread(bytes.data()+offset+y*rb,1,w*ps,stdin)!=size_t(w*ps))return 65;
    const auto before=bytes;
    PF_EffectWorld world{};world.data=(PF_PixelPtr)(bytes.data()+offset);
    world.width=w;world.height=h;world.rowbytes=rb;
#ifdef F03_CHECK_SPAN
    if(!WorldLayoutIsSafe(&world,ps))return 71;
    if(WorldLayoutIsSafe(nullptr,ps)||WorldLayoutIsSafe(&world,0))return 72;
    PF_EffectWorld invalid=world;
    invalid.rowbytes=w*ps-1;if(WorldLayoutIsSafe(&invalid,ps))return 73;
    invalid=world;invalid.rowbytes=0;if(WorldLayoutIsSafe(&invalid,ps))return 74;
    invalid.rowbytes=-rb;if(WorldLayoutIsSafe(&invalid,ps))return 75;
    invalid=world;invalid.width=0;if(WorldLayoutIsSafe(&invalid,ps))return 76;
    invalid=world;invalid.height=0;if(WorldLayoutIsSafe(&invalid,ps))return 77;
    invalid=world;invalid.data=nullptr;if(WorldLayoutIsSafe(&invalid,ps))return 78;
    invalid=world;invalid.data=(PF_PixelPtr)(UINTPTR_MAX-ps);
    if(WorldLayoutIsSafe(&invalid,ps))return 79;
#endif
    std::vector<FloatRGBA> values;
    if(depth==8)values=ReadPixels<PF_Pixel8>(&world);
    if(depth==16)values=ReadPixels<PF_Pixel16>(&world);
    if(depth==32)values=ReadPixels<PF_PixelFloat>(&world);
    if(bytes!=before)return 67;
    for(const auto &v:values) {
        const float rgba[]={v.r,v.g,v.b,v.a};
        fwrite(rgba,1,sizeof(rgba),stdout);
    }
    for(int y=0;y<h;++y)for(int x=0;x<w;++x) {
        const auto &v=values[y*w+x];
        if(depth==8)StoreWorldPixel<PF_Pixel8>(&world,x,y,PixelTraits<PF_Pixel8>::WriteAexTruncate(v));
        if(depth==16)StoreWorldPixel<PF_Pixel16>(&world,x,y,PixelTraits<PF_Pixel16>::WriteAexTruncate(v));
        if(depth==32)StoreWorldPixel<PF_PixelFloat>(&world,x,y,PixelTraits<PF_PixelFloat>::WriteAexTruncate(v));
    }
    for(size_t i=0;i<bytes.size();++i) {
        bool active=i>=size_t(offset)&&i<size_t(offset+rb*h)&&((i-offset)%rb)<size_t(w*ps);
        if(!active&&bytes[i]!=before[i])return 68;
    }
    for(int y=0;y<h;++y)fwrite(bytes.data()+offset+y*rb,1,w*ps,stdout);
    return 0;
}
}
'''


def layout_off(source):
    start=source.find('\tsize_t alignment = 1;', source.index('static bool WorldLayoutIsSafe'))
    if start>=0:
        end=source.index('\tconst uint64_t last_row_offset',start)
        source=source[:start]+source[end:]
    source=source.replace('input->rowbytes == closure_rowbytes &&\n\t\toutput->rowbytes == closure_rowbytes &&',
        'WorldLayoutIsSafe(input, pixel_size) && WorldLayoutIsSafe(output, pixel_size) &&')
    source=source.replace('input->rowbytes == expected_rowbytes && output->rowbytes == expected_rowbytes &&',
        'WorldLayoutIsSafe(input, pixel_size) && WorldLayoutIsSafe(output, pixel_size) &&')
    return source


class ProbeAdapter(olmkirakira.Adapter):
    def compile(self, argv, deadline):
        argv=list(argv)
        if argv[0]=='clang++':
            host=next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
            source=self.probe_source.read_text()
            if self.gate_off: source=layout_off(source)
            source=source.replace('#include "OLMKiraKira.h"','#include "'+str(olmkirakira.SOURCE.with_suffix('.h'))+'"')
            source=source.replace('#include "../../core/','#include "'+str(ROOT/'core')+'/')
            snapshot=host.parent/'source.cpp';snapshot.write_text(source)
            self.compiled_source_sha256=sha(source.encode())
            if 'LoadWorldPixel' in source: argv.insert(1,'-DF03_HAS_BYTE_IO=1')
            if 'const uint64_t available' in source: argv.insert(1,'-DF03_CHECK_SPAN=1')
            body=host.read_text().replace(str(olmkirakira.SOURCE),str(snapshot))
            body=body.replace('int main(int argc,char **argv) {', (IO_MAIN if 'LoadWorldPixel' in source else '')+'''
int main(int argc,char **argv) {
    #ifdef F03_HAS_BYTE_IO
    if(argc==5&&!strcmp(argv[1],"io"))return io_probe(atoi(argv[2]),atoi(argv[3]),atoi(argv[4]));
#endif
''')
            # Keep offsets independent of row padding; validate prefix/suffix too.
            body=body.replace('std::vector<unsigned char> input(irb*h,0xa5),output(orb*h,0xee);',
                '''size_t io=std::strtoul(getenv("F03_INPUT_OFFSET")?getenv("F03_INPUT_OFFSET"):"0",nullptr,10);
    size_t oo=std::strtoul(getenv("F03_OUTPUT_OFFSET")?getenv("F03_OUTPUT_OFFSET"):"0",nullptr,10);
    std::vector<unsigned char> input(io+irb*h+16,0xa5),output(oo+orb*h+16,0xee);''')
            body=body.replace('input.data()+y*irb','input.data()+io+y*irb').replace('(PF_PixelPtr)input.data()','(PF_PixelPtr)(input.data()+io)')
            body=body.replace('output.data()+y*orb','output.data()+oo+y*orb').replace('(PF_PixelPtr)output.data()','(PF_PixelPtr)(output.data()+oo)')
            body=body.replace('output[y*orb+x]','output[oo+y*orb+x]')
            body=body.replace('if(input!=before)return 67;', '''if(input!=before)return 67;
    for(size_t i=0;i<output.size();++i)if((i<oo||i>=oo+orb*h)&&output[i]!=0xee)return 68;''')
            host.write_text(body)
            if self.sanitizers:
                argv[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-g']
                self.env.update(ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        return super().compile(argv,deadline)


def leaf_probe(adapter, scratch, deadline):
    from aex_loader import AexLoader
    from aex_witness import leaf_check
    loader=AexLoader(str(adapter.aex),verbose=False,fast=True)
    world=loader.host_alloc(128);ptr=loader.host_alloc(8);rgba=loader.host_alloc(16)
    src=loader.bump_alloc(512,align=16);dst=loader.bump_alloc(512,align=16)
    rows=[]
    for depth,addr,reader,writer in [(8,0x1812309f0,0x181230a80,0x181230b90),
                                   (16,0x181230a20,0x181230af0,0x181230bd0),
                                   (32,0x181230a50,0x181230b60,0x181230c20)]:
        fmt,top={8:('B',255),16:('H',32768),32:('f',1)}[depth];ps=depth//8*4
        raw=b''.join(struct.pack('<4'+fmt,*([((i*37+j*19)%256) if depth==8 else
            ((i*3137+j*997)%32769) if depth==16 else ((i*17+j*13)%97)/96 for j in range(4)])) for i in range(9))
        for pad in (0,1,3,7,16):
            for offset in (0,1,2,3):
                rb=3*ps+pad;loader.write_bytes(src,b'\xa5'*512);loader.write_bytes(dst,b'\xee'*512)
                loader.write_bytes(world,b'\0'*128)
                loader.write_bytes(world+0x18,struct.pack('<Qiii',src+offset,rb,3,3))
                for y in range(3):loader.write_bytes(src+offset+y*rb,raw[y*3*ps:(y+1)*3*ps])
                before=loader.read_bytes(src,512);plane=bytearray();written=bytearray()
                for y in range(3):
                    for x in range(3):
                        leaf_check(loader,addr,[world,x,y,ptr])
                        address=struct.unpack('<Q',loader.read_bytes(ptr,8))[0]
                        assert address==src+offset+y*rb+x*ps
                        leaf_check(loader,reader,[rgba,rgba+4,rgba+8,rgba+12,address])
                        lanes=loader.read_bytes(rgba,16);plane.extend(lanes)
                        target=dst+offset+y*rb+x*ps
                        loader.call_function(writer,int_args=[0,0,0,0,target],
                            float_args={i:lanes[i*4:i*4+4] for i in range(4)},max_instructions=1000)
                        written.extend(loader.read_bytes(target,ps))
                assert loader.read_bytes(src,512)==before
                out=loader.read_bytes(dst,512)
                active={offset+y*rb+x for y in range(3) for x in range(3*ps)}
                assert all(v==0xee for i,v in enumerate(out) if i not in active)
                status,actual,err=command([adapter.binary,'io',depth,pad,offset],data=raw,
                    timeout=10,deadline=deadline,env=adapter.env)
                assert status['status']=='ok', (status,err[-1000:])
                assert actual==plane+written, (depth,pad,offset)
                rows.append(dict(depth=depth,padding=pad,offset=offset,input_sha256=sha(raw),
                    source_rgba_sha256=sha(plane),writer_sha256=sha(written),exact=True))
    return rows


def public_probe(adapter,scratch,deadline):
    rows=[]
    for w,h in ([(32,18)] if adapter.mode3_closure else [(5,3),(9,7),(17,11)]):
        for depth in (8,16,32):
            case=adapter.generate(1,0);case.update(geometry=[w,h],depth=depth,profile='sdr')
            # Existing admitted m1_h7 tuple; gain 0.1 is the original builder
            # default even though its captured declared minimum is 1 (T06).
            overrides={1:1,2:1,3:1,4:0,5:.1,6:100,7:0,8:100,9:100,10:0,13:0,
                16:7,19:0,22:0,25:0,28:0,31:0,34:0,37:0,40:0}
            if adapter.mode3_closure: overrides.update({2:3,16:50})
            case['parameters']=adapter.defaults(w,h)
            for p in case['parameters']:
                p['value']=[255]*4 if p['kind']=='c' else overrides[p['slot']]
            values=[]
            for i in range(w*h):
                values.extend([(64+i*11)%256,(i*15)%256,(i*11)%256,(i*7)%256])
            case['pixels']=b''.join(struct.pack('<'+{8:'B',16:'H',32:'f'}[depth],
                v if depth==8 else int(v*32768/255+.5) if depth==16 else v/255) for v in values)
            oracle,expected=adapter.oracle(case,scratch,deadline)
            assert oracle['status']=='ok',oracle
            # Packed, independent padded, odd-stride, and every float alignment.
            for ip,op,io,oo in ((12,12,0,0),(0,0,0,0),(1,5,0,0),(3,11,1,3),(7,1,2,1),(16,32,3,2)):
                case.update(input_padding=ip,output_padding=op)
                adapter.env.update(F03_INPUT_OFFSET=str(io),F03_OUTPUT_OFFSET=str(oo))
                for route in adapter.routes:
                    status,actual,guards=adapter.candidate(case,scratch,route,deadline)
                    outcome='exact' if status['status']=='ok' and actual==expected else 'mismatch' if status['status']=='ok' else status['status']
                    rows.append(dict(geometry=[w,h],depth=depth,route=route,input_padding=ip,output_padding=op,
                        input_offset=io,output_offset=oo,status=outcome,guards=guards,
                        input_sha256=sha(case['pixels']), expected_sha256=sha(expected),actual_sha256=sha(actual) if actual else None,
                        diff=raw_diff(expected,actual,depth) if outcome=='mismatch' else None))
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source',type=Path,default=olmkirakira.SOURCE)
    p.add_argument('--baseline-report',type=Path)
    p.add_argument('--mode3-closure',action='store_true')
    p.add_argument('--layout-gate-off',action='store_true');p.add_argument('--sanitizers',action='store_true')
    args=p.parse_args();scratch=args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state/F03-kira-typed-row-io')
    scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch))
    options=argparse.Namespace(max_size=256,case_timeout=20,main=main_checkout(),worker=default_worker())
    adapter=ProbeAdapter(options);adapter.probe_source=args.source.resolve()
    adapter.gate_off=args.layout_gate_off;adapter.sanitizers=args.sanitizers
    adapter.mode3_closure=args.mode3_closure
    deadline=time.monotonic()+900
    provenance=adapter.prepare(scratch,deadline)
    # Only changed implementations expose Load/StoreWorldPixel; public baseline
    # comparisons are retained separately in the seeded fuzz campaign.
    leaves=leaf_probe(adapter,scratch,deadline) if 'LoadWorldPixel' in args.source.read_text() else []
    public=public_probe(adapter,scratch,deadline)
    from collections import Counter
    report=dict(provenance=provenance,source_sha256=sha(args.source.read_bytes()),
        compiled_source_sha256=adapter.compiled_source_sha256,
        layout_gate_off=args.layout_gate_off,sanitizers=args.sanitizers,leaves=leaves,public=public,
        summary=dict(leaf_exact=len(leaves),public=dict(Counter(r['status'] for r in public))))
    if args.baseline_report:
        baseline=json.loads(args.baseline_report.read_text())['public']
        transitions=Counter()
        for before,after in zip(baseline,public,strict=True):
            for key in ('geometry','depth','route','input_padding','output_padding','input_offset','output_offset','input_sha256','expected_sha256'):
                assert before[key]==after[key],key
            transitions[before['status']+'->'+after['status']]+=1
            if before['status'] in ('exact','mismatch'):
                assert before['actual_sha256']==after['actual_sha256']
            else:
                assert after['status']=='exact',(before,after)
        report['summary']['transitions']=dict(transitions)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['summary']))
    assert all(r['status'] in ('exact','mismatch','refusal') for r in public)

if __name__=='__main__':main()
