#!/usr/bin/env python3
"""Regression coverage for native OLMKiraKira blur-mode pass dispatch."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cli: Path, source: Path, params: Path, output: Path, *extra: str) -> bytes:
    command = [
        str(cli),
        "--input", str(source),
        "--params", str(params),
        "--output", str(output),
        "--seed-mode", "aex",
        "--gain-scale", "0.62",
        *extra,
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output.read_bytes()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    cli = root / "cli" / "OLMKiraKira" / "olmkirakira_cli"
    source = (
        root / "refs" / "win_references" / "olm_reference_return_windows_20260614" /
        "OLMKiraKira" /
        "kirakira_single_ray_20260606__software__fr24__kk_horizontal_len50_brightness1_strength100_before_effects.png"
    )
    if not source.is_file():
        print(f"missing test input: {source}", file=sys.stderr)
        return 1

    subprocess.run([str(root / "refs" / "scripts" / "build_olmkirakira_cli.sh")], cwd=root, check=True)
    base_values = {
        "glow_rotation": 0,
        "brightness_gain": 9.4,
        "vertical_length": 0,
        "horizontal_length": 50,
        "diagonal_length": 0,
        "diagonal2_length": 0,
        "glow_opacity": 100,
        "channel": 2,
        "strength_multiplier": 100,
        "source_opacity": 100,
    }

    with tempfile.TemporaryDirectory(prefix="olmkirakira_blur_mode_dispatch_") as temp:
        work = Path(temp)
        outputs: dict[str, bytes] = {}
        for mode in (1, 2, 3, 4):
            params = work / f"mode{mode}.json"
            values = {**base_values, "blur_mode": mode}
            params.write_text(
                json.dumps([{"name": name, "value": value} for name, value in values.items()]),
                encoding="utf-8",
            )
            outputs[f"mode{mode}"] = run(cli, source, params, work / f"mode{mode}.png")
            outputs[f"mode{mode}_box1"] = run(cli, source, params, work / f"mode{mode}_box1.png", "--falloff", "box1")
            outputs[f"mode{mode}_box3"] = run(cli, source, params, work / f"mode{mode}_box3.png", "--falloff", "box3")

        checks = {
            "mode1 dispatches to one pass": outputs["mode1"] == outputs["mode1_box1"],
            "mode2 retains three-pass output": outputs["mode2"] == outputs["mode2_box3"],
            "mode1 and mode2 are observably different": outputs["mode1"] != outputs["mode2"],
            "explicit box3 overrides mode1": outputs["mode1_box3"] == outputs["mode2"],
            "explicit box1 overrides mode2": outputs["mode2_box1"] == outputs["mode1"],
            "mode3 preserves current three-pass behavior": outputs["mode3"] == outputs["mode2"],
            "mode4 preserves current three-pass behavior": outputs["mode4"] == outputs["mode2"],
        }
        failed = [name for name, passed in checks.items() if not passed]
        for name, passed in checks.items():
            print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        if failed:
            return 1

    print("[PASS] OLMKiraKira blur-mode dispatch regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
