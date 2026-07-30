#!/usr/bin/env python3
"""Strict full-to-reduced smoke for the OLMSmoother v1 discriminator."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
REDUCED = ROOT / "refs/conformance/olmsmoother_v1_independent_binary_discriminator_20260730.json"
FULL = ROOT / "refs/conformance/olmsmoother_v1_independent_binary_discriminator_full_20260730.json"
FULL_SHA = "3008b8239c48e56c6d0fb0aa707ef7e46df41d311c8f8aa710a79503e2d75735"
HEX64 = re.compile(r"[0-9a-f]{64}")
CASES = {
    "case_0001": "166cafc8aaa2bb2d78ed26a12fe95b6dcf0f6eeeabd7f3a4daaf0ceece500e4c",
    "case_0002": "dd9c1adc8920f6785e5d4449545c29e5f3b60761244dae6d34293b401e0f0c9c",
    "case_0003": "7dc50c17733999bb952a69f65d6dfe60249694dd449fd9a0acb67411ba30570b",
}
V1_SURFACE = [[1, "Use Color Key", 4], [2, "Color Key", 5], [3, "Do Smooth Range", 1]]
V2_SURFACE = [
    [1, "Enable Color Key", 4], [2, "Color Key", 5], [3, "Invert Color Key", 4],
    [4, "Smoothness", 1], [5, "Extra Smooth", 1], [6, "Smooth Range", 1],
    [7, "Smoother Version", 7], [8, "Gamma Correction", 7], [9, "Gamma Value", 10],
    [10, "Number of Gamma Colors", 1], [11, "Gamma Color", 5], [12, "Gamma Color", 5],
    [13, "Gamma Color", 5], [14, "Gamma Color", 5], [15, "Gamma Color", 5],
]
V1_ASSIGNMENTS = [
    "Use Color Key@1=0", "Color Key@2=255,255,255,255", "Do Smooth Range@3=6",
]
V2_ASSIGNMENTS = [
    "Enable Color Key@1=0", "Color Key@2=255,255,255,255", "Invert Color Key@3=0",
    "Smoothness@4=100", "Extra Smooth@5=0", "Smooth Range@6=6",
    "Smoother Version@7=1", "Gamma Correction@8=1", "Gamma Value@9=2.4000000953674316",
    "Number of Gamma Colors@10=1", "Gamma Color@11=255,0,0,0",
    "Gamma Color@12=255,0,0,0", "Gamma Color@13=255,0,0,0",
    "Gamma Color@14=255,0,0,0", "Gamma Color@15=255,0,0,0",
]


def req(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def sha(value: Any, label: str) -> None:
    req(type(value) is str and HEX64.fullmatch(value) is not None, f"{label}: SHA")


def surface(setup: dict[str, Any]) -> list[list[Any]]:
    return [[p.get("slot"), p.get("name"), p.get("param_type")] for p in setup.get("parameters", [])]


def parameter_values(assignments: list[str]) -> list[dict[str, Any]]:
    colors = {2, 11, 12, 13, 14, 15}
    result = []
    for item in assignments:
        selector, encoded = item.split("=", 1)
        name, slot_text = selector.rsplit("@", 1)
        slot = int(slot_text)
        if slot in colors:
            result.append({"name": name, "slot": slot, "color": [int(x) for x in encoded.split(",")]})
        else:
            result.append({"name": name, "slot": slot, "value": float(encoded)})
    return result


def validate(reduced: Any, full: Any, *, verify_disk_hash: bool = False) -> None:
    req(type(reduced) is dict and type(full) is dict, "root types")
    if verify_disk_hash:
        req(hashlib.sha256(FULL.read_bytes()).hexdigest() == FULL_SHA, "full file hash")
    req(reduced.get("schema") == "olm.conformance.olmsmoother-v1-independent-binary-discriminator/1", "reduced schema")
    req(full.get("schema") == "olm.smoother-v1-discriminator/1", "full schema")
    req(full.get("verdict") == "discriminated", "full verdict")
    req(reduced["source_report"] == {
        "path": "refs/conformance/olmsmoother_v1_independent_binary_discriminator_full_20260730.json",
        "sha256": FULL_SHA,
    }, "source report binding")
    execution = reduced["execution"]
    req(execution["scope"] == "AEXCompat local execution only", "execution scope")
    req(execution["observed_build_source_commit"] == "8d2374bba6f618932593589e3a6530682dc6a615", "observed commit")
    req("not cryptographically bound" in execution["commit_binding"], "commit disclaimer")
    identity = full["identity"]
    for value, label in [
        (execution["worker_sha256"], "worker"), (identity["worker_sha256"], "full worker"),
        (identity["v1_aex_sha256"], "v1 AEX"), (identity["v2_aex_sha256"], "v2 AEX"),
    ]:
        sha(value, label)
    req(execution["worker_sha256"] == identity["worker_sha256"], "worker derivation")
    req(reduced["aex_identity"] == {
        "standalone_v1_sha256": identity["v1_aex_sha256"],
        "smoother2_sha256": identity["v2_aex_sha256"],
    }, "AEX derivation")

    for full_name, reduced_name, expected in [
        ("v1", "standalone_v1", V1_SURFACE),
        ("v2_forced_v1", "smoother2_forced_v1", V2_SURFACE),
    ]:
        fs = full["setup"][full_name]
        rs = reduced["setup"][reduced_name]
        req(type(fs["global_setup_error"]) is int and fs["global_setup_error"] == 0, f"{full_name} global setup")
        req(type(fs["params_setup_error"]) is int and fs["params_setup_error"] == 0, f"{full_name} params setup")
        req(surface(fs) == expected, f"{full_name} full surface")
        req(rs == {"global_setup_error": 0, "params_setup_error": 0, "parameter_surface": expected}, f"{full_name} reduced surface")

    req([c["id"] for c in full["cases"]] == list(CASES), "full case set/order")
    req([c["id"] for c in reduced["cases"]] == list(CASES), "reduced case set/order")
    reduced_by_id = {c["id"]: c for c in reduced["cases"]}
    for fc in full["cases"]:
        case_id = fc["id"]
        rc = reduced_by_id[case_id]
        req(fc["input_sha256"] == CASES[case_id] == rc["input_sha256"], f"{case_id} input identity")
        sha(fc["input_sha256"], f"{case_id} input")
        req(fc["size"] == [960, 540], f"{case_id} size")
        for label, assignments in [("v1", V1_ASSIGNMENTS), ("v2_forced_v1", V2_ASSIGNMENTS)]:
            readback = fc["render_readback"][label]
            result = readback["worker_result"]
            req(readback["assignments"] == assignments, f"{case_id} {label} assignments")
            req(result["parameter_values"] == parameter_values(assignments), f"{case_id} {label} parameter readback")
            req(type(result["render_error"]) is int and result["render_error"] == 0, f"{case_id} {label} render")
            req(type(result["guards_intact"]) is bool and result["guards_intact"], f"{case_id} {label} guards")
            req(result["input_png_sha256"] == fc["input_sha256"], f"{case_id} {label} input readback")
            req(result["pixel_format"] == "argb8", f"{case_id} {label} format")
            sha(result["raw_pixel_sha256"], f"{case_id} {label} raw")
            # output_png is deliberately ignored: it is an ephemeral temp path, not identity.
        raw = fc["raw_pf8_argb_sha256"]
        req(raw["v1_sha256"] == fc["render_readback"]["v1"]["worker_result"]["raw_pixel_sha256"], f"{case_id} v1 raw derivation")
        req(raw["v2_forced_v1_sha256"] == fc["render_readback"]["v2_forced_v1"]["worker_result"]["raw_pixel_sha256"], f"{case_id} v2 raw derivation")
        req(rc["raw_pf8_argb"] == {
            "standalone_v1_sha256": raw["v1_sha256"],
            "smoother2_forced_v1_sha256": raw["v2_forced_v1_sha256"],
            "exact": raw["exact"],
        }, f"{case_id} reduced raw")
        req(raw["exact"] is False and raw["v1_sha256"] != raw["v2_forced_v1_sha256"], f"{case_id} raw discrimination")
        for field in ("decoded_worker_png_rgba", "round_premultiplied_export_rgba"):
            req(rc[field] == fc[field], f"{case_id} {field} derivation")
            diff = fc[field]
            req(type(diff["exact"]) is bool and diff["exact"] is False, f"{case_id} {field} non-exact")
            req(type(diff["mismatched_bytes"]) is int and diff["mismatched_bytes"] > 0, f"{case_id} {field} count")
            req(type(diff["max_abs_diff"]) is int and diff["max_abs_diff"] > 0, f"{case_id} {field} max")
    req(reduced["conclusion"]["verdict"] == "discriminated_3_of_3", "reduced verdict")
    req(reduced["conclusion"]["formal_mapping_allowed"] is False, "formal mapping")
    req({"16bpc behavior", "32bpc behavior", "After Effects host equivalence or AE exact"} <= set(reduced["claims_not_made"]), "claim boundary")


def rejected(reduced: dict[str, Any], full: dict[str, Any], target: str, mutate: Callable, label: str) -> None:
    r, f = copy.deepcopy(reduced), copy.deepcopy(full)
    mutate(r if target == "reduced" else f)
    try:
        validate(r, f)
    except (AssertionError, KeyError, TypeError, ValueError, AttributeError):
        return
    raise AssertionError(f"mutation accepted: {label}")


def main() -> int:
    reduced = json.loads(REDUCED.read_text(encoding="utf-8"))
    full = json.loads(FULL.read_text(encoding="utf-8"))
    validate(reduced, full, verify_disk_hash=True)
    mutations = [
        ("reduced", lambda d: d["source_report"].__setitem__("sha256", "0" * 64), "source hash"),
        ("full", lambda d: d.__setitem__("verdict", "equivalent"), "full verdict"),
        ("full", lambda d: d["identity"].__setitem__("worker_sha256", "z" * 64), "worker SHA"),
        ("full", lambda d: d["setup"]["v2_forced_v1"]["parameters"].reverse(), "surface order"),
        ("full", lambda d: d["cases"].pop(), "case removal"),
        ("full", lambda d: d["cases"][0].__setitem__("size", [1, 1]), "size"),
        ("full", lambda d: d["cases"][0]["render_readback"]["v2_forced_v1"]["assignments"].pop(), "15 assignments"),
        ("full", lambda d: d["cases"][0]["render_readback"]["v2_forced_v1"]["worker_result"]["parameter_values"][6].__setitem__("value", 2.0), "slot7 readback"),
        ("full", lambda d: d["cases"][1]["render_readback"]["v1"]["worker_result"].__setitem__("render_error", False), "render type"),
        ("full", lambda d: d["cases"][1]["render_readback"]["v1"]["worker_result"].__setitem__("guards_intact", False), "guards"),
        ("full", lambda d: d["cases"][1]["render_readback"]["v1"]["worker_result"].__setitem__("input_png_sha256", "0" * 64), "input readback"),
        ("full", lambda d: d["cases"][2]["raw_pf8_argb_sha256"].__setitem__("exact", True), "raw exact"),
        ("reduced", lambda d: d["cases"][2]["decoded_worker_png_rgba"].__setitem__("mismatched_bytes", 0), "reduced diff"),
        ("reduced", lambda d: d["conclusion"].__setitem__("formal_mapping_allowed", True), "mapping"),
    ]
    for target, mutation, label in mutations:
        rejected(reduced, full, target, mutation, label)
    print("[OK] full report hash/readbacks derive strict reduced OLMSmoother v1 discriminator; 14 mutations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
