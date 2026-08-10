#!/usr/bin/env python3
"""PF8 RadialBlur ellipse differential without editing production source."""
from __future__ import annotations
import hashlib, importlib, json, struct, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_zoom_pf8_small_actual_aex_20260805 as z8
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as rot
SOURCE=ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp'
CASES=[(r,a) for r in (2.,5.) for a in (0.,30.,90.)]

def sha(b): return hashlib.sha256(b).hexdigest()
def configure(w,h,ratio,angle):
    visible=w*4; rb=visible+8
    def frame(seed=False):
        b=bytearray(rb*h)
        for y in range(h):
            for x in range(w):
                argb=(0x77,0x66,0x55,0x44) if seed else (255 if (x+y)%5 else 127,(x*31+y*7)%256,(x*11+y*29)%256,(x*47+y*13)%256)
                struct.pack_into('<4B',b,y*rb+x*4,*argb)
            b[y*rb+visible:(y+1)*rb]=bytes([(0xa0+y)&255])*8
        return bytes(b)
    def world(loader,payload):
        data=loader.bump_alloc(len(payload),align=64); loader.write_bytes(data,payload)
        p=loader.host_alloc(0x80); loader.write_bytes(p,b'\0'*0x80); loader.write_bytes(p+0x18,struct.pack('<Q',data)); loader.write_bytes(p+0x20,struct.pack('<I',rb)); loader.write_bytes(p+0x24,struct.pack('<I',w)); loader.write_bytes(p+0x28,struct.pack('<I',h)); loader.write_bytes(p+0x2c,struct.pack('<H',8)); return p,data
    z8.W,z8.H,z8.ROWBYTES,z8.VISIBLE=w,h,rb,visible; z8.source_frame,z8.build_world=frame,world; z8.configure()
    z8.zoom.CENTER_X,z8.zoom.CENTER_Y=w/2.,h/2.; z8.zoom.RATIO,z8.zoom.ANGLE_DEG=ratio,angle
    importlib.reload(rot); rot.W,rot.H,rot.ROWBYTES,rot.VISIBLE=w,h,rb,visible; rot.OWNER,rot.ROTATION_RETURN=0x180007520,0x180007b4a
    rot.FIXTURE_CENTER_X,rot.FIXTURE_CENTER_Y=w/2.,h/2.; rot.FIXTURE_RATIO,rot.FIXTURE_ANGLE_DEG=ratio,angle; rot.source_frame,rot.build_world=frame,world
    return frame,rb,visible

def patched_source(td):
    s=SOURCE.read_text()
    s=s.replace('std::is_same<PixelT, PF_PixelFloat>::value &&\n\t\tinput->rowbytes >= input->width * (A_long)sizeof(PF_PixelFloat)', '(std::is_same<PixelT, PF_PixelFloat>::value || std::is_same<PixelT, PF_Pixel8>::value) &&\n\t\tinput->rowbytes >= input->width * (A_long)sizeof(PixelT)',1)
    needle='std::is_same<PixelT, PF_PixelFloat>::value &&\n\t\tuse_aex_inner_geometry &&'
    s=s.replace(needle,'(std::is_same<PixelT, PF_PixelFloat>::value || std::is_same<PixelT, PF_Pixel8>::value) &&\n\t\tuse_aex_inner_geometry &&',1)
    p=td/'OLMRadialBlur.cpp'; p.write_text(s); return p

def compile_run(effect, expected, frame, rb, visible, ratio, angle):
    angular,radius=struct.unpack('<II',expected['geometry']); cells=angular*radius
    with tempfile.TemporaryDirectory(prefix='radial_pf8_ellipse_') as raw:
        td=Path(raw); src=patched_source(td); inp=td/'in'; inp.write_bytes(frame())
        names=('output','pre_blur','post_blur') if effect=='zoom' else ('output','polar','source_scalar','accum','max_alpha','final_rgba','coordinates')
        arrays='std::vector<float> a(C*4),b(C*4);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;' if effect=='zoom' else 'std::vector<float>a(C*4),b(C),c(C*4),d(C),n(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=n.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;'
        call='auto err=RenderZoomTyped<PF_Pixel8>(&iw,&ow,i,&cap);if(err)return 31;if(cap.written_floats!=C*4)return 4;' if effect=='zoom' else 'g_rotation_test_capture=&cap;auto err=RenderRotationTyped<PF_Pixel8>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(err)return 31;if(cap.written_cells!=C)return 4;'
        writes='W(2,ob);W(3,a);W(4,b);' if effect=='zoom' else 'W(2,ob);W(3,a);W(4,b);W(5,c);W(6,d);W(7,e);W(8,f);'
        cpp=td/'p.cpp'; exe=td/'p'
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1\n#include "{src}"\n#include <fstream>\n#include <vector>\nint main(int argc,char**q){{constexpr int W={z8.W},H={z8.H},RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x={visible};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if effect=='zoom' else 2};i.center_x=W/2.0;i.center_y=H/2.0;i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio={ratio};i.angle_deg={angle};i.quality=5;i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes.replace('W(','Put(')}}}''')
        sdk=subprocess.run(['xcrun','--show-sdk-path'],text=True,capture_output=True,check=True).stdout.strip()
        cmd=['clang++','-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off','-ffunction-sections','-fdata-sections','-isysroot',sdk,'-I',str(ROOT/'mac/OLMRadialBlur'),'-I',str(ROOT/'Headers'),'-I',str(ROOT/'Headers/SP'),'-I',str(ROOT/'Util'),'-I',str(ROOT/'Resources'),str(cpp),'-Wl,-dead_strip','-framework','Cocoa','-o',str(exe)]
        b=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert b.returncode==0,b.stderr
        outs=[td/n for n in names]; p=subprocess.run([str(exe),str(inp),*map(str,outs)]); assert p.returncode==0,p.returncode
        return {n:p.read_bytes() for n,p in zip(names,outs)}

def main():
    rows=[]
    for w,h in ((9,7),(32,18)):
      for ratio,angle in CASES:
        frame,rb,vis=configure(w,h,ratio,angle)
        za=z8.zoom.actual_aex(); zp=compile_run('zoom',za,frame,rb,vis,ratio,angle)
        ra=rot.actual_aex(); rp=compile_run('rotation',ra,frame,rb,vis,ratio,angle)
        zm={k:za[k]==zp[k] for k in ('pre_blur','post_blur','output')}; rm={k:ra[k]==rp[k] for k in ('polar','source_scalar','accum','max_alpha','final_rgba','coordinates','output')}
        output_diffs = [(i, a, p) for i, (a, p) in enumerate(zip(za['output'], zp['output'])) if a != p]
        rows.append({'geometry':[w,h],'ratio':ratio,'angle':angle,'zoom':zm,'rotation':rm,
                     'zoom_output_diff_count':len(output_diffs),'zoom_output_first_diffs':output_diffs[:8],
                     'exact':all(zm.values()) and all(rm.values())})
        print(rows[-1],flush=True)
    print(json.dumps({'exact':all(x['exact'] for x in rows),'cells':rows},indent=2)); return 0 if all(x['exact'] for x in rows) else 1
if __name__=='__main__': raise SystemExit(main())
