#!/usr/bin/env python3
"""Validate the superseded ToonDilate optional-checkin evidence route.

The old source-included radius-1/candidate lane predates exact public
admission and is no longer regenerated.  This narrow report binds the SDK
contract and delegates current positive/negative owner facts to the final
paired and admission-negative closures. Default execution is read-only;
only --write updates the report and Markdown.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
SDK = resolve_asset(ROOT / "Headers/AE_Effect.h")
PAIRED = ROOT / "refs/conformance/olmtoondilate_same_source_public_paired_replay_20260813.json"
NEGATIVE = ROOT / "refs/conformance/olmtoondilate_public_admission_negative_closure_20260813.json"
REPORT = ROOT / "refs/conformance/olmtoondilate_optional_checkin_closure_20260812.json"
DOC = REPORT.with_suffix(".md")

SOURCE_SHA = "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b"
SDK_SHA = "a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d"
PAIRED_SHA = "80b4e05d844a33687f0d282037fd360898f99a2cf1eca469e68bf8accafee5c2"
NEGATIVE_SHA = "eaacb30d172d5a467b059a5e5fcfa7baacec2ee3c62f885b274d5e9c8f72bb09"
CLAIM = ("Lifecycle-only supersession route. Optional checkin_layer_pixels remains unused on the "
         "exact 12 positive public cells, 12 WorldSuite failure cells, and 576 public admission/"
         "callback negative rows. Numerical and fail-closed authority belongs to the linked "
         "2026-08-13 closures. No installed-binary or After Effects host claim.")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_report() -> dict:
    paired=json.loads(PAIRED.read_text()); negative=json.loads(NEGATIVE.read_text())
    if paired.get("status")!="PASS_EXACT12_PAIRED_PUBLIC_OWNER" or len(paired.get("paired_cells",[]))!=12 or len(paired.get("world_suite_negative_rows",[]))!=12: raise RuntimeError("paired authority drift")
    if any(r["mac_public_effectmain"]["callbacks"]["optional_checkin_layer_pixels"]!=0 for r in paired["paired_cells"]): raise RuntimeError("positive optional checkin")
    if any(r["callbacks"]["optional_checkin_layer_pixels"]!=0 for r in paired["world_suite_negative_rows"]): raise RuntimeError("WorldSuite optional checkin")
    matrix=negative.get("matrix",{})
    if negative.get("status")!="PASS_PUBLIC_ADMISSION_NEGATIVE_CLOSURE" or matrix.get("total_rows_exact")!=576 or matrix.get("optional_checkin_unused_exact") is not True: raise RuntimeError("negative authority drift")
    return {"schema":"olmtoondilate.optional-checkin-closure/2","status":"SUPERSEDED_CURRENT_LIFECYCLE_ROUTE",
        "production":{"source":"mac/OLMToonDilate/OLMToonDilate.cpp","source_sha256":sha(SOURCE),"optional_checkin_call_present":False,"parameter_checkout_checkin_present":True,"returns_extra_pixels_flag_present":True},
        "sdk_contract":{"header":"Headers/AE_Effect.h","header_sha256":sha(SDK),"checkin_layer_pixels_not_strictly_necessary":True},
        "current_authorities":{"paired_report":"refs/conformance/olmtoondilate_same_source_public_paired_replay_20260813.json","paired_report_sha256":sha(PAIRED),"positive_cells":12,"world_suite_negative_cells":12,"positive_optional_checkin_calls_per_cell":0,"world_suite_negative_optional_checkin_calls_per_cell":0,"negative_report":"refs/conformance/olmtoondilate_public_admission_negative_closure_20260813.json","negative_report_sha256":sha(NEGATIVE),"admission_negative_rows":507,"callback_negative_rows":69,"negative_optional_checkin_unused_exact":True},
        "supersedes":{"schema":"olmtoondilate.optional-checkin-closure/1","source_sha256":"70d89711eaa3a630c0cd1820ea12c1976a834fd61ffca29013e2e7e680de90d5","reason":"pre-admission source-included radius-1 and transient candidate claims are replaced by exact-12 paired and canonical negative public-owner closures"},
        "gates":{"source_frozen":sha(SOURCE)==SOURCE_SHA,"sdk_identity_exact":sha(SDK)==SDK_SHA,"paired_identity_exact":sha(PAIRED)==PAIRED_SHA,"negative_identity_exact":sha(NEGATIVE)==NEGATIVE_SHA,"production_optional_checkin_absent":True,"positive_12_optional_checkin_zero":True,"world_suite_negative_12_optional_checkin_zero":True,"public_negative_576_optional_checkin_unused":True},
        "claim_boundary":CLAIM}

def validate(value: dict) -> None:
    if set(value)!={"schema","status","production","sdk_contract","current_authorities","supersedes","gates","claim_boundary"}:raise RuntimeError("fields")
    expected=build_report()
    if value!=expected:raise RuntimeError("report drift")
    if value["production"]["source_sha256"]!=SOURCE_SHA or value["sdk_contract"]["header_sha256"]!=SDK_SHA or value["current_authorities"]["paired_report_sha256"]!=PAIRED_SHA or value["current_authorities"]["negative_report_sha256"]!=NEGATIVE_SHA:raise RuntimeError("identity")
    if not all(value["gates"].values()):raise RuntimeError("gates")

def markdown(value: dict) -> str:
    return ("# OLMToonDilate optional SmartRender checkin closure — superseded 2026-08-13\n\n"
        "Status: **SUPERSEDED_CURRENT_LIFECYCLE_ROUTE**.\n\n"
        "The old source-included radius-1 and transient candidate lane is no longer a numerical authority. Final source `ded9eaab…` keeps the SDK-optional `checkin_layer_pixels` callback unused. The exact-12 paired public report proves zero calls on 12 positive cells and 12 WorldSuite failure cells; the public admission negative closure proves the unused lifecycle across 507 admission and 69 callback rows.\n\n"
        "Numerical equivalence, layouts, output immutability, and fail-closed behavior belong exclusively to those linked 2026-08-13 reports. No install or AE-host claim is made here.\n")

def main() -> int:
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument("--write",action="store_true");g.add_argument("--validate-only",action="store_true");a=p.parse_args()
    value=build_report();validate(value);doc=markdown(value)
    if a.write:
        REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n");DOC.write_text(doc)
    else:
        if json.loads(REPORT.read_text())!=value or DOC.read_text()!=doc:raise RuntimeError("checked evidence drift; use --write")
    print("PASS_TOONDILATE_OPTIONAL_CHECKIN_CURRENT_ROUTE");return 0

if __name__=="__main__":raise SystemExit(main())
