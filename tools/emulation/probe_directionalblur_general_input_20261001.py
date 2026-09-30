#!/usr/bin/env python3
"""Compare exported AEX Smart owner to the Mac dispatcher on authored inputs."""
import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
AEX=ROOT/'plugins_2025/OLMDirectionalBlur.aex'
HARNESS=ROOT/'tools/emulation/directionalblur_general_input_harness_20261001.cpp'
SOURCE=ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'
CORES=('dblur_frontonly.cpp','dblur_rotate.cpp','dblur_rowdriver.cpp','dblur_field.cpp')
def sha(data): return hashlib.sha256(data).hexdigest()
def pixels(w,h,mixed):
    return [(20+(x*41+y*7)%220,12+(x*13+y*37)%232,8+(x*23+y*19)%240,
             (0,32,96,160,224,255)[(x+2*y)%6] if mixed else 255)
            for y in range(h) for x in range(w)]
def typed(px,depth):
    out=[]
    for r,g,b,a in px:
        if depth==8: out.append(bytes((a,r,g,b)))
        elif depth==16: out.append(struct.pack('<4H',*((c*32768+127)//255 for c in (a,r,g,b))))
        else: out.append(struct.pack('<4f',*(c/255 for c in (a,r,g,b))))
    return b''.join(out)
def compile_harness(binary,sanitize=False):
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    flags=['-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++','-std=c++17','-arch','arm64',*flags,'-fno-fast-math','-ffp-contract=off','-Wno-deprecated-declarations','-Wno-pragma-pack','-ffunction-sections','-fdata-sections','-isysroot',sdk,
                    '-I',str(ROOT/'Headers'),'-I',str(ROOT/'Headers/SP'),'-I',str(ROOT/'Util'),'-I',str(ROOT/'Resources'),str(HARNESS),
                    *(str(ROOT/'core'/p) for p in CORES),'-Wl,-dead_strip','-framework','Cocoa','-o',str(binary)],check=True)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--boundary',action='store_true',help='non-cardinal angles and unequal/longer dual strengths')
    ap.add_argument('--signed-boundary',action='store_true',help='negative fractional and near-zero angles')
    args=ap.parse_args();rows=[]
    with tempfile.TemporaryDirectory(prefix='dblur_general_') as td:
        temp=Path(td);binary=temp/'mac';compile_harness(binary)
        for name,w,h,mixed in (('odd-mixed',7,5,True),('odd-opaque',9,7,False)):
            px=pixels(w,h,mixed);png=temp/'input.png';im=Image.new('RGBA',(w,h));im.putdata(px);im.save(png)
            for angle in ((-17.25,-0.25,0.25) if args.signed_boundary else ((-45,17.25,123.5) if args.boundary else (0,45,90))):
                for front,back in (((1,1),(7,11),(31,17)) if args.boundary or args.signed_boundary else ((4,3),(4,0),(0,3))):
                    for depth,fmt in ((8,'argb8'),(16,'argb16'),(32,'argb32f')):
                        data=typed(px,depth)
                        output=temp/'output.png'
                        params=[f'Angle@1={angle}','Brightness Gain@2=1','Size Variation@3=0',f'Blur Strength@5={front}','Alpha Fade@6=0','Sharp Tail@7=0',f'Blur Strength@10={back}','Alpha Fade@11=0','Sharp Tail@12=0','Noise Variation@15=0','Noise Type@16=1','Seed@18=1','Offset@19=0','Thickness@20=3']
                        requested={1:angle,2:1,3:0,5:front,6:0,7:0,10:back,11:0,12:0,15:0,16:1,18:1,19:0,20:3}
                        payload='v4|'+';'.join(f'param_{slot}@{slot}:{"angle" if slot in (1,19) else "f64"}={value}' for slot,value in requested.items())
                        req={'v':4,'type':'render_frame','frame_index':0,'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':payload}
                        message=json.dumps(req).encode();input_path=temp/'input.raw';output_path=temp/'output.raw';input_path.write_bytes(data)
                        run=subprocess.run([str(args.worker),'session',str(AEX),str(input_path),str(output_path),str(w),str(h),'24','--pixel-format',fmt],input=struct.pack('<I',len(message))+message,capture_output=True)
                        if run.returncode:raise RuntimeError(run.stderr.decode()[-2000:])
                        messages=[];pos=0
                        while pos<len(run.stdout):
                            n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4;messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
                        win=next(m for m in messages if m['type']=='frame_done')
                        if win.get('render_error')!=0 or win.get('status')!='ok' or win['output']['render_path']!='smartfx' or not win['output']['guards_intact']:raise RuntimeError('native owner failed: '+str(win))
                        native=output_path.read_bytes()
                        if sha(native)!=win['output']['checksum'] or input_path.read_bytes()!=data:raise RuntimeError('native slot identity mismatch')
                        mac=subprocess.run([str(binary),str(w),str(h),str(depth),str(angle),str(front),str(back)],input=data,check=True,capture_output=True)
                        lines=dict(line.split(' ',1) for line in mac.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW'])
                        if len(native)!=len(data) or len(raw)!=len(data):raise RuntimeError('typed extent mismatch')
                        row={'fixture':name,'geometry':[w,h],'depth':depth,'angle':angle,'front':front,'back':back,'input_sha256':sha(data),'input_png_sha256':sha(png.read_bytes()),'windows_raw_sha256':sha(native),'mac_raw_sha256':sha(raw),'raw_exact':sha(raw)==sha(native),'mac_route':int(lines['ROUTE']),'requested_values':requested,'resident_parameter_payload':payload,'frame_done':win,'guards_intact':True}
                        row['different_bytes']=sum(a!=b for a,b in zip(native,raw))
                        row['first_differences']=[{'offset':i,'windows':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12]
                        row['mac_materialized_angle']=float(lines['ANGLE'])
                        rows.append(row);print(name,depth,angle,front,back,'exact',row['raw_exact'],flush=True)
    report={'schema':'directionalblur.general-input-owner/1','campaign':'signed-boundary' if args.signed_boundary else ('boundary' if args.boundary else 'neutral-controls'),'aex_sha256':sha(AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'production_source_sha256':sha(SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'core_sha256':{p:sha((ROOT/'core'/p).read_bytes()) for p in CORES},'cases':rows,'exact_count':sum(r['raw_exact'] for r in rows),'total_case_count':len(rows),'claims_not_made':['No native Windows AE execution','Mac dispatcher seam does not prove public parameter checkout','Host math substitutes do not prove Windows UCRT fidelity','No arbitrary inputs or full compatibility claim']}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('EXACT',report['exact_count'],'/',len(rows));return 0
if __name__=='__main__':raise SystemExit(main())
