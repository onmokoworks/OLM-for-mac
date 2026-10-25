"""Select two existing exact full-frame corpus witnesses per plugin, unchanged.

Corpus dimensions/depth/pixels/parameters are preserved; these are additional
witnesses, not resized stand-ins for the requested large default matrix.
"""
import base64
import hashlib
import json
from pathlib import Path
import zlib
import numpy as np
import tifffile

ROOT=Path(__file__).resolve().parents[2]
PLUGINS=['OLMBlur','ColorKeep','OLMColorKey','OLMDirectionalBlur','OLMDistanceGradation','OLMKiraKira','OLMSmoother2','OLMToonDilate','OLMRadialBlur','OLMSmoother']

def within_readback(p, prop):
    value=p['value']
    if isinstance(value,list): return True
    low,high=prop.get('min',float('-inf')),prop.get('max',float('inf'))
    if low<=value<=high: return True
    # The observed endpoint text can round a source f32 slider word. This
    # only selects candidates; the actual AE setter must still accept them.
    return p['kind']=='s' and np.float32(low)<=np.float32(value)<=np.float32(high)


def prepare(out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    bounds_path=ROOT/'orchestra/reports/A02e-evidence/priority-e2/build.json'
    measured=json.loads(bounds_path.read_text())
    bounds={row['plugin']:{p['index']:p for p in row.get('properties',[])}
            for row in measured['projects'][0]['items'] if row['plugin']!='control'}
    for plugin in PLUGINS:
        name='radialblur' if plugin=='OLMRadialBlur' else plugin.lower()
        candidates=[]
        for path in sorted((ROOT/'tests/fuzz_corpus'/name).rglob('*.json')):
            data=json.loads(path.read_text())
            case=data.get('case',{})
            route='classic' if name=='olmsmoother' else 'smart'
            if data.get('result',{}).get('routes',{}).get(route,{}).get('status')!='exact' or 'pixels_zlib_base64' not in data:
                continue
            if any(p['slot'] not in bounds[plugin] or
                not within_readback(p,bounds[plugin][p['slot']])
                for p in case['parameters']): continue
            w,h=case['geometry']
            if case.get('full_geometry',[w,h])!=[w,h] or case.get('downsample',[[1,1],[1,1]])!=[[1,1],[1,1]]:
                continue
            if any(case.get(k,[0,0,w,h])!=[0,0,w,h] for k in ('checkout_rect','request_rect','extent_hint')):
                continue
            raw=zlib.decompress(base64.b64decode(data['pixels_zlib_base64']))
            if hashlib.sha256(raw).hexdigest()!=data['input_sha256']:
                raise ValueError('Corpus hash mismatch: '+str(path))
            depth=case['depth']
            argb=np.frombuffer(raw,dtype={8:np.uint8,16:np.dtype('<u2'),32:np.dtype('<f4')}[depth]).reshape(h,w,4)
            if depth==16 and np.any(argb>32768): continue
            if depth==32 and (not np.all(np.isfinite(argb)) or np.any(argb<0) or np.any(argb>1)): continue
            candidates.append((min(w,h)<4,str(path),data,case,raw,argb))
        candidates.sort(key=lambda c:(c[0],c[1]))
        if len(candidates)<2:
            raise ValueError('Fewer than two exact full-frame SDR corpus witnesses: '+plugin)
        for index,(_,path,data,case,raw,argb) in enumerate(candidates[:2],1):
            if any(p['slot'] not in bounds[plugin] or
                not within_readback(p,bounds[plugin][p['slot']])
                for p in case['parameters']): continue
            w,h=case['geometry']; depth=case['depth']
            identity=plugin+'-corpus'+str(index)
            raw_path=out/(identity+'.argb');raw_path.write_bytes(raw)
            image=out/(identity+('.tif' if depth==8 else '.exr'))
            rgba=argb[:,:,[1,2,3,0]]
            if depth==8:
                tifffile.imwrite(image,rgba,photometric='rgb',extrasamples=['unassalpha'],metadata=None)
            else:
                import OpenEXR
                rgba=rgba.astype(np.float32)/(np.float32(32768) if depth==16 else np.float32(1))
                OpenEXR.File({}, {c:np.ascontiguousarray(rgba[:,:,i]) for i,c in enumerate('RGBA')}).write(str(image))
            rows.append(dict(depth=depth,width=w,height=h,path=str(image),raw=str(raw_path),plugin=plugin,
                identity=identity,corpus=str(Path(path).relative_to(ROOT)),corpus_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                parameters=case['parameters'],source_sha256=data['input_sha256'],file_sha256=hashlib.sha256(image.read_bytes()).hexdigest()))
    (out/'inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows
