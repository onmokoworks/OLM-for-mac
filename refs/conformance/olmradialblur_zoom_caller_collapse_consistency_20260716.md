# OLMRadialBlur Zoom Caller-Collapse Consistency (2026-07-16)

- Status: `blocked`
- Classification: `measured-gate-failure`
- Gates: `{"all_points": true, "discriminating_alpha": false, "entry_reached": true, "exact_float32_replay_vs_d80": true, "exact_trunc_u8_replay": true, "hashes": true, "one_prepass_and_scatter": false}`

## FACT

The JSON records the actual-AEX core entry and four direct `FUN_180009D80`
observations. Worker and scatter were not reached.

## Measured Blocker

The full-size run hit the 250,000,000-instruction cap at `0x90000000` before the worker/scatter calls, so the requested alpha discriminator is not proven.

Do not rerun the same full-size configuration with the same cap. The next
local attempt must checkpoint after setup or enter the worker with reconstructed
caller state.

## INFERENCE

The direct sampler replay matched the actual AEX `FUN_180009D80` output for all captured points. This is a local Mac Unicorn/AEX observation only; it makes no AE-exact or Windows-live claim.
