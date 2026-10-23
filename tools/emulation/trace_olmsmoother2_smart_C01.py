#!/usr/bin/env python3
"""C01 paired core stages, joined to retained public Smart oracle.

Run with MAIN's tools/emulation/.venv/bin/python. Instrumentation is generated
only in ticket scratch. AEX classifier/cce0 execute original instructions using
captured input plane and explicit retained worker ABI/config offsets. Full output
is independently compared to the public AEX worker; this is not native AE proof.
"""
import argparse, json, os, struct, subprocess, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
SCRATCH = ROOT/'orchestra/state/C01-smoother2-smart'
sys.path[:0] = [str(ROOT/'tools/fuzz'), str(Path(__file__).parent)]
from adapters.olmsmoother2 import Adapter, SOURCE, SHIM
from core import load_corpus, sha
from aex_loader import AexLoader
from test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 import SmallStatic, Dynamic, desc
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RSP, UC_X86_REG_RBP, UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_XMM0, UC_X86_REG_XMM2, UC_X86_REG_XMM3


def build(adapter, directory, source):
    directory.mkdir(parents=True, exist_ok=True)
    adapter.prepare(directory, time.monotonic()+180)
    src = source
    helper = '''static void c01_dump(const char *name, const void *p, size_t n) {
 const char *root = std::getenv("C01_DUMP"); if (!root) return;
 char path[4096]; std::snprintf(path,sizeof(path),"%s/%s.bin",root,name);
 FILE *f=std::fopen(path,"wb"); if(!f) std::abort();
 std::fwrite(p,1,n,f); std::fclose(f);
}
'''
    src = src.replace('static int g_olmsmoother2_trace_x = -1;', helper+'static int g_olmsmoother2_trace_x = -1;')
    src = src.replace('const std::vector<FPix> scratch_pre_setup = scratch;', 'const std::vector<FPix> scratch_pre_setup = scratch; c01_dump("pre_setup",scratch.data(),w*h*sizeof(FPix));')
    src = src.replace('const std::vector<FPix> scratch_pre_gamma = scratch;', 'const std::vector<FPix> scratch_pre_gamma = scratch; c01_dump("pre_gamma",scratch.data(),w*h*sizeof(FPix));')
    src = src.replace('p.class_plane = class_plane.data();', '''p.class_plane = class_plane.data();
 c01_dump("input_plane",sample_base,w*h*sizeof(FPix));
 c01_dump("class_plane",class_plane.data(),w*h*4);''')
    src = src.replace('build_polygon(poly, plane_in, x, y, p);', '''build_polygon(poly, plane_in, x, y, p);
 if(trace_this_pixel) { c01_dump("center",&center,16); c01_dump("polygon",poly.samples,poly.count*20); }''')
    src = src.replace('gamma_decode_premul(working, poly, gamma_enable, adaptive_gamma);', '''gamma_decode_premul(working, poly, gamma_enable, adaptive_gamma);
 if(trace_this_pixel) { c01_dump("c0d0_center",&working,16); c01_dump("c0d0_polygon",poly.samples,poly.count*20); }''')
    src = src.replace('composite_separate_scalar(accum, working, poly);', '''composite_separate_scalar(accum, working, poly);
 if(trace_this_pixel) c01_dump("ab00",&accum,16);''')
    src = src.replace('post_unpremul_gamma(accum, gamma_enable, adaptive_gamma);', '''post_unpremul_gamma(accum, gamma_enable, adaptive_gamma);
 if(trace_this_pixel) c01_dump("b120",&accum,16);''')
    (directory/'production_under_test.cpp').write_text(src)
    adapter.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
        '-Wno-deprecated-declarations','-I',directory,'-I',SHIM,'-I',SOURCE.parent,
        directory/'host.cpp','-o',adapter.binary],time.monotonic()+180)


def pair(case, adapter, directory, xy):
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('pre_setup','pre_gamma','input_plane','class_plane','center','polygon','c0d0_center','c0d0_polygon','ab00','b120'):
        (directory/(name+'.bin')).unlink(missing_ok=True)
    adapter.env.update(C01_DUMP=str(directory), OLMSMOOTHER2_TRACE_PIXEL=','.join(map(str,xy)),
                       OLMSMOOTHER2_TRACE_LOG=str(directory/'mac.log'))
    status, raw, _ = adapter.candidate(case,directory,'smart',time.monotonic()+120)
    assert status['status']=='ok', status
    oracle, reference = adapter.oracle(case,directory,time.monotonic()+120)
    assert oracle['status']=='ok', oracle
    params = {p['slot']:p['value'] for p in case['parameters']}
    early_stages = {}
    assert params[8] != 3 or params[9] == 1, 'gamma pow outside this probe'
    w,h = case['geometry']
    l = AexLoader(str(adapter.aex),verbose=False,fast=False)
    l.register_libm_impls(max_threads=1)
    def alloc(data):
        p=l.bump_alloc(max(16,len(data)),align=16); l.write_bytes(p,bytes(data)); return p
    inp=(directory/'input_plane.bin').read_bytes()
    if params[1]:
        assert case['depth'] == 32, 'key stage currently grounded for PF32 only'
        pre=(directory/'pre_setup.bin').read_bytes()
        expected=b''.join(case['pixels'][i+4:i+16]+case['pixels'][i:i+4] for i in range(0,len(case['pixels']),16))
        assert pre==expected, 'PF32 source unpack differs before key stage'
        kb=alloc(pre); kd=desc(l,kb,w*16,w,h)
        ptrs=[alloc(struct.pack('<i',v)) for v in (w,0,h,0)]
        color=params[2]
        rgb=[v/255 for v in color[1:]]
        SmallStatic(l,h)
        if params[3]:
            palette=alloc(struct.pack('<4f',*rgb,color[0]/255))
            keycfg=bytearray(0x80)
            struct.pack_into('<QQ',keycfg,0x60,1,palette)
            l.call_function(0x180002930,int_args=[*ptrs,kd,alloc(keycfg)],max_instructions=10_000_000)
        else:
            key=alloc(struct.pack('<4f',color[0]/255,*rgb))
            l.call_function(0x180002a70,int_args=[*ptrs,kd,key],max_instructions=10_000_000)
        keyed=l.read_bytes(kb,len(pre))
        early_stages['pre_setup']=pre
        early_stages['pre_gamma']=keyed
        # The original key worker modifies alpha only. Reuse the captured
        # candidate RGB decode (not an independent decode-stage proof), and
        # join original keyed alpha to the independently rendered public AEX.
        decoded=bytearray(inp)
        for i in range(0,len(pre),16):
            assert keyed[i:i+12]==pre[i:i+12]
            decoded[i+12:i+16]=keyed[i+12:i+16]
        inp=bytes(decoded)
    sb=alloc(inp); cb=alloc(b'\xa5'*(w*h*4))
    sd,cd=desc(l,sb,w*16,w,h),desc(l,cb,w*4,w,h)
    cfg=bytearray(0x80)
    struct.pack_into('<i',cfg,0,int(params[7]==1))
    struct.pack_into('<iii',cfg,0x1c,int(params[6]),int(params[4]),int(params[5]))
    # Gamma None / empty gamma-colors list are apply=false. Gamma All 1 is
    # identity pow, so still invoke the original gamma helper with apply=true.
    struct.pack_into('<f',cfg,0x28,params[9])
    if params[8]==3: cfg[0x40]=1
    if params[8]==2 and params[10]:
        palette=alloc(b''.join(struct.pack('<4f',*(v/255 for v in params[11+i][1:]),params[11+i][0]/255) for i in range(params[10])))
        struct.pack_into('<QQ',cfg,0x30,params[10],palette)
        cfg[0x40]=3
    config=alloc(cfg); rect=alloc(struct.pack('<4i',0,0,w,h))
    SmallStatic(l,h)
    result=l.call_function(0x18000ada0,int_args=[sd,cd,rect,config],max_instructions=30_000_000)
    classes=l.read_bytes(cb,w*h*4)
    (directory/'aex_class_plane.bin').write_bytes(classes)
    stages={}; events=[]
    def hook(uc,address,size,user):
        sp=uc.reg_read(UC_X86_REG_RSP); bp=uc.reg_read(UC_X86_REG_RBP)
        if address in (0x1800104d0,0x18000e7c0,0x18000e290,0x180013630):
            event={'pc':hex(address),'caller':hex(struct.unpack('<Q',l.read_bytes(sp,8))[0])}
            if address==0x1800104d0:
                event.update(xy=list(struct.unpack('<ii',l.read_bytes(uc.reg_read(UC_X86_REG_RDX),8))),weight=hex(uc.reg_read(UC_X86_REG_XMM2)&0xffffffff))
            elif address==0x180013630:
                event.update(width=hex(uc.reg_read(UC_X86_REG_XMM0)&0xffffffff),position=uc.reg_read(UC_X86_REG_RDX)&0xffffffff,edge=hex(uc.reg_read(UC_X86_REG_XMM2)&0xffffffff))
            else:
                event.update(descriptor=list(struct.unpack('<6i',l.read_bytes(uc.reg_read(UC_X86_REG_RDX),24))),scale_m=hex(uc.reg_read(UC_X86_REG_XMM2)&0xffffffff),scale_h=hex(uc.reg_read(UC_X86_REG_XMM3)&0xffffffff))
            events.append(event)
        elif address==0x18000cd5f:
            count=struct.unpack('<Q',l.read_bytes(bp+0x90,8))[0]
            stages['polygon']=l.read_bytes(bp-0x60,count*20)
        elif address==0x18000cda3:
            stages['center']=l.read_bytes(sp+0x50,16)
        elif address==0x18000ce02:
            stages['c0d0_center']=l.read_bytes(sp+0x50,16)
            stages['c0d0_polygon']=l.read_bytes(bp-0x60,len(stages['polygon']))
        elif address==0x18000ce2e: stages['ab00']=l.read_bytes(bp-0x80,16)
        elif address==0x18000ce4c: stages['b120']=l.read_bytes(uc.reg_read(UC_X86_REG_RAX),16)
    hooks=[]
    for addr in (0x18000cd5f,0x18000cda3,0x18000ce02,0x18000ce2e,0x18000ce4c,0x1800104d0,0x18000e7c0,0x18000e290,0x180013630):
        hooks.append(l.uc.hook_add(UC_HOOK_CODE,hook,begin=addr,end=addr))
    out=alloc(b'\0'*16); coord=alloc(struct.pack('<ii',*xy)); ctx=alloc(b'\0'*0x20)
    l.call_function(0x18000cce0,int_args=[out,sd,cd,coord,config,ctx],max_instructions=20_000_000)
    # Join the reconstructed core to the independently rendered public AEX.
    from test_olmsmoother2_v2_nonuniform_actual_aex_20260805 import ENCODE
    from test_olmsmoother2_typed_writeback_20260717 import WORKERS
    table=alloc(ENCODE)
    l.write_bytes(ctx+0x10,struct.pack('<QQ',10000,table))
    ob=alloc(b'\xa5'*len(reference)); od=desc(l,ob,w*case['depth']//2,w,h)
    ptrs=[alloc(struct.pack('<i',v)) for v in (w,0,h,0)]
    # Remove pixel stage hooks before rendering the full frame.
    for handle in hooks: l.uc.hook_del(handle)
    worker=WORKERS['PF'+str(case['depth'])]; Dynamic(l,worker)
    l.call_function(worker,int_args=[*ptrs,sd,cd,od,config,ctx],max_instructions=150_000_000)
    joined=l.read_bytes(ob,len(reference))
    assert joined==reference, 'reconstructed core does not join public AEX output'
    comparisons={}
    for name,expected in dict(**early_stages,class_plane=classes,**stages).items():
        actual_path=directory/(name+'.bin')
        if not actual_path.exists():
            comparisons[name]={'equal':False,'mac_stage_not_executed':True,'aex_hex':expected.hex()}
            continue
        actual=actual_path.read_bytes()
        mismatches=[i for i in range(max(len(expected),len(actual))) if expected[i:i+1]!=actual[i:i+1]]
        comparisons[name]={'equal':expected==actual,'aex_bytes':len(expected),'mac_bytes':len(actual),
            'different_bytes':len(mismatches),'first_byte':mismatches[0] if mismatches else None,
            'first_aex_word':expected[(mismatches[0]//4)*4:(mismatches[0]//4)*4+4].hex() if mismatches else None,
            'first_mac_word':actual[(mismatches[0]//4)*4:(mismatches[0]//4)*4+4].hex() if mismatches else None,
            'aex_hex':expected.hex() if name not in ('class_plane','pre_setup','pre_gamma') else None,
            'mac_hex':actual.hex() if name not in ('class_plane','pre_setup','pre_gamma') else None}
    return {'index':case['index'],'geometry':[w,h],'xy':xy,'input_sha256':sha(case['pixels']),
        'core_public_aex_join':joined==reference,'public_exact':raw==reference,'public_aex_sha256':sha(reference),'public_mac_sha256':sha(raw),
        'source_plane_sha256':sha(inp),'key_stage_original':bool(params[1]),
        'rgb_decode_scope':'captured candidate RGB; original key alpha; full public join asserted' if params[1] else 'captured candidate source plane; full public join asserted',
        'aex_events':events,'stages':comparisons}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--indices',type=int,nargs='+',default=[299]); p.add_argument('--generated',action='store_true'); p.add_argument('--label',default='trace'); p.add_argument('--source-ref'); p.add_argument('--reference-trace',type=Path)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--scratch',type=Path,default=SCRATCH)
    p.add_argument('--worker',type=Path)
    args=p.parse_args()
    scratch=args.scratch.resolve()
    scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch))
    worker=args.worker
    if worker is None:
        baseline=json.loads((scratch/'before.json').read_text())
        worker=Path(baseline['provenance']['worker_path'])
    options=argparse.Namespace(main=MAIN,worker=worker,max_size=256,case_timeout=120)
    source=SOURCE.read_text() if not args.source_ref else subprocess.check_output(['git','show',args.source_ref+':'+str(SOURCE.relative_to(ROOT))],text=True)
    adapter=Adapter(options); build(adapter,scratch/(args.label+'-build'),source); rows=[]
    coords={c['index']:c['xy'] for c in json.loads(args.reference_trace.read_text())['cases']} if args.reference_trace else {}
    for index in args.indices:
        if args.generated:
            case=adapter.generate(args.seed,index)
        else:
            path=next((ROOT/'tests/fuzz_corpus/olmsmoother2').glob(f'*case{index:06d}_*.json'))
            case,_=load_corpus(path,adapter)
        directory=scratch/(args.label+f'-{index}')
        directory.mkdir(exist_ok=True)
        # Locate the first public output mismatch before capturing stages.
        adapter.env.pop('C01_DUMP',None); adapter.env.pop('OLMSMOOTHER2_TRACE_PIXEL',None)
        a,ref=adapter.oracle(case,directory,time.monotonic()+120)
        b,raw,_=adapter.candidate(case,directory,'smart',time.monotonic()+120)
        assert a['status']==b['status']=='ok'
        pixel=next((i//(case['depth']//8*4) for i,(x,y) in enumerate(zip(ref,raw)) if x!=y),0)
        xy=[pixel%case['geometry'][0],pixel//case['geometry'][0]]
        xy=coords.get(index,xy)
        row=pair(case,adapter,directory,xy); rows.append(row)
        print(index,xy,{k:v['equal'] for k,v in row['stages'].items()},flush=True)
    report={'source_sha256':sha(source.encode()),'aex_sha256':sha(adapter.aex.read_bytes()),'cases':rows}
    (scratch/(args.label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__': main()
