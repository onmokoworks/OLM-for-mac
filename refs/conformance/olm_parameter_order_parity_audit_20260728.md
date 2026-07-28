# OLM parameter-order parity audit (2026-07-28)

## Answer

No: the current Mac definitions do not reproduce the complete actual-AEX
parameter surface for every OLM plug-in in scope.

Seven plug-ins are ordered matches. `OLMColorKey` is a structural-row mismatch:
its payload rows and match-name/disk IDs are preserved, but the Mac Threshold
topic is registered after the precision/per-color controls while the Windows
AEX exposes the Threshold Parameters label at property row 3.
`OLMKiraKira` is a guarded partial match: all 25 ordinary mapped rows are in
Windows order on Mac, but the five ramp-label rows, five opaque ramp-payload
rows, and five blank separators present in the Windows 40-row ABI are absent.

This is a static/source and captured-host-surface conclusion. It is not a claim
that a newly built Mac binary was loaded by After Effects during this audit.

## Classification

- `match`: every plug-in-owned Windows row is represented in the same order by
  the Mac enum and `ParamsSetup`; disk IDs/match-name suffixes agree.
- `guarded partial`: the ordinary mapped rows agree, omitted Windows-only rows
  are classified exactly, and saved-project transfer fails closed where the
  omitted representation matters.
- `mismatch`: a known Windows row is registered at a different relative
  position on Mac and no compatibility guard converts that surface into a full
  ordered match.
- `unknown`: evidence is insufficient to classify the order.

AE built-ins (`ADBE Effect Mask Opacity` and `ADBE Force CPU GPU`) are host rows,
not plug-in `params[]` slots, and are excluded from all plug-in row counts.

## Exact per-plug-in matrix

| Plug-in | Windows/AEX plug-in rows | Mac slots after input | Status | Exact ordered result |
| --- | ---: | ---: | --- | --- |
| `OLMSmoother` (v1) | 3 | 3 | `match` | disk IDs / match-name suffixes `1,2,3`: Use Color Key, Color Key, Do Smooth Range |
| `OLMSmoother2` (v2) | 15 | 15 | `match` | `1,2,15,3,4,5,6,7,8,9,10,11,12,13,14`: Enable Color Key, Color Key, Invert Color Key, Smoothness, Extra Smooth, Smooth Range, Smoother Version, Gamma Correction, Gamma Value, Number of Gamma Colors, five Gamma Color rows |
| `OLMBlur` | 5 | 5 | `match` | `5,6,3,4,7`: Blur Amount, Blur Smoothness, Number of Repeat, Bias Direction, Legacy |
| `OLMColorKey` | 223 | 223 | `mismatch` | payload/leaf identity agrees, including all 25 repeated eight-row color blocks; structural Threshold Parameters row is Windows row 3 (`-0003`) but the Mac topic is registered after rows with disk IDs `4,5,522,6,7` and uses Mac-only topic ID `0x301`; topic-end IDs are also Mac-only structural IDs |
| `OLMToonDilate` | 1 | 1 | `match` | `1`: Search Radius (`ADBE OLMToonDilate-0001`) |
| `OLMDirectionalBlur` | 21 | 21 | `match` | contiguous IDs `1..21`, including display-label rows `4,9,14`, duplicate-label/blank separator rows `8,13,21`, and payload rows at their captured AEX indices |
| `OLMRadialBlur` | 30 | 30 | `match` | `1,2,3,4,28,29,5,6,7,8,30,31,9,10,26,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25`; labels/separators remain at rows `3,8,9,14,16,19,23,30` |
| `OLMDistanceGradation` | 12 | 12 | `match` | contiguous IDs `1..12`: Invert through Blur Size |
| `OLMKiraKira` | 40 | 25 | `guarded partial` | the 25 mapped Mac rows follow Windows order exactly; Windows rows `12/18/24/30/36` are ramp labels, `14/20/26/32/38` are opaque ramp payloads, and `15/21/27/33/39` are blank separators, all absent on Mac |

There are no `unknown` rows in this scope.

## KiraKira saved-project ABI result

The exact Windows disk-ID order is:

`8,9,17,10,2,11,27,7,12,3,13,29,18,19,30,4,14,31,20,21,32,5,15,33,22,23,34,26,28,37,35,36,38,6,16,39,24,25,40,1`.

The Mac mapped subsequence is:

`8,9,17,10,2,11,27,7,12,3,13,18,4,14,20,5,15,22,26,28,35,6,16,24,1`.

`scripts/guard_olmkirakira_saved_project_abi_20260728.py` embeds the full
40-row Windows ABI and rejects index-only transfer after Windows row 11,
unknown/duplicate/wrong-index match names, incomplete full transfers, and any
enabled ramp while the opaque `0x144`-byte ramp payload is unsupported.
Therefore the 25-row Mac subsequence is not mislabeled as full parity.

## Evidence used

- Windows cold-start property order and match names:
  `refs/win_references/olm_fresh_instance_defaults_20260629/OLMmulti-effectdefaultcapture/reference_manifest.json`
  and the corresponding ranges manifest.
- Mac enum, disk-ID constants, and registration order: each plug-in header and
  `ParamsSetup` implementation under `mac/`.
- Actual-AEX checkout/setup evidence, especially
  `refs/conformance/dblur_param_checkout_abi_20260711.md`, the radial manifest
  audit, and the checked-in actual-AEX conformance notes.
- KiraKira row classification:
  `refs/conformance/olmkirakira_parameter_surface_contract_20260717.json`.
- Existing cross-surface audit:
  `refs/conformance/olm_parameter_surface_audit_20260718.{md,json}`.

Display text is not used as identity where labels repeat. Match names/disk IDs
are the identity; display labels, topic/group labels, blank separators, and
opaque payload rows are classified separately.

## Validators run

All passed on 2026-07-28:

```text
python3 refs/scripts/smoke_validate_olm_parameter_order_20260718.py
python3 refs/scripts/smoke_olmsmoother2_parameter_surface.py
python3 refs/scripts/smoke_guard_olmkirakira_saved_project_abi_20260728.py
python3 refs/scripts/smoke_validate_olmkirakira_surface_contract_20260717.py
```

The first validator currently asserts ColorKey leaf/disk-ID stability and
KiraKira mapped-row order; its pass must not be interpreted as full structural
row parity.

## Actionable gaps

1. `OLMColorKey`: decide whether saved-project ABI compatibility requires the
   Windows `-0003/-0011/-0012/-0020/-0016/-1016` structural sequence to be
   represented literally. Do not reorder only the enum or only `ParamsSetup`;
   validate a rebuilt plug-in in AE and add a saved-project guard before
   accepting such a change.
2. `OLMKiraKira`: implement or deliberately reject the five opaque ramp
   payloads together with their label/separator rows. Until then, retain the
   fail-closed guard and describe compatibility as mapped-subsequence only.
3. Extend the order validator to cover the seven full-match plug-ins and to
   assert ColorKey structural divergence explicitly. At present those results
   rely on the captured manifests plus direct source review rather than one
   consolidated regression executable.

No AEXCompat tree, production source, Windows/AE state, NAS data, or ledger was
changed by this audit.
