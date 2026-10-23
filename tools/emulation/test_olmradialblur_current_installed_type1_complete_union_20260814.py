#!/usr/bin/env python3
"""Replay the complete proven Radial Type1 union through installed public entries."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
SHIM = ROOT / "tools/emulation/olmradialblur_installed_effectmain_shim_20260813.h"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
BUILD_IDENTITY = ROOT / "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814/build_identity.json"
INSTALL_IDENTITY = ROOT / "refs/conformance/olmradialblur_worldsuite_lifecycle_install_20260814.json"
REPORT = ROOT / "refs/conformance/olmradialblur_current_installed_type1_complete_union_20260814.json"
NOTE = REPORT.with_suffix(".md")

FAMILIES = (
    ("pairwise", "tools/emulation/probe_olmradialblur_type1_pairwise_source_guard_20260813.cpp",
     "refs/conformance/olmradialblur_type1_pairwise_source_guard_readiness_20260813.json", 16, 12),
    ("edge_noise", "tools/emulation/probe_olmradialblur_type1_edge_noise_source_guard_20260813.cpp",
     "refs/conformance/olmradialblur_type1_edge_noise_source_guard_20260813.json", 24, 9),
    ("size_noise", "tools/emulation/probe_olmradialblur_type1_size_noise_source_guard_20260813.cpp",
     "refs/conformance/olmradialblur_type1_size_noise_source_guard_20260813.json", 36, 9),
    ("dual_strength", "tools/emulation/probe_olmradialblur_type1_dual_strength_source_guard_20260813.cpp",
     "refs/conformance/olmradialblur_type1_dual_strength_source_guard_20260813.json", 18, 18),
    ("any_size_edge_noise", "tools/emulation/probe_olmradialblur_type1_any_size_edge_noise_source_guard_20260813.cpp",
     "refs/conformance/olmradialblur_type1_any_size_edge_noise_source_guard_20260813.json", 12, 9),
)

PINS = {
    "production_source": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
    "installed_binary": "9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5",
    "shim": "7506106dd5b9bac9e0ecd77cff0b13ab8f4e66823a2fe341759039035f28fb49",
    "build_identity": "641af05eec81269738fa65d99fcd59bd0d16f1d28f89eb95bbe8f978c5c6bb93",
    "install_identity": "a5ed6932892caf5dfb5db0d95620af5c05dfe6d70a8aa006eead4da85982d4f3",
}
STATUS = "PASS_OLMRADIALBLUR_CURRENT_INSTALLED_TYPE1_COMPLETE_UNION_AE_FREE"
CLAIM = (
    "The current installed arm64 and Rosetta x86_64 EffectMain Classic and Smart entries "
    "reproduce all 106 exact-source Type1 cells from the five retained source closures and "
    "reject their 57 source-mutation controls without output commit. Each installed wrapper "
    "requires Classic and Smart padded output to match before returning success. This is an "
    "AE-free dlopen replay, not native-AE or arbitrary-source evidence."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        if run.returncode == 0:
            found.extend(f"{name}:{pid}" for pid in run.stdout.split())
    return found


def authorities() -> dict[str, Any]:
    families: dict[str, dict[str, str]] = {}
    for name, probe_name, report_name, _, _ in FAMILIES:
        families[name] = {
            "probe_sha256": sha256(ROOT / probe_name),
            "source_closure_sha256": sha256(ROOT / report_name),
        }
    return {
        "production_source": sha256(SOURCE),
        "installed_binary": sha256(INSTALLED),
        "shim": sha256(SHIM),
        "build_identity": sha256(BUILD_IDENTITY),
        "install_identity": sha256(INSTALL_IDENTITY),
        "families": families,
    }


def wrapper_text() -> str:
    source = str(SOURCE).replace('"', '\\"')
    shim = str(SHIM).replace('"', '\\"')
    return f'''#pragma once
#define EffectMain SourceBuiltOLMRadialBlurEffectMain
#include "{source}"
#undef EffectMain
#include "{shim}"
#include <cmath>
#include <cstring>
#include <vector>

static int g_installed_depth=8;
static PF_Err InstalledGetFormat(const PF_EffectWorld*,PF_PixelFormat*f){{
 if(!f)return PF_Err_BAD_CALLBACK_PARAM;
 *f=g_installed_depth==8?PF_PixelFormat_ARGB32:(g_installed_depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128);
 return PF_Err_NONE;
}}
static PF_WorldSuite2 g_installed_world_suite{{nullptr,nullptr,InstalledGetFormat}};
static SPErr InstalledAcquire(const char*n,int32 v,const void**s){{
 if(!n||!s||std::strcmp(n,kPFWorldSuite)||v!=kPFWorldSuiteVersion2)return kSPBadParameterError;
 *s=&g_installed_world_suite;return kSPNoError;
}}
static SPErr InstalledRelease(const char*,int32){{return kSPNoError;}}
static SPBasicSuite g_installed_basic{{InstalledAcquire,InstalledRelease}};

static void InstalledFillParam(A_long n,PF_ParamDef&p,PF_EffectWorld*iw,const OLMRadialBlurInfo&i){{
 AEFX_CLR_STRUCT(p);
 if(n==OLMRADIALBLUR_INPUT)p.u.ld=*iw;
 else if(n==OLMRADIALBLUR_BLUR_TYPE)p.u.pd.value=i.blur_type;
 else if(n==OLMRADIALBLUR_CENTER){{p.u.td.x_value=(A_long)std::llround(i.center_x*65536.0);p.u.td.y_value=(A_long)std::llround(i.center_y*65536.0);}}
 else if(n==OLMRADIALBLUR_OUTER_STRENGTH)p.u.sd.value=i.outer_strength;
 else if(n==OLMRADIALBLUR_OUTER_EDGE_FADE)p.u.fs_d.value=i.outer_edge_fade;
 else if(n==OLMRADIALBLUR_OUTER_OFFSET_MODE)p.u.pd.value=i.outer_offset_mode;
 else if(n==OLMRADIALBLUR_OUTER_OFFSET)p.u.sd.value=i.outer_offset;
 else if(n==OLMRADIALBLUR_INNER_STRENGTH)p.u.sd.value=i.inner_strength;
 else if(n==OLMRADIALBLUR_INNER_EDGE_FADE)p.u.fs_d.value=i.inner_edge_fade;
 else if(n==OLMRADIALBLUR_INNER_OFFSET_MODE)p.u.pd.value=i.inner_offset_mode;
 else if(n==OLMRADIALBLUR_INNER_OFFSET)p.u.sd.value=i.inner_offset;
 else if(n==OLMRADIALBLUR_REPEAT_BORDER)p.u.bd.value=i.repeat_border;
 else if(n==OLMRADIALBLUR_RATIO)p.u.fs_d.value=i.ratio;
 else if(n==OLMRADIALBLUR_ANGLE)p.u.fs_d.value=i.angle_deg;
 else if(n==OLMRADIALBLUR_QUALITY)p.u.fs_d.value=i.quality;
 else if(n==OLMRADIALBLUR_BRIGHTNESS_GAIN)p.u.fs_d.value=i.brightness_gain;
 else if(n==OLMRADIALBLUR_SIZE_VARIATION)p.u.fs_d.value=i.size_variation;
 else if(n==OLMRADIALBLUR_NOISE_VARIATION)p.u.fs_d.value=i.noise_variation;
 else if(n==OLMRADIALBLUR_NOISE_TYPE)p.u.pd.value=i.noise_type;
 else if(n==OLMRADIALBLUR_NOISE_LAYER)p.u.ld.dephault=i.noise_layer;
 else if(n==OLMRADIALBLUR_SEED)p.u.sd.value=i.seed;
 else if(n==OLMRADIALBLUR_NOISE_OFFSET)p.u.sd.value=i.noise_offset;
 else if(n==OLMRADIALBLUR_THICKNESS)p.u.fs_d.value=i.thickness;
}}
struct InstalledHost{{PF_EffectWorld*iw;PF_EffectWorld*ow;const OLMRadialBlurInfo*info;int pre=0,pixel=0,output=0,checkin=0,param_out=0,param_in=0;}};
static PF_Err InstalledCheckoutParam(PF_ProgPtr q,A_long n,A_long,A_long,A_u_long,PF_ParamDef*p){{auto*h=(InstalledHost*)q;if(!h||!p)return PF_Err_BAD_CALLBACK_PARAM;++h->param_out;InstalledFillParam(n,*p,h->iw,*h->info);return PF_Err_NONE;}}
static PF_Err InstalledCheckinParam(PF_ProgPtr q,PF_ParamDef*){{auto*h=(InstalledHost*)q;++h->param_in;return PF_Err_NONE;}}
static PF_Err InstalledPreLayer(PF_ProgPtr q,PF_ParamIndex n,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){{auto*h=(InstalledHost*)q;if(!h||!r||n!=OLMRADIALBLUR_INPUT)return PF_Err_BAD_CALLBACK_PARAM;++h->pre;AEFX_CLR_STRUCT(*r);r->result_rect={{0,0,h->iw->width,h->iw->height}};r->max_result_rect=r->result_rect;r->ref_width=h->iw->width;r->ref_height=h->iw->height;return PF_Err_NONE;}}
static PF_Err InstalledPixelLayer(PF_ProgPtr q,A_long n,PF_EffectWorld**w){{auto*h=(InstalledHost*)q;if(!h||!w||n!=OLMRADIALBLUR_INPUT)return PF_Err_BAD_CALLBACK_PARAM;++h->pixel;*w=h->iw;return PF_Err_NONE;}}
static PF_Err InstalledPixelCheckin(PF_ProgPtr q,A_long){{++((InstalledHost*)q)->checkin;return PF_Err_NONE;}}
static PF_Err InstalledOutput(PF_ProgPtr q,PF_EffectWorld**w){{auto*h=(InstalledHost*)q;if(!h||!w)return PF_Err_BAD_CALLBACK_PARAM;++h->output;*w=h->ow;return PF_Err_NONE;}}
static PF_Err InstalledClassic(PF_EffectWorld&iw,PF_EffectWorld&ow,const OLMRadialBlurInfo&i){{
 PF_ParamDef p[OLMRADIALBLUR_NUM_PARAMS]{{}};PF_ParamDef*pp[OLMRADIALBLUR_NUM_PARAMS]{{}};
 for(int n=0;n<OLMRADIALBLUR_NUM_PARAMS;n++){{pp[n]=&p[n];InstalledFillParam(n,p[n],&iw,i);}}
 PF_InData in{{}};in.pica_basicP=&g_installed_basic;PF_OutData out{{}};
 return EffectMain(PF_Cmd_RENDER,&in,&out,pp,&ow,nullptr);
}}
static PF_Err InstalledSmart(PF_EffectWorld&iw,PF_EffectWorld&ow,const OLMRadialBlurInfo&i,int depth){{
 InstalledHost h{{&iw,&ow,&i}};PF_InData in{{}};in.effect_ref=(PF_ProgPtr)&h;in.current_time=0;in.time_step=1;in.time_scale=1;in.pica_basicP=&g_installed_basic;in.inter.checkout_param=InstalledCheckoutParam;in.inter.checkin_param=InstalledCheckinParam;PF_OutData out{{}};
 PF_PreRenderInput pri{{}};PF_PreRenderOutput pro{{}};PF_PreRenderCallbacks prc{{InstalledPreLayer,nullptr}};PF_PreRenderExtra pre{{&pri,&pro,&prc}};
 PF_Err e=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre);if(e)return e;
 PF_SmartRenderInput sri{{}};sri.bitdepth=depth;sri.pre_render_data=pro.pre_render_data;PF_SmartRenderCallbacks src{{InstalledPixelLayer,InstalledPixelCheckin,InstalledOutput}};PF_SmartRenderExtra x{{&sri,&src}};
 e=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&x);if(pro.delete_pre_render_data_func)pro.delete_pre_render_data_func(pro.pre_render_data);if(e)return e;
 return h.pre==1&&h.pixel==1&&h.output==1&&h.checkin==1&&h.param_out==32&&h.param_in==32?PF_Err_NONE:PF_Err_BAD_CALLBACK_PARAM;
}}
static PF_Err InstalledPublicRenderWorld(PF_EffectWorld*iw,PF_EffectWorld*ow,const OLMRadialBlurInfo*info,int depth){{
 if(!iw||!ow||!info||!iw->data||!ow->data||iw->rowbytes<=0||iw->height<=0||ow->rowbytes!=iw->rowbytes||ow->height!=iw->height)return PF_Err_BAD_CALLBACK_PARAM;
 g_installed_depth=depth;const size_t bytes=(size_t)ow->rowbytes*ow->height;std::vector<unsigned char> before(bytes),classic(bytes),smart(bytes);std::memcpy(before.data(),ow->data,bytes);classic=before;smart=before;
 PF_EffectWorld cw=*ow,sw=*ow;cw.data=(PF_PixelPtr)classic.data();sw.data=(PF_PixelPtr)smart.data();const auto input_before=std::vector<unsigned char>((unsigned char*)iw->data,(unsigned char*)iw->data+(size_t)iw->rowbytes*iw->height);
 PF_Err ce=InstalledClassic(*iw,cw,*info);PF_Err se=InstalledSmart(*iw,sw,*info,depth);
 if(std::memcmp(input_before.data(),iw->data,input_before.size()))return PF_Err_INTERNAL_STRUCT_DAMAGED;
 if(ce||se){{if(ce==PF_Err_BAD_CALLBACK_PARAM&&se==PF_Err_BAD_CALLBACK_PARAM&&classic==before&&smart==before)return PF_Err_BAD_CALLBACK_PARAM;return ce?ce:se;}}
 if(classic!=smart)return PF_Err_INTERNAL_STRUCT_DAMAGED;std::memcpy(ow->data,classic.data(),bytes);return PF_Err_NONE;
}}
'''


def source_report_lines(path: Path, architecture: str) -> tuple[list[str], str]:
    report = json.loads(path.read_text())
    runs = report.get("runs")
    if not isinstance(runs, list):
        raise RuntimeError(f"source report lacks runs: {path}")
    for row in runs:
        if row.get("arch") == architecture:
            lines = row.get("lines")
            transcript = row.get("transcript_sha256")
            if not isinstance(lines, list) or not isinstance(transcript, str):
                raise RuntimeError("source transcript schema")
            return lines, transcript
    raise RuntimeError(f"missing source architecture {architecture}")


def run_family(architecture: str, probe_path: Path, source_report: Path) -> dict[str, Any]:
    expected_lines, expected_transcript = source_report_lines(source_report, architecture)
    with tempfile.TemporaryDirectory(prefix=f"radial-installed-type1-{architecture}-") as raw:
        temp = Path(raw)
        wrapper = temp / "installed_wrapper.h"
        wrapper.write_text(wrapper_text())
        probe = temp / "probe.cpp"
        probe.write_text(
            f'#define OLM_RADIAL_SOURCE_INCLUDE "{wrapper}"\n' +
            probe_path.read_text().replace("OLMRadialBlurTestRenderWorld", "InstalledPublicRenderWorld")
        )
        executable = temp / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [
            _UCRT_CXX, "-std=c++17", "-arch", architecture, "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-isysroot", sdk, "-Wno-pragma-pack",
            "-Wno-deprecated-declarations", "-I", str(ROOT / "Headers"),
            "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
            "-I", str(ROOT / "Resources"), "-I", str(ROOT / "core"),
            "-I", str(ROOT / "mac/OLMRadialBlur"), str(probe),
            str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
            "-framework", "Cocoa", "-o", str(executable),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(f"{architecture} build failed: {built.stdout}{built.stderr}")
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"{architecture} public replay rc={run.returncode}: {run.stdout}{run.stderr}")
    lines = run.stdout.splitlines()
    transcript = hashlib.sha256(run.stdout.encode()).hexdigest()
    if lines != expected_lines or transcript != expected_transcript:
        raise RuntimeError(f"installed public transcript differs from source closure: {architecture}")
    return {"architecture": architecture, "lines": lines, "transcript_sha256": transcript}


def expected_family_authorities() -> dict[str, dict[str, str]]:
    return authorities()["families"]


def generate() -> dict[str, Any]:
    live = authorities()
    if {key: live[key] for key in PINS} != PINS:
        raise RuntimeError(f"Radial installed authority drift: {live}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    families = []
    for name, probe_name, source_report_name, positives, rejects in FAMILIES:
        probe = ROOT / probe_name
        source_report = ROOT / source_report_name
        runs = [run_family(arch, probe, source_report) for arch in ("arm64", "x86_64")]
        families.append({
            "name": name,
            "positive_cells_per_slice": positives,
            "mutation_rejects_per_slice": rejects,
            "runs": runs,
        })
    return {
        "schema": "olmradialblur.current-installed-type1-complete-union/1",
        "status": STATUS,
        "claim_boundary": CLAIM,
        "authorities": live,
        "families": families,
        "families_sha256": canonical(families),
        "summary": {
            "families": 5,
            "positive_cells_per_slice": 106,
            "positive_cells_total": 212,
            "mutation_rejects_per_slice": 57,
            "mutation_rejects_total": 114,
            "classic_smart_padded_output_exact": True,
            "input_storage_immutable": True,
        },
        "after_effects_processes": [],
        "scope": {
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "arbitrary_source_tuple_geometry": False,
            "production_or_install_changed": False,
        },
    }


def validate(report: dict[str, Any], *, live: bool = True) -> bool:
    try:
        top = {"schema", "status", "claim_boundary", "authorities", "families", "families_sha256", "summary", "after_effects_processes", "scope"}
        if set(report) != top or report["schema"] != "olmradialblur.current-installed-type1-complete-union/1" or report["status"] != STATUS:
            return False
        if report["claim_boundary"] != CLAIM:
            return False
        if report["authorities"] != ({**PINS, "families": expected_family_authorities()}):
            return False
        families = report["families"]
        if not isinstance(families, list) or len(families) != 5 or report["families_sha256"] != canonical(families):
            return False
        for stored, spec in zip(families, FAMILIES):
            name, _, source_report_name, positives, rejects = spec
            if set(stored) != {"name", "positive_cells_per_slice", "mutation_rejects_per_slice", "runs"}:
                return False
            if (stored["name"], stored["positive_cells_per_slice"], stored["mutation_rejects_per_slice"]) != (name, positives, rejects):
                return False
            if [run.get("architecture") for run in stored["runs"]] != ["arm64", "x86_64"]:
                return False
            for run in stored["runs"]:
                if set(run) != {"architecture", "lines", "transcript_sha256"}:
                    return False
                expected_lines, expected_sha = source_report_lines(ROOT / source_report_name, run["architecture"])
                if run["lines"] != expected_lines or run["transcript_sha256"] != expected_sha:
                    return False
                if hashlib.sha256(("\n".join(run["lines"]) + "\n").encode()).hexdigest() != expected_sha:
                    return False
        if report["summary"] != {"families": 5, "positive_cells_per_slice": 106, "positive_cells_total": 212, "mutation_rejects_per_slice": 57, "mutation_rejects_total": 114, "classic_smart_padded_output_exact": True, "input_storage_immutable": True}:
            return False
        if report["after_effects_processes"] != [] or report["scope"] != {"installed_arm64": True, "installed_x86_64": True, "native_after_effects": False, "arbitrary_source_tuple_geometry": False, "production_or_install_changed": False}:
            return False
        if live and authorities() != report["authorities"]:
            return False
        return True
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def markdown(report: dict[str, Any]) -> str:
    return f"""# OLMRadialBlur current installed Type1 complete union

Status: `{report['status']}`

The current installed arm64 and Rosetta x86_64 slices replay all 106 retained
exact-source Type1 cells through both public Classic and Smart EffectMain
entries. The wrapper requires their entire padded outputs to agree. The five
families also execute 57 source-mutation fail-close controls per slice with
input storage unchanged and no output commit.

This is AE-free installed-Mach-O evidence. It does not generalize source,
tuple, geometry or native After Effects behavior.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    if args.write or args.fresh:
        current = generate()
        if not validate(current):
            raise RuntimeError("fresh installed Type1 closure invalid")
        if args.write:
            REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
            NOTE.write_text(markdown(current))
        print(STATUS)
        return 0
    saved = json.loads(REPORT.read_text())
    if not validate(saved) or NOTE.read_text() != markdown(saved):
        raise RuntimeError("persisted installed Type1 closure drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
