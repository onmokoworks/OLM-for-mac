#!/usr/bin/env python3
"""Run the bounded ToonDilate matrix through the installed public EffectMain."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from olm_installed_identity import verified_binary


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_installed_dynamic_all_depths_20260806.json"
ACTUAL_REPORT = ROOT / "refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json"
ACTUAL_SUPPORT_REPORTS = (
    ("refs/conformance/olmtoondilate_nonpositive_radius_all_depths_20260805.json", "PASS_NONPOSITIVE_RADIUS_ALL_DEPTHS"),
    ("refs/conformance/olmtoondilate_alpha0_rgb_eligibility_all_depths_20260805.json", "PASS_ALPHA0_RGB_ELIGIBILITY_ALL_DEPTHS"),
    ("refs/conformance/olmtoondilate_corner_seed_all_depths_20260805.json", "PASS_CORNER_SEED_ALL_DEPTHS"),
    ("refs/conformance/olmtoondilate_pf8_radius3_boundary_tie_20260805.json", "PASS_PF8_RADIUS3_BOUNDARY_TIE"),
    ("refs/conformance/olmtoondilate_pf16_radius3_boundary_tie_20260805.json", "PASS_PF16_RADIUS3_BOUNDARY_TIE"),
    ("refs/conformance/olmtoondilate_pf32_radius3_boundary_tie_20260805.json", "PASS_PF32_RADIUS3_BOUNDARY_TIE"),
)
ACTUAL_AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
ACTUAL_AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PROBE = r'''
#include <dlfcn.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>
#include <vector>
#include "AE_Effect.h"

using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);
static PF_EffectWorld *g_input, *g_output;
static double g_radius;
static int g_pre, g_pixels, g_output_hits, g_checkin, g_param, g_param_checkin;
static bool g_preserve_rgb;

static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex, A_long, A_long, A_u_long, PF_ParamDef *p) {
    std::memset(p, 0, sizeof(*p)); p->u.fs_d.value = g_radius; ++g_param; return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *) { ++g_param_checkin; return PF_Err_NONE; }
static PF_Err pre_checkout(PF_ProgPtr, PF_ParamIndex, A_long, const PF_RenderRequest *req, A_long, A_long, A_u_long, PF_CheckoutResult *r) {
    g_preserve_rgb = req && req->preserve_rgb_of_zero_alpha;
    std::memset(r, 0, sizeof(*r)); r->result_rect = {17, 23, 20, 25}; r->max_result_rect = {11, 13, 29, 31};
    r->ref_width = g_input->width; r->ref_height = g_input->height; ++g_pre; return PF_Err_NONE;
}
static PF_Err pixels(PF_ProgPtr, A_long, PF_EffectWorld **w) { *w = g_input; ++g_pixels; return PF_Err_NONE; }
static PF_Err output(PF_ProgPtr, PF_EffectWorld **w) { *w = g_output; ++g_output_hits; return PF_Err_NONE; }
static PF_Err checkin(PF_ProgPtr, A_long) { ++g_checkin; return PF_Err_NONE; }

template <typename P> static bool opaque(const P &p);
template <> bool opaque(const PF_Pixel8 &p) { return p.alpha == 255; }
template <> bool opaque(const PF_Pixel16 &p) { return p.alpha == 32768; }
template <> bool opaque(const PF_PixelFloat &p) { return p.alpha >= 1.0f; }

template <typename P> static P pixel(unsigned kind, int x, int y) {
    const unsigned v = static_cast<unsigned>(x * 17 + y * 29 + 3);
    if constexpr (sizeof(P) == 4) {
        if (kind == 0) return P{0, static_cast<A_u_char>(91 + v % 97), static_cast<A_u_char>(37 + v % 113), static_cast<A_u_char>(11 + v % 127)};
        if (kind == 1) return P{static_cast<A_u_char>(64 + v % 160), static_cast<A_u_char>(13 + v % 211), static_cast<A_u_char>(19 + v % 197), static_cast<A_u_char>(23 + v % 191)};
        return P{255, static_cast<A_u_char>(31 + v % 181), static_cast<A_u_char>(47 + v % 173), static_cast<A_u_char>(59 + v % 167)};
    } else if constexpr (sizeof(P) == 8) {
        if (kind == 0) return P{0, static_cast<A_u_short>(41001 + v % 7000), static_cast<A_u_short>(30002 + v % 7000), static_cast<A_u_short>(20003 + v % 7000)};
        if (kind == 1) return P{static_cast<A_u_short>(4096 + v % 24000), static_cast<A_u_short>(1001 + v % 19000), static_cast<A_u_short>(2002 + v % 17000), static_cast<A_u_short>(3003 + v % 15000)};
        return P{32768, static_cast<A_u_short>(4001 + v % 19000), static_cast<A_u_short>(5002 + v % 17000), static_cast<A_u_short>(6003 + v % 15000)};
    } else {
        const float f = static_cast<float>(v % 101) / 128.0f;
        if (kind == 0) return P{0.0f, 0.75f + f, 0.5f + f, 0.25f + f};
        if (kind == 1) return P{0.5f, 0.125f + f, 0.25f + f, 0.375f + f};
        return P{1.0f, 0.1875f + f, 0.3125f + f, 0.4375f + f};
    }
}

template <typename P> static std::vector<P> oracle(std::vector<P> src, int w, int h, int radius) {
    if (radius <= 0) return src;
    const uint32_t INF = std::numeric_limits<uint32_t>::max();
    std::vector<uint32_t> dist(static_cast<size_t>(w) * h, INF);
    bool seeded = false;
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) if (opaque(src[y*w+x])) { dist[y*w+x] = 0; seeded = true; }
    if (!seeded) return src;
    auto relax = [&](int x, int y, const int offsets[][2]) {
        const size_t idx = static_cast<size_t>(y)*w+x; if (dist[idx] == 0) return;
        uint32_t best = INF; int bx = -1, by = -1;
        for (int i=0;i<4;++i) { int nx=x+offsets[i][0], ny=y+offsets[i][1]; if(nx<0||nx>=w||ny<0||ny>=h) continue; uint32_t d=dist[static_cast<size_t>(ny)*w+nx]; if(d<best){best=d;bx=nx;by=ny;} }
        if (best == INF || best + 1 >= dist[idx]) return; dist[idx] = best + 1; if (best + 1 <= static_cast<uint32_t>(radius)) src[idx] = src[static_cast<size_t>(by)*w+bx];
    };
    const int fw[4][2]={{-1,0},{-1,-1},{0,-1},{1,-1}}, bw[4][2]={{1,0},{1,1},{0,1},{-1,1}};
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) relax(x,y,fw);
    for(int y=h-1;y>=0;--y) for(int x=w-1;x>=0;--x) relax(x,y,bw);
    return src;
}

struct Result { bool pass; std::string name; unsigned long long words; };
template <typename P> static Result run_case(Effect effect, short depth, const char *family, int w, int h, double radius, int ds_num, int ds_den) {
    constexpr int PAD=13, GUARD=19; const int rowbytes=w*static_cast<int>(sizeof(P))+PAD; const size_t payload=static_cast<size_t>(rowbytes)*h;
    std::vector<unsigned char> ib(GUARD+payload+GUARD,0xC7), ob(GUARD+payload+GUARD,0xD9); std::vector<P> source(static_cast<size_t>(w)*h);
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) source[static_cast<size_t>(y)*w+x]=pixel<P>(1,x,y);
    if(!std::strcmp(family,"copy")) { for(int y=0;y<h;++y) for(int x=0;x<w;++x) source[static_cast<size_t>(y)*w+x]=pixel<P>((x+y)%3,x,y); }
    else if(!std::strcmp(family,"fractional")) { source[0]=pixel<P>(2,0,0); source[static_cast<size_t>(h/2)*w+w/2]=pixel<P>(2,w/2,h/2); source.back()=pixel<P>(0,w-1,h-1); }
    else { source[static_cast<size_t>(h/2)*w]=pixel<P>(2,0,h/2); source[static_cast<size_t>(h/2)*w+w-1]=pixel<P>(2,w-1,h/2); source[static_cast<size_t>(h/2)*w+w/2]=pixel<P>(1,w/2,h/2); }
    for(int y=0;y<h;++y){ std::memcpy(ib.data()+GUARD+static_cast<size_t>(y)*rowbytes,source.data()+static_cast<size_t>(y)*w,static_cast<size_t>(w)*sizeof(P)); std::memset(ib.data()+GUARD+static_cast<size_t>(y)*rowbytes+w*sizeof(P),0xA5,PAD); std::memset(ob.data()+GUARD+static_cast<size_t>(y)*rowbytes+w*sizeof(P),0xEE,PAD); }
    PF_EffectWorld input{}, destination{}; input.data=reinterpret_cast<PF_PixelPtr>(ib.data()+GUARD); input.rowbytes=rowbytes; input.width=w; input.height=h; input.extent_hint={101,201,101+w,201+h}; destination.data=reinterpret_cast<PF_PixelPtr>(ob.data()+GUARD); destination.rowbytes=rowbytes; destination.width=w; destination.height=h; destination.extent_hint={301,401,301+w,401+h};
    const PF_EffectWorld input_before=input, output_before=destination; g_input=&input;g_output=&destination;g_radius=radius;g_pre=g_pixels=g_output_hits=g_checkin=g_param=g_param_checkin=0;g_preserve_rgb=false;
    PF_InData in{};PF_OutData out{};in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;in.downsample_x.num=ds_num;in.downsample_x.den=ds_den;
    PF_PreRenderInput pi{};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};const PF_Err pre_err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
    PF_SmartRenderInput si{};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=pixels;scb.checkout_output=output;scb.checkin_layer_pixels=checkin;PF_SmartRenderExtra se{&si,&scb};const PF_Err render_err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
    const int effective=radius<=0?0:static_cast<int>(std::ceil(radius*ds_num/ds_den));const auto expected=oracle(source,w,h,effective);bool exact=pre_err==0&&render_err==0&&g_pre==1&&g_pixels==1&&g_output_hits==1&&g_checkin==1&&g_param==1&&g_param_checkin==1&&g_preserve_rgb;
    exact=exact&&std::memcmp(&input,&input_before,sizeof(input))==0&&std::memcmp(&destination,&output_before,sizeof(destination))==0;
    for(int y=0;y<h;++y){exact=exact&&std::memcmp(ob.data()+GUARD+static_cast<size_t>(y)*rowbytes,expected.data()+static_cast<size_t>(y)*w,static_cast<size_t>(w)*sizeof(P))==0;for(int i=w*sizeof(P);i<rowbytes;++i)exact=exact&&ob[GUARD+static_cast<size_t>(y)*rowbytes+i]==0xEE;}
    for(int i=0;i<GUARD;++i) exact=exact&&ib[i]==0xC7&&ib[GUARD+payload+i]==0xC7&&ob[i]==0xD9&&ob[GUARD+payload+i]==0xD9;
    if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);char name[128];std::snprintf(name,sizeof(name),"PF%d_%s",depth,family);return {exact,name,static_cast<unsigned long long>(w)*h*4};
}

template <typename P> static bool run_depth(Effect effect, short depth, std::vector<Result>& rows) {
    rows.push_back(run_case<P>(effect,depth,"copy",7,5,0.0,1,1));
    rows.push_back(run_case<P>(effect,depth,"fractional",9,7,2.01,1,1));
    rows.push_back(run_case<P>(effect,depth,"tie_semialpha",7,3,3.0,1,1));
    rows.push_back(run_case<P>(effect,depth,"high_downsample",513,17,100.0,2,1));
    return std::all_of(rows.end()-4,rows.end(),[](const Result&r){return r.pass;});
}
int main(int argc,char**argv){void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h){std::fprintf(stderr,"%s",dlerror());return 2;}auto effect=reinterpret_cast<Effect>(dlsym(h,"EffectMain"));if(!effect)return 3;std::vector<Result> rows;bool ok=run_depth<PF_Pixel8>(effect,8,rows)&&run_depth<PF_Pixel16>(effect,16,rows)&&run_depth<PF_PixelFloat>(effect,32,rows);std::printf("{\"cases\":[");for(size_t i=0;i<rows.size();++i)std::printf("%s{\"id\":\"%s\",\"raw_exact\":%s,\"compared_words\":%llu}",i?",":"",rows[i].name.c_str(),rows[i].pass?"true":"false",rows[i].words);std::printf("],\"all_exact\":%s}\n",ok?"true":"false");dlclose(h);return ok?0:4;}
'''


def verify_actual_boundary() -> dict:
    if sha256(ACTUAL_AEX) != ACTUAL_AEX_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: OLMToonDilate AEX identity drifted")
    actual = json.loads(ACTUAL_REPORT.read_text(encoding="utf-8"))
    gates = actual.get("gates", {})
    required = (
        "smart_pre_entry_returned", "smart_render_entry_returned",
        "downsample_radius_matrix_all_depths_exact",
        "high_radius_downsample_competing_seed_matrix_exact",
        "radius3_pf8_5x1_exact", "radius3_pf16_5x1_exact", "radius3_pf32_5x1_exact",
    )
    if actual.get("status") != "PASS_SEQUENCE_AND_SMARTPRE_ENTRY" or not all(gates.get(k) for k in required):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: actual-AEX covering evidence is incomplete")
    support = []
    for relative, expected_status in ACTUAL_SUPPORT_REPORTS:
        path = ROOT / relative
        evidence = json.loads(path.read_text(encoding="utf-8"))
        if evidence.get("status") != expected_status or not all(evidence.get("gates", {}).values()):
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: actual-AEX support evidence incomplete: {relative}")
        support.append({"path": relative, "sha256": sha256(path), "status": expected_status})
    return {"path": str(ACTUAL_REPORT.relative_to(ROOT)), "sha256": sha256(ACTUAL_REPORT), "aex_sha256": ACTUAL_AEX_SHA256, "support": support}


def main() -> int:
    actual_boundary = verify_actual_boundary()
    binary, identity = verified_binary("OLMToonDilate")
    compiler = shutil.which("clang++")
    if not compiler:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: clang++ unavailable")
    with tempfile.TemporaryDirectory(prefix="toondilate_installed_matrix_") as temp:
        temp_path = Path(temp)
        source, executable = temp_path / "probe.cpp", temp_path / "probe"
        source.write_text(PROBE, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        build = subprocess.run([compiler, "-std=c++17", "-O2", "-arch", "arm64", "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(source), "-o", str(executable)], capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: probe build failed\n{build.stderr}")
        run = subprocess.run([str(executable), str(binary)], capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: probe failed rc={run.returncode}\n{run.stdout}\n{run.stderr}")
    result = json.loads(run.stdout)
    report = {
        "status": "PASS_INSTALLED_DYNAMIC_COVERING_MATRIX",
        "installed_binary": str(binary), "binary_sha256": identity["sha256"], "architecture": "arm64",
        "commands": ["PF_Cmd_SMART_PRE_RENDER", "PF_Cmd_SMART_RENDER"],
        "actual_aex_boundary": actual_boundary,
        "matrix": {"depths": [8, 16, 32], "families": ["radius0_copy", "radius2.01_corner_frontier", "radius3_tie_semialpha_nonseed", "radius100_513x17_downsample2/1"], "case_count": 12},
        "cases": result["cases"],
        "gates": {"dlopen_effectmain": True, "all_12_raw_exact": result["all_exact"], "padding_and_guards_exact": result["all_exact"], "callback_lifecycle_exact": result["all_exact"], "world_headers_unchanged": result["all_exact"], "preserve_rgb_of_zero_alpha_requested": result["all_exact"]},
        "claim_boundary": "Current installed arm64 EffectMain under focused AE-free callbacks, connected to the checked-in actual-AEX covering evidence. No broader real-AE-host claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT.with_suffix(".md").write_text(
        "# OLMToonDilate installed public covering matrix — 2026-08-12\n\n"
        "- Status: **PASS_INSTALLED_DYNAMIC_COVERING_MATRIX**\n"
        f"- Current installed arm64 binary SHA-256: `{identity['sha256']}`.\n"
        "- Public `EffectMain` SmartPreRender → SmartRender covers PF8/PF16/PF32 × four semantic families (12/12 raw-exact).\n"
        "- Families: radius-0 mixed-alpha copy; radius-2.01 odd padded corner/frontier; radius-3 competing tie with semi-alpha nonseed; radius-100 513×17 downsample 2/1.\n"
        "- Every cell checks visible typed words, row padding, allocation guards, unchanged world headers, preserve-RGB request, and checkout/checkin lifecycle.\n"
        f"- The expected behavior is bound to actual AEX `{ACTUAL_AEX_SHA256}` and `{actual_boundary['path']}` (`{actual_boundary['sha256']}`).\n"
        "- This is an AE-free installed-binary boundary; it does not broaden the real AE-host claim.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
