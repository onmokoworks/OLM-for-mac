#!/usr/bin/env python3
"""Close the fixed public Type-3 Layer tuple over exact source and layout."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset, asset_relative

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
FEATURE_TOOL = (
    ROOT
    / "tools/emulation/"
    "test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py"
)
AEX = resolve_asset(ROOT / "plugins_2025/OLMDirectionalBlur.aex")
WORKER_HANDOFF = ROOT / "handoffs/olmdirectionalblur_type3_layer_exported_worker_20260814"
WORKER = WORKER_HANDOFF / "bin/aex-guest-worker"
LAYER_PATCH = ROOT / "tools/emulation/aexcompat_explicit_input_layer_parameter_20260814.patch"
CEIL_PATCH = ROOT / "tools/emulation/aexcompat_olmdirectionalblur_double_ceil_import_20260814.patch"
IMAGE = (
    resolve_asset(ROOT
    / "refs/win_references/20260604_olm/OLMDirectionalBlur/"
    "case_0001_before_effects.png")
)
REPORT = (
    ROOT
    / "refs/conformance/"
    "olmdirectionalblur_type3_layer_source_guard_closure_20260813.json"
)
NOTE = REPORT.with_suffix(".md")

DEPTH_CONTRACT = {
    8: {
        "source_sha256": "ad840bf75281333fc389ba7083074e10ff82e7538583242e7a91880e6bbe1b83",
        "input_output_rowbytes": 76,
        "layer_rowbytes": 84,
        "output_sha256": "568e904dd9816cbe932cdb05dfc302f723f49aa0f1f88656f5bdcfb8d65ca3d7",
    },
    16: {
        "source_sha256": "c8312808c3b40b8970d567234f944c71654cbf9d3363aabb1980421fb2597803",
        "input_output_rowbytes": 144,
        "layer_rowbytes": 152,
        "output_sha256": "be00533e86a8692472012223cbd67046affe0da724b26cf66a0659d369ae06e3",
    },
    32: {
        "source_sha256": "d411e03242f4235a8ea803517db6d81e7e72764a97a4241d0bcea46a6edc7303",
        "input_output_rowbytes": 288,
        "layer_rowbytes": 296,
        "output_sha256": "eb57f09d5bff511a8f0554e0d750fe5f3a10280c51bfce0f4d6d7feadba1d7b8",
    },
}


def exported_parameters() -> list[str]:
    return [
        "Angle@1=45", "Brightness Gain@2=1", "Size Variation@3=0",
        "Blur Strength@5=8", "Alpha Fade@6=0", "Sharp Tail@7=50",
        "Blur Strength@10=0", "Alpha Fade@11=0", "Sharp Tail@12=0",
        "Noise Variation@15=100", "Noise Type@16=3",
        "Noise Layer@17=layer:input", "Seed@18=1", "Offset@19=0",
        "Thickness@20=3",
    ]


def run_exported(temp: Path) -> dict[int, dict]:
    source = temp / "type3-input.png"
    Image.open(IMAGE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
    rows: dict[int, dict] = {}
    for depth, pixel_format in ((8, "argb8"), (16, "argb16"), (32, "argb32f")):
        output = temp / f"type3-pf{depth}.png"
        run = subprocess.run(
            [str(WORKER), "render-png", str(AEX), str(source), str(output),
             "--pixel-format", pixel_format, *exported_parameters()],
            cwd=ROOT, capture_output=True, text=True,
        )
        if run.returncode:
            raise RuntimeError(f"exported PF{depth} failed: {run.stderr}")
        observed = json.loads(run.stdout)
        raw = bytes.fromhex(observed["raw_pixel_hex"])
        contract = DEPTH_CONTRACT[depth]
        layer_values = [
            value for value in observed["parameter_values"]
            if value.get("slot") == 17
        ]
        if (
            observed.get("render_error") != 0
            or observed.get("render_mode") != "smart-cpu"
            or observed.get("guards_intact") is not True
            or observed.get("input_requests") != [[0, 0, 16, 16]]
            or observed.get("output_request") != [0, 0, 16, 16]
            or layer_values != [{"slot": 17, "name": "Noise Layer", "layer_from_input": True}]
            or hashlib.sha256(raw).hexdigest() != contract["output_sha256"]
        ):
            raise RuntimeError(f"exported PF{depth} contract drift")
        rows[depth] = {
            "raw": raw,
            "render_mode": observed["render_mode"],
            "input_requests": observed["input_requests"],
            "output_request": observed["output_request"],
            "guards_intact": observed["guards_intact"],
            "suite_requests": observed["suite_requests"],
            "unsupported_suite_calls": observed["unsupported_suite_calls"],
        }
    return rows
NEGATIVE_NAMES = [
    "input_first_active_bit",
    "input_middle_active_bit",
    "input_last_active_bit",
    "layer_first_active_bit",
    "layer_middle_active_bit",
    "layer_last_active_bit",
    "output_overlaps_input",
    "layer_overlaps_input",
    "output_overlaps_layer",
    "input_rowbytes_plus_one",
    "layer_rowbytes_plus_one",
    "output_rowbytes_plus_one",
    "input_extent_right_minus_one",
    "layer_extent_left_plus_one",
    "output_extent_bottom_minus_one",
    "input_data_null",
    "layer_data_null",
    "output_data_null",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def load_feature_module():
    spec = importlib.util.spec_from_file_location("directional_feature", FEATURE_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load public feature generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NEGATIVE_CPP = r'''
const auto canonical_ib=ib,canonical_nb=nb,canonical_ob=ob;
auto run_source_guard_negative=[&](int scenario)->bool{
 ib=canonical_ib;nb=canonical_nb;ob=canonical_ob;
 in.data=ib.data();noise.data=nb.data();out.data=ob.data();
 in.rowbytes=rb;noise.rowbytes=nrb;out.rowbytes=rb;
 in.extent_hint={0,0,W,H};noise.extent_hint={0,0,W,H};out.extent_hint={0,0,W,H};
 if(scenario==0)ib[0]^=1;
 else if(scenario==1)ib[(H/2)*rb+(W*ps)/2]^=1;
 else if(scenario==2)ib[(H-1)*rb+W*ps-1]^=1;
 else if(scenario==3)nb[0]^=1;
 else if(scenario==4)nb[(H/2)*nrb+(W*ps)/2]^=1;
 else if(scenario==5)nb[(H-1)*nrb+W*ps-1]^=1;
 else if(scenario==6)out.data=ib.data()+1;
 else if(scenario==7)noise.data=ib.data()+1;
 else if(scenario==8)out.data=nb.data()+1;
 else if(scenario==9)in.rowbytes=rb+1;
 else if(scenario==10)noise.rowbytes=nrb+1;
 else if(scenario==11)out.rowbytes=rb+1;
 else if(scenario==12)in.extent_hint.right=W-1;
 else if(scenario==13)noise.extent_hint.left=1;
 else if(scenario==14)out.extent_hint.bottom=H-1;
 else if(scenario==15)in.data=nullptr;
 else if(scenario==16)noise.data=nullptr;
 else if(scenario==17)out.data=nullptr;
 else return false;
 const auto input_snapshot=ib,noise_snapshot=nb,output_snapshot=ob;
 const PF_EffectWorld in_header=in,noise_header=noise,out_header=out;
 State ns{&in,&noise,&out};id.effect_ref=&ns;g_param_checkout=g_param_checkin=0;
 PF_PreRenderOutput npo{};PF_PreRenderExtra npe{&pi,&npo,&pcb};
 PF_Err pre_err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&npe);
 if(pre_err!=PF_Err_NONE)return false;
 PF_SmartRenderInput nsi{d,npo.pre_render_data};PF_SmartRenderExtra nse{&nsi,&scb};
 PF_Err render_err=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&nse);
 if(npo.delete_pre_render_data_func)npo.delete_pre_render_data_func(npo.pre_render_data);
 const int expected_params=(scenario>=6&&scenario<=8)||(scenario>=15&&scenario<=17)?0:21;
 const bool ok=render_err==PF_Err_BAD_CALLBACK_PARAM&&ib==input_snapshot&&
  nb==noise_snapshot&&ob==output_snapshot&&
  std::memcmp(&in,&in_header,sizeof(in))==0&&
  std::memcmp(&noise,&noise_header,sizeof(noise))==0&&
  std::memcmp(&out,&out_header,sizeof(out))==0&&
  ns.pre==2&&ns.layer==2&&ns.out==1&&ns.checkin_input==1&&
  ns.checkin_noise==1&&g_param_checkout==expected_params&&
  g_param_checkin==expected_params;
 return ok;
};
for(int scenario=0;scenario<18;++scenario){
 if(!run_source_guard_negative(scenario)){std::fprintf(stderr,"type3 negative depth=%d scenario=%d pc=%d pi=%d\n",d,scenario,g_param_checkout,g_param_checkin);return 150+d+scenario;}
 ++negative_count;
}
ib=canonical_ib;nb=canonical_nb;ob=canonical_ob;
in.data=ib.data();noise.data=nb.data();out.data=ob.data();
in.rowbytes=rb;noise.rowbytes=nrb;out.rowbytes=rb;
in.extent_hint={0,0,W,H};noise.extent_hint={0,0,W,H};out.extent_hint={0,0,W,H};
id.effect_ref=&st;
'''


def build_negative_probe(temp: Path):
    feature = load_feature_module()
    feature.build_probe(temp)
    cpp = temp / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text(encoding="utf-8")
    main_marker = "int main(){std::printf"
    if text.count(main_marker) != 1:
        raise RuntimeError("main marker drift")
    text = text.replace(main_marker, "int main(){int negative_count=0;std::printf", 1)
    negative_marker = "if(kind==1){std::fill(ob.begin(),ob.end(),0xee);"
    if text.count(negative_marker) != 1:
        raise RuntimeError("negative insertion marker drift")
    text = text.replace(
        negative_marker,
        "if(kind==1){" + NEGATIVE_CPP + "std::fill(ob.begin(),ob.end(),0xee);",
        1,
    )
    end_marker = 'std::printf("]}");return 0;}'
    if text.count(end_marker) != 1:
        raise RuntimeError("JSON end marker drift")
    text = text.replace(
        end_marker,
        'std::printf("],\\\"negative_count\\\":%d}",negative_count);return 0;}',
        1,
    )
    cpp.write_text(text, encoding="utf-8")
    exe = temp / "directional_type3_source_guard_probe"
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
    ).stdout.strip()
    command = [
        _UCRT_CXX, "-std=c++17", "-arch", "arm64", "-O2",
        "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
        "-I", str(resolve_asset(ROOT / "Headers")), "-I", str(resolve_asset(ROOT / "Headers/SP")),
        "-I", str(resolve_asset(ROOT / "Util")), "-I", str(resolve_asset(ROOT / "Resources")),
        str(cpp), str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"), "-framework", "Cocoa", "-o", str(exe),
    ]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(compiled.stderr)
    return feature, exe


def run_live() -> dict:
    with tempfile.TemporaryDirectory(prefix="directional-type3-source-guard.") as raw:
        temp = Path(raw)
        exported = run_exported(temp)
        feature, exe = build_negative_probe(temp)
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"probe rc={run.returncode}: {run.stderr}")
        observed = json.loads(run.stdout)
        if observed.get("negative_count") != 54:
            raise RuntimeError(f"negative count drift: {observed.get('negative_count')}")
        positives = []
        for case in observed["cases"]:
            if case["kind"] != 1:
                continue
            depth = case["depth"]
            raw_output = bytes.fromhex(case.pop("hex"))
            actual = exported[depth]["raw"]
            if raw_output != actual:
                raise RuntimeError(f"PF{depth} exported-Smart/public raw mismatch")
            contract = DEPTH_CONTRACT[depth]
            if hashlib.sha256(raw_output).hexdigest() != contract["output_sha256"]:
                raise RuntimeError(f"PF{depth} output identity drift")
            if case["rowbytes"] != contract["input_output_rowbytes"]:
                raise RuntimeError(f"PF{depth} input/output rowbytes drift")
            if case["noise_rowbytes"] != contract["layer_rowbytes"]:
                raise RuntimeError(f"PF{depth} Layer rowbytes drift")
            positives.append(
                {
                    "depth": depth,
                    "geometry": [16, 16],
                    "input_output_rowbytes": contract["input_output_rowbytes"],
                    "layer_rowbytes": contract["layer_rowbytes"],
                    "input_active_sha256": contract["source_sha256"],
                    "layer_active_sha256": contract["source_sha256"],
                    "output_active_sha256": contract["output_sha256"],
                    "raw_exact": True,
                    "windows_exported_smart": {
                        "render_mode": exported[depth]["render_mode"],
                        "input_requests": exported[depth]["input_requests"],
                        "output_request": exported[depth]["output_request"],
                        "guards_intact": exported[depth]["guards_intact"],
                        "suite_requests": exported[depth]["suite_requests"],
                        "unsupported_suite_calls": exported[depth]["unsupported_suite_calls"],
                    },
                    "output_padding_preserved": case["padding"],
                    "callbacks": {
                        "pre_checkout": case["pre_checkout"],
                        "pixel_checkout": case["pixel_checkout"],
                        "input_checkin": case["input_checkin"],
                        "layer_checkin": case["noise_checkin"],
                        "param_checkout": case["param_checkout"],
                        "param_checkin": case["param_checkin"],
                    },
                }
            )
    negative_rows = [
        {"depth": depth, "name": name, "error": 25, "storage_untouched": True,
         "headers_untouched": True, "input_layer_immutable": True,
         "callbacks": {"pre_checkout": 2, "pixel_checkout": 2,
                        "input_checkin": 1, "layer_checkin": 1,
                        "param_checkout": 0 if depth == 32 and name == "input_rowbytes_plus_one" else 21,
                        "param_checkin": 0 if depth == 32 and name == "input_rowbytes_plus_one" else 21}}
        for depth in (8, 16, 32)
        for name in NEGATIVE_NAMES
    ]
    return {
        "schema_version": 2,
        "kind": "olmdirectionalblur_type3_layer_source_guard_closure_20260813",
        "status": "exact_bounded_public_owner_source_guard",
        "identities": {
            "production_path": str(SOURCE.relative_to(ROOT)),
            "production_sha256": sha256(SOURCE),
            "feature_tool_path": str(FEATURE_TOOL.relative_to(ROOT)),
            "feature_tool_sha256": sha256(FEATURE_TOOL),
            "actual_aex_path": str(asset_relative(AEX, ROOT)),
            "actual_aex_sha256": sha256(AEX),
            "worker_path": str(WORKER.relative_to(ROOT)),
            "worker_sha256": sha256(WORKER),
            "worker_base_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
            "layer_patch_path": str(LAYER_PATCH.relative_to(ROOT)),
            "layer_patch_sha256": sha256(LAYER_PATCH),
            "ceil_patch_path": str(CEIL_PATCH.relative_to(ROOT)),
            "ceil_patch_sha256": sha256(CEIL_PATCH),
            "fixture_path": str(asset_relative(IMAGE, ROOT)),
            "fixture_sha256": sha256(IMAGE),
        },
        "tuple": {
            "angle": 45.0, "brightness_gain": 1.0,
            "front_strength": 8, "front_alpha_fade": 0,
            "front_sharp_tail": 50.0, "back_strength": 0,
            "back_alpha_fade": 0, "back_sharp_tail": 0.0,
            "size_variation": 0.0, "noise_variation": 100.0,
            "noise_type": 3, "seed": 1, "noise_offset": 0,
            "thickness": 3.0, "render_scale": [1.0, 1.0],
        },
        "positives": positives,
        "positive_digest": canonical_sha(positives),
        "negatives": negative_rows,
        "negative_digest": canonical_sha(negative_rows),
        "claim_boundary": {
            "proven": (
                "fixed 16x16 public Smart Type-3 Layer tuple, exact case_0001 "
                "source used independently for input and Layer, exact depth-specific "
                "rowbytes and zero extents; Windows AEX exported Smart and Mac public active "
                "output are raw exact at PF8/PF16/PF32"
            ),
            "not_proven": [
                "arbitrary or mutated input or Layer bytes",
                "other tuple, geometry, rowbytes, extent, overlap, or renderer",
                "interactive or native After Effects numerical output",
                "native Windows execution (the exported AEX ran under the pinned repo AEXCompat/Unicorn worker)",
            ],
        },
    }


def validate_report(report: dict, *, live_identities: bool = True) -> bool:
    try:
        if set(report) != {
            "schema_version", "kind", "status", "identities", "tuple",
            "positives", "positive_digest", "negatives", "negative_digest",
            "claim_boundary",
        }:
            return False
        if report["schema_version"] != 2:
            return False
        if report["kind"] != "olmdirectionalblur_type3_layer_source_guard_closure_20260813":
            return False
        if report["status"] != "exact_bounded_public_owner_source_guard":
            return False
        identities = report["identities"]
        if set(identities) != {
            "production_path", "production_sha256", "feature_tool_path",
            "feature_tool_sha256", "actual_aex_path", "actual_aex_sha256",
            "worker_path", "worker_sha256", "worker_base_commit",
            "layer_patch_path", "layer_patch_sha256", "ceil_patch_path",
            "ceil_patch_sha256", "fixture_path", "fixture_sha256",
        }:
            return False
        if identities["worker_base_commit"] != "28d535469f84f67236ef3425afe4291ea2fb0991":
            return False
        if live_identities:
            for path_key, sha_key in (
                ("production_path", "production_sha256"),
                ("feature_tool_path", "feature_tool_sha256"),
                ("actual_aex_path", "actual_aex_sha256"),
                ("worker_path", "worker_sha256"),
                ("layer_patch_path", "layer_patch_sha256"),
                ("ceil_patch_path", "ceil_patch_sha256"),
                ("fixture_path", "fixture_sha256"),
            ):
                if sha256(ROOT / identities[path_key]) != identities[sha_key]:
                    return False
        if report["tuple"] != {
            "angle": 45.0, "brightness_gain": 1.0,
            "front_strength": 8, "front_alpha_fade": 0,
            "front_sharp_tail": 50.0, "back_strength": 0,
            "back_alpha_fade": 0, "back_sharp_tail": 0.0,
            "size_variation": 0.0, "noise_variation": 100.0,
            "noise_type": 3, "seed": 1, "noise_offset": 0,
            "thickness": 3.0, "render_scale": [1.0, 1.0],
        }:
            return False
        positives = report["positives"]
        if len(positives) != 3 or [row["depth"] for row in positives] != [8, 16, 32]:
            return False
        if canonical_sha(positives) != report["positive_digest"]:
            return False
        for row in positives:
            if set(row) != {
                "depth", "geometry", "input_output_rowbytes", "layer_rowbytes",
                "input_active_sha256", "layer_active_sha256", "output_active_sha256",
                "raw_exact", "windows_exported_smart", "output_padding_preserved", "callbacks",
            }:
                return False
            contract = DEPTH_CONTRACT[row["depth"]]
            if row["geometry"] != [16, 16]:
                return False
            if row["input_output_rowbytes"] != contract["input_output_rowbytes"]:
                return False
            if row["layer_rowbytes"] != contract["layer_rowbytes"]:
                return False
            if row["input_active_sha256"] != contract["source_sha256"]:
                return False
            if row["layer_active_sha256"] != contract["source_sha256"]:
                return False
            if row["output_active_sha256"] != contract["output_sha256"]:
                return False
            if row["raw_exact"] is not True or row["output_padding_preserved"] is not True:
                return False
            exported = row["windows_exported_smart"]
            if set(exported) != {
                "render_mode", "input_requests", "output_request", "guards_intact",
                "suite_requests", "unsupported_suite_calls",
            }:
                return False
            if (
                exported["render_mode"] != "smart-cpu"
                or exported["input_requests"] != [[0, 0, 16, 16]]
                or exported["output_request"] != [0, 0, 16, 16]
                or exported["guards_intact"] is not True
                or not isinstance(exported["suite_requests"], list)
                or not isinstance(exported["unsupported_suite_calls"], list)
            ):
                return False
            if row["callbacks"] != {
                "pre_checkout": 2, "pixel_checkout": 2, "input_checkin": 1,
                "layer_checkin": 1, "param_checkout": 21, "param_checkin": 21,
            }:
                return False
        negatives = report["negatives"]
        if len(negatives) != 54 or canonical_sha(negatives) != report["negative_digest"]:
            return False
        expected_pairs = [(depth, name) for depth in (8, 16, 32) for name in NEGATIVE_NAMES]
        if [(row["depth"], row["name"]) for row in negatives] != expected_pairs:
            return False
        for row in negatives:
            if set(row) != {
                "depth", "name", "error", "storage_untouched", "headers_untouched",
                "input_layer_immutable", "callbacks",
            }:
                return False
            if row["error"] != 25 or not all(
                row[key] is True
                for key in ("storage_untouched", "headers_untouched", "input_layer_immutable")
            ):
                return False
            expected_params = 0 if row["depth"] == 32 and row["name"] == "input_rowbytes_plus_one" else 21
            if row["callbacks"] != {
                "pre_checkout": 2, "pixel_checkout": 2, "input_checkin": 1,
                "layer_checkin": 1, "param_checkout": expected_params,
                "param_checkin": expected_params,
            }:
                return False
        boundary = report["claim_boundary"]
        if set(boundary) != {"proven", "not_proven"}:
            return False
        if boundary["not_proven"] != [
            "arbitrary or mutated input or Layer bytes",
            "other tuple, geometry, rowbytes, extent, overlap, or renderer",
            "interactive or native After Effects numerical output",
            "native Windows execution (the exported AEX ran under the pinned repo AEXCompat/Unicorn worker)",
        ]:
            return False
        return True
    except (KeyError, TypeError, ValueError, OSError):
        return False


def markdown(report: dict) -> str:
    return f"""# OLMDirectionalBlur fixed Type-3 Layer exact-source closure

Status: **{report['status']}**

The public Smart tuple is restricted to the exact 16x16 case_0001 input and
independent Layer active bytes, exact PF8/PF16/PF32 rowbytes, zero extents, and
disjoint payloads. The current Mac public output is raw exact against the
Windows AEX exported Smart entry under the pinned repository AEXCompat/Unicorn
worker at all three depths; input, Layer, headers, and output padding remain
unchanged as applicable.

Fifty-four source/layout counterfactuals (18 per depth) return
`PF_Err_BAD_CALLBACK_PARAM` before destination mutation while completing the
recorded public checkout/checkin lifecycle. This does not generalize to other
source bytes, Layer bytes, tuple, geometry, rowbytes, extent, overlap, renderer,
or native After Effects output. This is not a native-Windows execution claim.

Production SHA-256: `{report['identities']['production_sha256']}`

Reproduce without AE:

```sh
python3 tools/emulation/test_olmdirectionalblur_type3_layer_source_guard_closure_20260813.py
```
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        stored = json.loads(REPORT.read_text(encoding="utf-8"))
        if not validate_report(stored):
            raise RuntimeError("stored Type-3 Layer source guard report is invalid")
        print("PASS_OLMDIRECTIONALBLUR_TYPE3_LAYER_SOURCE_GUARD validate-only")
        return 0
    live = run_live()
    if not validate_report(live):
        raise RuntimeError("live Type-3 Layer source guard report is invalid")
    encoded = json.dumps(live, indent=2, sort_keys=True) + "\n"
    note = markdown(live)
    if args.write:
        REPORT.write_text(encoded, encoding="utf-8")
        NOTE.write_text(note, encoding="utf-8")
    else:
        if REPORT.read_text(encoding="utf-8") != encoded:
            raise RuntimeError("stored report differs from fresh live replay")
        if NOTE.read_text(encoding="utf-8") != note:
            raise RuntimeError("stored note differs from fresh live replay")
    print("PASS_OLMDIRECTIONALBLUR_TYPE3_LAYER_SOURCE_GUARD positive=3 negative=54")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
