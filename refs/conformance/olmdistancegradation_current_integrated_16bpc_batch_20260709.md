# OLMDistanceGradation current integrated 16bpc batch

Date: 2026-07-09

## Decision

current integrated build is 5/16 exact.

2026-07-09 correction: the apparent `7/16` depthgate baseline was not a true16
canonical-verifier count. `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`
re-verifies the same `/tmp/olmdg_16ext_depthgate2` artifacts at `5/16`.
Therefore, do not treat this report as evidence of a current-vs-depthgate source
provenance delta.

## Command evidence

- Render: `python3 scripts/run_ae_validation_batch.py --base-dir handoff/ae_pixel_validation_20260618 --request-id ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625 --results-base refs/reports/ae_validation_batch_olmdistancegradation_16bpc_both_rule_20260709/results --progress-log refs/reports/ae_validation_batch_olmdistancegradation_16bpc_both_rule_20260709/progress.log --batch-result-json refs/reports/ae_validation_batch_olmdistancegradation_16bpc_both_rule_20260709/batch_result.json --timeout 1800`
- Verify: `python3 scripts/verify_ae_pixel_validation_result.py --run-dir refs/reports/ae_validation_batch_olmdistancegradation_16bpc_both_rule_20260709/verify handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625 refs/reports/ae_validation_batch_olmdistancegradation_16bpc_both_rule_20260709/results/bitdepth16_olmdistancegradation_extended_exact`

Current exact: 5/16
Depthgate true16 reverify exact: 5/16

## Case comparison

| case | depthgate true16 max/nz | current max/nz | current status | note |
| --- | ---: | ---: | --- | --- |
| 0008 | 0/0 | 0/0 | exact | same-max |
| 0010 | 2/351 | 2/351 | diff | same true16 residual |
| 0011 | 2/501 | 2/501 | diff | same true16 residual |
| 0012 | 16384/278028 | 2/2948 | diff | improved |
| 0013 | 16384/167383 | 2/9006 | diff | improved |
| 0014 | 16384/378683 | 4/9630 | diff | improved |
| 0016 | 9710/14131 | 2/5373 | diff | improved |
| 0020 | 0/0 | 0/0 | exact | same-max |
| 0021 | 0/0 | 0/0 | exact | same-max |
| 0022 | 0/0 | 0/0 | exact | same-max |
| 0023 | 0/0 | 0/0 | exact | same-max |
| 0024 | 20/1051915 | 20/1051915 | diff | same true16 residual |
| 0025 | 6/860084 | 6/860084 | diff | same true16 residual |
| 0026 | 4/900709 | 4/900709 | diff | same true16 residual |
| 0027 | 4/451535 | 4/451535 | diff | same true16 residual |
| 0028 | 3080/457177 | 3080/457177 | diff | same true16 residual |

## Interpretation

- FACT: the current installed/worktree integrated build verifies at `5/16` exact on the canonical 16bpc batch path.
- FACT: compared with `/tmp/olmdg_16ext_depthgate2/results.csv`, Layer/no-bg cases `0012/0013/0014/0016` are much improved in the current integrated build.
- FACT: canonical verifier recheck of the `/tmp/olmdg_16ext_depthgate2` artifacts shows `0010/0011/0024..0028` were not true16 exact there either.
- INFERENCE: the next DG work is not an integration split. It is true16 residual classification and closeout.
