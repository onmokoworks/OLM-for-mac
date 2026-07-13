# OLMSmoother2 c280 -> cce0 Differential Replay

Date: 2026-07-12

## Verdict

`PASS_GROUNDED_C280_AND_CCE0_ENTRY_REPLAY`

This is test-only local binary-semantic evidence. It is not Windows AE truth.

## FACT

- The actual 2025 Windows AEX `FUN_18000c280` entry executes locally with reconstructed source/class descriptors and a fixed-point scale config of `65536/65536`.
- For the c=2 witness, AEX and the production Mac `build_polygon` agree on classifier index `0x69`, count `1`, RGBA, and weight `0.4999988377` when both receive the same raw config `65536/65536` (`655.36/655.36` after the binary divisor `100.0`).
- For the c=4 suppressing control, both builders return count `0`.
- The separately replayed producer-helper chain agrees between AEX and Mac at `1e-6` both for the original `2.0/0.4` fixture and for the c280-equivalent `655.36/655.36` fixture.
- The actual AEX `FUN_18000cce0` six-argument entry executes in no-gamma mode and agrees with the Mac production orchestrator: c=2 AEX `[0.9910671711,0.9910671711,0.9910671711,0.4980380535]`, Mac `[0.991067231,0.991067231,0.991067231,0.498038054]`; c=4 is exact passthrough `[1,1,1,0]`.
- A discriminating Gamma Colors mode-3 fixture records `bb10 apply=1` and also agrees after registering the AEX `pow(double,double)` import: AEX `[0.8971925378,0.4243943989,0.4243943989,0.9980392456]`, Mac `[0.897192419,0.424394399,0.424394399,0.998039246]`.
- The independent `cce0` replay applies the decompiled accumulation rule: clamp summed sample weights to `[0,1]`, retain center residual `1-W`, and add weighted RGBA samples. It compares equal to the port composite float at `1e-6` for both the c=2 witness and c=4 suppressing control.
- The focused smoke requires every exercised c280/helper/cce0 boundary to agree.

## INFERENCE

- The prior `0.4999988377` versus `0.25` observation was a harness parameter mismatch (`raw=65536` versus `raw=100`), not a production implementation defect.
- This does not yet prove that the synthetic fixture maps to the live Windows case_0012 target pixel or prove final host packing.

## Blockers

- A same-run live Windows c280 polygon/class/config tuple is still needed to bind this synthetic result to case_0012.
- Live case_0012 class/config binding and byte-exact host packing remain outside this synthetic proof.
- Production plugin sources were not edited. Machine-readable details remain in `refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json`.

## Command

```sh
python3 refs/scripts/smoke_smoother2_fullchain_diff.py
```

Result: `PASS smoother2 fullchain local differential`.
