#!/usr/bin/env python3
"""Compile/run current OLMBlur Classic PF_Cmd_RENDER through the real SDK ABI."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import hashlib,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/"tools/emulation/probe_olmblur_classic_public_real_sdk_20260813.cpp"
FIXTURE=resolve_asset(ROOT/"tools/emulation/fixtures/olmblur_amount_repeat_legacy_matrix_20260810")
SOURCE=ROOT/"mac/OLMBlur/OLMBlur.cpp"
SOURCE_SHA="22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
  assert sha(SOURCE)==SOURCE_SHA
  with tempfile.TemporaryDirectory(prefix="olmblur-classic-real-sdk.") as td:
    exe=Path(td)/"probe";sdk=subprocess.run(["xcrun","--show-sdk-path"],capture_output=True,text=True,check=True).stdout.strip()
    core=[str(ROOT/"core"/name) for name in ("olmblur_helper.cpp","olmblur_fullworker_helper.cpp","olmblur_worker16_nonlegacy.cpp","olmblur_worker16_legacy.cpp","olmblur_worker32_nonlegacy.cpp","olmblur_worker32_legacy.cpp","olmblur_worker8_legacy.cpp","olmblur_worker_orchestration.cpp")]
    cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1","-Wno-pragma-pack","-Wno-deprecated-declarations","-isysroot",sdk,"-IHeaders","-IHeaders/SP","-IUtil","-IResources","-Icore","-Imac/OLMBlur",str(PROBE),"mac/OLMBlur/OLMBlur_Strings.cpp",*core,str(resolve_asset("Util/AEGP_SuiteHandler.cpp")),str(resolve_asset("Util/MissingSuiteError.cpp")),"-framework","Cocoa","-o",str(exe)]
    subprocess.run(cmd,cwd=ROOT,check=True)
    run=subprocess.run([str(exe),str(FIXTURE)],cwd=ROOT,capture_output=True,text=True)
    if run.returncode: raise RuntimeError(run.stdout+run.stderr)
    lines=run.stdout.splitlines();assert len([x for x in lines if x.startswith("CLASSIC ")])==10
    assert lines[-1]=="all_exact=1 positive_rows=8 negative_rows=2"
    print("PASS_OLMBLUR_CLASSIC_PUBLIC_REAL_SDK_CURRENT positives=8 negatives=2")
  return 0
if __name__=="__main__":raise SystemExit(main())
