#!/usr/bin/env python3
"""Fail-closed OLMSmoother v1 32bpc host-conversion boundary audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from compare_float_exr import compare, read_planes_with_layout


ROOT = Path(__file__).resolve().parents[1]
WIN = Path("refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMSmoother")
MANIFEST = WIN / "reference_manifest.json"
REQUEST = Path("refs/reference_requests/olm_final_random10_olm_smoother_20260629.json")
DISASM = Path("decomp/OLMSmoother.aex.c.txt")
MAC = Path("mac/OLMSmoother/Mac/OLMSmoother_port.cpp")
PIPL = Path("mac/OLMSmoother/OLMSmootherPiPL.r")

EXPECTED_SOURCE_HASHES = {
    str(MANIFEST): "ddb424993daa0fc2bd46657850b7d1ca7a03ac155ac9db6bd7e552a4d1946f73",
    str(REQUEST): "7dc4c2ac2e111713a746d5c5142137a2f968bfe3952d7620099ccb77b1540d33",
    str(DISASM): "107bc8ab393c2f26aeac4d1492a0bbf268e9ef5ddbdb3d6d9a84bc825451a652",
    str(MAC): "417056110abb4e2515851c697b0d1ae7e565dc0f27bbb2acd129761c19739b67",
    str(PIPL): "cf6c47d755fd89b8bd46ab5d102c353d9093e213e119edb6ea2ae9a6cdb571ea",
}

EXPECTED_EXR_HASHES = {
    "01.exr": "a03b81a1978e9dd9c70e23cf134e175aa25b327c02d056865fdd3295a7dd9098",
    "01_before_effects.exr": "4968b0b4cfdbea4bf71adf7e5715185adc0c3928c28a2ec88703cd2f62033dc8",
    "02.exr": "e9a0f1a81f89c9d073ce088de9de703b02ccb910eb5de2996fa0e21d31def0a4",
    "02_before_effects.exr": "55e10dd063e5d3dc954cec639fb8c649b1b1a2a91f43787253f33b4d9907f1d7",
    "03.exr": "4837467aef3e105e57bad4c54b6671bdf725537510c2658a60c66c1512c099ee",
    "03_before_effects.exr": "ccfac6bde0289ec42f28bed841d01409e84f70092762f2f1fba73d3a8191183a",
    "04.exr": "b4435145aa6cddea469d3527a4a26e69c496810bce070bf9a80546b2e40a963e",
    "04_before_effects.exr": "a044800240485f1ff5efb7ccd008f2c36260c806a267e7639cd4d482ea91761e",
    "05.exr": "b5aa46368891a38f8f1d13157fb6ac76bb418e2b195c299ef4d6c7de2cfb5289",
    "05_before_effects.exr": "89b4dabf8e9bb456f3622653dc56f05cc74b53001b3c485bf4401a8cd5acd466",
    "06.exr": "fafc461fc1486c9834d6821800976659dd27e37d82cd938dc269a8bff2489edf",
    "06_before_effects.exr": "e75fee99fb2cb136570c38cf3c05ba0342003969e834b76722b244846aba2e0d",
    "07.exr": "7ccd0ff5dad019ff9fc01d00fd8b40556d5984b36f93274c9f72899c235fd3e1",
    "07_before_effects.exr": "605e27a47b01bba9523248f06641fa9b17e91353fdda5dfa73338af6f6b91349",
    "08.exr": "624ea5ab9a10ee5108375a393841086bd6517e4dde6d89cee006688d663d6c0d",
    "08_before_effects.exr": "bce72ae30c659b2d4d9e243c1112e46ea16829fe391a1c115094a141cea591e7",
    "09.exr": "e8f8518ef98aaec54e385acb3acedf52a02b9f2bac1d1b877f8ee5c836e6cc30",
    "09_before_effects.exr": "d3f0c5ba481e3815ed797c85157211b1b86df417a8d59460361b6924a069a6fb",
    "10.exr": "ef75bf09758551e750aaee2c1cfd76ae5ed926f30bc55e7150903ff7e04512bd",
    "10_before_effects.exr": "2af3a489025ab885013d1d9bb2b3ebaef0a4dc51b17ae996596b26da30a7ba4b",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def function(text: str, name: str) -> str:
    match = re.search(
        rf"// === {re.escape(name)} @ [^\n]+ ===\s+.*?(?=\n// === FUN_|\Z)",
        text,
        re.S,
    )
    require(match is not None, f"cannot isolate pinned disassembly function {name}")
    return match.group(0)


def case_paths(root: Path, case_id: str) -> tuple[Path, Path]:
    stem = (
        "olm_bitdepth_32bpc_olmsmoother_v1_exr_20260710__"
        f"software_32bpc__fr24__{case_id}"
    )
    directory = root / WIN
    return directory / f"{stem}.exr", directory / f"{stem}_before_effects.exr"


def build_report(root: Path = ROOT) -> dict:
    manifest_path = root / MANIFEST
    request_path = root / REQUEST
    disasm_path = root / DISASM
    mac_path = root / MAC
    pipl_path = root / PIPL
    for relative, expected_hash in EXPECTED_SOURCE_HASHES.items():
        actual_hash = sha256(root / relative)
        require(actual_hash == expected_hash, f"pinned source hash drift: {relative}: {actual_hash}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))

    require(manifest["kind"] == "ae_effect_reference_manifest", "manifest kind drift")
    require(manifest["project"]["bits_per_channel"] == 32, "Windows project is not 32bpc")
    require(
        manifest["project"]["project_gpu_accel_type"]["current_name"] == "SOFTWARE",
        "Windows renderer is not SOFTWARE",
    )
    require(manifest["output_capabilities"]["float_preserving"] is True, "manifest is not float preserving")
    require(request["effect"] == {"match_name": "OLM Smoother", "name": "OLM Smoother"}, "request effect drift")
    request_cases = request["cases"]
    manifest_cases = manifest["cases"]
    require(len(request_cases) == len(manifest_cases) == 10, "expected exactly ten cases")
    request_by_id = {case["id"]: case for case in request_cases}
    require(len(request_by_id) == 10, "duplicate request case id")

    rows = []
    for index, case in enumerate(manifest_cases, 1):
        case_id = f"final_random10_olm_smoother_{index:02d}"
        require(case["id"] == case_id, f"manifest case order/id drift at {index}")
        require(case_id in request_by_id, f"case absent from request: {case_id}")
        require(case["output_format"] == "exr" and case["float_preserving"] is True, f"{case_id}: output drift")
        require(case["comp"]["width"] == 1920 and case["comp"]["height"] == 1080, f"{case_id}: comp dimensions drift")
        effect = case["effects"]
        require(len(effect) == 1 and effect[0]["match_name"] == "OLM Smoother", f"{case_id}: effect identity drift")
        observed = {
            item["property_index"]: item["value"]
            for item in effect[0]["params"]
            if item.get("match_name") in {
                "OLM Smoother-0001",
                "OLM Smoother-0002",
                "OLM Smoother-0003",
            }
        }
        expected = request_by_id[case_id]["params"]
        require(observed[1] == expected["__index_1"], f"{case_id}: use-key readback drift")
        require(observed[3] == expected["__index_3"], f"{case_id}: tolerance readback drift")
        require(
            len(observed[2]) == 4
            and all(abs(float(a) - float(b)) < 1e-6 for a, b in zip(observed[2], expected["__index_2"])),
            f"{case_id}: key-color readback drift",
        )

        effect_path, before_path = case_paths(root, case_id)
        require(
            sha256(effect_path) == EXPECTED_EXR_HASHES[f"{index:02d}.exr"],
            f"{case_id}: pinned effect EXR hash drift",
        )
        require(
            sha256(before_path) == EXPECTED_EXR_HASHES[f"{index:02d}_before_effects.exr"],
            f"{case_id}: pinned before-effects EXR hash drift",
        )
        require(effect_path.name == case["frame"], f"{case_id}: effect filename drift")
        require(before_path.name == case["before_effects_frame"], f"{case_id}: before filename drift")
        effect_planes, ew, eh, _ = read_planes_with_layout(effect_path)
        before_planes, bw, bh, _ = read_planes_with_layout(before_path)
        require(set(effect_planes) == set(before_planes) == {"A", "B", "G", "R"}, f"{case_id}: channel drift")
        require((ew, eh) == (bw, bh) == (1920, 1080), f"{case_id}: EXR dimensions drift")
        delta = compare(before_path, effect_path)
        rows.append(
            {
                "id": case_id,
                "classification": "exact_pass_through" if delta["mismatched_values"] == 0 else "effect_changing",
                "mismatched_float_values": delta["mismatched_values"],
                "max_raw_u32_delta": delta["max_raw_u32_delta"],
                "dimensions": [ew, eh],
                "effect_sha256": sha256(effect_path),
                "before_effects_sha256": sha256(before_path),
            }
        )

    changing = [row["id"] for row in rows if row["classification"] == "effect_changing"]
    exact = [row["id"] for row in rows if row["classification"] == "exact_pass_through"]
    require(len(changing) == 8, f"expected 8 effect-changing cases, got {changing}")
    require(exact == ["final_random10_olm_smoother_05", "final_random10_olm_smoother_07"], f"pass-through set drift: {exact}")

    disasm = disasm_path.read_text(encoding="utf-8")
    dispatcher = function(disasm, "FUN_1800096f0")
    require(dispatcher.count("FUN_180001400(") == 1, "PF8 dispatcher call drift")
    require(dispatcher.count("FUN_1800011e0(") == 1, "PF16 dispatcher call drift")
    require(
        re.search(r"if \(\(\*\(byte \*\)\(param_4 \+ 0x10\) & 1\) == 0\).*?FUN_180001400\(.*?\n  \}\n  else \{.*?FUN_1800011e0\(", dispatcher, re.S)
        is not None,
        "dispatcher is not the pinned two-way PF8/PF16 split",
    )
    require("PF_PixelFloat" not in dispatcher and "IterateFloat" not in dispatcher, "unexpected PF32 dispatcher branch")

    mac = mac_path.read_text(encoding="utf-8")
    pipl = pipl_path.read_text(encoding="utf-8")
    require("out_data->out_flags2 = 0x08000000;" in mac, "Mac runtime out_flags2 drift")
    require("AE_Effect_Global_OutFlags_2 { 0x08000000 }" in pipl, "PiPL out_flags2 drift")
    flags2 = 0x08000000
    require((flags2 & (1 << 10)) == 0, "Smart Render bit unexpectedly advertised")
    require((flags2 & (1 << 12)) == 0, "Float Color Aware bit unexpectedly advertised")
    require("short bitdepth = PF_WORLD_IS_DEEP(input) ? 16 : 8;" in mac, "classic Render is not 8/16 only")
    require("*outP = *inP;" in function_like(mac, "ScanlinePixelFloat_Main"), "float callback is not pass-through")
    require("case PF_Cmd_SMART_RENDER:" in mac, "float source path unexpectedly absent")

    return {
        "kind": "olmsmoother_v1_32bpc_host_conversion_boundary",
        "schema": 1,
        "status": "pass",
        "date": "2026-07-30",
        "windows": {
            "manifest_sha256": sha256(manifest_path),
            "request_sha256": sha256(request_path),
            "dimensions": [1920, 1080],
            "effect_changing_count": len(changing),
            "exact_pass_through_count": len(exact),
            "exact_pass_through_cases": exact,
            "cases": rows,
        },
        "binary": {
            "disassembly_sha256": sha256(disasm_path),
            "dispatcher": "FUN_1800096f0",
            "branches": ["PF8:FUN_180001400", "PF16:FUN_1800011e0"],
            "native_pf32_branch": False,
        },
        "mac": {
            "source_sha256": sha256(mac_path),
            "pipl_sha256": sha256(pipl_path),
            "out_flags2": "0x08000000",
            "threaded_rendering_bit27": True,
            "smart_render_bit10": False,
            "float_color_aware_bit12": False,
            "classic_render_depths": [8, 16],
            "float_pass_through_source_present": True,
            "float_path_advertised_by_declared_flags": False,
        },
        "conclusion": (
            "The retained Windows 32bpc project renders are host-conversion/classic-lane evidence, "
            "not evidence of a native PF32 callback in standalone OLMSmoother v1. A Mac AE "
            "effect/control comparison is required; no exact host-conversion numeric formula is asserted."
        ),
    }


def function_like(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\(.*?\n\}}", text, re.S)
    require(match is not None, f"cannot isolate source function {name}")
    return match.group(0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    report = build_report(args.root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    print("[OK] OLMSmoother v1 32bpc host-conversion boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
