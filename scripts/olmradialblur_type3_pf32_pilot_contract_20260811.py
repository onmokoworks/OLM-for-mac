"""Contract helpers for the witness-v2 PF32 Type-3 Windows AE pilot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
AE_VERSION = "25.2x131"
OUTPUT_TEMPLATE = "OLM EXR 32 Float"
REQUEST_SCHEMA = "olmradialblur-type3-windows-witness-request/2"
RETURN_SCHEMA = "olmradialblur-type3-windows-witness-return/2"
PILOT_SCHEMA = "olmradialblur-type3-windows-ae-pilot/2"

PARAM_MATCH_NAMES = {
    "Blur Type": "OLM RadialBlur-0001",
    "Center": "OLM RadialBlur-0002",
    "Outer Strength": "OLM RadialBlur-0004",
    "Outer Offset Mode": "OLM RadialBlur-0028",
    "Outer Offset": "OLM RadialBlur-0029",
    "Inner Strength": "OLM RadialBlur-0008",
    "Repeat Border": "OLM RadialBlur-0026",
    "Ratio": "OLM RadialBlur-0012",
    "Angle": "OLM RadialBlur-0013",
    "Quality": "OLM RadialBlur-0015",
    "Brightness Gain": "OLM RadialBlur-0016",
    "Size Variation": "OLM RadialBlur-0017",
    "Noise Variation": "OLM RadialBlur-0019",
    "Noise Type": "OLM RadialBlur-0020",
    "Thickness": "OLM RadialBlur-0024",
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_hash(value: object) -> str:
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def pilot_cases(witness: dict) -> list[dict]:
    if witness.get("schema") != REQUEST_SCHEMA:
        raise ValueError("witness schema mismatch")
    selected = [case for case in witness.get("cases", [])
                if case.get("project_bpc") == 32 and case.get("noise_variation") == 25]
    if len(selected) != 4:
        raise ValueError(f"witness pilot case cardinality: {len(selected)}")
    rows = []
    for case in selected:
        translated = {PARAM_MATCH_NAMES["Blur Type"]: case["blur_type"]}
        parameter_names = set(PARAM_MATCH_NAMES) - {"Blur Type"}
        if set(case["parameters"]) != parameter_names:
            raise ValueError(f"{case['case_id']}: unsupported witness parameter surface")
        for name, value in case["parameters"].items():
            translated[PARAM_MATCH_NAMES[name]] = value
        layer_name = Path(case["noise_layer"]).stem
        for repeat in case["repeats"]:
            row_id = f"{case['case_id']}.r{repeat}"
            row = {
                "row_id": row_id,
                "case_id": case["case_id"],
                "repeat": repeat,
                "depth": case["project_bpc"],
                "renderer": case["renderer"],
                "source_member": case["primary_source"],
                "noise_layer_member": case["noise_layer"],
                "noise_layer_match_name": "OLM RadialBlur-0021",
                "noise_layer_expected_source_name": f"{layer_name}.png",
                "parameters": translated,
                "comp": {"width": case["width"], "height": case["height"],
                         "pixel_aspect": 1, "frame_rate": 24, "duration_seconds": 1},
            }
            row["execution_row_sha256"] = canonical_hash(row)
            rows.append(row)
    if len(rows) != 8:
        raise ValueError(f"witness pilot render cardinality: {len(rows)}")
    return rows


def contract(witness: dict, files: dict[str, bytes]) -> dict:
    expected_assets = {
        witness["primary_source"]["path"]: witness["primary_source"]["sha256"],
        **{asset["path"]: asset["sha256"] for asset in witness["layers"].values()},
    }
    observed = {path: digest(raw) for path, raw in files.items()}
    if observed != expected_assets:
        raise ValueError("packaged fixtures do not exactly match witness v2")
    rows = pilot_cases(witness)
    return {
        "schema": PILOT_SCHEMA,
        "parent_witness_schema": REQUEST_SCHEMA,
        "return_schema": RETURN_SCHEMA,
        "witness_request_member": "WITNESS_REQUEST.json",
        "witness_request_sha256": canonical_hash(witness),
        "package_id": "olmradialblur_type3_windows_ae_pilot_20260811",
        "target": {"ae_version": AE_VERSION, "ae_file_version": [25, 2, 0, 131],
                   "renderer": "Software", "renderer_raw": 1816, "depth": 32,
                   "output_template": OUTPUT_TEMPLATE},
        "plugin": {"member": "aex/OLMRadialBlur.aex", "sha256": AEX_SHA256},
        "fixtures": {path: {"member": path, "sha256": checksum,
                             "dimensions": [9, 7], "alpha": "straight"}
                     for path, checksum in expected_assets.items()},
        "rows": rows,
        "process_contract": {"fresh_afterfx_per_row": True, "expected_rows": 8,
                             "all_ae_pids_unique": True},
        "noise_layer_binding": {
            "write_then_readback_required": True,
            "known_risk": "PF layer stream may expose PropertyValueType.NO_VALUE to ExtendScript",
            "fail_closed_code": "NOISE_LAYER_BINDING_UNAVAILABLE",
            "forbidden_fallback": "rendering with PF_LayerDefault_NONE",
        },
        "claim_boundary": "Exact witness-v2 --pilot subset only: PF32, NV25, AE 25.2x131 Software, Zoom/Rotation x pattern/inverse x repeat2",
    }


def validate_embedded_witness(package_root: Path, request: dict) -> dict:
    witness_path = package_root / request["witness_request_member"]
    witness = json.loads(witness_path.read_text(encoding="utf-8"))
    if canonical_hash(witness) != request.get("witness_request_sha256"):
        raise ValueError("embedded witness request hash mismatch")
    files = {path: (package_root / path).read_bytes() for path in request["fixtures"]}
    expected = contract(witness, files)
    if request != expected:
        raise ValueError("pilot contract drifted from embedded witness v2")
    return witness


def validate_return(package_root: Path, return_root: Path) -> dict:
    request = json.loads((package_root / "BATCH_CONTRACT.json").read_text(encoding="utf-8"))
    validate_embedded_witness(package_root, request)
    got = []
    for expected in request["rows"]:
        path = return_root / "outputs" / expected["row_id"] / "attestation.json"
        if not path.is_file():
            raise ValueError(f"missing attestation: {expected['row_id']}")
        row = json.loads(path.read_text(encoding="utf-8-sig"))
        checks = (("row_id", expected["row_id"]), ("case_id", expected["case_id"]),
                  ("repeat", expected["repeat"]),
                  ("execution_row_sha256", expected["execution_row_sha256"]),
                  ("ae_version", AE_VERSION), ("renderer", "Software"), ("depth", 32),
                  ("aex_sha256", AEX_SHA256),
                  ("noise_layer_source_name", expected["noise_layer_expected_source_name"]))
        for key, value in checks:
            if row.get(key) != value:
                raise ValueError(f"{expected['row_id']}: {key} mismatch")
        if row.get("witness_request_sha256") != request["witness_request_sha256"]:
            raise ValueError(f"{expected['row_id']}: witness request mismatch")
        if row.get("noise_layer_readback") != row.get("noise_layer_written"):
            raise ValueError(f"{expected['row_id']}: Noise Layer readback mismatch")
        if row.get("output_template") != OUTPUT_TEMPLATE or not isinstance(row.get("output_settings"), dict):
            raise ValueError(f"{expected['row_id']}: output template/settings missing")
        if row.get("parameters_before") != row.get("parameters_after"):
            raise ValueError(f"{expected['row_id']}: parameter readback drift")
        observed = {item.get("match_name"): item.get("value")
                    for item in row.get("parameters_before", [])}
        if observed != expected["parameters"]:
            raise ValueError(f"{expected['row_id']}: parameter values mismatch")
        source = request["fixtures"][expected["source_member"]]["sha256"]
        layer = request["fixtures"][expected["noise_layer_member"]]["sha256"]
        if row.get("source_sha256") != source or row.get("noise_layer_sha256") != layer:
            raise ValueError(f"{expected['row_id']}: source/layer hash mismatch")
        member = f"outputs/{expected['row_id']}/effect_on.exr"
        output = return_root / member
        if (row.get("output_member") != member or not output.is_file()
                or digest(output.read_bytes()) != row.get("output_sha256")):
            raise ValueError(f"{expected['row_id']}: EXR missing/hash mismatch")
        got.append(row)
    pids = [row.get("ae_pid") for row in got]
    if any(not isinstance(pid, int) or pid <= 0 for pid in pids) or len(set(pids)) != 8:
        raise ValueError("all eight rows must bind unique fresh AE PIDs")
    groups = {}
    for row in got:
        groups.setdefault(row["case_id"], set()).add(row["output_sha256"])
    unstable = [key for key, values in groups.items() if len(values) != 1]
    if unstable:
        raise ValueError("fresh-process nondeterminism: " + ", ".join(unstable))
    return {"status": "exact_return_contract", "schema": RETURN_SCHEMA,
            "rows": 8, "cases": 4}
