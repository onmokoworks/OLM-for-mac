#!/usr/bin/env python3
"""Run and check the bounded OLMDistanceGradation 8bpc coordinate witness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIRS = {
    "case_0001": ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_olmdistancegradation_basic_exact_20260619",
    "case_0015": ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_olmdistancegradation_basic_exact_20260619",
    "case_0029": ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_olmdistancegradation_blur_exact_20260619",
}
CASES = {
    "case_0001": (17, 0),
    "case_0015": (780, 495),
    "case_0029": (987, 496),
}
FIELD_HEADER = re.compile(r"\bw=(\d+) h=(\d+) pixel_size=(\d+)\b")
FIELD_POINT = re.compile(r"\bpoint x=(-?\d+) y=(-?\d+)\b")
SHADE_POINT = re.compile(r"\bshade x=(-?\d+) y=(-?\d+) pixel_size=(\d+)\b")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract(request_dir: Path, case: str) -> dict:
    request = json.loads((request_dir / "request_manifest.json").read_text(encoding="utf-8"))
    reference = json.loads((request_dir / request["reference_manifest"]).read_text(encoding="utf-8"))
    bits = reference.get("project", {}).get("bits_per_channel")
    if bits is None:
        bits = reference.get("comp", {}).get("bpc")
    if bits != 8:
        raise ValueError(f"request is not 8bpc (bits_per_channel={bits!r})")
    reference_cases = {row.get("id"): row for row in reference.get("cases", [])}
    request_cases = {row.get("id"): row for row in request.get("cases", [])}
    if case not in reference_cases or case not in request_cases:
        raise ValueError(f"request is missing bounded case: {case}")
    filename = reference_cases[case].get("before_effects_frame") or request_cases[case].get("before_effects_frame")
    if not filename or not (request_dir / request["input_dir"] / filename).is_file():
        raise ValueError(f"input fixture is missing for {case}: {filename!r}")
    return {"request": request, "reference": reference, "bits_per_channel": bits}


def paths(root: Path, case: str) -> dict[str, Path]:
    case_root = root / case
    return {
        "root": case_root,
        "field": case_root / "field_debug.txt",
        "shade": case_root / "shade_debug.txt",
        "result": case_root / "AE_SINGLE_CASE_RESULT.json",
    }


def command(request_dir: Path, case: str, output_root: Path, app_name: str) -> list[str]:
    p = paths(output_root, case)
    return [
        sys.executable,
        str(ROOT / "scripts/run_ae_single_case.py"),
        "--request-dir", str(request_dir),
        "--case-id", case,
        "--output-dir", str(p["root"]),
        "--app-name", app_name,
        "--keep-open",
        "--ae-env", f"OLM_AE_FORCE_NEW_PROJECT=1",
        "--ae-env", f"OLM_AE_FORCE_SOFTWARE=1",
        "--ae-env", f"OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1",
        "--ae-env", f"OLM_DG_DEBUG_POINTS={CASES[case][0]},{CASES[case][1]}",
        "--ae-env", f"OLM_DG_DEBUG_DUMP_PATH={p['field']}",
        "--ae-env", f"OLM_DG_SHADE_DEBUG_PATH={p['shade']}",
    ]


def check_case(output_root: Path, case: str) -> dict:
    expected = CASES[case]
    p = paths(output_root, case)
    required = {name: path for name, path in p.items() if name != "root"}
    missing = [str(path) for path in required.values() if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise ValueError(f"{case}: missing or empty artifacts: {', '.join(missing)}")
    result = json.loads(p["result"].read_text(encoding="utf-8-sig"))
    if result.get("status") != "ok":
        raise ValueError(f"{case}: AE status is {result.get('status')!r}: {result.get('error', '')}")
    if result.get("project_bits_per_channel") != 8:
        raise ValueError(f"{case}: AE project depth is {result.get('project_bits_per_channel')!r}, expected 8")
    field_text = p["field"].read_text(encoding="utf-8", errors="replace")
    headers = FIELD_HEADER.findall(field_text)
    if not headers or any(int(pixel_size) != 4 for _, _, pixel_size in headers):
        raise ValueError(f"{case}: field dump has no PF8 header")
    field_hits = [tuple(map(int, hit)) for hit in FIELD_POINT.findall(field_text) if tuple(map(int, hit)) == expected]
    shade_hits = [tuple(map(int, hit[:2])) for hit in SHADE_POINT.findall(p["shade"].read_text(encoding="utf-8", errors="replace")) if int(hit[2]) == 4 and tuple(map(int, hit[:2])) == expected]
    if len(field_hits) != 1:
        raise ValueError(f"{case}: expected one PF8 field witness at {expected}, found {len(field_hits)}")
    if len(shade_hits) != 1:
        raise ValueError(f"{case}: expected one PF8 shade witness at {expected}, found {len(shade_hits)}")
    png = Path(result.get("output_png", ""))
    return {
        "case_id": case,
        "coordinate": list(expected),
        "status": "answered",
        "project_bits_per_channel": result.get("project_bits_per_channel"),
        "field_pf8_hits": len(field_hits),
        "shade_pf8_hits": len(shade_hits),
        "output_png": str(png),
        "output_png_sha256": sha256(png) if png.is_file() else None,
    }


def check_all(output_root: Path) -> dict:
    cases = [check_case(output_root, case) for case in CASES]
    report = {"kind": "olmdg_8bpc_coordinate_witness", "status": "answered", "bounded_cases": cases}
    (output_root / "WITNESS_CHECK.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Validate discovery inputs and print the three AE commands.")
    mode.add_argument("--run", action="store_true", help="Run the three bounded cases through scripts/run_ae_single_case.py.")
    mode.add_argument("--check", action="store_true", help="Check an existing run directory without invoking AE.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    args = parser.parse_args()
    try:
        output_root = (args.output_dir or Path("/tmp") / f"olmdg_8bpc_coordinate_witness_{datetime.now().strftime('%Y%m%d_%H%M%S')}").resolve()
        if args.check:
            print(json.dumps(check_all(output_root), indent=2))
            return 0
        output_root.mkdir(parents=True, exist_ok=True)
        for case in CASES:
            request_dir = REQUEST_DIRS[case].resolve()
            load_contract(request_dir, case)
            argv = command(request_dir, case, output_root, args.app_name)
            print(" ".join(shlex.quote(item) for item in argv))
            if args.run:
                completed = subprocess.run(argv, cwd=ROOT, check=False)
                if completed.returncode:
                    return completed.returncode
        if args.run:
            print(json.dumps(check_all(output_root), indent=2))
        else:
            for case, request_dir in REQUEST_DIRS.items():
                print(f"validated_request_dir[{case}]={request_dir.resolve()}")
            print(f"planned_output_dir={output_root}")
            print("bounded_cases=" + ",".join(f"{case}@{x},{y}" for case, (x, y) in CASES.items()))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
