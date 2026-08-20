#!/usr/bin/env python3
"""Run a generic-beta AEX oracle bundle with an explicitly selected worker."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile, time
from pathlib import Path

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def select_cases(manifest: dict, max_pixels: int | None, requested: set[str] | None = None) -> tuple[list[dict], list[str]]:
    inputs={row["id"]:row for row in manifest["inputs"]}
    selected=[];pending=[]
    for case in manifest["cases"]:
        source=inputs[case["input"]]
        if requested is not None and case["id"] not in requested: pending.append(case["id"])
        elif max_pixels is not None and source["width"]*source["height"]>max_pixels: pending.append(case["id"])
        else: selected.append(case)
    return selected,pending
def write_report(path: Path, manifest: dict, worker: Path, plugins: dict, rows: list[dict], pending: list[str]) -> dict:
    successful=all(row["status"]=="ok" for row in rows)
    status=("partial_complete" if pending else "complete") if successful else "failed"
    report={"schema_version":1,"request_id":manifest["request_id"],"status":status,"selection":{"executed_cases":len(rows),"pending_cases":pending},"worker":{"path":str(worker),"sha256":sha(worker)},"aex_sha256":{key:value["aex_sha256"] for key,value in plugins.items()},"cases":rows}
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report
def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--bundle",type=Path,required=True);ap.add_argument("--worker",type=Path,required=True);ap.add_argument("--output-dir",type=Path);ap.add_argument("--timeout",type=int,default=1200);ap.add_argument("--max-pixels",type=int);ap.add_argument("--case",action="append",default=[]);a=ap.parse_args()
    bundle=a.bundle.resolve();worker=a.worker.resolve()
    if not worker.is_file(): raise SystemExit(f"worker not found: {worker}")
    output=(a.output_dir.resolve() if a.output_dir else Path(tempfile.mkdtemp(prefix="olm_generic_beta_oracle_")));output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((bundle/"campaign-manifest.json").read_text());plugins={p["id"]:p for p in manifest["plugins"]};inputs={p["id"]:p for p in manifest["inputs"]}
    for p in plugins.values():
        if sha(bundle/p["aex_file"])!=p["aex_sha256"]: raise SystemExit(f"AEX hash mismatch: {p['id']}")
    requested=set(a.case) if a.case else None
    if requested is not None:
        known={case["id"] for case in manifest["cases"]};missing=requested-known
        if missing: raise SystemExit(f"unknown case IDs: {sorted(missing)}")
    cases,pending=select_cases(manifest,a.max_pixels,requested);rows=[]
    for case in cases:
        plugin=plugins[case["plugin"]];source=inputs[case["input"]];source_path=bundle/source["file"]
        if sha(source_path)!=source["sha256"]: raise SystemExit(f"input hash mismatch: {source['id']}")
        target=output/f"{case['id']}.png";stderr=output/f"{case['id']}.stderr.txt"
        command=[str(worker),"render-png",str(bundle/plugin["aex_file"]),str(source_path),str(target),*case["arguments"]]
        started=time.monotonic()
        try: run=subprocess.run(command,text=True,capture_output=True,timeout=a.timeout)
        except subprocess.TimeoutExpired as error: run=None;stderr.write_text(str(error))
        elapsed=time.monotonic()-started
        payload=None
        if run is not None:
            stderr.write_text(run.stderr)
            try: payload=json.loads(run.stdout)
            except json.JSONDecodeError: pass
        ok=run is not None and run.returncode==0 and payload is not None and payload.get("render_error")==0 and target.is_file()
        rows.append({"id":case["id"],"plugin":case["plugin"],"input":case["input"],"parameters":case["parameter_set"],"status":"ok" if ok else "error","elapsed_seconds":round(elapsed,3),"exit_code":run.returncode if run else None,"render_error":payload.get("render_error") if payload else None,"input_sha256":source["sha256"],"output_sha256":sha(target) if ok else None,"output_file":target.name if ok else None,"stderr_file":stderr.name})
        print(f"[{'OK' if ok else 'ERROR'}] {case['id']}",flush=True)
        write_report(output/"GENERIC_BETA_WINDOWS_ORACLE_RETURN.json",manifest,worker,plugins,rows,pending)
    path=output/"GENERIC_BETA_WINDOWS_ORACLE_RETURN.json";report=write_report(path,manifest,worker,plugins,rows,pending);print(path)
    return 0 if report["status"] in {"complete","partial_complete"} else 2
if __name__=="__main__": raise SystemExit(main())
