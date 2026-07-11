#!/usr/bin/env python3
"""Smoke-test summarize_win_reference_return.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from smoke_olm_return_intake import make_windows_ref_return


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    intake = repo / "scripts" / "intake_olm_return.py"
    summary = repo / "scripts" / "summarize_win_reference_return.py"
    with tempfile.TemporaryDirectory(prefix="olm_smoke_win_ref_summary_") as tmp:
        tmp_path = Path(tmp)
        return_zip, requests_dir, request_path = make_windows_ref_return(tmp_path)
        dest_root = tmp_path / "win_references"
        next_actions = tmp_path / "next_actions.json"
        intake_proc = subprocess.run(
            [
                sys.executable,
                str(intake),
                str(return_zip),
                "--dest-root",
                str(dest_root),
                "--requests-dir",
                str(requests_dir),
                "--request",
                str(request_path),
                "--set-id",
                "synthetic_return",
                "--next-actions-json",
                str(next_actions),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(intake_proc.stdout, end="" if intake_proc.stdout.endswith("\n") else "\n")
        if intake_proc.returncode != 0:
            return intake_proc.returncode
        out_json = tmp_path / "summary.json"
        out_md = tmp_path / "summary.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(summary),
                str(return_zip),
                "--imported-set-dir",
                str(dest_root / "synthetic_return"),
                "--next-actions-json",
                str(next_actions),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        if report["source_summary"]["manifest_count"] != 1:
            print("[FAIL] expected one source manifest", file=sys.stderr)
            return 1
        if report["next_action"].get("request_id") != "synthetic_intake_20260606":
            print("[FAIL] expected next action request id", file=sys.stderr)
            return 1
        if report["source_summary"]["float_preserving_present"]:
            print("[FAIL] synthetic PNG-only return should not be float-preserving", file=sys.stderr)
            return 1
        if report["reference_quality"] != "unclassified":
            print("[FAIL] generic synthetic return should classify as unclassified without a tracked repo request", file=sys.stderr)
            return 1

        request32_dir = tmp_path / "requests32"
        request32_path = request32_dir / "olm_bitdepth_32bpc_probe_smoke_20260703.json"
        request32_dir.mkdir(parents=True)
        request32 = {
            "request_id": "olm_bitdepth_32bpc_probe_smoke_20260703",
            "scope": {"bit_depth": "32bpc"},
            "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
            "compare_policy": {
                "path": "refs/conformance/bitdepth_32bpc_compare_policy_20260703.md",
                "mode": "float-preserving-required",
                "png_only_classification": "probe-only",
            },
            "output_requirements": {
                "preferred_formats": ["exr"],
                "acceptable_float_preserving_fallbacks": ["tiff", "tif", "hdr", "raw-float-rgba"],
                "png_only_allowed": True,
                "png_only_classification": "probe-only",
                "float_preserving_required_for_ae_exact": True,
                "record_exact_format_used": True,
            },
            "render_sets": [{"id": "software_32bpc", "required": True, "bit_depth": "32bpc"}],
            "manifest_requirements": [],
            "cases": [{"id": "case_a"}],
        }
        request32_path.write_text(json.dumps(request32, indent=2), encoding="utf-8")
        repo_request_copy = repo / "refs" / "reference_requests" / request32_path.name
        repo_request_copy.write_text(json.dumps(request32, indent=2), encoding="utf-8")
        try:
            ret32_root = tmp_path / "ret32"
            ret32_root.mkdir(parents=True)
            return32_zip, _, _ = make_windows_ref_return(ret32_root)
            raw32 = out_json.parent / "summary32.json"
            raw32md = out_json.parent / "summary32.md"
            proc32 = subprocess.run(
                [
                    sys.executable,
                    str(summary),
                    str(return32_zip),
                    "--output-json",
                    str(raw32),
                    "--output-md",
                    str(raw32md),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            print(proc32.stdout, end="" if proc32.stdout.endswith("\n") else "\n")
            if proc32.returncode != 0:
                return proc32.returncode
            report32 = json.loads(raw32.read_text(encoding="utf-8"))
            if report32["reference_quality"] != "unclassified":
                print("[FAIL] control synthetic 32bpc return should stay unclassified before request-id swap", file=sys.stderr)
                return 1

            # Rewrite the generated synthetic return to use the tracked 32bpc request id, while staying PNG-only.
            import zipfile
            patched_zip = tmp_path / "patched32.zip"
            with zipfile.ZipFile(return32_zip) as src, zipfile.ZipFile(patched_zip, "w", zipfile.ZIP_DEFLATED) as dst:
                for info in src.infolist():
                    payload = src.read(info.filename)
                    if info.filename.endswith("reference_manifest.json"):
                        manifest = json.loads(payload.decode("utf-8"))
                        manifest["request_id"] = request32["request_id"]
                        for case in manifest.get("cases", []):
                            if isinstance(case, dict):
                                case["request_id"] = request32["request_id"]
                        payload = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
                    dst.writestr(info, payload)
            proc32b = subprocess.run(
                [
                    sys.executable,
                    str(summary),
                    str(patched_zip),
                    "--output-json",
                    str(raw32),
                    "--output-md",
                    str(raw32md),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            print(proc32b.stdout, end="" if proc32b.stdout.endswith("\n") else "\n")
            if proc32b.returncode != 0:
                return proc32b.returncode
            report32b = json.loads(raw32.read_text(encoding="utf-8"))
            if report32b["reference_quality"] != "probe-only-png-return":
                print("[FAIL] 32bpc PNG-only synthetic return should classify as probe-only-png-return", file=sys.stderr)
                return 1
        finally:
            if repo_request_copy.exists():
                repo_request_copy.unlink()
    print("[OK] summarize Windows reference return smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
