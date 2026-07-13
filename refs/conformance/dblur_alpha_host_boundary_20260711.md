# DirectionalBlur Alpha Fade host-boundary proof

## Verdict

The requested same-run Windows capture is accepted. It proves the exact 2025
AEX identity, complete 8bpc PF input/output worlds, and AE host conversion on
both sides of the plug-in. The retained June 19 PNG is not output from this
current binary and is no longer a valid oracle for this case.

Against the new hash-pinned reference, the current Mac AE render remains
`known-red`: `max_diff=3`, `980` channel values and `563` pixels differ. The
portable Alpha Fade path is still `binary-grounded`, but this feature is not
`AE exact`.

Current classification:

- `correctness_status`: `binary-grounded / known-red`
- `host_status`: `host-debuggable`
- `work_lane`: `binary-proof`

## Accepted Windows run

- Request: `olmdirectionalblur_front_alpha_host_boundary_2025_20260711`
- Status: `answered`
- Case: `db_angle0_alpha_fade_hard_edges`
- AE input alpha mode: `PREMULTIPLIED`
- Loaded path:
  `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMDirectionalBlur.aex`
- Loaded AEX SHA-256:
  `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`
- File size: `56832`
- PE image size: `77824`
- Both worlds: `1920x1080`, rowbytes `7680`, origin `(0,0)`, full extent
- Both worlds share invocation `00000088bb4f3110` and context
  `00000088bb4f4050`.
- Input ARGB8 SHA-256:
  `671ae54fcf5eaca65986389034c63ce47c0bce9b842b193a652a87e195d05dcd`
- Output ARGB8 SHA-256:
  `1c53bb46bde66355ac77059b29be237e4c800ddd3931e9db4d0181b25af644b1`

The accepted return is archived under `refs/returns/windows` locally and under
the NAS `old` queue. A convenient ignored local reference set is
`refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex`.

## Host arithmetic

The captured worlds close both host transforms byte-for-byte:

1. PNG to PF input world uses straight RGB reconstructed from the premultiplied
   PNG with integer half-up unpremultiplication:
   `rgb_straight = (rgb_premult * 255 + alpha / 2) / alpha`, with integer
   division and zero RGB when alpha is zero. Modeled versus captured PF input:
   `max_diff=0`, `differing_values=0`.
2. PF output world to returned PNG uses integer half-up premultiplication:
   `rgb_png = (rgb_straight * alpha + 127) / 255`. Modeled versus returned PNG:
   `max_diff=0`, `differing_values=0`.

This proves the host boundary. Neither transform belongs inside the plug-in
kernel.

## Reference correction

The current hash-pinned Windows render has PNG SHA-256
`552a055bfaca2472d32eafb5d60d4d47f909c2808106344bf1b16cdb2a8ff8d4`.
The retained June 19 PNG has SHA-256
`d7ed7ea80324961d59a9fe3d2c841b6efea47136debbeca6d8685e8337c111bc`.
They differ at `max_diff=3`, `234845` channel values and `183482` pixels,
including `30` alpha values. The old manifest did not record its loaded AEX;
the new same-run proof demonstrates that it is not current-2025-AEX truth.

The current Mac candidate compared with the new Windows render is much closer,
but not exact:

| Comparison | max | Values | Pixels | A | R | G | B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mac AE PNG vs current Windows PNG | 3 | 980 | 563 | 30 | 218 | 394 | 338 |
| Mac arm64 raw vs Windows raw | 4 | 1030 | 587 | 30 | 231 | 421 | 348 |
| Mac x86_64 raw vs Windows raw | 4 | 468 | 226 | 30 | 129 | 174 | 135 |
| Mac arm64 raw vs Mac x86_64 raw | 1 | 562 | 361 | 0 | 102 | 247 | 213 |

A fresh Mac AE `26.3x87` Software render using the corrected one-case request
reproduces the PNG row exactly: `max=3`, mean `0.0001263503`, `563/2073600`
pixels. Its exact-check report is
`refs/reports/ae_single_case_dblur_front_alpha_current_2025_aex_20260711/reports/current_mac_exact.json`.

The x86_64-versus-Windows residual is confined to column `x=1308`, rows
`y=184..517`. The broader arm64-versus-x86_64 residual spans other locations.

## Architecture split

The current Gaussian table builder calls `std::exp(float)`. Rebuilding the
same source so that the float argument is evaluated with double `exp` and then
cast back to float makes the arm64 raw output byte-identical to the macOS
x86_64 output:

- arm64 current raw SHA-256:
  `cb1c843b9bcbcee8e37bfdf54208578888c70b11ed2de157e1a7c76d11df815c`
- macOS x86_64 raw SHA-256:
  `65e79246d482eb7f0ad01c72fe5c367b39b0fe0dbe6ab47032ef21fe982ce21f`
- arm64 double-exp probe SHA-256:
  `65e79246d482eb7f0ad01c72fe5c367b39b0fe0dbe6ab47032ef21fe982ce21f`

This proves that the broad Mac architecture split comes from platform `expf`
behavior. It does not prove that double-exp matches Windows: the remaining
`468` raw values on one column still differ from the Windows UCRT build.

The AEX imports `expf` from the Universal CRT. `FUN_180001830` constructs the
Gaussian tables with float arithmetic, a double-width `+1e-5` denominator
step, a float cast, and then `expf`. The live Alpha Fade case uses table sizes
`96` for the prepass and `240` for the scatter stage.

## Next proof

The narrow next action is to capture the exact UCRT `expf` result bits for all
Gaussian arguments used by the `n=96` and `n=240` tables. This can be done on
Windows without AE. Replay those exact table words locally and compare the
single residual column.

Prepared request:
`refs/runtime_trace_packages/olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711.zip`
(SHA-256
`2d89928c03b0d131acc07fb0c4f1e31f5ce61184f4a232c2f4c50aa9b9849b6e`).
It requires 64-bit x64 PowerShell, records the exact `ucrtbase.dll` identity,
and returns 336 rows without launching AE.

`scripts/intake_latest_windows_return_from_share.py` automatically runs
`scripts/analyze_dblur_ucrt_expf_return.py` for this request before archiving
the return. Invalid architecture, missing rows, argument-bit drift or artifact
hash mismatch leaves the ZIP in `new` and fails closed. A validated return also
emits a provenance-only table JSON for deterministic replay.

If the UCRT table closes the residual, replace the platform-libm dependency
with a deterministic, binary-grounded table generator and rerun Mac AE. If it
does not, capture the first affected prepass/scatter call and compare its
destination, denominator and alpha buffers. The current boundary capture does
not contain those intermediate buffers, so it cannot yet distinguish the
`n=96` prepass from the `n=240` scatter table.

## Forbidden fixes

- Do not use the June 19 PNG as current-AEX truth.
- Do not add channel bias, subtract-one, spatial lookup or case-specific pixel
  patches.
- Do not bake host unpremultiplication or premultiplication into the kernel.
- Do not promote double-exp merely because it removes the Mac architecture
  split; Windows exactness is still unproven.
- Do not call Alpha Fade `AE exact` while any value differs.

## Verification

- Runtime-return verifier: one answered request, hash and same-run world gates
  passed.
- Input half-up reconstruction versus captured PF input: exact.
- Output half-up premultiplication versus returned PNG: exact.
- Current Mac AE versus current Windows AE: known-red as tabulated above.
- Fresh corrected-reference Mac AE exact verifier: expected failure, one case,
  `max=3`, `nonzero_px=563`.
- `python3 refs/scripts/smoke_list_olm_return_candidates.py`: passed after
  adding portable `RETURN_RUNTIME_TRACE.json` coverage.
