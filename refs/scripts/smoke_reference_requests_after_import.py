#!/usr/bin/env python3
"""Run post-import checks for Windows reference requests.

The script is intentionally safe to run before Windows refs are returned: pending
requests are reported as SKIP and exit 0. Once a request is covered, its manifest
is verified and any request-specific follow-up smoke registered below is run.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from check_reference_request_status import load_status_rows


FOLLOW_UP_SMOKES = {
    "directionalblur_context_scale_20260606": [
        [
            "refs/scripts/smoke_reference_request_cli_probe.py",
            "--request-id",
            "directionalblur_context_scale_20260606",
            "--expected-effect",
            "OLM DirectionalBlur",
            "--build-script",
            "refs/scripts/build_olmdirectionalblur_cli.sh",
            "--command",
            '"cli/OLMDirectionalBlur/olmdirectionalblur_cli" --input "{input}" --params "{params}" --output "{output}" --algorithm rotated-aex-full-choreo --angle-sign -1 --sample-sign 1 --strength-scale auto',
        ],
    ],
    "kirakira_single_ray_20260606": [
        [
            "refs/scripts/smoke_reference_request_cli_probe.py",
            "--request-id",
            "kirakira_single_ray_20260606",
            "--expected-effect",
            "OLM Kira Kira",
            "--build-script",
            "refs/scripts/build_olmkirakira_cli.sh",
            "--command",
            '"cli/OLMKiraKira/olmkirakira_cli" --input "{input}" --params "{params}" --output "{output}" --seed-mode aex --falloff box3 --gain-scale 0.72 --ray-mode axis-rotate --compose-mode aex-premul --filter-border mirror --auto-length-scale --comp-width 1920',
        ],
    ],
    "olmcolorkey_replace_colorspace_20260606": [
        ["refs/scripts/smoke_olmcolorkey_replace_colorspace_request_cli.py"],
    ],
    "radialblur_inner_20260605": [
        [
            "refs/scripts/smoke_reference_request_cli_probe.py",
            "--request-id",
            "radialblur_inner_20260605",
            "--expected-effect",
            "OLM RadialBlur",
            "--build-script",
            "refs/scripts/build_olmradialblur_cli.sh",
            "--command",
            '"cli/OLMRadialBlur/olmradialblur_cli" --input "{input}" --params "{params}" --output "{output}" --inner-source-scatter-prepass',
        ],
    ],
    "radialblur_inner_size_variation_20260606": [
        [
            "refs/scripts/smoke_reference_request_cli_probe.py",
            "--request-id",
            "radialblur_inner_size_variation_20260606",
            "--expected-effect",
            "OLM RadialBlur",
            "--build-script",
            "refs/scripts/build_olmradialblur_cli.sh",
            "--command",
            '"cli/OLMRadialBlur/olmradialblur_cli" --input "{input}" --params "{params}" --output "{output}" --inner-source-scatter-prepass --ignore-size-variation',
        ],
    ],
    "smoother2_no_key_grid_20260606": [
        ["refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py"],
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request",
        action="append",
        default=[],
        help="Run only this request_id. May be repeated.",
    )
    parser.add_argument(
        "--require-optional-render-sets",
        action="store_true",
        help="Fail if optional render sets such as CUDA are absent.",
    )
    parser.add_argument(
        "--requests-dir",
        type=Path,
        default=None,
        help="Directory containing request JSON files. Defaults to refs/reference_requests.",
    )
    parser.add_argument(
        "--references-dir",
        type=Path,
        default=None,
        help="Directory containing imported reference manifests. Defaults to refs/win_references.",
    )
    return parser.parse_args()


def run(cmd: list[str], root: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=root).returncode


def verify_request(
    root: Path,
    requests_dir: Path,
    request_id: str,
    manifest: str,
    require_optional: bool,
) -> int:
    request_path = requests_dir / f"{request_id}.json"
    manifest_path = Path(manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    cmd = [
        sys.executable,
        "refs/scripts/verify_reference_request_result.py",
    ]
    if not require_optional:
        cmd.append("--allow-missing-optional-render-sets")
    cmd.extend([str(request_path), str(manifest_path)])
    return run(cmd, root)


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    requests_dir = (args.requests_dir or root / "refs" / "reference_requests").resolve()
    references_dir = (args.references_dir or root / "refs" / "win_references").resolve()
    wanted = set(args.request)
    rows = load_status_rows(requests_dir, references_dir)
    if wanted:
        known = {str(row.get("request_id")) for row in rows}
        unknown = sorted(wanted - known)
        if unknown:
            print(f"[FAIL] unknown request_id(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        rows = [row for row in rows if row.get("request_id") in wanted]

    failures = 0
    for row in rows:
        request_id = str(row["request_id"])
        status = row.get("status")
        best = row.get("best") or {}
        if status == "pending":
            print(f"[SKIP] {request_id}: pending")
            continue
        if status == "partial":
            print(f"[FAIL] {request_id}: partial coverage: {best}", file=sys.stderr)
            failures += 1
            continue
        if status != "covered":
            print(f"[FAIL] {request_id}: unknown status {status!r}", file=sys.stderr)
            failures += 1
            continue

        manifest = best.get("manifest")
        if not isinstance(manifest, str) or not manifest:
            print(f"[FAIL] {request_id}: covered but no manifest path", file=sys.stderr)
            failures += 1
            continue

        print(f"[COVERED] {request_id}: {manifest}")
        if verify_request(root, requests_dir, request_id, manifest, args.require_optional_render_sets) != 0:
            failures += 1
            continue

        follow_ups = FOLLOW_UP_SMOKES.get(request_id, [])
        if not follow_ups:
            print(f"[INFO] {request_id}: no registered request-specific smoke; manifest verification only")
            continue
        for follow_up in follow_ups:
            if run([sys.executable, *follow_up], root) != 0:
                failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
