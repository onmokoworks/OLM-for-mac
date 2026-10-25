#!/usr/bin/env python3
"""Capture original-AEX UI sessions, sequentially; never interpret failures as traces."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
THEME = {'2': [60000]*3, '7': [18000]*3, '8': [26000]*3, '42': [0]*3}

def event(kind, x=0, y=0, **kw):
    value = dict(event=kind, slot=14, area=2, frame=[30,40,340,210], x=x+30, y=y+40,
                clicks=1, last=False, context=1, window_type=2, theme=THEME,
                picker_argb_bits=None)
    value.update(kw)
    return value

def sessions():
    yield 'DistanceGradation-update', 'DistanceGradation', dict(updates=[[], ['p@9=4','p@2=2','p@5=2','p@6=1','p@11=2'], ['p@2=3','p@9=1','p@5=1','p@6=0','p@11=1']])
    yield 'KiraKira-update', 'OLMKiraKira', dict(updates=[[],[f'p@{s}=1' for s in [13,19,25,31,37]],[f'p@{s}=0' for s in [13,19,25,31,37]]])
    yield 'Blur-update', 'OLMBlur', dict(updates=[[],[]])
    yield 'ColorKeep-update', 'ColorKeep', dict(updates=[[f'p@1={v}'] for v in [1,2,99,100]])
    yield 'DirectionalBlur-update', 'OLMDirectionalBlur', dict(updates=[[f'p@16={v}'] for v in [1,2,3]])
    yield 'Smoother2-update', 'OLMSmoother2', dict(updates=[[f'p@1={key}',f'p@8={mode}',f'p@10={n}'] for key in [0,1] for mode in [1,2,3] for n in [0,1,5]])
    yield 'RadialBlur-update', 'OLMRadialBlur', dict(updates=[[f'p@25={noise}',f'p@1={kind}',f'p@5={outer}',f'p@11={inner}'] for noise in [1,2,3] for kind in [1,2] for outer in [1,2,3] for inner in [1,2,3]])
    yield 'ColorKey-update', 'OLMColorKey', dict(updates=[[f'p@7={p}',f'p@8={c}',f'p@23={r}',f'p@22={n}'] for p in [0,1] for c in [0,1] for r in [0,1] for n in [0,1,24,25]] + [[f'p@24={use}',f'p@25={replace}',f'p@216={use}',f'p@217={replace}','p@22=25','p@23=1'] for use in [0,1] for replace in [0,1]])
    yield 'KiraKira-draw-click', 'OLMKiraKira', dict(events=[event(4),event(2,100,30),event(4),event(3,130,30,last=True),event(4)])
    for y in [75,76]:
        yield f'KiraKira-drag-delete-{y-55}', 'OLMKiraKira', dict(events=[event(4),event(2,10,65),event(3,50,y),event(4),event(3,50,y,last=True),event(4)])
    for accept in [False,True]:
        yield 'KiraKira-picker-'+('accept' if accept else 'cancel'), 'OLMKiraKira', dict(events=[event(4),event(2,10,65,clicks=2,picker_argb_bits=[1065353216,1048576000,1056964608,1061158912] if accept else None),event(4)])
    def button(x,y,slot=14):
        return [event(2,x,y,slot=slot),event(3,x,y,slot=slot,last=True)]
    yield 'KiraKira-copy-paste', 'OLMKiraKira', dict(events=[event(4),event(2,100,30),event(3,100,30,last=True)]+button(250,45)+[event(4,slot=20)]+button(250,70,20)+[event(4,slot=20)])
    yield 'KiraKira-randomize-flip', 'OLMKiraKira', dict(initial_state_u32={str(0x1824968):123456789},events=[event(4)]+button(70,90)+button(70,90)+button(170,90)+[event(4)])
    yield 'KiraKira-presets', 'OLMKiraKira', dict(events=[event(4),event(2,260,15),event(4),event(3,260,150),event(4),event(3,260,150,last=True),event(2,260,38),event(3,260,38,last=True),event(4)])
    yield 'KiraKira-context-negative', 'OLMKiraKira', dict(events=[event(4,area=1),event(4,slot=13)])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--worker',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--only',action='append')
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    worker_hash=hashlib.sha256(args.worker.read_bytes()).hexdigest()
    (args.output/'capture.json').write_text(json.dumps({'worker_sha256':worker_hash},sort_keys=True)+'\n')
    rows=[]
    for name,plugin,request in sessions():
        if args.only and name not in args.only: continue
        request={'current_time':7,'time_scale':24,**request}
        request_path=args.output/(name+'.request.json')
        request_path.write_text(json.dumps(request,sort_keys=True,indent=2)+'\n')
        output=args.output/(name+'.jsonl'); log=args.output/(name+'.log')
        with output.open('w') as out, log.open('w') as err:
            proc=subprocess.run([str(args.worker.resolve()),'ui-session',str(MAIN/'plugins_2025'/f'{plugin}.aex'),str(request_path.resolve())],stdout=out,stderr=err,env={**os.environ,'TMPDIR':str(args.output.resolve())},timeout=180)
        rows.append({'name':name,'returncode':proc.returncode,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'events':sum(1 for _ in output.open())})
        print(name,proc.returncode,rows[-1]['events'],flush=True)
    (args.output/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    return int(any(r['returncode'] for r in rows))
if __name__=='__main__': raise SystemExit(main())
