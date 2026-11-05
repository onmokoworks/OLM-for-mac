#!/usr/bin/env python3
"""Replay an OLM live world capture with the retained AEXCompat session worker.
Exit 0 exact, 1 mismatch, 2 unsupported capture or worker failure. No tolerances.
Padding is retained in capture; comparisons address active ARGB sample words.
"""
import argparse, hashlib, json, math, os, struct, sys, time, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import command
from adapters.public import messages


def packed_rows(path, world):
    stride=world['rowbytes']; n=world['width']*4*(world['depth']//8)
    if stride<n or path.stat().st_size!=stride*world['height']:
        raise ValueError('invalid world byte length/rowbytes: '+str(path))
    with path.open('rb') as source:
        for _ in range(world['height']):
            yield source.read(n)
            source.seek(stride-n,1)


def sha_file(path):
    with path.open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()


def compare(expected, actual, depth, width):
    if len(expected)!=len(actual): raise ValueError('output length differs')
    unit=depth//8; count=0; pixel_count=0; last_pixel=-1; first=None; maximum=0
    for i in range(0,len(expected),unit):
        a,b=expected[i:i+unit],actual[i:i+unit]
        if a==b:continue
        count+=1; pixel=i//(4*unit)
        if pixel!=last_pixel:pixel_count+=1;last_pixel=pixel
        if first is None:first={'x':pixel%width,'y':pixel//width,'channel':'ARGB'[(i//unit)%4],
                              'aex_word_hex':a.hex(),'mac_word_hex':b.hex()}
        if depth==32:
            x,y=struct.unpack('<f',a)[0],struct.unpack('<f',b)[0]
            diff=abs(x-y) if math.isfinite(x) and math.isfinite(y) else None
        else:diff=abs(int.from_bytes(a,'little')-int.from_bytes(b,'little'))
        if diff is None: maximum=None
        elif maximum is not None:maximum=max(maximum,diff)
    return {'status':'exact' if not count else 'mismatch','different_words':count,
            'different_pixels':pixel_count,'max_diff':maximum,'first':first,
            'comparison':'active ARGB words, bit-exact; row padding excluded',
            'aex_sha256':hashlib.sha256(expected).hexdigest(),'mac_sha256':hashlib.sha256(actual).hexdigest()}


def replay(capture, scratch, worker, main, timeout=600):
    m=json.loads((capture/'capture.json').read_text())
    if m['schema']!=1 or m['render_error']:raise ValueError('incomplete/failed capture')
    names={'OLMDistanceGradation':'DistanceGradation','OLMKiraKira':'OLMKiraKira'}
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
    scratch=Path(tempfile.mkdtemp(prefix='replay-',dir=scratch))
    ip,op=scratch/'input.raw',scratch/'aex-output.raw'
    with ip.open('wb') as dest:
        for row in packed_rows(capture/'input.raw',w):dest.write(row)
    op.unlink(missing_ok=True)
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
    float_colors={}
    for slot,c in colors.items():
        if slot not in raw_colors:raise ValueError('missing raw color')
        derived=[struct.unpack('<f',struct.pack('<f',x/255.0))[0] for x in raw_colors[slot]]
        if c!=derived:float_colors[str(slot)]=c
    if float_colors:
        metadata=worker.parent/'build.json'
        if not metadata.exists() or json.loads(metadata.read_text()).get('capability')!='S02-float-colors-v1':
            raise ValueError('independent float colors require --worker ~/.cache/olm-emu/worker-S02-F53/aex-guest-worker')
    request={'v':4,'type':'render_frame','frame_index':0,'current_time':{
        'value':h['current_time'],'scale':h['time_scale'],'step':h['time_step'],'total':h.get('total_time') or max(1,h['current_time']+h['time_step'])},
        'parameters':'v4|'+';'.join(encoded)}
    data=json.dumps(request,allow_nan=False).encode()
    rect=m.get('request_rect',[0,0,w['width'],w['height']])
    argv=[worker,'session',aex,ip,op,h['width'],h['height'],h['time_scale'],
          '--pixel-format',{8:'argb8',16:'argb16',32:'argb32f'}[depth],
          '--fixture-render-path',route,'--negotiate-output','1','--rowbytes-pad',pad,
          '--extent-hint',','.join(map(str,w['extent_hint']))]
    if h.get('pixel_aspect') and all(h['pixel_aspect']):argv+=['--pixel-aspect','/'.join(map(str,h['pixel_aspect']))]
    if route=='smart':argv+=['--request-rect',','.join(map(str,rect))]
    for axis,ratio in zip(('x','y'),h['downsample']):argv+=['--downsample-'+axis,'/'.join(map(str,ratio))]
    env={k:v for k,v in os.environ.items() if not k.startswith(('OLM','DBLUR','COLORKEEP'))}
    if float_colors:env['OLM_FLOAT_COLOR_VALUES']=json.dumps(float_colors,allow_nan=False)
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
    if not result['guards_intact'] or result['checksum']!=sha_file(op):raise ValueError('worker guard/checksum failed')
    if result['rect']!=m['output_rect']:raise ValueError('negotiated output rectangle differs from capture')
    report={'status':'exact','different_words':0,'different_pixels':0,'max_diff':0,'first':None,
            'comparison':'active ARGB words, bit-exact; row padding excluded'}
    mac_hash=hashlib.sha256()
    with op.open('rb') as oracle:
        for y,actual in enumerate(packed_rows(capture/'output.raw',o)):
            mac_hash.update(actual)
            row=compare(oracle.read(len(actual)),actual,depth,o['width'])
            for key in ('different_words','different_pixels'):report[key]+=row[key]
            if report['first'] is None and row['first'] is not None:
                report['first']=dict(row['first'],y=y)
            report['max_diff']=None if report['max_diff'] is None or row['max_diff'] is None else max(report['max_diff'],row['max_diff'])
        if oracle.read(1):raise ValueError('AEX output is longer than captured output')
    if report['different_words']:report['status']='mismatch'
    report.update(artifacts=str(scratch),aex_sha256=sha_file(aex),worker_sha256=sha_file(worker),capture_build=m['build'],
                  aex_output_sha256=sha_file(op),mac_output_sha256=mac_hash.hexdigest())
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
