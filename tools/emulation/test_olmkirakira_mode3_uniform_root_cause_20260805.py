#!/usr/bin/env python3
"""Diagnose the Unicorn-only uniform Mode-3 Gaussian coefficients."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.py"


def run(extra_env: dict[str, str]) -> dict:
    with tempfile.TemporaryDirectory(prefix="kk_mode3_root_") as temporary:
        out = Path(temporary) / "report.json"
        env = os.environ.copy()
        env.update(extra_env)
        subprocess.run(
            ["python3", str(PROBE), "--output-json", str(out),
             "--output-md", str(Path(temporary) / "report.md")],
            cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL,
        )
        return json.loads(out.read_text(encoding="utf-8"))


def assert_uniform(report: dict, sync_implemented: bool) -> None:
    evidence = report["evidence"]
    assert report["status"] == "captured"
    generator = evidence["coefficient_generators"][0]
    assert generator["entry"] == {"r8_count": 21, "xmm3_sigma_f64": 2.5}
    returned = generator["return"]
    assert returned["count"] == 21
    assert returned["values_f64"] == [1.0 / 21.0] * 21
    exp_calls = evidence["soft_exp_calls"]
    assert len(exp_calls) == 10
    assert len({item["input_u64"] for item in exp_calls}) == 10
    assert all(item["input_f64"] < 0.0 for item in exp_calls)
    assert all(item["output_f64"] == 1.0 for item in exp_calls)
    imports = returned["imports_during_generator"]
    assert {item["name"] for item in imports} <= {
        "EnterCriticalSection", "LeaveCriticalSection", "SetEvent", "ResetEvent", "malloc"
    }
    assert all(
        item["implemented"] == sync_implemented
        for item in imports if item["name"] != "malloc"
    )


def main() -> int:
    pe = pefile.PE(str(ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"), fast_load=False)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    assert image_base + pe.OPTIONAL_HEADER.AddressOfEntryPoint == 0x18132B650
    assert pe.DIRECTORY_ENTRY_TLS.struct.AddressOfCallBacks == 0x181485978
    callback_rva = pe.DIRECTORY_ENTRY_TLS.struct.AddressOfCallBacks - image_base
    assert pe.get_data(callback_rva, 8) == b"\0" * 8

    baseline = run({})
    successful_sync = run({"OLM_KK_SYNC_SHIM_DIAGNOSTIC": "1"})
    process_attach = run({"OLM_KK_PROCESS_ATTACH_DIAGNOSTIC": "1"})
    assert_uniform(baseline, False)
    assert_uniform(successful_sync, True)
    assert_uniform(process_attach, False)
    attach = process_attach["evidence"]["process_attach_diagnostic"]
    assert {key: attach[key] for key in ("entry", "instructions", "rax")} == {
        "entry": "0x18132b650", "instructions": 466, "rax": 1,
    }
    assert {item["name"] for item in attach["imports"]} >= {"_initterm", "_initterm_e"}
    assert all(not item["implemented"] for item in attach["imports"]
               if item["name"] in {"_initterm", "_initterm_e"})
    assert (
        baseline["evidence"]["coefficient_generators"][0]["return"]["words_u64"]
        == successful_sync["evidence"]["coefficient_generators"][0]["return"]["words_u64"]
        == process_attach["evidence"]["coefficient_generators"][0]["return"]["words_u64"]
    )
    print(
        "PASS_OLMKIRAKIRA_MODE3_UNIFORM_ROOT_CAUSE_20260805 "
        "soft_exp_negative_inputs=10 outputs_all_one=true sync_shims_no_effect=true "
        "dll_process_attach_no_effect=true tls_callbacks=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
