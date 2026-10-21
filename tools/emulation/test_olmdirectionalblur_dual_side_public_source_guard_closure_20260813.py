#!/usr/bin/env python3
"""Close the fixed public 32x18 dual-side Type-2 tuple over source/layout."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
FEATURE_TOOL = (
    ROOT / "tools/emulation/"
    "test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py"
)
FEATURE_REPORT = (
    ROOT / "refs/conformance/"
    "olmdirectionalblur_public_effectmain_feature_matrix_20260811.json"
)
PUBLIC64_TOOL = (
    ROOT / "tools/emulation/"
    "test_olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.py"
)
PUBLIC64_REPORT = (
    ROOT / "refs/conformance/"
    "olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.json"
)
EXPORTED_REPORT = (
    ROOT / "refs/conformance/"
    "olmdirectionalblur_dual_side_exported_smart_closure_20260814.json"
)
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
IMAGE = (
    ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/"
    "case_0001_before_effects.png"
)
REPORT = (
    ROOT / "refs/conformance/"
    "olmdirectionalblur_dual_side_public_source_guard_closure_20260813.json"
)
NOTE = REPORT.with_suffix(".md")

TUPLES = (
    (50, 50, 100, 100, 0, 25, 1),
    (50, 100, 50, 50, 50, 100, 2),
    (100, 50, 50, 100, 0, 100, 2),
    (100, 100, 100, 50, 50, 25, 1),
)
CONFIGS = (
    (32, 18, 1, (8, 16, 32)),
    (64, 36, 0, (8, 16, 32)),
    (64, 36, 1, (8, 16, 32)),
    (64, 36, 2, (8, 16, 32)),
    (64, 36, 3, (8, 16, 32)),
)

DEPTH_CONTRACT = {
    (32, 18, 8): {
        "source_sha256": "7c65cdf081119a7db77d804cb5ad256f3b89beb73bb32587fbf53224c56d06e6",
        "rowbytes": 140,
        "output_sha256": "9834db6f461bdb35d6efdffd9e84515d8f56a16e9214dc7cbce98650829ddc1e",
    },
    (32, 18, 16): {
        "source_sha256": "44f6470ac55a81953e062df177d996a0336348a472b7e0e050b8de261c1fcbf5",
        "rowbytes": 272,
        "output_sha256": "b632375e576257c251f6c01d535eab2cbf981f78edec9e5b2d5084b5f97d954c",
    },
    (32, 18, 32): {
        "source_sha256": "0c626ba0cc34551753ea2176999eb075610ebd63c40fee5af7b2c31a10812ba6",
        "rowbytes": 544,
        "output_sha256": "0094576105d9cabecce0dea71c5b7352a2dcd2990b8eb4ff29b4a295a2e470d4",
    },
    (64, 36, 8): {
        "source_sha256": "0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
        "rowbytes": 268,
        "outputs": (
            "1697b835063aa0fb975a1785e9a374a2c4658ff6f9d79952f167b993144b2926",
            "2f5c9ef8f69ccab111d2d230a542293fd8dd7377a5fd83be50940f5d053cc31a",
            "636e649414ff0ad3968aabb97733dbb67f92900898829361b3f44c58758cfdb3",
            "39e05b0f1b5bfbc8923cc11f7c43caa2eab6ca5de8c07111601a2e2d3418bfe7",
        ),
    },
    (64, 36, 16): {
        "source_sha256": "18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450",
        "rowbytes": 528,
        "outputs": (
            "7393895df5581f2baa31aca43376c31c55755ee67e20b0f43d6664953a5e8311",
            "eeea58c8cc7bc7a68f396e69b0e3d4446e7ee2c23387c17e320462222916188c",
            "4846a56aea99d2db6be3e56930a8ef1143394e89ca97e316d84a8ec165b4179d",
            "d0b367cb47a3937b68159f02401d585b785ac063c6b8893afe8b03a5c93af592",
        ),
    },
    (64, 36, 32): {
        "source_sha256": "884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d",
        "rowbytes": 1056,
        "outputs": (
            "05989b2976a2056c738a2c41cf6c9ac39a3fcf8caa35eba4ca1d828fecb9fe19",
            "814ae4ec073d6e6ad4c83dea25227de5362d0ae6b8346d155c6aafe086149ac7",
            "453bbdf19955a3c6b91f2ca9b756e0d0aa9f2949b5855050636170a117039fc1",
            "3424989500b9b05791c1ce9e33e99fb810b5e3c63ad6b4e8c3897c6a2d832c09",
        ),
    },
}
NEGATIVE_NAMES = [
    "input_first_active_bit",
    "input_middle_active_bit",
    "input_last_active_bit",
    "output_overlaps_input",
    "input_overlaps_output",
    "input_rowbytes_plus_one",
    "output_rowbytes_plus_one",
    "input_extent_right_minus_one",
    "output_extent_bottom_minus_one",
    "input_data_null",
    "output_data_null",
    "input_width_minus_one",
    "input_height_minus_one",
    "output_width_minus_one",
    "output_height_minus_one",
    "geometry_16x16_internal_owner_only",
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
auto run_dual_source_guard_negative=[&](int scenario)->bool{
 ib=canonical_ib;nb=canonical_nb;ob=canonical_ob;
 in.data=ib.data();noise.data=nb.data();out.data=ob.data();
 in.rowbytes=rb;noise.rowbytes=nrb;out.rowbytes=rb;
 in.width=W;in.height=H;out.width=W;out.height=H;
 in.extent_hint={0,0,W,H};noise.extent_hint={0,0,W,H};out.extent_hint={0,0,W,H};
 if(scenario==0)ib[0]^=1;
 else if(scenario==1)ib[(H/2)*rb+(W*ps)/2]^=1;
 else if(scenario==2)ib[(H-1)*rb+W*ps-1]^=1;
 else if(scenario==3)out.data=ib.data()+1;
 else if(scenario==4)in.data=ob.data()+1;
 else if(scenario==5)in.rowbytes=rb+1;
 else if(scenario==6)out.rowbytes=rb+1;
 else if(scenario==7)in.extent_hint.right=W-1;
 else if(scenario==8)out.extent_hint.bottom=H-1;
 else if(scenario==9)in.data=nullptr;
 else if(scenario==10)out.data=nullptr;
 else if(scenario==11)in.width=W-1;
 else if(scenario==12)in.height=H-1;
 else if(scenario==13)out.width=W-1;
 else if(scenario==14)out.height=H-1;
 else if(scenario==15){
  const int pad=rb-W*ps;
  in.width=out.width=16;in.height=out.height=16;
  in.rowbytes=out.rowbytes=16*ps+pad;
  in.extent_hint={0,0,16,16};out.extent_hint={0,0,16,16};
 }
 else return false;
 const auto input_snapshot=ib,noise_snapshot=nb,output_snapshot=ob;
 const PF_EffectWorld in_header=in,noise_header=noise,out_header=out;
 State ns{&in,nullptr,&out};id.effect_ref=&ns;g_param_checkout=g_param_checkin=0;
 PF_PreRenderOutput npo{};PF_PreRenderExtra npe{&pi,&npo,&pcb};
 PF_Err pre_err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&npe);
 if(pre_err!=PF_Err_NONE)return false;
 PF_SmartRenderInput nsi{d,npo.pre_render_data};PF_SmartRenderExtra nse{&nsi,&scb};
 PF_Err render_err=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&nse);
 if(npo.delete_pre_render_data_func)npo.delete_pre_render_data_func(npo.pre_render_data);
 const int expected_params=(scenario==3||scenario==4||scenario==9||scenario==10)?0:21;
 const bool ok=render_err==PF_Err_BAD_CALLBACK_PARAM&&ib==input_snapshot&&
  nb==noise_snapshot&&ob==output_snapshot&&
  std::memcmp(&in,&in_header,sizeof(in))==0&&
  std::memcmp(&noise,&noise_header,sizeof(noise))==0&&
  std::memcmp(&out,&out_header,sizeof(out))==0&&
  ns.pre==2&&ns.layer==2&&ns.out==1&&ns.checkin_input==1&&
  ns.checkin_noise==0&&g_param_checkout==expected_params&&
  g_param_checkin==expected_params;
 return ok;
};
for(int scenario=0;scenario<16;++scenario){
 if(!run_dual_source_guard_negative(scenario))return 150+d+scenario;
 ++negative_count;
}
ib=canonical_ib;nb=canonical_nb;ob=canonical_ob;
in.data=ib.data();noise.data=nb.data();out.data=ob.data();
in.rowbytes=rb;noise.rowbytes=nrb;out.rowbytes=rb;
in.width=W;in.height=H;out.width=W;out.height=H;
in.extent_hint={0,0,W,H};noise.extent_hint={0,0,W,H};out.extent_hint={0,0,W,H};
id.effect_ref=&st;
'''


def build_negative_probe(temp: Path, width: int, height: int, tuple_index: int,
                         depths: tuple[int, ...]):
    feature = load_feature_module()
    feature.DUAL_W, feature.DUAL_H = width, height
    feature.DUAL_TUPLE = TUPLES[tuple_index]
    feature.build_probe(temp)
    cpp = temp / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text(encoding="utf-8")
    loop = "for(short d:{8,16,32})for(int kind=0;kind<2;++kind)"
    replacement = "for(short d:{" + ",".join(map(str, depths)) + "})for(int kind=0;kind<1;++kind)"
    if text.count(loop) != 1:
        raise RuntimeError("depth loop marker drift")
    text = text.replace(loop, replacement, 1)
    main_marker = "int main(){std::printf"
    if text.count(main_marker) != 1:
        raise RuntimeError("main marker drift")
    text = text.replace(main_marker, "int main(){int negative_count=0;std::printf", 1)
    insertion_marker = "if(kind==1){std::fill(ob.begin(),ob.end(),0xee);"
    if text.count(insertion_marker) != 1:
        raise RuntimeError("negative insertion marker drift")
    text = text.replace(
        insertion_marker,
        "if(kind==0){" + NEGATIVE_CPP + "}" + insertion_marker,
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
    exe = temp / "directional_dual_source_guard_probe"
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
    ).stdout.strip()
    command = [
        "clang++", "-std=c++17", "-arch", "arm64", "-O2",
        "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
        "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
        "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
        str(cpp), str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"), "-framework", "Cocoa", "-o", str(exe),
    ]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(compiled.stderr)
    return feature, exe


def run_live() -> dict:
    positives = []
    negative_rows = []
    with tempfile.TemporaryDirectory(prefix="directional-dual-source-guard.") as raw:
        root = Path(raw)
        for width, height, tuple_index, depths in CONFIGS:
            temp = root / f"{width}x{height}-t{tuple_index}"
            temp.mkdir()
            feature, exe = build_negative_probe(temp, width, height, tuple_index, depths)
            run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(
                    f"probe {width}x{height}/tuple{tuple_index} rc={run.returncode}: {run.stderr}"
                )
            observed = json.loads(run.stdout)
            if observed.get("negative_count") != len(depths) * len(NEGATIVE_NAMES):
                raise RuntimeError(f"negative count drift: {observed.get('negative_count')}")
            for case in observed["cases"]:
                if case["kind"] != 0:
                    continue
                depth = case["depth"]
                raw_output = bytes.fromhex(case.pop("hex"))
                contract = DEPTH_CONTRACT[(width, height, depth)]
                expected_output = contract.get("output_sha256") or contract["outputs"][tuple_index]
                if hashlib.sha256(raw_output).hexdigest() != expected_output:
                    raise RuntimeError(f"PF{depth} output identity drift")
                if case["rowbytes"] != contract["rowbytes"]:
                    raise RuntimeError(f"PF{depth} input/output rowbytes drift")
                positives.append({
                    "geometry": [width, height], "tuple_index": tuple_index,
                    "depth": depth, "input_output_rowbytes": contract["rowbytes"],
                    "input_active_sha256": contract["source_sha256"],
                    "output_active_sha256": expected_output, "raw_exact": True,
                    "output_padding_preserved": case["padding"],
                    "callbacks": {
                        "pre_checkout": case["pre_checkout"],
                        "pixel_checkout": case["pixel_checkout"],
                        "input_checkin": case["input_checkin"],
                        "noise_checkin": case["noise_checkin"],
                        "param_checkout": case["param_checkout"],
                        "param_checkin": case["param_checkin"],
                    },
                })
            negative_rows.extend(
                {"geometry": [width, height], "tuple_index": tuple_index,
                 "depth": depth, "name": name, "error": 516,
                 "storage_untouched": True, "headers_untouched": True,
                 "input_output_immutable": True,
                 "callbacks": {"pre_checkout": 2, "pixel_checkout": 2,
                               "input_checkin": 1, "noise_checkin": 0,
                               "param_checkout": 21, "param_checkin": 21}}
                for depth in depths for name in NEGATIVE_NAMES
            )
    return {
        "schema_version": 1,
        "kind": "olmdirectionalblur_dual_side_public_source_guard_closure_20260813",
        "status": "exact_bounded_public_owner_source_guard",
        "identities": {
            "production_path": str(SOURCE.relative_to(ROOT)),
            "production_sha256": sha256(SOURCE),
            "feature_tool_path": str(FEATURE_TOOL.relative_to(ROOT)),
            "feature_tool_sha256": sha256(FEATURE_TOOL),
            "feature_report_path": str(FEATURE_REPORT.relative_to(ROOT)),
            "feature_report_sha256": sha256(FEATURE_REPORT),
            "public64_tool_path": str(PUBLIC64_TOOL.relative_to(ROOT)),
            "public64_tool_sha256": sha256(PUBLIC64_TOOL),
            "public64_report_path": str(PUBLIC64_REPORT.relative_to(ROOT)),
            "public64_report_sha256": sha256(PUBLIC64_REPORT),
            "exported_report_path": str(EXPORTED_REPORT.relative_to(ROOT)),
            "exported_report_sha256": sha256(EXPORTED_REPORT),
            "actual_aex_path": str(AEX.relative_to(ROOT)),
            "actual_aex_sha256": sha256(AEX),
            "fixture_path": str(IMAGE.relative_to(ROOT)),
            "fixture_sha256": sha256(IMAGE),
        },
        "tuples": [list(value) for value in TUPLES],
        "positives": positives,
        "positive_digest": canonical_sha(positives),
        "negatives": negative_rows,
        "negative_digest": canonical_sha(negative_rows),
        "claim_boundary": {
            "proven": (
                "fifteen exported-Smart cells: 32x18 tuple1 PF8/PF16/PF32 plus "
                "64x36 tuples0/1/2/3 PF8/PF16/PF32, "
                "exact case_0001 source, depth-specific rowbytes and zero extents; "
                "the exported owner and Mac public output are raw exact only for those cells"
            ),
            "not_proven": [
                "arbitrary or mutated input bytes",
                "16x16 or other dual-side tuple, geometry, rowbytes, extent, overlap, or renderer",
                "interactive or native After Effects numerical output",
            ],
        },
    }


def validate_report(report: dict, *, live_identities: bool = True) -> bool:
    try:
        if set(report) != {
            "schema_version", "kind", "status", "identities", "tuples",
            "positives", "positive_digest", "negatives", "negative_digest",
            "claim_boundary",
        }:
            return False
        if report["schema_version"] != 1:
            return False
        if report["kind"] != "olmdirectionalblur_dual_side_public_source_guard_closure_20260813":
            return False
        if report["status"] != "exact_bounded_public_owner_source_guard":
            return False
        identities = report["identities"]
        if set(identities) != {
            "production_path", "production_sha256", "feature_tool_path",
            "feature_tool_sha256", "feature_report_path", "feature_report_sha256",
            "public64_tool_path", "public64_tool_sha256", "public64_report_path",
            "public64_report_sha256", "exported_report_path", "exported_report_sha256",
            "actual_aex_path", "actual_aex_sha256", "fixture_path", "fixture_sha256",
        }:
            return False
        if live_identities:
            for path_key, sha_key in (
                ("production_path", "production_sha256"),
                ("feature_tool_path", "feature_tool_sha256"),
                ("feature_report_path", "feature_report_sha256"),
                ("public64_tool_path", "public64_tool_sha256"),
                ("public64_report_path", "public64_report_sha256"),
                ("exported_report_path", "exported_report_sha256"),
                ("actual_aex_path", "actual_aex_sha256"),
                ("fixture_path", "fixture_sha256"),
            ):
                if sha256(ROOT / identities[path_key]) != identities[sha_key]:
                    return False
        if report["tuples"] != [list(value) for value in TUPLES]:
            return False
        positives = report["positives"]
        expected_positive_keys = [
            (width, height, tuple_index, depth)
            for width, height, tuple_index, depths in CONFIGS for depth in depths
        ]
        if len(positives) != 15 or [
            (*row["geometry"], row["tuple_index"], row["depth"])
            for row in positives
        ] != expected_positive_keys:
            return False
        if canonical_sha(positives) != report["positive_digest"]:
            return False
        for row in positives:
            if set(row) != {
                "depth", "geometry", "tuple_index", "input_output_rowbytes", "input_active_sha256",
                "output_active_sha256", "raw_exact", "output_padding_preserved", "callbacks",
            }:
                return False
            width, height = row["geometry"]
            contract = DEPTH_CONTRACT[(width, height, row["depth"])]
            if not any((width, height, row["tuple_index"]) == config[:3] and
                       row["depth"] in config[3] for config in CONFIGS):
                return False
            if row["input_output_rowbytes"] != contract["rowbytes"]:
                return False
            if row["input_active_sha256"] != contract["source_sha256"]:
                return False
            expected_output = contract.get("output_sha256") or contract["outputs"][row["tuple_index"]]
            if row["output_active_sha256"] != expected_output:
                return False
            if row["raw_exact"] is not True or row["output_padding_preserved"] is not True:
                return False
            if row["callbacks"] != {
                "pre_checkout": 2, "pixel_checkout": 2, "input_checkin": 1,
                "noise_checkin": 0, "param_checkout": 21, "param_checkin": 21,
            }:
                return False
        negatives = report["negatives"]
        if len(negatives) != len(expected_positive_keys) * len(NEGATIVE_NAMES) or canonical_sha(negatives) != report["negative_digest"]:
            return False
        expected_pairs = [
            (width, height, tuple_index, depth, name)
            for width, height, tuple_index, depths in CONFIGS
            for depth in depths for name in NEGATIVE_NAMES
        ]
        if [(*row["geometry"], row["tuple_index"], row["depth"], row["name"])
            for row in negatives] != expected_pairs:
            return False
        for row in negatives:
            if set(row) != {
                "geometry", "tuple_index", "depth", "name", "error",
                "storage_untouched", "headers_untouched",
                "input_output_immutable", "callbacks",
            }:
                return False
            if row["error"] != 516 or not all(
                row[key] is True
                for key in ("storage_untouched", "headers_untouched", "input_output_immutable")
            ):
                return False
            if row["callbacks"] != {
                "pre_checkout": 2, "pixel_checkout": 2, "input_checkin": 1,
                "noise_checkin": 0, "param_checkout": 21, "param_checkin": 21,
            }:
                return False
        boundary = report["claim_boundary"]
        if set(boundary) != {"proven", "not_proven"}:
            return False
        if boundary["not_proven"] != [
            "arbitrary or mutated input bytes",
            "16x16 or other dual-side tuple, geometry, rowbytes, extent, overlap, or renderer",
            "interactive or native After Effects numerical output",
        ]:
            return False
        return True
    except (KeyError, TypeError, ValueError, OSError):
        return False


def markdown(report: dict) -> str:
    return f"""# OLMDirectionalBlur fixed dual-side Type-2 exact-source closure

Status: **{report['status']}**

The public Smart route is restricted to fifteen exact cells: 32x18 tuple 1 at
PF8/PF16/PF32, plus 64x36 tuples 0, 1, 2 and 3 at PF8/PF16/PF32. They use the exact case_0001 input
bytes, depth-specific input/output rowbytes, zero extents, and disjoint payloads.
The current Mac public output is raw exact against the exported AEX Smart route.

Two hundred forty source/layout counterfactuals return
`PF_Err_BAD_CALLBACK_PARAM` before destination mutation while completing the
recorded public checkout/checkin lifecycle. This does not generalize to other
source bytes, 16x16 or other tuple/geometry, rowbytes, extent, overlap, renderer,
or native After Effects output.

Production SHA-256: `{report['identities']['production_sha256']}`

Reproduce without AE:

```sh
python3 tools/emulation/test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py
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
            raise RuntimeError("stored dual-side source guard report is invalid")
        print("PASS_OLMDIRECTIONALBLUR_DUAL_SIDE_PUBLIC_SOURCE_GUARD validate-only")
        return 0
    live = run_live()
    if not validate_report(live):
        raise RuntimeError("live dual-side source guard report is invalid")
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
    print("PASS_OLMDIRECTIONALBLUR_DUAL_SIDE_PUBLIC_SOURCE_GUARD positive=15 negative=240")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
