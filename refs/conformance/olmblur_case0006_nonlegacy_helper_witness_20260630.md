# OLMBlur case_0006 Non-Legacy Helper Witness - 2026-06-30

> **2026-07-10 correction:** the later claim below that Windows current-AEX
> pre-store/store agrees with Mac is retracted. The CDB target was never
> captured; the populated `windows_*` fields were not backed by a Windows debug
> artifact. Use
> `refs/conformance/olmblur_case0006_unverified_windows_value_audit_20260710.md`.
> The Mac helper/store observations in this note remain valid.

Live Mac AE witness capture for the remaining 16bpc non-Legacy `case_0006`
pair `(314,14)` and `(29,71)`.

Source run:

- `/tmp/olmblur_case0006_helperdebug_20260630/blur_debug.txt`
- `python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625 --case-id olmblur__case_0006 --output-dir /tmp/olmblur_case0006_helperdebug_20260630 --ae-env 'OLMBLUR_DEBUG_DUMP_PATH=/tmp/olmblur_case0006_helperdebug_20260630/blur_debug.txt' --ae-env 'OLMBLUR_DEBUG_POINTS=314,14;29,71' --ae-env 'OLMBLUR_DEBUG_NONLEGACY_HELPERS=1'`

## Key witness facts

- The non-Legacy helper paths already diverge far upstream of `store16`.
- Final iteration (`iter=10`, `radius=3`) outputs:
  - `(314,14)` vertical helper `out_norm=(0.0335845947,0.0335845947,0.0335845947)`
  - `(29,71)` vertical helper `out_norm=(0.0110931396,0.0110931396,0.0110931396)`
- Final store16 witness remains:
  - `(314,14)` raw `1100.5 -> stored 1100`
  - `(29,71)` raw `363.5 -> stored 364`
- 2026-07-01 imported Windows current-AEX witness now agrees at the same two
  points:
  - `(314,14)` Windows pre-store `1100.5`, internal word `1100`
  - `(29,71)` Windows pre-store `363.5`, internal word `364`

## Reading

- The tracked pair does not stay equal until the writer boundary on the Mac
  side, but the newly imported Windows current-AEX witness shows the same final
  pre-store float and internal word at the active points.
- That means the old live helper/writer suspicion is no longer enough to
  explain the remaining exported PNG residual at these two witnesses.
- The before-effects source image and local helper replay remain useful as
  structure context, but the next bounded question is no longer "which writer
  rule does Windows use here?".
- The active question is now provenance/export-side:
  does the canonical 2026-06-25 16bpc Windows reference set for this slice
  match the same current-AEX build/path that produced the imported witness?

## Bottom line

- Keep the current non-Legacy writer proof, and stop treating both `store16`
  and the final helper witness as primary suspects for `case_0006`.
- The next bounded work should stay on 16bpc reference/export provenance for
  this slice rather than writer-only surgery.
