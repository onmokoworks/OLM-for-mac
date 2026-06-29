# OLMBlur Last 1px Family Probe - 2026-06-29

## Scope

- Plug-in: `OLMBlur`
- Goal: classify the remaining post-carry-prev residual family without making a
  blind global writer change

## 8bpc witness

CLI rerun using the normalized `case_0007` input and params:

```sh
OLMBLUR_TRACE_PIXELS='488,941;488,942' \
  cli/OLMBlur/olmblur_cli \
  --input refs/reports/ae_host_validation_20260618_232926/cli_checks/olmblur_normalized/reference/case_0007_before_effects.png \
  --params refs/reports/ae_host_validation_20260618_232926/cli_checks/olmblur_normalized/candidate/_params/case_0007.json \
  --output /tmp/olmblur_case0007_trace.png
```

Witness values:

- `(488,941)`:
  - raw `250.499985`
  - `floor05 = 250`
  - `nearby = 250`
- `(488,942)`:
  - raw `250.500015`
  - `floor05 = 251`
  - `nearby = 251`

Interpretation:

- the remaining old 8bpc `case_0007` witness is now a pure half-step boundary
  split
- current Mac/CLI is only low on the one coordinate that stays just below
  `250.5`
- this is not the old structural Legacy border/all-same issue anymore

## 16bpc witness

Mac AE single-case probe:

- report:
  `refs/reports/ae_single_case_olmblur_case0007_final1px_probe_20260629/probe_report.md`
- debug dump:
  `refs/reports/ae_single_case_olmblur_case0007_final1px_probe_20260629/olmblur__case_0007/blur_debug.txt`

Target point:

- `(345,672)`:
  - raw `(624.429565, 0.0000126167242, 12544.5)`
  - `floor05 = (624, 0, 12545)`
  - `nearby = (624, 0, 12544)`
  - stored `(624, 0, 12545)` because Legacy uses `floor(x + 0.5)`

PNG comparison:

- Windows normalized 16bpc ref:
  `(4, 0, 97, 255)`
- current Mac AE:
  `(4, 0, 98, 255)`

This matches the known export mapping where positive PNG channel values track
`2 * stored_word - 1`:

- Windows `97` implies internal word `12544`
- Mac `98` implies internal word `12545`

Interpretation:

- the remaining 16bpc `case_0007` witness is also now a one-word half-step
  boundary family
- current Mac probe lands exactly on `12544.5`, which makes the Legacy writer
  round up to `12545`
- this is not evidence that the Legacy writer rule is globally wrong
- instead it means the final unresolved question is whether Windows reaches a
  slightly smaller pre-store float at this coordinate

## What this rules out

- Do not re-open the retired `(0,0)` border/seed blocker from old `case_0007`.
  It stays zero in the live Mac AE probe.
- Do not make a blind global `floorf(v + 0.5f) -> nearbyintf(v)` swap for
  Legacy, because the surviving witness is consistent with a tiny pre-store
  float difference rather than a proven writer-rule mismatch.
- Do not change the non-Legacy 16bpc writer from this Legacy witness.

## Best next evidence

The next useful proof is a Windows-side narrow witness for the same surviving
coordinates:

- old 8bpc `case_0007` `(488,941)`
- 16bpc normalized `case_0007` `(345,672)`

We want the pre-store float, not just the final PNG byte/word, so we can tell
whether Windows is:

1. below the half-step (`250.499...` / `12544.499...`), or
2. using a different writer/helper rule at the last step

Current evidence favors (1).
