#!/usr/bin/env python3
"""Join actual AEX classifier/worker to production EffectMain and installed identity."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
from olm_installed_identity import verified_binary
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_effectmain_pf16_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_effectmain_pf16_chain_installed_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_effectmain_pf16_chain_installed_20260805.md'
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 BINARY,identity=verified_binary('OLMSmoother2');INSTALLED=BINARY.parents[2];installed_sha=identity['sha256'];arch=subprocess.run(['lipo','-archs',str(BINARY)],check=True,text=True,capture_output=True).stdout.split();req(set(arch)=={'arm64','x86_64'},'installed architectures')
 with tempfile.TemporaryDirectory(prefix='sm2entry16_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);out=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout.strip().split()[1]
 px=[(0,0,0,1),(0,1,1,1),(1,0,1,1),(1,1,0,1),(.25,.25,.25,1),(.75,.75,.75,1)];px=[tuple(typed.f32(v) for v in q) for q in px];raw,plane,linear,ci,wi=v2.actual('PF16',px,6);req(raw.hex()==out,'EffectMain PF16 mismatch');req(raw[24:30]==b'\xa5'*6 and raw[54:60]==b'\xa5'*6,'padding')
 report={'verdict':'PASS_ACTUAL_AEX_CLASSIFIER_WORKER_TO_PRODUCTION_EFFECTMAIN_PF16_INSTALLED_IDENTITY','closed_boundary':'production PF_Cmd_RENDER EffectMain -> depth dispatch -> RenderBits, joined byte-exactly to actual AEX natural classifier -> PF16 worker -> writer','chain':['production EffectMain(PF_Cmd_RENDER)','PF_WORLD_IS_DEEP -> RenderBits<PF_Pixel16>','actual AEX natural classifier','actual AEX PF16 typed worker/writer','byte-exact padded output','current installed Universal bundle identity'], 'actual_aex_sha256':typed.AEX_SHA256,'production_source_sha256':sha(SOURCE),'installed':{'path':str(INSTALLED),'binary_sha256':installed_sha,'architectures':arch,'identity_manifest':str(identity['plugin'])},'fixture':{'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi},'remaining_largest_boundary':'AE process load/binding of the installed hash and real host command invocation; AE was not operated in this task','claims_not_made':['No AE host execution','No actual-AEX exported entry invocation in this synthetic classifier fixture','No PF32 production EffectMain dynamic callback chain in this report']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 PF16 EffectMain-to-installed chain\n\nVerdict: `'+report['verdict']+'`\n\nThis closes the production `EffectMain(PF_Cmd_RENDER) -> PF16 depth dispatch -> RenderBits` gap and joins its padded bytes to the natural actual-AEX classifier/PF16 worker/writer fixture. The installed Universal bundle identity remains pinned to `'+installed_sha+'`.\n\nThe remaining maximum boundary is real AE process loading/binding and host command invocation. AE was not operated. Actual-AEX exported entry invocation and PF32 SmartRender callbacks remain separate claims.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
