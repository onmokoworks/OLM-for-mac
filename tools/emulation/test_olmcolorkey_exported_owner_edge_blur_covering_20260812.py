#!/usr/bin/env python3
"""Actual exported ColorKey Edge Blur owner versus production EffectMain."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import test_olmcolorkey_mac_smartrender_adapter_20260717 as adapter  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
REPORT = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_covering_20260812.json"
DOC = REPORT.with_suffix(".md")
DEFAULT_WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites/guest/target/release/aex-guest-worker")
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
WORKER_SHA256 = "16c329a481aef88c00fd6016e79996eecaabf7a588cff084e866b6bd15d411fc"
WIDTH, HEIGHT, PADDING = 32, 18, 8
DEPTHS = {"PF8": ("argb8", 4), "PF16": ("argb16", 8), "PF32": ("argb32f", 16)}
TUPLES = ((1, 1, 1.0), (1, 3, 4.0), (2, 2, 1.0),
          (2, 1, 4.0), (3, 3, 1.0), (3, 2, 4.0))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def keyed_kind(x: int, y: int) -> int:
    black = ((x in (2, WIDTH - 3) and y in (2, HEIGHT - 3)) or
             (WIDTH // 2 - 1 <= x <= WIDTH // 2 + 1 and
              HEIGHT // 2 - 1 <= y <= HEIGHT // 2 + 1) or
             (y == HEIGHT // 3 and WIDTH // 4 <= x < WIDTH // 4 + 5))
    if black:
        return 1
    green = ((x, y) in {(WIDTH // 3, HEIGHT // 2),
                        (WIDTH // 3 + 1, HEIGHT // 2),
                        (WIDTH * 2 // 3, HEIGHT // 3),
                        (WIDTH * 2 // 3, HEIGHT * 2 // 3),
                        (WIDTH // 2, HEIGHT // 4)})
    return 2 if green else 0


def rgba_fixture() -> tuple[tuple[int, int, int, int], ...]:
    pixels = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            kind = keyed_kind(x, y)
            alpha = 48 + ((x * 29 + y * 43) % 192)
            if kind == 1:
                rgb = (0, 0, 0)
            elif kind == 2:
                rgb = (0, 255, 0)
            else:
                rgb = (32 + (x % 16) * 8, 64 + (y % 16) * 8, 96)
            pixels.append((*rgb, alpha))
    return tuple(pixels)


RGBA = rgba_fixture()


def owner_params(direction: int, distance: int, amount: float) -> list[str]:
    return [
        "Color Keep=0", "Premultiplied Color=0", "Number of Colors=2",
        "Use Color 1=1", "Color 1=255,0,0,0",
        "Use Color 2=1", "Color 2=255,0,255,0",
        f"Amount@18={amount:g}",
        f"Distance Type@19={distance}",
        f"Direction@20={direction}",
    ]


HARNESS = r'''
static std::vector<int> g_checkout_order; static int g_checkins=0; static int g_case=0;
static const int g_dirs[]={1,1,2,2,3,3};
static const int g_dists[]={1,3,2,1,3,2};
static const double g_amounts[]={1,4,1,4,1,4};
static PF_Err color_from_def(PF_ProgPtr,PF_ParamDef*p,PF_PixelFloat*out){out->alpha=p->u.cd.value.alpha/255.f;out->red=p->u.cd.value.red/255.f;out->green=p->u.cd.value.green/255.f;out->blue=p->u.cd.value.blue/255.f;return 0;}
static PF_Err checkout_param(PF_InData*,A_long i,A_long,A_long,A_long,PF_ParamDef*p){std::memset(p,0,sizeof(*p));g_checkout_order.push_back(i);if(i==OLMCOLORKEY_COLOR_SPACE||i==OLMCOLORKEY_FORCE_LOWER_PRECISION)p->u.pd.value=1;else if(i==OLMCOLORKEY_NUMBER_OF_COLORS)p->u.sd.value=2;else if(i==OLMCOLORKEY_EDGE_BLUR_AMOUNT)p->u.fs_d.value=g_amounts[g_case];else if(i==OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE)p->u.pd.value=g_dists[g_case];else if(i==OLMCOLORKEY_EDGE_BLUR_DIRECTION)p->u.pd.value=g_dirs[g_case];else if(i==OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE)p->u.pd.value=2;else if(i==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_USE_COLOR||i==OLMCOLORKEY_COLOR_FIRST+COLOR_PARAM_STRIDE+COLOR_OFFSET_USE_COLOR)p->u.bd.value=true;else if(i==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_COLOR)p->u.cd.value={255,0,0,0};else if(i==OLMCOLORKEY_COLOR_FIRST+COLOR_PARAM_STRIDE+COLOR_OFFSET_COLOR)p->u.cd.value={255,0,255,0};return 0;}
static void checkin_param(PF_InData*,PF_ParamDef*){g_checkins++;}
static PF_ColorParamSuite1 g_color_suite_instance={color_from_def}; static PF_ANSICallbacksSuite1 g_ansi_suite_instance={&std::sprintf};
namespace { struct State{PF_EffectWorld*input,*output;int pre=0,pixels=0,out=0,layer_checkin=0;bool preserve=true;}; State*st(PF_ProgPtr p){return static_cast<State*>(p);} PF_Err pre(PF_ProgPtr p,A_long,A_long,PF_RenderRequest*r,A_long,A_long,A_long,PF_CheckoutResult*o){st(p)->pre++;st(p)->preserve=r->preserve_rgb_of_zero_alpha;o->result_rect={0,0,32,18};o->max_result_rect=o->result_rect;return 0;} PF_Err pixels(PF_ProgPtr p,A_long,PF_EffectWorld**o){st(p)->pixels++;*o=st(p)->input;return 0;} PF_Err output(PF_ProgPtr p,PF_EffectWorld**o){st(p)->out++;*o=st(p)->output;return 0;} PF_Err layer_checkin(PF_ProgPtr p,A_long){st(p)->layer_checkin++;return 0;} }
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;constexpr int W=32,H=18,P=8;for(g_case=0;g_case<6;g_case++)for(int depth:{8,16,32}){int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);for(int y=0;y<H;y++)for(int x=0;x<W;x++){bool black=((x==2||x==W-3)&&(y==2||y==H-3))||(x>=W/2-1&&x<=W/2+1&&y>=H/2-1&&y<=H/2+1)||(y==H/3&&x>=W/4&&x<W/4+5);bool green=(x==W/3&&y==H/2)||(x==W/3+1&&y==H/2)||(x==W*2/3&&y==H/3)||(x==W*2/3&&y==H*2/3)||(x==W/2&&y==H/4);int a=48+((x*29+y*43)%192),r=black||green?0:32+(x%16)*8,g=black?0:(green?255:64+(y%16)*8),b=black||green?0:96;auto*q=inb.data()+y*rb+x*ps;if(depth==8)*reinterpret_cast<PF_Pixel8*>(q)={(A_u_char)a,(A_u_char)r,(A_u_char)g,(A_u_char)b};else if(depth==16)*reinterpret_cast<PF_Pixel16*>(q)={(A_u_short)std::lround(a*32768.0/255.0),(A_u_short)std::lround(r*32768.0/255.0),(A_u_short)std::lround(g*32768.0/255.0),(A_u_short)std::lround(b*32768.0/255.0)};else *reinterpret_cast<PF_PixelFloat*>(q)={a/255.f,r/255.f,g/255.f,b/255.f};}auto before=inb;PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};State state{&in,&out};PF_InData id{&state,7,1,24,nullptr};PF_OutData od{};PF_RenderRequest rr{false};PF_PreRenderInput pri{rr};PF_PreRenderOutput pro{};PF_PreRenderCallbacks prc{pre};PF_PreRenderExtra prex{&pri,&pro,&prc};g_checkout_order.clear();g_checkins=0;if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&prex))return 10;PF_SmartRenderInput sri{(A_short)depth,pro.pre_render_data};PF_SmartRenderCallbacks src{pixels,output,layer_checkin};PF_SmartRenderExtra sre{&sri,&src};if(EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&sre))return 11;bool input_same=inb==before,input_pad=true,output_pad=true;for(int y=0;y<H;y++)for(int i=W*ps;i<rb;i++){input_pad&=inb[y*rb+i]==0xA5;output_pad&=outb[y*rb+i]==0xCC;}bool order=g_checkout_order.size()==33&&g_checkout_order.front()==1&&g_checkout_order[15]==22&&g_checkout_order[16]==23&&g_checkout_order.back()==35;bool gates=state.pre==1&&state.pixels==1&&state.out==1&&state.layer_checkin==1&&!state.preserve&&g_checkins==33&&order&&input_same&&input_pad&&output_pad;if(!gates){std::fprintf(stderr,"fail case=%d depth=%d callbacks=%d/%d/%d/%d params=%zu/%d order=%d input=%d pads=%d/%d\n",g_case,depth,state.pre,state.pixels,state.out,state.layer_checkin,g_checkout_order.size(),g_checkins,order,input_same,input_pad,output_pad);return 20;}for(int y=0;y<H;y++)std::fwrite(outb.data()+y*rb,1,W*ps,stdout);if(pro.delete_pre_render_data_func)pro.delete_pre_render_data_func(pro.pre_render_data);}return 0;}
'''


def production_effectmain() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_edge_owner_prod_") as raw:
        directory = Path(raw)
        adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        generated = source.read_text()
        generated = generated.replace("#define PF_CHECKIN_PARAM(...) ((void)0)",
                                      "#define PF_CHECKIN_PARAM(in,p) checkin_param((in),(p))")
        generated = generated.replace(
            "static PF_Err checkout_param(PF_InData*,A_long,A_long,A_long,A_long,PF_ParamDef*);",
            "static PF_Err checkout_param(PF_InData*,A_long,A_long,A_long,A_long,PF_ParamDef*); static void checkin_param(PF_InData*,PF_ParamDef*);")
        generated = generated.split("static std::vector<int> g_param_order", 1)[0] + HARNESS
        source.write_text(generated)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                             text=True, check=True).stdout.strip()
        executable = directory / "effectmain"
        build = subprocess.run(["clang++", "-std=c++17", "-arch", "arm64", "-O2",
                                "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
                                "-I", str(directory), str(source), "-framework", "Cocoa",
                                "-o", str(executable)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def main() -> int:
    if sha(AEX) != AEX_SHA256:
        raise RuntimeError("pinned ColorKey AEX hash drift")
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(DEFAULT_WORKER)))
    if not worker.is_file() or sha(worker) != WORKER_SHA256:
        raise RuntimeError("pinned typed-iterate AEXCompat worker missing or drifted")
    expected_all = production_effectmain()
    expected_offset, rows = 0, []
    with tempfile.TemporaryDirectory(prefix="olmck_edge_exported_owner_") as raw:
        directory = Path(raw)
        input_png = directory / "input.png"
        image = Image.new("RGBA", (WIDTH, HEIGHT)); image.putdata(RGBA); image.save(input_png)
        input_png_sha = sha(input_png)
        for direction, distance, amount in TUPLES:
            name = f"direction{direction}_distance{distance}_amount{amount:g}"
            for depth, (pixel_format, pixel_bytes) in DEPTHS.items():
                size = WIDTH * HEIGHT * pixel_bytes
                expected = expected_all[expected_offset:expected_offset + size]
                expected_offset += size
                output = directory / f"{name}_{depth}.png"
                command = [str(worker), "render-png", str(AEX), str(input_png), str(output),
                           "--pixel-format", pixel_format,
                           *owner_params(direction, distance, amount)]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                if result.returncode:
                    raise RuntimeError(f"exported owner failed {name} {depth}: {result.stderr}")
                actual = json.loads(result.stdout)
                expected_sha = hashlib.sha256(expected).hexdigest()
                exact = (actual["render_error"] == 0 and
                         actual["raw_pixel_bytes"] == size and
                         actual["raw_pixel_sha256"] == expected_sha and
                         actual["gpu"]["pre_render"]["completed"] and
                         actual["gpu"]["render"]["completed"] and
                         not actual["unsupported_suite_calls"] and
                         actual["dropped_unsupported_suite_calls"] == 0)
                if not exact:
                    raise RuntimeError(f"owner mismatch {name} {depth}: "
                                       f"actual={actual['raw_pixel_sha256']} expected={expected_sha} "
                                       f"params={actual['parameter_values']}")
                rows.append({"case": name, "direction": direction, "distance_type": distance,
                             "amount": amount, "depth": depth, "bytes": size,
                             "actual_exported_raw_sha256": actual["raw_pixel_sha256"],
                             "production_effectmain_raw_sha256": expected_sha,
                             "smart_pre_render": actual["gpu"]["pre_render"],
                             "smart_render": actual["gpu"]["render"],
                             "suite_requests": actual["suite_requests"], "status": "exact"})
    if expected_offset != len(expected_all) or len(rows) != 18:
        raise RuntimeError("matrix slicing/count drift")
    report = {
        "schema": "olmcolorkey.exported-owner-edge-covering/1", "status": "exact",
        "actual_aex_sha256": AEX_SHA256,
        "aexcompat_worker": {"path": str(worker), "sha256": sha(worker)},
        "fixture": {"dimensions": [WIDTH, HEIGHT], "alpha8_range": [48, 239],
                    "keys": ["black", "green"], "source_png_sha256": input_png_sha,
                    "row_padding_bytes": PADDING},
        "covering_tuples": [{"direction": d, "distance_type": t, "amount": a}
                            for d, t, a in TUPLES],
        "owner_chain": ["actual exported SmartPreRender", "parameter materialization",
                        "typed world checkout", "worker/writer", "actual exported SmartRender"],
        "production_chain": ["Mac EffectMain SmartPreRender", "33 ordered parameter checkouts",
                             "Mac EffectMain SmartRender", "typed RenderWorld", "33 checkins"],
        "production_gates": {"checkout_layer": 1, "checkout_layer_pixels": 1,
                             "checkout_output": 1, "checkin_layer_pixels": 1,
                             "parameter_checkouts": 33, "parameter_checkins": 33,
                             "input_complete_buffer_unchanged": True,
                             "input_padding_preserved": True, "output_padding_preserved": True},
        "cases": rows, "production_source_sha256": sha(SOURCE),
        "claim_boundary": ("Exact only for the declared 32x18 semitransparent two-key fixture, "
                           "six public Direction/Distance/Amount covering tuples, and PF8/PF16/PF32. "
                           "Unlisted values, arbitrary geometry, native Windows, and AE-host execution "
                           "remain fail-closed/unclaimed."),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLMColorKey exported-owner Edge Blur covering\n\n"
                   "Status: **exact**\n\n"
                   "Actual exported SmartPreRender/SmartRender and Mac production EffectMain "
                   "match raw output for all 18 declared cells. Production verifies ordered "
                   "checkout/checkin, input immutability, and eight-byte input/output row padding.\n\n"
                   f"Boundary: {report['claim_boundary']}\n")
    print(json.dumps({"status": "exact", "cases": len(rows), "report": str(REPORT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
