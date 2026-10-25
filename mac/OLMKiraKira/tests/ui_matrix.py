#!/usr/bin/env python3
"""Capture additional natural UI sequences using the immutable U03 worker."""
import gzip, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
WORKER=Path.home()/'.cache/olm-emu/worker-U03-ui/aex-guest-worker'
ORIGINAL=Path('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMKiraKira.aex')
OUT=HERE/'ui_witnesses'
SCRATCH=ROOT/'orchestra/state/U02b-kirakira-ui-vs-original'
THEME={'7':[12345,23456,34567],'8':[54321,43210,32109],'2':[65535,54321,43210],'42':[123,456,789]}
def event(kind,x=0,y=0,slot=14,clicks=1,last=False):
    return dict(event=kind,x=x,y=y,slot=slot,clicks=clicks,last=last,area=2,context=1,window_type=2,frame=[0,0,310,170],theme=THEME,picker_argb_bits=None)
def click(x,y,slot=14,clicks=1):return [event(2,x,y,slot,clicks),event(3,x,y,slot,last=True)]
def draw(slot=14):return event(4,slot=slot)
def sessions():
    e=[draw()]
    for x in [202,159,10]:e += [event(2,x,65),event(3,x,76,last=True),draw()]
    e+=click(100,30)+[draw()]
    # Independently exercise marker endpoints x-5/x+5 and just outside.
    for dx in [-6,-5,5,6]:e += [event(2,100+dx,65,clicks=2),draw()]
    for y in [59,60,70,71]:e += [event(2,100,y,clicks=2),draw()]
    for x in range(10,160,10):e+=click(x,30)
    e+=[draw()]+click(190,30)+[draw()]
    yield 'KiraKira-count-boundaries',e
    e=[]
    for slot in [14,20,26,32,38]:
        e += [event(9,250,45,slot),draw(slot)]+click(250,45,slot)+[draw(slot)]
    yield 'KiraKira-five-slots-hover',e
    e=[draw()]+click(260,15)+[draw()]+click(260,38)+[draw()]+click(260,15)+[draw()]
    # Menu row zero selects the last valid preset after maximum scroll.
    e += [event(2,260,38),event(3,260,1000),draw(),event(3,260,1000,last=True)]
    e += click(260,38)+[draw()]
    yield 'KiraKira-menu-last',e

def main():
    OUT.mkdir(exist_ok=True);SCRATCH.mkdir(parents=True,exist_ok=True);entries=[]
    for name,events in sessions():
        request=dict(current_time=7,time_scale=24,events=events)
        path=OUT/(name+'.request.json');path.write_text(json.dumps(request,indent=2)+'\n')
        raw=SCRATCH/(name+'.original.jsonl')
        with raw.open('w') as o,(SCRATCH/(name+'.original.stderr')).open('w') as err:
            p=subprocess.run([str(WORKER),'ui-session',str(ORIGINAL),str(path)],stdout=o,stderr=err,env=dict(os.environ,TMPDIR=str(SCRATCH)))
        rows=sum(1 for _ in raw.open());print(name,p.returncode,rows,flush=True)
        assert p.returncode==0 and rows==len(events)
        destination=OUT/(name+'.jsonl.gz')
        with raw.open('rb') as source,destination.open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',filename='',mtime=0) as compressed:
            import shutil
            shutil.copyfileobj(source,compressed)
        entries.append(dict(name=name,dispatches=rows,request_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),compressed_sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    (OUT/'manifest.json').write_text(json.dumps(dict(worker_sha256=hashlib.sha256(WORKER.read_bytes()).hexdigest(),original_sha256=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),sessions=entries),indent=2)+'\n')
if __name__=='__main__':main()
