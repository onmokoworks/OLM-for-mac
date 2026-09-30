#!/usr/bin/env python3
"""Replay native-boundary algorithm against the independent 162-cell witness."""
from __future__ import annotations

import json
from pathlib import Path

import probe_olmcolorkey_composition_hypotheses_20261001 as hypotheses
import probe_olmcolorkey_thin_metric_boundaries_20261001 as boundaries

ROOT = boundaries.ROOT
BASELINE = ROOT / "reports/colorkey_thin_metric_boundaries_20261001.json"


def main() -> int:
    report = json.loads(BASELINE.read_text())
    if report["source_sha256"] != hypotheses.sha(boundaries.SOURCE.read_bytes()):
        raise RuntimeError("independent witness source identity drift")
    if report["aex_sha256"] != hypotheses.sha(hypotheses.base.retained.actual_probe.AEX.read_bytes()):
        raise RuntimeError("independent witness AEX identity drift")
    if report["case_count"] != 162 or len(report["cases"]) != 162:
        raise RuntimeError("independent witness cell count drift")
    expected = [(d, a, b, depth) for d in (1, 2, 3) for a, b in boundaries.MODES for depth in boundaries.DEPTHS]
    observed = [(r["type"], r["thin"], r["blur"], r["depth"]) for r in report["cases"]]
    if observed != expected:
        raise RuntimeError("independent witness ordering drift")
    variants = hypotheses.kernel_variants(boundaries.SOURCE.read_text())
    results = []
    for name in ("current", "negative_native_boundary_strict"):
        output = boundaries.compile_core(variants[name])
        offset, rows = 0, []
        for case in report["cases"]:
            size = (13 * hypotheses.base.retained.FORMATS[case["depth"]] + 8) * 11
            raw = output[offset:offset + size]
            offset += size
            if len(raw) != size:
                raise RuntimeError("candidate truncated")
            digest = hypotheses.sha(raw)
            if name == "current" and digest != case["candidate_sha256"]["current"]:
                raise RuntimeError("current baseline replay drift")
            rows.append({"type": case["type"], "thin": case["thin"], "blur": case["blur"],
                         "depth": case["depth"], "exact": digest == case["actual_sha256"],
                         "actual_sha256": case["actual_sha256"], "candidate_sha256": digest})
        if offset != len(output):
            raise RuntimeError("candidate output tail")
        results.append({"variant": name, "exact_count": sum(r["exact"] for r in rows), "cases": rows})
        print(name, results[-1]["exact_count"], "/", len(rows), flush=True)
    output = {"schema": "olmcolorkey.native-thin-boundary-replay/1", "date": "2026-10-01",
              "witness_sha256": hypotheses.sha(BASELINE.read_bytes()), "source_sha256": report["source_sha256"],
              "probe_sha256": hypotheses.sha(Path(__file__).read_bytes()),
              "hypotheses_sha256": hypotheses.sha(Path(hypotheses.__file__).read_bytes()),
              "results": results,
              "scope": "Temporary core source replay against independent 162-cell actual-AEX witness; no production edit or public admission; no new native/host capture"}
    (ROOT / "reports/colorkey_thin_boundary_replay_20261001.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
