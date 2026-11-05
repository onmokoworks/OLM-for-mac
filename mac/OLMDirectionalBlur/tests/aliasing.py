"""T21: actual AEX source aliasing and public Mac SmartRender differential.
Run with MAIN/tools/emulation/.venv/bin/python; no AEXCompat rebuild required.
"""
import argparse, hashlib, json, os, struct, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
MAIN = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
STATE = ROOT/'orchestra/state/T21-directionalblur-noise-aliasing-refusal'
EVIDENCE = ROOT/'orchestra/reports/T21-directionalblur-noise-aliasing-refusal-evidence'
STATE.mkdir(parents=True, exist_ok=True); EVIDENCE.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(STATE), TMP=str(STATE), TEMP=str(STATE), PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0, str(ROOT/'tools/emulation'))
W = H = 8

def sha(b): return hashlib.sha256(b).hexdigest()
def memory():
    import re
    text = subprocess.check_output(['memory_pressure'], text=True)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', text)[1])
    assert free >= 30, free
    return free

def source(depth):
    import probe_directionalblur_general_input_20261001 as owner
    packed = owner.typed(owner.pixels(W,H,True), depth)
    ps=depth//8*4; rb=W*ps+16
    padded=b''.join(packed[y*W*ps:(y+1)*W*ps]+bytes(16) for y in range(H))+bytes(ps)
    return packed,padded,rb

def oracle(depth,kind,relation):
    import dblur_fullrender_host_fixture_20260711 as f
    from unicorn import UC_HOOK_MEM_WRITE
    packed,padded,rb=source(depth); ps=depth//8*4
    calls=[]; writes=[]; worlds=[]
    original=f.build_world
    def build(ld,w,h,pixels,rowbytes,area):
        i=len(worlds)
        if i==0: pixels=padded
        if i==1: pixels=padded[ps:ps+rb*H] if relation=='partial' else padded[:rb*H]
        world=original(ld,w,h,pixels,rowbytes,area)
        if i==0:
            data=f.u64(ld,world+0x18)
            ld.uc.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,address,size,value,user:writes.append([address,size]),begin=data,end=data+len(padded)-1)
            calls.append((ld,data,bytes(padded)))
        if i==1 and relation in ('same','partial'):
            ld.write_bytes(world+0x18,struct.pack('<Q',calls[0][1]+(ps if relation=='partial' else 0)))
        worlds.append(world)
        return world
    f.build_world=build
    # Fixture's host callbacks execute original AEX populate/writer instructions.
    # Observe slot 17 checkout without altering its implementation.
    original_install=f.AexLoader.install_callback
    slots=[]
    def install(ld,name,callback,*a,**kw):
        if name=='PF_ParamCheckout':
            def wrapper(loader,args):
                slots.append(args[1]); return callback(loader,args)
            return original_install(ld,name,wrapper,*a,**kw)
        return original_install(ld,name,callback,*a,**kw)
    f.AexLoader.install_callback=install
    original_hook=f.AexLoader.add_code_hook
    def hook(ld,address,callback,*a,**kw):
        # Legacy diagnostic samples y=73 even for an 8-row fixture. Omit that
        # observer (not an AEX instruction or a host callback).
        if callback.__name__=='capture_rowdriver_entry': return
        return original_hook(ld,address,callback,*a,**kw)
    f.AexLoader.add_code_hook=hook
    directory=STATE/f'aex-{depth}-{kind}-{relation}';directory.mkdir(exist_ok=True)
    from PIL import Image
    import probe_directionalblur_general_input_20261001 as owner
    im=Image.new('RGBA',(W,H));im.putdata(owner.pixels(W,H,True));im.save(directory/'source.png')
    sys.argv=[str(Path(f.__file__)), '--source',str(directory/'source.png'),'--output',str(directory/'report.json'),
      '--host-output-raw',str(directory/'output.raw'),'--bitdepth',str(depth),'--pf16-source-scale','sdk-32768',
      '--downsample-den','1','--front-strength','4','--front-sharp-tail','0','--size-variation','0',
      '--noise-variation','25','--noise-type',str(kind),'--row-padding','16','--actual-iterate-callbacks',
      '--no-detour-rotate','--no-detour-rowdriver','--max-instructions','20000000']
    f.main()
    report=json.loads((directory/'report.json').read_text())
    ld,data,before=calls[0]
    intact=ld.read_bytes(data,len(before))==before
    result={'depth':depth,'type':kind,'relation':relation,'complete':report['output']['complete'],
            'source_intact':intact,'source_writes':writes,'checkout_slots':slots,
            'world_data':[hex(f.u64(ld,w+0x18)) for w in worlds], 'rowbytes':rb,'output':report['output']}
    (directory/'alias.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['complete'] and intact and not writes,result
    assert slots.count(17)==(kind==3),result
    return result

def build_mac():
    import probe_directionalblur_general_input_20261001 as owner
    body=(ROOT/'tools/emulation/directionalblur_layer_general_effectmain_harness_20261001.cpp').read_text()
    body=body[:body.index('int main(int argc,char**argv)')]
    body=body.replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp',str(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'))
    body+='''
int main(int argc,char**argv) {
 if(argc!=4)return 64; int depth=atoi(argv[1]),type=atoi(argv[2]);std::string relation=argv[3];
 int w=8,h=8,ps=depth/8*4,rb=w*ps+16;
 std::vector<unsigned char> input(rb*h+ps),layer(rb*h),output(rb*h,0xa5);
 if(fread(input.data(),1,input.size(),stdin)!=input.size())return 65;
 if(fread(layer.data(),1,layer.size(),stdin)!=layer.size())return 65;
 const auto before=input,lb=layer,ob=output;
 auto iw=MakeWorld(input.data(),rb,w,h,depth),ow=MakeWorld(output.data(),rb,w,h,depth),lw=MakeWorld(layer.data(),rb,w,h,depth);
 if(relation=="same")lw.data=iw.data;
 if(relation=="partial")lw.data=reinterpret_cast<PF_PixelPtr>(input.data()+ps);
 if(relation=="input_output")ow.data=iw.data;
 if(relation=="noise_output")ow.data=lw.data;
 PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS];PF_ParamDef*params[OLMDIRECTIONALBLUR_NUM_PARAMS];
 InitParams(defs,params,iw,0,4);defs[1].u.ad.value=0;defs[2].u.fs_d.value=1;defs[20].u.fs_d.value=10;
 defs[15].u.fd.value=25*65536;defs[16].u.pd.value=type;defs[17].u.ld=lw;
 HostState state;state.input=&iw;state.output=&ow;state.noise=&lw;state.defs=defs;
 state.format=depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;state.noise_format=state.format;
 SPBasicSuite basic=MakeBasic();PF_Err err=InvokeSmart(&state,&basic,depth,true);
 if(state.pre_noise_calls||state.pixel_noise_calls||state.param_checkout_attempts!=state.param_checkin_attempts||state.acquire!=state.release)return 68;
 if(input!=before||layer!=lb)return 66;
 for(int y=0;y<h;++y)for(int x=w*ps;x<rb;++x)if(output[y*rb+x]!=0xa5)return 67;
 printf("ERROR %d\\nCHECKOUT17 %d\\nRAW ",int(err),int(std::count(state.checkout_order.begin(),state.checkout_order.end(),17)));
 for(int y=0;y<h;++y)for(int x=0;x<w*ps;++x)printf("%02x",output[y*rb+x]);puts("");
 return 0;
}
'''
    path=STATE/'alias-host.cpp';path.write_text(body);owner.HARNESS=path
    # SDK and Util are untracked assets in MAIN; core is this worktree.
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    binary=STATE/'alias-host'
    subprocess.run([str(ROOT/'tools/ucrt_cxx.py'),'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
      '-Wno-pragma-pack','-Wno-deprecated-declarations','-ffunction-sections','-fdata-sections','-isysroot',sdk,
      *[v for p in ('Headers','Headers/SP','Util','Resources') for v in ('-I',str(MAIN/p))],str(path),
      str(ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp'),str(MAIN/'Util/AEGP_SuiteHandler.cpp'),str(MAIN/'Util/MissingSuiteError.cpp'),*[str(ROOT/'core'/p) for p in owner.CORES],'-Wl,-dead_strip','-framework','Cocoa','-o',str(binary)],check=True)
    return binary

def main():
    p=argparse.ArgumentParser();p.add_argument('--oracle',nargs=3);p.add_argument('--mac-only',action='store_true');args=p.parse_args()
    if args.oracle:
        d,t,r=args.oracle;oracle(int(d),int(t),r);return
    binary=build_mac();rows=[]
    for depth in (8,16,32):
      for kind in (1,2,3):
        for relation in ('disjoint','same','partial','input_output','noise_output'):
          if relation=='noise_output' and kind!=3: continue
          packed,padded,rb=source(depth);ps=depth//8*4
          layer=padded[ps:ps+rb*H] if relation=='partial' else padded[:rb*H]
          run=subprocess.run([str(binary),str(depth),str(kind),relation],input=padded+layer,capture_output=True,check=True)
          lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW'])
          row=dict(depth=depth,type=kind,relation=relation,error=int(lines['ERROR']),checkout17=int(lines['CHECKOUT17']),mac_sha256=sha(raw))
          overlap=relation=='input_output' or (relation=='noise_output' and kind==3)
          row['expected_refusal']=overlap
          if not overlap and not args.mac_only:
            free=memory();directory=STATE/f'aex-{depth}-{kind}-{relation}'
            with (STATE/'oracle.log').open('a') as log:
              subprocess.run([sys.executable,__file__,'--oracle',str(depth),str(kind),relation],stdout=log,stderr=subprocess.STDOUT,check=True)
            original=(directory/'output.raw').read_bytes()
            row.update(aex_sha256=sha(original),different_bytes=sum(a!=b for a,b in zip(raw,original)),first_mismatch=next((i for i,(a,b) in enumerate(zip(raw,original)) if a!=b),None),memory_free=free)
          rows.append(row);(EVIDENCE/'aliasing.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
          assert bool(row['error'])==overlap,row
          if 'different_bytes' in row: assert row['different_bytes']==0,row
    print('PASS',len(rows),flush=True)
if __name__=='__main__':main()
