#!/usr/bin/env python3
"""Actual-AEX vs production Replace composed with Edge Thin/Blur."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_pf16_full_worker_20260805 as actual_probe  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

WIDTH, HEIGHT, PADDING = 13, 11, 8
FORMATS = {"PF8": 4, "PF16": 8, "PF32": 16}
MODES = (
    {"name": "none", "thin": 0, "blur": 0.0},
    {"name": "thin_negative4", "thin": -4, "blur": 0.0},
    {"name": "thin_positive4", "thin": 4, "blur": 0.0},
    {"name": "blur_direction2_amount4", "thin": 0, "blur": 4.0},
    {"name": "thin_negative4_blur_direction2_amount4", "thin": -4, "blur": 4.0},
    {"name": "thin_positive4_blur_direction2_amount4", "thin": 4, "blur": 4.0},
)
REPLACEMENTS = ((0.90, 0.10, 0.75), (0.95, 0.55, 0.05))
REPORT = ROOT / "refs/conformance/olmcolorkey_replace_edge_composition_actual_aex_20260811.json"
MD = REPORT.with_suffix(".md")

CURRENT_REPLACE = False
CURRENT_MODE = MODES[0]
_original_parameter_record = actual_probe.parameter_record


def key_at(x: int, y: int) -> int:
    ring = x >= 1 and x <= 6 and y >= 1 and y <= 6 and not (x >= 3 and x <= 4 and y >= 3 and y <= 4)
    slope = y >= 2 and y <= 6 and x >= 8 and x <= 8 + (y - 2)
    island = y == 9 and (x == 10 or x == 11)
    return 1 if ring or island else 2 if slope else 0


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fixture(enabled_key: bool = False, key_shape: str = "single") -> tuple[bytes, int]:
    pb = 16 if actual_probe.PIXEL_FORMAT == "PF32" else 8 if actual_probe.PIXEL_FORMAT == "PF16" else 4
    rb = WIDTH * pb + PADDING
    raw = bytearray([0xA5] * (rb * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            key = key_at(x, y) if enabled_key else 0
            if actual_probe.PIXEL_FORMAT == "PF32":
                value = ((1.0, 0.0, 0.0, 0.0) if key == 1 else
                         (1.0, 0.0, 1.0, 0.0) if key == 2 else
                         (1.0, f32(f32(0.18) + f32(x / f32(80.0))),
                          f32(f32(0.22) + f32(y / f32(70.0))), f32(0.34)))
                fmt = "<4f"
            elif actual_probe.PIXEL_FORMAT == "PF16":
                value = ((32768, 0, 0, 0) if key == 1 else
                         (32768, 0, 32768, 0) if key == 2 else
                         (32768, 5898 + x * 410, 7209 + y * 468, 11141))
                fmt = "<4H"
            else:
                value = ((255, 0, 0, 0) if key == 1 else
                         (255, 0, 255, 0) if key == 2 else
                         (255, 46 + x * 2, 56 + y * 3, 87))
                fmt = "<4B"
            struct.pack_into(fmt, raw, y * rb + x * pb, *value)
    return bytes(raw), rb


def parameter_record(enabled_key: bool = False, edge_blur: float = 0.0,
                     edge_blur_direction: int = 2, key_count: int = 1,
                     edge_blur_distance_type: int = 2) -> bytes:
    payload = bytearray(_original_parameter_record(True, float(CURRENT_MODE["blur"]), 2, 2, 2))
    payload[0x24] = 1  # Color Keep: replacement is visible only on this branch.
    struct.pack_into("<i", payload, 0x28, int(CURRENT_MODE["thin"]))
    payload[0x4D] = int(CURRENT_REPLACE)
    for i, rgb in enumerate(REPLACEMENTS):
        payload[0x53D + i] = int(CURRENT_REPLACE)
        struct.pack_into("<3f", payload, 0x208 + i * 0x10, *rgb)
    return bytes(payload)


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=13,H=11,P=8;struct Mode{int thin;float blur;};const Mode modes[]={{0,0},{-4,0},{4,0},{0,4},{-4,4},{4,4}};
for(int replace: {0,1})for(Mode mode:modes)for(int depth: {8,16,32}){
 int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);
 auto keyat=[](int x,int y){bool ring=x>=1&&x<=6&&y>=1&&y<=6&&!(x>=3&&x<=4&&y>=3&&y<=4);bool slope=y>=2&&y<=6&&x>=8&&x<=8+(y-2);bool island=y==9&&(x==10||x==11);return ring||island?1:slope?2:0;};
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){int k=keyat(x,y);auto*q=inb.data()+y*rb+x*ps;
  if(depth==8){auto*v=reinterpret_cast<PF_Pixel8*>(q);*v=k==1?PF_Pixel8{255,0,0,0}:k==2?PF_Pixel8{255,0,255,0}:PF_Pixel8{255,(A_u_char)(46+x*2),(A_u_char)(56+y*3),87};}
  else if(depth==16){auto*v=reinterpret_cast<PF_Pixel16*>(q);*v=k==1?PF_Pixel16{32768,0,0,0}:k==2?PF_Pixel16{32768,0,32768,0}:PF_Pixel16{32768,(A_u_short)(5898+x*410),(A_u_short)(7209+y*468),11141};}
  else{auto*v=reinterpret_cast<PF_PixelFloat*>(q);*v=k==1?PF_PixelFloat{1,0,0,0}:k==2?PF_PixelFloat{1,0,1,0}:PF_PixelFloat{1,.18f+x/80.f,.22f+y/70.f,.34f};}}
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};OLMColorKeyInfo info{};
 info.color_keep=true;info.number_of_colors=2;info.use_color[0]=info.use_color[1]=true;info.colors[0]={1,0,0,0};info.colors[1]={1,0,1,0};
 info.enable_replace=replace;info.use_replace_color[0]=info.use_replace_color[1]=replace;info.replace_colors[0]={1,.90f,.10f,.75f};info.replace_colors[1]={1,.95f,.55f,.05f};
 info.edge_thin_amount=mode.thin;info.edge_thin_distance_type=2;info.edge_blur_amount=mode.blur;info.edge_blur_distance_type=2;info.edge_blur_direction=102;
 if(RenderWorldDirect(&in,&out,info,(short)depth))return depth;std::fwrite(outb.data(),1,outb.size(),stdout);}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_replace_edge_") as raw:
        directory=Path(raw);mac_adapter.compile_probe(directory);source=directory/"olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){","int legacy_main(){",1)+CUSTOM_MAIN)
        sdk=subprocess.run(["xcrun","--show-sdk-path"],capture_output=True,text=True,check=True).stdout.strip();exe=directory/"replace_edge"
        build=subprocess.run(["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-isysroot",sdk,"-I",str(directory),str(source),"-framework","Cocoa","-o",str(exe)],cwd=ROOT,capture_output=True,text=True)
        if build.returncode:raise RuntimeError(build.stderr)
        run=subprocess.run([str(exe)],cwd=ROOT,capture_output=True)
        if run.returncode:raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def alpha_plane(raw: bytes, pb: int) -> bytes:
    rb=WIDTH*pb+PADDING;size=4 if pb==16 else 2 if pb==8 else 1
    return b"".join(raw[y*rb+x*pb:y*rb+x*pb+size] for y in range(HEIGHT) for x in range(WIDTH))


def main() -> int:
    global CURRENT_REPLACE,CURRENT_MODE
    actual_probe.WIDTH,actual_probe.HEIGHT=WIDTH,HEIGHT;actual_probe.fixture=fixture;actual_probe.parameter_record=parameter_record
    actual={}
    for replace in (False,True):
        for mode in MODES:
            CURRENT_REPLACE,CURRENT_MODE=replace,mode
            for fmt in FORMATS:
                actual_probe.PIXEL_FORMAT=fmt;actual[(replace,mode["name"],fmt)]=actual_probe.execute_case(actual_probe.AEX,True,float(mode["blur"]),"single",2,2,2)
    candidate=production();offset=0;rows=[];passed=True;outputs={}
    for replace in (False,True):
        for mode in MODES:
            for fmt,pb in FORMATS.items():
                rb=WIDTH*pb+PADDING;size=rb*HEIGHT;prod=candidate[offset:offset+size];offset+=size;case=actual[(replace,mode["name"],fmt)]
                act=b"".join(bytes.fromhex(r)+b"\xCC"*PADDING for r in case["captures"]["output_active_rows_hex"]);exact=act==prod
                hits=case["execution"]["hits"];native=hits["smart_worker"]==1 and hits["parameter_materialize"]==1
                outputs[(replace,mode["name"],fmt)]=act;passed &= exact and native
                callback_counts={}
                for event in case["execution"]["events"]:
                    callback_counts[event["callback"]]=callback_counts.get(event["callback"],0)+1
                rows.append({"replace":replace,"edge_mode":mode["name"],"pixel_format":fmt,"status":"exact" if exact else "mismatch","bytes":size,"native_full_worker_path":native,"actual_worker_status":case["status"],"actual_sha256":hashlib.sha256(act).hexdigest(),"production_sha256":hashlib.sha256(prod).hexdigest(),"alpha_sha256":hashlib.sha256(alpha_plane(act,pb)).hexdigest(),"native_blur_apply_calls":len(case["execution"]["blur_apply_weights"]),"native_callback_counts":callback_counts,"native_temporary_world_sha256":[w["sha256"] for w in case["execution"]["temporary_worlds"]]})
    topology=[]
    for mode in MODES:
        for fmt,pb in FORMATS.items():
            off=outputs[(False,mode["name"],fmt)];on=outputs[(True,mode["name"],fmt)]
            alpha_equal=alpha_plane(off,pb)==alpha_plane(on,pb);rgb_diff=off!=on
            topology.append({"edge_mode":mode["name"],"pixel_format":fmt,"replace_changes_rgb":rgb_diff,"replace_preserves_alpha_topology":alpha_equal});passed &= alpha_equal and rgb_diff
    for replace in (False,True):
        for fmt,pb in FORMATS.items():
            base=alpha_plane(outputs[(replace,"none",fmt)],pb)
            for name in ("thin_negative4","thin_positive4","blur_direction2_amount4",
                         "thin_negative4_blur_direction2_amount4",
                         "thin_positive4_blur_direction2_amount4"):
                passed &= alpha_plane(outputs[(replace,name,fmt)],pb)!=base

            # This fixture deliberately reaches uniform mattes after either
            # Thin sign.  The native worker still executes Blur once per pixel;
            # its output consequently equals the Thin-only result while
            # differing from Blur-only.  Requiring the callback count prevents
            # a false pass from silently skipping the second stage.
            for thin_name, combo_name in (
                ("thin_negative4", "thin_negative4_blur_direction2_amount4"),
                ("thin_positive4", "thin_positive4_blur_direction2_amount4"),
            ):
                combo = outputs[(replace,combo_name,fmt)]
                passed &= combo == outputs[(replace,thin_name,fmt)]
                passed &= combo != outputs[(replace,"blur_direction2_amount4",fmt)]
                combo_row = next(r for r in rows if r["replace"] == replace and
                                 r["edge_mode"] == combo_name and r["pixel_format"] == fmt)
                passed &= combo_row["native_callback_counts"].get("PF_HandleSuite.new_handle",0) == 1
                passed &= combo_row["native_callback_counts"].get("PF_HandleSuite.dispose_handle",0) == 1
                if fmt == "PF16":
                    passed &= combo_row["native_blur_apply_calls"] == WIDTH * HEIGHT
    passed &= offset==len(candidate)
    report={"schema_version":2,"status":"exact" if passed else "mismatch","fixture":{"dimensions":[WIDTH,HEIGHT],"shape":"black asymmetric ring with hole plus green sloped triangle and disconnected black island","replacement_colors":[list(x) for x in REPLACEMENTS],"row_padding_bytes":PADDING},"matrix":{"replace":[False,True],"edge_modes":[x["name"] for x in MODES],"pixel_formats":list(FORMATS)},"native_materialized_parameters":{"edge_thin_distance_type_internal":0,"edge_blur_direction_internal":2,"edge_blur_distance_type_internal":2},"actual_aex_sha256":actual_probe.AEX_SHA256,"comparison":"actual AEX full worker versus production RenderWorldDirect core; full typed ARGB active bytes and every padding byte; public admission is intentionally bypassed","cases":rows,"composition_assertions":topology,"claim_boundary":"Exact only for the declared 13x11 two-key fixture and the recorded internal parameter bytes: Edge Thin Distance Type remains zero-initialized, while Edge Blur uses internal Direction 2 / Distance Type 2 / Amount 4. This does not prove any public Edge Thin Distance Type 1..3 composition tuple, other amounts/directions/geometry, or AE-host execution."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");MD.write_text("# OLMColorKey Replace × Edge composition\n\n"+f"Status: **{report['status']}**\n\nReplace changes RGB while preserving the Edge-derived alpha topology in every depth/mode pair. Every actual-AEX depth executes the Blur lifecycle after Thin, but the retained parameter record leaves Edge Thin Distance Type at internal value 0. The capture therefore remains useful orchestration evidence and is not public-popup conformance evidence.\n\n"+f"Boundary: {report['claim_boundary']}\n")
    print(("PASS" if passed else "FAIL")+f"_OLMCOLORKEY_REPLACE_EDGE_COMPOSITION_ACTUAL_AEX_20260811 cases={len(rows)} bytes={offset}");return 0 if passed else 3


if __name__=="__main__":raise SystemExit(main())
