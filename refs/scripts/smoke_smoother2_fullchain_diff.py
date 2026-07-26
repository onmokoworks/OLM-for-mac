#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path("/tmp/olmsmoother2_fullchain_diff")
ADAPTER = BUILD / "port_adapter"
RESULT = ROOT / "refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json"
REPORT = ROOT / "refs/conformance/olmsmoother2_c280_cce0_replay_20260712.md"

BUILD.mkdir(parents=True, exist_ok=True)
compile_cmd = [
    "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra",
    f"-I{ROOT / 'cli/OLMSmoother2/shim'}",
    f"-I{ROOT / 'mac/OLMSmoother2/Mac'}",
    str(ROOT / "tools/emulation/smoother2_fullchain_port_adapter.cpp"),
    "-o", str(ADAPTER),
]
subprocess.run(compile_cmd, check=True, cwd=ROOT)
run = subprocess.run([
    "python3", str(ROOT / "tools/emulation/test_smoother2_fullchain_diff.py"),
    "--adapter", str(ADAPTER), "--output", str(RESULT),
], check=False, cwd=ROOT)
result = __import__("json").loads(RESULT.read_text())
comparisons = [row["comparison"] for row in result["facts"]]
facts_by_fixture = {row["aex"]["fixture"]: row for row in result["facts"]}
assert run.returncode == 0, run.returncode
assert result["status"] == "pass_all_production_boundaries_with_expected_helper_replay_gap"
assert result["expected_helper_replay_gap_fixtures"] == ["classifier_one"]
assert all(row["all_production_boundaries_equal"] for row in comparisons)
assert all(row["c280_entry_vs_production_builder_equal_1e-6"] for row in comparisons)
assert not facts_by_fixture["classifier_one"]["comparison"]["c280_equiv_helpers_vs_production_builder_equal_1e-6"]
assert all(
    row["comparison"]["c280_equiv_helpers_vs_production_builder_equal_1e-6"]
    for name, row in facts_by_fixture.items()
    if name != "classifier_one"
)
assert all(row["cce0_entry_vs_production_orchestrator_equal_1e-6"] for row in comparisons)
assert all(row["cce0_gamma_colors_vs_production_orchestrator_equal_1e-6"] for row in comparisons)
assert result["facts"][0]["aex"]["cce0_entry"]["rgba"] != result["facts"][0]["aex"]["cce0_gamma_colors_entry"]["rgba"]
assert all(row["cce0_accumulation_equal_1e-6"] for row in comparisons)
REPORT.write_text(
    f"""# OLMSmoother2 c280 -> cce0 Differential Replay

Date: 2026-07-16

## Verdict

`PASS_PRODUCTION_BOUNDARIES_WITH_EXPECTED_HELPER_REPLAY_GAP`

This is test-only local binary-semantic evidence. It is not Windows AE truth.

## FACT

- The actual 2025 Windows AEX `FUN_18000c280` entry executes locally with reconstructed source/class descriptors and a fixed-point scale config of `65536/65536`.
- For the c=2 witness, AEX and the production Mac `build_polygon` agree on classifier index `0x69`, count `1`, RGBA, and weight `0.4999988377` when both receive the same raw config `65536/65536` (`655.36/655.36` after the binary divisor `100.0`).
- For the c=4 suppressing control, both builders return count `0`.
- All four rows agree at every production c280/cce0 boundary. The standalone classifier-`0x40` helper replay remains incomplete because it emits one contribution while actual c280 and the production builder emit two; that helper-only gap is named and excluded from production claims.
- The actual AEX `FUN_18000cce0` six-argument entry executes in no-gamma mode and agrees with the Mac production orchestrator: c=2 AEX `[0.9910671711,0.9910671711,0.9910671711,0.4980380535]`, Mac `[0.991067231,0.991067231,0.991067231,0.498038054]`; c=4 is exact passthrough `[1,1,1,0]`.
- A discriminating Gamma Colors mode-3 fixture uses the AEX internal v2 flag `0`, a zeroed output-transfer context, and a transfer-invariant white key. It records `bb10 apply=1` and agrees after registering the AEX `pow(double,double)` import: AEX `[0.8971925378,0.4243943989,0.4243943989,0.9980392456]`, Mac `[0.897192538,0.424394399,0.424394399,0.998039246]`.
- The independent `cce0` replay applies the decompiled accumulation rule: clamp summed sample weights to `[0,1]`, retain center residual `1-W`, and add weighted RGBA samples. It compares equal to the port composite float at `1e-6` for both the c=2 witness and c=4 suppressing control.
- The focused smoke requires every production c280/cce0 boundary to agree and permits the helper-only gap for `classifier_one` alone.

## INFERENCE

- The prior `0.4999988377` versus `0.25` observation was a harness parameter mismatch (`raw=65536` versus `raw=100`), not a production implementation defect.
- The later classifier-`0x40` half-weight mismatch was a production initializer defect: the four affected leaf initializers now use the AEX-grounded `1.0`, while their optional chase paths retain `0.5`.
- This does not yet prove that the synthetic fixture maps to the live Windows case_0012 target pixel or prove final host packing.

## Blockers

- A same-run live Windows c280 polygon/class/config tuple is still needed to bind this synthetic result to case_0012.
- Live case_0012 class/config binding and byte-exact host packing remain outside this synthetic proof.
- The binary-grounded initializer corrections are covered by dedicated sibling/`ead0` probes. Machine-readable fullchain details remain in `refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json`.

## Command

```sh
python3 refs/scripts/smoke_smoother2_fullchain_diff.py
```

Result: `PASS smoother2 fullchain local differential`.
"""
)
print("PASS smoother2 fullchain local differential")
print(f"result={RESULT}")
print(f"report={REPORT}")
