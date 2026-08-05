#!/usr/bin/env python3
"""Audit the completed current-binary OLMColorKey Mac AE host render."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/"refs/reports/olmcolorkey_case0001_pf16_current_binary_host_run_20260805/runner_report.json"
OUT=ROOT/"refs/conformance/olmcolorkey_mac_ae_host_phase_result_20260805.json"
EXPECTED_BINARY="34fd47cd04c6665f75a84ffb0d2bb01390823e50d2224059917043cd45350464"; EXPECTED_OUTPUT="d650ed20952374cdce84872aa57777c2c758884bca9c8d2c7a036a4ee7dec133"
def main():
 r=json.loads(RUN.read_text()); p=subprocess.run(["pgrep","-x","After Effects"],capture_output=True,text=True); current_pids=[int(x) for x in p.stdout.split() if x.isdigit()]; pre=r["checks"]; post=r["post_render_identity"]
 gates={"runner_pass":r["status"]=="pass" and r["ae_exact_claim"] is True,"run_was_explicit_and_executed":r["run_requested"] is True and r["run_executed"] is True,"software_16bpc_contract":r["contract"]["renderer"]=="SOFTWARE" and r["contract"]["bits_per_channel"]==16,"pre_single_pid_60573":pre["ae_pids"]==[60573] and pre["single_ae_process"],"pre_loaded_exact_current_binary":pre["loaded_module_is_sole_exact_current_binary"] and pre["binary_hash"]==EXPECTED_BINARY,"fresh_output_exact":r["fresh_output"]=={"exists":True,"sha256":EXPECTED_OUTPUT},"post_same_pid_mapping_hash":all(post.values()),"osascript_success":r["osascript"]["returncode"]==0}
 result={"status":"pass" if all(gates.values()) else "fail","ae_exact_claim":all(gates.values()),"case":{"id":"olmcolorkey__case_0001","application":"Adobe After Effects 2026","build":"26.3.0.87","renderer":"SOFTWARE","bits_per_channel":16,"readable_parameter_count":219},"identity":{"render_pid":60573,"installed_binary_sha256":EXPECTED_BINARY,"pre_loaded_exact":pre["loaded_module_is_sole_exact_current_binary"],"post_same_pid":post["same_single_ae_pid"],"post_sole_exact_mapping":post["sole_exact_module_mapping"],"post_hash_unchanged":post["installed_binary_hash_unchanged"],"current_ae_pids_after_runner_return":current_pids,"agent_ae_termination_or_restart_performed":False},"output":{"expected_sha256":EXPECTED_OUTPUT,"fresh_sha256":r["fresh_output"]["sha256"],"exact":r["fresh_output"]["sha256"]==EXPECTED_OUTPUT},"runner_report":{"path":str(RUN.relative_to(ROOT)),"sha256":hashlib.sha256(RUN.read_bytes()).hexdigest()},"gates":gates,"claim_boundary":"Current installed OLMColorKey SHA, AE 26.3.0.87 Software/16bpc case0001 only. The runner proved pre/post identity and fresh output equality; no other case is promoted."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps({"status":result["status"],"json":str(OUT)})); return 0 if all(gates.values()) else 1
if __name__=="__main__": raise SystemExit(main())
