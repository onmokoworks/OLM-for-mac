#!/usr/bin/env python3
"""Run and analyze the bounded actual-AEX B150 live/no-op differential."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_radialblur_final_plane_small.py"
ANALYZER = HERE / "analyze_radialblur_case0009_sampler_prepass_writeback.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--input-png", type=Path)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--max-instructions", type=int, default=2_000_000)
    parser.add_argument("--combined-json", type=Path, default=Path("/tmp/olmradialblur_b150_differential.json"))
    parser.add_argument("--output-json", type=Path, default=Path("/tmp/olmradialblur_b150_analysis.json"))
    parser.add_argument("--output-md", type=Path, default=Path("/tmp/olmradialblur_b150_analysis.md"))
    args = parser.parse_args()

    live_path = args.combined_json.with_name(args.combined_json.stem + ".live.json")
    noop_path = args.combined_json.with_name(args.combined_json.stem + ".noop.json")
    common = ["--width", str(args.width), "--height", str(args.height),
              "--max-instructions", str(args.max_instructions)]
    for name, value in (("--aex-path", args.aex_path), ("--manifest", args.manifest),
                        ("--input-png", args.input_png)):
        if value is not None:
            common.extend([name, str(value)])

    live = subprocess.run([sys.executable, str(PROBE), *common, "--output-json", str(live_path)], check=False)
    noop = subprocess.run([sys.executable, str(PROBE), *common, "--detour-prepass", "--output-json", str(noop_path)], check=False)
    if live.returncode != 0 or noop.returncode not in (0, 2):
        print(f"status=blocked probe_exit_live={live.returncode} probe_exit_noop={noop.returncode}")
        return 2
    try:
        document = {
            "kind": "olmradialblur_case0009_b150_live_noop_differential",
            "schema": 1,
            "differential": {
                "live": json.loads(live_path.read_text(encoding="utf-8")),
                "noop": json.loads(noop_path.read_text(encoding="utf-8")),
            },
        }
        args.combined_json.parent.mkdir(parents=True, exist_ok=True)
        args.combined_json.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"status=blocked combined_input_error={exc}")
        return 2

    analyzed = subprocess.run([
        sys.executable, str(ANALYZER), str(args.combined_json),
        "--output-json", str(args.output_json), "--output-md", str(args.output_md),
    ], check=False)
    if analyzed.returncode != 0:
        return 2
    print(f"combined_json={args.combined_json}")
    print(f"analysis_json={args.output_json}")
    print(f"analysis_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
