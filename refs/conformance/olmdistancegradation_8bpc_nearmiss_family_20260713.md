# OLMDistanceGradation 8/16bpc Near-miss Family Classification

Date: 2026-07-13

Scope: `case_0024..0027` only. Existing conformance reports, stored result CSV/JSON,
existing compare artifacts, and existing Mac AE probe artifacts only. No algorithm
edits. No PNG-only tuning.

## FACT

### Sources used

- `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.{md,json}`
- `refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md`
- `refs/conformance/olmdistancegradation_depthgate_quantization_return_intake_20260708.md`
- `refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.{md,json}`
- `refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.{md,json}`
- `refs/conformance/olmdistancegradation_8bpc_current_binary_reconstruction_20260712.md`
- `refs/conformance/packaged_8bpc_manifest.json`
- `refs/reports/ae_validation_batch_olmdistancegradation_16bpc_depthgate_singlecase_reverify_20260709/reports/ae_pixel_16bpc_extended_exact.{csv,json}`
- `refs/reports/ae_single_case_distancegradation_depthgate_nearmiss_20260708/case_0026/field_debug_report.{md,json}`
- `refs/reports/ae_single_case_distancegradation_depthgate_nearmiss_20260708/case_0027/field_debug_report.{md,json}`
- `refs/reports/ae_host_validation_20260618_232926/cli_checks/olmdistancegradation_extended_normalized/candidate/_params/case_0024.json`
- same `_params` path for `case_0025.json`, `case_0026.json`, `case_0027.json`

### Parameter correlation

Shared across all four cases:

- `In/Out=3`
- `Inside Threshold=158`
- `Use Background Color=1`
- `BG Color=[1,0,0,1]`
- `Gradation Color=[0.1098041459918,0,0.93333333730698,1]`
- `Blur Mode=1`
- `Blur Size=0`

Per-case splits:

| Case | Invert | Outside Threshold | Render Mode | Interpolation Mode | Power |
| --- | ---: | ---: | ---: | ---: | ---: |
| `case_0024` | `0` | `17` | `1` | `3` | `1` |
| `case_0025` | `1` | `13` | `1` | `3` | `1` |
| `case_0026` | `1` | `13` | `1` | `4` | `2.59740740729979` |
| `case_0027` | `1` | `13` | `2` | `4` | `2.59740740729979` |

The cleanest control pair is still `case_0026` vs `case_0027`: same parameters
except `Render Mode` (`1 -> 2`).

### 8bpc classification

Current-binary 8bpc is not a defensible near-miss family. The authoritative
2026-07-11 depth-correct AE report says `0/29 exact`, and the extended slices
remain `known-red`.

Current 8bpc rows:

| Case | Max diff | Mean diff | Nonzero px | Nonzero % | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| `case_0024` | `80` | `0.1781948061` | `1052452` | `50.7548%` | `known-red` |
| `case_0025` | `65` | `0.1739252990` | `959911` | `46.2920%` | `known-red` |
| `case_0026` | `45` | `0.1544129774` | `986899` | `47.5935%` | `known-red` |
| `case_0027` | `48` | `0.0673403742` | `479704` | `23.1339%` | `known-red` |

Source: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json`
and `refs/conformance/packaged_8bpc_manifest.json`.

### 16bpc classification

There are two distinct evidence views:

1. Historical byte-view/depth-gate near-miss (`2026-07-08`):

| Case | Max | Nonzero px | BBox `(x0,y0)-(x1,y1)` | Channel counts `(R,G,B,A)` |
| --- | ---: | ---: | --- | --- |
| `case_0024` | `1` | `3984` | `(232,328)-(1919,1079)` | `(2934,0,1050,0)` |
| `case_0025` | `1` | `12291` | `(0,0)-(1919,1079)` | `(3143,0,9148,0)` |
| `case_0026` | `1` | `2570` | `(265,222)-(1893,1019)` | `(1216,0,1354,0)` |
| `case_0027` | `1` | `489` | `(390,443)-(1893,941)` | `(442,13,40,0)` |

2. Current canonical true16 compare (`2026-07-11` / `2026-07-12` authority):

| Case | Max diff | Mean diff | Nonzero px | Status |
| --- | ---: | ---: | ---: | --- |
| `case_0024` | `2` | `0.3274211516` | `1051915` | `broad-field-export-residual-max-2` |
| `case_0025` | `2` | `0.2896231192` | `860084` | `broad-field-export-residual-max-2` |
| `case_0026` | `2` | `0.2681557436` | `900709` | `broad-field-export-residual-max-2` |
| `case_0027` | `2` | `0.1176097126` | `451535` | `broad-field-export-residual-max-2` |

Representative stored compare samples from the current true16 report all start on
`y=0` and show small `R/B` word deltas:

- `case_0024`: `(1,0) [2,0,0,0]`, `(4,0) [2,0,2,0]`
- `case_0025`: `(3,0) [0,0,2,0]`, `(14,0) [4,0,0,0]`
- `case_0026`: `(3,0) [0,0,4,0]`, `(6,0) [4,0,0,0]`
- `case_0027`: `(4,0) [2,0,0,0]`, `(21,0) [2,0,0,0]`

Source: `ae_pixel_16bpc_extended_exact.csv/json` under
`refs/reports/ae_validation_batch_olmdistancegradation_16bpc_depthgate_singlecase_reverify_20260709/`.

### Existing Mac AE probe facts

`case_0026` probe header:

- `invert=1`, `in_out=3`, `inside_threshold=158`, `outside_threshold=13`
- `render_mode=1`, `use_bg=1`, `interp=4`, `power=2.59740734`

`case_0027` probe header:

- same as `case_0026` except `render_mode=2`

For all 14 sampled points in both probe reports:

- `outside_x=0`
- `winner=inside-or-tie`
- `compose_input_x == field_x`

Representative sampled `field_x` values:

- `case_0026`: `(907,222)=0.121742934`, `(395,477)=0.161361381`,
  `(1589,579)=0.783686459`, `(898,670)=0.888987124`
- `case_0027`: `(1234,443)=0.237236261`, `(906,668)=0.929949105`,
  `(505,941)=0.98936832`, `(1893,719)=0.556998014`

`refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md`
adds that only `case_0026` currently has any located live points, and even there
the replay is still blocked by missing returned field raw words.

### Existing Windows return fact for the cleanest 16bpc witness

The `2026-07-08` Windows return for `case_0026` classified three representative
pixels as `export-quantization` and left one unresolved:

- `(395,477)`, `(1589,579)`, `(898,670)`: `export-quantization`
- `(907,222)`: `unresolved`

The unresolved pixel has:

- Windows exported RGBA8 `[255,0,0,255]`
- sampled PF16 store `[32645,0,129,65535]`

and the report explicitly says the simple export rule does not explain `B=0` from
store word `129` without a direct Windows PF16 store/export stop.

## INFERENCE

- `case_0024..0027` is not one cross-depth family with one fix.
  - In 8bpc it is a broad `known-red` current-binary failure family.
  - In 16bpc it is a small-residual family only in the older byte-view, but the
    canonical true16 authority keeps it open as `max=2`.
- The Mac AE probes make `case_0026` and `case_0027` the strongest control pair:
  existing sampled points already show the same inside-path handoff, and the main
  explicit parameter split is `Render Mode`.
- The `2026-07-08` Windows `export-quantization` result is real evidence for part
  of the byte-view residual, but it does not close the current canonical true16
  family by itself. The 2026-07-12 classifier is correct to keep this family open.
- `case_0024` and `case_0025` currently lack the live typed field/source witnesses
  that `case_0026` already partially has, so they are weaker next probes despite
  belonging to the same parameter cluster.

## Single Next Evidence

Request one hash-pinned Windows same-run typed witness package centered on the
`case_0026` / `case_0027` control pair, binding at matched contour coordinates:

`field raw word -> compose input/output -> render-mode branch -> PF16 store -> same-run true16 export`

If the package must collapse to one pixel, use `case_0026 (907,222)` first. It is
already the only partially bound live witness and remains the one unresolved point
in the existing Windows export-quantization return.

## Commands run for this classification

```sh
git status --short
rg -n "case_0024|case_0025|case_0026|case_0027" refs/conformance notes scripts mac tools refs/runtime_trace_support refs/windows_witness_specs refs/windows_returns
find refs -iname '*.csv' | rg 'distancegradation|olmdistancegradation|case002[4-7]|case_002[4-7]'
sed -n '1,220p' refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md
sed -n '1,220p' refs/conformance/olmdistancegradation_depthgate_quantization_return_intake_20260708.md
sed -n '1,260p' refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md
sed -n '1,260p' refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md
sed -n '1,240p' refs/conformance/olmdistancegradation_8bpc_current_binary_reconstruction_20260712.md
sed -n '1,240p' refs/reports/ae_single_case_distancegradation_depthgate_nearmiss_20260708/case_0026/field_debug_report.md
sed -n '1,240p' refs/reports/ae_single_case_distancegradation_depthgate_nearmiss_20260708/case_0027/field_debug_report.md
python3 - <<'PY'
import json
from pathlib import Path
p=Path('refs/reports/ae_validation_batch_olmdistancegradation_16bpc_depthgate_singlecase_reverify_20260709/reports/ae_pixel_16bpc_extended_exact.json')
obj=json.loads(p.read_text())
for item in obj['cases']:
    if item['id'] in [f'olmdistancegradation_extended__case_{n:04d}' for n in (24,25,26,27)]:
        print(item['id'], item['max_diff'], item['mean_diff'], item['nonzero_px'], item['samples'][:3])
PY
python3 - <<'PY'
import json
from pathlib import Path
for n in (24,25,26,27):
    p=Path(f'refs/reports/ae_host_validation_20260618_232926/cli_checks/olmdistancegradation_extended_normalized/candidate/_params/case_{n:04d}.json')
    obj=json.loads(p.read_text())
    vals={entry['name'].strip(): entry['value'] for entry in obj['params']['effects'][0]['params']}
    print(f'case_{n:04d}', vals['Invert'], vals['Outside Threshold'], vals['Render Mode'], vals['Interpolation Mode'], vals['Power'])
PY
```

Command results used here:

- worktree is dirty from other agents; no revert performed
- `ae_pixel_16bpc_extended_exact.csv/json` rows confirm `case_0024..0027` are
  still non-exact in current true16 authority
- param JSON confirms the `0026 -> 0027` split is `Render Mode` only
