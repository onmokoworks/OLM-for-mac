#!/usr/bin/env python3
"""Pairwise geometry/classifier matrix: actual AEX versus production."""
from __future__ import annotations
import collections,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as v1
import test_olmsmoother2_typed_writeback_20260717 as typed

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_geometry_classifier_matrix_production_harness_20260811.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_geometry_classifier_matrix_actual_aex_20260811.json'
DOC=ROOT/'refs/conformance/olmsmoother2_geometry_classifier_matrix_actual_aex_20260811.md'
TUPLES={'default':(100,2,0),'mid':(50,50,50),'low':(1,0,1),'upper':(100,100,100)}
FIXTURES=[
 ('g1_uniform',1,1,'uniform',('default','low')),
 ('g2_isolated',2,2,'isolated',('mid','upper')),
 ('g3_vertical',3,2,'vertical',('default','upper')),
 ('g5_horizontal',5,5,'horizontal',('low','mid')),
 ('g9_diagonal',9,7,'diagonal',('default','mid')),
 ('g9_checker',9,7,'checker',('low','upper')),
 ('g32_seeded',32,18,'seeded',('default','upper')),
 ('g32_isolated',32,18,'isolated',('mid','low')),
]
DEPTHS={'PF8':(4,5),'PF16':(8,7),'PF32':(16,13)}
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def f32(x):return typed.f32(x)
def pixel(pattern,x,y,w,h):
 if pattern=='uniform':return (96,96,96,255)
 if pattern=='isolated':return (240,20,180,128) if x==w//2 and y==h//2 else (8,12,16,0)
 if pattern=='vertical':return (16,32,220,255) if x<w//2 else (230,180,20,255)
 if pattern=='horizontal':return (20,220,64,255) if y<h//2 else (210,24,180,255)
 if pattern=='diagonal':return (245,40,32,255) if x*h<y*w else (18,80,224,255)
 if pattern=='checker':return (250,8,170,255) if (x+y)&1 else (2,220,40,64)
 u=((x+1)*0x9e3779b9)^((y+3)*0x85ebca6b);u&=0xffffffff;u^=u>>16;u=(u*0x7feb352d)&0xffffffff;u^=u>>15
 return (u&255,(u>>8)&255,(u>>16)&255,(0,1,64,128,192,255)[(x+3*y)%6])
def encoded(depth,pattern,w,h,feature='none'):
 out=[]
 for y in range(h):
  for x in range(w):
   r,g,b,a=pixel(pattern,x,y,w,h)
   if feature!='none' and x==0 and y==0:r,g,b,a=(1,1,1,255)
   if feature!='none' and x==1 and y==0:r,g,b,a=(255,0,0,255)
   if depth=='PF8':
    # AEX FUN_1800024c0 is CVTDQ2PS followed by MULSS with the rounded
    # float32 1/255 constant, not a double division rounded once at the end.
    inv=f32(1/255);out.append(tuple(f32(f32(c)*inv) for c in (r,g,b,a)));continue
   elif depth=='PF16': q=tuple(round(c*32768/255) for c in (r,g,b,a))
   else:q=(r/255,g/255,b/255,a/255)
   scale=32768 if depth=='PF16' else 1
   out.append(tuple(f32(c/scale) for c in q))
 return out
def histogram(plane,w,h):
 def cb(x,y,b):return plane[(y*w+x)*4+b] if 0<=x<w and 0<=y<h else 0
 hist=collections.Counter()
 for y in range(h):
  for x in range(w):
   A,R,G,B=(cb(x,y,k) for k in range(4));er0=1 if x==w-1 or cb(x+1,y,0)==0 else 0
   bsw=bool(y<h-1 and x>0 and cb(x-1,y+1,3));bse=bool(y<h-1 and cb(x,y+1,1));uv=1 if y==h-1 or x==w-1 or cb(x+1,y+1,2)==0 else 0
   idx=((0 if bsw else 2)+er0+(((0 if bse else 1)+uv*2)*4))*16+(4 if B==0 else 0)+(1 if G==0 else 0)+(2 if R==0 else 0)+(8 if A==0 else 0)
   hist[idx]+=1
 return dict(sorted(hist.items()))
def actual(depth,ver,pixels,pad,w,h,s,r,e,feature='none',gamma_value=2.4,writer_witnesses=None):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1)
 if writer_witnesses is not None:
  def capture_writer(current,address,size):
   rsp=current.uc.reg_read(typed.UC_X86_REG_RSP)
   x,y=struct.unpack('<ii',current.read_bytes(rsp+0x34,8))
   rgba=struct.unpack('<4f',current.read_bytes(rsp+0x48,16))
   writer_witnesses.append({'x':x,'y':y,'cce0_rgba':rgba,'cce0_rgba_u32':struct.unpack('<4I',current.read_bytes(rsp+0x48,16))})
  l.add_code_hook(0x180003510,capture_writer)
 ss=16*w+16;sb=l.bump_alloc(ss*h,align=16)
 for y in range(h):l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*pixels[y*w+x]) for x in range(w))+b'\x3c'*16)
 sd=v2.desc(l,sb,ss,w,h);ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[w,0,h,0]):l.write_bytes(p,struct.pack('<i',n))
 if feature in ('colors_noninvert','colors_invert'):
  keysv=v1.SmallStatic(l,h)
  key=f32(1/255)
  if feature=='colors_noninvert':
   kp=l.bump_alloc(16,align=16);l.write_bytes(kp,struct.pack('<4f',1.,key,key,key));l.call_function(0x180002a70,int_args=[*ptr,sd,kp],max_instructions=10_000_000)
  else:
   cp=l.bump_alloc(16,align=16);l.write_bytes(cp,struct.pack('<4f',key,key,key,1.));kc=l.bump_alloc(0x80,align=16);l.write_bytes(kc,b'\0'*0x80);l.write_bytes(kc+0x60,struct.pack('<Q',1));l.write_bytes(kc+0x68,struct.pack('<Q',cp));l.call_function(0x180002930,int_args=[*ptr,sd,kc],max_instructions=10_000_000)
 pixels=[struct.unpack('<4f',l.read_bytes(sb+y*ss+x*16,16)) for y in range(h) for x in range(w)]
 linear=pixels if ver==1 else [(v2.interp(v2.DECODE,R),v2.interp(v2.DECODE,G),v2.interp(v2.DECODE,B),A) for R,G,B,A in pixels]
 for y in range(h):l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*linear[y*w+x]) for x in range(w))+b'\x3c'*16)
 cs=4*w+4;cb=l.bump_alloc(cs*h,align=16);l.write_bytes(cb,b'\xa5'*(cs*h));sd=v2.desc(l,sb,ss,w,h);cd=v2.desc(l,cb,cs,w,h);rect=l.bump_alloc(16,align=16);l.write_bytes(rect,struct.pack('<4i',0,0,w,h));cfg=l.bump_alloc(0x80,align=16);l.write_bytes(cfg,b'\0'*0x80);l.write_bytes(cfg,struct.pack('<i',1 if ver==1 else 0));l.write_bytes(cfg+0x1c,struct.pack('<i',r));l.write_bytes(cfg+0x20,struct.pack('<ii',s,e))
 if feature=='gamma_all':l.write_bytes(cfg+0x28,struct.pack('<f',f32(gamma_value)));l.write_bytes(cfg+0x2c,struct.pack('<i',5));l.write_bytes(cfg+0x40,b'\x01')
 if feature in ('colors_noninvert','colors_invert'):
  key=f32(1/255);pal=[(1.,0.,0.,1.),(key,key,key,1.)];colors=l.bump_alloc(32,align=16);l.write_bytes(colors,b''.join(struct.pack('<4f',*q) for q in pal));l.write_bytes(cfg+0x28,struct.pack('<f',f32(gamma_value)));l.write_bytes(cfg+0x30,struct.pack('<Q',2));l.write_bytes(cfg+0x38,struct.pack('<Q',colors));l.write_bytes(cfg+0x40,b'\x03')
 sv=v1.SmallStatic(l,h);cr=l.call_function(v1.FUN_ADA0,int_args=[sd,cd,rect,cfg],max_instructions=20_000_000);plane=b''.join(l.read_bytes(cb+y*cs,w*4) for y in range(h));req(all(x in (0,255) for x in plane),'invalid class plane')
 psz,pad0=DEPTHS[depth];req(pad==pad0,'pad drift');os=w*psz+pad;ob=l.bump_alloc(os*h,align=16);l.write_bytes(ob,b'\xa5'*(os*h));od=v2.desc(l,ob,os,w,h);ctx=l.bump_alloc(0x20,align=16);l.write_bytes(ctx,b'\0'*0x20)
 if ver==2:
  tab=l.bump_alloc(len(v2.ENCODE),align=16);l.write_bytes(tab,v2.ENCODE);l.write_bytes(ctx+0x10,struct.pack('<Q',10000));l.write_bytes(ctx+0x18,struct.pack('<Q',tab))
 dy=v1.Dynamic(l,typed.WORKERS[depth])
 rr=l.call_function(typed.WORKERS[depth],int_args=[*ptr,sd,cd,od,cfg,ctx],max_instructions=100_000_000);raw=l.read_bytes(ob,os*h)
 return raw,plane,cr['instructions'],rr['instructions']
def main():
 with tempfile.TemporaryDirectory(prefix='sm2_geom_matrix_') as td:
  binary=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True)
  rows=[];all_indices=set()
  for fid,w,h,pattern,names in FIXTURES:
   for name in names:
    s,r,e=TUPLES[name]
    for ver in (1,2):
     planes={}
     for depth,(psz,pad) in DEPTHS.items():
      px=encoded(depth,pattern,w,h);raw,plane,ci,wi=actual(depth,ver,px,pad,w,h,s,r,e)
      p=subprocess.run([str(binary),str(w),str(h),pattern,str(ver),str(s),str(r),str(e),depth],check=True,text=True,capture_output=True);lines=dict(line.split(' ',1) for line in p.stdout.splitlines());prod=bytes.fromhex(lines['RAW']);ph={int(a):int(b) for a,b in (x.split(':') for x in lines['HIST'].split(','))} if lines['HIST'] else {}
      ah=histogram(plane,w,h);req(raw==prod,f'{fid}/{name}/v{ver}/{depth} output');req(ah==ph,f'{fid}/{name}/v{ver}/{depth} index histogram');planes[depth]=plane;all_indices.update(ah)
      rb=w*psz+pad;req(all(raw[y*rb+w*psz:(y+1)*rb]==b'\xa5'*pad for y in range(h)),'actual padding')
      rows.append({'id':fid,'geometry':[w,h],'pattern':pattern,'tuple':name,'smoothness':s,'smooth_range':r,'extra_smooth':e,'version':ver,'depth':depth,'raw_sha256':hashlib.sha256(raw).hexdigest(),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'class_nonzero_bytes':sum(bool(x) for x in plane),'switch_index_histogram':{str(k):v for k,v in ah.items()},'padding_per_row':pad,'classifier_instructions':ci,'worker_instructions':wi,'exact':True})
     req(planes['PF8']==planes['PF16']==planes['PF32'] if ver==1 else True,f'{fid}/{name} v1 class depth divergence')
  req(len(rows)==96,'core case count');features=[]
  scanner_witnesses=[]
  for x,y,needle in [(4,0,'109d0=8,4'),(3,1,'10ad0=8,6')]:
   env=dict(__import__('os').environ,SM2_DEBUG_SCAN='1',SM2_PROBE_X=str(x),SM2_PROBE_Y=str(y));out=subprocess.run([str(binary),'9','7','checker','1','100','2','0','PF8'],check=True,text=True,capture_output=True,env=env).stdout;scan=next(line for line in out.splitlines() if line.startswith('SCAN '));req(needle in scan,f'scanner witness {needle}');scanner_witnesses.append({'pixel':[x,y],'expected_fragment':needle,'production_scan':scan})
  for fid,w,h,pattern,tname in [('feature9',9,7,'diagonal','upper'),('feature32',32,18,'seeded','mid')]:
   s,r,e=TUPLES[tname]
   for feature in ('colors_noninvert','colors_invert','gamma_all'):
    for depth,(psz,pad) in DEPTHS.items():
     raw,plane,ci,wi=actual(depth,2,encoded(depth,pattern,w,h,feature),pad,w,h,s,r,e,feature);p=subprocess.run([str(binary),str(w),str(h),pattern,'2',str(s),str(r),str(e),depth,feature],check=True,text=True,capture_output=True);lines=dict(line.split(' ',1) for line in p.stdout.splitlines());prod=bytes.fromhex(lines['RAW']);ph={int(a):int(b) for a,b in (x.split(':') for x in lines['HIST'].split(','))} if lines['HIST'] else {};ah=histogram(plane,w,h);req(raw==prod,f'{fid}/{feature}/{depth} output');req(ah==ph,f'{fid}/{feature}/{depth} histogram');all_indices.update(ah);features.append({'id':fid,'geometry':[w,h],'pattern':pattern,'tuple':tname,'feature':feature,'depth':depth,'raw_sha256':hashlib.sha256(raw).hexdigest(),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'switch_index_histogram':{str(k):v for k,v in ah.items()},'padding_per_row':pad,'exact':True})
 report={'schema':'olmsmoother2.geometry-classifier-matrix/1','verdict':'PASS_96_CORE_PLUS_18_FEATURE_GEOMETRY_CLASSIFIER_CASES_ACTUAL_AEX_TO_PRODUCTION_EXACT','scope':'96 pairwise core cases plus 18 v2 key/Gamma feature intersections; actual-AEX owner/classifier/typed worker versus production, padded rows','core_case_count':len(rows),'feature_case_count':len(features),'total_case_count':len(rows)+len(features),'distinct_switch_indices':sorted(all_indices),'distinct_switch_index_count':len(all_indices),'scanner_witnesses':scanner_witnesses,'tuples':TUPLES,'fixtures':[{'id':a,'geometry':[w,h],'pattern':p,'tuples':list(t)} for a,w,h,p,t in FIXTURES],'core_cases':rows,'feature_cases':features,'aex_sha256':typed.AEX_SHA256,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No AE-host execution claim','No arbitrary image/parameter generalization']};req(len(features)==18,'feature count');REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text(f"# OLMSmoother2 geometry/classifier pairwise matrix\n\nVerdict: `{report['verdict']}`\n\nAll 96 core cases and 18 feature intersections are exact for output bytes, row padding, actual-AEX class plane-derived switch-index histogram, and the production switch-index histogram. The corpus spans all six requested geometries, seven pattern families, both versions, all three depths, four representative smoothing tuples, and representative non-invert key + Gamma Colors, invert key + Gamma Colors, and Gamma All paths. It reaches {len(all_indices)} distinct switch indices. Focused checker witnesses also lock `FUN_1800109d0` at `(8,4)` and `FUN_180010ad0` at `(8,6)`, preventing the former double-decrement regression.\n\nAE-host execution and arbitrary inputs remain separately scoped.\n");print(report['verdict'],len(all_indices),sorted(all_indices))
if __name__=='__main__':raise SystemExit(main())
