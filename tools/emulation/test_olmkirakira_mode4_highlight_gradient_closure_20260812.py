#!/usr/bin/env python3
"""Close the bounded Mode-4 Highlight gradient box-filter seam."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
CORE = ROOT / "core/kirakira_highlight.h"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
SCAFFOLD = ROOT / "tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py"
PUBLIC = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
CURRENT_PROBE = ROOT / "tools/emulation/test_kirakira_highlight_canonical.cpp"
OLD_PROBE = ROOT / "tools/emulation/test_kirakira_highlight_separable_counterfactual.cpp"
HISTORICAL_SEAM = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json"
PF8_DECODE_CLOSURE = ROOT / "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json"
OUT = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json"
DOC = OUT.with_suffix(".md")

WORKER = Path(os.environ.get(
    "OLM_AEX_GUEST_WORKER",
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker",
))
EXPECTED = {
    "aex": "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
    "worker": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
    "asm": "d23c749d225a934580c96f2929fb9d7253d07b1be208faa9de6ff89efc1f89b3",
    "decomp": "990693e95695cd83032764f0452fbbe336b8f910ce4d9f5af94a2094c7f6328a",
    "core": "e98232e4224b6ae4dd372216e10c29f3ba6621f68ab6cb10b56a02b9cc248390",
    "source": "f2e285be7e6caae764bef7c4fa4a6c422bd5312368ba3481022b9eabe9035492",
    "scaffold": "df7e62dd9efd9ca4f039000129d25d0c4291b4efe2c0bb7e14b86d27d7da87d7",
    "current_probe": "b9247481f085da6714a99da405531677991f9d032aaf9985dc713de298da1981",
    "counterfactual_probe": "c52d3a472f16f071c46b6a74c307194f93b858b95198e02e6bba5bbde6290a23",
}
EXPECTED_SEED_SHA = "281139cc61343bc478d88ec592f27d909977147bc221ac1c7f96425e0d9f5376"
EXPECTED_RAY_SHA = "4c2e39a69241ae5ec473f1782839fc4e1f5a4afe888a7a8745d2471134bb245c"
EXPECTED_OLD_RAY_SHA = "2509a03ca80ae140b3368ff96a6232e1d8b8ace27b6a99159626002cecb11461"
EXPECTED_HISTORICAL_SEAM_SHA = "531179e93d198d6b794c6e9ba4869df624de24b9cc3464582ab3b13a6a192c82"
EXPECTED_PF8_DECODE_CLOSURE_SHA = "d3da9c00aa57297f7b2fa937803f6e8a2b1f955f01884e65edaed85435f03bb3"
EXPECTED_AGGREGATION_SHA = "e4f46ec47dae7845cc87e1a345b69b672ad61148b5fa71b4e3228aabb9b9260e"
EXPECTED_HOSTLESS_TYPED = {
    "PF8": "0181a1e39d16d438d980395368af4eb7caeb1ac20429de1ba2529d2360910e50",
    "PF16": "bf70b56862229c326a05782af505274da8eb4d748560d4c177cade608d471650",
    "PF32": "25ee167e73e0aa92e8f59620e3d99bcb1c233f080642849fdbcfb064523d60da",
}
EXPECTED_PUBLIC = {
    "PF8": (60, "5026fd55404879917f3b72e242987289e35c918b07edcdbe983005d6d019e38c"),
    "PF16": (120, "c2e203a0e5a355d98f7b1c23da47f398ec3fe846875b957d3b75e70b5f870c39"),
    "PF32": (240, "fbd4f245f442b20ec73a1e67b26286e4bc01b9cab7fde6b4b5a086a1e31612f9"),
}
EXPECTED_MODE1 = {
    "PF8": (True, "46245e23f8902a243be948ae282b0b1b3bf53a9f276c0566bc820917076e5ec9",
            "46245e23f8902a243be948ae282b0b1b3bf53a9f276c0566bc820917076e5ec9"),
    "PF16": (True, "71c2c1ae26ae4e63dc7e985f5b3666bd1a912fcc36d91842a0a2e65841693b13",
             "71c2c1ae26ae4e63dc7e985f5b3666bd1a912fcc36d91842a0a2e65841693b13"),
    "PF32": (True, "df36edb6a9a16c88c2eb7582928b80493df46da1a46708ee75495a2e513c3dc4",
             "df36edb6a9a16c88c2eb7582928b80493df46da1a46708ee75495a2e513c3dc4"),
}
EXPECTED_LIFECYCLE_SHA = "32909aa0670cf57563ce0af1d7a047884cf4be7c421eeab9796229012c36bfa3"
EXPECTED_SUITES = ["PF Handle Suite v2", "AEGP Utility Suite v13", "PF ColorParamSuite v1"]
EXPECTED_PIXEL_FORMATS = {"PF8": "argb8", "PF16": "argb16", "PF32": "argb32f"}
EXPECTED_CORE_CONTRACT = {
    "row_accumulator": "double",
    "column_accumulator": "double",
    "output_store": "float after one 2-D kernel-area scale",
}
EXPECTED_CLAIM_BOUNDARY = (
    "fixed 5x3 Highlight-only Radius=3 gradient tuple; natural hostless AEX ray and "
    "public exported Mode4 PF8/PF16/PF32"
)
EXPECTED_SUPERSEDES = "olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json"
EXPECTED_CLAIMS_NOT_MADE = [
    "No arbitrary dimensions, radii, sources, parameter Cartesian product, or live-AE promotion",
    "Mode 1 PF8 is exact only for the separately hash-bound source-decode tuple",
    "No claim that the baseline filter-type anchors prove the runtime CPU dispatch branch",
]
EXPECTED_OLD_DIFFERENCES = [
    {"word": 3, "actual": "0x3ed359b2", "old_separable": "0x3ed359b1", "ulp": 1},
    {"word": 11, "actual": "0x3ed24bf4", "old_separable": "0x3ed24bf5", "ulp": 1},
]
BOX_CALLS = ("18114fa95", "18114fae7", "18114fb39")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_sha(value: object) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def words_bytes(words: list[str]) -> bytes:
    return struct.pack(f"<{len(words)}I", *(int(word, 16) for word in words))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_hostless(directory: Path) -> dict[str, object]:
    scaffold = load_module(SCAFFOLD, "kira_highlight_gradient_scaffold")
    scaffold.NATURAL_JSON = directory / "hostless.json"
    scaffold.NATURAL_MD = directory / "hostless.md"
    result = scaffold.main(
        natural=True, natural_slot=4, natural_length=3,
        highlight_gradient=True, allow_ray_mismatch=False,
    )
    if result:
        raise RuntimeError("same-run Highlight scaffold did not close")
    return json.loads(scaffold.NATURAL_JSON.read_text(encoding="utf-8"))


def compile_ray(directory: Path, source: Path, seed: bytes) -> bytes:
    executable = directory / source.stem
    subprocess.run([
        "c++", "-std=c++20", "-O2", "-ffp-contract=off",
        str(source), "-o", str(executable),
    ], cwd=ROOT, check=True)
    input_words = "\n".join(f"{word:08x}" for word in struct.unpack("<15I", seed)) + "\n"
    output = subprocess.check_output(
        [str(executable), "5", "3", "3"], cwd=ROOT, input=input_words, text=True,
    )
    words = [int(line, 16) for line in output.splitlines()]
    if len(words) != 15:
        raise AssertionError("Highlight probe did not return 15 words")
    return struct.pack("<15I", *words)


def static_anchors() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    calls = {f"0x{site}": asm.count(f"{site}  CALL 0x181280bc0") for site in BOX_CALLS}
    types = {
        "baseline_RowSum<float,double>": decomp.count("_anon_24825CC5::RowSum<float,double>"),
        "baseline_ColumnSum<double,float>": decomp.count("_anon_24825CC5::ColumnSum<double,float>"),
    }
    if calls != {f"0x{site}": 1 for site in BOX_CALLS}:
        raise AssertionError(f"Highlight three-pass boxFilter callsites changed: {calls}")
    if types != {
        "baseline_RowSum<float,double>": 3,
        "baseline_ColumnSum<double,float>": 3,
    }:
        raise AssertionError(f"baseline boxFilter accumulator anchors changed: {types}")
    core = CORE.read_text(encoding="utf-8")
    for fragment in (
        "std::vector<double> horizontal",
        "const double scaled_sum = sum +",
        "static_cast<float>(scaled_sum * scale)",
    ):
        if core.count(fragment) != 1:
            raise AssertionError(f"production core anchor changed: {fragment}")
    return {
        "highlight_three_pass_boxfilter_calls": calls,
        "baseline_filter_types": types,
        "production_core_contract": {
            "row_accumulator": "double",
            "column_accumulator": "double",
            "output_store": "float after one 2-D kernel-area scale",
        },
    }


def run_public(directory: Path, mode: int) -> dict[str, object]:
    report_path = directory / f"mode{mode}.json"
    env = os.environ.copy()
    env.update({
        "OLM_KIRA_EXPORTED_CASE": f"mode{mode}_highlight_gradient_closure",
        "OLM_KIRA_EXPORTED_REPORT": str(report_path),
        "OLM_KIRA_BLUR_MODE": str(mode),
        "OLM_KIRA_MERGE_MODE": "1",
        "OLM_KIRA_BRIGHTNESS_GAIN": "1",
        "OLM_KIRA_GLOW_ROTATION": "0",
        "OLM_KIRA_HORIZONTAL_LENGTH": "0",
        "OLM_KIRA_DIAGONAL2_LENGTH": "0",
        "OLM_KIRA_HIGHLIGHT_RADIUS": "3",
        "OLM_KIRA_HIGHLIGHT_USE_RAMP": "0",
        "OLM_KIRA_SOURCE_PATTERN": "alpha_i_over_17",
        "OLM_AEX_GUEST_WORKER": str(WORKER),
    })
    process = subprocess.run(["python3", str(PUBLIC)], cwd=ROOT, env=env)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if process.returncode:
        raise RuntimeError(f"public Mode {mode} all-depth gate did not close")
    return report


def summarize_public(report: dict[str, object]) -> dict[str, object]:
    rows = []
    for row in report["rows"]:
        lifecycle = {
            "smart_pre_render": row["smart_pre_render"],
            "smart_render": row["smart_render"],
        }
        rows.append({
            "depth": row["depth"], "pixel_format": row["pixel_format"],
            "bytes": row["bytes"], "exact": row["exact"],
            "actual_exported_raw_sha256": row["actual_exported_raw_sha256"],
            "mac_effectmain_raw_sha256": row["mac_effectmain_raw_sha256"],
            "mac_active_bytes_sha256": sha(bytes.fromhex(row["mac_effectmain_active_hex"])),
            "lifecycle": lifecycle, "lifecycle_sha256": json_sha(lifecycle),
            "render_error": row["render_error"], "guards_intact": row["guards_intact"],
            "input_unchanged": row["input_unchanged"],
            "mac_padding_preserved": row["mac_padding_preserved"],
            "suite_requests": row["suite_requests"],
            "unsupported_suite_calls": row["unsupported_suite_calls"],
        })
    return {"source_status": report["status"], "rows": rows}


def validate_public(section: dict[str, object], mode: int) -> None:
    rows = section["rows"]
    assert [row["depth"] for row in rows] == ["PF8", "PF16", "PF32"]
    assert section["source_status"] == "exact"
    for row in rows:
        depth = row["depth"]
        size, _expected_public = EXPECTED_PUBLIC[depth]
        assert row["pixel_format"] == EXPECTED_PIXEL_FORMATS[depth]
        assert row["bytes"] == size
        if mode in (2, 4):
            _size, expected = EXPECTED_PUBLIC[depth]
            assert row["exact"]
            assert row["actual_exported_raw_sha256"] == expected
            assert row["mac_effectmain_raw_sha256"] == expected
            assert row["mac_active_bytes_sha256"] == expected
        else:
            exact, actual, mac = EXPECTED_MODE1[depth]
            assert row["exact"] is exact
            assert row["actual_exported_raw_sha256"] == actual
            assert row["mac_effectmain_raw_sha256"] == mac
            assert row["mac_active_bytes_sha256"] == mac
        assert row["lifecycle_sha256"] == EXPECTED_LIFECYCLE_SHA
        assert row["lifecycle_sha256"] == json_sha(row["lifecycle"])
        assert row["render_error"] == 0 and row["guards_intact"]
        assert row["input_unchanged"] and row["mac_padding_preserved"]
        assert row["suite_requests"] == EXPECTED_SUITES
        assert row["unsupported_suite_calls"] == []
        for item in row["lifecycle"].values():
            assert item["attempted"] and item["completed"] and item["error"] == 0


def validate_report(report: dict[str, object]) -> bool:
    try:
        assert report["schema_version"] == 1
        assert report["kind"] == "olmkirakira_mode4_highlight_gradient_closure"
        assert report["status"] == "raw_exact"
        assert report["claim_boundary"] == EXPECTED_CLAIM_BOUNDARY
        identities = report["identities"]
        for key in ("aex", "worker", "asm", "decomp", "core", "source", "scaffold", "current_probe"):
            assert identities[f"{key}_sha256"] == EXPECTED[key]
        assert identities["aex_sha256"] == sha(AEX.read_bytes())
        assert identities["worker_sha256"] == sha(WORKER.read_bytes())
        assert identities["asm_sha256"] == sha(ASM.read_bytes())
        assert identities["decomp_sha256"] == sha(DECOMP.read_bytes())
        assert identities["core_sha256"] == sha(CORE.read_bytes())
        assert identities["source_sha256"] == sha(SOURCE.read_bytes())
        assert identities["scaffold_sha256"] == sha(SCAFFOLD.read_bytes())
        assert identities["current_probe_sha256"] == sha(CURRENT_PROBE.read_bytes())
        assert identities["counterfactual_probe_sha256"] == EXPECTED["counterfactual_probe"]
        assert identities["counterfactual_probe_sha256"] == sha(OLD_PROBE.read_bytes())
        assert identities["generator_sha256"] == sha(Path(__file__).read_bytes())
        assert identities["aexcompat_commit"] == "28d535469f84f67236ef3425afe4291ea2fb0991"
        assert report["fixture"] == {
            "dimensions": [5, 3], "source_pattern": "gradient i/17",
            "hostless_source_rgba": "opaque gray i/17",
            "public_source_rgba": "RGB zero, alpha byte i*15",
            "blur_modes": {"primary": 4, "same_algorithm_control": 2, "cross_mode_control": 1},
            "highlight_radius": 3, "all_directional_lengths_zero": True,
            "merge_mode": 1, "brightness_gain": 1.0, "rotation": 0,
            "all_ramps_off": True,
        }
        hostless = report["hostless_same_run_actual_aex"]
        assert hostless["entry"] == {"function": "FUN_18114f4a0", "va": "0x18114f4a0", "entries": 1}
        assert hostless["direction"] == {
            "slot": 4, "angle_degrees": None, "glow_rotation": 0,
            "length": 3, "blur_mode": 4,
        }
        assert hostless["seed_words"] == 15 and hostless["seed_sha256"] == EXPECTED_SEED_SHA
        assert hostless["actual_ray_words"] == 15 and hostless["actual_ray_sha256"] == EXPECTED_RAY_SHA
        assert hostless["portable_ray_sha256"] == EXPECTED_RAY_SHA
        assert hostless["ray_exact"] and hostless["ray_differences"] == []
        assert hostless["aggregation_words"] == 60
        assert hostless["aggregation_sha256"] == EXPECTED_AGGREGATION_SHA
        assert hostless["suite_acquire_count"] == hostless["suite_release_count"] == 12
        assert hostless["fault"] is None
        assert hostless["typed_output_sha256"] == EXPECTED_HOSTLESS_TYPED
        counter = report["counterfactual_old_separable"]
        assert counter["current_ray_sha256"] == EXPECTED_RAY_SHA
        assert counter["current_exact"]
        assert counter["old_ray_sha256"] == EXPECTED_OLD_RAY_SHA
        assert counter["old_ray_differences"] == EXPECTED_OLD_DIFFERENCES
        for item in counter["old_ray_differences"]:
            assert item["ulp"] == abs(int(item["actual"], 16) - int(item["old_separable"], 16))
        assert counter["old_ray_difference_count"] == 2 and counter["old_ray_max_ulp"] == 1
        anchors = report["static_binary_and_core_anchors"]
        assert anchors["highlight_three_pass_boxfilter_calls"] == {f"0x{site}": 1 for site in BOX_CALLS}
        assert anchors["baseline_filter_types"] == {
            "baseline_RowSum<float,double>": 3,
            "baseline_ColumnSum<double,float>": 3,
        }
        assert anchors["production_core_contract"] == EXPECTED_CORE_CONTRACT
        validate_public(report["public_exported_mode4"], 4)
        validate_public(report["public_exported_mode2_control"], 2)
        validate_public(report["public_exported_mode1_cross_mode_regression"], 1)
        assert report["connected_pf8_source_decode_closure"] == {
            "path": "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json",
            "sha256": EXPECTED_PF8_DECODE_CLOSURE_SHA,
            "status": "raw_exact",
        }
        assert sha(PF8_DECODE_CLOSURE.read_bytes()) == EXPECTED_PF8_DECODE_CLOSURE_SHA
        assert json.loads(PF8_DECODE_CLOSURE.read_text(encoding="utf-8"))["status"] == "raw_exact"
        assert report["promotion"] == {
            "admitted": "Mode 4 Highlight Radius=3 alpha_i_over_17 tuple, PF8/PF16/PF32",
            "mode2_control": "exact regression only; no new promotion",
            "mode1_control": "PF8/PF16/PF32 exact after the separately hash-bound source-decode closure",
        }
        assert report["supersedes"] == EXPECTED_SUPERSEDES
        assert report["history"] == {
            "historical_seam": EXPECTED_SUPERSEDES,
            "sha256": EXPECTED_HISTORICAL_SEAM_SHA,
            "status": "fail_closed_pf32_seam",
        }
        assert report["history"]["sha256"] == sha(HISTORICAL_SEAM.read_bytes())
        historical = json.loads(HISTORICAL_SEAM.read_text(encoding="utf-8"))
        assert historical["status"] == report["history"]["status"]
        assert report["claims_not_made"] == EXPECTED_CLAIMS_NOT_MADE
        return True
    except (AssertionError, KeyError, TypeError, ValueError):
        return False


def main() -> int:
    paths = {
        "aex": AEX, "worker": WORKER, "asm": ASM, "decomp": DECOMP,
        "core": CORE, "source": SOURCE, "scaffold": SCAFFOLD,
        "current_probe": CURRENT_PROBE,
    }
    for key, path in paths.items():
        if sha(path.read_bytes()) != EXPECTED[key]:
            raise RuntimeError(f"unexpected pinned {key} identity")
    if sha(OLD_PROBE.read_bytes()) != EXPECTED["counterfactual_probe"]:
        raise RuntimeError("unexpected pinned counterfactual probe identity")
    if sha(HISTORICAL_SEAM.read_bytes()) != EXPECTED_HISTORICAL_SEAM_SHA:
        raise RuntimeError("immutable historical seam identity changed")
    if sha(PF8_DECODE_CLOSURE.read_bytes()) != EXPECTED_PF8_DECODE_CLOSURE_SHA:
        raise RuntimeError("PF8 source-decode closure identity changed")
    historical = json.loads(HISTORICAL_SEAM.read_text(encoding="utf-8"))
    if historical.get("status") != "fail_closed_pf32_seam":
        raise RuntimeError("immutable historical seam status changed")
    anchors = static_anchors()
    with tempfile.TemporaryDirectory(prefix="kira_mode4_highlight_gradient_closure_") as raw:
        directory = Path(raw)
        hostless_report = run_hostless(directory)
        actual = hostless_report["actual_aex"]
        seed = struct.pack("<15f", *actual["same_run_seed_f32"])
        actual_ray = words_bytes(actual["selected_ray_u32"])
        current_ray = compile_ray(directory, CURRENT_PROBE, seed)
        old_ray = compile_ray(directory, OLD_PROBE, seed)
        public4 = summarize_public(run_public(directory, 4))
        public2 = summarize_public(run_public(directory, 2))
        public1 = summarize_public(run_public(directory, 1))
    if actual_ray != current_ray:
        raise AssertionError("current two-dimensional double accumulator ray is not actual-AEX exact")
    actual_words = struct.unpack("<15I", actual_ray)
    old_words = struct.unpack("<15I", old_ray)
    old_differences = [
        {"word": index, "actual": f"0x{actual_word:08x}",
         "old_separable": f"0x{old_word:08x}", "ulp": abs(actual_word - old_word)}
        for index, (actual_word, old_word) in enumerate(zip(actual_words, old_words))
        if actual_word != old_word
    ]
    direction = dict(actual["same_run_direction"])
    direction.pop("seed_mat_address", None)
    typed_hashes = {
        depth: sha(bytes.fromhex(value["actual_hex"]))
        for depth, value in actual["typed_outputs"].items()
    }
    report = {
        "schema_version": 1,
        "kind": "olmkirakira_mode4_highlight_gradient_closure",
        "date": "2026-08-12", "status": "raw_exact",
        "claim_boundary": EXPECTED_CLAIM_BOUNDARY,
        "identities": {
            **{f"{key}_sha256": sha(path.read_bytes()) for key, path in paths.items()},
            "counterfactual_probe_sha256": sha(OLD_PROBE.read_bytes()),
            "generator_sha256": sha(Path(__file__).read_bytes()),
            "aexcompat_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
        },
        "fixture": {
            "dimensions": [5, 3], "source_pattern": "gradient i/17",
            "hostless_source_rgba": "opaque gray i/17",
            "public_source_rgba": "RGB zero, alpha byte i*15",
            "blur_modes": {"primary": 4, "same_algorithm_control": 2, "cross_mode_control": 1},
            "highlight_radius": 3, "all_directional_lengths_zero": True,
            "merge_mode": 1, "brightness_gain": 1.0, "rotation": 0,
            "all_ramps_off": True,
        },
        "hostless_same_run_actual_aex": {
            "entry": hostless_report["entry"], "direction": direction,
            "seed_words": 15, "seed_sha256": sha(seed),
            "actual_ray_words": 15, "actual_ray_sha256": sha(actual_ray),
            "portable_ray_sha256": sha(words_bytes(actual["portable_ray_u32"])),
            "ray_exact": actual["selected_ray_u32"] == actual["portable_ray_u32"],
            "ray_differences": actual["ray_differences"],
            "aggregation_words": len(actual["aggregation_u32"]),
            "aggregation_sha256": sha(words_bytes(actual["aggregation_u32"])),
            "typed_output_sha256": typed_hashes,
            "suite_acquire_count": actual["suite_acquire_count"],
            "suite_release_count": actual["suite_release_count"],
            "fault": actual["fault"],
        },
        "counterfactual_old_separable": {
            "description": "normalize/cast after horizontal, then normalize/cast after vertical, repeated three times",
            "current_ray_sha256": sha(current_ray), "current_exact": current_ray == actual_ray,
            "old_ray_sha256": sha(old_ray),
            "old_ray_difference_count": len(old_differences),
            "old_ray_max_ulp": max(item["ulp"] for item in old_differences),
            "old_ray_differences": old_differences,
        },
        "static_binary_and_core_anchors": anchors,
        "public_exported_mode4": public4,
        "public_exported_mode2_control": public2,
        "public_exported_mode1_cross_mode_regression": public1,
        "connected_pf8_source_decode_closure": {
            "path": "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json",
            "sha256": EXPECTED_PF8_DECODE_CLOSURE_SHA,
            "status": "raw_exact",
        },
        "promotion": {
            "admitted": "Mode 4 Highlight Radius=3 alpha_i_over_17 tuple, PF8/PF16/PF32",
            "mode2_control": "exact regression only; no new promotion",
            "mode1_control": "PF8/PF16/PF32 exact after the separately hash-bound source-decode closure",
        },
        "supersedes": "olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json",
        "history": {
            "historical_seam": EXPECTED_SUPERSEDES,
            "sha256": sha(HISTORICAL_SEAM.read_bytes()),
            "status": historical["status"],
        },
        "claims_not_made": EXPECTED_CLAIMS_NOT_MADE,
    }
    if not validate_report(report):
        raise AssertionError("Highlight gradient closure report validation failed")
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira Mode 4 Highlight gradient closure（2026-08-12）\n\n"
        "Status: **raw exact**\n\n"
        "5×3、Highlight Radius 3、gradient `i/17` の限定tuple。actual AEX same-run seedから"
        "Highlight rayまで15/15 words exact。旧separable実装のword 3/11各1 ULP差は"
        "counterfactualとして保持した。AEXの3回の`boxFilter` callsiteと"
        "`RowSum<float,double>`→`ColumnSum<double,float>`を静的に固定し、"
        "public Mode 4 PF8/PF16/PF32はそれぞれ`5026fd…`、`c2e203…`、`fbd4f245…`でraw exact。\n\n"
        "Mode 2の同tupleは3深度exactの回帰control。Mode 1も別のhash-bound PF8 "
        "source-decode closure `olmkirakira_pf8_source_decode_closure_20260812.json` "
        f"（SHA-256 `{EXPECTED_PF8_DECODE_CLOSURE_SHA}`）を適用後、この固定tupleは3深度exactである。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "raw_exact", "mode4_depths": 3,
                      "old_ray_differences": [item["word"] for item in old_differences],
                      "mode1_exact": [row["exact"] for row in public1["rows"]]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
