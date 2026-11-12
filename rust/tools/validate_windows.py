"""Fresh, sequential ten-plugin integration campaign using the shared oracle.

Each oracle owns/reaps its harness process trees. Raw results and logs stay in
--out; copy only compact-report.json into versioned evidence after review.
Known nondeterminism is never automatically turned into a pass: use the crate's
diagnostic script on any saved mismatches, retaining the baseline verdicts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RUST = Path(__file__).resolve().parents[1]
ORACLE = RUST / "tools/oracle/olm_oracle.py"
PLUGINS = [
    ("color-keep", "ColorKeep"),
    ("olm-distance-gradation", "DistanceGradation"),
    ("olm-blur", "OLMBlur"),
    ("olm-color-key", "OLMColorKey"),
    ("olm-directional-blur", "OLMDirectionalBlur"),
    ("olm-kirakira", "OLMKiraKira"),
    ("olm-radial-blur", "OLMRadialBlur"),
    ("olm-smoother", "OLMSmoother"),
    ("olm-smoother2", "OLMSmoother2"),
    ("olm-toon-dilate", "OLMToonDilate"),
]


def identity(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--staged", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--reference-dir", type=Path, required=True)
    p.add_argument("--harness", type=Path, required=True)
    p.add_argument("--kira-harness", type=Path, required=True)
    args = p.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    report = {"seed": 20261120, "cases": 12, "jobs": 4, "runner_pid": os.getpid(),
              "downsample": ["1", "1/2", "1/4"],
              "runner": identity(Path(__file__)), "oracle": identity(ORACLE),
              "raw_artifacts": {"path": str(args.out), "local_only": True},
              "plugins": [], "complete": False}
    for crate, name in PLUGINS:
        harness = args.kira_harness if name == "OLMKiraKira" else args.harness
        common = ["--reference", str((args.reference_dir / (name + ".aex")).resolve()),
                  "--candidate", str((args.staged / (name + ".aex")).resolve()),
                  "--harness", str(harness.resolve())]
        worker = harness.resolve().parents[3] / "target/minihost-build/aex_worker.exe"
        row = {"crate": crate, "name": name, "commands": [],
               "worker_file_identity": identity(worker),
               "worker_provenance": "default-path file hash; not observed module mapping"}
        for command in ("inventory", "render"):
            output = args.out / name / command
            script = ORACLE
            options = []
            if command == "render":
                timeout = 300 if name == "DistanceGradation" else 600 if name == "OLMRadialBlur" else 120
                sizes = "5x5,11x7,31x19,97x61" if name == "OLMKiraKira" else "1x1,3x7,11x7,17x9" if name == "OLMRadialBlur" else "1x1,3x7,11x7,31x19,97x61"
                if name in ("OLMKiraKira", "OLMRadialBlur"):
                    script = RUST / "plugins" / crate / "validate.py"
                routes = "classic8,classic16" if name == "OLMSmoother" else "smart8,smart16,smart32"
                options = ["--seed", "20261120", "--cases", "12", "--jobs", "4",
                           "--downsample", "1,1/2,1/4", "--routes", routes,
                           "--timeout", str(timeout), "--sizes", sizes]
            argv = [sys.executable, "-X", "utf8", str(script), command, *common, *options, "--out", str(output)]
            print(name, command, flush=True)
            log = args.out / (name + "-" + command + ".log")
            with log.open("w", encoding="utf-8") as stream:
                with subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT) as child:
                    returncode = child.wait()
                    child_pid = child.pid
            row["commands"].append({"argv": argv, "pid": child_pid, "returncode": returncode, "log": identity(log)})
            summary_path = output / "summary.json"
            if summary_path.exists():
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                row[command] = {k: v for k, v in summary.items() if k not in ("results", "inventories")}
                row[command]["summary_identity"] = identity(summary_path)
                if command == "render":
                    row["nonexact"] = [{k: r.get(k) for k in ("case", "route", "directory", "status")} for r in summary.get("results", []) if r["status"] != "exact"]
                    plans_path = output / "cases.json"
                    plans = json.loads(plans_path.read_text())
                    row["case_plans_identity"] = identity(plans_path)
                    if name in ("OLMDirectionalBlur", "OLMRadialBlur"):
                        slot = 16 if name == "OLMDirectionalBlur" else 25
                        types = [next(a["value"] for a in c["assignments"] if a["slot"] == slot) for c in plans]
                        if 3 in types:
                            raise RuntimeError("Type 3 unexpectedly admitted")
                        row["noise_type_audit"] = {"slot": slot, "admitted_values": types,
                            "rule": "Exclude Type 3. Directional declared popup count is 2; Radial wrapper records skipped plans."}
                    exclusions = output / "exclusions.json"
                    if exclusions.exists():
                        row["exclusions"] = json.loads(exclusions.read_text())
            else:
                row[command] = {"missing_summary": True}
            print(name, command, "exit", returncode, flush=True)
        report["plugins"].append(row)
        (args.out / "compact-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["complete"] = True
    (args.out / "compact-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 1 if any(c["returncode"] for r in report["plugins"] for c in r["commands"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
