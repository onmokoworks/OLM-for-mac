#!/usr/bin/env python3
"""Prove the Mac-local cce0 float4 to PF8 writer byte bridge."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "refs/scripts/build_olmsmoother2_cli.sh"
REFERENCE_ROOT = ROOT / "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621"
PARAM_ROOT = ROOT / "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params"


def one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {pattern!r} under {root}, got {matches}")
    return matches[0]


def main() -> int:
    source = one(REFERENCE_ROOT, "*current_olm_cells.png")
    params = one(PARAM_ROOT, "*case_0012_gamma5_red_blue_current_aex*.json")
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_writer_bridge_20260718_") as directory:
        out = Path(directory)
        cli = out / "olmsmoother2_cli"
        subprocess.run(["bash", str(BUILD), str(cli)], cwd=ROOT, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        report_path = out / "writer_frame.json"
        env = os.environ.copy()
        env["OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY"] = "1"
        subprocess.run(
            [str(cli), "--input", str(source), "--params", str(params),
             "--output", str(out / "output.png"), "--writer-frame", "92,841",
             "--writer-frame-json", str(report_path)],
            cwd=ROOT, env=env, check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))

        incomplete = subprocess.run(
            [str(cli), "--input", str(source), "--params", str(params),
             "--output", str(out / "incomplete.png"),
             "--writer-frame-json", str(out / "incomplete.json")],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        assert incomplete.returncode == 2
        assert "must be supplied together" in incomplete.stderr

        missing = subprocess.run(
            [str(cli), "--input", str(source), "--params", str(params),
             "--output", str(out / "missing.png"), "--writer-frame", "99999,99999",
             "--writer-frame-json", str(out / "missing.json")],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        assert missing.returncode == 1
        assert "did not produce" in missing.stderr

    assert report["polygon_count"] == 2
    assert report["cce0_rgba_u32"] == [1062962791, 1062962791, 1062962791, 1064324887]
    assert report["expected_pf8_argb_memory"] == [239, 238, 238, 238]
    assert report["actual_pf8_argb_memory"] == report["expected_pf8_argb_memory"]
    assert report["writer_bytes_equal"] is True
    assert report["invariant"] == "cce0_to_pf8_writer_bytes_equal"
    print("PASS_OLMSMOOTHER2_CCE0_TO_PF8_WRITER_BRIDGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
