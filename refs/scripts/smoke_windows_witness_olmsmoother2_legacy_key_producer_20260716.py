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
            event("S2_PRODUCER_BIND", "bind", "x=91 y=841 idx=105 expected_descriptor_hint=91,841,1,91,843,5 writer_hook_rva=350b binding_expression=writer_xy_anchor_then_producer_return_address pointer_context=rsp+0x34_x_rsp+0x38_y"),
            event("S2_UPSTREAM_C280", "c280_entry", "hook_rva=c280 caller_x=91 caller_y=841 source_plane=0x2800 class_plane=0x3000 class_stride=7680 cplane_w=1920 cplane_h=1080 config_pointer=0x4000 index_inputs=unavailable index_inputs_proven=false"),
            event("S2_UPSTREAM_10760", "cardinal_10760", "hook_rva=10760 starting_center=92,841 class_plane=0x3000 class_stride=7680 cplane_w=1920 cplane_h=1080 scanner_grid=stack_local"),
            event("S2_UPSTREAM_D3B0", "d3b0_entry", "hook_rva=d3b0 input_xy=92,841 input_third=unavailable result_triple=deferred_to_fef0_descriptor"),
            event("S2_UPSTREAM_DA50", "da50_entry", "hook_rva=da50 input_xy=92,841 input_third=unavailable result_triple=deferred_to_fef0_descriptor"),
            event("S2_UPSTREAM_FEF0", "fef0_entry", "hook_rva=fef0 descriptor_before=92,841,1,92,842,2 d3b0_return_triple=92,841,1 da50_return_triple=92,842,2 return_triples_source=fef0_p2_descriptor_before dispatch_key=20 dispatch_key_expression=(p2[2]-1)+p2[5]*10"),
            event("S2_PRODUCER_E170_ENTRY", "e170_entry", "hook_rva=e170 return_address=0x2000 p2_ptr=0x2800 descriptor=92,841,1,92,842,2 sample_x=92 sample_y=841 cplane_w=1920 cplane_h=1080 class_base=0x3000 class_stride=7680 center_addr=0xdead prev_addr=0xbeef left_addr=0xcafe center_b0=255 prev_b0=255 left_b1=255 class_base_offset=18 class_stride_offset=28 p2_source=rdx"),
            event("S2_PRODUCER_E170_RETURN", "e170_return", "hook_rva=e170 return_site=f284 return_rax=0x7 e170_c=7"),
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
