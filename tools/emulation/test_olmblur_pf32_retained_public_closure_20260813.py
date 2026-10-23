#!/usr/bin/env python3
"""Windows exported-owner census plus Mac real-SDK closure for retained PF32 cells."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];EMU=ROOT/"tools/emulation";sys.path.insert(0,str(EMU))
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as public
SOURCE=ROOT/"mac/OLMBlur/OLMBlur.cpp";PROBE=EMU/"probe_olmblur_pf32_retained_public_admission_20260813.cpp"
NON=EMU/"fixtures/olmblur_worker32_nonlegacy/manifest.json";LEG=EMU/"fixtures/olmblur_worker32_legacy/manifest.json"
REPORT=ROOT/"refs/conformance/olmblur_pf32_retained_public_closure_20260813.json";DOC=REPORT.with_suffix(".md")
EXPECTED={"source":"22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7","probe":"0d4c9e29c50e7656ba46186dd78ac54af6e086c6f2bc9daaa5940028d8a9f690","public_runner":"5043ba89701d5af95018f50df8f712df0e8d2e4348b25d9658f7e54a0f5ffae6","nonlegacy_manifest":"03e9d5386c96c75f6173a438c629c47bfb30bef4ad40369dad3e1e032a03e2f8","legacy_manifest":"53b4f553c3ebc6ad81c4562f251c4624ff55383fcef89c8de4db1e4674227cf5","aex":"f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"}
EXACT={"32bpc_nonlegacy_basic","32bpc_nonlegacy_large_radius_reverse","32bpc_nonlegacy_amount1294_bias1","32bpc_nonlegacy_amount1294_bias2","32bpc_nonlegacy_amount1256_repeat4","32bpc_nonlegacy_amount5_repeat2","32bpc_nonlegacy_amount5_repeat10","32bpc_nonlegacy_case0001_repeat1_large_radius","32bpc_nonlegacy_case0002_repeat2_large_radius_reverse","32bpc_nonlegacy_case0004_repeat4_full24","32bpc_nonlegacy_case0005_repeat2_full24","32bpc_nonlegacy_case0006_repeat10_full24","32bpc_legacy_basic","32bpc_legacy_large_radius_reverse","32bpc_legacy_mixed_alpha_reverse","32bpc_legacy_declared_248_6_red_boundary","32bpc_legacy_declared_5_mixed_alpha","32bpc_legacy_case0007_repeat1_full24","32bpc_legacy_case0003_repeat10_full24"}
MISMATCH={"32bpc_legacy_smoothness37_5_full24":3945}
CLAIM="All twenty retained PF32 same-source cells are raw exact between the Windows exported Smart owner and current Mac public SmartRender. The Legacy Smoothness 37.5 exported owner intentionally consumes the signed integer part of PF_Fixed and therefore differs from the fractional internal-worker oracle; Mac reproduces that public boundary only for the exact admitted cell. Mac controls comprise 40 optional-checkin successes and 60 source one-away rejects."
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def census():
 rows=[]
 for family,path,legacy in (("nonlegacy",NON,0),("legacy",LEG,1)):
  public.FIXTURE=path.parent;public.PADDING[32]=13
  for item in json.loads(path.read_text())["cases"]:
   public.WIDTH=item["width"];public.HEIGHT=item["height"]
   case=dict(item,depth=32,legacy=legacy,amount=item["blur_amount"],source=f"{item['id']}/source_argb_f32.bin",expected=f"{item['id']}/expected_argb_f32.bin",expect_exact=False)
   got=public.run_row(case);rows.append({"id":item["id"],"family":family,"geometry":[item["width"],item["height"]],"rowbytes":item["width"]*16+13,"parameters":{"amount_f64":item["blur_amount"],"smoothness_fixed":round(item["smoothness"]*65536),"repeat":item["repeat"],"bias":item["bias_direction"],"legacy":legacy},"active_source_sha256":item["source_sha256"],"worker_oracle_sha256":item["expected_sha256"],"exported_active_sha256":got["active_sha256"],"mismatched_bytes":got["mismatched_bytes"],"padding_mismatches":got["padding_mismatches"]})
 return rows
def macrun():
 with tempfile.TemporaryDirectory(prefix="olmblur-pf32-") as td:
  exe=Path(td)/"probe";sources=[PROBE,ROOT/"mac/OLMBlur/OLMBlur_Strings.cpp",*[ROOT/"core"/n for n in ("olmblur_helper.cpp","olmblur_fullworker_helper.cpp","olmblur_worker16_nonlegacy.cpp","olmblur_worker16_legacy.cpp","olmblur_worker32_nonlegacy.cpp","olmblur_worker32_legacy.cpp","olmblur_worker8_legacy.cpp","olmblur_worker_orchestration.cpp")],resolve_asset(ROOT/"Util/AEGP_SuiteHandler.cpp"),resolve_asset(ROOT/"Util/MissingSuiteError.cpp")]
  cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1","-Wno-pragma-pack","-Wno-deprecated-declarations",*[x for d in ("Headers","Headers/SP","Util","Resources","core","mac/OLMBlur") for x in ("-I",str(ROOT/d))],*[str(x) for x in sources],"-framework","Cocoa","-o",str(exe)]
  subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True);r=subprocess.run([str(exe)],cwd=ROOT,text=True,capture_output=True)
  if r.returncode or r.stderr:raise RuntimeError(f"probe {r.returncode} {r.stdout} {r.stderr}")
  return r.stdout
def build(rows,stdout):
 lines=stdout.splitlines()
 if len(rows)!=20 or {r["id"] for r in rows}!=EXACT|set(MISMATCH) or len(lines)!=101 or lines[-1]!="pf32_retained_all_exact=1 positive=40 negative=60" or any("exact=0" in x for x in lines):raise RuntimeError("shape")
 for r in rows:
  if r["mismatched_bytes"]!=(0 if r["id"] in EXACT else MISMATCH[r["id"]]) or r["padding_mismatches"]:raise RuntimeError("census")
 ids={"source":{"path":"mac/OLMBlur/OLMBlur.cpp","sha256":EXPECTED["source"]},"probe":{"path":"tools/emulation/probe_olmblur_pf32_retained_public_admission_20260813.cpp","sha256":EXPECTED["probe"]},"public_runner":{"path":"tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py","sha256":EXPECTED["public_runner"]},"nonlegacy_manifest":{"path":"tools/emulation/fixtures/olmblur_worker32_nonlegacy/manifest.json","sha256":EXPECTED["nonlegacy_manifest"]},"legacy_manifest":{"path":"tools/emulation/fixtures/olmblur_worker32_legacy/manifest.json","sha256":EXPECTED["legacy_manifest"]},"actual_aex":{"path":"plugins_2025/OLMBlur.aex","sha256":EXPECTED["aex"]}}
 return {"schema":"olmblur.pf32-retained-public-closure/3","status":"PASS_20_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT","identities":ids,"owner_rows":rows,"owner_rows_sha256":hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"mac_run_lines":lines,"mac_run_sha256":hashlib.sha256(stdout.encode()).hexdigest(),"summary":{"owner_cells":20,"windows_exported_to_mac_raw_exact":20,"internal_worker_oracle_exact":19,"integer_materialization_boundary":1,"mac_positive_controls":40,"mac_negative_controls":60},"claim_boundary":CLAIM,"claims_not_made":["native AE","installed binary","fractional internal-worker equality for Smoothness 37.5","arbitrary PF32 source or tuple"]}
def validate(v):
 if not isinstance(v,dict) or set(v)!={"schema","status","identities","owner_rows","owner_rows_sha256","mac_run_lines","mac_run_sha256","summary","claim_boundary","claims_not_made"}:raise ValueError("schema")
 if v["schema"]!="olmblur.pf32-retained-public-closure/3" or v["status"]!="PASS_20_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT" or v["claim_boundary"]!=CLAIM:raise ValueError("authority")
 if v["summary"]!={"owner_cells":20,"windows_exported_to_mac_raw_exact":20,"internal_worker_oracle_exact":19,"integer_materialization_boundary":1,"mac_positive_controls":40,"mac_negative_controls":60}:raise ValueError("summary")
 try:fresh=build(v["owner_rows"],"\n".join(v["mac_run_lines"])+"\n")
 except (RuntimeError,KeyError,TypeError) as e:raise ValueError("recanonicalization") from e
 if v!=fresh:raise ValueError("recanonicalization")
def main():
 p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");p.add_argument("--validate-only",action="store_true");a=p.parse_args()
 live={"source":sha(SOURCE),"probe":sha(PROBE),"public_runner":sha(EMU/"test_olmblur_exported_effectmain_chain_actual_aex_20260811.py"),"nonlegacy_manifest":sha(NON),"legacy_manifest":sha(LEG),"aex":sha(resolve_asset(ROOT/"plugins_2025/OLMBlur.aex"))}
 if live!=EXPECTED:raise RuntimeError(f"identity drift {live}")
 fresh=build(census(),macrun());validate(fresh)
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLMBlur PF32 retained public closure\n\nStatus: **{fresh['status']}**\n\n{CLAIM}\n");print(fresh["status"]);return 0
 saved=json.loads(REPORT.read_text());validate(saved)
 if saved!=fresh:raise RuntimeError("stored differs")
 print(saved["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
