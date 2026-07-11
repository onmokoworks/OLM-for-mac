#!/usr/bin/env python3
"""End-to-end DirectionalBlur gate for the rotate + rowdriver detours."""

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
CORRECT_HOST_AREA_SHA256 = "8b8a28887908f089024bc38f69221148b612adfdcf44afc63d282216a0d7d3ae"


def run(source: Path, report: Path, detour_rowdriver: bool) -> dict:
    command = [
        sys.executable,
        str(FIXTURE),
        "--source",
        str(source),
        "--output",
        str(report),
        "--detour-rotate",
        "--detour-rowdriver" if detour_rowdriver else "--no-detour-rowdriver",
        "--downsample-num",
        "1",
        "--downsample-den",
        "2",
        "--max-instructions",
        "200000000",
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(report.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_fullrender_gate_") as temp_name:
        temp = Path(temp_name)
        source = temp / "source.png"
        Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
        actual = run(source, temp / "actual.json", False)
        detoured = run(source, temp / "detoured.json", True)

    assert actual["status"] == detoured["status"] == "ok"
    assert actual["output"]["complete"] is True
    assert detoured["output"]["complete"] is True
    assert actual["output"]["sha256"] == detoured["output"]["sha256"]
    assert actual["output"]["sha256"] == CORRECT_HOST_AREA_SHA256
    assert actual["exact_case"]["host_argb_sha256"] == detoured["exact_case"]["host_argb_sha256"]
    for report in (actual, detoured):
        assert [call["area_words"] for call in report["execution"]["iterate_calls"]] == [
            [0, 0, 16, 16],
            [0, 0, 16, 16],
        ]
    assert actual["execution"]["rowdriver_detours"] == []
    assert detoured["execution"]["rowdriver_state"]["complete"] is True
    assert len(detoured["execution"]["rowdriver_detours"]) == 26
    assert detoured["execution"]["budget"]["instructions"] < actual["execution"]["budget"]["instructions"]
    print(json.dumps({
        "status": "pass",
        "dimensions": [16, 16],
        "argb_sha256": actual["output"]["sha256"],
        "actual_aex_instructions": actual["execution"]["budget"]["instructions"],
        "detoured_instructions": detoured["execution"]["budget"]["instructions"],
        "rowdriver_detour_calls": len(detoured["execution"]["rowdriver_detours"]),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
