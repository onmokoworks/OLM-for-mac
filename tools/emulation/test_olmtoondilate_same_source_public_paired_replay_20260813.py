#!/usr/bin/env python3
"""Regenerate the exact-12 ToonDilate public-owner paired replay closure.

Default execution performs fresh, transient Windows-AEX and Mac public
replays and compares the canonical result with the checked-in artifacts.
Only --write updates the JSON/Markdown evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
AEX_RUNNER = ROOT / "tools/emulation/probe_olmtoondilate_same_source_actual_aex_20260813.py"
MAC_RUNNER = ROOT / "tools/emulation/test_olmtoondilate_same_source_mac_public_20260813.py"
MAC_PROBE = ROOT / "tools/emulation/probe_olmtoondilate_same_source_mac_public_20260813.cpp"
PRE_FLAG_REPORT = ROOT / "refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json"
REPORT = ROOT / "refs/conformance/olmtoondilate_same_source_public_paired_replay_20260813.json"
DOC = REPORT.with_suffix(".md")

SOURCE_SHA = "42b47acbc3cd37bcaefdedc1b46f0507ed2e478c5eaab921f645f9055a9c8470"
AEX_SHA = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
AEX_RUNNER_SHA = "a25e421ad170a13b045a525a297ebd35b0a8e0d596b54d639efbff561aea04d5"
MAC_RUNNER_SHA = "3fa2255c2ca98b28fa81c73fb2d606354f5adc33dc58b3bc09a155d4bface00a"
MAC_PROBE_SHA = "17fcace86b9d5c95fe6d4d136a5df04f7659f60d39ac45296e8ecf335df10f00"
PRE_FLAG_REPORT_SHA = "7713103e879a1da5eb2d0758c917229f353bd1fd2f08533516e4c8fdb1194e1e"
PAIRED_ROWS_SHA = "4bcb94801709d6a898b3623f76535b7ced6c34a03b41a6d120d6e8464969844c"
NEGATIVE_ROWS_SHA = "76a78f0f693ee111a9b9cc028e39c40bf3c39993d7883ea34cfee4c5a1dc0a29"

ORDER = [f"PF{depth}_{family}" for depth in (8, 16, 32) for family in
         ("copy", "fractional", "tie_semialpha", "high_downsample")]
TUPLES = {
    "copy": ([7, 5], 0.0, "0000000000000000", "00000000", [1, 1], 0),
    "fractional": ([9, 7], 2.01, "14ae47e17a140040", "d7a30040", [1, 1], 3),
    "tie_semialpha": ([7, 3], 3.0, "0000000000000840", "00004040", [1, 1], 3),
    "high_downsample": ([513, 17], 100.0, "0000000000005940", "0000c842", [2, 1], 200),
}
ACTIVE = {
    "PF8_copy": ("28fcdd1bae528a5ca9b3d0ed04599003b0c244d62c2a49c7c7600cbdd3a0d87e", "28fcdd1bae528a5ca9b3d0ed04599003b0c244d62c2a49c7c7600cbdd3a0d87e"),
    "PF8_fractional": ("b0bb2f13a7b1df3715f3166e8c170801f3e547e6261e9af40ceb309b0b74f593", "9e22bace19f7dae26258e99573917c68b7327e6d1ccaf141940be94e2d70e27d"),
    "PF8_tie_semialpha": ("3e82a3170b01e243044550f4ec7c73823901e3d9decb21441fe9850d517545ef", "05dd195813a594c4185a488a0433eaca16b8668cd6588f48fb77ca7c0050eb0c"),
    "PF8_high_downsample": ("10a8f71efc874ad922ad1784eab5f0eec57a623eeca2742e54ef2de55148c902", "5aeed3ca62bc73ecc24a4fa05fc3db2b9b5ac258de2ce90c98724ea055d4707a"),
    "PF16_copy": ("29728fe4ef8dbec47f7fd68da5a9a582b59066038b27add5ebe87071c8f09b54", "29728fe4ef8dbec47f7fd68da5a9a582b59066038b27add5ebe87071c8f09b54"),
    "PF16_fractional": ("3bcb46077510265bd25eec45104f439f587bd03495df5edce01c61cecba21037", "b57f15217528ebbe5b1b61415688f3d046c417d39c361a6a07dfda9c24faac59"),
    "PF16_tie_semialpha": ("31af1cb49d73db7b803b95a653d51bf583a00fae9ff78cd98847e35d14bb7cbe", "d52a4cadf64b8177fba642b054fad4fef99e5f769124989f5844d31fde1bccb7"),
    "PF16_high_downsample": ("79653684e48ad270e5ba921be40d938cc15f1017402da54536fd35ff8f3bf002", "ab2480b2e58e3c575b9cacdbe2d483174898d5eab6024a7d170ceadabcf9d036"),
    "PF32_copy": ("d4bf63076bba553b519d80af8678f0bae141ab2512d2f5ef3139904ef6623807", "d4bf63076bba553b519d80af8678f0bae141ab2512d2f5ef3139904ef6623807"),
    "PF32_fractional": ("fef7add0856a28eab2b61dbf3427ab5f799caa6188d65b27d825398ca45d3b96", "b9767fdbd1733f8281566ca003c19514e1b60072e054cda53923f5b85b0c430e"),
    "PF32_tie_semialpha": ("1c2b046b5ea08eb1aa3ed19b940c3e162ecbfbe5d562ce51b95e3eaa6fe0c0d7", "87de042025825f99d43cd8b7b3441cea78dbc0afcd5410786d7952f2bfc013e6"),
    "PF32_high_downsample": ("ca82e46d2885daaa63de2920207b385573dcc2ede60ec7036bbc5e8bf05c66b0", "162e0f47588045812bdfad5f4a13347d02486fb3c4d6e5ebf4bbff4b97d2755d"),
}
NEGATIVE_ORDER = ["acquire_error", "acquire_success_null", "get_pixel_format_null",
                  "get_input_error", "get_output_error", "release_error",
                  "acquire_throw_pferr", "acquire_bad_alloc", "acquire_throw_other",
                  "release_throw_pferr", "release_bad_alloc", "release_throw_other"]
GATES = {"same_source_active_payload_padding_all_12": True,
         "same_output_active_payload_padding_all_12": True,
         "normalized_headers_equal_all_12": True,
         "authority_specific_lifecycle_exact": True,
         "returns_extra_pixels_flag_equal": True,
         "world_suite_negative_12_exact": True,
         "production_source_frozen": True}
CLAIM = ("Exact 12-cell same-source numerical bridge: actual Windows AEX public Smart entry under "
         "AexLoader/Unicorn and internal f32 radius materialization seam, paired with an isolated "
         "AE-free Mac public EffectMain replay. No AEXCompat, native Windows, installed binary, or "
         "real After Effects host claim.")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def load_strict(path: Path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise RuntimeError(f"duplicate JSON key: {key}")
            out[key] = value
        return out
    return json.loads(path.read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(RuntimeError(value)))

def fresh_inputs() -> tuple[dict, dict]:
    win = subprocess.run([sys.executable, str(AEX_RUNNER)], cwd=ROOT, capture_output=True, text=True)
    if win.returncode: raise RuntimeError(win.stdout + win.stderr)
    with tempfile.TemporaryDirectory(prefix="toon_paired_") as td:
        out = Path(td) / "mac.json"
        mac = subprocess.run([sys.executable, str(MAC_RUNNER), "--output", str(out)],
                             cwd=ROOT, capture_output=True, text=True)
        if mac.returncode: raise RuntimeError(mac.stdout + mac.stderr)
        return json.loads(win.stdout), load_strict(out)

def make_report(win: dict, mac: dict) -> dict:
    if win.get("status") != "PASS_SAME_SOURCE_ACTUAL_AEX_12" or not all(win.get("gates", {}).values()):
        raise RuntimeError("Windows actual-AEX replay not exact")
    if mac.get("status") != "PASS_SAME_SOURCE_MAC_PUBLIC_12" or not all(mac.get("gates", {}).values()):
        raise RuntimeError("Mac public replay not exact")
    wc, mc = win["cases"], mac["cases"]
    if [x.get("id") for x in wc] != ORDER or [x.get("id") for x in mc] != ORDER:
        raise RuntimeError("case order/count drift")
    rows = []
    for a, m in zip(wc, mc):
        cid = a["id"]; family = cid.split("_", 1)[1]; geom, radius, f64, f32, dsx, eff = TUPLES[family]
        if m["id"] != cid: raise RuntimeError("case pairing drift")
        shared = {"geometry": geom, "pixel_size": a["pixel_size"], "rowbytes": a["rowbytes"],
                  "radius_f64_le": f64, "downsample_x": dsx, "downsample_y": [0, 0],
                  "effective_radius": eff, "input_extent": a["input_extent"],
                  "output_extent": a["output_extent"], "origins": [0, 0], "world_flags": [0, 0],
                  "input_active_sha256": a["input_active_sha256"], "input_payload_sha256": a["input_payload_sha256"],
                  "input_padding_sha256": a["input_padding_sha256"], "output_active_sha256": a["output_active_sha256"],
                  "output_payload_sha256": a["output_payload_sha256"], "output_padding_sha256": a["output_padding_sha256"],
                  "input_header_sha256": a["normalized_input_header_sha256"],
                  "output_header_sha256": a["normalized_output_header_sha256"]}
        compare = (a["input_active_sha256"], a["input_payload_sha256"], a["input_padding_sha256"],
                   a["output_active_sha256"], a["output_payload_sha256"], a["output_padding_sha256"],
                   a["normalized_input_header_sha256"], a["normalized_output_header_sha256"])
        observed = (m["input_active_sha256"], m["input_payload_sha256"], m["input_padding_sha256"],
                    m["output_active_sha256"], m["output_payload_sha256"], m["output_padding_sha256"],
                    m["input_header_sha256_before"], m["output_header_sha256_before"])
        if compare != observed or ACTIVE[cid] != (shared["input_active_sha256"], shared["output_active_sha256"]):
            raise RuntimeError(f"same-source mismatch {cid}")
        rows.append({"id": cid, "shared": shared,
                     "windows_actual_aex": {"radius_materialized_f32_le": f32, "raw_exact": a["raw_exact"],
                         "input_storage_unchanged": a["input_storage_unchanged"], "padding_guards_headers_exact": a["padding_exact"] and a["guards_exact"] and a["headers_unchanged"],
                         "preserve_rgb_requested": a["preserve_rgb_requested"], "callbacks": a["callback_counts"]},
                     "mac_public_effectmain": {"radius_f64_le": f64, "raw_exact": m["raw_exact"],
                         "input_storage_unchanged": m["input_storage_immutable"], "padding_guards_headers_exact": m["output_padding_exact"] and m["input_guards_untouched"] and m["output_guards_untouched"] and m["input_header_immutable"] and m["output_header_immutable"],
                         "row0_aligned": m["row0_aligned"], "preserve_rgb_requested": m["preserve_rgb_requested"],
                         "pre_render_output_flags": m["pre_render_output_flags"], "returns_extra_pixels_exact": m["returns_extra_pixels_exact"], "callbacks": m["callbacks"]}})
    negatives = mac["world_suite_negatives"]
    if len(negatives) != 12 or [x.get("id") for x in negatives] != NEGATIVE_ORDER:
        raise RuntimeError("WorldSuite negative order/count drift")
    return {"schema": "olmtoondilate.same-source-public-paired-replay/1",
            "status": "PASS_EXACT12_PAIRED_PUBLIC_OWNER",
            "identities": {"production_source_sha256": sha(SOURCE), "actual_aex_sha256": sha(AEX),
                "actual_aex_runner_sha256": sha(AEX_RUNNER), "mac_runner_sha256": sha(MAC_RUNNER),
                "mac_probe_sha256": sha(MAC_PROBE), "windows_pre_flag_report_sha256": sha(PRE_FLAG_REPORT),
                "generator_sha256": sha(Path(__file__))},
            "matrix": {"depths": [8, 16, 32], "families": list(TUPLES), "case_count": 12,
                "rowbytes": "width*pixel_size+13", "padding_bytes_per_row": 13, "guard_bytes_per_side": 19},
            "paired_cells": rows, "paired_cells_sha256": canonical(rows),
            "smart_pre_relation": {"windows_observed_output_flag_offset": "0x22", "windows_output_flags": 1,
                "mac_output_flags": 1, "returns_extra_pixels_equal": all(r["mac_public_effectmain"]["returns_extra_pixels_exact"] for r in rows),
                "preserve_rgb_requested_windows": False, "preserve_rgb_requested_mac": False},
            "world_suite_negative_rows": negatives, "world_suite_negative_rows_sha256": canonical(negatives),
            "gates": GATES,
            "claim_boundary": CLAIM}

def validate(report: dict) -> None:
    keys = {"schema","status","identities","matrix","paired_cells","paired_cells_sha256","smart_pre_relation","world_suite_negative_rows","world_suite_negative_rows_sha256","gates","claim_boundary"}
    if set(report) != keys or report["schema"] != "olmtoondilate.same-source-public-paired-replay/1" or report["status"] != "PASS_EXACT12_PAIRED_PUBLIC_OWNER": raise RuntimeError("top-level")
    ids = report["identities"]
    expected_ids = {"production_source_sha256": SOURCE_SHA, "actual_aex_sha256": AEX_SHA,
        "actual_aex_runner_sha256": AEX_RUNNER_SHA, "mac_runner_sha256": MAC_RUNNER_SHA,
        "mac_probe_sha256": MAC_PROBE_SHA, "windows_pre_flag_report_sha256": PRE_FLAG_REPORT_SHA,
        "generator_sha256": sha(Path(__file__))}
    if ids != expected_ids: raise RuntimeError("identities")
    if report["matrix"] != {"depths":[8,16,32],"families":list(TUPLES),"case_count":12,"rowbytes":"width*pixel_size+13","padding_bytes_per_row":13,"guard_bytes_per_side":19}: raise RuntimeError("matrix")
    rows = report["paired_cells"]
    if len(rows) != 12 or [r.get("id") for r in rows] != ORDER or canonical(rows) != report["paired_cells_sha256"] or report["paired_cells_sha256"] != PAIRED_ROWS_SHA: raise RuntimeError("paired rows")
    row_keys={"id","shared","windows_actual_aex","mac_public_effectmain"}
    shared_keys={"geometry","pixel_size","rowbytes","radius_f64_le","downsample_x","downsample_y","effective_radius","input_extent","output_extent","origins","world_flags","input_active_sha256","input_payload_sha256","input_padding_sha256","output_active_sha256","output_payload_sha256","output_padding_sha256","input_header_sha256","output_header_sha256"}
    win_keys={"radius_materialized_f32_le","raw_exact","input_storage_unchanged","padding_guards_headers_exact","preserve_rgb_requested","callbacks"}
    mac_keys={"radius_f64_le","raw_exact","input_storage_unchanged","padding_guards_headers_exact","row0_aligned","preserve_rgb_requested","pre_render_output_flags","returns_extra_pixels_exact","callbacks"}
    mac_callbacks={"pre_checkout":1,"checkout_layer_pixels":1,"checkout_output":1,"optional_checkin_layer_pixels":0,"checkout_param":1,"checkin_param":1,"acquire_world_suite":1,"release_world_suite":1,"get_pixel_format":2}
    for row in rows:
        if set(row)!=row_keys or set(row["shared"])!=shared_keys or set(row["windows_actual_aex"])!=win_keys or set(row["mac_public_effectmain"])!=mac_keys: raise RuntimeError("nested keys")
        family=row["id"].split("_",1)[1]; shared=row["shared"]; geom,_,f64,f32,dsx,eff=TUPLES[family]
        if shared["geometry"] != geom or shared["radius_f64_le"] != f64 or shared["downsample_x"] != dsx or shared["effective_radius"] != eff: raise RuntimeError("tuple")
        if ACTIVE[row["id"]] != (shared["input_active_sha256"],shared["output_active_sha256"]): raise RuntimeError("active hashes")
        if row["windows_actual_aex"]["radius_materialized_f32_le"] != f32 or row["mac_public_effectmain"]["radius_f64_le"] != f64: raise RuntimeError("radius bits")
        if not all((row["windows_actual_aex"]["raw_exact"],row["windows_actual_aex"]["input_storage_unchanged"],row["windows_actual_aex"]["padding_guards_headers_exact"],row["mac_public_effectmain"]["raw_exact"],row["mac_public_effectmain"]["input_storage_unchanged"],row["mac_public_effectmain"]["padding_guards_headers_exact"],row["mac_public_effectmain"]["row0_aligned"],row["mac_public_effectmain"]["returns_extra_pixels_exact"])): raise RuntimeError("row gates")
        if row["windows_actual_aex"]["preserve_rgb_requested"] is not False or row["mac_public_effectmain"]["preserve_rgb_requested"] is not False or row["mac_public_effectmain"]["pre_render_output_flags"] != 1: raise RuntimeError("pre relation")
        wc=row["windows_actual_aex"]["callbacks"]
        expected_wc={"smartpre_checkout_layer":1,row["id"]+"_checkout":1,row["id"]+"_output":1,row["id"]+"_checkin":0,"parameter_checkout_seam":1,"PF_COPY":1}
        if wc!=expected_wc or row["mac_public_effectmain"]["callbacks"]!=mac_callbacks: raise RuntimeError("callbacks")
    neg=report["world_suite_negative_rows"]
    if len(neg)!=12 or [r.get("id") for r in neg]!=NEGATIVE_ORDER or canonical(neg)!=report["world_suite_negative_rows_sha256"] or report["world_suite_negative_rows_sha256"]!=NEGATIVE_ROWS_SHA: raise RuntimeError("negatives")
    neg_keys={"id","exact","expected_err","actual_err","input_storage_untouched","output_storage_untouched","input_header_untouched","output_header_untouched","padding_and_guards_untouched","preserve_rgb_false","callbacks","world_suite_identity_exact","pre_render_lifecycle_exact","pre_render_output_flags","returns_extra_pixels_exact"}
    if any(set(r)!=neg_keys for r in neg): raise RuntimeError("negative keys")
    if not all(r.get("exact") is True and r.get("input_storage_untouched") is True and r.get("output_storage_untouched") is True and r.get("input_header_untouched") is True and r.get("output_header_untouched") is True and r.get("padding_and_guards_untouched") is True and r.get("pre_render_output_flags")==1 and r.get("returns_extra_pixels_exact") is True for r in neg): raise RuntimeError("negative gates")
    if report["smart_pre_relation"] != {"windows_observed_output_flag_offset":"0x22","windows_output_flags":1,"mac_output_flags":1,"returns_extra_pixels_equal":True,"preserve_rgb_requested_windows":False,"preserve_rgb_requested_mac":False}: raise RuntimeError("smart pre")
    if report["gates"] != GATES or report["claim_boundary"] != CLAIM: raise RuntimeError("gates/claim")

def markdown(report: dict) -> str:
    return ("# OLMToonDilate same-source public paired replay — 2026-08-13\n\n"
            "Status: **PASS_EXACT12_PAIRED_PUBLIC_OWNER**.\n\n"
            "The exact four fixture families at PF8/PF16/PF32 (12 cells) use identical active, padded payload, extent, origin, flags, rowbytes, and output hashes across the actual Windows AEX public Smart entry and the isolated Mac public `EffectMain`. Windows materializes Radius as f32 at its pinned internal seam; Mac receives the requested f64 value, and both produce the same effective radius and byte-exact output.\n\n"
            "SmartPre requests preserve-RGB=false on both owners. Windows output flag `+0x22` and Mac `PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS` are both 1. The Mac replay also closes 12 WorldSuite error/NULL/exception paths with exact callback counts and complete input/output/header/padding/guard immutability.\n\n"
            "This is not an AEXCompat, native-Windows, installed-binary, or real-After-Effects-host claim. The isolated Debug binary hash is intentionally observational and excluded because transient build paths change it.\n")

def main() -> int:
    parser=argparse.ArgumentParser(); group=parser.add_mutually_exclusive_group(); group.add_argument("--write",action="store_true"); group.add_argument("--validate-only",action="store_true"); args=parser.parse_args()
    if args.validate_only:
        value=load_strict(REPORT);validate(value)
        if DOC.read_text()!=markdown(value): raise RuntimeError("Markdown drift")
        print("PASS_TOONDILATE_PAIRED_VALIDATE");return 0
    win,mac=fresh_inputs();value=make_report(win,mac);validate(value);doc=markdown(value)
    if args.write:
        REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n");DOC.write_text(doc)
    else:
        if load_strict(REPORT)!=value or DOC.read_text()!=doc: raise RuntimeError("checked evidence drift; use --write")
    print("PASS_TOONDILATE_PAIRED_EXACT12");return 0

if __name__ == "__main__": raise SystemExit(main())
