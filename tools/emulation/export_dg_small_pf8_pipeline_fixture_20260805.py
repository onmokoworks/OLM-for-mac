#!/usr/bin/env python3
import hashlib,json,struct
from pathlib import Path
import numpy as np
from export_dg_fieldgen_fixture import run_aex_fieldgen,sha256_file
from test_dg_fieldgen_p1b import make_mask
from test_dg_pf8_compose_store_differential_20260716 import build_world8,CALLBACK
from test_dg_compose import make_loader,alloc_refcon
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).parent/'fixtures/distancegradation_pipeline_pf8_17x11_threshold4_linear_inside'; AEX=ROOT/'plugins_2025/DistanceGradation.aex'
def main():
 assert not OUT.exists();OUT.mkdir();w,h=17,11;mask=make_mask(w,h);field,trace=run_aex_fieldgen(mask,4,0);fw=np.rint(np.clip(field,0,1)*255).astype('u1');ld=make_loader();src={(x,y):(255,0,0,0) for y in range(h) for x in range(w) if mask[y,x]};fld={(x,y):(0,int(fw[y,x]),0,0) for y in range(h) for x in range(w)};sw=build_world8(ld,src);fworld=build_world8(ld,fld);r=alloc_refcon(ld)
 def put(o,f,v):ld.write_bytes(r+o,struct.pack(f,v))
 put(0,'<Q',sw);put(8,'<Q',fworld);put(0x94,'<i',1);put(0xc0,'<B',1);put(0xc1,'<B',1);put(0xc8,'<i',1);put(0xcc,'<i',1);put(0xd0,'<f',1);put(0x9c,'<f',0);put(0xa0,'<f',28/255);put(0xa4,'<f',238/255);put(0xac,'<f',0);put(0xb0,'<f',1);put(0xb4,'<f',0)
 source=bytearray();output=bytearray()
 for y in range(h):
  for x in range(w):
   source+=bytes(src.get((x,y),(0,0,0,0)));o=ld.bump_alloc(4,align=16);ld.write_bytes(o,b'\xee'*4);ld.call_function(CALLBACK,int_args=[r,x,y,0,o],max_instructions=200000);output+=ld.read_bytes(o,4)
 blobs={'source_agrb8.bin':bytes(source),'field_f32.bin':field.astype('<f4').tobytes(),'field_pf8.bin':fw.tobytes(),'output_agrb8.bin':bytes(output)}
 for n,b in blobs.items():(OUT/n).write_bytes(b)
 d=lambda n,b:{'blob':n,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()};m={'schema':'olm.aex.cpu-pipeline-fixture/1','case_id':'distancegradation.pipeline.pf8.17x11.threshold4.linear.inside','width':w,'height':h,'threshold':4,'params':{'invert':1,'in_out':1,'render_mode':1,'use_bg':1,'interp_mode':1,'grad_rgb_u8':[28,0,238],'bg_rgb_u8':[255,0,0]},'provenance':{'oracle':'unicorn-aex','binary_sha256':sha256_file(AEX),'field_function':'0x181174760','compose_function':'0x181170870','execution':trace},'blobs':{n:d(n,b) for n,b in blobs.items()},'exclusions':['host resize','blur','After Effects checkout/export']};(OUT/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n');print(OUT)
if __name__=='__main__':main()
