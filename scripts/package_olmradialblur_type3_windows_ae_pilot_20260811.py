#!/usr/bin/env python3
"""Create the deterministic eight-process OLMRadialBlur Type-3 AE pilot ZIP."""
from __future__ import annotations
import hashlib, importlib.util, json, shutil, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from olmradialblur_type3_pf32_pilot_contract_20260811 import (  # noqa: E402
    AEX_SHA256, contract)

WITNESS_GENERATOR = ROOT / "tools/emulation/prepare_olmradialblur_type3_windows_witness_20260811.py"

OUTPUT = ROOT / "refs/reference_requests/olmradialblur_type3_windows_ae_pilot_20260811.zip"
ZIP_TIME = (2026, 8, 11, 0, 0, 0)

def write_zip(stage: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                info=zipfile.ZipInfo(p.relative_to(stage).as_posix(), ZIP_TIME)
                info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644 << 16
                z.writestr(info, p.read_bytes())

def build(output: Path = OUTPUT) -> Path:
    aex=ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
    if hashlib.sha256(aex.read_bytes()).hexdigest()!=AEX_SHA256: raise ValueError("pinned AEX hash drift")
    with tempfile.TemporaryDirectory(prefix="olmrb_type3_") as td:
        scratch=Path(td);stage=scratch/"package"; stage.mkdir()
        spec=importlib.util.spec_from_file_location("type3_witness_v2",WITNESS_GENERATOR)
        if not spec or not spec.loader: raise ValueError("cannot load witness v2 generator")
        witness_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(witness_module)
        witness_root=scratch/"witness";witness_module.prepare(witness_root)
        witness=json.loads((witness_root/"request.json").read_text())
        fixtures={path:(witness_root/path).read_bytes() for path in
                  [witness["primary_source"]["path"],
                   *[asset["path"] for asset in witness["layers"].values()]]}
        for member,raw in fixtures.items():
            p=stage/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        p=stage/"aex/OLMRadialBlur.aex";p.parent.mkdir();shutil.copy2(aex,p)
        (stage/"WITNESS_REQUEST.json").write_text(json.dumps(witness,indent=2)+"\n")
        (stage/"BATCH_CONTRACT.json").write_text(json.dumps(contract(witness,fixtures),indent=2)+"\n")
        for source,target in (
            (ROOT/"scripts/ae_render_olmradialblur_type3_windows_ae_pilot_20260811.jsx",stage/"scripts/ae_render.jsx"),
            (ROOT/"scripts/run_olmradialblur_type3_windows_ae_pilot_20260811.ps1",stage/"RUN_WINDOWS.ps1"),
            (ROOT/"scripts/verify_olmradialblur_type3_windows_ae_pilot_20260811.py",stage/"VERIFY_RETURN.py"),
            (ROOT/"scripts/olmradialblur_type3_pf32_pilot_contract_20260811.py",stage/"tools/olmradialblur_type3_pf32_pilot_contract_20260811.py")):
            target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
        (stage/"README_WINDOWS.md").write_text(
            "# OLMRadialBlur Type 3 PF32 pilot\n\nRun `RUN_WINDOWS.ps1`. Exactly eight fresh AE 25.2x131 Software processes are used. "
            "If AE exposes `OLM RadialBlur-0021` as `NO_VALUE`, the runner stops with `NOISE_LAYER_BINDING_UNAVAILABLE`; "
            "an output made with the default None layer is never accepted.\n")
        output.parent.mkdir(parents=True,exist_ok=True);write_zip(stage,output)
    return output

if __name__=="__main__":
    p=build();print(f"[PASS] {p} sha256={hashlib.sha256(p.read_bytes()).hexdigest()}")
