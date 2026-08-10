#!/usr/bin/env python3
"""Read-only probe: Rotation Size Variation, centered 32x18, all depths."""
from __future__ import annotations
import hashlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS=[(d,s) for d in (8,16,32) for s in (1.0,25.0,100.0)]
OUT=ROOT/'refs/conformance/olmradialblur_rotation_size_variation_32x18_actual_aex_20260811.json'

def configure(cell):
    depth,size=cell
    synthetic=("rotation",depth,32,18,0.0,0.0,1.0)
    target,frame,rb,cx,cy=base.configure(synthetic)
    fixture=target.base if depth==32 else target
    fixture.FIXTURE_SIZE_VARIATION=size
    fixture.CAPTURE_NOISE_INTERNALS=True
    if depth==32: target.SIZE_VARIATION=size
    return synthetic,target

def capture(cell):
    _,target=configure(cell)
    return target.actual_aex()

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix='radial_size_rotation_') as raw:
        p=Path(raw)/'a.pkl'
        subprocess.run([sys.executable,__file__,'--capture',str(cell[0]),str(cell[1]),str(p)],check=True)
        return pickle.loads(p.read_bytes())

def production(cell, expected):
    synthetic,_=configure(cell); _,size=cell
    original_write=Path.write_text
    def write_text(path,data,*args,**kwargs):
        if path.name=='p.cpp':
            needle='i.noise_type=1;i.seed=1;i.thickness=10;'
            if needle not in data: raise RuntimeError('info marker absent')
            data=data.replace(needle,f'i.size_variation={size};'+needle,1)
        return original_write(path,data,*args,**kwargs)
    Path.write_text=write_text
    try: return base.production(synthetic,expected)
    finally: Path.write_text=original_write

def floats(raw): return struct.unpack('<%df'%(len(raw)//4),raw)
def firstdiff(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return i,x,y
    return None

def main():
    with ThreadPoolExecutor(max_workers=6) as pool: actuals=dict(zip(CELLS,pool.map(isolated,CELLS)))
    rows=[]
    for cell in CELLS:
        actual=actuals[cell]; prod=production(cell,actual)
        planes=('polar','source_scalar','accum','max_alpha','final_rgba','coordinates','output')
        matches={p:(p in actual and p in prod and actual[p]==prod[p]) for p in planes}
        sf=floats(actual['size_factor'])
        span=(struct.unpack('<%di'%(len(actual['source_span'])//4),actual['source_span'])
              if 'source_span' in actual else ())
        row={'depth':cell[0],'size_variation':cell[1],'matches':matches,
             'size_factor':{'count':len(sf),'min':min(sf),'max':max(sf),'unique':sorted(set(sf))[:32],'unique_count':len(set(sf))},
             'span':({'min':min(span),'max':max(span),'unique':sorted(set(span))} if span else None),
             'first_diffs':{p:firstdiff(actual[p],prod[p]) for p in planes if p in actual and p in prod and actual[p]!=prod[p]},
             'hashes':{p:hashlib.sha256(actual[p]).hexdigest() for p in (*planes,'source_size_factor','source_span') if p in actual}}
        rows.append(row);print(cell,matches,row['size_factor'],row['span'],flush=True)
    assert all(all(row['matches'].values()) for row in rows), rows
    OUT.write_text(json.dumps({'kind':'olmradialblur_rotation_size_variation_32x18_actual_aex_20260811',
        'scope':'Rotation 32x18 centered Outer4 Inner0 neutral tuple; PF8/PF16/PF32; Size Variation 1/25/100.',
        'status':'18-cell parent matrix Rotation half: 9/9 internal planes and padded output byte exact',
        'cells':rows},indent=2,sort_keys=True)+'\n')

if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='--capture':
        cell=(int(sys.argv[2]),float(sys.argv[3]));Path(sys.argv[4]).write_bytes(pickle.dumps(capture(cell)));raise SystemExit(0)
    main()
