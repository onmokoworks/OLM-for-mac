#!/usr/bin/env python3
"""Independent typed Lab key-state and adjacent-FLOAT32 threshold witnesses."""
import argparse, copy, json, struct, tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
from colorkey_lab_mutation_candidate_20261001 import candidate_source

COLORS = ((0,0,0),(0,255,0),(0,0,255),(255,255,255),(128,128,128),
          (204,38,26),(26,191,204),(27,190,205),(127,129,126),
          (255,0,255),(1,1,1),(254,253,252),(44,75,119))

def fixture(definition, depth):
    w,h=definition['width'],definition['height'];ps={'PF8':4,'PF16':8,'PF32':16}[depth];rb=w*ps+8
    data=bytearray([0xa5]*(rb*h))
    for y in range(h):
        for x in range(w):
            rgb=definition.get('rgb',COLORS[(x+3*y)%len(COLORS)])
            alpha=255 if definition.get('opaque') else (255,128,0,64)[(x+y)%4]
            vals=(alpha,*rgb)
            if depth=='PF8':struct.pack_into('<4B',data,y*rb+x*ps,*vals)
            elif depth=='PF16':struct.pack_into('<4H',data,y*rb+x*ps,*(int(v*32768/255) for v in vals))
            else:struct.pack_into('<4f',data,y*rb+x*ps,*(v/255 for v in vals))
    return bytes(data),rb

def controls(space, component, precision, palette, keep, per_color, threshold, premultiplied=False, replace=True):
    colors=[(204,38,26),(26,191,204),(128,128,128),(0,255,0)]
    enabled=[1]*4
    if palette=='reverse':colors.reverse()
    elif palette=='single':colors=colors[1:2];enabled=[1]
    elif palette=='disabled_first':enabled[0]=0
    elif palette=='disabled_middle':enabled[1]=0
    elif palette=='duplicate':colors=[colors[1]]*4
    elif palette=='all_off':enabled=[0]*4
    elif palette=='last25':colors=[(10+i,20+i,30+i) for i in range(24)]+[colors[1]];enabled=[0]*24+[1]
    elif palette!='normal':raise ValueError(palette)
    values=owner.parameters(keep=keep,premultiplied=premultiplied,replace=replace,space=space,precision=precision,threshold=threshold,per_component=component,per_color=per_color,count=len(colors))
    for v in values:
        if v['slot']<24:continue
        i,off=divmod(v['slot']-24,8)
        if off==0:v['value']=enabled[i]
        elif off==2:v['color']=[255,*colors[i]]
        elif off in (4,5,6,7):v['value']=threshold if not per_color else min(1,threshold+0.025*(i%3))
    return values

def state_cases():
    palettes=('normal','reverse','single','disabled_first','disabled_middle','duplicate','all_off','last25')
    for space,component in ((3,False),(3,True),(4,True)):
        for precision in (1,2,3):
            for pi,palette in enumerate(palettes):
                for depth in ('PF8','PF16','PF32'):
                    for keep in (False,True):
                        threshold=(0,0.001,0.1,0.49,0.8,1)[pi%6]
                        yield {'fixture':{'id':'independent_lab_strip','width':13,'height':3},'depth':depth,
                               'label':f'lab{space}_component{component}_precision{precision}_{palette}_keep{keep}',
                               'parameters':controls(space,component,precision,palette,keep,pi%2==1,threshold,premultiplied=pi%3==2)}

def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def number(v):return struct.unpack('<f',struct.pack('<I',v))[0]
def set_threshold(case,threshold):
    c=copy.deepcopy(case)
    for v in c['parameters']:
        if v['slot'] in (2,9,10,11) or (v['slot']>=24 and (v['slot']-24)%8>=4):v['value']=threshold
    return c

def compare(exe,temp,c,native):
    results={}
    for route,name in ((0,'classic'),(1,'smart')):
        err,raw=owner.mac_render(exe,temp,c,route)
        results[name]={'error':err,'sha256':owner.sha(raw) if not err else None,'exact':err==0 and raw==native,
                       'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,
                       'first_differences':[{'offset':i,'aex':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:16]}
    return results

def capture(worker,temp,c,executables):
    native,frame,payload,close=owner.native_render(worker,temp,c);raw,rb=fixture(c['fixture'],c['depth']);ps={'PF8':4,'PF16':8,'PF32':16}[c['depth']]
    c.update(input_sha256=owner.sha(raw),packed_input_sha256=owner.sha(b''.join(raw[y*rb:y*rb+c['fixture']['width']*ps] for y in range(c['fixture']['height']))),
             actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,config_sha256=owner.sha(owner.config_text(c['parameters']).encode()),
             frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],results={name:compare(exe,temp,c,native) for name,exe in executables.items()})
    return c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--matrix',choices=('state','boundary'),required=True);args=ap.parse_args()
    source=owner.SOURCE.read_text();candidate=candidate_source(source);cases=[];searches=[];owner.fixture=fixture
    with tempfile.TemporaryDirectory(prefix='olmck_lab_state_') as td:
        temp=Path(td);executables={'production':owner.compile_public(temp/'production',source),'candidate':owner.compile_public(temp/'candidate',candidate)}
        if args.matrix=='state':
            for c in state_cases():
                cases.append(capture(args.worker,temp,c,executables))
                if len(cases)%48==0:print('LAB_STATE',len(cases),sum(c['results']['candidate']['classic']['exact'] for c in cases),flush=True)
        else:
            for space,component in ((3,False),(3,True),(4,True)):
                for precision in (1,2,3):
                    for depth in ('PF8','PF16','PF32'):
                        c={'fixture':{'id':'independent_lab_boundary','width':1,'height':1,'opaque':True,'rgb':[44,75,119]},'depth':depth,
                           'label':f'lab{space}_component{component}_precision{precision}',
                           'parameters':controls(space,component,precision,'single',True,False,0,replace=False)}
                        low,high=bits(0.0),bits(1.0);trace=[]
                        while high-low>1:
                            mid=(low+high)//2;t=number(mid);trial=set_threshold(c,t);raw,frame,payload,close=owner.native_render(args.worker,temp,trial)
                            hit=any(raw[:{'PF8':1,'PF16':2,'PF32':4}[depth]])
                            trace.append({'threshold_bits':mid,'threshold':t,'matched':hit,'actual_sha256':owner.sha(raw)})
                            if hit:high=mid
                            else:low=mid
                        searches.append({'label':c['label'],'depth':depth,'last_unmatched_bits':low,'first_matched_bits':high,'trace':trace})
                        for tb in range(max(0,low-2),min(bits(1.0),high+2)+1):
                            trial=set_threshold(c,number(tb));trial['threshold_bits']=tb;cases.append(capture(args.worker,temp,trial,executables))
                        print('LAB_BOUNDARY',c['label'],depth,number(low),number(high),flush=True)
    summary={build:{route:sum(c['results'][build][route]['exact'] for c in cases) for route in ('classic','smart')} for build in ('production','candidate')}
    report={'schema':'olmcolorkey.lab-state-boundary/1','matrix':args.matrix,'case_count':len(cases),'summary':summary,'source_sha256':owner.sha(source.encode()),'candidate_source_sha256':owner.sha(candidate.encode()),
            'dependencies_sha256':{str(Path(p).relative_to(owner.ROOT)):owner.sha(Path(p).read_bytes()) for p in (Path(__file__),Path(owner.__file__),owner.HARNESS,Path(__file__).with_name('colorkey_lab_mutation_candidate_20261001.py'))},
            'aex_sha256':owner.sha(owner.AEX.read_bytes()),'worker_sha256':owner.sha(args.worker.read_bytes()),'searches':searches,'cases':cases,
            'claims_not_made':['Candidate is temporary; no production Lab generalization','Local exported AEX with emulated imports; no native Windows UCRT/AE or Mac installed proof','No tolerance, final-byte correction or all-settings/geometry proof','Lab94 scalar omitted because frozen reference worker lacks atan2f','Resident payload is slot/type bound; per-frame parameter readback unavailable']}
    head=dict(report);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==report;print('RESULT',summary,flush=True)
if __name__=='__main__':main()
