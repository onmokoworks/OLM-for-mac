# Bit-Depth Reference Strategy

The final conformance target covers 8bpc, 16bpc, and 32bpc, but references
should be expanded in phases so algorithm work stays grounded.

## Canonical Render Context

- Renderer: Windows AE Software render.
- GPU/CUDA: out of scope for the current conformance profile.
- `ADBE Force CPU GPU`: record as metadata only; do not use it for path
  selection.
- Record with every return:
  - AE version
  - project renderer / `project_gpu_accel_type`
  - project color settings
  - bit depth
  - input asset ID and checksum when possible
  - request ID and case ID
  - full effect parameter manifest

## Expansion Order

1. `8bpc`: stabilize binary-grounded IR and AE-host exact checks.
2. `16bpc`: reuse the same case IDs and inputs; add cases only when 16bpc
   exposes a new branch or quantization rule.
3. `32bpc`: define the comparator before claiming completion. If an epsilon is
   needed for float output, record it as an exception profile, not `AE exact`.

## 2026-06-25 Expansion Plan

`scripts/analyze_bit_depth_expansion_plan.py` turns the current normalized
8bpc Software exact audit into a request plan. The generated local report is:

- `refs/reports/bit_depth_expansion_plan_20260625/bit_depth_plan.md`

The first 16bpc request has been generated from that plan and returned from
Windows AE:

- Request JSON:
  `refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json`
- Project-local Windows zip:
  `handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`

Current machine decision:

- `reference-covered-compare-pending`

Included feature groups are only the ones with normalized 8bpc Software exact
evidence in `refs/reports/software_reference_canonicalization_8bpc.json`:

| Feature group | Cases | Next depth |
| --- | ---: | --- |
| `OLMBlur` | 7 | `16bpc` |
| `OLMColorKey` | 9 | `16bpc` |
| `OLMToonDilate` | 3 | `16bpc` |
| `OLMDistanceGradation basic` | 12 | `16bpc` |
| `OLMDistanceGradation extended` | 16 | `16bpc` |
| `OLMDistanceGradation blur` | 1 | `16bpc` |

Total: 48 cases across 4 plug-ins. This plan deliberately excludes blocked
or binary-unresolved features such as RadialBlur, KiraKira, DirectionalBlur,
and Smoother2 legacy key/gamma. It also excludes 32bpc until the float compare
policy is fixed.

Preflight verification for the project-local zip passed on 2026-06-25:

- `python3 refs/scripts/verify_reference_request_package.py handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`
- `python3 refs/scripts/smoke_generate_bitdepth_reference_request.py`

The packaged request contains one `software_16bpc` / `SOFTWARE` render set and
48 unique cases: OLMBlur 7, OLMColorKey 9, OLMToonDilate 3, and
OLMDistanceGradation 29.

The Windows return was imported on 2026-06-25:

- Imported manifest:
  `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json`
- Tracked receipt:
  `refs/conformance/bitdepth_16bpc_reference_return_20260625.md`
- Verification:
  `verify_reference_request_result.py` reports 45 required request cases and
  45 matching rendered cases for `software_16bpc`.
- PNG format spot check:
  sampled output is `16-bit/color RGBA`.

The Mac AE 16bpc comparison has now been run. It is not `AE exact`.

Mac AE validation packages were generated on 2026-06-25:

- `handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/bitdepth16_olmblur_exact.zip`
- `handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/bitdepth16_olmcolorkey_exact.zip`
- `handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/bitdepth16_olmdistancegradation_basic_exact.zip`
- `handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/bitdepth16_olmdistancegradation_extended_exact.zip`
- `handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/bitdepth16_olmdistancegradation_blur_exact.zip`

A single bundle containing those five request zips plus verification
instructions was also generated:

- `handoffs/ae_host_validation/20260625_222505_20260625_16bpc_mac_ae_validation_bundle/olm_ae_pixel_validation_20260625_16bpc_mac_ae_validation_20260625_222505.zip`

Mac AE 2026 rendered all 45 cases locally. The first local run produced
12/45 exact, but that result is superseded because the render JSX skipped
manifest parameters that provided `path` / `match_name` but no `path_full`.
After fixing `scripts/ae_pixel_validation_render.jsx`, native 16bit comparison
against the Windows Software references produced 15/45 exact. Rerendering after
the binary-grounded ColorKey `Force Lower Precision` epsilon fix and the
DistanceGradation Inside/all-opaque no-source rule improved the current slice
to 17/45 exact:

- Result ledger:
  `refs/conformance/bitdepth_16bpc_mac_ae_validation_20260626_distancegradation_inside_no_source.md`
- Residual classifier:
  `refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_distancegradation_inside_no_source.md`

The residual classes were then reverified on 2026-06-26 after fixing
16-bit ImageMagick endian decoding in `refs/scripts/verify_manifest.py`.
This did not change the exact count, but it materially corrected the 16bpc
residual amplitudes, especially for OLMBlur:

- Reverify batch:
  `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/`
- Reverify residual classifier:
  `refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_2335_endian_fix.md`

The current residual classes are:

| Class | Count | Meaning |
| --- | ---: | --- |
| `full-scale-mismatch` | 3 | too large to treat as rounding; inspect color management, branch selection, or effect-path mismatch |
| `large-structured-mismatch` | 17 | structured residual after params are applied; likely implementation-path mismatch, not broad harness failure |
| `candidate-looks-8bit-quantized` | 1 | candidate output looks quantized compared with the Windows 16bpc reference |
| `olmblur-16bpc-near-1lsb` | 6 | OLMBlur residuals are only about one AE 16bpc output unit, appearing as `max_diff=2` in exported PNG space |
| `olmblur-16bpc-legacy-border-plus-near-1lsb` | 1 | same near-1LSB OLMBlur family plus a small Legacy-only border/seed anomaly |

By plug-in slice:

| Slice | Exact | Residual |
| --- | ---: | ---: |
| `OLMBlur` | 0/7 | 7, now classified as 6 near-1LSB and 1 legacy-border-plus-near-1LSB |
| `OLMColorKey` | 8/9 | 1, now identified as `case_0009` on `Lab76 + Force Lower Precision=3 + Edge Thin Amount=25 (Distance Type=2)` with `Edge Blur Amount=0` |
| `OLMDistanceGradation basic` | 8/12 | 4 |
| `OLMDistanceGradation blur` | 0/1 | 1 |
| `OLMDistanceGradation extended` | 1/16 | 15 |

2026-06-28 OLMBlur follow-up audit:
`refs/conformance/olmblur_16bpc_word_delta_audit_20260628.md` re-read the
same PNGs with the fixed 16bpc path and inferred the OLMBlur near-1LSB family
more concretely as sign-mixed `+/-1` PF_Pixel16 word deltas. The only larger
OLMBlur 16bpc witness remains Legacy `case_0007 (0,0)`, which is separated as a
border/seed/all-same issue rather than a general blur-kernel problem.

The remaining 16bpc investigation is now narrowed to binary/runtime proof, not
another Windows PNG reference request. `scripts/print_next_olm_action.py`
currently reports the project-local runtime trace package
`olm_runtime_trace_olmdistancegradation_16bpc_case0026_x_witness_20260628.zip`
as the highest-value next action.

## 2026-06-28 32bpc Probe Preview

The request generator can now produce a `32bpc` probe request, but the generated
request is deliberately kept out of `refs/reference_requests/` so it does not
preempt the active 16bpc binary-proof wait.

- Preview:
  `refs/reports/bit_depth_32bpc_probe_plan_20260628/request_preview.json`
- Notes:
  `refs/reports/bit_depth_32bpc_probe_plan_20260628/README.md`

This preview is not completion evidence. It is a way to ask the Windows helper
whether a float-preserving output path is available for the 45 normalized
8bpc-exact cases. Move it into `refs/reference_requests/` only when 32bpc
probing is intentionally scheduled.

A focused variant now also exists for the already-strong ColorKey slice:

- Preview:
  `refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260630/request_preview.json`
- Notes:
  `refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260630/README.md`

This uses the same generator with `--plugin OLMColorKey` and reduces the probe
to the 9 normalized `OLMColorKey` cases when a smaller Windows turn is more
useful than the mixed 48-case batch.

A second focused preview now exists for the already-exact ToonDilate slice:

- Preview:
  `refs/reports/bit_depth_32bpc_toondilate_probe_plan_20260630/request_preview.json`

This is the same style of probe but reduced to the 3 normalized
`OLMToonDilate` cases. It is useful when we want a tiny float-output turn
instead of resending the full mixed batch.

## 2026-07-01 OLMColorKey 32bpc Next Step

The next clean 32bpc move stays plugin-scoped and probe-only: regenerate the
focused `OLMColorKey` float-output request as a self-contained preview bundle,
then send that smaller Windows turn instead of reopening the mixed 48-case
batch.

- Preview:
  `refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260701/request_preview.json`
- Notes:
  `refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260701/README.md`

Generate or refresh that bundle from the repo root with:

```sh
python3 scripts/generate_bitdepth_reference_request.py \
  --bit-depth 32bpc \
  --plugin OLMColorKey \
  --request-id olm_bitdepth_32bpc_colorkey_probe_20260701 \
  --preview-dir refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260701
```

The generator now writes both `request_preview.json` and a companion
`README.md` into the preview directory. Keep this request out of
`refs/reference_requests/` until the Windows helper is intentionally scheduled
for a 32bpc float-output turn.

Operational note on 2026-06-30:

- `OLMToonDilate` had been marked `bitdepth-expand` in the ledger for a while,
  but it was absent from the bit-depth plan only because
  `scripts/analyze_soft_reference_canonicalization.py` still used a fixed
  feature list that omitted ToonDilate.
- This was a planning/input gap, not negative evidence against ToonDilate.
- After the canonicalization input is regenerated, ToonDilate should travel in
  the same low-risk expansion lane as other normalized 8bpc exact slices.

For that remaining ColorKey case, sampled residual pixels are input-identical
in the Mac candidate and transparent in the Windows reference. That makes the
active question a positive Edge Thin dilate / seed-world difference, not an
Edge Blur blend path.
The 2026-06-26 witness extraction sharpens this further: `12436 / 12597`
residual pixels are opaque black `[0,0,0,65535]`, and representative witness
islands sit `8..43` taxicab pixels away from the naive Lab76 hit set while
still being removed by Windows. So this is no longer consistent with a small
`65535 vs 32768` normalization tweak or a simple `hit + 25px` dilate model.
2026-06-27 local re-analysis narrows it further: using the exported 16bpc
before-effects PNG, `Lab76 hit + taxicab <= 25` is only `370px` closer to the
Windows reference than the real Mac AE candidate (`12227px` vs `12597px`).
More importantly, the current Mac candidate matches a local epsilon sweep built
with `epsilon=0` or `1/65536`, while the intended source-level
`Force Lower Precision=3` rule (`0.5/255`, UI string `8bit`) overshoots by
exactly those `370px`. So the next ColorKey question is narrower than a broad
seed-world rewrite: either the live 16bpc AE path is not taking the intended
Force Lower Precision branch, or exported before-effects PNG reconstruction is
still a slightly imperfect stand-in for the live AE input world.

Return intake is covered by `refs/scripts/smoke_verify_bitdepth_reference_result.py`,
including a synthetic 45-case mixed-effect manifest and the
`scripts/intake_olm_return.py --kind win-reference` path. Use this command when
the Windows render return arrives:

```sh
python3 scripts/intake_olm_return.py path/to/returned_16bpc_reference.zip \
  --kind win-reference \
  --request refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json \
  --set-id olm_bitdepth_16bpc_normalized_exact_20260625 \
  --quick
```

## Request Shape

Each future bit-depth request should keep the same logical case ID and add a
bit-depth profile suffix only where file naming requires it. Example:

```json
{
  "request_id": "olmblur_conformance_bitdepth_YYYYMMDD",
  "render_sets": [
    {
      "id": "software_8bpc",
      "project_gpu_accel_type.current_name": "SOFTWARE",
      "bit_depth": "8bpc",
      "required": true
    },
    {
      "id": "software_16bpc",
      "project_gpu_accel_type.current_name": "SOFTWARE",
      "bit_depth": "16bpc",
      "required": true
    },
    {
      "id": "software_32bpc",
      "project_gpu_accel_type.current_name": "SOFTWARE",
      "bit_depth": "32bpc",
      "required": true
    }
  ]
}
```

## Comparator Expectations

- `8bpc`: byte exact, `max_diff=0`.
- `16bpc`: integer sample exact, zero diff in the exported 16bpc comparison
  representation.
- `32bpc`: exact float comparison only when the return format preserves
  floating-point samples, such as EXR or a raw float dump. A PNG exported from a
  32bpc project is a smoke/probe artifact, not completion evidence. If the
  Windows runner cannot return float-preserving output, record that as
  `32bpc-probe-only` and do not claim `AE exact`.

## Promotion Rule

A feature can be called complete only for the bit-depth slices that have:

1. Windows Software reference.
2. Mac AE render for the same manifest.
3. Zero-diff comparison for that bit depth.
4. Binary-grounded IR for the algorithm path.
