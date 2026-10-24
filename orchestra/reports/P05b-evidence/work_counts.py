#!/usr/bin/env python3
"""Source-derived work counts for P00b corpus05, not measured CPU timings.

P00 host supplies fixed pixel Point parameters unchanged at all downsample sizes.
Smart center conversion cancels equal X/Y downsample; comp size becomes input size.
RenderRotationTyped / ZoomRadiusBoundsAEX then construct this polar plane.
"""
import json, math, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
case=json.loads((ROOT/'tests/fuzz_corpus/radialblur/C45_seed1_case000108.json').read_text())['case']
p={v['slot']:v['value'] for v in case['parameters']}
cx,cy=p[2];quality=f(p[20]);angles=int(f(360/f(1/quality)))
assert p[22]>0 and cx>0 and cy>0
rows=[]
for w,h in [(240,135),(480,270),(1920,1080),(3840,2160)]:
    assert cx<w/2 and cy<h/2
    dx=f(w-f(cx));dy=f(h-f(cy))
    radii=int(f(math.sqrt(f(f(dx*dx)+f(dy*dy)))))+3
    cells=radii*angles
    rows.append(dict(width=w,height=h,radii=radii,angles=angles,polar_cells=cells,
        rgba_calls=cells,scalar_calls=2*cells,rgba_calls_per_output_pixel=cells/(w*h),
        sin_hot_calls_before=2*radii*(angles-1),sin_hot_calls_after=2*(angles-1)))
print(json.dumps(dict(kind='source-derived counts; scatter taps are data-dependent',rows=rows),indent=2))
