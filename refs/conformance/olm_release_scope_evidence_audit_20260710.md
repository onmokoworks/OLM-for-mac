# OLM Release Scope Evidence Audit

Date: 2026-07-10

## Verdict

The target plugin set is complete and matches `notes/PORTING_ROADMAP.md`: the
scope contains the nine named plugin entries, including `OLMSmoother v1`, and
correctly excludes support-only `ColorKeep`. No goal plugin is missing.

The scope is not release-complete. Its main evidence defect is granularity:
several 8bpc cells claim `AE exact` while their coverage strings and the
manifests establish only packaged slices. The ledger explicitly says a passing
packaged subset does not satisfy plugin completion.

## Overclaims requiring correction

### 8bpc packaged slices

These scope cells should not be `result_status: "AE exact"` at the declared
feature-scope level:

| Scope cell | Evidence | Exact correction |
| --- | --- | --- |
| `OLMBlur` 8bpc | `olm_release_scope.json:21,25`; manifest is only 7 packaged normalized cases (`packaged_8bpc_manifest.json:4-5,44-52`) | Change to `partial-ae-exact` (or an equivalent non-complete slice status), retaining `coverage: "packaged normalized 7-case slice"`. The ledger still has unclosed 16bpc/export and Legacy work. |
| `OLMColorKey` 8bpc | Scope feature includes core, Edge Thin, Edge Blur, replace/color-space (`olm_release_scope.json:32,36`), but manifest is 8 exact plus one `reference-generation split` (`packaged_8bpc_manifest.json:18-21,55-64`) | Change to `partial-ae-exact` at whole feature scope, or explicitly redefine the cell as the normalized packaged slice and retain the split qualifier. Do not present the nine-case manifest as all declared feature coverage. |
| `OLMToonDilate` 8bpc | Scope says all declared controls/boundary behavior but evidence is a packaged 3-case slice (`olm_release_scope.json:43,47`; `packaged_8bpc_manifest.json:67-75`) | Change to `partial-ae-exact` or rename the cell's feature scope to the packaged 3-case slice. |
| `OLMDistanceGradation` 8bpc | Scope declares layer/background and in/out modes, while evidence is only packaged basic/extended/blur slices (`olm_release_scope.json:54,58`; manifest summary/suites at `packaged_8bpc_manifest.json:23-25,78-94`) | Change to `partial-ae-exact` or narrow the declared cell to the packaged slices. Keep the ledger's exact 29-case slice count; it does not close all declared paths. |
| `OLMSmoother v1` 8bpc | Scope declares independent v1 behavior or a proven Smoother2 mapping, but evidence is only a packaged 3-case slice and policy is pending (`olm_release_scope.json:108-114`) | Change to `partial-ae-exact` until the v1 policy and complete declared behavior are closed, or explicitly label this as the packaged slice only. |

These are scope-level corrections, not claims that the underlying measured
cases failed. The measured packaged cases remain exact where the manifest says
they are exact. The ledger's rule is the controlling distinction:
`notes/CONFORMANCE_LEDGER.md:37-44` and `notes/PORTING_ROADMAP.md:81-92`.

### 16bpc interpretation

The 16bpc `OLMColorKey` and `OLMToonDilate` entries correctly preserve the
narrow fact that 9/9 and 3/3 covered cases are exact, while marking full
declared coverage as open (`olm_release_scope.json:37-48`). The correction is
documentation consistency only: keep `partial-ae-exact`; do not promote these
cells to plugin-complete.

The 16bpc `OLMBlur` and `OLMDistanceGradation` statuses are conservative. The
current ledger says OLMBlur still needs Mac export/run provenance and narrow
Legacy closure, and DistanceGradation is 5/16 exact with residual families
open (`notes/CONFORMANCE_LEDGER.md:438,440`). No downgrade is required.

## Correct claims

The 32bpc cells correctly remain blocked/probe-only. Every 2026-07-09 status
entry reports PNG-only returns, `float_preserving_present: false`, and no
preferred EXR (`bitdepth_32bpc_probe_status_20260709.json:19-30,60-71` and the
EXR-first rerun at `:87-125`). Exact 32bpc claims require a float-preserving
return, preferably EXR, as also recorded in the current ledger
(`notes/CONFORMANCE_LEDGER.md:50-54`).

The blocked 8/16/32bpc cells for `OLMDirectionalBlur`, `OLMRadialBlur`,
`OLMSmoother2`, and `OLMKiraKira` agree with the ledger's current unresolved
lanes. `OLMSmoother2` correctly distinguishes its exact 12/12 no-key grid from
known-red legacy/key/gamma (`olm_release_scope.json:86-93`; manifest summary at
`packaged_8bpc_manifest.json:31-34`). `ColorKeep` is correctly excluded.

## Underclaims or missing feature accounting

No target plugin is missing from the scope. One feature obligation is
underrepresented in the current ledger matrix: the scope declares
`OLMRadialBlur` **Size/Noise variation and edge behavior** in addition to Zoom,
Rotation, and Inner (`olm_release_scope.json:75-82`), while the ledger's
explicit current rows focus on Zoom/tiny Rotation and Inner
(`notes/CONFORMANCE_LEDGER.md:445`). Add separate ledger rows or an explicit
case-set entry for Size variation, Noise variation, and edge behavior, each at
8/16/32bpc, so those obligations cannot disappear behind the broader RadialBlur
label. This is an accounting correction; it is not evidence that any such row
is exact.

The scope's `OLMDistanceGradation` feature string already includes
layer/background and in/out modes, and the ledger's current residual notes
mention those families. No additional goal feature was found there. Likewise,
the KiraKira scope's remaining visible controls and the Smoother v1 policy
decision are represented as open work in the ledger.

## Commands run

All commands were read-only except creation of this audit file.

```sh
sed -n '1,240p' refs/conformance/olm_release_scope.json
sed -n '1,260p' refs/conformance/packaged_8bpc_manifest.json
sed -n '1,300p' refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json
sed -n '1,300p' refs/conformance/bitdepth_32bpc_probe_status_20260709.json
sed -n '1,260p' notes/CONFORMANCE_LEDGER.md
sed -n '1,220p' notes/PORTING_ROADMAP.md
jq '{summary, suites: [.suites[] | {plugin,feature,bit_depth,case_count,counts,evidence_status,notes}]}' refs/conformance/packaged_8bpc_manifest.json
jq '{summary, suites: [.suites[] | {plugin,feature,bit_depth,case_count,counts,evidence_status,notes}]}' refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json
jq '[.suites[] | {plugin,scope,case_count,plugins,expected_status,returned_case_count,returned_asset_formats,float_preserving_present,preferred_exr_present,classification,next_action}]' refs/conformance/bitdepth_32bpc_probe_status_20260709.json
jq -r '.plugins[] | [.plugin,.feature_scope,.host_status,.ir_status,(.policy_status // ""),(.depths|to_entries[]|[.key,.value.reference_status,.value.result_status,.value.coverage]|@tsv)] | @tsv' refs/conformance/olm_release_scope.json
nl -ba refs/conformance/olm_release_scope.json
nl -ba refs/conformance/packaged_8bpc_manifest.json
nl -ba refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json
nl -ba refs/conformance/bitdepth_32bpc_probe_status_20260709.json
nl -ba notes/PORTING_ROADMAP.md
nl -ba notes/CONFORMANCE_LEDGER.md
```

## Required follow-up

Correct the five packaged-slice 8bpc statuses above, or narrow their feature
labels to the exact packaged slices. Add explicit RadialBlur Size/Noise/edge
rows to the ledger. Do not change the JSON manifests, scripts, or evidence
classification based on this audit alone.
