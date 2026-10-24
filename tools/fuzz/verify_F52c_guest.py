#!/usr/bin/env python3
"""Cross-build a synthetic Windows PE to verify oracle allocation, not plugin math."""
import json,os,struct,subprocess
from pathlib import Path
from adapters.public import messages
ROOT=Path(__file__).resolve().parents[2]
def main():
 s=ROOT/'orchestra/state/F52c-geometry-hosts-and-campaigns/guest-contract';s.mkdir(parents=True,exist_ok=True)
 for stale in s.glob('fixture-*.bin'):stale.unlink()
 env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
 sysroot=Path(subprocess.check_output(['rustc','--print','sysroot'],text=True).strip())
 linker=sysroot/'lib/rustlib/aarch64-apple-darwin/bin/rust-lld'
 subprocess.run(['clang','--target=x86_64-pc-windows-msvc','-O1','-ffreestanding','-fno-stack-protector','-c',str(ROOT/'tools/fuzz/harnesses/geometry_guest.c'),'-o',str(s/'fixture.obj')],env=env,check=True)
 subprocess.run([linker,'-flavor','link','/dll','/noentry','/nodefaultlib','/out:'+str(s/'fixture.aex'),str(s/'fixture.obj')],env=env,check=True)
 (s/'input.raw').write_bytes(bytes([255,32,64,128])*77)
 request=json.dumps(dict(v=4,type='render_frame',frame_index=0,current_time=dict(value=0,scale=24,step=1,total=1),parameters='v4|')).encode()
 cmd=[str(Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker'),'session',str(s/'fixture.aex'),str(s/'input.raw'),str(s/'output.raw'),'21','19','24','--pixel-format','argb8','--fixture-render-path','smart','--downsample-x','1/2','--downsample-y','1/3','--rowbytes-pad','3','--negotiate-output','1','--request-rect','-3,-2,14,10']
 r=subprocess.run(cmd,input=struct.pack('<I',len(request))+request,capture_output=True,env=env)
 (s/'stderr.log').write_bytes(r.stderr)
 decoded=messages(r.stdout);(s/'protocol.json').write_text(json.dumps(decoded,indent=2)+'\n')
 assert r.returncode==0,(r.returncode,r.stderr.decode())
 frame=next(m for m in decoded if m['type']=='frame_done')
 assert frame['output']['rect']==[-3,-2,14,10] and frame['output']['guards_intact'],frame
 expected=b''.join(bytes([255,x-3+32,y-2+32,77]) for y in range(12) for x in range(17))
 assert (s/'output.raw').read_bytes()==expected
 print('PASS synthetic PE: expanded 17x12 origin -3,-2 stride 71; 816 exact bytes; guards intact')
if __name__=='__main__':main()
