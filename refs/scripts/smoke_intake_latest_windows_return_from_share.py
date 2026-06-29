#!/usr/bin/env python3
"""Smoke-test intake_latest_windows_return_from_share.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_runtime_trace_return import make_return_zip

def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def write_runtime_request_zip(path: Path, request_id: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "runtime_trace_package_manifest.json",
            (
                "{\n"
                '  "kind": "olm_runtime_trace_request_package",\n'
                '  "runtime_actions": [\n'
                f'    {{"request_id": "{request_id}"}}\n'
                "  ]\n"
                "}\n"
            ),
        )
        archive.writestr("README_RUNTIME_TRACE.md", "synthetic runtime request\n")


def write_runtime_return_zip(path: Path, request_id: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "RETURN_RUNTIME_TRACE_RESULT.json",
            (
                "{\n"
                '  "kind": "olm_runtime_trace_result",\n'
                '  "schema": 1,\n'
                '  "results": [\n'
                "    {\n"
                f'      "request_id": "{request_id}",\n'
                '      "status": "answered",\n'
                '      "summary": "Synthetic bundled runtime witness.",\n'
                '      "observations": {"synthetic_value": 31}\n'
                "    }\n"
                "  ]\n"
                "}\n"
            ),
        )


def write_bundle_return_zip(path: Path, request_zip: Path, return_zip: Path) -> None:
    bundle_stem = path.stem
    request_stem = request_zip.stem
    return_stem = return_zip.stem
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{bundle_stem}/windows_action_bundle_manifest.json",
            '{\n  "kind": "olm_windows_action_bundle",\n  "priority": "priority4-runtime"\n}\n',
        )
        archive.writestr(
            f"{bundle_stem}/README_RETURN_BUNDLE.md",
            "synthetic bundle return\n",
        )
        archive.writestr(
            f"{bundle_stem}/request_package/{request_stem}/windows_action_bundle_manifest.json",
            '{\n  "kind": "olm_windows_action_bundle",\n  "priority": "priority4-runtime"\n}\n',
        )
        archive.write(
            request_zip,
            f"{bundle_stem}/request_package/{request_stem}/runtime_trace/{request_zip.name}",
        )
        archive.write(
            return_zip,
            f"{bundle_stem}/runtime_trace_returns/{return_zip.name}",
        )


def main() -> int:
    root = repo_root()
    helper = root / "scripts" / "intake_latest_windows_return_from_share.py"
    py = sys.executable

    with tempfile.TemporaryDirectory(prefix="olm_share_intake_smoke_") as tmp:
        tmp_root = Path(tmp)
        share_root = tmp_root / "olm_pr"
        new_dir = share_root / "new"
        old_dir = share_root / "old"
        new_dir.mkdir(parents=True)
        old_dir.mkdir(parents=True)

        package = tmp_root / "runtime_request.zip"
        run([py, "scripts/package_runtime_trace_requests.py", "--output", str(package)], root)

        returned = new_dir / "runtime_trace_return.zip"
        make_return_zip(returned)
        (new_dir / "runtime_trace_return__README.txt").write_text("runtime trace return\n", encoding="utf-8")

        summary_json = tmp_root / "runtime_summary.json"
        summary_md = tmp_root / "runtime_summary.md"
        comparisons = tmp_root / "runtime_comparisons"

        dry = run(
            [
                py,
                str(helper),
                "--share-root",
                str(share_root),
                "--dry-run",
            ],
            root,
        )
        if "runtime-trace-return" not in dry.stdout:
            print("[FAIL] dry-run did not choose runtime-trace return")
            return 1

        proc = run(
            [
                py,
                str(helper),
                "--share-root",
                str(share_root),
                "--kind",
                "runtime-trace-return",
                f"--intake-arg=--runtime-package",
                f"--intake-arg={package}",
                "--intake-arg=--runtime-summary-json",
                f"--intake-arg={summary_json}",
                "--intake-arg=--runtime-summary-md",
                f"--intake-arg={summary_md}",
                "--intake-arg=--runtime-comparison-dir",
                f"--intake-arg={comparisons}",
            ],
            root,
        )
        if "[INFO] detected return kind: runtime-trace" not in proc.stdout:
            print("[FAIL] helper did not route to runtime-trace intake")
            return 1
        if "proof_lane_json=" not in proc.stdout or "proof_lane_md=" not in proc.stdout:
            print("[FAIL] helper did not emit runtime proof-lane summary")
            return 1
        if not summary_json.exists() or not summary_md.exists():
            print("[FAIL] helper did not produce runtime trace summaries")
            return 1
        if not (tmp_root / "runtime_summary_proof_lanes.json").exists():
            print("[FAIL] helper did not produce runtime proof-lane JSON")
            return 1
        if not (tmp_root / "runtime_summary_proof_lanes.md").exists():
            print("[FAIL] helper did not produce runtime proof-lane Markdown")
            return 1
        if any(path.is_file() for path in new_dir.iterdir()):
            print("[FAIL] helper did not archive files out of share/new")
            return 1
        archived_names = {path.name for path in old_dir.iterdir() if path.is_file()}
        if not any(name.endswith("runtime_trace_return.zip") for name in archived_names):
            print("[FAIL] helper did not archive the processed zip")
            return 1
        if not any(name.endswith("runtime_trace_return__README.txt") for name in archived_names):
            print("[FAIL] helper did not archive the companion README")
            return 1

        bundle_share_root = tmp_root / "olm_pr_bundle"
        bundle_new = bundle_share_root / "new"
        bundle_old = bundle_share_root / "old"
        bundle_new.mkdir(parents=True)
        bundle_old.mkdir(parents=True)

        request_id = "synthetic_bundle_runtime_trace_20260630"
        request_zip = tmp_root / f"{request_id}.zip"
        write_runtime_request_zip(request_zip, request_id)
        nested_return_zip = tmp_root / f"{request_id}_return_windows.zip"
        write_runtime_return_zip(nested_return_zip, request_id)
        bundle_zip = bundle_new / "olm_windows_action_bundle_synthetic_return_windows.zip"
        write_bundle_return_zip(bundle_zip, request_zip, nested_return_zip)

        bundle_dry = run(
            [
                py,
                str(helper),
                "--share-root",
                str(bundle_share_root),
                "--dry-run",
            ],
            root,
        )
        if "windows-action-bundle-return" not in bundle_dry.stdout:
            print("[FAIL] dry-run did not choose windows-action-bundle-return")
            return 1

        bundle_proc = run(
            [
                py,
                str(helper),
                "--share-root",
                str(bundle_share_root),
                "--kind",
                "windows-action-bundle-return",
            ],
            root,
        )
        if "[OK] processed bundled runtime returns into" not in bundle_proc.stdout:
            print("[FAIL] helper did not process bundled runtime returns")
            return 1
        if "proof_lane_json=" not in bundle_proc.stdout:
            print("[FAIL] helper did not emit proof-lane summary for bundled runtime returns")
            return 1
        bundle_report_dir = (
            root
            / "refs"
            / "reports"
            / "runtime_trace_bundle"
            / "olm_windows_action_bundle_synthetic_return_windows"
        )
        if not any(bundle_report_dir.glob("runtime_trace_summary_*.json")):
            print("[FAIL] helper did not write bundled runtime summary JSON")
            return 1
        if not any(bundle_report_dir.glob("runtime_trace_summary_*_proof_lanes.json")):
            print("[FAIL] helper did not write bundled proof-lane JSON")
            return 1
        if any(path.is_file() for path in bundle_new.iterdir()):
            print("[FAIL] helper did not archive bundle-return files out of share/new")
            return 1

    print("[OK] intake latest Windows return from share smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
