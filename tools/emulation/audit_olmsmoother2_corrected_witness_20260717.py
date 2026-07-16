#!/usr/bin/env python3
"""Machine-parsed, fail-closed audit for the corrected current-AEX witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_ALL
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP, UC_X86_REG_EAX

SOURCE_FIXTURE = ROOT / "refs/conformance/fixtures/olmsmoother2_corrected_witness_20260717/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.json"
SOURCE_METADATA = ROOT / "refs/conformance/fixtures/olmsmoother2_corrected_witness_20260717/metadata.json"
FUNCTION_FIXTURE = ROOT / "refs/conformance/fixtures/olmsmoother2_corrected_witness_20260717/FUN_18000e170.json"
SOURCE_MEMBER = "RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.json"

PINNED = {
    "source_zip_sha256": "8c031837ac6a2e95fec657cd444ca303ba3c8fb66bf2235f3c038b37e207efcf",
    "source_member_sha256": "c5f48309d9cc995f324ce7345caf8e993755db7d73e0745d36adbe252ed065bd",
    "function_code_sha256": "90503de993f8891f72003eef21eff906ff9ed5cb0be4654295549a9aebc6378d",
}

TARGET_CASE = "legacy_case_0012_gamma5_red_blue_current_aex"
TARGET_XY = (92, 841)
EVENT_ORDER = ("f270_entry", "e170_entry", "e170_return", "e3a0_entry", "e3a0_return", "f270_return")
IDENTITY_FIELDS = ("ae_pid", "aex_sha256", "case_id", "module_base", "project_bpc", "renderer", "run_id", "witness_id")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise RuntimeError("FAIL CLOSED: " + message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def parse_ints(value: str, count: int, label: str) -> list[int]:
    parts = [part.strip() for part in value.split(",")]
    require(len(parts) == count and all(re.fullmatch(r"-?\d+", part) for part in parts), f"invalid {label}: {value!r}")
    return [int(part) for part in parts]


def parse_hex(value: str, label: str) -> int:
    require(bool(re.fullmatch(r"0x[0-9a-fA-F]+", value)), f"invalid {label}: {value!r}")
    return int(value, 16)


def load_source() -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    require(SOURCE_FIXTURE.exists(), f"missing repository corrected witness member {SOURCE_FIXTURE}")
    require(SOURCE_METADATA.exists(), f"missing repository witness metadata {SOURCE_METADATA}")
    metadata = json.loads(SOURCE_METADATA.read_text(encoding="utf-8"))
    require(isinstance(metadata, dict), "witness metadata is not an object")
    require(metadata.get("source_member_name") == SOURCE_MEMBER, "fixture member name metadata mismatch")
    require(metadata.get("source_zip_name") == "RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip", "fixture ZIP name metadata mismatch")
    require(metadata.get("source_zip_role") == "provenance_attestation_only_not_clean_clone_reproof", "source ZIP role is not explicitly provenance attestation only")
    require(metadata.get("source_zip_sha256") == PINNED["source_zip_sha256"], "source ZIP hash metadata changed")
    require(metadata.get("source_member_sha256") == PINNED["source_member_sha256"], "source member hash metadata changed")
    require("91,841" not in str(metadata.get("source_zip_path", "")), "retired 91,841 source path selected")
    raw = SOURCE_FIXTURE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PINNED["source_member_sha256"], "primary witness JSON hash changed")
    payload = json.loads(raw)
    require(payload.get("status") == "answered" and payload.get("schema_version") == 1, "unsupported primary witness schema/status")
    return payload, {
        "source_zip": metadata["source_zip_sha256"],
        "source_member": hashlib.sha256(raw).hexdigest(),
        "function_code": PINNED["function_code_sha256"],
    }, metadata


def load_function_code() -> tuple[bytes, dict[str, Any]]:
    require(FUNCTION_FIXTURE.exists(), f"missing repository executable function fixture {FUNCTION_FIXTURE}")
    fixture = json.loads(FUNCTION_FIXTURE.read_text(encoding="utf-8"))
    require(isinstance(fixture, dict), "function fixture is not an object")
    require(fixture.get("function") == "FUN_18000e170", "wrong function fixture")
    require(fixture.get("code_sha256") == PINNED["function_code_sha256"], "function fixture metadata hash changed")
    code_hex = fixture.get("code_hex")
    require(isinstance(code_hex, str) and re.fullmatch(r"[0-9a-f]+", code_hex) is not None, "invalid function fixture bytes")
    code = bytes.fromhex(code_hex)
    require(hashlib.sha256(code).hexdigest() == PINNED["function_code_sha256"], "function fixture bytes hash changed")
    require(len(code) == fixture.get("code_size") == 132, "unexpected extracted function size")
    return code, fixture


def execute_function(code: bytes, class_bytes: dict[str, list[int]], descriptor: list[int]) -> int:
    """Execute the exact extracted bytes with only the function's input buffers."""
    code_base, stack_base, data_base = 0x18000E000, 0x0F000000, 0x20000000
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    uc.mem_map(code_base, 0x1000, UC_PROT_ALL)
    uc.mem_write(0x18000E170, code)
    uc.mem_map(stack_base, 0x1000, UC_PROT_ALL)
    width, height, stride = 1920, 1080, 1920 * 4
    class_addr = data_base + 0x2000
    class_plane = bytearray(stride * height)
    for (x, y), values in ((TARGET_XY, class_bytes["center"]), ((TARGET_XY[0], TARGET_XY[1] - 1), class_bytes["previous"]), ((TARGET_XY[0] - 1, TARGET_XY[1]), class_bytes["left"])):
        class_plane[y * stride + x * 4:y * stride + x * 4 + 4] = bytes(values)
    uc.mem_map(data_base, 0x2000, UC_PROT_ALL)
    uc.mem_map(data_base + 0x2000, len(class_plane), UC_PROT_ALL)
    uc.mem_write(class_addr, bytes(class_plane))
    struct_addr, desc_addr = data_base, data_base + 0x800
    uc.mem_write(struct_addr + 0x18, struct.pack("<Q", class_addr))
    uc.mem_write(struct_addr + 0x20, struct.pack("<ii", width, height))
    uc.mem_write(struct_addr + 0x28, struct.pack("<Q", stride))
    uc.mem_write(desc_addr, struct.pack("<6i", *descriptor))
    return_addr, rsp = stack_base + 0xF00, stack_base + 0xFF8
    uc.mem_write(rsp, struct.pack("<Q", return_addr))
    uc.reg_write(UC_X86_REG_RCX, struct_addr)
    uc.reg_write(UC_X86_REG_RDX, desc_addr)
    uc.reg_write(UC_X86_REG_RSP, rsp)
    uc.emu_start(0x18000E170, return_addr)
    return uc.reg_read(UC_X86_REG_EAX)


def validate_e170_addresses(fields: dict[str, Any], descriptor: list[int], sample_xy: tuple[int, int]) -> dict[str, int]:
    """Fail closed on the returned pointer relation before executing the bytes."""
    width = int(fields["cplane_w"])
    height = int(fields["cplane_h"])
    x, y = sample_xy
    require(width > 0 and height > 0, "class plane dimensions are not positive")
    require(0 <= x < width and 0 < y < height, "target sample or previous row is out of bounds")
    require(descriptor[0] == x and descriptor[1] == y, "address relation is not bound to descriptor sample")
    require(descriptor[3] == x and descriptor[4] == y + 1, "descriptor neighbor coordinates are not bound to target sample")

    parsed = {name: parse_hex(str(fields[name]), name) for name in ("class_base", "class_stride", "center_addr", "prev_addr", "left_addr")}
    base, stride = parsed["class_base"], parsed["class_stride"]
    max_u64 = (1 << 64) - 1
    require(0 < base <= max_u64 and base % 4 == 0, "class_base is not a sane aligned address")
    require(0 < stride <= 0x100000000 and stride % 4 == 0 and stride >= width * 4, "class_stride is not sane for the class plane")
    require(base + height * stride <= max_u64, "class plane address range overflows 64-bit arithmetic")
    expected = {
        "center_addr": base + y * stride + x * 4,
        "prev_addr": base + (y - 1) * stride + x * 4,
        "left_addr": base + y * stride + (x - 1) * 4 + 1,
    }
    for name, address in expected.items():
        alignment = 4 if name != "left_addr" else 1
        require(0 < parsed[name] <= max_u64 and parsed[name] % alignment == 0, f"{name} is not a sane address")
        require(parsed[name] == address, f"{name} relation mismatch: returned=0x{parsed[name]:x} expected=0x{address:x}")
        require(base <= parsed[name] < base + height * stride, f"{name} is outside the class plane")
    return {**parsed, **expected}


def select_events(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    events = payload.get("events")
    require(isinstance(events, list), "primary witness events are not a list")
    selected: dict[str, dict[str, Any]] = {}
    for item in events:
        require(isinstance(item, dict) and isinstance(item.get("fields"), dict), "malformed witness event")
        stage = item["event"]
        if stage in EVENT_ORDER:
            require(stage not in selected, f"duplicate authoritative event {stage}")
            selected[stage] = item["fields"]
    require(tuple(selected) == EVENT_ORDER, f"event order/scope mismatch: {tuple(selected)}")
    return selected


def audit() -> dict[str, Any]:
    payload, input_hashes, source_metadata = load_source()
    events = select_events(payload)
    run = payload.get("run")
    require(isinstance(run, dict), "missing run identity")

    require(all(key in run for key in ("ae_pid", "aex_sha256", "module_base", "project_bits_per_channel", "renderer", "run_id")), "incomplete run identity")
    identity = {
        "ae_pid": str(run["ae_pid"]),
        "aex_sha256": str(run["aex_sha256"]),
        "module_base": str(run["module_base"]),
        "project_bpc": str(run["project_bits_per_channel"]),
        "renderer": str(run["renderer"]),
        "run_id": str(run["run_id"]),
    }
    e170_entry = events["e170_entry"]
    e170_return = events["e170_return"]
    anchor_identity = {key: str(e170_entry[key]) for key in ("case_id", "witness_id")}
    require(anchor_identity["case_id"] == TARGET_CASE, "authoritative witness is not case_0012")
    identity.update(anchor_identity)
    for stage, fields in events.items():
        for key, expected in (("aex_sha256", identity["aex_sha256"]), ("module_base", identity["module_base"]),
                             ("project_bpc", identity["project_bpc"]), ("renderer", identity["renderer"]),
                             ("run_id", identity["run_id"]), ("case_id", anchor_identity["case_id"]),
                             ("witness_id", anchor_identity["witness_id"])):
            require(str(fields.get(key)) == expected, f"{stage} identity mismatch for {key}")
        require("ae_pid" in fields, f"{stage} is missing ae_pid")
        require(str(fields["ae_pid"]) == str(run["ae_pid"]), f"{stage} identity mismatch for ae_pid")

    descriptor = parse_ints(str(e170_entry["descriptor"]), 6, "live RDX descriptor")
    sample_xy = (int(e170_entry["sample_x"]), int(e170_entry["sample_y"]))
    require(sample_xy == TARGET_XY and tuple(descriptor[:2]) == TARGET_XY, "authoritative witness is not exactly (92,841)")
    require(91 not in descriptor, "retired x=91 descriptor selected")
    require(str(e170_entry.get("p2_source")) == "rdx", "descriptor is not sourced from live RDX")

    class_bytes = {
        "center": parse_ints(str(e170_entry["center_class_bytes"]), 4, "center class bytes"),
        "previous": parse_ints(str(e170_entry["prev_class_bytes"]), 4, "previous-row class bytes"),
        "left": parse_ints(str(e170_entry["left_class_bytes"]), 4, "left-neighbor class bytes"),
    }
    windows_previous_b0 = int(e170_entry["prev_b0"])
    require(windows_previous_b0 == class_bytes["previous"][0], "Windows previous_b0 disagrees with retained previous bytes")
    windows_c = int(e170_return["e170_c"])
    require(windows_c == (int(str(e170_return["return_rax"]), 16) & 0xFF), "Windows e170_c disagrees with return RAX")
    require(windows_c == 7, "corrected Windows e170 return is not 7")
    require(int(e170_entry["center_b0"]) == class_bytes["center"][0], "Windows center_b0 disagrees with retained bytes")
    require(int(e170_entry["left_b1"]) == class_bytes["left"][1], "Windows left_b1 disagrees with retained bytes")

    address_facts = validate_e170_addresses(e170_entry, descriptor, sample_xy)
    function_code, function_metadata = load_function_code()
    local_c = execute_function(function_code, class_bytes, descriptor)
    require(local_c == windows_c, f"extracted FUN_18000e170 mismatch: local={local_c} Windows={windows_c}")

    return {
        "verdict": "PASS_CORRECTED_E170_EXTRACTED_CODE_WITNESS_AUDIT",
        "scope": "legacy case_0012 producer e170 semantics only at x=92,y=841",
        "inputs": {
            "primary_artifact": str(SOURCE_FIXTURE.relative_to(ROOT)),
            "primary_member": SOURCE_MEMBER,
            "source_metadata": str(SOURCE_METADATA.relative_to(ROOT)),
            "original_zip_path": source_metadata["source_zip_path"],
            "original_zip_name": source_metadata["source_zip_name"],
            "source_zip_provenance_attestation": {
                "path": source_metadata["source_zip_path"],
                "name": source_metadata["source_zip_name"],
                "sha256": input_hashes["source_zip"],
                "clean_clone_reproof": False,
                "role": "provenance attestation only; not clean-clone re-proof",
            },
            "function_fixture": str(FUNCTION_FIXTURE.relative_to(ROOT)),
            "function_fixture_metadata": function_metadata,
            "hashes": {**input_hashes, "source_aex": identity["aex_sha256"]},
        },
        "parsed_windows_facts": {
            "identity": identity,
            "descriptor_rdx_p2": descriptor,
            "sample_xy": list(sample_xy),
            "class_bytes": class_bytes,
            "previous_b0": windows_previous_b0,
            "e170_c": windows_c,
            "event_order": list(EVENT_ORDER),
            "e170_address_relation": address_facts,
        },
        "local_extracted_function": {
            "function": "FUN_18000e170",
            "code_sha256": PINNED["function_code_sha256"],
            "input_bytes_source": "exact retained Windows e170 class bytes",
            "e170_c": local_c,
            "branch_logic": "previous_b0 must be nonzero",
        },
        "interpretation": [
            "The local branch logic requires previous_b0 to be nonzero.",
            "The Windows witness separately reports previous_b0=255 for this corrected run.",
        ],
        "claims_not_made": [
            "No mixed-identity bind event is used as the corrected sample identity.",
            "No claim that c280 is solved.",
            "No claim that cce0 is solved.",
            "No claim about x=91,y=841 or any ZIP carrying that retired witness.",
            "No AE exactness, full-AEX reproducibility, or final-writer claim.",
        ],
        "pass": True,
    }


def tampered_relation_self_test() -> None:
    payload, _, _ = load_source()
    fields = next(item["fields"] for item in payload["events"] if item.get("event") == "e170_entry")
    descriptor = parse_ints(str(fields["descriptor"]), 6, "live RDX descriptor")
    sample_xy = (int(fields["sample_x"]), int(fields["sample_y"]))
    tampered = copy.deepcopy(fields)
    tampered["center_addr"] = hex(int(fields["center_addr"], 16) + 4)
    try:
        validate_e170_addresses(tampered, descriptor, sample_xy)
    except RuntimeError as exc:
        require("center_addr relation mismatch" in str(exc), "tampered address was rejected for the wrong reason")
        return
    fail("tampered address relation was accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--self-test-tampered-relation", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test_tampered_relation:
            tampered_relation_self_test()
            print("PASS: tampered e170 address relation rejected")
            return 0
        result = audit()
    except (AssertionError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.output_json:
        args.output_json.write_text(rendered, encoding="utf-8")
    if args.output_md:
        facts = result["parsed_windows_facts"]
        local = result["local_extracted_function"]
        lines = [
            "# OLMSmoother2 corrected current-AEX witness audit - 2026-07-17", "",
            f"- Verdict: `{result['verdict']}`", "- Scope: `legacy_case_0012_gamma5_red_blue_current_aex`, exactly `(x=92,y=841)`.",
            "- Primary evidence is the extracted corrected returned JSON fixture; all facts below are machine-parsed.", "",
            "## Pinned Inputs", "",
        ]
        lines += [
            f"- Source ZIP provenance attestation only (not clean-clone re-proof): `{result['inputs']['original_zip_path']}` (`{result['inputs']['original_zip_name']}`)",
            f"- Extracted member: `{result['inputs']['primary_member']}`",
            f"- Fixture metadata: `{result['inputs']['source_metadata']}`",
        ]
        for key, value in result["inputs"]["hashes"].items():
            label = "source ZIP SHA-256 provenance attestation (not clean-clone re-proof)" if key == "source_zip" else key
            lines.append(f"- `{label}`: `{value}`")
        lines += [
            "", "## Parsed Windows Facts", "",
            f"- Identity: `{facts['identity']}`", f"- Live `RDX p2[0..5]`: `{facts['descriptor_rdx_p2']}`; sample: `{facts['sample_xy']}`.",
            f"- Retained class bytes: `{facts['class_bytes']}`.", f"- Windows `e170_c`: `{facts['e170_c']}`; event order: `{facts['event_order']}`.",
            f"- Validated e170 addresses: `{facts['e170_address_relation']}`; center and previous equal `class_base + y * class_stride + x * 4`, while the reported left byte equals `class_base + y * class_stride + (x - 1) * 4 + 1`.",
            "- The returned artifact also contains a retired bind hint for `91,841`; this audit does not use it as sample identity.", "",
            "## Narrow Local Check", "", f"- The extracted `FUN_18000e170` bytes were run with the exact retained class bytes and returned `{local['e170_c']}`.",
            "- Local branch logic: `previous_b0` must be nonzero.", f"- Windows witness separately reports `previous_b0={facts['previous_b0']}`.", "",
            "## Claims Not Made", "", *[f"- {claim}" for claim in result["claims_not_made"]], "",
            "## Smoke", "", "```sh", "python3 tools/emulation/audit_olmsmoother2_corrected_witness_20260717.py \\", "  --output-json refs/conformance/olmsmoother2_corrected_witness_audit_20260717.json \\", "  --output-md refs/conformance/olmsmoother2_corrected_witness_audit_20260717.md", "python3 tools/emulation/audit_olmsmoother2_corrected_witness_20260717.py --self-test-tampered-relation", "```", "",
        ]
        args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
