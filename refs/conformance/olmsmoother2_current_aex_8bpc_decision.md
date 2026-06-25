# OLMSmoother2 Current-AEX 8bpc Decision

- Decision: `runtime-or-asm-first-divergence-required`
- Status: `writer-confirmed-internal-branch-unresolved`
- Recommended action: keep the Smooth Range threshold fix; do not tune from
  broad PNG residuals.

The remaining legacy current-AEX failures are local, opposite-shaped residuals.
They are not a license for global alpha/index/curve/f270 changes.

## Witnesses

| Case | XY | Static dispatch | Reference | Candidate | Required proof |
| --- | ---: | --- | --- | --- | --- |
| `legacy_case_0004_current_aex` | `[1903,519]` | `0xd0 -> FUN_180013140` | `[103,103,103,113]` | `[0,0,0,0]` | prove whether idx=208 produces zero polygon vertices or whether `FUN_180013140` / `cce0` / `c280` appends neighbor-derived samples |
| `legacy_case_0012_gamma5_red_blue_current_aex` | `[91,841]` | `0x69 -> FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70` | `[0,0,0,0]` | `[90,90,90,91]` | prove whether divergence is c280 idx, cardinal6 descriptor/key, e170 bits/code, f270/e3a0 emission, cce0 blend, or final writer |

## 2026-06-25 Return

Returned package:

- `handoffs/windows_returns/20260625_2027_smoother2_current_aex_neighborhood/olm_runtime_trace_smoother2_current_aex_neighborhood_witness_20260624_235610_return_windows.zip`

Result: `answered_partial`.

What it proves:

- `legacy_case_0012_gamma5_red_blue_current_aex [91,841]`: final writer hit;
  Windows rendered sample is `[0,0,0,0]`; writer `RAX=00000000ffffff00`.
- `legacy_case_0004_current_aex [1903,519]`: final writer hit; Windows rendered
  sample is `[103,103,103,113]`; writer `RAX=00000000e8e8e871`.
- Both requested pixels failed to hit the `OLMSmoother2+0x350b` exact-XY
  internal predicate; marker: `TRACE_RENDER_RETURNED_WITHOUT_TARGET`.

What it does not prove:

- `c280` switch index for either witness.
- `cardinal6` descriptor/key for `0012`.
- `e170` / `f270` / `e3a0` branch behavior for `0012`.
- Whether `0004` receives a helper append, a fallback, or a different upstream
  coordinate path.

So the final writer path is now confirmed, but the first internal divergence is
still unresolved.

## Stop Lines

- Do not add a global transparent-center fallback for `0004`.
- Do not globally suppress `f270` or transparent-center appends for `0012`.
- Do not request broad PNGs for these witnesses.
- Do not call this complete until Mac AE exact is proven.

## Evidence Boundary

Useful next evidence is a focused Windows runtime trace or equivalent asm proof
anchored at the final writer/callstack and walking upstream to the actual
producer of the value. The next proof should explain why the expected
`OLMSmoother2+0x350b` / `r9 == xy` predicate does not hit, then identify the
actual `cce0` / `c280` or alternate path for these two witness pixels.

Prepared Windows package:

- `refs/runtime_trace_packages/olm_runtime_trace_smoother2_current_aex_neighborhood_witness_20260624_235610.zip`

Source reports:

- `refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.md`
- `refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.md`
- `refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.md`
- `refs/reports/runtime_trace_summary_smoother2_legacy_current_aex_polygon_20260621.md`
- `refs/reports/runtime_trace_summary_smoother2_legacy_current_aex_0004_cce0_stepover_20260621.md`
