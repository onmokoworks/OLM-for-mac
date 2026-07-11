#!/usr/bin/env python3
"""Smoke-test focused runtime packages prepared as follow-up evidence asks."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


CASES = [
    {
        "profile": "radialblur-zoom-case0009-final-plane-cells",
        "filename": "radialblur_zoom_case0009_final_plane_cells.zip",
        "request_id": "olmradialblur_zoom_case0009_final_plane_cells_20260709",
        "entrypoint": "refs/conformance/olmradialblur_zoom_case0009_final_plane_cells_contract_20260709.md",
        "readme_pin": "Execute `olmradialblur_zoom_case0009_final_plane_cells_20260709` only.",
        "required": {
            "refs/conformance/olmradialblur_zoom_case0009_final_plane_cells_contract_20260709.md",
            "refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md",
            "refs/conformance/olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md",
            "refs/conformance/olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.md",
            "refs/conformance/olmradialblur_zoom_case0009_quantize_locus_20260709.md",
            "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json",
            "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png",
            "refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png",
        },
    },
    {
        "profile": "directionalblur-angle0-single-shot-witness",
        "filename": "directionalblur_angle0_single_shot.zip",
        "request_id": "olmdirectionalblur_angle0_single_shot_witness_20260708",
        "entrypoint": "refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md",
        "readme_pin": "Execute `olmdirectionalblur_angle0_single_shot_witness_20260708` only.",
        "required": {
            "refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md",
            "refs/conformance/olmdirectionalblur_angle0_helper_gate_return_acceptance_20260707.md",
            "refs/reference_requests/directionalblur_context_scale_20260606.json",
        },
    },
    {
        "profile": "distancegradation-case0014-layer-source-witness",
        "filename": "distancegradation_case0014_layer_source.zip",
        "request_id": "olmdistancegradation_case0014_layer_source_witness_20260708",
        "entrypoint": "refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md",
        "readme_pin": "Execute `olmdistancegradation_case0014_layer_source_witness_20260708` only.",
        "required": {
            "refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md",
            "refs/conformance/olmdistancegradation_depth_gate_result_20260708.md",
            "refs/conformance/olmdistancegradation_16bpc_powerfix_residual_families_20260629.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0014_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0014.png",
        },
    },
    {
        "profile": "distancegradation-depthgate-907-store-export-witness",
        "filename": "distancegradation_depthgate_907_store_export.zip",
        "request_id": "olmdistancegradation_depthgate_907_store_export_witness_20260708",
        "entrypoint": "refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md",
        "readme_pin": "Execute `olmdistancegradation_depthgate_907_store_export_witness_20260708` only.",
        "required": {
            "refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md",
            "refs/conformance/olmdistancegradation_depthgate_quantization_return_intake_20260708.md",
            "refs/conformance/olmdistancegradation_depthgate_quantization_witness_contract_20260708.md",
            "refs/conformance/olmdistancegradation_depth_gate_result_20260708.md",
            "refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_quantization_witness_20260708.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0026_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0026.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-field-store-witness",
        "filename": "distancegradation_0010_0011_field_store.zip",
        "request_id": "olmdistancegradation_0010_0011_field_store_witness_20260709",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_field_store_witness_contract_20260709.md",
        "readme_pin": "Execute `olmdistancegradation_0010_0011_field_store_witness_20260709` only.",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_field_store_witness_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-field-store-prewarm-witness",
        "filename": "distancegradation_0010_0011_field_store_prewarm.zip",
        "request_id": "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_field_store_prewarm_contract_20260709.md",
        "readme_pin": "Execute `olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709` only.",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_field_store_prewarm_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_store_witness_contract_20260709.md",
            "refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_witness_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-writeback-follow-witness",
        "filename": "distancegradation_0010_0011_writeback_follow.zip",
        "request_id": "olmdistancegradation_0010_0011_writeback_follow_witness_20260709",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_writeback_follow_contract_20260709.md",
        "readme_pin": "Execute `olmdistancegradation_0010_0011_writeback_follow_witness_20260709` only.",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_writeback_follow_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_store_return2_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_store_prewarm_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_store_witness_contract_20260709.md",
            "refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_witness_20260709.md",
            "refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_witness_20260709.json",
            "refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-writeback-pointer-map-witness",
        "filename": "distancegradation_0010_0011_writeback_pointer_map.zip",
        "request_id": "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_contract_20260709.md",
        "readme_pin": "Execute `olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709` only.",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_follow_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_follow_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_store_return2_intake_20260709.md",
            "refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_writeback_follow_witness_20260709.md",
            "refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_writeback_follow_witness_20260709.json",
            "refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-rdx-producer-packsite-witness",
        "filename": "distancegradation_0010_0011_rdx_producer_packsite.zip",
        "request_id": "olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_rdx_producer_packsite_contract_20260709.md",
        "readme_pin": "olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_rdx_producer_packsite_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-compose-input-pointer-witness",
        "filename": "distancegradation_0010_0011_compose_input_pointer.zip",
        "request_id": "olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md",
        "readme_pin": "olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_rdx_producer_return_intake_20260710.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md",
            "notes/IR_OLMDistanceGradation.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
        },
    },
    {
        "profile": "distancegradation-0010-0011-compose-exact-address-witness",
        "filename": "distancegradation_0010_0011_compose_exact_address.zip",
        "request_id": "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710",
        "entrypoint": "refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md",
        "readme_pin": "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710",
        "required": {
            "refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md",
            "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_return_intake_20260710.md",
            "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_rdx_producer_return_intake_20260710.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
            "notes/IR_OLMDistanceGradation.md",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/request_manifest.json",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
            "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
        },
    },
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def verify_case(root: Path, case: dict[str, object], tmp: Path) -> None:
    output = tmp / str(case["filename"])
    subprocess.run(
        [
            "python3",
            str(root / "scripts/package_runtime_trace_requests.py"),
            "--profile",
            str(case["profile"]),
            "--output",
            str(output),
        ],
        cwd=root,
        check=True,
    )
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json").decode("utf-8"))
        template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json").decode("utf-8"))
        snapshot = json.loads(archive.read("next_reference_actions_snapshot.json").decode("utf-8"))
        readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")

    required = {
        "README_RUNTIME_TRACE.md",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        "runtime_trace_package_manifest.json",
        "next_reference_actions_snapshot.json",
        *case["required"],
    }
    missing = sorted(required - names)
    if missing:
        raise AssertionError(f"{case['profile']} missing package files: {missing}")
    if manifest.get("profile") != case["profile"]:
        raise AssertionError(f"unexpected profile for {case['profile']}: {manifest.get('profile')}")
    if manifest.get("entrypoint") != case["entrypoint"]:
        raise AssertionError(f"unexpected entrypoint for {case['profile']}: {manifest.get('entrypoint')}")
    action_ids = [action.get("request_id") for action in manifest.get("runtime_actions", [])]
    if action_ids != [case["request_id"]]:
        raise AssertionError(f"unexpected actions for {case['profile']}: {action_ids}")
    if case["readme_pin"] not in readme:
        raise AssertionError(f"README does not pin {case['request_id']}")
    if snapshot.get("kind") != "focused_runtime_trace_package_snapshot":
        raise AssertionError(f"unexpected snapshot kind for {case['profile']}: {snapshot.get('kind')}")
    result_ids = [row.get("request_id") for row in template.get("results", [])]
    if result_ids != [case["request_id"]]:
        raise AssertionError(f"unexpected return template results for {case['profile']}: {result_ids}")
    if case["profile"] == "directionalblur-angle0-single-shot-witness":
        observations = template["results"][0].get("observations") or {}
        case_ids = [row.get("case_id") for row in observations.get("cases", [])]
        if case_ids != ["case_0001"]:
            raise AssertionError(f"single-shot DirectionalBlur template must stay angle-0 only: {case_ids}")


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="focused_runtime_followups_") as tmp_name:
        tmp = Path(tmp_name)
        for case in CASES:
            verify_case(root, case, tmp)
    print("[OK] focused runtime follow-up package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
