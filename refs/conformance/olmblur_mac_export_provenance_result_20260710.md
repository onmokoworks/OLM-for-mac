# OLMBlur Mac Export Provenance Result

Date: 2026-07-10

## Verdict

The historical Mac single-versus-batch export split did not reproduce. Two
fresh single-case runs and two fresh batch runs under AE `26.3x87` produced a
stable, identical artifact per case across both execution paths.

This closes the current Mac export-path provenance question. It does not close
16bpc compatibility: the stable Mac outputs still differ from the canonical
Windows Software references with `max_diff=2`.

## FACT

- Request: `ae_pixel_bitdepth16_olmblur_exact_20260625`.
- Mac AE: `26.3x87`.
- `case_0006`:
  - Windows canonical SHA-256:
    `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`.
  - Mac single and batch SHA-256, unchanged on repeat:
    `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787`.
- `case_0007`:
  - Windows canonical SHA-256:
    `2b7f5f0990cd3009fc3690b7b1b4943b11c6bce67ec41cbcde98508ec6578f50`.
  - Mac single and batch SHA-256, unchanged on repeat:
    `dad5c6f855599c8714b7eaff480235ec1b0a7fed68fc8cbdc514d5cebaff2426`.
- The canonical verifier processed all seven batch outputs. Result: `0/7`
  exact; every case has `max_diff=2`. Representative nonzero counts are
  `case_0006=283/2073600` and `case_0007=306/2073600`.
- The batch result JSON listed `case_0003: PNG was not written`, but the PNG was
  present and the canonical verifier read it. Treat that message as a runner
  reporting anomaly, not as missing OLMBlur output for this run.
- `case_0006` debug values remain ties-to-even on Mac, including
  `1100.5 -> 1100` at `(314,14)` and `363.5 -> 364` at `(29,71)`.
- `case_0007` debug output remains the known Legacy half-step:
  `12544.5 -> 12545` at `(345,672)`.

## INFERENCE

- The old single/batch artifact split is stale or depended on historical host
  state. It is not a live explanation for the current 16bpc residual.
- No broad writer or helper change is justified. `case_0006` now needs a typed
  Windows helper/pre-store discriminator, or equivalent binary-grounded AEX
  evidence, rather than another Windows reference export.
- `case_0007` remains a separate Legacy pre-store half-step family.

## Commands

```bash
python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625 --case-id olmblur__case_0006 --output-dir /tmp/olmblur_mac_export_provenance_20260710/single/olmblur__case_0006
python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625 --case-id olmblur__case_0007 --output-dir /tmp/olmblur_mac_export_provenance_20260710/single/olmblur__case_0007
python3 scripts/run_ae_validation_batch.py --base-dir handoff/ae_pixel_validation_20260618 --request-id ae_pixel_bitdepth16_olmblur_exact_20260625 --results-base /tmp/olmblur_mac_export_provenance_20260710/batch/results --progress-log /tmp/olmblur_mac_export_provenance_20260710/batch/AE_PIXEL_VALIDATION_PROGRESS.log --batch-result-json /tmp/olmblur_mac_export_provenance_20260710/batch/AE_PIXEL_VALIDATION_BATCH_RESULT.json
python3 scripts/verify_ae_pixel_validation_result.py handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625 /tmp/olmblur_mac_export_provenance_20260710/batch/results/bitdepth16_olmblur_exact --run-dir /tmp/olmblur_mac_export_provenance_20260710/verify_repeat
```

The single and batch commands were each repeated before recording the stable
hashes above.
