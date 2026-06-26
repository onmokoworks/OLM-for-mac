#!/usr/bin/env python3
"""Smoke-test AE pixel validation request packaging and verification."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run(cmd: list[object], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [str(part) for part in cmd],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print("$", " ".join(str(part) for part in cmd))
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc


def manifest_frames(reference: Path) -> dict[str, str]:
    manifest_path = reference / "reference_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames: dict[str, str] = {}
    for index, case in enumerate(data.get("cases", []), start=1):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id") or f"case_{index:04d}")
        frame = case.get("frame")
        if isinstance(frame, str):
            frames[case_id] = frame
    return frames


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_smoke_") as tmp:
        tmp_path = Path(tmp)
        presets = [
            (
                "olmblur",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMBlur",
                ("case_0001", "case_0002", "case_0003", "case_0004", "case_0005", "case_0006", "case_0007"),
            ),
            (
                "olmblur_exact",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMBlur",
                ("case_0001", "case_0002", "case_0003", "case_0004", "case_0005", "case_0006", "case_0007"),
            ),
            (
                "olmcolorkey",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMColorKey",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0005",
                    "case_0006",
                    "case_0007",
                    "case_0008",
                    "case_0009",
                ),
            ),
            (
                "olmcolorkey_exact",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMColorKey",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0005",
                    "case_0006",
                    "case_0007",
                    "case_0008",
                    "case_0009",
                ),
            ),
            (
                "olmtoondilate",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate",
                ("case_0001", "case_0002", "case_0003"),
            ),
            (
                "olmtoondilate_exact",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate",
                ("case_0001", "case_0002", "case_0003"),
            ),
            (
                "olmdistancegradation",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0005",
                    "case_0006",
                    "case_0007",
                    "case_0009",
                    "case_0015",
                    "case_0017",
                    "case_0018",
                    "case_0019",
                ),
            ),
            (
                "olmdistancegradation_exact",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0005",
                    "case_0006",
                    "case_0007",
                    "case_0009",
                    "case_0015",
                    "case_0017",
                    "case_0018",
                    "case_0019",
                ),
            ),
            (
                "olmdistancegradation_extended",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                (
                    "case_0008",
                    "case_0010",
                    "case_0011",
                    "case_0012",
                    "case_0013",
                    "case_0014",
                    "case_0016",
                    "case_0020",
                    "case_0021",
                    "case_0022",
                    "case_0023",
                    "case_0024",
                    "case_0025",
                    "case_0026",
                    "case_0027",
                    "case_0028",
                ),
            ),
            (
                "olmdistancegradation_extended_exact",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                (
                    "case_0008",
                    "case_0010",
                    "case_0011",
                    "case_0012",
                    "case_0013",
                    "case_0014",
                    "case_0016",
                    "case_0020",
                    "case_0021",
                    "case_0022",
                    "case_0023",
                    "case_0024",
                    "case_0025",
                    "case_0026",
                    "case_0027",
                    "case_0028",
                ),
            ),
            (
                "olmdistancegradation_blur",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                ("case_0029",),
            ),
            (
                "olmdistancegradation_blur_exact",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                ("case_0029",),
            ),
            (
                "olmsmoother",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMSmoother",
                ("case_0001", "case_0002", "case_0003"),
            ),
            (
                "olmsmoother2",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMSmoother2",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0010",
                    "case_0011",
                    "case_0012",
                ),
            ),
            (
                "olmsmoother2_no_key_grid",
                repo
                / "refs"
                / "win_references"
                / "olm_reference_return_windows_recapture_20260615"
                / "OLMSmoother2",
                (
                    "sm2_no_key_s000_r1",
                    "sm2_no_key_s025_r1",
                    "sm2_no_key_s050_r1",
                    "sm2_no_key_s100_r1",
                    "sm2_no_key_s000_r2",
                    "sm2_no_key_s025_r2",
                    "sm2_no_key_s050_r2",
                    "sm2_no_key_s100_r2",
                    "sm2_no_key_s000_r3",
                    "sm2_no_key_s025_r3",
                    "sm2_no_key_s050_r3",
                    "sm2_no_key_s100_r3",
                ),
            ),
            (
                "bitdepth16_olmblur_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
                tuple(f"olmblur__case_{index:04d}" for index in range(1, 8)),
            ),
            (
                "bitdepth16_olmcolorkey_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
                tuple(f"olmcolorkey__case_{index:04d}" for index in range(1, 10)),
            ),
            (
                "bitdepth16_olmdistancegradation_basic_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
                tuple(
                    f"olmdistancegradation_basic__{case_id}"
                    for case_id in (
                        "case_0001",
                        "case_0002",
                        "case_0003",
                        "case_0004",
                        "case_0005",
                        "case_0006",
                        "case_0007",
                        "case_0009",
                        "case_0015",
                        "case_0017",
                        "case_0018",
                        "case_0019",
                    )
                ),
            ),
            (
                "bitdepth16_olmdistancegradation_extended_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
                tuple(
                    f"olmdistancegradation_extended__{case_id}"
                    for case_id in (
                        "case_0008",
                        "case_0010",
                        "case_0011",
                        "case_0012",
                        "case_0013",
                        "case_0014",
                        "case_0016",
                        "case_0020",
                        "case_0021",
                        "case_0022",
                        "case_0023",
                        "case_0024",
                        "case_0025",
                        "case_0026",
                        "case_0027",
                        "case_0028",
                    )
                ),
            ),
            (
                "bitdepth16_olmdistancegradation_blur_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
                ("olmdistancegradation_blur__case_0029",),
            ),
        ]
        for preset, reference, case_ids in presets:
            request_zip = tmp_path / f"{preset}_request.zip"
            proc = run(
                [
                    sys.executable,
                    repo / "scripts" / "package_ae_pixel_validation_request.py",
                    "--preset",
                    preset,
                    "--output",
                    request_zip,
                ],
                repo,
            )
            if proc.returncode != 0:
                return proc.returncode
            with zipfile.ZipFile(request_zip) as archive:
                manifest_name = next(name for name in archive.namelist() if name.endswith("request_manifest.json"))
                template_name = next(
                    name for name in archive.namelist() if name.endswith("AE_PIXEL_VALIDATION_RESULT.template.json")
                )
                manifest = json.loads(archive.read(manifest_name))
                template = json.loads(archive.read(template_name))
            if manifest.get("gate_kind") != "host_smoke_pixel_tolerance":
                print("[FAIL] request manifest missing host_smoke_pixel_tolerance gate_kind")
                return 1
            if template.get("gate_kind") != "host_smoke_pixel_tolerance":
                print("[FAIL] result template missing host_smoke_pixel_tolerance gate_kind")
                return 1

            result_root = tmp_path / f"returned_{preset}"
            result_dir = result_root / "candidate"
            result_dir.mkdir(parents=True)
            frames = manifest_frames(reference)
            for case_id in case_ids:
                frame = frames.get(case_id, f"{case_id}.png")
                shutil.copy2(reference / frame, result_dir / frame)

            result_zip = tmp_path / f"returned_{preset}.zip"
            with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in result_root.rglob("*"):
                    archive.write(path, path.relative_to(result_root))

            proc = run(
                [
                    sys.executable,
                    repo / "scripts" / "verify_ae_pixel_validation_result.py",
                    request_zip,
                    result_zip,
                    "--run-dir",
                    tmp_path / f"verify_run_{preset}",
                ],
                repo,
            )
            if proc.returncode != 0:
                return proc.returncode

    print("[OK] AE pixel validation request smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
