#!/usr/bin/env python3
"""Typed exported-owner probes for HDR, color spaces, thresholds and palettes."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_olmcolorkey_inside_outside_owner_20261001 as public
ROOT=public.ROOT
SOURCE=public.SOURCE
sha=public.sha
HARNESS=ROOT/'tools/emulation/colorkey_typed_controls_harness_20261001.cpp'
AEX=public.thin_owner.general.base.retained.actual_probe.AEX

def fixture(definition,depth):
    raw,rb=public.around.source_fixture(definition,depth);profile=definition['profile']
    if profile=='sdr':return raw,rb
    assert depth in ('PF16','PF32')
    data=bytearray(raw);ps=8 if depth=='PF16' else 16;fmt='<4H' if depth=='PF16' else '<4f'
    for y in range(definition['height']):
        for x in range(definition['width']):
            at=y*rb+x*ps;a,r,g,b=struct.unpack_from(fmt,data,at)
            if depth=='PF16':
                if profile in ('alpha_hdr','combined'):a=min(65535,a*2)
                if profile in ('rgb_hdr','combined'):r,g,b=[min(65535,v*2) for v in (r,g,b)]
            else:
                if profile=='alpha_hdr':a*=2
                elif profile=='alpha_signed':a=-a if a else 0
                elif profile=='rgb_hdr':r,g,b=[v*2 for v in (r,g,b)]
                elif profile=='rgb_signed':r,g,b=[-v for v in (r,g,b)]
                elif profile=='combined':
                    a=a*(2 if (x+y)%2 else -1)
                    r,g,b=[v*(2 if (x+y)%2 else -1) for v in (r,g,b)]
                else:raise ValueError(profile)
            struct.pack_into(fmt,data,at,a,r,g,b)
    return bytes(data),rb

def parameters(keep=False,premultiplied=False,replace=False,space=1,precision=1,threshold=0,per_component=False,per_color=False,count=2,palette='normal',thin=0,thin_type=2,blur=0,blur_type=2,direction=2):
    values={1:int(keep),2:threshold,4:int(premultiplied),5:space,6:precision,7:int(per_color),8:int(per_component),9:threshold,10:threshold,11:threshold,14:thin,15:thin_type,18:blur,19:blur_type,20:direction,22:count,23:int(replace)}
    result=[{'slot':slot,'value':value} for slot,value in values.items()]
    for i in range(count):
        color=[255,0,0,0] if i%2==0 else [255,0,255,0]
        if palette=='tail':color=[255,0,0,0] if i==count-1 else [255,13+i,27+i,81+i]
        if palette=='duplicate':color=[255,0,0,0]
        base=24+i*8
        for offset,value in ((0,int(palette!='tail' or i==count-1)),(1,1),(4,threshold),(5,threshold),(6,threshold),(7,threshold)):
            result.append({'slot':base+offset,'value':value})
        result.extend([{'slot':base+2,'color':color},{'slot':base+3,'color':[255,224,32,96] if i%2==0 else [255,26,89,242]}])
    return sorted(result,key=lambda v:v['slot'])

def config_text(values):
    return ''.join(f"{p['slot']} c "+' '.join(map(str,p['color']))+'\n' if 'color' in p else f"{p['slot']} s {p['value']}\n" for p in values)

def compile_public(directory,body,sanitize=False):
    saved=public.range_owner.HARNESS
    try:
        public.range_owner.HARNESS=HARNESS.read_text()
        return public.range_owner.compile_public(directory,body,sanitize)
    finally:public.range_owner.HARNESS=saved

def mac_render(exe,temp,c,route,env=None):
    f=c['fixture'];raw,_=fixture(f,c['depth']);config=temp/'params.txt';config.write_text(config_text(c['parameters']))
    run=subprocess.run([str(exe),str(f['width']),str(f['height']),c['depth'][2:],str(route),str(config)],input=raw,check=True,capture_output=True,env=env)
    err=int(run.stderr.decode().strip().split(' ')[1]);assert not err or not run.stdout
    return err,run.stdout

def native_render(worker,temp,c):
    f=c['fixture'];raw,rb=fixture(f,c['depth']);ps={'PF8':4,'PF16':8,'PF32':16}[c['depth']]
    packed=b''.join(raw[y*rb:y*rb+f['width']*ps] for y in range(f['height']))
    payload='v4|'+';'.join(f"param_{v['slot']}@{v['slot']}:argb8="+','.join(map(str,v['color'])) if 'color' in v else f"param_{v['slot']}@{v['slot']}:f64={v['value']}" for v in c['parameters'])
    req={'v':4,'type':'render_frame','frame_index':0,'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':payload};message=json.dumps(req).encode()
    ip=temp/'input.raw';op=temp/'output.raw';ip.write_bytes(packed)
    run=subprocess.run([str(worker),'session',str(AEX),str(ip),str(op),str(f['width']),str(f['height']),'24','--pixel-format',{'PF8':'argb8','PF16':'argb16','PF32':'argb32f'}[c['depth']]],input=struct.pack('<I',len(message))+message,capture_output=True,check=True)
    messages=[];pos=0
    while pos<len(run.stdout):
        n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4;messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
    ready=next(m for m in messages if m['type']=='session_ready');frame=next(m for m in messages if m['type']=='frame_done');closed=next(m for m in messages if m['type']=='session_closed');out=op.read_bytes()
    assert ready['setup']['global_setup_error']==0 and ready['setup']['params_setup_error']==0
    assert frame['status']=='ok' and frame['render_error']==0 and frame['output']['guards_intact'] and frame['output']['render_path']=='smartfx' and frame['output']['checksum']==sha(out)
    close=closed['close'];assert close['session_clean'] and not close['unsupported_suite_calls'] and close['dropped_unsupported_suite_calls']==0
    return out,frame,payload,close

def specifications(matrix,w,h):
    f=lambda profile:{'id':f'edge{w}_{profile}','width':w,'height':h,'alpha':'mixed','profile':profile}
    if matrix=='hdr':
        edges=(('none',{}),('thin_minus',{'thin':-1}),('thin_plus',{'thin':1}),('inside',{'blur':1.5,'direction':1}),('around',{'blur':1.5}),('outside',{'blur':1.5,'direction':3}),('composed_inside',{'thin':1,'thin_type':3,'blur':7.3,'blur_type':3,'direction':1}),('composed_outside',{'thin':-1,'thin_type':1,'blur':.5,'blur_type':1,'direction':3}))
        for depth,profiles in (('PF8',('sdr',)),('PF16',('sdr','rgb_hdr','alpha_hdr','combined')),('PF32',('sdr','rgb_hdr','rgb_signed','alpha_hdr','alpha_signed','combined'))):
            for profile in profiles:
                for keep,premultiplied,replace in ((False,False,False),(True,False,True),(False,True,True),(True,True,True)):
                    for edge,values in edges:yield {'fixture':f(profile),'depth':depth,'label':edge,'parameters':parameters(keep=keep,premultiplied=premultiplied,replace=replace,**values)}
    elif matrix=='spaces':
        for space in range(1,7):
            for precision in (1,2,3):
                for component in (False,True):
                    for threshold in (0,.1):
                        for depth in ('PF8','PF16','PF32'):
                            for keep in (False,True):yield {'fixture':f('sdr'),'depth':depth,'label':f'space{space}_precision{precision}_component{component}_threshold{threshold}','parameters':parameters(keep=keep,space=space,precision=precision,per_component=component,threshold=threshold)}
    elif matrix=='palette':
        for count in (1,2,4,5,24,25):
            for palette in ('normal','tail','duplicate'):
                for per_color in (False,True):
                    for depth in ('PF8','PF16','PF32'):
                        for keep in (False,True):yield {'fixture':f('sdr'),'depth':depth,'label':f'count{count}_{palette}_percolor{per_color}','parameters':parameters(keep=keep,count=count,palette=palette,per_color=per_color,threshold=.1,replace=True)}
    else:raise ValueError(matrix)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--matrix',choices=('hdr','spaces','palette'),required=True);ap.add_argument('--width',type=int,default=9);ap.add_argument('--height',type=int,default=7);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    original=SOURCE.read_text();cases=[]
    with tempfile.TemporaryDirectory(prefix='olmck_typed_controls_') as td:
        temp=Path(td);exe=compile_public(temp/'mac',original)
        for c in specifications(args.matrix,args.width,args.height):
            source,_=fixture(c['fixture'],c['depth']);native,frame,payload,close=native_render(args.worker,temp,c);results={}
            for route,name in ((0,'classic'),(1,'smart')):
                err,raw=mac_render(exe,temp,c,route)
                results[name]={'error':err,'sha256':sha(raw) if not err else None,'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'aex':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:16] if not err else []}
            c.update(input_sha256=sha(source),packed_input_sha256=sha(b''.join(source[y*(c['fixture']['width']*{'PF8':4,'PF16':8,'PF32':16}[c['depth']]+8):y*(c['fixture']['width']*{'PF8':4,'PF16':8,'PF32':16}[c['depth']]+8)+c['fixture']['width']*{'PF8':4,'PF16':8,'PF32':16}[c['depth']]] for y in range(c['fixture']['height']))),actual_sha256=sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,config_sha256=sha(config_text(c['parameters']).encode()),frame_done=frame,unsupported_suite_calls=close['unsupported_suite_calls'],session_clean=close['session_clean'],results=results)
            cases.append(c)
            if len(cases)%32==0:print(args.matrix,len(cases),sum(c['results']['classic']['exact'] for c in cases),flush=True)
    r={'schema':'olmcolorkey.typed-controls-owner/1','matrix':args.matrix,'case_count':len(cases),'summary':{name:sum(c['results'][name]['exact'] for c in cases) for name in ('classic','smart')},'source_sha256':sha(original.encode()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'aex_sha256':sha(AEX.read_bytes()),'cases':cases,'claims_not_made':['No native Windows AE/UCRT/Mac AE/installed completion','No normal AE UI production of HDR/raw uint16 worlds proved','No all settings/geometry/ROI/downsample completion','Resident payload is slot/type bound; no per-frame parameter readback reported by session API']}
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==r;print(r['summary'],flush=True)
if __name__=='__main__':main()
