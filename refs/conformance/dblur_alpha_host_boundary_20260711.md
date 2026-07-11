# DirectionalBlur Alpha Fade host-boundary closeout

## Verdict

Current evidence makes further Alpha Fade kernel tuning unjustified pending a
Windows boundary capture. The 2025 AEX choreography is grounded through the
complete raw callback, while the retained June 19 AE reference does not
identify the AEX generation or retain the exact input world seen by that AEX.
The case therefore remains `blocked-reference-provenance`, not `AE exact` and
not permission to tune PNGs. Host/provenance ownership is a strong inference,
not final proof until the requested PF worlds return.

## Measured facts

- The Mac callback input for the retained premultiplied PNG is exactly
  `round(premultiplied_rgb * 255 / alpha)`. Its packed RGBA8 SHA-256 is
  `abd939d253b6b955f2912f8ace74cb4c1fe19b44029479fb30bb095082c63ed8`.
- The Mac portable core output is byte-identical to the bytes written into the
  Mac PF output world. The callback ARGB8 SHA-256 is
  `cb1c843b9bcbcee8e37bfdf54208578888c70b11ed2de157e1a7c76d11df815c`.
- The resulting Mac AE PNG differs from the retained Windows PNG by RGB-only
  `max_diff=1`, `234049` channel bytes and `183121` pixels. Alpha is exact.
- Reconstructing the input with integer floor unpremultiplication reduces the
  modeled 2025-AEX/Windows-PNG residual to RGB-only `max_diff=1`, `22993`
  channel bytes. The complete actual-AEX wrapper consumed `557498777`
  instructions and produced raw ARGB8 SHA-256
  `7f64aa7caef89cbdf2bb86eee5f6b87f063fb2927e85e10e8abbce2d2fcd5bd9`.
- A real Mac AE render with the same floor-reconstructed input leaves `23053`
  channel bytes across `21778` pixels. The small 60-byte delta is consistent
  with the measured architecture-sensitive raw boundary; it does not explain
  the original 234049-byte family.
- Compiling the same portable source for arm64 and macOS x86_64 changes raw
  output at only `2055` channel bytes / `1646` pixels on the straight-palette
  probe. On the floor-input probe, the complete actual AEX and Mac callback
  differ at only `78` raw channel bytes.
- A 64-group floor/nearest input sensitivity sweep can overfit the retained
  image down to `12621` differing channel bytes, but no single arithmetic rule
  becomes exact. This is diagnostic only and must not become plug-in code.
- The June 19 manifest records AE `26.2x49`, Software renderer, parameters and
  timestamps, but no loaded AEX path, size, version or SHA-256. The official
  bundle contains distinct 2024 and 2025 DirectionalBlur binaries.

## Runner correction

`scripts/run_ae_single_case.py` now clears volatile AE environment keys before
applying the current run's values. Without this reset, a preceding
`OLM_AE_DISABLE_EFFECT=1` no-effect control can leak into the next rapidly
started AE process and silently invalidate that render.

A debug build compiled with `OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE=1` can use
`OLM_DBLUR_CAPTURE_PREFIX=/tmp/name` for Mac raw boundary capture. It writes
tightly packed input RGBA8, core output RGBA8, callback output ARGB8 and world
metadata. Normal builds contain no environment-triggered capture path.

## Required Windows proof

Executable request package:
`refs/runtime_trace_packages/olmdirectionalblur_front_alpha_host_boundary_2025_20260711.zip`.
It hash-gates the loaded module, binds the two worlds by PID/RBP/RBX/output
world, validates readable PF structures and buffers, and creates the return ZIP
automatically.

Use one same-run capture of `db_angle0_alpha_fade_hard_edges`:

1. Record the loaded `OLMDirectionalBlur.aex` path, file size, version and
   SHA-256. The known 2025 target is
   `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
2. For that hash only, capture the complete PF input world at
   `OLMDirectionalBlur+0x5267`, before the populate callback at `+0x6980`.
3. Capture the complete PF output world at `OLMDirectionalBlur+0x566a`, after
   the output Iterate8 callback at `+0x6b30` and before AE export.
4. Return rowbytes, width, height, extent/origin metadata and both row-stripped
   ARGB8 files. Both worlds must be `1920x1080`, 8bpc and from the same run.

If the loaded hash differs, do not install offset breakpoints. Return
`binary_identity_mismatch` with path/hash/version instead. A hash-pinned
current-AEX recapture is then the next action.

## Forbidden fixes

- Do not bake floor unpremultiplication into the released plug-in from this one
  lossy replay.
- Do not add a channel bias, subtract-one rule, spatial lookup or PNG-fit table.
- Do not call the Alpha Fade case `AE exact` from a modeled host transform.
- Do not treat the June 19 PNG as current-2025-AEX proof until binary identity
  or a hash-pinned recapture exists.

## Post-hardening verification

- Normal Universal `arm64/x86_64` plug-in build: passed. The installed binary
  SHA-256 is
  `afb83a83a4dcdeb3d6bef3fc4fe72e08035e7dbad24267bf3dffe7f598f9cc56`
  and contains none of the capture-environment or capture-filename strings.
- Instrumented Universal build with
  `OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE=1`: passed in a separate `/tmp` build root.
- Mac AE 26.3 Software regression `db_angle0_strength_sweep_small`: `max_diff=0`,
  `differing_bytes=0`, output/reference PNG SHA-256 both
  `bd1e82f2648cdf2f5f3c814608498b71fc4dba3ed518f4b3c52fb00320a96f9b`.
- Windows request ZIP integrity/static contract/pending-priority/staging smokes:
  passed. Request ZIP SHA-256 is
  `08465290715f7cdd766a1e374d39174c5f984028d71b48c17f3f62f8184ee66a`.

## Reproduction commands

```text
python3 scripts/run_ae_single_case.py --request-dir refs/reports/ae_single_case_dblur_frontonly_current_20260711/request --case-id db_angle0_alpha_fade_hard_edges --output-dir refs/reports/ae_single_case_dblur_frontonly_current_20260711/candidate_alpha_fade_premult_fixed --ae-env OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1 --ae-env OLM_AE_FORCE_NEW_PROJECT=1 --ae-env OLM_AE_FORCE_SOFTWARE=1 --ae-env OLM_AE_INPUT_ALPHA_MODE=PREMULTIPLIED --ae-env OLM_DBLUR_CAPTURE_PREFIX=/tmp/dblur_mac_callback_alpha_premult_fixed_20260711

python3 tools/emulation/dblur_fullrender_host_fixture_20260711.py --source /tmp/dblur_alpha_floor_request_20260711/input/directionalblur_context_scale_20260606__software__fr24__db_angle0_alpha_fade_hard_edges_before_effects.png --expected refs/reports/ae_single_case_dblur_frontonly_current_20260711/request/expected/directionalblur_context_scale_20260606__software__fr24__db_angle0_alpha_fade_hard_edges.png --output /tmp/dblur_alpha_floor_actualaex_20260711.json --host-output-raw /tmp/dblur_alpha_floor_actualaex_20260711.argb --downsample-num 1 --downsample-den 1 --angle 0 --brightness-gain 1 --size-variation 0 --front-strength 240 --front-alpha-fade 96 --front-sharp-tail 0 --back-strength 0 --back-alpha-fade 0 --back-sharp-tail 0 --noise-variation 0 --noise-type 1 --seed 1 --noise-offset 0 --thickness 10 --detour-rotate --detour-rowdriver --max-instructions 1500000000
```
