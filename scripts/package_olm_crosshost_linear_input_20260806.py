#!/usr/bin/env python3
"""Build the minimal ColorKeep/Kira cross-host linear-input AE package."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from generate_olm_crosshost_linear_fixture_20260806 import generate


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
FIXTURE = ROOT / "refs/fixtures/olm_crosshost_linear/opaque_cells_linear_float32.exr"
MANIFEST = ROOT / "refs/fixtures/olm_crosshost_linear/manifest.json"
OUTPUT = ROOT / "refs/reference_requests/olm_crosshost_linear_input_20260806.zip"
PACKAGE_ID = "olm_crosshost_linear_input_20260806"
ZIP_TIME = (2026, 8, 6, 0, 0, 0)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(value: object) -> str:
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def safe_members(path: Path) -> dict[str, bytes]:
    result = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or any(part in ("", ".", "..") for part in pure.parts):
                raise ValueError(f"unsafe ZIP member: {name}")
            result[name] = archive.read(info)
    return result


def write_zip(stage: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(stage).as_posix(), ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())


def main() -> int:
    fixture_manifest = generate(FIXTURE)
    MANIFEST.write_text(json.dumps(fixture_manifest, indent=2) + "\n", encoding="utf-8")
    base = safe_members(BASE)
    old = json.loads(base["BATCH_CONTRACT.json"])
    rows = [copy.deepcopy(row) for row in old["acquire"] if row["plugin"] in ("ColorKeep", "OLMKiraKira")]
    rows.sort(key=lambda row: (row["plugin"], row["depth"]))
    if len(rows) != 6:
        raise SystemExit("expected ColorKeep/Kira PF8/PF16/PF32 rows")
    fixture_bytes = FIXTURE.read_bytes()
    fixture_hash = digest(fixture_bytes)
    for row in rows:
        row["row_id"] += "__linear_float32_input"
        row["source_member"] = "inputs/opaque_cells_linear_float32.exr"
        row["source_sha256"] = fixture_hash
        interpretation = row["project_contract"]["input_interpretation"]
        interpretation.update({
            "source_format": "OpenEXR",
            "source_sample_type": "FLOAT32",
            "source_compression": "none",
            "preserve_rgb_runtime_write_if_api_available": True,
            "preserve_rgb_api_availability_readback_required": True,
            "color_profile_name_live_readback_required": True,
            "source_color_conversion_forbidden": True,
        })
        row.pop("execution_row_sha256", None)
        row["execution_row_sha256"] = canonical_hash(row)
    contract = {
        "kind": "olm_crosshost_linear_input_contract",
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "derived_from_package_sha256": digest(BASE.read_bytes()),
        "target": old["target"],
        "input_contract": {
            "member": "inputs/opaque_cells_linear_float32.exr",
            "sha256": fixture_hash,
            "dimensions": [1920, 1080],
            "channels": ["A", "B", "G", "R"],
            "sample_type": "FLOAT32",
            "compression": "none",
            "working_space_raw_accepted": [None, ""],
            "linear_blending": False,
            "alpha_mode": "straight",
            "preserve_rgb_policy": "set and require true only when ExtendScript exposes the property",
            "preserve_rgb_api_availability_readback_required": True,
            "color_profile_name_live_readback_required": True,
            "effective_no_conversion_gate": "paired no_effect raw FLOAT32 equality; descriptive properties alone never prove it",
        },
        "acquire": rows,
        "required_return": old["required_return"],
        "cross_host_acceptance": {
            "same_execution_row_required": True,
            "no_effect_raw_float32_mismatches": 0,
            "effect_on_raw_float32_mismatches": 0,
            "epsilon": 0,
            "nan_inf_policy": "raw words must match",
        },
        "reuse_boundary": {
            "existing_seven_row_return": "process/module/parameter identity and same-host relation only",
            "existing_pixel_artifacts": "not reusable for cross-host raw exact because PNG effect-off RGB already differs on every pixel",
            "new_windows_rows": 6,
            "reason": "one effect-on row per plugin and native depth is irreducible; each row also supplies its own disabled control",
        },
        "claim_boundary": "ColorKeep and OLMKiraKira representative cases at PF8/PF16/PF32 only; no other mode, fixture, host version, renderer, or color contract is implied.",
    }
    with tempfile.TemporaryDirectory(prefix=PACKAGE_ID + "_") as tmp:
        stage = Path(tmp) / PACKAGE_ID
        stage.mkdir()
        needed = {"inputs/preserve_rgb_template.aep", "tools/verify_32bpc_float_return.py"}
        for row in rows:
            needed.update((row["aex_member"], row["case_definition_file"]))
        for name in sorted(needed):
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base[name])
        target = stage / "inputs/opaque_cells_linear_float32.exr"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fixture_bytes)
        (stage / "FIXTURE_MANIFEST.json").write_text(json.dumps(fixture_manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "BATCH_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

        jsx = (ROOT / "scripts/ae_render_olm_windows_ae_release_boundary_20260806.jsx").read_text(encoding="utf-8")
        anchor = 'footage[0].replace(new File(root+"/"+row.source_member)); footage[0].mainSource.alphaMode=AlphaMode.STRAIGHT;'
        replacement = anchor + ' var preserveRGBAvailable=(typeof footage[0].mainSource.preserveRGB!=="undefined"); if(preserveRGBAvailable){footage[0].mainSource.preserveRGB=true;if(footage[0].mainSource.preserveRGB!==true)die("Preserve RGB readback");} var sourceInterpretation={alpha_mode:Number(footage[0].mainSource.alphaMode),preserve_rgb_api_available:preserveRGBAvailable,preserve_rgb:preserveRGBAvailable?Boolean(footage[0].mainSource.preserveRGB):null,color_profile_name:String(footage[0].mainSource.colorProfileName),source_extension:String((new File(root+"/"+row.source_member)).name).toLowerCase().slice(-4)}; if(sourceInterpretation.source_extension!==".exr")die("source extension");'
        if jsx.count(anchor) != 1:
            raise SystemExit("JSX source anchor drift")
        jsx = jsx.replace(anchor, replacement)
        jsx = jsx.replace("linear_blending:pr.linearBlending,parameters_before:before", "linear_blending:pr.linearBlending,source_interpretation:sourceInterpretation,parameters_before:before")
        (stage / "scripts").mkdir()
        (stage / "scripts/ae_render_olm_crosshost_linear_input_20260806.jsx").write_text(jsx, encoding="utf-8")

        ps = (ROOT / "scripts/run_olm_windows_ae_release_boundary_20260806.ps1").read_text(encoding="utf-8")
        ps = ps.replace("ae_render_olm_windows_ae_release_boundary_20260806.jsx", "ae_render_olm_crosshost_linear_input_20260806.jsx")
        ps = ps.replace("RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip", "RETURN_OLM_CROSSHOST_LINEAR_INPUT_20260806.zip")
        ps = ps.replace("olm_windows_boundary_run_20260806", "olm_crosshost_linear_run_20260806")
        ps = ps.replace("$contract.package_id -ne 'olm_windows_ae_release_boundary_minimal_20260806' -or @($contract.acquire).Count -ne 7", "$contract.package_id -ne 'olm_crosshost_linear_input_20260806' -or @($contract.acquire).Count -ne 6")
        ps = ps.replace("$att=[ordered]@{row_id=", "$att=[ordered]@{source_interpretation=$ae.source_interpretation;row_id=")
        (stage / "scripts/run_olm_crosshost_linear_input_20260806.ps1").write_text(ps, encoding="utf-8")
        shutil.copy2(ROOT / "scripts/verify_olm_crosshost_linear_input_20260806.py", stage / "VERIFY_CROSSHOST.py")
        (stage / "README_WINDOWS.md").write_text(
            "# OLM cross-host linear input\n\nRun `scripts\\run_olm_crosshost_linear_input_20260806.ps1`. "
            "This is six rows only (ColorKeep/Kira, PF8/PF16/PF32). FLOAT32 EXR input and live Preserve RGB readback are mandatory.\n",
            encoding="utf-8",
        )
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        if OUTPUT.exists():
            OUTPUT.unlink()
        write_zip(stage, OUTPUT)
    print(f"[PASS] {OUTPUT} sha256={digest(OUTPUT.read_bytes())} rows=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
