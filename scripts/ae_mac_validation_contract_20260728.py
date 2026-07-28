"""Pure validation primitives for Mac AE exact-conformance runners.

This module does not launch AE.  Most validators are pure. Bundle identity is
deliberately filesystem-aware so that it can reject symlink escapes: runners
still supply the observed SHA, while this module resolves the existing bundle
and Mach-O paths and checks their containment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SOFTWARE_RENDERER_RAW = 1816
SIDECAR_KIND = "olm_mac_ae_evalfile_sidecar"
SIDECAR_SCHEMA_VERSION = 1
RAW_FLOAT32 = "FLOAT32"


class ContractViolation(ValueError):
    """An observed Mac validation contract is incomplete or inconsistent."""


def _require_plain_int(value: Any, field: str) -> int:
    # bool is an int subclass, but never a valid AE numeric readback.
    if type(value) is not int:
        raise ContractViolation(f"{field} must be a numeric integer readback")
    return value


def _require_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise ContractViolation(f"{field} must be boolean")
    return value


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractViolation(f"{field} must be a non-empty string")
    return value


def _require_sha256(value: Any, field: str) -> str:
    digest = _require_nonempty_string(value, field).lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ContractViolation(f"{field} must be a 64-character SHA-256 hex digest")
    return digest


def normalize_working_space_raw(value: Any) -> None:
    """Normalize AE's two observed raw representations of no working space."""

    if value in ("", None):
        return None
    raise ContractViolation("working_space_raw must be the raw empty string or null")


@dataclass(frozen=True)
class ProjectContract:
    bits_per_channel_raw: int
    renderer_raw: int
    working_space_raw: None
    linear_blending: bool


def validate_project_contract(observed: Mapping[str, Any], *, expected_bpc: int) -> ProjectContract:
    expected_bpc = _require_plain_int(expected_bpc, "expected_bpc")
    if expected_bpc not in (8, 16, 32):
        raise ContractViolation("expected_bpc must be one of 8, 16, or 32")
    bpc = _require_plain_int(observed.get("bits_per_channel_raw"), "bits_per_channel_raw")
    renderer = _require_plain_int(observed.get("renderer_raw"), "renderer_raw")
    linear = _require_bool(observed.get("linear_blending"), "linear_blending")
    working = normalize_working_space_raw(observed.get("working_space_raw"))
    if bpc != expected_bpc:
        raise ContractViolation(f"bits_per_channel_raw drift: expected {expected_bpc}, got {bpc}")
    if renderer != SOFTWARE_RENDERER_RAW:
        raise ContractViolation(
            f"renderer_raw drift: expected SOFTWARE {SOFTWARE_RENDERER_RAW}, got {renderer}"
        )
    if linear:
        raise ContractViolation("linear_blending must be false")
    return ProjectContract(bpc, renderer, working, linear)


@dataclass(frozen=True)
class MacBundleIdentity:
    bundle_path: str
    macho_path: str
    macho_sha256: str


def validate_mac_bundle_identity(observed: Mapping[str, Any]) -> MacBundleIdentity:
    """Validate an existing bundle identity, keyed by its Mach-O SHA.

    Both declared paths must be absolute and lexically traversal-free. Their
    resolved filesystem targets are then checked so a symlinked Mach-O cannot
    escape the resolved bundle.
    """

    bundle_path = _require_nonempty_string(observed.get("bundle_path"), "bundle_path")
    macho_path = _require_nonempty_string(observed.get("macho_path"), "macho_path")
    digest = _require_sha256(observed.get("macho_sha256"), "macho_sha256")
    bundle_declared = Path(bundle_path)
    macho_declared = Path(macho_path)
    if not bundle_declared.is_absolute() or not macho_declared.is_absolute():
        raise ContractViolation("bundle_path and macho_path must be absolute")
    if ".." in bundle_declared.parts or ".." in macho_declared.parts:
        raise ContractViolation("bundle_path and macho_path must not contain traversal")
    try:
        bundle_resolved = bundle_declared.resolve(strict=True)
        macho_resolved = macho_declared.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractViolation(f"bundle or Mach-O path cannot be resolved: {exc}") from exc
    if not bundle_resolved.is_dir():
        raise ContractViolation("bundle_path must resolve to an existing directory")
    if not macho_resolved.is_file():
        raise ContractViolation("macho_path must resolve to an existing file")
    try:
        relative = macho_resolved.relative_to(bundle_resolved)
    except ValueError as exc:
        raise ContractViolation("macho_path must resolve inside bundle_path") from exc
    relative_parts = relative.parts
    if len(relative_parts) != 3 or relative_parts[:2] != ("Contents", "MacOS"):
        raise ContractViolation("macho_path must identify a bundle Contents/MacOS binary")
    return MacBundleIdentity(str(bundle_resolved), str(macho_resolved), digest)


@dataclass(frozen=True)
class EvalFileSidecar:
    eval_file_path: str
    eval_file_sha256: str
    wrapper_path: str
    wrapper_sha256: str


def validate_evalfile_sidecar(sidecar: Mapping[str, Any]) -> EvalFileSidecar:
    """Validate the versioned attestation for the JSX passed to ``$.evalFile``."""

    allowed = {
        "kind",
        "schema_version",
        "eval_file_path",
        "eval_file_sha256",
        "wrapper_path",
        "wrapper_sha256",
    }
    extra = set(sidecar) - allowed
    missing = allowed - set(sidecar)
    if missing or extra:
        raise ContractViolation(
            f"evalFile sidecar fields invalid; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if sidecar["kind"] != SIDECAR_KIND:
        raise ContractViolation(f"evalFile sidecar kind must be {SIDECAR_KIND!r}")
    version = _require_plain_int(sidecar["schema_version"], "sidecar.schema_version")
    if version != SIDECAR_SCHEMA_VERSION:
        raise ContractViolation(
            f"evalFile sidecar schema_version must be {SIDECAR_SCHEMA_VERSION}"
        )
    return EvalFileSidecar(
        _require_nonempty_string(sidecar["eval_file_path"], "sidecar.eval_file_path"),
        _require_sha256(sidecar["eval_file_sha256"], "sidecar.eval_file_sha256"),
        _require_nonempty_string(sidecar["wrapper_path"], "sidecar.wrapper_path"),
        _require_sha256(sidecar["wrapper_sha256"], "sidecar.wrapper_sha256"),
    )


@dataclass(frozen=True)
class RawFloat32Gate:
    word_count: int
    mismatched_words: int
    max_raw_u32_delta: int

    @property
    def exact(self) -> bool:
        return self.mismatched_words == 0 and self.max_raw_u32_delta == 0


def _validate_gate(value: Any, field: str) -> RawFloat32Gate:
    if not isinstance(value, Mapping):
        raise ContractViolation(f"{field} must be an object")
    if value.get("sample_type") != RAW_FLOAT32:
        raise ContractViolation(f"{field}.sample_type must be {RAW_FLOAT32}")
    words = _require_plain_int(value.get("word_count"), f"{field}.word_count")
    mismatches = _require_plain_int(value.get("mismatched_words"), f"{field}.mismatched_words")
    delta = _require_plain_int(value.get("max_raw_u32_delta"), f"{field}.max_raw_u32_delta")
    if words <= 0 or not 0 <= mismatches <= words or delta < 0:
        raise ContractViolation(f"{field} contains invalid comparison counts")
    if (mismatches == 0) != (delta == 0):
        raise ContractViolation(f"{field} mismatch count and max delta disagree")
    return RawFloat32Gate(words, mismatches, delta)


@dataclass(frozen=True)
class RawFloat32CrossHostGates:
    control_cross_host: RawFloat32Gate
    effect_cross_host: RawFloat32Gate
    windows_effect_vs_control: RawFloat32Gate
    mac_effect_vs_control: RawFloat32Gate
    expected_noop: bool


def validate_raw_float32_cross_host_gates(
    observed: Mapping[str, Any],
) -> RawFloat32CrossHostGates:
    """Require exact cross-host control/effect gates and reject undeclared no-ops."""

    expected_noop = _require_bool(observed.get("expected_noop"), "expected_noop")
    result = RawFloat32CrossHostGates(
        _validate_gate(observed.get("control_cross_host"), "control_cross_host"),
        _validate_gate(observed.get("effect_cross_host"), "effect_cross_host"),
        _validate_gate(
            observed.get("windows_effect_vs_control"), "windows_effect_vs_control"
        ),
        _validate_gate(observed.get("mac_effect_vs_control"), "mac_effect_vs_control"),
        expected_noop,
    )
    counts = {
        result.control_cross_host.word_count,
        result.effect_cross_host.word_count,
        result.windows_effect_vs_control.word_count,
        result.mac_effect_vs_control.word_count,
    }
    if len(counts) != 1:
        raise ContractViolation("all raw FLOAT32 gates must compare the same word count")
    if not result.control_cross_host.exact:
        raise ContractViolation("raw FLOAT32 no-effect control is not cross-host exact")
    if not result.effect_cross_host.exact:
        raise ContractViolation("raw FLOAT32 effect-on output is not cross-host exact")
    windows_noop = result.windows_effect_vs_control.exact
    mac_noop = result.mac_effect_vs_control.exact
    if windows_noop != mac_noop:
        raise ContractViolation("hosts disagree whether the declared effect case is a no-op")
    if expected_noop != windows_noop:
        if windows_noop:
            raise ContractViolation("effect is a no-op but expected_noop is false")
        raise ContractViolation("expected_noop is true but the effect changes raw FLOAT32 words")
    return result
