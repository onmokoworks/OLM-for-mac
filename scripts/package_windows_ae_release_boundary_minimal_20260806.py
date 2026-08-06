#!/usr/bin/env python3
"""Build the minimal Windows AE calibration batch for the OLM Mac release.

This deliberately reuses one already-materialized row from the pinned r5
campaign.  The frozen release matrix identifies OLMSmoother v1 PF16 as the
only definite missing Windows observation; all other release cells reuse
retained evidence and must not be recaptured.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5"
OUT_DIR = ROOT / "refs/reference_requests"
PACKAGE_ID = "olm_windows_ae_release_boundary_minimal_20260806"
ZIP_TIME = (2026, 8, 6, 0, 0, 0)
SELECTED = {("OLMSmoother v1", "case_0001", 16)}
REUSED = {
    "OLMBlur": "refs/conformance/olmblur_32bpc_case0001_ae_exact_20260727.json",
    "OLMColorKey": "refs/conformance/olmcolorkey_32bpc_all9_ae_exact_20260728.json",
    "OLMToonDilate": "refs/conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728.json",
    "OLMSmoother2": "refs/conformance/olmsmoother2_32bpc_case01_10_ae_exact_20260727.json",
    "ColorKeep": "refs/conformance/colorkeep_pf16_upstream_chain_current_mac_ae_20260806.md",
    "OLMDistanceGradation": "refs/conformance/olmdistancegradation_pf32_case0001_current_mac_ae_exact_20260806.json",
    "OLMDirectionalBlur": "refs/conformance/olmdirectionalblur_pf8_current_mac_ae_exact_20260806.json",
    "OLMRadialBlur": "refs/conformance/olmradialblur_current_mac_ae_supported_lanes_20260806.json",
    "OLMKiraKira": "refs/conformance/olmkirakira_completion_matrix_20260805.json",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_member(stage: Path, member: str) -> dict:
    source = SOURCE / member
    if not source.is_file():
        raise SystemExit(f"missing pinned campaign member: {source}")
    target = stage / member
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {"member": member, "sha256": sha(target), "bytes": target.stat().st_size}


def write_zip(stage: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(stage).as_posix(), ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())


def main() -> int:
    rows_path = SOURCE / "EXECUTION_ROWS.json"
    rows_doc = json.loads(rows_path.read_text(encoding="utf-8"))
    rows = [
        row for row in rows_doc["rows"]
        if (row["plugin"], row["case_id"], row["depth"]) in SELECTED
    ]
    observed = {(r["plugin"], r["case_id"], r["depth"]) for r in rows}
    if observed != SELECTED:
        raise SystemExit(f"selected row mismatch: missing={sorted(SELECTED - observed)!r}")
    rows.sort(key=lambda r: (r["plugin"], r["depth"]))

    output = OUT_DIR / f"{PACKAGE_ID}.zip"
    with tempfile.TemporaryDirectory(prefix=PACKAGE_ID + "_") as tmp:
        stage = Path(tmp) / PACKAGE_ID
        stage.mkdir()
        members: list[dict] = []
        needed = set()
        for row in rows:
            needed.update((row["aex_member"], row["source_member"], row["case_definition_file"]))
            template = row["project_contract"]["input_interpretation"].get("template_member")
            if template:
                needed.add(template)
        for member in sorted(needed):
            members.append(copy_member(stage, member))
        exr_tool = "tools/verify_32bpc_float_return.py"
        members.append(copy_member(stage, exr_tool))
        scope_source = ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md"
        scope_member = "scope_evidence/olm_release_completion_matrix_20260806.md"
        scope_target = stage / scope_member
        scope_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scope_source, scope_target)
        members.append({"member": scope_member, "sha256": sha(scope_target), "bytes": scope_target.stat().st_size})

        reuse_rows = []
        for plugin, repo_member in REUSED.items():
            source = ROOT / repo_member
            if not source.is_file():
                raise SystemExit(f"missing reuse evidence: {source}")
            member = f"reuse_evidence/{source.name}"
            target = stage / member
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            record = {"plugin": plugin, "member": member, "sha256": sha(target), "bytes": target.stat().st_size}
            reuse_rows.append(record)
            members.append({k: record[k] for k in ("member", "sha256", "bytes")})

        contract = {
            "kind": "olm_windows_ae_release_boundary_minimal",
            "schema_version": 1,
            "package_id": PACKAGE_ID,
            "source_campaign_id": rows_doc["campaign_id"],
            "authoritative_release_scope": {
                "member": scope_member,
                "sha256": sha(scope_target),
                "decision": "only OLMSmoother v1 PF16 is a definite missing Windows observation",
            },
            "target": {
                "after_effects": "26.3x87",
                "renderer": "SOFTWARE",
                "renderer_raw": 1816,
                "working_space": None,
                "linear_blending": False,
                "input": "straight alpha, Preserve RGB, hash-bound source",
                "output": "uncompressed scanline OpenEXR FLOAT32 ABGR, Preserve RGB",
            },
            "claim_boundary": (
                "One OLMSmoother v1 PF16 AE-host calibration cell only. Major-mode/depth "
                "implementation parity remains grounded by retained actual-AEX fixtures; this row "
                "must not be generalized to PF8 or a native PF32 lane."
            ),
            "acquire": rows,
            "reuse": reuse_rows,
            "required_return": {
                "archive": "RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip",
                "per_row": [
                    "outputs/{row_id}/no_effect.exr",
                    "outputs/{row_id}/effect_on.exr",
                    "outputs/{row_id}/attestation.json",
                ],
                "attestation_fields": [
                    "row_id", "execution_row_sha256", "ae_version", "ae_executable_path",
                    "ae_executable_sha256", "ae_pid", "ae_process_start_utc", "renderer_raw",
                    "bits_per_channel", "working_space_raw", "linear_blending", "aex_path",
                    "aex_sha256", "module_base", "source_sha256", "parameters_before",
                    "parameters_after", "no_effect_sha256", "effect_on_sha256",
                ],
            },
            "members": members,
        }
        (stage / "BATCH_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(ROOT / "scripts/verify_windows_ae_release_boundary_minimal_20260806.py", stage / "VERIFY_RETURN.py")
        readme = """# Minimal OLM Windows AE release-boundary batch

Run only the single row in `BATCH_CONTRACT.json`: OLMSmoother v1 `case_0001`
at native PF16.  The other nine plug-ins are evidence reuse rows and MUST NOT
be rerendered.  In particular, do not recapture ColorKeep or OLMKiraKira: their
remaining release work is Mac-host/production closure using retained Windows
references.  Use a fresh AE 26.3x87 process/project/effect, Software
renderer (raw 1816), working space None, linear blending off, straight-alpha
Preserve-RGB import, and the pinned AEX/source/template hashes.

For each row render disabled and enabled branches to uncompressed scanline
FLOAT32 OpenEXR and retain `attestation.json` with every field listed in the
contract.  Hash files after AE exits.  Do not substitute PNG previews.

Before returning, run:

    py -3 VERIFY_RETURN.py RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
"""
        (stage / "README_WINDOWS.md").write_text(readme, encoding="utf-8")
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()
        write_zip(stage, output)

    print(f"[PASS] wrote {output}")
    print(f"[SUMMARY] acquire_rows={len(rows)} reuse_plugins={len(REUSED)} total_plugins=10")
    print(f"[SHA256] {sha(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
