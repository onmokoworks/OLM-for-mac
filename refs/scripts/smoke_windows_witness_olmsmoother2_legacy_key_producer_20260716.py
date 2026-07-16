#!/usr/bin/env python3
"""Fail-closed compile/return-validator smoke for the Smoother2 producer request."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.windows_witness.compiler import compile_witness
from tools.windows_witness.runtime import read_json, validate_trace

SPEC = ROOT / "refs/windows_witness_specs/olmsmoother2_legacy_key_producer_common_core_20260716/witness-spec.json"
CASE = "legacy_case_0012_gamma5_red_blue_current_aex"
WITNESS = "olmsmoother2-legacy-key-producer-common-core-v1"


def event(prefix: str, stage: str, extra: str = "") -> str:
    return (f"{prefix} run_id=smoke-run ae_pid=42 module_base=0x1000 "
            f"aex_sha256=7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7 "
            f"project_bpc=8 renderer=Software case_id={CASE} witness_id={WITNESS} stage={stage} {extra}").strip()


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        package, archive = compile_witness(SPEC, root / "package", root / "package.zip")
        contract = read_json(package / "witness-contract.json")
        assert archive.is_file()
        assert (package / "request" / "input" / "case_0012_before_effects.png").is_file()
        assert (package / "request" / "HOST_LIMITATION.md").is_file()
        assert "AE2025 exits" in contract["description"]
        probe = (package / "cdb" / f"000_{CASE}.cdb.in").read_text(encoding="ascii")
        assert "poi(@rcx+0x18)" in probe and "poi(@rcx+0x28)" in probe
        assert "&&" not in probe
        assert "bc {{ADDRESS:" not in probe
        assert ".if (@$t2==1) {.if (@$t1==0) {.if (poi(@rsp)=={{ADDRESS:e170_return}})" in probe
        assert ".if (@$t0==1) {.if (@$t2==0) {.if (poi(@rsp)=={{ADDRESS:f270_return}})" in probe
        assert ".if (@$t2==1) {.if (@$t3==0) {.if (poi(@rsp)=={{ADDRESS:f270_return}})" in probe
        assert "ADDRESS:e3a0_return0" in probe and "ADDRESS:e3a0_return1" in probe
        assert "hook_rva=e170 return_site=f284" in probe
        assert "hook_rva=f270 return_site=ff5b" in probe
        assert "hook_rva=e3a0 return_site=e3f4" in probe
        assert "hook_rva=e3a0 return_site=e420" in probe
        assert "vertex_storage=%p vertex_count=%u first_vertex_rgba_words=%08x,%08x,%08x,%08x weight_word=%08x" in probe
        assert "@$t10+0x40,dwo(@$t10+0x130)" in probe
        assert "first_vertex_rgba_words=%08x,%08x,%08x,%08x" in probe
        assert "weight_word=%08x" in probe
        assert "@rax+0x40,dwo(@rax+0x30)" not in probe
        common = dict(run_id="smoke-run", ae_pid=42, module_base="0x1000")
        trace = "\n".join([
            event("S2_PRODUCER_BIND", "bind", "x=91 y=841 idx=105 descriptor=91,841,1,91,843,5 writer_hook_rva=3370 binding_expression=writer_xy_anchor_then_producer_return_address pointer_context=rsp+0x34_x_rsp+0x38_y"),
            event("S2_PRODUCER_E170_ENTRY", "e170_entry", "hook_rva=e170 return_address=0x2000 class_base=0x3000 class_stride=192 center_addr=0xdead prev_addr=0xbeef left_addr=0xcafe center_b0=0 prev_b0=1 left_b1=0 class_base_offset=18 class_stride_offset=28"),
            event("S2_PRODUCER_E170_RETURN", "e170_return", "hook_rva=e170 return_site=f284 return_rax=0x2 e170_c=2"),
            event("S2_PRODUCER_F270_ENTRY", "f270_entry", "hook_rva=f270 return_address=0x2100 producer_struct=0x4000"),
            event("S2_PRODUCER_F270_RETURN", "f270_return", "hook_rva=f270 return_site=ff5b return_rax=0x1 return_low=1 vertex_storage=0x4040 vertex_count=1 first_vertex_rgba_words=00000000,00000000,00000000,00000000 weight_word=3ecccccd"),
            event("S2_PRODUCER_E3A0_ENTRY", "e3a0_entry", "hook_rva=e3a0 return_address=0x2200 producer_struct=0x4000"),
            event("S2_PRODUCER_E3A0_RETURN", "e3a0_return", "hook_rva=e3a0 return_site=e3f4 return_rax=0x1 return_low=1 vertex_storage=0x4040 vertex_count=1 first_vertex_rgba_words=3f666666,3f666666,3f666666,3f800000 weight_word=3ecccccd"),
        ]) + "\n"
        answered = validate_trace(contract, trace, common)
        assert answered["status"] == "answered", answered
        failed = validate_trace(contract, trace.replace("stage=e3a0_return", "stage=wrong"), common)
        assert failed["status"] == "exact_bind_failure"
        wrong_hook = validate_trace(contract, trace.replace("hook_rva=e170 return_site=f284", "hook_rva=f284 return_site=f284"), common)
        assert wrong_hook["status"] == "exact_bind_failure"
        wrong_f270_site = validate_trace(contract, trace.replace("return_site=ff5b", "return_site=0x2100"), common)
        assert wrong_f270_site["status"] == "exact_bind_failure"
        wrong_e3a0_site = validate_trace(contract, trace.replace("return_site=e3f4", "return_site=ff5b"), common)
        assert wrong_e3a0_site["status"] == "exact_bind_failure"
    print("[OK] OLMSmoother2 legacy producer common-core smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
