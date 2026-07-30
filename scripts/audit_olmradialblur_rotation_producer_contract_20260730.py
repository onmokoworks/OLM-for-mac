#!/usr/bin/env python3
"""Audit the OLMRadialBlur Rotation producer chain without running AE."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASM = ROOT / "disasm/OLMRadialBlur.aex.asm.txt"
DEFAULT_MAC = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
ROTATION_SIGNATURE = (
    "static PF_Err RenderRotation8(PF_EffectWorld *input, PF_EffectWorld *output, "
    "const OLMRadialBlurInfo &info)"
)
EXPECTED_ROTATION_BODY_SHA256 = "cf024b3dcba907aca99a28db6cd74d28b715f755f63b38fb2f469c4c82f85276"


def evidence(lines: list[str], needle: str) -> dict[str, Any]:
    matches = [(number, text) for number, text in enumerate(lines, 1) if needle in text]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one match for {needle!r}, got {len(matches)}")
    number, text = matches[0]
    return {"line": number, "text": text}


def ordered(rows: list[dict[str, Any]]) -> bool:
    return [row["line"] for row in rows] == sorted(row["line"] for row in rows)


def function_body(lines: list[str], signature: str) -> tuple[int, list[str]]:
    starts = [index for index, line in enumerate(lines) if line.strip() == signature]
    if len(starts) != 1:
        raise ValueError(f"expected one exact function signature {signature!r}, got {len(starts)}")
    start = starts[0]
    depth = 0
    opened = False
    for index in range(start + 1, len(lines)):
        code = lines[index].split("//", 1)[0]
        for char in code:
            if char == "{":
                depth += 1
                opened = True
            elif char == "}":
                depth -= 1
                if opened and depth == 0:
                    return start + 1, lines[start:index + 1]
    raise ValueError(f"unterminated function {signature!r}")


def raw_function_slice(source: str, signature: str) -> bytes:
    starts = [match.start() for match in re.finditer(re.escape(signature), source)]
    if len(starts) != 1:
        raise ValueError(f"expected one raw function signature {signature!r}, got {len(starts)}")
    start = starts[0]
    opening = source.find("{", start + len(signature))
    if opening < 0:
        raise ValueError(f"missing opening brace for {signature!r}")
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1].encode("utf-8")
    raise ValueError(f"unterminated raw function slice {signature!r}")


def body_evidence(body: list[str], first_line: int, exact: str) -> dict[str, Any]:
    matches = [
        (first_line + index, text)
        for index, text in enumerate(body)
        if text.strip() == exact
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one exact executable line {exact!r} in RenderRotation8, got {len(matches)}")
    number, text = matches[0]
    return {"line": number, "text": text}


def body_evidence_after(
    body: list[str], first_line: int, exact: str, after_line: int, window: int
) -> dict[str, Any]:
    matches = [
        (first_line + index, text)
        for index, text in enumerate(body)
        if after_line < first_line + index <= after_line + window and text.strip() == exact
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one nearby executable line {exact!r}, got {len(matches)}")
    number, text = matches[0]
    return {"line": number, "text": text}


def executable_path_supported(body: list[str], first_line: int, anchor_line: int) -> tuple[bool, str]:
    """Conservatively reject an anchor nested in dead/unsupported static control flow."""
    brace_dead: list[bool] = []
    preprocessor: list[bool] = []
    pending_dead = False
    dead_patterns = (
        r"\bif\s*\(\s*false\s*\)",
        r"\bif\s+constexpr\s*\(\s*false\s*\)",
        r"\bwhile\s*\(\s*false\s*\)",
    )
    for index, text in enumerate(body):
        line_number = first_line + index
        code = text.split("//", 1)[0].strip()
        if code.startswith("#if"):
            expression = code[3:].strip()
            if expression not in {"0", "1"}:
                return False, f"unsupported_preprocessor_condition_at_line_{line_number}"
            preprocessor.append(expression == "1")
            continue
        if code.startswith("#else"):
            if not preprocessor:
                return False, f"unmatched_preprocessor_else_at_line_{line_number}"
            preprocessor[-1] = not preprocessor[-1]
            continue
        if code.startswith("#endif"):
            if not preprocessor:
                return False, f"unmatched_preprocessor_endif_at_line_{line_number}"
            preprocessor.pop()
            continue
        if line_number == anchor_line:
            if preprocessor and not all(preprocessor):
                return False, "anchor_in_inactive_preprocessor_branch"
            if any(brace_dead) or pending_dead:
                return False, "anchor_in_statically_dead_branch"
            return True, "supported_reachable_conditional_path"
        if any(re.search(pattern, code) for pattern in dead_patterns):
            pending_dead = True
        for char in code:
            if char == "{":
                brace_dead.append((brace_dead[-1] if brace_dead else False) or pending_dead)
                pending_dead = False
            elif char == "}":
                if not brace_dead:
                    return False, f"unsupported_brace_flow_at_line_{line_number}"
                brace_dead.pop()
        if pending_dead and ";" in code:
            pending_dead = False
    return False, "anchor_not_reached_by_control_flow_audit"


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def uint_array(value: object, length: int, maximum: int = 0xFFFFFFFF) -> bool:
    return (
        isinstance(value, list)
        and len(value) == length
        and all(type(item) is int and 0 <= item <= maximum for item in value)
    )


def fixture_gate(path: Path | None) -> dict[str, Any]:
    required = [
        "schema", "aex_sha256", "aex_binary", "identity", "geometry", "raw_artifact",
        "polar_rgba_f32_words", "validity_u8", "span_f32_words", "factor_f32_words",
        "expected_prepass_alpha_f32_words", "expected_accum_rgba_f32_words",
        "expected_max_alpha_f32_words", "expected_normalized_rgba_f32_words",
        "expected_inverse_samples",
    ]
    if path is None:
        return {
            "status": "missing_required_binary_fixture",
            "production_promotion_allowed": False,
            "required_fields": required,
            "reason": "No raw polar-plane fixture was supplied; values must not be inferred from PNGs or source.",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "status": "invalid_fixture",
            "production_promotion_allowed": False,
            "fixture": str(path),
            "errors": [f"json:{type(exc).__name__}"],
        }
    errors: list[str] = []
    if not isinstance(payload, dict):
        errors.append("root:not_object")
        payload = {}
    unknown = sorted(set(payload) - set(required))
    missing = sorted(set(required) - set(payload))
    if unknown:
        errors.append("unknown_fields:" + ",".join(unknown))
    if missing:
        errors.append("missing_fields:" + ",".join(missing))
    if payload.get("schema") != "olmradialblur.rotation-polar-plane-fixture/1":
        errors.append("schema:invalid")
    if not is_sha256(payload.get("aex_sha256")):
        errors.append("aex_sha256:invalid")

    identity = payload.get("identity")
    if not isinstance(identity, dict) or set(identity) != {"request_id", "run_id", "case_id"}:
        errors.append("identity:invalid_shape")
    elif not all(isinstance(identity[key], str) and identity[key].strip() for key in identity):
        errors.append("identity:invalid_value")

    geometry = payload.get("geometry")
    cell_count = 0
    if not isinstance(geometry, dict) or set(geometry) != {"angular_count", "radius_count"}:
        errors.append("geometry:invalid_shape")
    elif not all(type(geometry[key]) is int and geometry[key] > 0 for key in geometry):
        errors.append("geometry:invalid_value")
    else:
        cell_count = geometry["angular_count"] * geometry["radius_count"]

    lengths = {
        "polar_rgba_f32_words": cell_count * 4,
        "validity_u8": cell_count,
        "span_f32_words": cell_count,
        "factor_f32_words": cell_count,
        "expected_prepass_alpha_f32_words": cell_count,
        "expected_accum_rgba_f32_words": cell_count * 4,
        "expected_max_alpha_f32_words": cell_count,
        "expected_normalized_rgba_f32_words": cell_count * 4,
    }
    for key, length in lengths.items():
        maximum = 0xFF if key == "validity_u8" else 0xFFFFFFFF
        if cell_count <= 0 or not uint_array(payload.get(key), length, maximum):
            errors.append(f"{key}:invalid_type_or_length")

    samples = payload.get("expected_inverse_samples")
    if not isinstance(samples, list) or not samples:
        errors.append("expected_inverse_samples:invalid")
    else:
        for index, sample in enumerate(samples):
            if (
                not isinstance(sample, dict)
                or set(sample) != {"x", "y", "rgba_f32_words"}
                or type(sample.get("x")) is not int
                or type(sample.get("y")) is not int
                or not uint_array(sample.get("rgba_f32_words"), 4)
            ):
                errors.append(f"expected_inverse_samples[{index}]:invalid")

    aex_binary = payload.get("aex_binary")
    aex_bound = False
    if not isinstance(aex_binary, dict) or set(aex_binary) != {"path", "sha256"}:
        errors.append("aex_binary:invalid_shape")
    elif (
        not isinstance(aex_binary["path"], str)
        or not aex_binary["path"]
        or not is_sha256(aex_binary["sha256"])
        or aex_binary["sha256"] != payload.get("aex_sha256")
    ):
        errors.append("aex_binary:invalid_value_or_identity_mismatch")
    else:
        aex_path = Path(aex_binary["path"])
        if not aex_path.is_absolute():
            aex_path = path.parent / aex_path
        if not aex_path.is_file():
            errors.append("aex_binary:missing")
        elif hashlib.sha256(aex_path.read_bytes()).hexdigest() != aex_binary["sha256"]:
            errors.append("aex_binary:sha256_mismatch")
        else:
            aex_bound = True

    artifact = payload.get("raw_artifact")
    artifact_bound = False
    if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
        errors.append("raw_artifact:invalid_shape")
    elif not isinstance(artifact["path"], str) or not artifact["path"] or not is_sha256(artifact["sha256"]):
        errors.append("raw_artifact:invalid_value")
    else:
        artifact_path = Path(artifact["path"])
        if not artifact_path.is_absolute():
            artifact_path = path.parent / artifact_path
        if not artifact_path.is_file():
            errors.append("raw_artifact:missing")
        else:
            digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            if digest != artifact["sha256"]:
                errors.append("raw_artifact:sha256_mismatch")
            else:
                artifact_bound = True

    return {
        "status": (
            "binary_hash_bound_but_unexecuted"
            if not errors and artifact_bound and aex_bound
            else "invalid_fixture"
        ),
        "production_promotion_allowed": False,
        "fixture": str(path),
        "errors": errors,
        "aex_binary_hash_bound": aex_bound,
        "binary_artifact_hash_bound": artifact_bound,
        "reason": (
            "Raw artifact hash and schema bind, but no byte-exact executor result is part of this audit."
            if not errors else "Fixture failed strict validation and cannot authorize implementation."
        ),
    }


def analyze(asm_path: Path, mac_path: Path, fixture: Path | None) -> dict[str, Any]:
    asm = asm_path.read_text(encoding="utf-8").splitlines()
    mac_source = mac_path.read_text(encoding="utf-8")
    mac = mac_source.splitlines()

    chain = [
        evidence(asm, "180004b0f  CALL R10"),
        evidence(asm, "180004b19  MOV byte ptr [RBX + RCX*0x1],AL"),
        evidence(asm, "180004b42  CALL R10"),
        evidence(asm, "180004b72  CALL R10"),
        evidence(asm, "180004b77  MOV dword ptr [RDI],0x3f800000"),
        evidence(asm, "180004c6a  CALL 0x180002780"),
        evidence(asm, "180004cef  CALL 0x1800024c0"),
        evidence(asm, "180004d40  MOV RAX,qword ptr [RSI + 0x3c948]"),
        evidence(asm, "180004dc9  MOVSS dword ptr [RCX + RAX*0x1],XMM2"),
        evidence(asm, "180004eb9  MOV R8D,R13D"),
        evidence(asm, "180004ec3  CALL 0x180001000"),
        evidence(asm, "180004ec8  ADD RDI,0x10"),
    ]
    if not ordered(chain):
        raise ValueError("Rotation producer/sampler anchors are not in the required order")

    body_first, rotation_body = function_body(
        mac, ROTATION_SIGNATURE
    )
    rotation_body_sha256 = hashlib.sha256(
        raw_function_slice(mac_source, ROTATION_SIGNATURE)
    ).hexdigest()
    rotation_body_hash_bound = rotation_body_sha256 == EXPECTED_ROTATION_BODY_SHA256
    mac_inner = body_evidence(rotation_body, body_first, "if (info.blur_type != 2 || info.inner_strength != 0 ||")
    mac_copy = body_evidence_after(
        rotation_body, body_first, "CopyWorld<PF_Pixel8>(input, output);", mac_inner["line"], 5
    )
    mac_return = body_evidence_after(
        rotation_body, body_first, "return PF_Err_NONE;", mac_copy["line"], 2
    )
    mac_same_row = body_evidence(
        rotation_body, body_first,
        "const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;",
    )
    same_row_executable, same_row_path_reason = executable_path_supported(
        rotation_body, body_first, mac_same_row["line"]
    )
    guard_flow_bound = mac_inner["line"] < mac_copy["line"] < mac_return["line"] < mac_same_row["line"]
    mac_prepass_calls = [
        line for line in rotation_body
        if not line.lstrip().startswith("//")
        and ("FUN_180002780" in line or "FUN_1800024c0" in line)
    ]
    chain_bound = ordered(chain)
    pre_scatter_divergence = (
        chain_bound
        and rotation_body_hash_bound
        and guard_flow_bound
        and same_row_executable
        and not mac_prepass_calls
    )

    return {
        "kind": "olmradialblur_rotation_producer_contract_audit",
        "status": "pre_scatter_divergence" if pre_scatter_divergence else "evidence_not_bound",
        "inputs": {"asm": str(asm_path), "mac_source": str(mac_path)},
        "aex_chain": {
            "ordered": True,
            "anchors": chain,
            "classification": (
                "polar RGBA/validity/span/factor population -> prepass -> scatter -> "
                "normalization -> inverse sampler"
            ),
        },
        "mac_classification": {
            "raw_function_body_sha256": {
                "expected": EXPECTED_ROTATION_BODY_SHA256,
                "actual": rotation_body_sha256,
                "matches": rotation_body_hash_bound,
            },
            "inner": "copy_before_rotation_producer",
            "outer": "same_radius_row_convolution_substitutes_for_aex_prepass_scatter",
            "inner_guard": mac_inner,
            "copy": mac_copy,
            "guard_return": mac_return,
            "same_row_support": mac_same_row,
            "same_row_executable_path_bound": same_row_executable,
            "same_row_path_reason": same_row_path_reason,
            "guard_control_flow_bound": guard_flow_bound,
            "aex_prepass_or_scatter_calls_present": bool(mac_prepass_calls),
        },
        "earliest_unresolved_boundary": {
            "after": "polar plane population ending at RVA 0x4b77",
            "before": "FUN_180002780 call at RVA 0x4c6a",
            "final_sampler_is_downstream": True,
        },
        "fixture_gate": fixture_gate(fixture),
        "decision": {
            "production_edit_justified": False,
            "bounded_test_seam_justified": True,
            "required_comparison": (
                "raw float32/u8 planes through 2780 -> 24c0/1c90 -> normalize, "
                "then raw inverse-sampler float32 words"
            ),
        },
    }


def markdown(report: dict[str, Any]) -> str:
    gate = report["fixture_gate"]
    return "\n".join([
        "# OLMRadialBlur Rotation Producer Contract Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Fixture gate: `{gate['status']}`",
        "- Production edit justified: `false`",
        "- Earliest boundary: after polar population `0x4b77`, before prepass call `0x4c6a`.",
        "- AEX order: `4b0f..4b77 -> 2780@4c6a -> 24c0@4cef -> "
        "normalize 4d40..4dc9 -> inverse sampler 4eb9/4ec3/4ec8`.",
        "- Current Mac Inner copies before this producer; outer Rotation uses same-row convolution.",
        "",
        "No fixture values are synthesized. Production promotion requires a separately supplied, "
        "identity-bound raw-plane fixture and byte-exact executor result.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asm", type=Path, default=DEFAULT_ASM)
    parser.add_argument("--mac-source", type=Path, default=DEFAULT_MAC)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.asm, args.mac_source, args.fixture)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    return 0 if report["status"] == "pre_scatter_divergence" else 2


if __name__ == "__main__":
    raise SystemExit(main())
