#!/usr/bin/env python3
"""Differentially exercise PF world extents and padded row strides."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"


def run(temp: Path, detour: bool) -> dict:
    source = temp / "source.png"
    Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
    report = temp / ("detoured.json" if detour else "actual.json")
    command = [
        sys.executable, str(FIXTURE), "--source", str(source), "--output", str(report),
        "--downsample-num", "1", "--downsample-den", "2", "--front-strength", "48",
        "--size-variation", "0", "--front-sharp-tail", "0", "--world-area", "2", "1", "14", "15",
        "--row-padding", "12", "--detour-rotate", "--max-instructions", "200000000",
    ]
    command.append("--detour-rowdriver" if detour else "--no-detour-rowdriver")
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(report.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_world_mapping_") as name:
        temp = Path(name)
        actual = run(temp, False)
        detoured = run(temp, True)

    assert actual["status"] == detoured["status"] == "ok"
    assert actual["output"]["complete"] is True
    assert detoured["output"]["complete"] is True
    assert actual["output"]["sha256"] == detoured["output"]["sha256"]
    for report in (actual, detoured):
        calls = report["execution"]["iterate_calls"]
        assert [call["area_words"] for call in calls] == [[2, 1, 14, 15], [2, 1, 14, 15]]
        assert all(call["callback_error"] == 0 for call in calls)
        assert report["execution"]["rowdriver_calls"]
    assert actual["execution"]["rowdriver_detours"] == []
    assert detoured["execution"]["rowdriver_state"]["complete"] is True
    print(json.dumps({
        "status": "pass",
        "world_area": [2, 1, 14, 15],
        "row_padding": 12,
        "actual_output_sha256": actual["output"]["sha256"],
        "detoured_output_sha256": detoured["output"]["sha256"],
        "iterate_areas": [call["area_words"] for call in actual["execution"]["iterate_calls"]],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
