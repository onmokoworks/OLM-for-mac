#!/usr/bin/env python3
"""Bounded transform-axis x non-neutral worker intersections."""
from __future__ import annotations
import hashlib, json, pickle, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

REPORT=ROOT/'refs/conformance/olmradialblur_transform_worker_intersections_actual_aex_20260811.json'
DOC=REPORT.with_suffix('.md'); CACHE=Path('/tmp/olmradialblur_transform_worker_intersections_20260811')
TUPLES={
 'A':dict(ox=0.,oy=0.,ratio=2.,angle=30.,quality=5.,repeat=1,edge=50,size=0.,nv=0.,nt=1),
 'B':dict(ox=0.,oy=0.,ratio=1.,angle=0.,quality=3.,repeat=0,edge=0,size=0.,nv=100.,nt=2),
 'C':dict(ox=-.25,oy=-1/6,ratio=1.,angle=0.,quality=5.,repeat=1,edge=0,size=50.,nv=0.,nt=1),
}
CELLS=[(m,d,t) for m in ('zoom','rotation') for d in (8,16,32) for t in TUPLES]
def sha(x):return hashlib.sha256(x).hexdigest()

def configure(cell):
 m,d,t=cell; q=TUPLES[t]; target,frame,rb,cx,cy=base.configure((m,d,32,18,q['ox'],q['oy'],1.))
 if m=='rotation':
  fixture=target.base if d==32 else target
  fixture.FIXTURE_CENTER_X,fixture.FIXTURE_CENTER_Y=cx,cy
  fixture.FIXTURE_QUALITY=q['quality'];fixture.FIXTURE_RATIO=q['ratio'];fixture.FIXTURE_ANGLE_DEG=q['angle']
  fixture.FIXTURE_OUTER_STRENGTH=4;fixture.FIXTURE_OUTER_EDGE_FADE=q['edge']
  fixture.FIXTURE_INNER_STRENGTH=0;fixture.FIXTURE_INNER_EDGE_FADE=0
  fixture.FIXTURE_SIZE_VARIATION=q['size'];fixture.FIXTURE_NOISE_VARIATION=q['nv'];fixture.FIXTURE_NOISE_TYPE=q['nt']
  fixture.FIXTURE_SEED=1;fixture.FIXTURE_NOISE_OFFSET=0.;fixture.FIXTURE_THICKNESS=10.
  fixture.CAPTURE_NOISE_INTERNALS=q['nv']!=0.;fixture.CAPTURE_EDGE_INTERNALS=q['edge']!=0.
 module=target.fixture.m4 if m=='zoom' else (target.base.m4 if d==32 else target.m4)
 old=module.install_reader_detours
 def install(loader,p):
  p=dict(p);p.update({'Center':(cx,cy),'Ratio':q['ratio'],'Angle':int(round(q['angle']*65536.0)),'Quality':q['quality'],
   'Repeat Border':q['repeat'],'Outer Strength':4,'Outer Edge Fade':q['edge'],'Outer Offset Mode':1,
   'Outer Offset':0,'Inner Strength':0,'Inner Edge Fade':0,'Inner Offset Mode':1,'Inner Offset':0,
   'Size Variation':q['size'],'Noise Variation':q['nv'],'Noise Type':q['nt'],'Noise Layer':0,
   'Seed':1,'Noise Offset':0.,'Thickness':10.,'Brightness Gain':1.})
  return old(loader,p)
 module.install_reader_detours=install
 return target,frame,rb,cx,cy

def capture(cell):return configure(cell)[0].actual_aex()
def isolated(cell):
 CACHE.mkdir(parents=True,exist_ok=True);p=CACHE/('_'.join(map(str,cell))+'.pkl')
 if not p.exists():
  x=p.with_suffix('.tmp');subprocess.run([sys.executable,__file__,'--capture',*map(str,cell),str(x)],check=True);x.replace(p)
 return pickle.loads(p.read_bytes())

def production(cell,expected):
 m,d,t=cell;q=TUPLES[t];target,frame,rb,cx,cy=configure(cell);oldc=base.configure;oldw=Path.write_text
 def conf(_):return target,(lambda seed=False:frame(seed)),rb,cx,cy
 def write(path,data,*a,**kw):
  if path.name=='p.cpp':
   marker='i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1.0;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;'
   repl=(f"i.outer_strength=4;i.outer_edge_fade={q['edge']};i.outer_offset_mode=1;i.outer_offset=0;"
    f"i.inner_strength=0;i.inner_edge_fade=0;i.inner_offset_mode=1;i.inner_offset=0;"
    f"i.repeat_border={q['repeat']};i.ratio={q['ratio']};i.angle_deg={q['angle']};i.quality={q['quality']};"
    f"i.brightness_gain=1;i.size_variation={q['size']};i.noise_variation={q['nv']};i.noise_type={q['nt']};"
    "i.seed=1;i.noise_offset=0;i.thickness=10;i.comp_width=W;i.comp_height=H;")
   if marker not in data:raise RuntimeError('info marker absent')
   data=data.replace(marker,repl,1)
  return oldw(path,data,*a,**kw)
 base.configure=conf;Path.write_text=write
 try:return base.production((m,d,32,18,0.,0.,1.),expected)
 finally:base.configure=oldc;Path.write_text=oldw

def main():
 with ThreadPoolExecutor(max_workers=6) as p:actual=dict(zip(CELLS,p.map(isolated,CELLS)))
 rows=[]
 for c in CELLS:
  try:prod=production(c,actual[c]);error=None
  except Exception as e:prod={};error=repr(e)
  names=('pre_blur','post_blur','output') if c[0]=='zoom' else (
   ('polar','source_scalar','prepass_alpha','accum','max_alpha','final_rgba','coordinates','output')
   if c[2]=='A' else
   ('polar','source_scalar','accum','max_alpha','final_rgba','coordinates','output'))
  matches={n:prod.get(n)==actual[c].get(n) for n in names};exact=all(matches.values())
  rows.append({'mode':c[0],'depth':c[1],'tuple':c[2],'params':TUPLES[c[2]],'exact':exact,'matches':matches,'production_error':error,'actual_sha256':{n:sha(actual[c][n]) for n in names if n in actual[c]}})
  print(c,exact,matches,error,flush=True)
 ok=all(r['exact'] for r in rows)
 REPORT.write_text(json.dumps({'kind':'olmradialblur_transform_worker_intersections_actual_aex_20260811','status':'18/18 exact' if ok else 'mismatch','scope':'32x18 PF8/PF16/PF32 Zoom/Rotation x three enumerated transform/worker tuples','tuples':TUPLES,'cases':rows,'boundary':'Only the 18 enumerated cells are admitted. Other cross-products, geometry, inner worker, brightness, Type3/layer and AE-host behavior remain fail-closed.'},indent=2,sort_keys=True)+'\n')
 DOC.write_text('# OLM RadialBlur transform axes × worker coefficients — 2026-08-11\n\nStatus: **'+('18/18 exact' if ok else 'mismatch')+'**\n')
 return 0 if ok else 1

if __name__=='__main__':
 if len(sys.argv)==6 and sys.argv[1]=='--capture':
  c=(sys.argv[2],int(sys.argv[3]),sys.argv[4]);Path(sys.argv[5]).write_bytes(pickle.dumps(capture(c)));raise SystemExit(0)
 raise SystemExit(main())
