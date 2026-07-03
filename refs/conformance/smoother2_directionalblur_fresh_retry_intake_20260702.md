# Smoother2 / DirectionalBlur Fresh Retry Intake

Date: `2026-07-02`

This note records what materially changed in the latest Windows retry returns.

## OLMSmoother2 current-AEX producer-path diff

Return:

- `refs/reports/runtime_trace_summary_smoother2_current_aex_producer_path_diff_20260702_220800.json`

What is now newly proven:

- this was a fresh CDB pass, not a retained-evidence rewrite
- `OLMSmoother2` loaded in the current AE run
- broad breakpoints at `+0xc280`, `+0xcce0`, `+0x350b`, and `+0x3610` are all reachable
- the live lane is no longer blocked on “does this path execute at all?”

What is still missing:

- `0004` witness-local c280 switch index / polygon count / helper append / cce0 fallback fact
- `0012` witness-local cardinal6 / `e170` / `f270` / `e3a0` first divergence

Interpretation:

- the blocker moved from “retained evidence only” to “broad hit storm before witness-local gating”
- next retry should narrow from reachable broad breakpoints to writer-anchored witness-local producer filtering

## OLMDirectionalBlur witness logging prep

Return:

- `refs/reports/runtime_trace_summary_directionalblur_witness_logging_prep_20260702_220801.json`

What is now newly proven:

- this was a fresh CDB pass, not a retained-evidence rewrite
- `OLMDirectionalBlur` loads in a valid Software render
- broad `+0x2000` breakpoint hits are reachable
- the live lane is no longer blocked on “module failed to load”

What is still missing:

- angle-0 witness-local A/B mapping, denominator, `alpha_or_valid`, helper touched range, pre-writeback
- diagonal witness-local rotate sampler order, border-validity, denominator, pre-writeback

Interpretation:

- the blocker moved from “module never resolved” to “entry-style broad breakpoints are too noisy”
- next retry should move away from broad `+0x2000` entry-style hits and toward a narrower witness-local stage

## Practical conclusion

These returns are still `failed_partial`, but they are useful failures:

- both lanes now have confirmed live execution in fresh CDB runs
- both lanes now need narrower witness-local gating, not another broad existence proof
