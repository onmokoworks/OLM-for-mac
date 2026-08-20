#!/usr/bin/env python3
"""Fail-closed intake for a generic-beta Windows oracle return directory."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_bundle_checksums(root: Path) -> None:
    checksum_path = root / "CHECKSUMS.sha256"
    if not checksum_path.is_file():
        raise SystemExit("request CHECKSUMS.sha256 is missing")
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected, separator, relative = line.partition("  ")
        path = root / relative
        if not separator or not path.is_file() or sha(path) != expected:
            raise SystemExit(f"request checksum mismatch: {relative or line}")

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("return_dir",type=Path);ap.add_argument("--request",type=Path,default=Path(__file__).with_name("campaign-manifest.json"));a=ap.parse_args()
    verify_bundle_checksums(a.request.parent)
    request=json.loads(a.request.read_text(encoding="utf-8-sig"));report_path=a.return_dir/"GENERIC_BETA_WINDOWS_ORACLE_RETURN.json";report=json.loads(report_path.read_text(encoding="utf-8-sig"))
    if report.get("schema_version")!=1 or report.get("request_id")!=request["request_id"] or report.get("status")!="complete": raise SystemExit("invalid or incomplete return")
    worker=report.get("worker")
    if not isinstance(worker,dict) or not isinstance(worker.get("sha256"),str) or len(worker["sha256"])!=64: raise SystemExit("worker hash is missing or invalid")
    expected={row["id"] for row in request["cases"]};rows=report.get("cases",[])
    if {row.get("id") for row in rows}!=expected or len(rows)!=len(expected): raise SystemExit("case identity/cardinality mismatch")
    request_cases={row["id"]:row for row in request["cases"]};inputs={row["id"]:row for row in request["inputs"]}
    for row in rows:
        output=a.return_dir/row["output_file"]
        request_case=request_cases[row["id"]];input_row=inputs[request_case["input"]]
        if row.get("status")!="ok" or row.get("exit_code")!=0 or row.get("render_error")!=0: raise SystemExit(f"failed execution: {row.get('id')}")
        if row.get("input_sha256")!=input_row["sha256"] or not output.is_file() or sha(output)!=row.get("output_sha256"): raise SystemExit(f"invalid output: {row.get('id')}")
    print(json.dumps({"status":"verified","request_id":request["request_id"],"cases":len(rows),"worker_sha256":report["worker"]["sha256"],"return_report_sha256":sha(report_path)},sort_keys=True));return 0
if __name__=="__main__": raise SystemExit(main())
