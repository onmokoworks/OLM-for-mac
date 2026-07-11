# OLMBlur shared-core Mac AE case_0006

- Status: `rejected-experiment`
- Scope: 16bpc non-Legacy `olmblur__case_0006`
- Mac AE: `26.3x87`
- Windows reference: Software 16bpc packaged expected PNG

## Result

| build | max diff | differing channel values | differing pixels |
| --- | ---: | ---: | ---: |
| shared-core Debug | 1 | 3 | 2 |
| prior Mac witness | 1 | 2 | 1 |

The shared-core result differs at `(601,598)` red/green (`18 -> 17`) and
`(1120,627)` red (`253 -> 252`). The prior Mac witness contains only the first
pixel family.

An explicit 8bpc formal batch, with `project.bits_per_channel=8` injected into
the otherwise depth-less legacy manifest, reports red-channel maxima
`59/59/14/58` for case_0001..0004 against the normalized 20260619 expected
set. Crucially, those outputs are byte-identical before and after the broad
shared-core integration and match the retained 20260604 legacy-family drift;
they are a pre-existing reference/provenance split, not an integration
regression. The integration changes only case_0006 by one red value
`186 -> 185`, making that normalized case exact; case_0007 is unchanged. The
first attempted batch without the injected depth is invalid because AE
inherited 16bpc from the preceding run.

## Interpretation

The portable horizontal/vertical helper remains byte-exact against six actual
AEX typed fixtures, but those fixtures do not prove that the helper pair is the
one used by the relevant full-worker branch. `FUN_180005f20` uses a different
labelled helper family (`FUN_1800014f0/FUN_180001ea0`) in the audited branch.
The broad Mac integration was removed because the full-worker callsite/branch
alias is unproven and the 16bpc run introduced an additional one-value residual,
not because of the pre-existing large 8bpc family. The portable core and
fixture evidence remain valid only for their declared function boundary. No
case or bit-depth cell is promoted by this experiment. A current-AEX 8bpc
Windows recapture must pin the AEX SHA-256 before choosing between the legacy
and normalized reference families.

## Reproduction

```text
python3 scripts/run_ae_single_case.py \
  --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625 \
  --case-id olmblur__case_0006 \
  --output-dir /tmp/olmblur_shared_core_case0006_20260710
```
