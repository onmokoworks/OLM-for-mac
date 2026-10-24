#!/usr/bin/env python3
"""Measure selected Blur PF8 sampled sizes against a 10-second oracle deadline."""
import json,time
from pathlib import Path
from types import SimpleNamespace
from adapters.olmblur import Adapter
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/F52-oracle-downsample-geometry/limits'
def main():
    S.mkdir(parents=True,exist_ok=True)
    a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52-geom/aex-guest-worker',max_size=256,case_timeout=10))
    a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S));rows=[]
    tile=b''.join(bytes([255,i,(i*31)%256,(i*53)%256]) for i in range(256))
    for w,h in [(32,24),(64,48),(128,96),(256,192),(480,270),(960,540),(1920,1080)]:
        case=dict(geometry=[w,h],full_geometry=[w*2,h*2],downsample=[[1,2],[1,2]],depth=8,parameters=a.defaults(w,h),pixels=(tile*((w*h+255)//256))[:w*h*4],input_padding=0,output_padding=0)
        t=time.monotonic();status,raw=a.oracle(case,S,t+15,'smart')
        row=dict(world=[w,h],full=case['full_geometry'],seconds=time.monotonic()-t,status=status,bytes=len(raw));rows.append(row);print(json.dumps(row),flush=True)
        (S/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
        if status['status']=='budget':break
if __name__=='__main__':main()
