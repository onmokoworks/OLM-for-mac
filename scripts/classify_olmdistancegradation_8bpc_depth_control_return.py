#!/usr/bin/env python3
"""Fail-closed intake for the DG PF8/PF32 live depth-control return."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_8bpc_current_aex_depth_control_20260713"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
EXPECTED_HITS = {"1170870": "positive", "1170c90": 0}


def load_return(path: Path) -> dict:
    if path.suffix.lower() != ".zip":
        return json.loads(path.read_text(encoding="utf-8-sig"))
    with zipfile.ZipFile(path) as archive:
        names = [
            name for name in archive.namelist()
            if name.replace("\\", "/").rsplit("/", 1)[-1] == "RETURN_RUNTIME_TRACE.json"
        ]
        if len(names) != 1:
            raise ValueError(f"expected one RETURN_RUNTIME_TRACE.json, found {len(names)}")
        return json.loads(archive.read(names[0]).decode("utf-8-sig"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_payload(payload: dict) -> dict:
    require(payload.get("request_id") == REQUEST_ID, "request_id mismatch")
    require(payload.get("status") == "answered", f"return is not answered: {payload.get('status')}")
    require(payload.get("kind") == "depth_control", "return kind mismatch")
    require(payload.get("project_bits_per_channel") == 8, "AE did not report 8bpc")
    require(str(payload.get("aex_sha256", "")).lower() == AEX_SHA256, "current AEX SHA256 mismatch")

    run_id = payload.get("run_id")
    require(isinstance(run_id, str) and bool(run_id.strip()), "run_id is missing")
    require(isinstance(payload.get("ae_pid"), int) and payload["ae_pid"] > 0, "AE PID is missing")
    module_base = payload.get("module_base")
    require(isinstance(module_base, str) and module_base.startswith("0x"), "module base is missing")
    try:
        require(int(module_base, 0) > 0, "module base must be nonzero")
    except ValueError as error:
        raise ValueError("module base is not hexadecimal") from error

    rows = payload.get("rvas")
    require(isinstance(rows, list) and len(rows) == 2, "expected exactly two callback summaries")
    counts: dict[str, int] = {}
    for row in rows:
        require(isinstance(row, dict), "callback summary is not an object")
        rva = str(row.get("rva", "")).lower().removeprefix("0x")
        hit_count = row.get("hit_count")
        require(rva in EXPECTED_HITS and rva not in counts, f"unexpected or duplicate RVA: {rva}")
        require(isinstance(hit_count, int) and hit_count >= 0, f"invalid hit count for {rva}")
        counts[rva] = hit_count
    require(set(counts) == set(EXPECTED_HITS), "callback RVA set mismatch")
    require(counts["1170870"] > 0, "PF8 callback did not execute")
    require(counts["1170c90"] == 0, "PF32 callback executed during the claimed 8bpc run")
    return {
        "request_id": REQUEST_ID,
        "classification": "pf8_live_pf32_negative_control_exact",
        "evidence_gate": "8bpc-hash-pinned-current-aex-same-run-callback-control",
        "run_id": run_id,
        "ae_pid": payload["ae_pid"],
        "module_base": module_base,
        "aex_sha256": AEX_SHA256,
        "project_bits_per_channel": 8,
        "hit_counts": counts,
        "claim_limit": "callback depth dispatch only; no pixel or algorithm proof",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    result = validate_payload(load_return(args.return_path))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
