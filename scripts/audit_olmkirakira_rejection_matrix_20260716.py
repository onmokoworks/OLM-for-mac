#!/usr/bin/env python3
"""Run the local OLMKiraKira binary-evidence rejection matrix.

This is a conformance gate, not a renderer and not a PNG scorer.  It binds
local implementation claims to retained evidence and fails closed when a
diagnostic or incomplete witness is mistaken for a production contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_rejection_matrix_20260716.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_rejection_matrix_20260716.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence(root: Path) -> dict[str, Any]:
    mode3 = load(root / "refs/conformance/olmkirakira_mode3_actual_aex_20260713.json")
    dispatch = load(root / "refs/conformance/olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.json")
    output = load(root / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json")
    sigma = load(root / "refs/conformance/olmkirakira_mode3_sigma_sweep_actual_aex_20260713.json")
    quant = load(root / "refs/conformance/olmkirakira_aggregation_quantization_invariant_20260715.json")
    source_cli = (root / "cli/OLMKiraKira/main.cpp").read_text(encoding="utf-8")
    source_mac = (root / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    gaussian = (root / "core/kirakira_gaussian.h").read_text(encoding="utf-8")
    dispatch_md = (root / "refs/conformance/olmkirakira_mode_dispatch_static_audit_20260710.md").read_text(encoding="utf-8")
    gaussian_audit = (root / "refs/conformance/olmkirakira_mode3_gaussian_actual_aex_dispatch_audit_20260715.md").read_text(encoding="utf-8")
    return locals()


def check(name: str, decision: str, basis: str, *, status: str = "PASS") -> dict[str, str]:
    return {"name": name, "status": status, "decision": decision, "basis": basis}


def build_report(root: Path) -> dict[str, Any]:
    e = evidence(root)
    mode3 = e["mode3"]
    dispatch = e["dispatch"]
    output = e["output"]
    sigma = e["sigma"]
    quant = e["quant"]
    cli = e["source_cli"]
    mac = e["source_mac"]
    gaussian = e["gaussian"]
    static = e["dispatch_md"]
    gaussian_audit = e["gaussian_audit"]

    checks = [
        check(
            "mode-1-dispatch-preserved",
            "retain one-pass dispatch",
            "static audit marks Mode 1 as one boxFilter pass and the retained dispatch smoke passed",
            status="PASS" if "single box-filter call" in static and "blur_mode_passes" in cli and "BlurModePasses" in mac else "FAIL",
        ),
        check(
            "mode-2-dispatch-preserved",
            "retain three-pass dispatch",
            "static audit marks Mode 2 as three boxFilter passes and the retained dispatch smoke passed",
            status="PASS" if "three-pass horizontal box-filter" in static and "blur_mode_passes" in cli else "FAIL",
        ),
        check(
            "mode-3-aex-to-portable-replay",
            "accept only the call contract and keep replay diagnostic",
            "actual-AEX captures CV_32FC1, Size(0,1), and sigma length*0.5; the portable Gaussian exists but is not wired",
            status="PASS" if mode3.get("status") == "captured" and sigma.get("summary", {}).get("sigma_matches_length_times_dat") and "not wired" in gaussian else "FAIL",
        ),
        check(
            "mode-3-live-gaussian-promotion",
            "reject production Gaussian promotion",
            "live coefficient return is absent; retained dispatch audit labels its 63-word output emulation-only",
            status="REJECT" if "not OpenCV-conformant" in gaussian_audit and output.get("status") == "captured" else "FAIL",
        ),
        check(
            "mode-4-implementation",
            "reject inferred recursive/exponential implementation",
            "static dispatch is known, but recurrence ordering and edge/writeback semantics remain unobserved",
            status="REJECT" if "value `4` falls through" in static and "Mode 4" in cli else "FAIL",
        ),
        check(
            "merge-mode-2-compose",
            "reject compose-mode-2 production claim",
            "merge-mode-2 target is statically identified, but its post-aggregation compose behavior is unwitnessed",
            status="REJECT" if "Merge Mode 1/2" in static and "mode-2 output/compose contract remains" in static else "FAIL",
        ),
        check(
            "merge-mode-1-local-compose",
            "retain screen RGB with source-alpha passthrough locally",
            "local invariant report passes its complete witness row",
            status="PASS" if quant.get("status") == "local-invariant-proven" and quant.get("summary", {}).get("passed_count") == 1 else "FAIL",
        ),
        check(
            "final-quantization-scope",
            "retain nearest 8bpc rounding only within the local witness scope",
            "one complete local row passes; three rows are incomplete and no cross-host exactness is claimed",
            status="REJECT" if quant.get("summary", {}).get("incomplete_count") == 3 and "does not claim AE exactness" in " ".join(quant.get("limits", [])) else "FAIL",
        ),
    ]
    failed = [item for item in checks if item["status"] == "FAIL"]
    return {
        "kind": "olmkirakira-rejection-matrix",
        "schema": 1,
        "date": "2026-07-16",
        "status": "pass" if not failed else "fail",
        "scope": "Mac-only KiraKira tools, source, and conformance evidence; no PNG tuning",
        "checks": checks,
        "FACT": [
            "Mode 1 and Mode 2 dispatch are statically grounded and retained by the local dispatch regression.",
            "Actual-AEX Mode 3 evidence grounds CV_32FC1, Size(0,1), and sigmaX=length*0.5.",
            "The portable Gaussian replay is exact against the local Unicorn diagnostic words, not a live-Windows oracle.",
            "The local merge-mode-1 compose and final 8bpc rounding invariant has one complete passing witness row.",
        ],
        "INFERENCE": [
            "No production Mode 3 Gaussian change is justified until a same-run live coefficient/output return is captured.",
            "No Mode 4 recurrence, merge-mode-2 compose, or broad final-quantization rewrite is justified by the current evidence.",
            "The strongest current advance is a fail-closed executable boundary that preserves grounded behavior and rejects unsupported promotions.",
        ],
        "limits": [
            "This matrix does not establish AE exactness or Windows/Mac equality.",
            "It intentionally does not edit the shared conformance ledger or production KiraKira render behavior.",
        ],
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# OLMKiraKira Executable Rejection Matrix",
        "",
        f"Date: {report['date']}",
        f"Status: **{report['status']}**",
        "",
        "## FACT",
        "",
    ]
    lines.extend(f"- {item}" for item in report["FACT"])
    lines += ["", "## Matrix", "", "| Check | Status | Decision | Evidence basis |", "| --- | --- | --- | --- |"]
    lines.extend(f"| `{item['name']}` | **{item['status']}** | {item['decision']} | {item['basis']} |" for item in report["checks"])
    lines += ["", "## INFERENCE", ""]
    lines.extend(f"- {item}" for item in report["INFERENCE"])
    lines += ["", "## LIMIT", ""]
    lines.extend(f"- {item}" for item in report["limits"])
    lines += ["", "## Reproduction", "", "```sh", "python3 scripts/audit_olmkirakira_rejection_matrix_20260716.py", "```", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    report = build_report(ROOT)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "json": str(args.output_json), "md": str(args.output_md)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
