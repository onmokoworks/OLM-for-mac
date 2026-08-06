#!/usr/bin/env python3
import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="olmkira-ae-preflight-") as td:
 p=Path(td)/"report.json";r=subprocess.run(["python3",str(ROOT/"scripts/run_olmkirakira_mode4_case01_mac_ae_20260805.py"),"--report","report.json"],cwd=td,capture_output=True,text=True)
 assert r.returncode==0,(r.stdout,r.stderr);x=json.loads(p.read_text());c=x["checks"]
 assert x["run_requested"] is False and x["run_executed"] is False
 assert c["installed_sha_matches"] and c["input_sha_matches"] and c["expected_sha_matches"] and c["manifest_sha_matches"]
 assert c["mode4_value"]==4 and c["software_renderer"] and c["bpc"]==32
 assert x["contract"]["expected_exr_sha256"]=="810b76cde27a6590f0f2913d2e4f7bc2c1649c77b128a7c174d46b0088215c1d"
 print("PASS_OLMKIRAKIRA_MODE4_MAC_AE_RUNNER_PREFLIGHT_20260805")
