#!/usr/bin/env python3
"""Bounded RadialBlur outer-offset matrix against the actual Windows AEX owner."""
from __future__ import annotations

import hashlib, importlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

GEOMETRIES = ((9, 7), (32, 18))
CELLS = [(effect, depth, w, h, mode, offset) for effect in ("zoom", "rotation")
         for depth in (8, 16, 32) for w, h in GEOMETRIES
         for mode in (2, 3) for offset in (2, 4)]
REPORT = ROOT / "refs/conformance/olmradialblur_offset_matrix_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")


def configure(cell):
    effect, depth, w, h, mode, offset = cell
    target, frame, rb, cx, cy = base.configure((effect, depth, w, h, 0., 0., 1.))
    m = target.fixture.m4 if effect == "zoom" else (target.base.m4 if depth == 32 else target.m4)
    old = m.install_reader_detours
    def install(loader, params):
        params = dict(params)
        params.update({"Outer Offset Mode": mode, "Outer Offset": offset})
        return old(loader, params)
    m.install_reader_detours = install
    return target, frame, rb, cx, cy


def capture(cell):
    target, *_ = configure(cell)
    return target.actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_offset_actual_") as raw:
        out = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def temporary_admitted_source(path: Path):
    """Broaden only the temporary probe copy; shared production remains untouched."""
    text = (ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text()
    if ("use_aex_typed_zoom_offset_matrix" in text and
            "use_aex_typed_rotation_offset_mode3" in text):
        path.write_text(text)
        return
    predicate = '''input && output && input->data && output->data &&
        ((input->width == 9 && input->height == 7) || (input->width == 32 && input->height == 18)) &&
        input->width == output->width && input->height == output->height &&
        info.center_x == (std::is_same<PixelT, PF_Pixel8>::value ? (PF_FpLong)input->width / 2.0 : (PF_FpLong)(input->width / 2)) &&
        info.center_y == (std::is_same<PixelT, PF_Pixel8>::value ? (PF_FpLong)input->height / 2.0 : (PF_FpLong)(input->height / 2)) &&
        info.outer_strength == 4 && info.outer_edge_fade == 0 &&
        (info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
        (info.outer_offset == 2 || info.outer_offset == 4) &&
        info.inner_strength == 0 && info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
        info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 && info.quality == 5.0 &&
        info.brightness_gain == 1.0 && info.size_variation == 0.0 && info.noise_variation == 0.0 &&
        info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
        info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height'''
    zoom_anchor = '\tif (!use_aex_typed_quality_repeat && !use_aex_typed_zoom_offcenter_brightness && (!use_aex_zoom_geometry ||'
    text = text.replace(zoom_anchor,
        '\tconst bool use_aex_temporary_offset_matrix = ' + predicate + ';\n' +
        '\tif (!use_aex_temporary_offset_matrix && !use_aex_typed_quality_repeat && !use_aex_typed_zoom_offcenter_brightness && (!use_aex_zoom_geometry ||', 1)
    text = text.replace('\t\tuse_aex_pf16_bounded_offset_small;\n',
                        '\t\tuse_aex_pf16_bounded_offset_small || use_aex_temporary_offset_matrix;\n', 1)
    rotation_anchor = '\tconst bool use_aex_exact = use_aex_typed_rotation_offcenter_brightness'
    text = text.replace(rotation_anchor,
        '\tconst bool use_aex_temporary_rotation_offset_matrix = ' + predicate + ';\n' +
        '\tconst bool use_aex_exact = use_aex_temporary_rotation_offset_matrix || use_aex_typed_rotation_offcenter_brightness', 1)
    if text.count('use_aex_temporary_offset_matrix') != 3 or text.count('use_aex_temporary_rotation_offset_matrix') != 2:
        raise RuntimeError('temporary offset admission anchors did not match uniquely')
    path.write_text(text)


def production(cell, expected):
    effect, depth, w, h, mode, offset = cell
    _, frame, rb, cx, cy = configure(cell)
    angular, radial = struct.unpack("<II", expected["geometry"]); cells = angular * radial
    pixel = {8:"PF_Pixel8", 16:"PF_Pixel16", 32:"PF_PixelFloat"}[depth]
    pb = {8:4, 16:8, 32:16}[depth]
    with tempfile.TemporaryDirectory(prefix="radial_offset_prod_") as raw:
        td=Path(raw); src=td/"OLMRadialBlur.cpp"; temporary_admitted_source(src)
        inp=td/"in"; inp.write_bytes(frame())
        if effect == "zoom":
            names=("output","pre_blur","post_blur")
            arrays="std::vector<float>a(C*4),b(C*4);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;"
            call=f"auto e=RenderZoomTyped<{pixel}>(&iw,&ow,i,&cap);if(e||cap.written_floats!=C*4)return 3;"
            writes="Put(2,ob);Put(3,a);Put(4,b);"
        else:
            names=("output","polar","source_scalar","accum","max_alpha","final_rgba","coordinates")
            arrays="std::vector<float>a(C*4),b(C),c(C*4),d(C),nn(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=nn.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;"
            call=f"g_rotation_test_capture=&cap;auto z=RenderRotationTyped<{pixel}>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(z||cap.written_cells!=C)return 3;"
            writes="Put(2,ob);Put(3,a);Put(4,b);Put(5,c);Put(6,d);Put(7,e);Put(8,f);"
        cpp=td/"p.cpp"; exe=td/"p"; visible=w*pb
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{src}"
#include <fstream>
#include <vector>
int main(int n,char**q){{constexpr int W={w},H={h},RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x={visible};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if effect=='zoom' else 2};i.center_x={cx};i.center_y={cy};i.outer_strength=4;i.outer_offset_mode={mode};i.outer_offset={offset};i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes}}}''')
        sdk=subprocess.run(["xcrun","--show-sdk-path"],text=True,capture_output=True,check=True).stdout.strip()
        cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"mac/OLMRadialBlur"),"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        built=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        if built.returncode: raise RuntimeError(built.stderr)
        outs=[td/n for n in names]
        subprocess.run([str(exe),str(inp),*map(str,outs)],check=True)
        return {n:p.read_bytes() for n,p in zip(names,outs)}


def main():
    cells = CELLS
    if "--admitted" in sys.argv:
        cells = [cell for cell in CELLS if cell[0] == "zoom" or cell[4] == 3]
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals=dict(zip(cells,pool.map(isolated,cells)))
    rows=[]
    for cell in cells:
        actual=actuals[cell]; prod=production(cell,actual)
        planes=("pre_blur","post_blur","output") if cell[0]=="zoom" else ("polar","source_scalar","accum","max_alpha","final_rgba","coordinates","output")
        matches={p:prod[p]==actual[p] for p in planes}; exact=all(matches.values())
        first_differences = {}
        for p in planes:
            if matches[p]: continue
            limit=min(len(actual[p]),len(prod[p]))
            at=next((i for i in range(limit) if actual[p][i] != prod[p][i]), limit)
            first_differences[p]={"byte_offset":at,
                "actual_hex":actual[p][at:at+8].hex(), "production_hex":prod[p][at:at+8].hex(),
                "actual_size":len(actual[p]), "production_size":len(prod[p])}
        rows.append({"effect":cell[0],"depth":cell[1],"geometry":list(cell[2:4]),"offset_mode":cell[4],"offset_ui":cell[5],"matches":matches,"first_differences":first_differences,"exact":exact,"actual_sha256":{p:hashlib.sha256(actual[p]).hexdigest() for p in planes}})
        print(cell, exact, matches, flush=True)
    count=sum(x["exact"] for x in rows); status="exact" if count==len(rows) else "mismatch"
    report={"kind":"olmradialblur_offset_matrix_actual_aex_20260811","status":status,"scope":"Zoom PF8/PF16/PF32 Mode2/3 and Rotation PF8/PF16/PF32 Mode3; 9x7/32x18; Outer Strength4; UI Offset2/4; centered neutral Ratio1 Angle0 Brightness1 Quality5 Repeat on Noise Type1.","exact_cases":count,"total_cases":len(rows),"cases":rows,"boundary":"Only the 36 admitted cells are evidence. Rotation Mode2 remains fail-closed; other offset modes/values, strengths, geometries, parameters and AE-host behavior remain unproved.","production_method":"Shared-direct comparison against the bounded production predicates."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    DOC.write_text(f"# OLM RadialBlur Offset matrix — 2026-08-11\n\nStatus: **{status}** ({count}/{len(rows)})\n\nZoomのMode 2/3とRotationのMode 3について、PF8/PF16/PF32、9×7/32×18、Outer Strength 4、UI Offset 2/4をactual AEXの内部planeとtyped outputで比較しました。Rotation Mode 2はscatter規則の解析中で、引き続きfail-closeです。\n")
    return 0 if status=="exact" else 1


if __name__ == "__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--capture":
        v=sys.argv[2:-1]; cell=(v[0],int(v[1]),int(v[2]),int(v[3]),int(v[4]),int(v[5]))
        Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell))); raise SystemExit(0)
    raise SystemExit(main())
