#!/usr/bin/env python3
"""Same-source exported Smart owner census for retained PF8 OLMBlur cells."""

from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as public

ROOT=Path(__file__).resolve().parents[2]
AEX=ROOT/"plugins_2025/OLMBlur.aex"
RUNNER=ROOT/"tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py"
NONLEGACY=ROOT/"tools/emulation/fixtures/olmblur_worker_orchestration/manifest.json"
LEGACY=ROOT/"tools/emulation/fixtures/olmblur_worker8_legacy/manifest.json"
REPORT=ROOT/"refs/conformance/olmblur_pf8_retained_exported_public_owner_20260813.json"
DOC=ROOT/"refs/conformance/olmblur_pf8_retained_exported_public_owner_20260813.md"
EXPECTED={"aex":"f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b","runner":"5043ba89701d5af95018f50df8f712df0e8d2e4348b25d9658f7e54a0f5ffae6","nonlegacy":"40b3225900bb679e03c1a675c1a3877df2335c5822731ae0fe7bed7edcee9b52","legacy":"144d0f8bfdccc6d8d6aa48344addb4dc9b10b280cbdfd585059c35d9f2bf4fa1"}
EXACT_IDS={"8bpc_nonlegacy_basic","8bpc_nonlegacy_large_radius","8bpc_nonlegacy_case0001_repeat1_large_radius","8bpc_nonlegacy_case0002_repeat2_large_radius_reverse","8bpc_legacy_basic","8bpc_legacy_large_radius_reverse","8bpc_legacy_mixed_alpha_reverse","8bpc_legacy_case0003_radius248_boundary_gradient","8bpc_legacy_case0003_repeat10_large_radius_full12","8bpc_legacy_case0007_repeat1","8bpc_legacy_bias_reverse_radius1_boundary"}
MISMATCH={"8bpc_legacy_smoothness43_75_byte_boundaries":6}
CLAIM="Eleven of twelve retained PF8 same-source cells are raw exact through the Windows exported SmartPre/SmartRender owner with 13 padding bytes per row unchanged. Only the Legacy Smoothness 43.75 cell differs, by exactly 6 active bytes, and remains fail-closed; no correction is inferred."

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def run()->list[dict[str,object]]:
    if {"aex":sha(AEX),"runner":sha(RUNNER),"nonlegacy":sha(NONLEGACY),"legacy":sha(LEGACY)}!=EXPECTED:raise RuntimeError("identity drift")
    rows=[]
    for family,path,legacy in (("nonlegacy",NONLEGACY,0),("legacy",LEGACY,1)):
        manifest=json.loads(path.read_text());public.FIXTURE=path.parent;public.PADDING[8]=13
        for item in manifest["cases"]:
            public.WIDTH=int(item["width"]);public.HEIGHT=int(item["height"])
            case=dict(item,depth=8,legacy=legacy,amount=item["blur_amount"],source=f"{item['id']}/source_argb.bin",expected=f"{item['id']}/expected_argb.bin",expect_exact=False)
            got=public.run_row(case)
            rows.append({"id":got["id"],"family":family,"geometry":[item["width"],item["height"]],"rowbytes":item["width"]*4+13,"parameters":{"amount_f64":item["blur_amount"],"smoothness_fixed":int(round(item["smoothness"]*65536)),"repeat":item["repeat"],"bias":item["bias_direction"],"legacy":legacy},"active_source_sha256":item["source_sha256"],"worker_oracle_sha256":item["expected_sha256"],"exported_active_sha256":got["active_sha256"],"mismatched_bytes":got["mismatched_bytes"],"padding_mismatches":got["padding_mismatches"],"return_codes":got["return_codes"],"parameter_checkout_order":got["parameter_checkout_order"],"callback_events":got["callback_events"]})
    return rows

def build(rows:list[dict[str,object]])->dict[str,object]:
    return {"schema":"olmblur.pf8-retained-exported-public-owner/1","status":"PASS_11_RAW_EXACT_1_PUBLIC_MISMATCH_FAIL_CLOSED","identities":{"actual_aex":{"path":"plugins_2025/OLMBlur.aex","sha256":EXPECTED["aex"]},"runner":{"path":"tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py","sha256":EXPECTED["runner"]},"nonlegacy_manifest":{"path":"tools/emulation/fixtures/olmblur_worker_orchestration/manifest.json","sha256":EXPECTED["nonlegacy"]},"legacy_manifest":{"path":"tools/emulation/fixtures/olmblur_worker8_legacy/manifest.json","sha256":EXPECTED["legacy"]}},"rows":rows,"canonical_rows_sha256":hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"summary":{"case_count":12,"raw_exact":11,"public_mismatch_fail_closed":1,"mismatch_bytes":MISMATCH,"padding_mismatches":0},"claim_boundary":CLAIM,"claims_not_made":["native Windows AE","Mac public admission","current installed binary","correction of mismatched cells","arbitrary source or tuple"]}

def validate(v:object)->None:
    if not isinstance(v,dict) or set(v)!={"schema","status","identities","rows","canonical_rows_sha256","summary","claim_boundary","claims_not_made"}:raise ValueError("top schema")
    if v["schema"]!="olmblur.pf8-retained-exported-public-owner/1" or v["status"]!="PASS_11_RAW_EXACT_1_PUBLIC_MISMATCH_FAIL_CLOSED" or v["claim_boundary"]!=CLAIM:raise ValueError("authority")
    if v["summary"]!={"case_count":12,"raw_exact":11,"public_mismatch_fail_closed":1,"mismatch_bytes":MISMATCH,"padding_mismatches":0}:raise ValueError("summary")
    rows=v["rows"]
    if not isinstance(rows,list) or {r["id"] for r in rows}!=EXACT_IDS|set(MISMATCH):raise ValueError("rows")
    for row in rows:
        expected=0 if row["id"] in EXACT_IDS else MISMATCH[row["id"]]
        if set(row)!={"id","family","geometry","rowbytes","parameters","active_source_sha256","worker_oracle_sha256","exported_active_sha256","mismatched_bytes","padding_mismatches","return_codes","parameter_checkout_order","callback_events"} or row["mismatched_bytes"]!=expected or row["padding_mismatches"]!=0:raise ValueError("row contract")
    if hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=v["canonical_rows_sha256"]:raise ValueError("row digest")
    for key,name in (("aex","actual_aex"),("runner","runner"),("nonlegacy","nonlegacy_manifest"),("legacy","legacy_manifest")):
        if v["identities"][name]["sha256"]!=EXPECTED[key]:raise ValueError("identity")
    if v!=build(rows):raise ValueError("recanonicalization")

def markdown(v:dict[str,object])->str:return f"# OLMBlur PF8 retained exported public owner\n\nStatus: **{v['status']}**\n\n{CLAIM}\n"

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");p.add_argument("--validate-only",action="store_true");a=p.parse_args()
    fresh=build(run());validate(fresh)
    if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");DOC.write_text(markdown(fresh));print(fresh["status"]);return 0
    saved=json.loads(REPORT.read_text());validate(saved)
    if saved!=fresh:raise RuntimeError("stored report differs from fresh replay")
    print(saved["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
