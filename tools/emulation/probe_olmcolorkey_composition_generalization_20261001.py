#!/usr/bin/env python3
"""Independent geometry/alpha witnesses for recovered Thin composition.

The CLI core harness consumes the identical typed input bytes used by the AEX
worker. Temporary source variants only; public admission is not broadened.
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import tempfile
import types
from pathlib import Path

import probe_olmcolorkey_legal_composition_20261001 as base
import probe_olmcolorkey_composition_hypotheses_20261001 as hypotheses

ROOT = base.ROOT
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
DEPTHS = {"PF8": 4, "PF16": 8, "PF32": 16}
FIXTURES = (
    {"id": "edge17_opaque", "width": 17, "height": 15, "alpha": "opaque"},
    {"id": "edge17_mixed_zero", "width": 17, "height": 15, "alpha": "mixed"},
    {"id": "edge9_mixed_zero", "width": 9, "height": 7, "alpha": "mixed"},
)
HARNESS = r"""
int main(int argc,char**argv){
 if(argc!=8)return 90;
 const int w=std::atoi(argv[1]),h=std::atoi(argv[2]),depth=std::atoi(argv[3]);
 const int thin=std::atoi(argv[4]),distance=std::atoi(argv[5]),blur=std::atoi(argv[6]);
 const int ps=depth==8?4:depth==16?8:16,rb=w*ps+8;
 std::vector<std::uint8_t>ib((size_t)rb*h),ob((size_t)rb*h,0xcc);
 if(std::fread(ib.data(),1,ib.size(),stdin)!=ib.size())return 91;
 auto before=ib;
 PF_EffectWorld in{ib.data(),rb,w,h,(A_short)depth,{0,0,w,h},0};
 PF_EffectWorld out{ob.data(),rb,w,h,(A_short)depth,{0,0,w,h},0};
 OLMColorKeyInfo info{};
 info.color_keep=std::atoi(argv[7])!=0;info.number_of_colors=2;info.use_color[0]=info.use_color[1]=true;
 info.colors8[0]={255,0,0,0};info.colors8[1]={255,0,255,0};
 info.colors[0]={1,0,0,0};info.colors[1]={1,0,1,0};
 info.edge_thin_amount=thin;info.edge_thin_distance_type=distance;
 info.edge_blur_amount=blur;info.edge_blur_distance_type=2;info.edge_blur_direction=102;
 g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
 if(RenderWorldDirect(&in,&out,info,(short)depth))return 92;
 if(ib!=before)return 93;
 for(int y=0;y<h;y++)for(int b=w*ps;b<rb;b++)if(ob[(size_t)y*rb+b]!=0xcc)return 94;
 if(std::fwrite(ob.data(),1,ob.size(),stdout)!=ob.size())return 95;
 return 0;
}
"""


def fixture(definition: dict, depth: str) -> tuple[bytes, int]:
    w,h = definition["width"],definition["height"]
    ps = DEPTHS[depth]
    rb = w*ps+8
    raw = bytearray([0xa5]*(rb*h))
    for y in range(h):
        for x in range(w):
            black = (x<3 and y<h//2) or (2<=x<w-2 and 2<=y<h-2 and
                      not (4<=x<w-4 and 4<=y<h-4))
            green = not black and (x==w-1 or (y==h-1 and x>=w//2))
            a = 255 if definition["alpha"]=="opaque" else (0 if (x*7+y*11)%5==0 else 32+(x*37+y*29)%224)
            r,g,b = (0,0,0) if black else (0,255,0) if green else (46+2*x,56+3*y,87)
            if depth=="PF8": values,fmt = (a,r,g,b),"<4B"
            elif depth=="PF16": values,fmt = tuple((v*32768+127)//255 for v in (a,r,g,b)),"<4H"
            else: values,fmt = tuple(v/255 for v in (a,r,g,b)),"<4f"
            struct.pack_into(fmt,raw,y*rb+x*ps,*values)
    return bytes(raw),rb


def compile_core(directory: Path, body: str, name: str) -> Path:
    directory.mkdir()
    modified = directory/"OLMColorKey.cpp"
    modified.write_text(base.replace_once(body,'#include "OLMColorKey.h"',
                        '#include "'+str(SOURCE.with_suffix(".h"))+'"'))
    saved = base.retained.mac_adapter.SOURCE
    try:
        base.retained.mac_adapter.SOURCE=modified
        base.retained.mac_adapter.compile_probe(directory)
    finally:
        base.retained.mac_adapter.SOURCE=saved
    source=directory/"olmcolorkey_mac_smartrender_adapter_probe.cpp"
    source.write_text(base.replace_once(source.read_text(),"int main(){","int legacy_main(){")+HARNESS)
    sdk=subprocess.run(["xcrun","--show-sdk-path"],check=True,capture_output=True,text=True).stdout.strip()
    exe=directory/name
    subprocess.run(["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off",
                    "-isysroot",sdk,"-I",str(directory),str(source),"-framework","Cocoa","-o",str(exe)],
                   check=True,capture_output=True)
    return exe


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--quick",action="store_true")
    parser.add_argument("--permit-retained-stubs",action="store_true",help="Historical diagnostic only; mark missing sinf import as invalid oracle evidence")
    parser.add_argument("--standard-host",action="store_true",help="Use unit downsample numerators instead of the retained synthetic integer-255 context")
    parser.add_argument("--remove",action="store_true",help="Color Keep off; same matched-matte operations, final alpha complement")
    parser.add_argument("--report",type=Path,default=ROOT/"reports/colorkey_composition_generalization_20261001.json")
    args=parser.parse_args()
    definitions=(FIXTURES[1],) if args.quick else FIXTURES
    depths=("PF8","PF32") if args.quick else tuple(DEPTHS)
    original=SOURCE.read_text()
    historical=subprocess.check_output(["git","show","290e150d:mac/OLMColorKey/OLMColorKey.cpp"],cwd=ROOT,text=True)
    measured=json.loads(hypotheses.BASELINE.read_text())
    if base.sha(historical.encode())!=measured["production_source_sha256"]:
        raise RuntimeError("historical hypothesis source binding drift")
    variants=hypotheses.kernel_variants(historical)
    variants["baseline"]=historical
    variants["current"]=original
    probe=base.retained.actual_probe
    if args.standard_host:
        retained_body=Path(probe.__file__).read_text()
        probe_body=base.replace_once(retained_body,
            'metric_cost = 1 if PIXEL_FORMAT == "PF32" else 255', 'metric_cost = 1')
        adjusted=types.ModuleType("olmck_standard_host_probe")
        adjusted.__file__=probe.__file__
        exec(compile(probe_body,probe.__file__,"exec"),adjusted.__dict__)
        probe=adjusted
        for name,body in list(variants.items()):
            if name in ("current","baseline"):continue
            variants[name]=body.replace(
                'const float scale = OLMCKPixelTraits<PixelT>::is_32bpc() ? 1.0f : 255.0f;',
                'const float scale = 1.0f;').replace(
                'const float distance_scale = OLMCKPixelTraits<PixelT>::is_32bpc() ? 1.0f : 255.0f;',
                'const float distance_scale = 1.0f;').replace(
                '(bounded_public_owner_lane || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;',
                '1.0f;')
    math_audit = probe.AexLoader(str(probe.AEX), verbose=False, fast=False)
    missing_math = [name for name in ("sinf",) if name not in math_audit.import_impls]
    if missing_math and not args.permit_retained_stubs:
        raise RuntimeError("retained loader has unimplemented math imports: " + ",".join(missing_math) +
                           "; use the exported around_composition_owner probe for numerical evidence")
    original_record=base.retained._original_parameter_record
    current_thin,current_type,current_blur=0,1,0
    definition=definitions[0]

    def source_fixture(*_args):
        return fixture(definition,probe.PIXEL_FORMAT)

    def parameters(*values):
        payload=bytearray(original_record(*values))
        struct.pack_into("<i",payload,0x20,int(probe.PIXEL_FORMAT[2:]))
        payload[0x24]=0 if args.remove else 1
        struct.pack_into("<i",payload,0x28,current_thin)
        struct.pack_into("<i",payload,0x2c,current_type)
        return bytes(payload)

    probe.fixture=source_fixture
    probe.parameter_record=parameters
    rows=[]
    with tempfile.TemporaryDirectory(prefix="olmck_generalization_") as raw:
        directory=Path(raw)
        exes={name:compile_core(directory/name,variants[name],name)
              for name in ("baseline","current","native_final_complement")}
        for definition in definitions:
            probe.WIDTH,probe.HEIGHT=definition["width"],definition["height"]
            for current_type in (1,2,3):
                for current_thin in (0,-1,1,-4,4):
                    for current_blur in (0,4):
                        for depth in depths:
                            probe.PIXEL_FORMAT=depth
                            source,rb=source_fixture()
                            actual=probe.execute_case(probe.AEX,True,current_blur,"single",2,2,2)
                            required=("normal_return","exact_dispatch_hits","checkout_callbacks_exact","output_padding_preserved")
                            if not all(actual["acceptance_gates"][k] for k in required):
                                raise RuntimeError("AEX execution/padding failure")
                            expected=b"".join(bytes.fromhex(r)+b"\xcc"*8 for r in actual["captures"]["output_active_rows_hex"])
                            if actual["captures"]["input_sha256"]!=base.sha(source):
                                raise RuntimeError("input identity drift")
                            results={}
                            for name,exe in exes.items():
                                run=subprocess.run([str(exe),str(probe.WIDTH),str(probe.HEIGHT),depth[2:],
                                                    str(current_thin),str(current_type),str(current_blur),"0" if args.remove else "1"],
                                                   input=source,capture_output=True,check=True)
                                candidate=run.stdout
                                if len(candidate)!=len(expected):raise RuntimeError("candidate size drift")
                                diffs=[i for i,(a,b) in enumerate(zip(expected,candidate)) if a!=b]
                                first=diffs[0] if diffs else None
                                results[name]={"exact":not diffs,"different_bytes":len(diffs),"sha256":base.sha(candidate),
                                               "first_difference":None if first is None else
                                               {"row":first//rb,"byte_in_row":first%rb,"actual":expected[first],"candidate":candidate[first]}}
                            rows.append({"fixture":definition,"depth":depth,"thin":current_thin,"type":current_type,
                                         "blur":current_blur,"input_sha256":base.sha(source),"actual_sha256":base.sha(expected),
                                         "results":results})
                        print(f"measured {definition['id']} type={current_type} thin={current_thin} blur={current_blur}",flush=True)
    summary={name:{"exact":sum(r["results"][name]["exact"] for r in rows),
                   "regressions":sum(r["results"]["baseline"]["exact"] and not r["results"][name]["exact"] for r in rows)}
             for name in exes}
    report={"schema":"olmcolorkey.composition-generalization/1","date":"2026-10-01","status":"measured",
            "case_count":len(rows),"color_keep":not args.remove,"missing_math_imports":missing_math,
            "valid_numerical_oracle":not missing_math,"standard_host":args.standard_host,
            "historical_baseline_sha256":base.sha(historical.encode()),
            "effective_aex_probe_sha256":base.sha((probe_body if args.standard_host else Path(probe.__file__).read_text()).encode()),
            "host_metric_numerators":"1/1" if args.standard_host else "synthetic integer255/float1",
            "candidate_source_sha256":{name:base.sha(variants[name].encode()) for name in exes},"summary":summary,"source_sha256":base.sha(SOURCE.read_bytes()),
            "aex_sha256":probe.AEX_SHA256,"probe_sha256":base.sha(Path(__file__).read_bytes()),
            "dependency_sha256":{str(Path(p).relative_to(ROOT)):base.sha(Path(p).read_bytes())
                                for p in (base.__file__,hypotheses.__file__,probe.__file__,base.retained.__file__,base.retained.mac_adapter.__file__)},
            "cases":rows,"scope":"Different edge-touching source/geometry, identical typed input bytes; actual AEX worker with declared parameter record versus temporary Mac core. No public-owner/native AE/installed claim."}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(summary))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
