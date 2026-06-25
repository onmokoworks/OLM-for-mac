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

The first 16bpc request has been generated from that plan:

- Request JSON:
  `refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json`
- Project-local Windows zip:
  `handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`

Current machine decision:

- `request-16bpc-for-normalized-8bpc-exact-features`

Included feature groups are only the ones with normalized 8bpc Software exact
evidence in `refs/reports/software_reference_canonicalization_8bpc.json`:

| Feature group | Cases | Next depth |
| --- | ---: | --- |
| `OLMBlur` | 7 | `16bpc` |
| `OLMColorKey` | 9 | `16bpc` |
| `OLMDistanceGradation basic` | 12 | `16bpc` |
| `OLMDistanceGradation extended` | 16 | `16bpc` |
| `OLMDistanceGradation blur` | 1 | `16bpc` |

Total: 45 cases across 3 plug-ins. This plan deliberately excludes blocked
or binary-unresolved features such as RadialBlur, KiraKira, DirectionalBlur,
and Smoother2 legacy key/gamma. It also excludes 32bpc until the float compare
policy is fixed.

Preflight verification for the project-local zip passed on 2026-06-25:

- `python3 refs/scripts/verify_reference_request_package.py handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`
- `python3 refs/scripts/smoke_generate_bitdepth_reference_request.py`

The packaged request contains one `software_16bpc` / `SOFTWARE` render set and
45 unique cases: OLMBlur 7, OLMColorKey 9, and OLMDistanceGradation 29.

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
- `32bpc`: exact float comparison if the return format preserves floats;
  otherwise define an explicit epsilon profile before using the result.

## Promotion Rule

A feature can be called complete only for the bit-depth slices that have:

1. Windows Software reference.
2. Mac AE render for the same manifest.
3. Zero-diff comparison for that bit depth.
4. Binary-grounded IR for the algorithm path.
