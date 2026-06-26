#!/usr/bin/env python3
"""Bundle multiple AE pixel validation request zips into one handoff zip."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request-dir",
        type=Path,
        default=None,
        help="Directory containing AE pixel validation request zips. Defaults to latest *_16bpc_mac_ae_validation.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Output bundle zip path.")
    parser.add_argument(
        "--label",
        default=None,
        help="Human label for the bundle. Defaults to the request directory name.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def latest_16bpc_request_dir(root: Path) -> Path:
    candidates = sorted((root / "handoffs" / "ae_host_validation").glob("*_16bpc_mac_ae_validation"))
    if not candidates:
        raise ValueError("no *_16bpc_mac_ae_validation request directory found")
    return candidates[-1]


def request_zips(request_dir: Path) -> list[Path]:
    zips = sorted(path for path in request_dir.glob("*.zip") if zipfile.is_zipfile(path))
    if not zips:
        raise ValueError(f"no request zips found in {request_dir}")
    return zips


def request_summary(zip_path: Path) -> dict:
    summary = {"file": zip_path.name, "request_id": None, "effect_name": None, "case_count": None}
    with zipfile.ZipFile(zip_path) as archive:
        matches = [name for name in archive.namelist() if name.endswith("request_manifest.json")]
        if len(matches) != 1:
            summary["warning"] = f"expected one request_manifest.json, found {len(matches)}"
            return summary
        data = json.loads(archive.read(matches[0]))
    if isinstance(data, dict):
        summary["request_id"] = data.get("request_id")
        summary["effect_name"] = data.get("effect_name")
        cases = data.get("cases")
        if isinstance(cases, list):
            summary["case_count"] = len(cases)
    return summary


def build_readme(label: str, source_dir: Path, summaries: list[dict]) -> str:
    lines = [
        "# OLM AE Pixel Validation Bundle",
        "",
        f"Bundle: `{label}`",
        f"Source request dir: `{source_dir}`",
        "",
        "Run each zip in `requests/` with Mac AE and return the rendered PNGs.",
        "The returned files can be zips or directories; names may include the request stem.",
        "",
        "After returns are collected, verify them from the repo root:",
        "",
        "```sh",
        "python3 scripts/verify_ae_pixel_validation_batch.py \\",
        "  path/to/unzipped_bundle/requests \\",
        "  path/to/mac_ae_returns \\",
        "  --run-dir /tmp/olm_ae_pixel_validation_batch",
        "```",
        "",
        "A pass means the returned Mac AE PNGs match the bundled Windows Software",
        "references under each request's exact thresholds. For exact profiles this",
        "means `max_diff=0`.",
        "",
        "## Requests",
        "",
        "| File | Request id | Effect | Cases |",
        "| --- | --- | --- | ---: |",
    ]
    for summary in summaries:
        lines.append(
            "| {file} | {request_id} | {effect_name} | {case_count} |".format(
                file=summary.get("file") or "-",
                request_id=summary.get("request_id") or "-",
                effect_name=summary.get("effect_name") or "-",
                case_count=summary.get("case_count") if summary.get("case_count") is not None else "-",
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_zip(stage: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(stage))


def main() -> int:
    args = parse_args()
    root = repo_root()
    try:
        request_dir = args.request_dir.resolve() if args.request_dir else latest_16bpc_request_dir(root).resolve()
        zips = request_zips(request_dir)
        label = args.label or request_dir.name
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = (
            args.output.resolve()
            if args.output
            else root
            / "handoffs"
            / "ae_host_validation"
            / f"{stamp}_{label}_bundle"
            / f"olm_ae_pixel_validation_{label}_{stamp}.zip"
        )
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))

    summaries = [request_summary(path) for path in zips]
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_bundle_") as tmp:
        stage = Path(tmp) / label
        requests_dir = stage / "requests"
        requests_dir.mkdir(parents=True)
        for zip_path in zips:
            shutil.copy2(zip_path, requests_dir / zip_path.name)

        manifest = {
            "kind": "olm_ae_pixel_validation_bundle",
            "label": label,
            "source_request_dir": str(request_dir),
            "request_count": len(zips),
            "requests": summaries,
        }
        (stage / "bundle_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (stage / "README.md").write_text(build_readme(label, request_dir, summaries), encoding="utf-8")
        write_zip(stage, output)

    print(f"wrote {output}")
    print(f"- label: {label}")
    print(f"- requests: {len(zips)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
