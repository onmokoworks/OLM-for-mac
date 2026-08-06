#!/usr/bin/env python3
"""Fail closed on the seven-case PF32 actual-AEX/production matrix."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "refs/conformance/olmblur_pf32_formal_worker_matrix_20260805.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert matrix["coverage"] == {
        "declared_formal_cases": [f"case{number:04d}" for number in range(1, 8)],
        "status": "complete_actual_aex_worker_to_production_exact",
        "fixture_count": 7,
    }
    manifests = {}
    for name, lane in matrix["lanes"].items():
        manifest_path = ROOT / lane["manifest"]
        assert sha256(manifest_path) == lane["manifest_sha256"]
        assert sha256(ROOT / lane["production_source"]) == lane["production_source_sha256"]
        assert sha256(ROOT / lane["replay"]) == lane["replay_sha256"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["binary_sha256"] == matrix["oracle_binary_sha256"]
        manifests[name] = {row["id"]: row for row in manifest["cases"]}
    seen = set()
    for row in matrix["cases"]:
        assert row["case"] not in seen
        seen.add(row["case"])
        lane = "legacy" if row["legacy"] else "nonlegacy"
        fixture = manifests[lane][row["fixture"]]
        assert fixture["formal_case"] == row["case"]
        assert fixture["width"] == fixture["height"] == 24
        assert all(fixture[key] == value for key, value in row["params"].items())
        assert fixture["source_sha256"] == row["source_sha256"]
        assert fixture["expected_sha256"] == row["expected_sha256"]
        directory = ROOT / matrix["lanes"][lane]["manifest"].rsplit("/", 1)[0] / row["fixture"]
        assert sha256(directory / "source_argb_f32.bin") == row["source_sha256"]
        assert sha256(directory / "expected_argb_f32.bin") == row["expected_sha256"]
        assert row["production_replay"] == "exact"
    assert seen == {f"case{number:04d}" for number in range(1, 8)}
    for lane in matrix["lanes"].values():
        subprocess.run([sys.executable, lane["smoke"]], cwd=ROOT, check=True)
    print("[OK] OLMBlur PF32 formal cases 0001..0007 map uniquely to retained actual-AEX fixtures and exact production replays")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
