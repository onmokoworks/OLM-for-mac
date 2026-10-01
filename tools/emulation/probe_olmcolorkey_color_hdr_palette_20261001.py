#!/usr/bin/env python3
"""Independent color-space/palette decisions for typed HDR and FLOAT32 grains."""
import argparse,json,struct,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
BUILD=owner.ROOT/'reports/colorkey_lab94_controlled_worker_build_20261001.json'
FROZEN_SHA='0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'
GRAIN_BITS=(0x00000000,0x80000000,0x000116c2,0x358637bd,0x3b808080,0x3effffff,0x3f000000,0x3f000001,0x3f7fffff,0x3f800000,0x3f800001,0x40100000,0xbeaaaaab)
def fixture(f,depth):
    w,h=f['width'],f['height'];ps={'PF8':4,'PF16':8,'PF32':16}[depth];rb=w*ps+8;raw=bytearray([0xa5]*(rb*h));profile=f['profile']
    for y in range(h):
        for x in range(w):
            rgb=independent.COLORS[(x+3*y)%len(independent.COLORS)];a=(255,128,0,64)[(x+y)%4];vals=[a,*rgb]
            if depth=='PF8':assert profile=='sdr';struct.pack_into('<4B',raw,y*rb+x*ps,*vals);continue
            vals=[int(v*32768/255) for v in vals] if depth=='PF16' else [v/255 for v in vals]
            if depth=='PF16':
                if profile in ('alpha_hdr','combined'):vals[0]=min(65535,vals[0]*2)
                if profile in ('rgb_hdr','combined'):vals[1:]=[min(65535,v*2) for v in vals[1:]]
            elif profile=='float_grains':
                vals=[independent.number(GRAIN_BITS[(x*3+y*5+i*4)%len(GRAIN_BITS)]) for i in range(4)]
            else:
                if profile in ('alpha_hdr','combined'):vals[0]*=2 if (x+y)%2 else -1
                elif profile=='alpha_signed':vals[0]*=-1
                if profile in ('rgb_hdr','combined'):vals[1:]=[v*2 for v in vals[1:]]
                elif profile=='rgb_signed':vals[1:]=[-v for v in vals[1:]]
            struct.pack_into('<4H' if depth=='PF16' else '<4f',raw,y*rb+x*ps,*vals)
    return bytes(raw),rb

def parameters(space,component,variant):
    count=(1,2,4,25)[variant];threshold=(0,.025,.15,.4)[variant]
    p=owner.parameters(space=space,precision=1+variant%3,count=count,threshold=threshold,per_component=component,per_color=variant%2==1,keep=variant%2==0,premultiplied=variant>=2,replace=variant!=0)
    colors=[independent.COLORS[(i*5+6)%len(independent.COLORS)] for i in range(count)]
    if variant==1:colors.reverse()
    elif variant==2:colors[2]=colors[0]
    for v in p:
        if v['slot'] in (9,10,11):v['value']={9:threshold,10:min(1,threshold+.035),11:min(1,threshold+.07)}[v['slot']]
        if v['slot']<24:continue
        i,off=divmod(v['slot']-24,8)
        if off==0:v['value']=int(variant!=3 or i%4!=1)
        elif off==1:v['value']=int(i%3!=2)
        elif off==2:v['color']=[(255,127,0,255)[i%4],*colors[i]]
        elif off==3:v['color']=[(255,127,0)[i%3],(17+i*67)%256,(91+i*43)%256,(231+i*29)%256]
        elif off>=4:v['value']=min(1,threshold+.01*(i%5)+.025*(off-4))
    return p

def specifications():
    for space in range(1,7):
        for component in (False,True):
            for depth,profiles in (('PF8',('sdr',)),('PF16',('sdr','rgb_hdr','alpha_hdr','combined')),('PF32',('sdr','rgb_hdr','rgb_signed','alpha_hdr','alpha_signed','combined','float_grains'))):
                for profile in profiles:
                    for variant in range(4):yield {'fixture':{'id':'independent_color_hdr_palette','width':13,'height':5,'profile':profile},'depth':depth,'label':f'space{space}_component{component}_{profile}_variant{variant}','parameters':parameters(space,component,variant)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--controlled-worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();build=json.loads(BUILD.read_text());assert owner.sha(args.worker.read_bytes())==FROZEN_SHA;assert owner.sha(args.controlled_worker.read_bytes())==build['controlled_worker_sha256'];source=owner.SOURCE.read_text();owner.fixture=fixture;cases=[]
    with tempfile.TemporaryDirectory(prefix='olmck_color_hdr_palette_') as td:
        temp=Path(td);exe=owner.compile_public(temp/'production',source)
        for c in specifications():
            values={v['slot']:v.get('value') for v in c['parameters']};controlled=values[5]==4 and values[8]==0;worker=args.controlled_worker if controlled else args.worker
            native,frame,payload,close=owner.native_render(worker,temp,c);raw,rb=fixture(c['fixture'],c['depth']);ps={'PF8':4,'PF16':8,'PF32':16}[c['depth']]
            c.update(input_sha256=owner.sha(raw),packed_input_sha256=owner.sha(b''.join(raw[y*rb:y*rb+c['fixture']['width']*ps] for y in range(c['fixture']['height']))),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],reference_kind='controlled-host-f32-atan2f' if controlled else 'frozen-exported-owner',worker_sha256=owner.sha(worker.read_bytes()),results=independent.compare(exe,temp,c,native));cases.append(c)
            if len(cases)%48==0:print('COLOR_HDR_PALETTE',len(cases),sum(c['results']['classic']['exact'] for c in cases),flush=True)
    report={'schema':'olmcolorkey.color-hdr-palette/1','case_count':len(cases),'summary':{route:sum(c['results'][route]['exact'] for c in cases) for route in ('classic','smart')},'source_sha256':owner.sha(source.encode()),'aex_sha256':owner.sha(owner.AEX.read_bytes()),'frozen_worker_sha256':FROZEN_SHA,'controlled_worker_sha256':build['controlled_worker_sha256'],'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(owner.__file__),Path(independent.__file__),owner.HARNESS,BUILD)},'grain_bits':[f'{v:08x}' for v in GRAIN_BITS],'cases':cases,'claims_not_made':['Reference routes and host mathematics remain distinct from native Windows UCRT/AE','No all-source/palette/threshold/geometry/float/HDR/state completion','No public AE production of raw HDR/uint16 worlds asserted','Per-frame resident parameter readback unavailable','Combinations are a bounded campaign, not a full parameter Cartesian product']}
    head=dict(report);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==report;print('RESULT',report['summary'],flush=True)
if __name__=='__main__':main()
