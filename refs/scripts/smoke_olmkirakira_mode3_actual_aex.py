#!/usr/bin/env python3
"""Smoke-check the OLMKiraKira Mode 3 actual-AEX probe artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=Path("refs/conformance/olmkirakira_mode3_actual_aex_20260713.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = args.json if args.json.is_absolute() else root / args.json
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema"] == "olmkirakira-mode3-actual-aex-probe/1"
    assert report["entry"]["address"] == "0x181150790"
    assert report["target"]["address"] == "0x181272ec0"
    assert report["input"]["blur_mode"] == 3
    scaffold = report.get("tls_scaffold")
    assert scaffold and scaffold["mode"] == "probe-local-windows-tls-fls"
    assert scaffold["tls_generation_dword"] == -1
    if report["status"] == "captured":
        hits = report["target_capture"]["hits"]
        assert hits, "captured status requires a target hit"
        hit = hits[0]
        assert hit["size"] == [0, 1]
        assert hit["sigma_x_f64"] == report["input"]["length"] * 0.5
        assert hit["input_array"]["flags"] == "0x1010000"
        assert hit["output_array"]["flags"] == "0x2010000"
        for key in ("input_array", "output_array"):
            mat = hit[key]["mat"]
            assert mat["rows"] == report["input"]["height"]
            assert mat["cols"] == report["input"]["width"]
            assert mat["step_bytes"] == report["input"]["width"] * 4
        assert report.get("post_sample") is None
        print("[OK] OLMKiraKira Mode 3 actual-AEX boundary smoke passed")
    elif report["status"] in {"blocked", "completed_without_target_hit", "skip"}:
        print(f"[INFO] Mode 3 actual-AEX probe artifact status={report['status']}; no false conformance claim")
    else:
        raise AssertionError(f"unexpected probe status: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
