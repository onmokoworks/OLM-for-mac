#!/usr/bin/env python3
"""Build, run, write, and validate Kira's bounded public Smart closure."""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HARNESS = ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
DOC = REPORT.with_suffix(".md")
DEPTHS = (8, 16, 32)

def rows(a: str, b: str, c: str) -> dict[int, str]:
    return dict(zip(DEPTHS, (a, b, c)))

EXPECTED = {
    "m1_h7_r0": rows("ff4de3ff2622faf02c62afe42a7c850586fea7f0fa7a3777f329b1d82b88ed5b", "ee37cf06360d144b85b8d7a32ce9b0612af1f354a0a988c9e1e952e58b9ce41d", "0d50d86e40f9dd25daef5683e78bc3c066501477ccc36c8c4c7eab0c274b2cb6"),
    "m1_h7_r1": rows("9c20573663b0cda83708eeb206ac7a6dddd6705629eeee0f7a9d357959881ef6", "80792b3f984e959150aacfecbc4bc01ab2ee51f047c41f5676df5fb9073479f2", "4a221600eb32528a6b186712f1dc9a3d5f97b2f61add1ae8662e8c52e2dd58bb"),
    "m1_highlight_r3": rows("46245e23f8902a243be948ae282b0b1b3bf53a9f276c0566bc820917076e5ec9", "71c2c1ae26ae4e63dc7e985f5b3666bd1a912fcc36d91842a0a2e65841693b13", "df36edb6a9a16c88c2eb7582928b80493df46da1a46708ee75495a2e513c3dc4"),
    "m2_h7_ramp_r0": rows("9193537a74075244aa1a7c38f506dbc546864940942315f7358fbab5d2145d26", "7df16d7172e645dacc52711a6c3fbf49faeb2eaba00ef463a9c00584d4fbe0ad", "f3d831eab1bc4d57e787733aeffd0863a1840cbf0bf7e79dd1f2d4eec60c1763"),
    "m2_h7_ramp_r1": rows("0328f5deed53fdab62d0ce08db1f2666fe13b8cbd85c743f85dc0d048c127ace", "d7cad5ac7c353627bef978b85205fefb749bff6fa2e1b6a9429d772f7edd73fd", "024e207a669266ad0e8382d80adef67f6b55fdfc17e208b060bf2340a79b9eb6"),
    "m2_h7_ramp_r22_g073": rows("189bb206a4ed6bf15e184de6f63fa2b4b72d21419b86e65ee6685d3b50f9f1c8", "78700c7c4e5f680fcc9fc4b8fbd86d6e8ba364b252b6755cb47178c1b9014625", "8c86b78f9a81cf7988ef7c76c2108e221b8cfc65fd129ac166e0b5e73651014f"),
    "m2_highlight_r3": rows("5026fd55404879917f3b72e242987289e35c918b07edcdbe983005d6d019e38c", "c2e203a0e5a355d98f7b1c23da47f398ec3fe846875b957d3b75e70b5f870c39", "fbd4f245f442b20ec73a1e67b26286e4bc01b9cab7fde6b4b5a086a1e31612f9"),
    "m3_h50_r0": rows("0cf9de4e73720eba926739b6f1a92d901bd0b64b9e29c597a6239a43da415d94", "67b1fbbf6750a81d8fe2ac6c5d3d96457714f6437770bb3842a35f5d853da5a4", "36a6eebfb764e075667cf1d0f40cba6d7e8ef7fb65fbc95b66721e7ae44a1518"),
    "m3_h50_r1": rows("a338165e447b5a22b49c089763a9cbaf3325e29c05e7ed76047b19ad7a821564", "8228e38081d8e8d84df7263bdf3dfeb9b2c873a43c0423c9a81a8f2304af9986", "3d7f63c1ff88a3a4f00205af6a553a6f7a0927f5ae68bd4e93a2d901f55749f5"),
    "m4_highlight_r3": rows("5026fd55404879917f3b72e242987289e35c918b07edcdbe983005d6d019e38c", "c2e203a0e5a355d98f7b1c23da47f398ec3fe846875b957d3b75e70b5f870c39", "fbd4f245f442b20ec73a1e67b26286e4bc01b9cab7fde6b4b5a086a1e31612f9"),
    "m4_h5_ramp": rows("bacc1fc79a6076e6ef5a681ed444acd18de5585cb47b7332ef9628c5e494ed34", "28ffaa5d3c1a66c4095c89dd7ccb87782b30a8ae8d7bc9f21779efedcbe1914e", "5cc484e50772e2acd74bc85b4c5d073837cd7349c22d068d655ab0ed3877bd49"),
    "m4_d2_l7": rows("30b58167110e9bcc125244395ee07a16a6e8d00142869fd283f10f264b1ae0f6", "0853a40e66d15baf32fc85a6233b2fc387ec8413b1d4789df736c66afe5ea4b3", "1eb072a44e5fad044073c09245f25ff1a4359f378e24c28cbaa6a62fd6025d27"),
    "m4_highlight_ramp": rows("d7a4fd9628e70685681455e3971110d125112086a94db3fb11b3b6170ee46917", "81bafe08009db7c1be9400a788527a4df899b2f5e05a33981e6a0aac0a1391b0", "b8421b82508a79162b116e90408a6013419f07b47a4d6150aac4f767d8963537"),
    "m4_multiray": rows("5befdae0f497de64a04804c3576c8960f4d9fc06a664c7ea8e692600e1c38233", "92fdd029c1a005be30c8f57d7049ff284dd5a452466166ffb1a1393456b2798d", "4b82d09706892d87e42088a909dc5884a158e711947cf86181444a7e3108f858"),
}
EXPECTED_CONTRACT = {"dimensions": [5,3], "row_padding_bytes": 12, "admitted_tuple_count": 14,
    "positive_cell_count": 42, "partial_request_returns_full_frame": True, "returns_extra_pixels": True,
    "preserve_rgb_of_zero_alpha": True, "pre_render_data_deleter_invoked": True,
    "parameter_lifecycle": "25 base plus enabled ramps; 25x8, 26x5, 27x1", "pixel_callback_lifecycle": [1,1,1,0],
    }
EXPECTED_SCOPE = {"public_admission": "same 14 Classic tuples only", "installed": False, "ae_host_run": False}
EXPECTED_NEGATIVE_MATRIX = {"checkout_fail_tuple_ordinal_cells":357,"checkin_fail_tuple_ordinal_cells":357,
    "parameter_lifecycle_failure_cells":714,"color_suite_fail":True,"layer_output_error_and_null":True,
    "world_layout_extent_origin_format_depth_rowbytes_data_alias":True,"source_tuple_ramp_rejected":True,
    "all_output_untouched":True}
BASE_25 = {name: 25 + (name in {"m2_h7_ramp_r0","m2_h7_ramp_r1","m2_h7_ramp_r22_g073","m4_h5_ramp","m4_multiray"}) +
           (name in {"m4_highlight_ramp","m4_multiray"}) for name in EXPECTED}
NAMED_STAGE = {
 "pre_request_unlisted":(516,"0/0/0/0","0/0",0,False),"pre_checkout_error":(1003,"1/0/0/0","0/0",0,False),
 "pre_result_rect":(516,"1/0/0/0","0/0",0,False),"pre_max_result_rect":(516,"1/0/0/0","0/0",0,False),
 "pre_ref_width":(516,"1/0/0/0","0/0",0,False),"pre_ref_height":(516,"1/0/0/0","0/0",0,False),
 "pre_checkout_throw":(1013,"1/0/0/0","0/0",0,False),"layer_error":(1001,"1/1/0/0","0/0",0,True),
 "layer_null":(516,"1/1/0/0","0/0",0,True),"layer_throw":(1011,"1/1/0/0","0/0",0,True),
 "output_error":(1002,"1/1/1/0","0/0",0,True),"output_null":(516,"1/1/1/0","0/0",0,True),
 "output_throw":(1012,"1/1/1/0","0/0",0,True),"color_suite_error":(900,"1/1/1/0","6/6",1,True),
 "color_acquire_error":(516,"1/1/1/0","6/6",0,True),"color_suite_null":(516,"1/1/1/0","6/6",0,True),
 "color_function_null":(516,"1/1/1/0","6/6",0,True),"pica_null_smart":(516,"1/0/0/0","0/0",0,True),
 "pica_null_classic":(516,"1/0/0/0","0/0",0,True),
}

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())

def canonical(cells: list[dict]) -> str:
    return sha_bytes(json.dumps(cells, sort_keys=True, separators=(",", ":")).encode())

def canonical_negatives(rows: list[dict]) -> str:
    return sha_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())

def canonical_controls(rows: list[dict]) -> str:
    return sha_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())

def parse_line(line: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in shlex.split(line)[1:] if "=" in part)

NEGATIVE_NAMES = {
    "layer_error", "layer_null", "output_error", "output_null", "color_suite_error",
    "input_width", "input_height", "output_width", "output_height", "input_extent",
    "output_extent", "input_origin", "output_origin", "format_mismatch", "unsupported_format",
    "declared_depth", "input_rowbytes_short", "output_rowbytes_short", "input_rowbytes_extra",
    "output_rowbytes_extra", "input_data_null", "output_data_null", "world_alias", "world_overlap",
    "source_mutation", "tuple_mutation", "ramp_null", "ramp_short", "ramp_lock_null",
    "ramp_count_overflow",
    "input_deep_clear", "output_deep_clear",
    "pre_request_unlisted", "pre_checkout_error", "pre_result_rect", "pre_max_result_rect",
    "pre_ref_width", "pre_ref_height", "layer_throw", "output_throw", "color_acquire_error",
    "color_suite_null", "input_flags_extra", "output_flags_extra",
    "pre_checkout_throw", "color_function_null", "pica_null_smart", "pica_null_classic",
    "predata_null", "predata_width", "predata_height",
}
for _n in NEGATIVE_NAMES - NAMED_STAGE.keys():
    if _n in {"source_mutation","tuple_mutation"}: NAMED_STAGE[_n]=(516,"1/1/1/0","25/25",5,True)
    elif _n.startswith("ramp_"): NAMED_STAGE[_n]=(516,"1/1/1/0","20/20",5,True)
    elif _n=="input_data_null": NAMED_STAGE[_n]=(516,"1/1/0/0","0/0",0,True)
    else: NAMED_STAGE[_n]=(516,"1/1/1/0","0/0",0,True)

def run_harness() -> tuple[list[dict], list[dict]]:
    with tempfile.TemporaryDirectory(prefix="kira_public_smart_") as raw:
        exe = Path(raw) / "closure"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        define = '-DKIRA_SOURCE="' + str(SOURCE) + '"'
        cmd = ["clang++", "-std=c++20", "-O2", "-fno-fast-math", "-ffp-contract=off",
               "-isysroot", sdk, "-w", "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), define, str(HARNESS),
               str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
               "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if built.returncode: raise RuntimeError(built.stderr[-8000:])
        ran = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        if ran.returncode: raise RuntimeError(f"harness={ran.returncode}\n{ran.stdout[-8000:]}\n{ran.stderr}")
    parsed = [parse_line(line) for line in ran.stdout.splitlines() if line.startswith("CASE ")]
    positives = [r for r in parsed if r["fail"] == "-1/-1"]
    cells = []
    for r in positives:
        key, depth = r["tuple"], int(r["depth"])
        smart = sha_bytes(bytes.fromhex(r["smart_hex"]))
        classic = sha_bytes(bytes.fromhex(r["classic_hex"]))
        oracle = EXPECTED[key][depth]
        if not (r["pre"] == r["smart"] == r["classic"] == "0" and
                r["callbacks"] == "1/1/1/0" and
                r["param_order"] == r["input"] == r["headers"] == r["pads"] ==
                r["exact"] == r["extra"] == r["requested_full"] == "1" and smart == classic == oracle):
            raise AssertionError((r, smart, classic, oracle))
        param_count = 25 + (key in {"m2_h7_ramp_r0", "m2_h7_ramp_r1", "m2_h7_ramp_r22_g073", "m4_h5_ramp", "m4_multiray"}) + (key in {"m4_highlight_ramp", "m4_multiray"})
        if r["params"] != f"{param_count}/{param_count}": raise AssertionError(r)
        cells.append({"tuple": key, "depth": depth, "pixel_format": {8:"PF8/ARGB32",16:"PF16/ARGB64",32:"PF32/ARGB128"}[depth],
                      "oracle_sha256": oracle, "smart_sha256": smart, "classic_sha256": classic,
                      "input_header_padding_immutable": True, "checkout_checkin": [param_count, param_count],
                      "pixel_callbacks": [1, 1, 1, 0]})
    if len(cells) != 42: raise AssertionError(len(cells))
    failures = [r for r in parsed if r["fail"] != "-1/-1"]
    if len(failures) != 714 or not all(r["injected_ok"] == "1" for r in failures):
        raise AssertionError("parameter lifecycle failures did not all fail closed")
    negatives = []
    for r in failures:
        checkout, checkin = map(int, r["fail"].split("/"))
        ordinal = checkout if checkout >= 0 else checkin
        kind = "checkout" if checkout >= 0 else "checkin"
        expected_error = (700 if kind == "checkout" else 800) + ordinal
        if int(r["smart"]) != expected_error or r["input"] != "1" or r["headers"] != "1":
            raise AssertionError(r)
        negatives.append({"identity": f"param_{r['tuple']}_{kind}_{ordinal}", "error": int(r["smart"]),
                          "callbacks": r["callbacks"], "param_attempts": r["attempts"],
                          "output_untouched": True, "input_headers_immutable": True})
    parsed_neg = [parse_line(line) for line in ran.stdout.splitlines() if line.startswith("NEG ")]
    if {r["name"] for r in parsed_neg} != NEGATIVE_NAMES:
        raise AssertionError({r["name"] for r in parsed_neg} ^ NEGATIVE_NAMES)
    for r in parsed_neg:
        pre_failure = r["name"].startswith("pre_")
        if not ((int(r["pre"]) != 0 if pre_failure else r["pre"] == "0") and int(r["error"]) != 0 and
                r["output_untouched"] == r["input_headers_immutable"] == "1" and
                r["deleted"] == ("0" if pre_failure else "1")):
            raise AssertionError(r)
        negatives.append({"identity": r["name"], "error": int(r["error"]),
                          "callbacks": r["callbacks"], "param_attempts": r["params"],
                          "color_attempts": int(r["colors"]), "output_untouched": True,
                          "input_headers_immutable": True, "predata_deleted": not pre_failure})
    request_controls=[]
    for r in [parse_line(line) for line in ran.stdout.splitlines() if line.startswith("REQUEST_CONTROL ")]:
        depth=int(r["depth"]); smart=sha_bytes(bytes.fromhex(r["smart_hex"])); classic=sha_bytes(bytes.fromhex(r["classic_hex"])); oracle=EXPECTED[r["tuple"]][depth]
        if not (r["pre"]==r["smart"]==r["classic"]=="0" and r["callbacks"]=="1/1/1/0" and
                r["params"]=="25/25" and r["param_order"]==r["input"]==r["headers"]==r["pads"]==r["exact"]==r["extra"]==r["requested_full"]=="1" and smart==classic==oracle):
            raise AssertionError(r)
        request_controls.append({"tuple":r["tuple"],"depth":depth,"request_rect":[0,0,5,3],"oracle_sha256":oracle,"smart_sha256":smart,"classic_sha256":classic,"callbacks":[1,1,1,0],"checkout_checkin":[25,25]})
    if len(request_controls)!=3: raise AssertionError(request_controls)
    return cells, negatives, request_controls

def expected_identity_set() -> set[tuple[str, int, str]]:
    return {(name, depth, digest) for name, ds in EXPECTED.items() for depth, digest in ds.items()}

def validate(data: dict) -> None:
    assert set(data) == {"kind","date","status","identities","contract","positive_cells",
                         "canonical_cells_sha256","negative_rows","canonical_negative_rows_sha256",
                         "request_controls","canonical_request_controls_sha256","negative_matrix","scope"}
    assert data["date"] == "2026-08-12"
    assert data["kind"] == "olmkirakira_public_smart_bounded_closure"
    assert data["status"] == "raw_exact_bounded_public_smart"
    identities = data["identities"]
    assert identities["production_source_sha256"] == sha(SOURCE)
    assert identities["harness_sha256"] == sha(HARNESS)
    assert identities["aex_sha256"] == "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
    assert identities["aexcompat_worker_sha256"] == "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61"
    assert identities["aexcompat_commit"] == "28d535469f84f67236ef3425afe4291ea2fb0991"
    assert set(identities) == {"production_source_sha256","harness_sha256","aex_sha256","aexcompat_worker_sha256","aexcompat_commit"}
    cells = data["positive_cells"]
    assert len(cells) == 42
    got = {(c["tuple"], c["depth"], c["oracle_sha256"]) for c in cells}
    assert got == expected_identity_set()
    assert all(c["smart_sha256"] == c["classic_sha256"] == c["oracle_sha256"] for c in cells)
    for c in cells:
        assert set(c) == {"tuple","depth","pixel_format","oracle_sha256","smart_sha256","classic_sha256",
                          "input_header_padding_immutable","checkout_checkin","pixel_callbacks"}
        assert c["pixel_format"] == {8:"PF8/ARGB32",16:"PF16/ARGB64",32:"PF32/ARGB128"}[c["depth"]]
        assert c["pixel_callbacks"] == [1,1,1,0] and c["input_header_padding_immutable"] is True
        assert c["checkout_checkin"] == [BASE_25[c["tuple"]], BASE_25[c["tuple"]]]
    assert data["canonical_cells_sha256"] == canonical(cells)
    negatives = data["negative_rows"]
    assert len(negatives) == 765
    assert {r["identity"] for r in negatives if not r["identity"].startswith("param_")} == NEGATIVE_NAMES
    assert data["canonical_negative_rows_sha256"] == canonical_negatives(negatives)
    assert all(r["output_untouched"] and r["input_headers_immutable"] for r in negatives)
    param_rows = [r for r in negatives if r["identity"].startswith("param_")]
    expected_param_ids = {f"param_{name}_{kind}_{ordinal}" for name,count in BASE_25.items()
                          for kind in ("checkout","checkin") for ordinal in range(count)}
    assert {r["identity"] for r in param_rows} == expected_param_ids
    for r in param_rows:
        assert set(r) == {"identity","error","callbacks","param_attempts","output_untouched","input_headers_immutable"}
        parts=r["identity"].rsplit("_",2); kind=parts[-2]; ordinal=int(parts[-1])
        assert r["error"] == (700 if kind=="checkout" else 800)+ordinal
        assert r["callbacks"] == "1/1/1/0" and r["output_untouched"] is True
        assert r["input_headers_immutable"] is True
        assert r["param_attempts"] == (f"{ordinal+1}/{ordinal}" if kind=="checkout" else f"{ordinal+1}/{ordinal+1}")
    named = [r for r in negatives if not r["identity"].startswith("param_")]
    assert {r["identity"] for r in named} == NEGATIVE_NAMES
    for r in named:
        assert set(r) == {"identity","error","callbacks","param_attempts","color_attempts",
                          "output_untouched","input_headers_immutable","predata_deleted"}
        assert (r["error"],r["callbacks"],r["param_attempts"],r["color_attempts"],r["predata_deleted"]) == NAMED_STAGE[r["identity"]]
    assert data["contract"] == EXPECTED_CONTRACT
    assert data["scope"] == EXPECTED_SCOPE
    assert data["negative_matrix"] == EXPECTED_NEGATIVE_MATRIX
    controls=data["request_controls"]
    assert len(controls)==3 and {r["depth"] for r in controls}=={8,16,32}
    assert data["canonical_request_controls_sha256"]==canonical_controls(controls)
    for r in controls:
        assert set(r)=={"tuple","depth","request_rect","oracle_sha256","smart_sha256","classic_sha256","callbacks","checkout_checkin"}
        assert r["tuple"]=="m1_h7_r0" and r["request_rect"]==[0,0,5,3] and r["callbacks"]==[1,1,1,0] and r["checkout_checkin"]==[25,25]
        assert r["oracle_sha256"]==r["smart_sha256"]==r["classic_sha256"]==EXPECTED[r["tuple"]][r["depth"]]
    assert data["contract"]["admitted_tuple_count"] == 14
    assert data["contract"]["dimensions"] == [5, 3]
    assert data["contract"]["row_padding_bytes"] == 12
    assert data["negative_matrix"]["checkout_fail_tuple_ordinal_cells"] == 357
    assert data["negative_matrix"]["checkin_fail_tuple_ordinal_cells"] == 357
    assert data["negative_matrix"]["all_output_untouched"] is True

def make_report(cells: list[dict], negatives: list[dict], request_controls: list[dict]) -> dict:
    return {
        "kind": "olmkirakira_public_smart_bounded_closure", "date": "2026-08-12",
        "status": "raw_exact_bounded_public_smart",
        "identities": {"production_source_sha256": sha(SOURCE), "harness_sha256": sha(HARNESS),
                       "aex_sha256": "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
                       "aexcompat_worker_sha256": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
                       "aexcompat_commit": "28d535469f84f67236ef3425afe4291ea2fb0991"},
        "contract": EXPECTED_CONTRACT,
        "positive_cells": cells, "canonical_cells_sha256": canonical(cells),
        "request_controls": request_controls, "canonical_request_controls_sha256": canonical_controls(request_controls),
        "negative_rows": negatives, "canonical_negative_rows_sha256": canonical_negatives(negatives),
        "negative_matrix": EXPECTED_NEGATIVE_MATRIX,
        "scope": EXPECTED_SCOPE,
    }

def markdown(data: dict) -> str:
    return ("# OLMKiraKira bounded public Smart closure (2026-08-12)\n\n"
            "The Mac public SmartPreRender → SmartRender owner is raw-byte exact for the same "
            "14 fixed 5×3 tuples admitted by Classic, at PF8/PF16/PF32 (42 canonical cells using "
            "the measured partial request). Each Smart "
            "active plane equals both the Classic EffectMain plane and the pinned actual Windows "
            "oracle hash. Input bytes, world headers, and 12-byte row padding remain immutable.\n\n"
            "The partial pre-render request returns the full 5×3 result/max rect with "
            "`PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS`, preserves zero-alpha RGB, and exercises "
            "the pre-render-data deleter. Separate full-request controls are exact at PF8/PF16/PF32 "
            "(3/3). Smart parameters use the Windows-conditional lifecycle: "
            "25 checkouts/checkins for eight tuples, 26 for five, and 27 for multiray.\n\n"
            "The 765 fail-closed negative rows include 714 parameter checkout/checkin failure rows. "
            "Malformed callbacks, parameters, ramps, worlds, layouts, formats, depths, extents, "
            "origins, rowbytes, data, aliases, sources, and tuples fail closed before output mutation.\n\n"
            f"Canonical 42-cell digest: `{data['canonical_cells_sha256']}`.\n\n"
            "Verify read-only: `python3 tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py`\n\n"
            "Regenerate explicitly: append `--write`. No install or AE host action is performed.\n")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only or not args.write:
        saved=json.loads(REPORT.read_text())
        validate(saved)
        cells, negatives, request_controls=run_harness()
        fresh=make_report(cells, negatives, request_controls)
        validate(fresh)
        if fresh != saved: raise AssertionError("fresh semantic harness result differs from canonical report")
        print(json.dumps({"status": "validated", "report_sha256": sha(REPORT)}))
        return 0
    cells, negatives, request_controls = run_harness()
    data = make_report(cells, negatives, request_controls)
    validate(data)
    REPORT.write_text(json.dumps(data, indent=2) + "\n")
    DOC.write_text(markdown(data))
    print(json.dumps({"status": data["status"], "cells": len(cells), "canonical": data["canonical_cells_sha256"]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
