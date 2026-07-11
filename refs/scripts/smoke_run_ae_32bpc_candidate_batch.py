#!/usr/bin/env python3
"""Smoke-test 32bpc candidate batching without launching After Effects."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_32bpc_candidate_batch_") as tmp:
        work = Path(tmp) / "work"
        proc = subprocess.run(
            ["python3", "scripts/run_ae_32bpc_candidate_batch.py", "--dry-run", "--work-dir", str(work)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        index = json.loads((work / "MAC_32BPC_CANDIDATE_INDEX.json").read_text())
        rows = index["candidates"]
        assert len(rows) == 12
        assert {row["request_id"] for row in rows} == {
            "olm_bitdepth_32bpc_colorkey_float_20260710",
            "olm_bitdepth_32bpc_toondilate_float_20260710",
        }
        assert all(row["state"] == "planned" for row in rows)
        assert all(Path(row["bridge_dir"]).is_dir() for row in rows)
        assert all(row["candidate_contract"] == "mac-float-rgba-exr-v1" for row in rows)
        assert all(row["bit_depth"] == "32bpc" and row["bits_per_channel"] == 32 for row in rows)
        assert all(len(row["params_sha256"]) == 64 for row in rows)
        assert (work / "MAC_32BPC_READINESS.json").is_file()
        readiness = json.loads((work / "MAC_32BPC_READINESS.json").read_text())
        assert readiness["status"] == "ready_for_mac_ae_gui"
        validator = subprocess.run(
            [
                "python3", "scripts/verify_32bpc_float_return.py",
                "--mac-candidate-index", str(work / "MAC_32BPC_CANDIDATE_INDEX.json"),
                "--allow-unrendered", "--json",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        assert '"pending": 12' in validator.stdout
        assert "[SUMMARY] planned=12 rendered=0 errors=0" in proc.stdout
    print("[OK] 32bpc Mac candidate batch smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
