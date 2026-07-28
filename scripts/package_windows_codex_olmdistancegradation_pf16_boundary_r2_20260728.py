#!/usr/bin/env python3
"""Build the immutable r2 OLMDistanceGradation PF16 Windows boundary child."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader
    module_spec.loader.exec_module(module)
    return module


base = load(
    ROOT
    / "scripts"
    / "package_windows_codex_olmdistancegradation_pf16_boundary_20260728.py",
    "olmdg_pf16_r1_base",
)
radial = load(
    ROOT / "scripts" / "package_windows_codex_olmradialblur_case0010_20260728.py",
    "olmradialblur_ownership_source",
)

JOB_ID = "olmdistancegradation_pf16_boundary_20260728_r2"
WITNESS_ID = "olmdistancegradation-pf16-direct-boundary-v2"
RUNTIME_ID = "observed_afterfx_cdb_runtime_unpinned"
CLAIM_BOUNDARY = base.CLAIM_BOUNDARY
UNRESOLVED_BOUNDARY = (
    "field_pack_producer_conversion_export_mapping_cli_ae_and_"
    "afterfx_cdb_binary_exactness_unresolved"
)
REQUEST_ID = base.REQUEST_ID
PROJECT_ID = base.PROJECT_ID
PLUGIN_ID = base.PLUGIN_ID
AEX_SHA256 = base.AEX_SHA256
CASE_MANIFEST_SHA256 = base.CASE_MANIFEST_SHA256
REFERENCE_MANIFEST_SHA256 = base.REFERENCE_MANIFEST_SHA256
INPUT_SHA256 = base.INPUT_SHA256
CASES = base.CASES
TARGET = (
    ROOT
    / "refs"
    / "handoffs"
    / "windows_codex_batch_jobs_20260728"
    / JOB_ID
)

DISASSEMBLY = ROOT / "disasm" / "DistanceGradation.aex.asm.txt"
DISASSEMBLY_SHA256 = (
    "b830129adaf05dc2e32a357902b0a60d6cf8f0429340f8cbf869b8287507229c"
)
ENTRY_ANCHOR_LINES = (
    "181170480  MOV qword ptr [RSP + 0x8],RBX",
    "181170485  PUSH RDI",
    "181170486  SUB RSP,0xa0",
    "18117048d  CMP byte ptr [RCX + 0x90],0x0",
    "181170494  MOV RBX,RCX",
    "181170497  MOV RDI,qword ptr [RSP + 0xd0]",
    "18117049f  MOVSXD R9,EDX",
)

EVENT_IDENTITY = base.EVENT_IDENTITY
CDB_TEMPLATE = f""".effmach amd64
.expr /s masm
sxi e06d7363
.logopen /t "{{{{TRACE_PATH}}}}"
r @$t0=0;r @$t1=0;r @$t2=0;r @$t3=0;r @$t4=0;r @$t5=0
bp {{{{ADDRESS:entry}}}} ".if (@edx==0n{{{{CASE_VALUE:x}}}} && @r8d==0n{{{{CASE_VALUE:y}}}}) {{r @$t0=1;r @$t1=poi(@rsp+0x28);.printf \\"{{{{CASE_VALUE:event_prefix}}}}_ENTRY {EVENT_IDENTITY} stage=entry hook_rva=1170480 x=%u y=%u output_addr=%p in_out=%u inside_threshold=%u outside_threshold=%u use_bg=%u invert=%u render_mode=%u interp_mode=%u power_bits=0x%08x entry_refcon_register=rcx entry_x_register=edx entry_y_register=r8d entry_output_location=poi_rsp_plus_0x28 same_run=1\\\\n\\",@edx,@r8d,@$t1,dwo(@rcx+0x94),dwo(@rcx+0xb8),dwo(@rcx+0xbc),by(@rcx+0xc0),by(@rcx+0xc1),dwo(@rcx+0xc8),dwo(@rcx+0xcc),dwo(@rcx+0xd0);gu}} .else {{gc}}"
bp {{{{ADDRESS:field_read}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_FIELD {EVENT_IDENTITY} stage=direct_field_read hook_rva=117057d x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p field_addr=%p field_words_agrb=%hu,%hu,%hu,%hu direct_field_staging_word=%hu capture_semantics=direct_memory_read_not_derived same_run=1\\\\n\\",@rdi,@rcx,wo(@rcx),wo(@rcx+2),wo(@rcx+4),wo(@rcx+6),wo(@rcx+2))}};gc"
bp {{{{ADDRESS:source_read}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_SOURCE {EVENT_IDENTITY} stage=direct_source_read hook_rva=11705f1 x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p source_addr=%p source_words_agrb=%hu,%hu,%hu,%hu capture_semantics=direct_memory_read_not_derived same_run=1\\\\n\\",@rdi,@rdx,wo(@rdx),wo(@rdx+2),wo(@rdx+4),wo(@rdx+6))}};gc"
bp {{{{ADDRESS:pre_store}}}} ".if (@$t0==1 && @rdi==@$t1) {{r @$t2=(@xmm6&0xffffffff);r @$t3=(@xmm1&0xffffffff);r @$t4=(@xmm4&0xffffffff);r @$t5=(@xmm5&0xffffffff);.printf \\"{{{{CASE_VALUE:event_prefix}}}}_PRESTORE {EVENT_IDENTITY} stage=direct_pre_store hook_rva=11707f4 x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p pre_store_argb_f32_bits=0x%08x,0x%08x,0x%08x,0x%08x pre_store_argb_f32=%.9g,%.9g,%.9g,%.9g xmm_bit_extraction=masm_low32_mask capture_semantics=direct_register_bits_before_pf16_scale same_run=1\\\\n\\",@rdi,@$t2,@$t3,@$t4,@$t5,@xmm6,@xmm1,@xmm4,@xmm5)}};gc"
bp {{{{ADDRESS:stored}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_STORED {EVENT_IDENTITY} stage=direct_stored_pf16 hook_rva=117082b x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p stored_pf16_words_agrb=%hu,%hu,%hu,%hu capture_semantics=direct_output_memory_after_four_stores same_run=1\\\\n\\",@rdi,wo(@rdi),wo(@rdi+2),wo(@rdi+4),wo(@rdi+6);.detach;q}};gc"
.echo OLMDG_PF16_DIRECT_BREAKPOINTS_ARMED
g
"""


TYPED_VALIDATOR = r'''#!/usr/bin/env python3
"""Fail-closed typed validation for the direct DG PF16 return."""
import argparse
import json
import math
import re
import struct
from pathlib import Path

WORD_FIELDS = (
    "field_words_agrb",
    "direct_field_staging_word",
    "source_words_agrb",
    "stored_pf16_words_agrb",
)
WORD_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
BITS_RE = re.compile(r"0x[0-9a-fA-F]{8}\Z", re.ASCII)


def parse_words(value, count, label):
    if not isinstance(value, str):
        raise ValueError(f"{label}: not a string")
    parts = value.split(",")
    if len(parts) != count:
        raise ValueError(f"{label}: expected {count} words")
    words = []
    for part in parts:
        if WORD_RE.fullmatch(part) is None:
            raise ValueError(f"{label}: malformed decimal word")
        word = int(part, 10)
        if not 0 <= word <= 32768:
            raise ValueError(f"{label}: PF16 word outside 0..32768")
        words.append(word)
    return words


def validate_float_pair(fields, label):
    bit_tokens = fields.get("pre_store_argb_f32_bits", "").split(",")
    text_tokens = fields.get("pre_store_argb_f32", "").split(",")
    if len(bit_tokens) != 4 or len(text_tokens) != 4:
        raise ValueError(f"{label}: expected four float lanes")
    for lane, (bit_token, text_token) in enumerate(zip(bit_tokens, text_tokens)):
        if BITS_RE.fullmatch(bit_token) is None:
            raise ValueError(f"{label}: malformed float bits lane {lane}")
        bits = int(bit_token[2:], 16)
        decoded = struct.unpack("<f", struct.pack("<I", bits))[0]
        if not math.isfinite(decoded):
            raise ValueError(f"{label}: non-finite bit pattern forbidden")
        try:
            textual = float(text_token)
            packed = struct.unpack("<I", struct.pack("<f", textual))[0]
        except (ValueError, OverflowError, struct.error):
            raise ValueError(f"{label}: malformed/out-of-range float text lane {lane}")
        if not math.isfinite(textual):
            raise ValueError(f"{label}: non-finite float text forbidden")
        if packed != bits:
            raise ValueError(f"{label}: float text/bits mismatch lane {lane}")


def validate_document(document):
    if document.get("status") != "answered":
        raise ValueError("direct return is not answered")
    events = document.get("events")
    if not isinstance(events, list) or len(events) != 30:
        raise ValueError("expected exactly 30 direct events")
    names = set()
    word_scalars = 0
    float_lanes = 0
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not isinstance(event.get("fields"), dict):
            raise ValueError(f"event[{index}]: malformed record")
        name = event.get("event")
        if not isinstance(name, str) or name in names:
            raise ValueError(f"event[{index}]: missing/duplicate event name")
        names.add(name)
        fields = event["fields"]
        for field in WORD_FIELDS:
            if field in fields:
                count = 1 if field == "direct_field_staging_word" else 4
                parse_words(fields[field], count, f"{name}.{field}")
                word_scalars += count
        if "pre_store_argb_f32_bits" in fields or "pre_store_argb_f32" in fields:
            validate_float_pair(fields, name)
            float_lanes += 4
    if word_scalars != 78:
        raise ValueError(f"typed PF16 cardinality mismatch: {word_scalars}")
    if float_lanes != 24:
        raise ValueError(f"typed float cardinality mismatch: {float_lanes}")
    return {
        "schema_version": 1,
        "status": "accepted",
        "event_count": 30,
        "pf16_word_scalar_count": word_scalars,
        "float32_lane_count": float_lanes,
        "pf16_range": "inclusive_0_32768",
        "float_policy": "finite_float32_only_and_text_must_roundtrip_to_declared_bits",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = validate_document(json.loads(args.input.read_text(encoding="utf-8-sig")))
        code = 0
    except Exception as exc:
        result = {"schema_version": 1, "status": "rejected", "reason": str(exc)}
        code = 2
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label} anchor count is {text.count(old)}, expected 1")
    return text.replace(old, new, 1)


def make_root_runner() -> str:
    text = base.FAIL_CLOSED_RUNNER
    replacements = (
        ("work_pf16_boundary_r1", "work_pf16_boundary_r2", "work directory"),
        (base.WITNESS_ID, WITNESS_ID, "witness id"),
        (base.RUNTIME_ID, RUNTIME_ID, "runtime id"),
        (base.UNRESOLVED_BOUNDARY, UNRESOLVED_BOUNDARY, "unresolved boundary"),
        (
            "$expectedAeVersion = '25.2x131'\n",
            "",
            "unpinned AE version",
        ),
        (
            "    if ([string]$row.ae_version -cne $expectedAeVersion) {\n"
            "      throw \"AE application identity mismatch for $caseId: $([string]$row.ae_version)\"\n"
            "    }\n",
            "",
            "AE exact check",
        ),
        (
            "      expected_app_version=$expectedAeVersion\n",
            "      attestation_role='observed_not_pinned'\n",
            "AE attestation role",
        ),
        (
            "      product_version=[string]$cdbItem.VersionInfo.ProductVersion\n",
            "      product_version=[string]$cdbItem.VersionInfo.ProductVersion\n"
            "      attestation_role='observed_not_pinned'\n",
            "CDB attestation role",
        ),
        (
            "    cases = $aeResults\n"
            "    claim_boundary = $claimBoundary\n"
            "    unresolved_boundary = $unresolvedBoundary\n",
            "    cases = $aeResults\n"
            "    claim_boundary = $claimBoundary\n"
            "    runtime_binary_exact = $false\n"
            "    runtime_attestation_role = 'observed_not_pinned'\n"
            "    unresolved_boundary = $unresolvedBoundary\n",
            "attestation exactness",
        ),
        (
            "  if ($process.ExitCode -ne 0 -or [string]$parsed.status -cne 'answered') {\n",
            "  $cleanupSource = Join-Path $run.FullName 'ownership_cleanup.json'\n"
            "  Copy-Direct $cleanupSource 'OWNERSHIP_CLEANUP.json' $true | Out-Null\n"
            "  Copy-Direct (Join-Path $run.FullName 'launch_ownership_context.json') 'LAUNCH_OWNERSHIP_CONTEXT.json' $true | Out-Null\n"
            "  Copy-Direct (Join-Path $run.FullName 'owned_afterfx_process.json') 'OWNED_AFTERFX_PROCESS.json' $true | Out-Null\n"
            "  Copy-Direct (Join-Path $run.FullName 'owned_cdb_process.json') 'OWNED_CDB_PROCESS.json' $true | Out-Null\n"
            "  $cleanup = Get-Content -LiteralPath $cleanupSource -Raw -ErrorAction Stop | ConvertFrom-Json\n"
            "  if ([bool]$cleanup.cleanup_unresolved) { throw 'cleanup_unresolved; no ambiguous or user PID was touched' }\n"
            "  $typedValidator = Join-Path $PackageRoot 'scripts\\validate_direct_boundary.py'\n"
            "  $typedOutput = Join-Path $evidenceRoot 'DIRECT_TYPED_VALIDATION.json'\n"
            "  $typedProcess = Start-Process -FilePath 'py.exe' -ArgumentList @('-3',('\"' + $typedValidator + '\"'),('\"' + (Join-Path $evidenceRoot 'DIRECT_BOUNDARY_RETURN.json') + '\"'),('\"' + $typedOutput + '\"')) -PassThru -Wait -WindowStyle Hidden -ErrorAction Stop\n"
            "  $typed = Get-Content -LiteralPath $typedOutput -Raw -ErrorAction Stop | ConvertFrom-Json\n"
            "  if ($typedProcess.ExitCode -ne 0 -or [string]$typed.status -cne 'accepted') { throw \"typed direct validation failed: $([string]$typed.reason)\" }\n"
            "  if ($process.ExitCode -ne 0 -or [string]$parsed.status -cne 'answered') {\n",
            "typed and cleanup validation",
        ),
        (
            "    cli_exact = $false\n"
            "    ae_exact = $false\n"
            "    production_change_authorized = $false\n",
            "    cli_exact = $false\n"
            "    ae_exact = $false\n"
            "    runtime_binary_exact = $false\n"
            "    runtime_attestation_role = 'observed_not_pinned'\n"
            "    cleanup_unresolved = $false\n"
            "    typed_direct_validation = 'accepted'\n"
            "    production_change_authorized = $false\n",
            "answered limitations",
        ),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text


FAIL_CLOSED_RUNNER = make_root_runner()


def validate_entry_cdb_source(source: str) -> None:
    entry = next(
        (line for line in source.splitlines() if line.startswith("bp {{ADDRESS:entry}}")),
        "",
    )
    if not entry:
        raise ValueError("entry breakpoint missing")
    if "@rbx" in entry.lower():
        raise ValueError("RBX is invalid at the entry hook; config/refcon must use RCX")
    required = ("@rcx+0x94", "@edx", "@r8d", "poi(@rsp+0x28)")
    missing = [token for token in required if token not in entry]
    if missing:
        raise ValueError(f"entry breakpoint register contract missing: {missing}")


def verify_anchor() -> dict[str, Any]:
    if base.sha256_file(DISASSEMBLY) != DISASSEMBLY_SHA256:
        raise RuntimeError("DistanceGradation disassembly anchor drifted")
    source = DISASSEMBLY.read_text(encoding="utf-8")
    missing = [line for line in ENTRY_ANCHOR_LINES if line not in source]
    if missing:
        raise RuntimeError(f"entry disassembly lines drifted: {missing}")
    validate_entry_cdb_source(CDB_TEMPLATE)
    return {
        "schema_version": 1,
        "source": "disasm/DistanceGradation.aex.asm.txt",
        "source_sha256": DISASSEMBLY_SHA256,
        "aex_sha256": AEX_SHA256,
        "entry_rva": "0x1170480",
        "excerpt": list(ENTRY_ANCHOR_LINES),
        "register_contract": {
            "refcon_config": "RCX at entry before 0x181170494 MOV RBX,RCX",
            "x": "EDX",
            "y": "R8D (callback contract)",
            "output": "poi(RSP+0x28), fifth argument at entry",
            "forbidden_entry_alias": "RBX",
        },
    }


def configure_base() -> None:
    base.JOB_ID = JOB_ID
    base.WITNESS_ID = WITNESS_ID
    base.RUNTIME_ID = RUNTIME_ID
    base.UNRESOLVED_BOUNDARY = UNRESOLVED_BOUNDARY
    base.TARGET = TARGET
    base.CDB_TEMPLATE = CDB_TEMPLATE
    base.FAIL_CLOSED_RUNNER = FAIL_CLOSED_RUNNER


def finalize_compiled_package(package_dir: Path, package_zip: Path) -> None:
    radial.patch_inner_runner(package_dir)
    (package_dir / "run.ps1").write_text(
        FAIL_CLOSED_RUNNER, encoding="ascii", newline="\n"
    )
    scripts_dir = package_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / "validate_direct_boundary.py").write_text(
        TYPED_VALIDATOR, encoding="ascii", newline="\n"
    )
    anchors_dir = package_dir / "anchors"
    anchors_dir.mkdir(exist_ok=True)
    (anchors_dir / "entry_1170480.json").write_bytes(
        base.canonical_json(verify_anchor())
    )
    (package_dir / "README.md").write_text(
        f"""# OLMDistanceGradation PF16 direct boundary r2

The only supported entrypoint is the package-root `run.ps1`. Do not invoke
`artifacts/run_witness.ps1` directly; it is an `internal_not_entrypoint`
implementation detail whose exact-owned AE/CDB lifecycle is coordinated by the
root wrapper.

An `answered` status proves only direct observations from the hash-pinned AEX at
the six bound coordinates: PF16 field/source words, finite normalized pre-store
float32 register bits whose text round-trips to those bits, and stored PF16
words. Every PF16 word is typed and range-checked in inclusive `0..32768`.

AfterFX.exe and cdb.exe paths, hashes, and file versions are recorded as
`observed_not_pinned`; their binary exactness is not established. The boundary
`{UNRESOLVED_BOUNDARY}` remains unresolved. This package makes no conversion,
export, CLI, AE-exact, nearest-even, or production-change claim.

Cleanup is limited to exact package-owned processes after request/run/project,
scheduled-task, PID, executable path/hash, and creation-time revalidation.
Ambiguity yields `cleanup_unresolved` and touches no ambiguous or user PID.
""",
        encoding="ascii",
        newline="\n",
    )
    manifest_path = package_dir / "package-manifest.json"
    generated = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = []
    for path in sorted(
        (
            item
            for item in package_dir.rglob("*")
            if item.is_file() and item != manifest_path
        ),
        key=lambda item: item.relative_to(package_dir).as_posix(),
    ):
        inventory.append(
            {
                "path": path.relative_to(package_dir).as_posix(),
                "sha256": base.sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest = {
        "schema_version": 1,
        "kind": "windows_witness_generated_package",
        "request_id": REQUEST_ID,
        "contract": "witness-contract.json",
        "entrypoint": "run.ps1",
        "internal_runner": {
            "path": "artifacts/run_witness.ps1",
            "role": "internal_not_entrypoint",
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "unresolved_boundary": UNRESOLVED_BOUNDARY,
        "runtime_binary_exact": False,
        "runtime_attestation_role": "observed_not_pinned",
        "case_manifest_sha256": CASE_MANIFEST_SHA256,
        "reference_manifest_sha256": REFERENCE_MANIFEST_SHA256,
        "files": inventory,
    }
    if "queue" in generated:
        manifest["queue"] = generated["queue"]
    manifest_path.write_bytes(base.canonical_json(manifest))
    base.deterministic_zip(package_dir, package_zip)


def build_bytes(work: Path) -> tuple[bytes, bytes, bytes]:
    configure_base()
    verify_anchor()
    spec_path = base.prepare_sources(work)
    package_dir = work / "compiled"
    package_zip = work / "package.zip"
    base.compile_witness(spec_path, package_dir, package_zip)
    finalize_compiled_package(package_dir, package_zip)
    package = package_zip.read_bytes()
    package_sha = hashlib.sha256(package).hexdigest()
    manifest = {
        "schema": "windows_codex_batch_job_v1",
        "job_id": JOB_ID,
        "package": "package.zip",
        "package_sha256": package_sha,
        "entrypoint": "run.ps1",
        "failure_policy": "independent",
        "success_status": "answered",
        "failure_status": "exact_bind_failure",
        "request_id": REQUEST_ID,
        "description": (
            "DG PF16 direct r2 with RCX entry anchor, typed finite/range "
            "validation, exact-owned cleanup, and observed-unpinned host tools."
        ),
    }
    return (
        package,
        base.canonical_json(manifest),
        f"{package_sha}  package.zip\n".encode("ascii"),
    )


def result(package: bytes) -> dict[str, Any]:
    return {
        "status": "verified",
        "job_id": JOB_ID,
        "request_id": REQUEST_ID,
        "package_sha256": hashlib.sha256(package).hexdigest(),
        "claim_boundary": CLAIM_BOUNDARY,
        "unresolved_boundary": UNRESOLVED_BOUNDARY,
        "target": str(TARGET),
    }


def build_target() -> dict[str, Any]:
    if TARGET.exists():
        raise RuntimeError(f"immutable target already exists: {TARGET}; use --verify")
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_r2_") as tmp:
        built = build_bytes(Path(tmp))
    TARGET.mkdir(parents=True)
    for name, data in zip(
        ("package.zip", "job_manifest.json", "package.zip.sha256"), built
    ):
        (TARGET / name).write_bytes(data)
    return result(built[0])


def verify_target() -> dict[str, Any]:
    paths = (
        TARGET / "package.zip",
        TARGET / "job_manifest.json",
        TARGET / "package.zip.sha256",
    )
    if any(not path.is_file() for path in paths):
        raise RuntimeError("immutable r2 child target is incomplete")
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_r2_verify_") as tmp:
        expected = build_bytes(Path(tmp))
    actual = tuple(path.read_bytes() for path in paths)
    if actual != expected:
        raise RuntimeError("immutable r2 child drifted from deterministic build")
    return result(actual[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    value = verify_target() if args.verify else build_target()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
