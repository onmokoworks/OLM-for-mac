#!/usr/bin/env python3
"""Render reproducible Mac AE 32bpc EXR candidates for focused request specs.

The resulting index is a Mac candidate record, not a Windows reference result
and not an AE-exact verdict. It exists so a valid Windows EXR return can be
compared immediately without rerendering the Mac side.
"""

from __future__ import annotations

import argparse
import json
import platform
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from materialize_32bpc_mac_request import materialize
from verify_32bpc_float_return import (
    VerificationError,
    canonical_sha256,
    inspect_float_rgba_exr,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPECS = (
    ("refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json", "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"),
    ("refs/reference_requests/olm_bitdepth_32bpc_toondilate_float_20260710.json", "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"),
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("/tmp/olm_ae_32bpc_mac_candidates"))
    parser.add_argument("--output-template", default="OLM EXR 32 Float")
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--request-id", default="", help="Render only one focused request id.")
    parser.add_argument("--dry-run", action="store_true", help="Materialize bridges and write the planned index without starting AE.")
    parser.add_argument("--keep-open", action="store_true", help="Keep AE open after each case instead of quitting it.")
    return parser.parse_args()


def bridge_dir(work_dir: Path, request_id: str, case_id: str) -> Path:
    return work_dir / "bridges" / request_id / case_id


def exr_summary(path: Path) -> dict[str, Any]:
    return inspect_float_rgba_exr(path)


def main() -> int:
    args = parse_args()
    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    candidates_dir = work_dir / "candidates"
    candidates_dir.mkdir(exist_ok=True)
    rows: list[dict[str, Any]] = []

    for spec_rel, source_rel in DEFAULT_SPECS:
        spec_path = ROOT / spec_rel
        source_reference = ROOT / source_rel
        spec = load_json(spec_path)
        request_id = str(spec["request_id"])
        if args.request_id and request_id != args.request_id:
            continue
        for case in spec["cases"]:
            case_id = str(case["id"])
            bridge = bridge_dir(work_dir, request_id, case_id)
            if not bridge.exists():
                materialize(spec_path, source_reference, bridge, case_id)
            output_dir = candidates_dir / request_id / case_id
            row: dict[str, Any] = {
                "request_id": request_id,
                "case_id": case_id,
                "bridge_dir": str(bridge),
                "case": case,
                "bit_depth": "32bpc",
                "bits_per_channel": 32,
                "params_sha256": canonical_sha256(case.get("params_full")),
                "candidate_contract": "mac-float-rgba-exr-v1",
                "state": "planned" if args.dry_run else "pending",
                "readiness": {
                    "bridge_materialized": True,
                    "ae_gui_required": True,
                    "executed": False,
                    "host_platform": platform.system(),
                },
            }
            if not args.dry_run and platform.system() != "Darwin":
                row.update({
                    "state": "not_run_host_platform",
                    "readiness": {
                        **row["readiness"],
                        "reason": "AE GUI candidate execution is a Mac-only no-op on this host",
                    },
                })
            elif not args.dry_run:
                command = [
                    sys.executable,
                    str(ROOT / "scripts/run_ae_single_case.py"),
                    "--request-dir", str(bridge),
                    "--case-id", case_id,
                    "--output-dir", str(output_dir),
                    "--output-mode", "exr_render_queue",
                    "--output-template", args.output_template,
                    "--app-name", args.app_name,
                    "--timeout", str(args.timeout),
                ]
                if args.keep_open:
                    command.append("--keep-open")
                proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                (output_dir / "RUNNER_OUTPUT.txt").parent.mkdir(parents=True, exist_ok=True)
                (output_dir / "RUNNER_OUTPUT.txt").write_text(proc.stdout, encoding="utf-8")
                result_path = output_dir / "AE_SINGLE_CASE_RESULT.json"
                if proc.returncode != 0 or not result_path.is_file():
                    row.update({"state": "error", "runner_exit": proc.returncode, "runner_output": str(output_dir / "RUNNER_OUTPUT.txt")})
                else:
                    result = load_json(result_path)
                    exr_value = result.get("output_exr")
                    exr = Path(exr_value) if isinstance(exr_value, str) else None
                    if result.get("status") != "ok" or exr is None or not exr.is_file():
                        row.update({"state": "error", "result": result, "runner_output": str(output_dir / "RUNNER_OUTPUT.txt")})
                    else:
                        try:
                            summary = exr_summary(exr.resolve())
                        except (OSError, ValueError, struct.error, VerificationError) as exc:
                            row.update({"state": "error", "result": result, "validation_error": str(exc), "runner_output": str(output_dir / "RUNNER_OUTPUT.txt")})
                        else:
                            row.update({
                                "state": "rendered",
                                "result": result,
                                "exr": summary,
                                "readiness": {**row["readiness"], "executed": True, "validated": True},
                            })
            rows.append(row)
            print(f"[{row['state'].upper()}] {request_id} {case_id}")

    index = {
        "kind": "olm_mac_ae_32bpc_candidate_index",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_template": args.output_template,
        "output_mode": "exr_render_queue",
        "host_platform": platform.system(),
        "ae_exact_claim": False,
        "execution": {
            "ae_gui_required": True,
            "status": "not_run" if args.dry_run or platform.system() != "Darwin" else "executed",
            "note": "Mac candidate EXRs only; this index is never an AE exact verdict.",
        },
        "candidates": rows,
    }
    index_path = work_dir / "MAC_32BPC_CANDIDATE_INDEX.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    rendered = sum(row["state"] == "rendered" for row in rows)
    errors = sum(row["state"] == "error" for row in rows)
    readiness_path = work_dir / "MAC_32BPC_READINESS.json"
    readiness_path.write_text(json.dumps({
        "kind": "olm_mac_ae_32bpc_candidate_readiness",
        "status": "ready_for_mac_ae_gui" if any(row["state"] in {"planned", "not_run_host_platform"} for row in rows) else "rendered_and_validated",
        "executed": any(row["readiness"].get("executed") for row in rows),
        "host_platform": platform.system(),
        "candidate_index": str(index_path),
        "note": "AE GUI execution is required for Mac candidates and is not performed by --dry-run or on non-Mac hosts.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] candidate index: {index_path}")
    print(f"[OK] readiness package: {readiness_path}")
    print(f"[SUMMARY] planned={len(rows)} rendered={rendered} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
