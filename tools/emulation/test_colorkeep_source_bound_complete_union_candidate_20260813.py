#!/usr/bin/env python3
"""Bind the source-bounded ColorKeep complete public union to one Universal candidate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import plistlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
PROJECT = ROOT / "mac/ColorKeep/Mac/ColorKeep.xcodeproj/project.pbxproj"
LEGACY_GENERATOR = ROOT / "tools/emulation/test_colorkeep_installed_public_covering_matrix_20260812.py"
LEGACY_REPORT = ROOT / "refs/conformance/colorkeep_installed_public_covering_matrix_20260812.json"
SOURCE_PROBE = ROOT / "tools/emulation/probe_colorkeep_legacy_source_admission_20260813.cpp"
SOURCE_UNIT = ROOT / "tests/test_colorkeep_legacy_source_admission_20260813.py"
COUNT9_GENERATOR = ROOT / "tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py"
COUNT9_REPORT = ROOT / "refs/conformance/colorkeep_nine_color_public_closure_20260813.json"
CANDIDATE = ROOT / "handoffs/colorkeep_source_bound_complete_union_candidate_20260813/Product/ColorKeep.plugin"
BINARY = CANDIDATE / "Contents/MacOS/ColorKeep"
REPORT = ROOT / "refs/conformance/colorkeep_source_bound_complete_union_candidate_20260813.json"
DOC = REPORT.with_suffix(".md")

STATUS = "PASS_COLORKEEP_SOURCE_BOUND_COMPLETE_UNION_CANDIDATE"
SCHEMA = "colorkeep.source-bound-complete-union-candidate/1"
SOURCE_SHA = "d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3"
PROJECT_SHA = "6020880ddb4db0b10e0d437101930e6bc4338834e2df47fa84f48a5294eebf46"
BINARY_SHA = "dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d"
COUNT9_OUTPUT_SHA = "2e68fc7a643641652edb27b6400cbdb2358b10c438893a8c346f8efd1ef7aebe"
LEGACY_ACTIVE = {
    "PF8/count5": "3f768aa03c4045a70d16e7695403a27810cc6fe50c46c350fe3f67931b990b13",
    "PF16/count5": "37d9446d656008362f7bf81324cd7a6ceefb883b668b9d1c4da1264ee432632a",
    "PF32/count5": "fff4c594c4f5c06d8fc8744e189ab8b516fafae63aadd25419636eed9f9de043",
    "PF8/count100": "7e9e8bbb203b8aed460ba6f4461469e49861975c34a3c662d4edea4a29909f8d",
    "PF16/count100": "dd4b822eafa0ae04ef3766f475f0d792b2dd7597dd48a8e3d7d1fe49cc5527c6",
    "PF32/count100": "0768f9ca22351943755bc735356bacaf6b6e6bac9b4dc86deb826b0103dba3df",
}
TOP = {"schema", "status", "claim_boundary", "authorities", "candidate", "legacy_union", "count9_union", "scope"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def inventory() -> list[dict]:
    rows = []
    for path in sorted(p for p in CANDIDATE.rglob("*") if p.is_file()):
        rows.append({"path": str(path.relative_to(CANDIDATE)), "size": path.stat().st_size, "sha256": sha(path)})
    return rows


def candidate_identity() -> dict:
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(CANDIDATE)], check=True, capture_output=True)
    archs = subprocess.check_output(["lipo", "-archs", str(BINARY)], text=True).split()
    if set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"candidate is not Universal: {archs}")
    plist = plistlib.loads((CANDIDATE / "Contents/Info.plist").read_bytes())
    if plist.get("LSMinimumSystemVersion") != "11.0":
        raise RuntimeError("Info.plist deployment target drift")
    slice_info = {}
    for arch in ("arm64", "x86_64"):
        text = subprocess.check_output(["otool", "-arch", arch, "-l", str(BINARY)], text=True)
        if "minos 11.0" not in text:
            raise RuntimeError(f"{arch} deployment target drift")
        exports = subprocess.check_output(["nm", "-arch", arch, "-gjU", str(BINARY)], text=True).split()
        required = ["_EffectMain", "_PluginDataEntryFunction2"]
        if [item for item in exports if item in required] != required:
            raise RuntimeError(f"{arch} export drift")
        slice_info[arch] = {"minos": "11.0", "exports": required}
    return {
        "bundle": str(CANDIDATE.relative_to(ROOT)), "binary_sha256": sha(BINARY),
        "architectures": archs, "info_minimum_system_version": "11.0",
        "slices": slice_info, "codesign": "strict-valid-ad-hoc", "inventory": inventory(),
    }


def legacy_inputs(module) -> dict:
    result = {}
    for count in (5, 100):
        rows8 = module.cases("PF8", count)
        for depth, fmt in (("PF8", "<4B"), ("PF16", "<4H"), ("PF32", "<4f")):
            rows = [(name, module.promote(value, depth), matched) for name, value, matched in rows8]
            result[(depth, count)] = module.input_frame(fmt, rows)
    return result


def check_legacy() -> dict:
    module = load(LEGACY_GENERATOR, "colorkeep_legacy_union")
    inputs = legacy_inputs(module)
    order = [("PF8", 5), ("PF16", 5), ("PF32", 5), ("PF8", 100), ("PF16", 100), ("PF32", 100),
             ("PF8", 5), ("PF16", 5), ("PF8", 100), ("PF16", 100)]
    per_arch = {}
    for arch in ("arm64", "x86_64"):
        blob = module.execute_installed(BINARY, inputs, include_classic=True, arch=arch)
        offset = 0
        observed = []
        for depth, count in order:
            pixel_size = {"PF8": 4, "PF16": 8, "PF32": 16}[depth]
            rowbytes = 11 * pixel_size + 12
            full = blob[offset:offset + rowbytes * 7]
            offset += rowbytes * 7
            if len(full) != rowbytes * 7 or any(full[y * rowbytes + 11 * pixel_size:(y + 1) * rowbytes] != b"\xee" * 12 for y in range(7)):
                raise RuntimeError(f"{arch} legacy framing/padding drift")
            active = b"".join(full[y * rowbytes:y * rowbytes + 11 * pixel_size] for y in range(7))
            digest = hashlib.sha256(active).hexdigest()
            if digest != LEGACY_ACTIVE[f"{depth}/count{count}"]:
                raise RuntimeError(f"{arch} {depth}/count{count} output drift")
            observed.append({"entry": "Smart" if len(observed) < 6 else "Classic", "depth": depth,
                             "count": count, "active_sha256": digest})
        if offset != len(blob):
            raise RuntimeError(f"{arch} legacy output framing drift")
        per_arch[arch] = observed
    return {"paths_per_slice": 10, "source_helper_exact_inputs": 6,
            "source_helper_active_mutation_rejects": 18, "architectures": per_arch}


def check_count9() -> dict:
    current = load(ROOT / "tools/emulation/test_colorkeep_current_installed_count9_20260813.py", "colorkeep_count9_arch")
    base = current.load()
    inputs, outputs, _rows = base.fresh_oracle()
    expected = outputs["PF8"] + outputs["PF16"] + outputs["PF8"] + outputs["PF16"] + outputs["PF32"]
    per_arch = {}
    for arch in ("arm64", "x86_64"):
        observed, negative = current.load_for_arch(arch).probe(BINARY, inputs)
        if observed != expected or hashlib.sha256(observed).hexdigest() != COUNT9_OUTPUT_SHA:
            raise RuntimeError(f"{arch} count9 positive drift")
        if negative != {"rejects": 136, "all_precommit_atomic": True}:
            raise RuntimeError(f"{arch} count9 negative drift")
        per_arch[arch] = {"paths": 5, "padded_output_sha256": COUNT9_OUTPUT_SHA,
                          "rejects": 136, "all_precommit_atomic": True}
    return {"architectures": per_arch}


def authorities() -> dict:
    return {
        "production_source_sha256": sha(SOURCE), "project_sha256": sha(PROJECT),
        "legacy_generator_sha256": sha(LEGACY_GENERATOR), "legacy_report_sha256": sha(LEGACY_REPORT),
        "legacy_source_probe_sha256": sha(SOURCE_PROBE), "legacy_source_unit_sha256": sha(SOURCE_UNIT),
        "count9_generator_sha256": sha(COUNT9_GENERATOR), "count9_report_sha256": sha(COUNT9_REPORT),
    }


def generate() -> dict:
    if sha(SOURCE) != SOURCE_SHA or sha(PROJECT) != PROJECT_SHA or sha(BINARY) != BINARY_SHA:
        raise RuntimeError("frozen production/project/candidate identity drift")
    return {
        "schema": SCHEMA, "status": STATUS,
        "claim_boundary": "AE-free current-workspace evidence for the exact source-bound ColorKeep public union only: legacy 11x7 count5/100 and count9 4x3. No arbitrary source, palette, geometry, native AE, installation, Developer ID, or notarization claim.",
        "authorities": authorities(), "candidate": candidate_identity(),
        "legacy_union": check_legacy(), "count9_union": check_count9(),
        "scope": {"arm64": True, "x86_64_rosetta": True, "installed": False, "after_effects_launched": False},
    }


def validate(report: dict) -> None:
    if set(report) != TOP or report["schema"] != SCHEMA or report["status"] != STATUS:
        raise RuntimeError("report schema/status drift")
    if report["authorities"] != authorities():
        raise RuntimeError("report authority drift")
    if report["candidate"] != candidate_identity() or report["candidate"]["binary_sha256"] != BINARY_SHA:
        raise RuntimeError("candidate identity drift")
    if report["scope"] != {"arm64": True, "x86_64_rosetta": True, "installed": False, "after_effects_launched": False}:
        raise RuntimeError("scope drift")
    legacy = report["legacy_union"]
    if set(legacy) != {"paths_per_slice", "source_helper_exact_inputs", "source_helper_active_mutation_rejects", "architectures"}:
        raise RuntimeError("legacy schema drift")
    if (legacy["paths_per_slice"], legacy["source_helper_exact_inputs"], legacy["source_helper_active_mutation_rejects"]) != (10, 6, 18):
        raise RuntimeError("legacy cardinality drift")
    order = [("PF8", 5), ("PF16", 5), ("PF32", 5), ("PF8", 100), ("PF16", 100), ("PF32", 100),
             ("PF8", 5), ("PF16", 5), ("PF8", 100), ("PF16", 100)]
    expected_rows = [
        {"entry": "Smart" if index < 6 else "Classic", "depth": depth, "count": count,
         "active_sha256": LEGACY_ACTIVE[f"{depth}/count{count}"]}
        for index, (depth, count) in enumerate(order)
    ]
    if set(legacy["architectures"]) != {"arm64", "x86_64"} or any(rows != expected_rows for rows in legacy["architectures"].values()):
        raise RuntimeError("legacy architecture/path drift")
    expected_count9 = {arch: {"paths": 5, "padded_output_sha256": COUNT9_OUTPUT_SHA,
                              "rejects": 136, "all_precommit_atomic": True}
                       for arch in ("arm64", "x86_64")}
    if report["count9_union"] != {"architectures": expected_count9}:
        raise RuntimeError("count9 drift")


def markdown(report: dict) -> str:
    return (
        "# ColorKeep source-bound complete-union candidate — 2026-08-13\n\n"
        f"Status: `{STATUS}`\n\n"
        "The frozen Universal candidate reproduces all ten legacy count5/100 public paths and all five count9 public paths on both arm64 and Rosetta x86_64. The legacy source predicate accepts six exact typed sources and rejects first/middle/last active-byte mutations (18 controls). Count9 retains 136 precommit-atomic rejects per slice. Both slices require macOS 11.0 and export EffectMain/PluginDataEntryFunction2; the bundle has a strict-valid ad-hoc signature.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--live-validate", action="store_true")
    args = parser.parse_args()
    if args.write:
        report = generate()
        validate(report)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(report))
    else:
        report = json.loads(REPORT.read_text())
        validate(report)
        if DOC.read_text() != markdown(report):
            raise RuntimeError("markdown drift")
        if args.live_validate and generate() != report:
            raise RuntimeError("live candidate replay drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
