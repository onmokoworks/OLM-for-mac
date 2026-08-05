#!/usr/bin/env python3
"""Pin the actual AEX SmartPreRender/SmartRender command dispatch boundary."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[2];AEX=ROOT/"aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex";DECOMP=ROOT/"decomp/OLMToonDilate.aex.c.txt"
REPORT=ROOT/"refs/conformance/olmtoondilate_actual_aex_smartrender_entrypoint_20260805.json";MARKDOWN=REPORT.with_suffix(".md")
AEX_SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3";ENTRY=0x1801ABC00;VTABLE=0x180311E18;PRE=0x1801A5940;RENDER=0x1801A5970
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 pe=pefile.PE(str(AEX));exports={s.name.decode():0x180000000+s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols};image=pe.get_memory_mapped_image();off=VTABLE-0x180000000
 slots={"base":hex(struct.unpack_from("<Q",image,off)[0]),"smart_pre_render_plus_0x10":hex(struct.unpack_from("<Q",image,off+0x10)[0]),"smart_render_plus_0x20":hex(struct.unpack_from("<Q",image,off+0x20)[0])}
 text=DECOMP.read_text(errors="replace");tokens=["case 0x17:","*local_a8 + 0x10","case 0x18:","*local_a8 + 0x20","FUN_1801a5970("]
 gates={"aex_sha256_exact":sha(AEX)==AEX_SHA,"entry_export_exact":exports.get("entry_point")==ENTRY,"smart_pre_vtable_exact":slots["smart_pre_render_plus_0x10"]==hex(PRE),"smart_render_vtable_exact":slots["smart_render_plus_0x20"]==hex(RENDER),"decomp_dispatch_tokens_exact":all(t in text for t in tokens)}
 status="PASS_ENTRYPOINT_DISPATCH_IDENTIFIED" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
 p={"status":status,"schema":"olmtoondilate.actual-aex-smartrender-entrypoint/1","aex":str(AEX.relative_to(ROOT)),"aex_sha256":AEX_SHA,"exports":{k:hex(v) for k,v in exports.items()},"pf_cmd_mapping":{"PF_Cmd_SMART_PRE_RENDER":0x17,"PF_Cmd_SMART_RENDER":0x18},"my_effect_vtable":hex(VTABLE),"vtable_slots":slots,"functions":{"smart_pre_render":hex(PRE),"smart_render":hex(RENDER),"typed_worker_dispatch":{"PF8":"0x1801a6150","PF16":"0x1801a5a90","PF32":"0x1801a6800"}},"gates":gates,"not_proven":["actual-AEX sequence setup succeeds under the current synthetic suite set","actual-AEX SmartPreRender checkout/result_rect host callback readback","partial-world pixel equivalence"],"next_boundary":"extend synthetic suites required by command 1 sequence setup, copy out_data+0x28 handle into in_data+0x138, then call entry_point commands 0x17 and 0x18","claim_boundary":"binary-identity-bound entrypoint and command/vtable dispatch identification only"}
 REPORT.write_text(json.dumps(p,indent=2)+"\n");MARKDOWN.write_text(f"# OLMToonDilate Actual-AEX SmartRender Entrypoint — 2026-08-05\n\n- Status: **{status}**\n- Export `entry_point`: `{hex(ENTRY)}`.\n- PF_Cmd 0x17 dispatches vtable +0x10 to `{hex(PRE)}`.\n- PF_Cmd 0x18 dispatches vtable +0x20 to `{hex(RENDER)}`.\n- Checkout/result_rect readback is not yet proved; sequence setup currently reaches a missing suite callback after allocating the 0x90-byte object.\n")
 print(json.dumps(p,indent=2));return 0 if status.startswith("PASS") else 1
if __name__=="__main__":raise SystemExit(main())
