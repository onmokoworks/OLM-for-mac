# OLMDistanceGradation 16bpc Residual-Family Classifier

Scope: existing reports/results only; no PNG tuning, production edits, ledger edits, or invented Windows values.

- Exact control set: `0008, 0010, 0011, 0020, 0021, 0022, 0023`
- Unresolved families: `layer-no-bg`, `max-2`, `outlier-0028`

| Family | Cases | Classification | Next missing boundary |
| --- | --- | --- | --- |
| `exact` | `0008, 0010, 0011, 0020, 0021, 0022, 0023` | ae-exact-control | none-for-this-control-slice |
| `layer-no-bg` | `0012, 0013, 0014, 0016` | residual-max-2-with-case-0014-max-4 | Windows source RGBA16 -> normalized source -> composed RGBA float -> PF16 store words -> same-run true16 export |
| `max-2` | `0024, 0025, 0026, 0027` | broad-field-export-residual-max-2 | case-0024..0027 Windows field-world value -> compose input -> PF16 store/export true16 binding |
| `outlier-0028` | `0028` | separate-large-field-source-or-premultiply-residual | case-0028 Windows source/premultiply ownership versus field-X shape at composed RGBA float |

## `exact`

Next evidence: Preserve these seven cases as controls while closing the three unresolved families.

### Evidence

- `typed` `present`: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json` - Current Mac AE 16bpc result reports max=0 and nonzero_pixels=0 for all seven cases.
- `binary` `present`: `refs/conformance/olmdg_compose_exact_address_witness_20260710.json` - The bounded actual-AEX compose witness validates the 16bpc callback shape for the 0010/0011 control lane; it is local evidence, not a Windows live return.

Measured rows:

| Case | Max diff | Nonzero pixels |
| --- | ---: | ---: |
| `0008` | 0 | 0 |
| `0010` | 0 | 0 |
| `0011` | 0 | 0 |
| `0020` | 0 | 0 |
| `0021` | 0 | 0 |
| `0022` | 0 | 0 |
| `0023` | 0 | 0 |

## `layer-no-bg`

Next evidence: One same-run typed witness at case_0012 (438,0) and case_0014 (448,0), with all six stages bound.

### Evidence

- `typed` `present`: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json` - Current AE rows are small even-valued residuals: 0012/0013/0016 max=2 and 0014 max=4.
- `typed` `present`: `refs/conformance/olmdistancegradation_16bpc_export_rounding_residual_audit_20260709.json` - Existing samples show the Layer/no-bg residual at the exported true16 words, including the 0012 +/-2 and 0014 -4 RGB witnesses.
- `typed` `present`: `refs/conformance/olmdistancegradation_0012_0014_store_export_local_audit_20260710.md` - Local audit keeps both cases open and records the representative store/export values without claiming Windows pre-store values.
- `binary` `present`: `refs/conformance/olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.md` - The rejected Layer unpremultiply experiment rules out a broad ownership change from the existing evidence.

Measured rows:

| Case | Max diff | Nonzero pixels |
| --- | ---: | ---: |
| `0012` | 2 | 2793 |
| `0013` | 2 | 10135 |
| `0014` | 4 | 10664 |
| `0016` | 2 | 5373 |

## `max-2`

Next evidence: A paired typed witness for 0026/0027 should bind field value, interpolation output, render-mode branch, PF16 store, and same-run true16 export; do not reuse the stale max=1 classification as proof.

### Evidence

- `typed` `present`: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json` - Current AE rows report max=2 for each case; the family remains non-exact despite the PF16 boundary improvement.
- `typed` `present`: `refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md` - Earlier max=1 byte-view/depthgate witnesses identify contour-region controls, but are not promoted over the canonical true16 result.
- `binary` `present`: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json` - AEX facts identify FUN_181174760, FUN_18117ca50, and FUN_181170480 plus the OpenCV 4.5.5 round-to-nearest-even PF16 boundary.
- `binary` `present`: `tools/emulation/DG_FIELD_GEN_REPORT.md` - Disassembly-grounded field generation and threshold facts exist, but no case-specific Windows live field value is present for 0024..0027.

Measured rows:

| Case | Max diff | Nonzero pixels |
| --- | ---: | ---: |
| `0024` | 2 | 991667 |
| `0025` | 2 | 808516 |
| `0026` | 2 | 819532 |
| `0027` | 2 | 505602 |

## `outlier-0028`

Next evidence: One 0028 witness must bind source alpha/RGB, field X, composed RGBA float, PF16 store, and true16 export in one run before choosing source or field ownership.

### Evidence

- `typed` `present`: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json` - Current AE row reports max=3080 and 461476 nonzero pixels, separating 0028 from the max-2 family.
- `typed` `present`: `refs/conformance/olmdistancegradation_16bpc_case0027_analysis_20260628.md` - Existing neighboring power/layer analysis identifies source-zero and background contribution witnesses, but does not close 0028.
- `binary` `present`: `notes/IR_OLMDistanceGradation.md` - The IR records the binary-backed field, source-mask, and compose stages relevant to separating field shape from source/premultiply ownership.
- `binary` `present`: `tools/emulation/DG_FIELD_GEN_REPORT.md` - Binary field-generation facts constrain the next probe without supplying an invented Windows value for 0028.

Measured rows:

| Case | Max diff | Nonzero pixels |
| --- | ---: | ---: |
| `0028` | 3080 | 461476 |

## Boundary Discipline

- No PNG-only tuning or production edits are part of this classifier.
- A local AEX/binary witness is labeled binary evidence and is never promoted to a Windows live value.
- Missing boundaries are named explicitly; no Windows values are invented.
