#!/usr/bin/env python3
"""Rebuild the local DG 8bpc typed-boundary request after support fixes."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
OUTPUT = PACKAGE.with_suffix(".zip")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    runner = PACKAGE / "artifacts/run_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.ps1"
    queue = PACKAGE / "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx"
    required = [runner, queue, PACKAGE / "request/request_manifest.json", PACKAGE / "request/reference_manifest.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(", ".join(missing))
    runner_text = runner.read_text(encoding="utf-8")
    queue_text = queue.read_text(encoding="utf-8")
    pre_load = runner_text.split(".logopen", 1)[0]
    if ".logopen" not in runner_text or "bp " in pre_load or "bu " in pre_load:
        raise ValueError("runner does not use the post-load hook-arm sequence")
    if "Get-FileHash" not in runner_text or "OLM_DG_REQUEST_DIR" not in runner_text:
        raise ValueError("runner is missing hash pinning or request-root binding")
    if "OLM_AE_REQUEST_DIR" not in queue_text:
        raise ValueError("queue does not pass the package request root to AE")

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(PACKAGE).as_posix())
    print(f"[OK] rebuilt local package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
