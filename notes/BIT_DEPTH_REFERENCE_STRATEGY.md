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

