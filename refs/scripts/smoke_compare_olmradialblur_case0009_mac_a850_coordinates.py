#!/usr/bin/env python3
"""Smoke-test the case_0009 Mac/AEX raw-coordinate comparator."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import compare_olmradialblur_case0009_mac_a850_coordinates as compare  # noqa: E402


def run(
    mac_path: Path,
    reference_path: Path,
    out_json: Path,
    out_md: Path,
    requirement: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/compare_olmradialblur_case0009_mac_a850_coordinates.py"),
         "--mac-debug-json", str(mac_path), "--reference-json", str(reference_path),
         "--output-json", str(out_json), "--output-md", str(out_md), requirement],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )


def main() -> int:
    reference = json.loads(compare.DEFAULT_REFERENCE.read_text(encoding="utf-8"))
    assert reference["index_cell_semantic"] is False
    mac_points = []
    for point in reference["points"]:
        expected = compare.expected_from_reference(point)
        production = copy.deepcopy(expected)
        candidate = copy.deepcopy(expected)
        candidate["operation_bits"] = {name: "0x00000000" for name in compare.OPERATION_FIELDS}
        candidate["cell_values_available"] = True
        mac_points.append({
            "kind": "zoom", "x": point["xy"][0], "y": point["xy"][1],
            "coordinate_raw": {"production": production, "aex_f32_candidate": candidate},
        })
    mac_points[0]["coordinate_raw"]["production"]["radius_raw_bits"] = "0x00000000"
    mac = {"kind": "olmradialblur_debug_points", "schema": 1, "points": mac_points}
    with tempfile.TemporaryDirectory(prefix="radialblur_a850_compare_") as tmp:
        tmp_path = Path(tmp)
        mac_path = tmp_path / "mac.json"
        reference_path = tmp_path / "reference.json"
        out_json = tmp_path / "comparison.json"
        out_md = tmp_path / "comparison.md"
        mac_path.write_text(json.dumps(mac), encoding="utf-8")
        reference_path.write_text(json.dumps(reference), encoding="utf-8")

        raw_exact = run(mac_path, reference_path, out_json, out_md, "--require-candidate-raw-exact")
        if raw_exact.returncode != 0:
            raise AssertionError(raw_exact.stdout)
        raw_report = json.loads(out_json.read_text(encoding="utf-8"))
        assert raw_report["raw_a850_classifications"]["aex_f32_candidate"] == "raw-a850-exact"
        assert raw_report["raw_a850_match_counts"]["aex_f32_candidate"] == 32
        blocked_full = run(mac_path, reference_path, out_json, out_md, "--require-candidate-exact")
        assert blocked_full.returncode == 2 and "FAIL-CLOSED" in blocked_full.stdout

        reference["index_cell_semantic"] = True
        reference_path.write_text(json.dumps(reference), encoding="utf-8")
        exact = run(mac_path, reference_path, out_json, out_md, "--require-candidate-exact")
        if exact.returncode != 0:
            raise AssertionError(exact.stdout)
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["classifications"] == {
            "production": "first-difference-found", "aex_f32_candidate": "raw-bit-exact"
        }
        assert report["match_counts"] == {"production": 31, "aex_f32_candidate": 32}
        assert report["first_differences"]["production"]["xy"] == [0, 0]
        assert "AEX-order f32 candidate" in out_md.read_text(encoding="utf-8")

        mac["points"][7]["coordinate_raw"]["aex_f32_candidate"]["cell_rgba_bits"][0][3] = "0x00000000"
        mac_path.write_text(json.dumps(mac), encoding="utf-8")
        mismatch = run(mac_path, reference_path, out_json, out_md, "--require-candidate-exact")
        assert mismatch.returncode == 1
        mismatch_report = json.loads(out_json.read_text(encoding="utf-8"))
        assert mismatch_report["first_differences"]["aex_f32_candidate"]["xy"] == [7, 0]
        assert mismatch_report["first_differences"]["aex_f32_candidate"]["field"] == "cell_rgba_bits"

        mac["points"].pop()
        mac_path.write_text(json.dumps(mac), encoding="utf-8")
        blocked = run(mac_path, reference_path, out_json, out_md, "--require-candidate-exact")
        assert blocked.returncode == 2 and "FAIL-CLOSED" in blocked.stdout
    print("[OK] RadialBlur case_0009 Mac/AEX coordinate comparator smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
