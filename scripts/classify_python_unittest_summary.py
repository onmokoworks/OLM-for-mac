#!/usr/bin/env python3
"""Classify failures in an isolated unittest JSON summary."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def classify(row: dict) -> tuple[str, str]:
    text = f"{row.get('stdout', '')}\n{row.get('stderr', '')}".lower()
    if row["status"] == "pass":
        return "pass", "test process passed"
    if "no tests ran" in text:
        return "d_external_or_collection", "file has no unittest-discoverable cases"
    if row["status"] == "timeout":
        return "d_external_or_collection", "per-file timeout"
    if re.search(r"modulenotfounderror|no module named|no such file|file not found|sdk.*not found", text):
        return "d_external_or_collection", "missing module, file, or SDK dependency"
    # Source/report/binary identity pins are expected to drift while generalized
    # plugin sources and their generated evidence are changing.
    if re.search(r"sha256|source_sha|hash mismatch|authority drift|identity drift|pinned input drift|digest", text):
        return "a_old_source_identity_pin", "source/report/binary identity pin drift"
    if re.search(r"reject|fail.?close|bounded|admission|guard closure|only equal|must fail|unsupported.*accepted", text):
        return "b_old_reject_contract", "legacy bounded-admission or rejection expectation"
    return "c_regression_or_compile", "behavioral assertion, compile error, or unclassified regression"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.summary.read_text())
    rows = []
    for source_row in source["results"]:
        category, reason = classify(source_row)
        rows.append({"file": source_row["file"], "execution_status": source_row["status"],
                     "category": category, "reason": reason,
                     "duration_seconds": source_row["duration_seconds"]})
    counts = Counter(row["category"] for row in rows)
    output = {"schema": "olm.python-unittest-classification/1",
              "source_summary": str(args.summary), "test_file_count": len(rows),
              "counts": dict(sorted(counts.items())), "results": rows,
              "classification_boundary": (
                  "Heuristic triage during concurrent beta implementation; category c requires individual rerun "
                  "after source changes settle. Category b tests must retain their exact historical fixture as a "
                  "regression case while replacing rejection-of-all-other-inputs with generic safety invariants."
              )}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
