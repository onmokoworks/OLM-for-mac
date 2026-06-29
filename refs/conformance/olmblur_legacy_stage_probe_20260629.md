# OLMBlur Legacy Stage Probe - 2026-06-29

## Scope

- Plug-in: `OLMBlur`
- Case: `olmblur__case_0007`
- Goal: identify which Legacy pass creates the surviving `(0,0)` 16bpc anomaly

Artifacts:

- `refs/reports/ae_single_case_olmblur_legacy_stage_probe_20260629/probe_report.md`
- `refs/reports/ae_single_case_olmblur_legacy_stage_probe_20260629/olmblur__case_0007/blur_debug.txt`

## Main result

The localized Legacy anomaly at `(0,0)` is not created by the final 16bpc
writer and is not introduced by the vertical Legacy pass.

It first appears in the Legacy **horizontal** pass at `iter=3`.

## Key witness sequence for `(0,0)`

| Stage | Iter | all_same | center | out | Meaning |
| --- | ---: | ---: | ---: | ---: | --- |
| horizontal | 1 | `1` | `0` | `0` | passthrough |
| vertical | 1 | `1` | `0` | `0` | passthrough |
| horizontal | 2 | `1` | `0` | `0` | passthrough |
| vertical | 2 | `1` | `0` | `0` | passthrough |
| horizontal | 3 | `0` | `0` | `3.83520412` | anomaly begins here |
| vertical | 3 | `1` | `3.83520412` | `3.83520412` | vertical preserves it |
| horizontal | 10 | `0` | `180.615829` | `191.976715` | final horizontal growth |
| vertical | 10 | `1` | `191.976715` | `191.976715` | final vertical passthrough |
| store16 | final | n/a | raw `191.976715` | stored `192` | writer only preserves existing value |

## Boundary facts

For `(0,0)` the Legacy sampling windows consistently show:

- horizontal sample span: `first_coord=1`, `last_coord=5`, `sample_count=5`
- vertical sample span: `first_coord=1`, `last_coord=5`, `sample_count=5`

That means the current Mac Legacy path skips coordinate `0` itself and only
samples inward neighbors `1..5` at the corner witness.

## Interpretation

1. The anomaly is not a final rounding problem.
   - By `store16`, raw is already `191.976715`.
2. The anomaly is not a vertical-pass introduction.
   - Every vertical witness at `(0,0)` remains `all_same=1`, so the vertical
     pass keeps passing the current center value through.
3. The anomaly is introduced by the Legacy horizontal pass when the local
   neighborhood stops being considered `all_same`.
   - That transition happens first at `iter=3`.

## What this narrows

The remaining proof target for Legacy `case_0007 (0,0)` is now:

- horizontal Legacy border handling
- horizontal Legacy `all_same` detection / neighborhood equality rule
- horizontal Legacy source neighborhood contents reaching the corner witness

## Rejected local control

A local CLI control on 2026-06-29 forced **horizontal passthrough whenever the
Legacy sample window was truncated** (`sample_count < 2*radius+1`).

That broad rule is rejected:

- exact 8bpc cases `0001/0002/0004` stayed exact
- residual `0003/0005/0006` stayed within their prior gates
- but Legacy `case_0007` worsened from the usual tiny residual family to
  `max=90`, `mean=0.0125`, `nonzero=8052/2073600`

So the remaining border explanation cannot be "all truncated windows
passthrough". If a border special-case exists, it is narrower than generic
truncation.

It is no longer productive to spend time on:

- final writer rounding family
- vertical Legacy pass for the `(0,0)` anomaly

## Decision

- Keep the existing writer conclusions unchanged.
- Treat Legacy `(0,0)` as a **horizontal border/all_same** investigation from
  here onward.
