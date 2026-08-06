#!/usr/bin/env python3
"""Fail-closed proof that skipped CRT initializers cause Mode-3 uniform taps."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.py"
INIT_BEGIN = 0x1814857B8
INIT_END = 0x181485950


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kk_crt_init_exact_") as temporary:
        output = Path(temporary) / "report.json"
        env = os.environ.copy()
        env.update({
            "OLM_KK_PROCESS_ATTACH_DIAGNOSTIC": "1",
            "OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC": "1",
            # The sole _initterm_e callback initializes CRT synchronization
            # fallback state and currently requires additional Win32 handles.
            # This bounded experiment executes only the ordinary C++ global
            # initializer range that owns the OpenCV softdouble constants.
        })
        subprocess.run(
            ["python3", str(PROBE), "--output-json", str(output),
             "--output-md", str(Path(temporary) / "report.md")],
            cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL,
        )
        report = json.loads(output.read_text(encoding="utf-8"))

    evidence = report["evidence"]
    assert report["status"] == "captured"
    attach = evidence["process_attach_diagnostic"]
    assert attach["entry"] == "0x18132b650" and attach["rax"] == 1
    initializer_run = evidence["manual_crt_initializers_diagnostic"]
    assert initializer_run["result"] == 0
    callbacks = initializer_run["callbacks"]
    assert len(callbacks) == 50
    slots = [int(item["slot"], 16) for item in callbacks]
    targets = [int(item["target"], 16) for item in callbacks]
    assert slots == list(range(INIT_BEGIN + 8, INIT_END, 8))
    assert len(targets) == len(set(targets))
    assert all(0x180001000 <= target < 0x181398000 for target in targets)
    assert all(item["kind"] == "_initterm" for item in callbacks)
    assert all(item["result"] >= 0 for item in callbacks)

    exp_calls = evidence["soft_exp_calls"]
    assert len(exp_calls) == 10
    assert all(item["output_f64"] != 1.0 for item in exp_calls)
    assert all(
        math.isclose(item["output_f64"], math.exp(item["input_f64"]), rel_tol=0.0, abs_tol=3e-16)
        for item in exp_calls
    )
    coefficients = evidence["coefficient_generators"][0]["return"]["values_f64"]
    assert len(coefficients) == 21 and len(set(coefficients)) == 11
    assert coefficients == list(reversed(coefficients))
    assert math.isclose(sum(coefficients), 1.0, rel_tol=0.0, abs_tol=2e-16)
    print(
        "PASS_OLMKIRAKIRA_MODE3_PROBE_LOCAL_CRT_INITIALIZERS_20260805 "
        "callbacks=50 soft_exp=restored gaussian_taps=nonuniform"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
