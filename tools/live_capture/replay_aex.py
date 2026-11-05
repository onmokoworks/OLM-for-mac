#!/usr/bin/env python3
"""Replay an OLM live world capture with the retained AEXCompat session worker.
Exit 0 exact, 1 mismatch, 2 unsupported capture or worker failure. No tolerances.
Padding is retained in capture; comparisons address active ARGB sample words.
"""
import argparse, hashlib, json, math, os, struct, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import command
from adapters.public import messages


def tight(path, world):
    raw=path.read_bytes(); stride=world['rowbytes']; n=world['width']*4*(world['depth']//8)
    if stride<n or len(raw)!=stride*world['height']:
        raise ValueError('invalid world byte length/rowbytes: '+str(path))
    return b''.join(raw[y*stride:y*stride+n] for y in range(world['height']))


def compare(expected, actual, depth, width):
    if len(expected)!=len(actual): raise ValueError('output length differs')
    unit=depth//8; count=0; pixels=set(); first=None; maximum=0
    for i in range(0,len(expected),unit):
        a,b=expected[i:i+unit],actual[i:i+unit]
        if a==b:continue
        count+=1; pixel=i//(4*unit);pixels.add(pixel)
        if first is None:first={'x':pixel%width,'y':pixel//width,'channel':'ARGB'[(i//unit)%4],
                              'aex_word_hex':a.hex(),'mac_word_hex':b.hex()}
        if depth==32:
            x,y=struct.unpack('<f',a)[0],struct.unpack('<f',b)[0]
            diff=abs(x-y) if math.isfinite(x) and math.isfinite(y) else None
        else:diff=abs(int.from_bytes(a,'little')-int.from_bytes(b,'little'))
        if diff is None: maximum=None
        elif maximum is not None:maximum=max(maximum,diff)
    return {'status':'exact' if not count else 'mismatch','different_words':count,
            'different_pixels':len(pixels),'max_diff':maximum,'first':first,
            'comparison':'active ARGB words, bit-exact; row padding excluded',
            'aex_sha256':hashlib.sha256(expected).hexdigest(),'mac_sha256':hashlib.sha256(actual).hexdigest()}


def replay(capture, scratch, worker, main, timeout=600):
    m=json.loads((capture/'capture.json').read_text())
    if m['schema']!=1 or m['render_error']:raise ValueError('incomplete/failed capture')
    names={'OLMDistanceGradation':'DistanceGradation','OLMKiraKira':'OLMKiraKira'}
    # Original KiraKira filename differs from match name.
    names['OLMKiraKira']='KiraKira'
    aex=main/'plugins_2025'/(names[m['plugin']]+'.aex')
    w,o,h=m['input'],m['output'],m['host']; depth=w['depth']; route=m['route']
    if depth not in (8,16,32) or o['depth']!=depth:raise ValueError('unsupported depth')
    if h['field'] not in (None,0):raise ValueError('worker cannot reproduce field rendering')
    if h['source_origin']!=[0,0]:raise ValueError('worker cannot reproduce pre-effect source origin')
    if w['origin']!=[0,0]:raise ValueError('worker cannot reproduce this input origin')
    if o['origin']!=h['output_origin']:raise ValueError('world/output origin disagreement')
    pad=w['rowbytes']-w['width']*4*(depth//8)
    if o['rowbytes']-o['width']*4*(depth//8)!=pad:
        raise ValueError('worker requires equal input/output padding; capture preserved for a future transport')
    if [math.ceil(h['width']*h['downsample'][0][0]/h['downsample'][0][1]),
        math.ceil(h['height']*h['downsample'][1][0]/h['downsample'][1][1])]!=[w['width'],w['height']]:
        raise ValueError('worker requires a full sampled input world')
    scratch.mkdir(parents=True,exist_ok=True)
    ip,op=scratch/'input.raw',scratch/'aex-output.raw'
    ip.write_bytes(tight(capture/'input.raw',w));op.unlink(missing_ok=True)
    encoded=[]; colors={}; raw_colors={}
    default_ramp=[[0.,1.,1.,0.,0.],[struct.unpack('<f',struct.pack('<f',.78))[0],1.,1.,struct.unpack('<f',struct.pack('<f',.651))[0],0.],[1.,1.,1.,1.,1.]]
    for p in m['parameters']:
        kind=p['kind'];v=p['value'];slot=p['slot']
        if kind=='color_float':colors[slot]=v;continue
        if kind=='ramp':
            if v!=default_ramp:raise ValueError('custom ramp transport is unsupported; captured ramp is retained')
            continue
        if kind=='c':raw_colors[slot]=v
        wire={'c':'argb8','a':'angle'}.get(kind,'f64')
        encoded.append(f"param_{slot}@{slot}:{wire}="+(','.join(map(str,v)) if isinstance(v,list) else str(v)))
    # The standard worker reconstructs PF_ColorParamSuite floats from byte colors.
    # Reject an independent AE float color rather than silently quantizing it.
    for slot,c in colors.items():
        if slot not in raw_colors:raise ValueError('missing raw color')
        derived=[struct.unpack('<f',struct.pack('<f',x/255.0))[0] for x in raw_colors[slot]]
        if c!=derived:raise ValueError(f'independent float color at slot {slot} requires S02 float-color transport')
    request={'v':4,'type':'render_frame','frame_index':0,'current_time':{
        'value':h['current_time'],'scale':h['time_scale'],'step':h['time_step'],'total':max(1,h['current_time']+h['time_step'])},
        'parameters':'v4|'+';'.join(encoded)}
    data=json.dumps(request,allow_nan=False).encode()
    rect=m.get('request_rect',[0,0,w['width'],w['height']])
    argv=[worker,'session',aex,ip,op,h['width'],h['height'],h['time_scale'],
          '--pixel-format',{8:'argb8',16:'argb16',32:'argb32f'}[depth],
          '--fixture-render-path',route,'--negotiate-output','1','--rowbytes-pad',pad,
          '--extent-hint',','.join(map(str,w['extent_hint']))]
    if route=='smart':argv+=['--request-rect',','.join(map(str,rect))]
    for axis,ratio in zip(('x','y'),h['downsample']):argv+=['--downsample-'+axis,'/'.join(map(str,ratio))]
    env={k:v for k,v in os.environ.items() if not k.startswith(('OLM','DBLUR','COLORKEEP'))}
    env.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch))
    status,out,err=command(argv,data=struct.pack('<I',len(data))+data,timeout=timeout,deadline=time.monotonic()+timeout,env=env)
    (scratch/'worker.stderr').write_bytes(err)
    (scratch/'worker.messages').write_bytes(out)
    (scratch/'command.json').write_text(json.dumps(list(map(str,argv)),indent=2))
    if status['status']!='ok':raise ValueError('worker failed: '+json.dumps(status)+'; see worker.stderr')
    decoded=messages(out)
    frame=next(x for x in decoded if x['type']=='frame_done')
    close=next(x['close'] for x in decoded if x['type']=='session_closed')
    if frame['status']!='ok' or frame['render_error'] or not close['session_clean'] or close['unsupported_suite_calls'] or close['dropped_unsupported_suite_calls']:
        raise ValueError('worker/session did not complete cleanly')
    result=frame['output']
    expected=op.read_bytes()
    if not result['guards_intact'] or result['checksum']!=hashlib.sha256(expected).hexdigest():raise ValueError('worker guard/checksum failed')
    if result['rect']!=m['output_rect']:raise ValueError('negotiated output rectangle differs from capture')
    report=compare(expected,tight(capture/'output.raw',o),depth,o['width'])
    report.update(worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),aex_sha256=hashlib.sha256(aex.read_bytes()).hexdigest(),capture_build=m['build'])
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--worker',type=Path,default=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker')
    p.add_argument('--main',type=Path,default=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT)
    p.add_argument('--timeout',type=float,default=600)
    args=p.parse_args()
    try:r=replay(args.capture.resolve(),args.scratch.resolve(),args.worker,args.main,args.timeout)
    except Exception as e:r={'status':'unsupported_or_error','error':str(e)}
    print(json.dumps(r,indent=2));return {'exact':0,'mismatch':1}.get(r['status'],2)
if __name__=='__main__':sys.exit(main())
