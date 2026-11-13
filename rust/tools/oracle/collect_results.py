"""Retain compact, hash-bound campaign evidence without copying plug-in binaries."""
import argparse
import collections
import json
from pathlib import Path

import olm_oracle as o
from self_test import NAMES


def collect(root):
    report = {"schema_version": 1, "campaign_directory": str(root.resolve()), "plugins": {}}
    for name in NAMES:
        directory = root / name
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        inventory = json.loads((root / (name + "-inventory") / "summary.json").read_text(encoding="utf-8"))
        if not summary["complete"]:
            raise ValueError(f"campaign incomplete: {name}")
        failures = collections.Counter()
        witnesses = []
        for row in summary["results"]:
            if row["status"] == "exact":
                continue
            case_dir = directory / row.get("directory", f"case-{row['case']:04d}-{row['route']}")
            witness = {"case": row["case"], "route": row["route"], "status": row["status"],
                       "directory": str(case_dir.relative_to(root)), "comparison": row.get("comparison")}
            for side in ("reference", "candidate"):
                path = case_dir / f"{side}.process.json"
                if not path.exists():
                    continue
                process = json.loads(path.read_text(encoding="utf-8"))
                witness[side + "_log_sha256"] = o.sha256(path)
                if process["timeout"]:
                    reason = "timeout"
                elif process["returncode"]:
                    reason = process["stderr"].splitlines()[0] if process["stderr"] else "exit " + str(process["returncode"])
                    # Retain the short diagnostic heading, not a multi-kilobyte callback trace.
                    reason = reason.split(": diagnostics=")[0].split("diagnostics=")[0][:200]
                else:
                    continue
                failures[side + ": " + reason] += 1
            witnesses.append(witness)
        report["plugins"][name] = {
            "inventory_identical": inventory["identical"],
            "inventory_summary_sha256": o.sha256(root / (name + "-inventory") / "summary.json"),
            "render_summary_sha256": o.sha256(directory / "summary.json"),
            **{key: summary[key] for key in ("tool", "harness", "reference", "candidate", "seed", "cases", "jobs", "sizes", "downsample", "routes", "exit_code")},
            "host": inventory["inventories"]["reference"]["host"],
            "failure_diagnostics": dict(failures), "nonexact_cases": witnesses,
        }
    negative = root / "negative-control" / "summary.json"
    report["negative_control"] = json.loads(negative.read_text(encoding="utf-8"))
    report["negative_control_summary_sha256"] = o.sha256(negative)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("campaign", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    o.write_json(args.out, collect(args.campaign))
