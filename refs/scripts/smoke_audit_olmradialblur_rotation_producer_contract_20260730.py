#!/usr/bin/env python3
"""Smoke-test the AE-free OLMRadialBlur Rotation producer audit."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    audit = root / "scripts/audit_olmradialblur_rotation_producer_contract_20260730.py"
    with tempfile.TemporaryDirectory(prefix="olmrb_rotation_contract_") as temp:
        out_json = Path(temp) / "audit.json"
        out_md = Path(temp) / "audit.md"
        subprocess.run(
            [sys.executable, str(audit), "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["status"] == "pre_scatter_divergence"
        assert report["aex_chain"]["ordered"] is True
        assert len(report["aex_chain"]["anchors"]) == 12
        assert report["mac_classification"]["inner"] == "copy_before_rotation_producer"
        assert report["mac_classification"]["raw_function_body_sha256"]["matches"] is True
        assert report["mac_classification"]["same_row_executable_path_bound"] is True
        assert report["mac_classification"]["aex_prepass_or_scatter_calls_present"] is False
        assert report["fixture_gate"]["status"] == "missing_required_binary_fixture"
        assert report["fixture_gate"]["production_promotion_allowed"] is False
        assert report["decision"]["production_edit_justified"] is False

        incomplete = Path(temp) / "incomplete.json"
        incomplete.write_text('{"schema":"olmradialblur.rotation-polar-plane-fixture/1"}\n', encoding="utf-8")
        subprocess.run(
            [
                sys.executable, str(audit), "--fixture", str(incomplete),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            check=True,
        )
        rejected = json.loads(out_json.read_text(encoding="utf-8"))
        assert rejected["fixture_gate"]["status"] == "invalid_fixture"
        assert any("aex_sha256" in error for error in rejected["fixture_gate"]["errors"])
        assert rejected["fixture_gate"]["production_promotion_allowed"] is False

        original_source = (root / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text(encoding="utf-8")
        adversarial_source = Path(temp) / "comment_only.cpp"
        adversarial_source.write_text(
            original_source.replace(
                "const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;",
                "// const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;",
                1,
            ),
            encoding="utf-8",
        )
        failed = subprocess.run(
            [
                sys.executable, str(audit), "--mac-source", str(adversarial_source),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert failed.returncode != 0

        early_return_source = Path(temp) / "early_return.cpp"
        early_return_source.write_text(
            original_source.replace(
                "\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n",
                "\t\t\treturn PF_Err_NONE;\n"
                "\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n",
                1,
            ),
            encoding="utf-8",
        )
        failed = subprocess.run(
            [
                sys.executable, str(audit), "--mac-source", str(early_return_source),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert failed.returncode == 2
        early_return_report = json.loads(out_json.read_text(encoding="utf-8"))
        assert early_return_report["status"] == "evidence_not_bound"
        assert early_return_report["mac_classification"]["raw_function_body_sha256"]["matches"] is False

        dead_source = Path(temp) / "dead.cpp"
        dead_source.write_text(
            original_source.replace(
                "\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n",
                "\t\t\tif constexpr (false) {\n"
                "\t\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n"
                "\t\t\t}\n",
                1,
            ),
            encoding="utf-8",
        )
        failed = subprocess.run(
            [
                sys.executable, str(audit), "--mac-source", str(dead_source),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert failed.returncode == 2
        dead_report = json.loads(out_json.read_text(encoding="utf-8"))
        assert dead_report["status"] == "evidence_not_bound"
        assert dead_report["mac_classification"]["same_row_executable_path_bound"] is False

        if0_source = Path(temp) / "if0.cpp"
        if0_source.write_text(
            original_source.replace(
                "\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n",
                "\t\t\t#if 0\n"
                "\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n"
                "\t\t\t#endif\n",
                1,
            ),
            encoding="utf-8",
        )
        failed = subprocess.run(
            [
                sys.executable, str(audit), "--mac-source", str(if0_source),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert failed.returncode == 2
        if0_report = json.loads(out_json.read_text(encoding="utf-8"))
        assert if0_report["status"] == "evidence_not_bound"
        assert if0_report["mac_classification"]["same_row_path_reason"] == "anchor_in_inactive_preprocessor_branch"

        moved_source = Path(temp) / "moved.cpp"
        moved_source.write_text(
            original_source.replace(
                "\t\t\tconst A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n",
                "",
                1,
            ) + "\n// const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;\n",
            encoding="utf-8",
        )
        failed = subprocess.run(
            [
                sys.executable, str(audit), "--mac-source", str(moved_source),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert failed.returncode != 0

        artifact = Path(temp) / "planes.bin"
        artifact.write_bytes(b"\x00\x01fixture")
        aex_binary = Path(temp) / "OLMRadialBlur.aex"
        aex_binary.write_bytes(b"pinned-aex-fixture")
        aex_digest = hashlib.sha256(aex_binary.read_bytes()).hexdigest()
        valid_fixture = {
            "schema": "olmradialblur.rotation-polar-plane-fixture/1",
            "aex_sha256": aex_digest,
            "aex_binary": {"path": str(aex_binary), "sha256": aex_digest},
            "identity": {"request_id": "request", "run_id": "run", "case_id": "case_0010"},
            "geometry": {"angular_count": 1, "radius_count": 1},
            "raw_artifact": {
                "path": str(artifact),
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            },
            "polar_rgba_f32_words": [0, 0, 0, 0x3F800000],
            "validity_u8": [1],
            "span_f32_words": [0x3F800000],
            "factor_f32_words": [0x3F800000],
            "expected_prepass_alpha_f32_words": [0x3F800000],
            "expected_accum_rgba_f32_words": [0, 0, 0, 0x3F800000],
            "expected_max_alpha_f32_words": [0x3F800000],
            "expected_normalized_rgba_f32_words": [0, 0, 0, 0x3F800000],
            "expected_inverse_samples": [{"x": 0, "y": 0, "rgba_f32_words": [0, 0, 0, 0x3F800000]}],
        }
        strict_fixture = Path(temp) / "strict.json"
        strict_fixture.write_text(json.dumps(valid_fixture), encoding="utf-8")
        subprocess.run(
            [
                sys.executable, str(audit), "--fixture", str(strict_fixture),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            check=True,
        )
        bound = json.loads(out_json.read_text(encoding="utf-8"))
        assert bound["fixture_gate"]["status"] == "binary_hash_bound_but_unexecuted"
        assert bound["fixture_gate"]["production_promotion_allowed"] is False

        valid_fixture["raw_artifact"]["sha256"] = "0" * 64
        strict_fixture.write_text(json.dumps(valid_fixture), encoding="utf-8")
        subprocess.run(
            [
                sys.executable, str(audit), "--fixture", str(strict_fixture),
                "--output-json", str(out_json), "--output-md", str(out_md),
            ],
            cwd=root,
            check=True,
        )
        mismatch = json.loads(out_json.read_text(encoding="utf-8"))
        assert mismatch["fixture_gate"]["status"] == "invalid_fixture"
        assert "raw_artifact:sha256_mismatch" in mismatch["fixture_gate"]["errors"]

        text = out_md.read_text(encoding="utf-8")
        assert "4b0f..4b77" in text
        assert "No fixture values are synthesized" in text
    print("[OK] OLMRadialBlur Rotation producer contract audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
