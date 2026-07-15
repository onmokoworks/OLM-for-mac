#!/usr/bin/env python3
"""No-AE smoke for the OLMKiraKira Mode 2 Mac runner/reporter contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/"scripts/run_olmkirakira_mode2_32bpc_mac_validation_20260715.py"
REQUEST=ROOT/"refs/mac_validation_requests/olmkirakira_mode2_32bpc_mac_validation_20260715.json"


def main() -> int:
    data=json.loads(REQUEST.read_text(encoding="utf-8")); case=data["case"]
    assert data["status"]=="sendable_fail_closed_no_ae_exact_claim"
    assert case["id"]=="final_random10_olm_kira_kira_06"
    assert len(case["effect"]["params_full"])==42
    values={p["name"]:p.get("value") for p in case["effect"]["params_full"]}
    assert values["Blur Mode"]==2 and values["Merge mode"]==1 and values["Approximated Input"]==0
    assert "raw FLOAT32 word equality" in data["comparison"]["required"]
    assert any("Mode3 Gaussian" in item for item in data["fail_closed"])
    with tempfile.TemporaryDirectory(prefix="olmkirakira_mode2_mac_smoke_") as t:
        root=Path(t); plugin=root/"OLMKiraKira.plugin"; plugin.write_bytes(b"smoke"); source=root/"input.png"; source.write_bytes(b"smoke input"); dump=root/"wrapper.jsx"
        proc=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(plugin),"--input-path",str(source),"--support-dir",str(root/"support"),"--dump-js",str(dump)],cwd=ROOT,text=True,capture_output=True)
        assert proc.returncode==0, proc.stdout+proc.stderr
        jsx=(root/"support"/"run_mac_olmkirakira_mode2_32bpc_validation.jsx").read_text()
        for token in ("params_full","GpuAccelType.SOFTWARE","bits_per_channel","workingSpace","OLMKiraKira.plugin","getSettings(GetSettingsFormat.STRING)","before_effects_control","effect_on","same_comp_control","FAIL_CLOSED"):
            assert token in jsx, token
        assert "Blur Mode" in jsx and "mode3" not in jsx.lower() and "gaussian" not in jsx.lower()
    print("[OK] OLMKiraKira Mode 2 32bpc Mac validation smoke passed without launching AE")
    return 0


if __name__=="__main__": raise SystemExit(main())
