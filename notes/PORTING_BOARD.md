# OLM Porting Board

Updated: 2026-06-06

Goal: port Windows OLM AEX plug-ins to Apple Silicon/macOS, using Ghidra/GhidraMCP
analysis plus Windows PNG/manifest references, with AE-free CLI verification where
possible and final AE plug-in validation.

## Current Infrastructure

- Ghidra headless export works via `scripts/ghidra_export_one.sh`.
- GhidraMCP HTTP endpoint works at `127.0.0.1:8080` when Ghidra GUI has a program open.
- Direct helper: `scripts/ghidra_http.py`.
- AE-free harness smoke test passes via `python3 refs/scripts/smoke_algorithm_harness.py`.
- Aggregate AE-free algorithm smoke passes via `python3 refs/scripts/smoke_all_algorithm_clis.py`;
  known experimental scaffolds are expected as `DIFF-observed`.
- Mac plug-in build verification passes via `scripts/build_all_mac_plugins.sh`.
  The script recreates ignored AE SDK symlinks, builds `ColorKeep`, `OLMBlur`,
  `OLMColorKey`, `OLMDirectionalBlur`, `OLMRadialBlur`, `OLMToonDilate`,
  `OLMKiraKira`, `OLMDistanceGradation`, `OLMSmoother`, and `OLMSmoother2`
  in Debug, checks
  `arm64`/`x86_64` slices, and runs `codesign --verify`.
- Mac plug-in package export works via `scripts/package_mac_plugins.sh`.
  It can build/verify first or use `--skip-build` after a verified build, then
  writes a zip for AE-host install containing the 10 `.plugin` bundles,
  `INSTALL.txt`, `AE_VALIDATION_CHECKLIST.txt`,
  `AE_VALIDATION_RESULT.template.json`, and a JSON manifest. Returned AE host
  validation JSON can be checked with `scripts/verify_ae_validation_result.py`.
- Windows references imported under `refs/win_references/20260604_olm/`.
- Extra Windows references imported under `refs/win_references/20260605_extra/`.

## Render Path Caution

Every current reference manifest records `Compositing Options > GPU Rendering`
with `match_name = ADBE Force CPU GPU` and value `1`. That value does **not**
identify the actual AE render path. Windows AE 2025 (`25.2x131`) kept this
value at `1` under both Project Settings GPU Acceleration modes:

- CUDA: `project_gpu_accel_type.current_name = CUDA`, raw `1813`
- Software Only: `project_gpu_accel_type.current_name = SOFTWARE`, raw `1816`

OLM plug-in UIs also do not appear to expose a visible GPU Rendering button for
these effects. Keep `ADBE Force CPU GPU` in manifests as a reference property
only; record `project_gpu_accel_type` separately and use that field when
comparing CUDA vs Software renders. Local source/string survey found no AE GPU
selector flag such as `PF_OutFlag2_SUPPORTS_GPU_RENDER_F32` in the mac ports,
and Windows OpenCL/CUDA/OpenCV traces are obvious only in some AEXs
(`DistanceGradation`, `OLMKiraKira`, `OLMToonDilate`). Treat remaining
boundary/classifier residuals as an unresolved render-path or implementation
gap, not automatically as "GPU vs CPU".

## Reference Sets

Base `20260604_olm` set:

| Plugin | Cases | Notes |
|---|---:|---|
| OLMDirectionalBlur | 9 | Has before/effect PNG pairs; cases 1-3 have incomplete `selected_layer_effect_count`; cases 6/7 appear duplicate. |
| OLMBlur | 7 | Has before/effect PNG pairs; cases 1/2 have identical output despite different bias direction. |
| OLMColorKey | 9 | Has before/effect PNG pairs; case 4 is identical to before-effects input. |
| OLMKiraKira | 3 | Has before/effect PNG pairs. |
| OLMRadialBlur | 13 | Has before/effect PNG pairs; cases 3-5 appear duplicate. |
| OLMSmoother | 3 | Has before/effect PNG pairs. |
| OLMToonDilate | 4 | `case_0004` records `OLM RadialBlur`; treat as RadialBlur reference/side case. |

Extra `20260605_extra` set imported from Downloads zips:

| Folder | Cases | Effect | Immediate use |
|---|---:|---|---|
| OLMDistanceGradation | 30 | `OLM Distance Gradation` | First Distance Gradation PNG/manifest reference set. `case_0030` has no selected effect and should be treated as identity/reference-only unless needed. |
| OLMRadialBlur_img2 | 30 | `OLM RadialBlur` | Additional Blur Type 2 / Rotation-style references for RadialBlur work. |
| OLMSmoother2 | 12 | `OLM Smoother v2` | First Smoother v2 PNG/manifest reference set. |

The extra manifests are Windows AE `25.2x131`, comp `1920x1080`, 8 bpc,
24 fps. Import integrity check passed: every manifest `frame` and
`before_effects_frame` exists, and `verify_manifest.py` self-checks passed on
`case_0001` for all three folders.
First CLI probe against the new RadialBlur set also works:
`OLMRadialBlur_img2 case_0026` with current C++ rotation scaffold reports
`max=255 mean=7.4415`, so the set is usable as a red measurement target for
future Rotation work.

## Suggested Porting Order

1. `OLMBlur`: existing Mac source has a compact blur kernel and reference data exists.
2. `OLMDirectionalBlur`: Mac plugin and Python/C++ direct/rotated CLI scaffolds exist; continue row-driver/host-edge RE, not initial source discovery.
3. `OLMColorKey`: reference exists; separate from already-ported `ColorKeep`.
4. `OLMRadialBlur`: Mac plugin exists for Zoom/no-inner/no-noise plus outer-only Rotation/noise-off; continue Inner/Edge Fade diagnostics, especially +0x10/+0x14 and 0xf250/0xf252 coupling.
5. `OLMSmoother` / `OLMSmoother2`: existing work exists, but algorithm is more complex.
6. `OLMToonDilate`: pure cases 1-3 are now CLI-characterized and have a Mac plug-in build; case 4 remains a mixed RadialBlur reference.
7. `OLMKiraKira`: Mac plugin exists and now uses all-ray two-temp/no-fastpath; simple Mat/ROI/`dst=` aliasing probe is neutral, so remaining work is destination canvas/final composition/pre-post ray details.

## Verification gates

`run_reference_test.py` now forwards `--max-diff / --mean-diff /
--nonzero-px-percent` to `verify_manifest.py`, so a smoke test can assert a
known-good residual as a **regression guard** (default is still 0 = exact).
Current smoke status:

- `smoke_olmblur_cli.py` (cases 1-7): exact gate for cases 1/2/4 plus
  residual gate for cases 3/5/6/7 at max-diff 1 / mean 0.01 / nz 3.0%,
  **ok=7**. Keeping the gates separate prevents exact cases from regressing
  inside the known rounding-level tolerance.
- `smoke_olmcolorkey_cli.py` (cases 1-4): exact gate, **ok=4**.
- `smoke_olmcolorkey_extended_cli.py` (cases 5-7): exact gate for case 7 plus
  residual gate for cases 5/6 at max-diff 255 / mean 0.31 / nz 0.49%,
  **ok=3** — guards the known erode boundary shell without weakening the
  exact no-residual case.
- `smoke_olmcolorkey_edgeblur_cli.py` (cases 8-9): gated at max-diff 255 /
  mean 1.26 / nz 50.0%, **ok=2** — exploratory Edge Blur/Lab76 regression guard.
- `smoke_olmcolorkey_rust_cli.py` (cases 1-9): Rust compatibility CLI,
  **ok=9** under the same RGB/Edge Thin/Edge Blur gates as the current Python/C++
  scaffolds. Use it as a memory-safe cross-check, not yet as the AE plug-in
  entrypoint.
- `smoke_olmtoondilate_cli.py` (1-3): gated at max-diff 255 / mean 4.0 /
  nz 1.7% (known boundary residual), **ok=3** — guards against regressing worse.
- `smoke_olmdistancegradation_cli.py` (12 stable cases): gated at max-diff 7 /
  mean 0.11 / nz 22.0%, **ok=12**. This covers cases
  1/2/3/4/5/6/7/9/15/17/18/19; omitted blur/constant/interpolation cases remain
  red measurement targets rather than promoted green behavior.
- `smoke_olmsmoother_cli.py` (1-3): intentionally **not** gated green; the CPU
  MLAA path diverges structurally from the current reference (kept honest as DIFF).
- `smoke_olmsmoother2_cli.py` (20260605_extra cases 1-4): intentionally
  **not** gated green. It drives `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`
  through the new C++ CLI. 2026-06-05 disasm-first fix for the
  Color Key + Invert active-palette path changed case_0002 from
  `mean=41.8427` to `mean=0.0216`; the non-invert scalar-key path changed
  case_0003 from `1.3899` to exact and case_0004 from `1.3052` to `0.0189`.
  A follow-up writeback-premultiply fix, grounded in `FUN_1800036e0`, changed
  no-key case_0001 from `mean=0.4304` to `0.1832` without regressing key paths.
  Current measurements: case_0001 `0.1832`, case_0002 `0.0216`,
  case_0003 `0.0000`, case_0004 `0.0189`.
  `notes/OLMSmoother2_ASM_FACTS.md` now records the objdump/disasm-confirmed
  class-plane generation facts. For `case_0001`, frame setup and class-plane
  generation match the observed assembly closely, and the gross straight-vs-
  premultiplied writeback mismatch is fixed, so the remaining no-key residual
  should be investigated in polygon dispatch / helper sampling or finer
  color-space/writeback details rather than by tuning class-plane thresholds.
  2026-06-06 `idx=0` four-corner suppression/scaling diagnostic is negative:
  `none=0.1832`, `suppress=0.2720`, `half=0.2069`, `quarter=0.2349`.
  This rules out a simple over-strong corner-weight fix; next no-key work should
  split the class-plane source from the `FUN_1800104d0` sample source.
  2026-06-06 source/class-plane timing split is also negative:
  `none=0.1832`, `sample-pre-setup=0.4606`, `class-pre-setup=0.2049`,
  `sample-pre-gamma=0.4606`, `class-pre-gamma=0.2049`. Because both
  diagnostics worsened, stop blind tuning and use
  `refs/reference_requests/smoother2_no_key_grid_20260606.json` for the next
  Windows reference pass.
- `smoke_olmsmoother2_keypaths_cli.py` (20260605_extra cases 2-4): green
  regression gate for the objdump/disasm-confirmed key paths. Gated at
  `max<=95`, `mean<=0.022`, `nonzero<=0.15%`; current result **ok=3**.
- `smoke_all_algorithm_clis.py`: one-command aggregate. It runs all green
  smokes plus known-red measurement scaffolds and treats `[DIFF]` on red
  scaffolds as expected observation rather than a missing/failed CLI.
- `smoke_olmradialblur_cpp_inner_polar_valid_probe_cli.py`: known-red C++
  Inner diagnostic for the polar-grid base/validity buffer. It compares strict
  in-image validity with an AEX Repeat Border-style loose integer validity
  (`-2 < int(coord) < size`). Current result is effectively neutral:
  strict `case_0011/0012/0013 mean=25.2972/10.6222/21.2910`;
  `aex-repeat` `mean=25.1925/10.6245/21.2894`. Do not promote this to the
  production path unless later asm facts require it.
- `smoke_olmradialblur_cpp_inner_prepass_factor_probe_cli.py`: known-red C++
  Inner diagnostic for the `FUN_180002780` `+0x14` factor buffer. Strength-span
  factor modes `alpha/one/valid` are all bad for case_0011
  (`88.4305/90.9893/90.9893` mean). Edge-fade factor modes are currently
  indistinguishable because the inner reference cases have Edge Fade=0. If
  `+0x14` becomes the deciding ambiguity, ask Windows for RadialBlur Inner
  refs with nonzero Edge Fade or Size Variation instead of guessing.

## ASM-First Porting Flow

Use this order for every unresolved algorithm path:

1. Treat `disasm/*.aex.asm.txt` / `llvm-objdump` as the primary source of
   truth for offsets, branch gates, constants, packed return values, and enum
   mapping.
2. Use `decomp/*.aex.c.txt` as a navigation aid only. When decomp offset names
   disagree with asm, prefer asm and record the discrepancy.
3. Port only behavior with an asm/decomp reason. Keep image-diff parameter
   sweeps as default-off diagnostic probes, not as production fixes.
4. Verify with the smallest relevant `smoke_*.py` first, then the quick
   aggregate, then the full aggregate when red-measurement scaffolds might have
   changed.
5. Record confirmed facts in a `notes/*_ASM_FACTS.md` or plugin RE note before
   moving on, including negative evidence from probes.
6. If the remaining diff cannot be distinguished from AE renderer/project
   setting behavior with the current references, stop that path and request a
   targeted Windows reference instead of guessing.

For OLMSmoother2 specifically, the 2026-06-05 asm pass confirmed that
`FUN_18000ab00` is the simple center-residual plus weighted-sample accumulator,
so the remaining `case_0001` work should stay focused on polygon/sample
generation, frame setup, or finer writeback/color-space details. The
`FUN_1800036e0` final writeback path does premultiply RGB by alpha when its
writeback flag byte is set; enabling that path for the port improved no-key
`case_0001` from `mean=0.4304` to `0.1832`. A follow-up diagnostic confirmed
the residual is still dominated by `FUN_18000c280` switch index `0x00`
(`15280/17000` large-diff pixels), but the four corner helper constants match
the AEX `.rdata`; the optional `FUN_18000ae10` pruning block is gated by
`SMParams+0x70` and should not run for no-key `case_0001`.

Latest aggregate:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py
```

Summary: harness, ColorKeep, OLMBlur build/smoke, OLMColorKey RGB/Edge
Thin/Edge Blur/C++/C++ Edge Blur, OLMToonDilate, OLMSmoother build, OLMRadialBlur tiny Rotation,
OLMRadialBlur Zoom, OLMRadialBlur Zoom Offset, OLMRadialBlur C++ Zoom Offset,
OLMRadialBlur C++ Zoom, and OLMToonDilate C++ build/smoke all passed. OLMSmoother, broad OLMRadialBlur Rotation,
OLMRadialBlur Inner, OLMDirectionalBlur Python/C++ direct plus C++ rotated/gather
probes, the OLMDirectionalBlur rotated-preserve-alpha split, OLMKiraKira, and
the OLMKiraKira Brightness probe all produced expected DIFF measurement output.

## Status

| Plugin | Win Ref | Ghidra Dump | Mac AE Source | AE-Free CLI | Reference Diff |
|---|---|---|---|---|---|
| ColorKeep | none in 20260604 set | yes | complete-ish | smoke CLI works | synthetic smoke ok |
| DistanceGradation | yes, 20260605_extra | yes | complete-ish | Python CLI works | 12-case smoke OK (`max<=7`, `mean<=0.11`) |
| OLMBlur | yes | yes | in progress | C++ CLI works | 3 exact, 4 near-match max=1 |
| OLMColorKey | yes | yes | new Mac plugin builds | Python + C++ + Rust RGB/premult/box/Edge Thin/Edge Blur CLI | C++: 1-4 & 7 exact; 5/6 erode 0.48% off; Edge Blur C++ now matches Python exploratory residual (`case8 mean=1.0396`, `case9 mean=1.2503`); Mac plugin has cases 1-9 scaffold |
| OLMDirectionalBlur | yes | yes | new Mac plugin builds | Python + C++ direct/rotated CLI scaffold | front-only/no-noise DIFF; Mac plugin has 8bpc front-only/no-noise direct slice; rotate-back denom-alpha is neutral/negative; exact row-driver equals exact-scatter-helper (`4.4392/1.1761`), so residual needs ASM argument mapping or extra refs |
| OLMKiraKira | yes | yes | new Mac plugin builds | Python OpenCV/two-temp ray probe + C++ native scaffold | Python OpenCV 4.5.5 two-temp `0.8504/1.1570/1.0514`; explicit ROI/`dst=` alias probe is identical, so simple Mat aliasing is not the residual; C++ all-ray two-temp/no-fastpath `0.8506/1.1570/1.0563`; Mac plugin uses that same all-ray two-temp candidate and still DIFF |
| OLMRadialBlur | yes | yes | new Mac plugin builds | Python rotation + zoom polar CLI scaffold; C++ Zoom/Rotation/Inner diagnostic CLI | Rotation case_0010 near-match; Zoom 0009 OK in Python and C++; C++ Zoom 0003-0005 OK with Size Variation ignored; Mac plugin has 8bpc Zoom/no-inner/no-noise slice with large-Strength FFT path and Size Variation no-op pass-through; Inner source-scatter/prepass old refs baseline 25.2972/10.6222/21.2910; Edge Fade conditional seed improves means but remains red diagnostic due coverage; continue exact +0x10/+0x14 buffer construction |
| OLMSmoother | yes | yes | prefer v2 compat | C++ CLI over mac port; OLMSmoother2 forced-v1 compat gate | standalone classifier over-fires ~20x, but OLMSmoother2 `Smoother Version=1` matches v1 refs closely (`mean=0.0055/0.0051/0.0200`); do not deep-dive standalone v1 unless this migration path is rejected |
| OLMSmoother2 | yes, 20260605_extra | yes | port complete-ish | C++ CLI over mac port | first 4 cases measured: case1 mean 0.1832, case2 0.0216, case3 exact, case4 0.0189 after asm key-path + writeback-premul fixes |
| OLMToonDilate | yes | yes | new Mac plugin builds | Python + C++ Chebyshev/BFS CLI | C++ gated: case1 mean 0.4762, case2 0.0022, case3 3.0676; Mac plugin has cases 1-3 kernel |

## Active Sub-Agent Assignments

Current parallelization model is plug-in ownership, not broad effect groups.
Use subagents for narrow read-only IR/ASM audits while the parent agent owns
implementation, regression gates, and commits.
Current run details and reusable prompt shape are recorded in
`notes/SUBAGENT_ASSIGNMENTS.md`.

| Owner slice | Scope | Current best use | Stop condition / next reference |
|---|---|---|---|
| `OLMDirectionalBlur` | `notes/IR_OLMDirectionalBlur.md`, `notes/OLMDirectionalBlur_ASM_FACTS.md`, `cli/OLMDirectionalBlur/`, `refs/scripts/smoke_olmdirectionalblur*` | Keep as read-only IR/argument-mapping audit unless new Windows refs arrive. Re-run `rotated-aex-full-choreo` / `rotated-aex-exact-rowdriver` only as regression checks. | Current opaque refs cannot separate render-context scale, source premul, and alpha ownership. Wait for `refs/reference_requests/directionalblur_context_scale_20260606.json` before further PNG-only fitting. |
| `OLMRadialBlur` | `notes/OLMRadialBlur_RE.md`, `notes/OLMRadialBlur_ASM_FACTS.md`, `cli/OLMRadialBlur/`, `refs/scripts/smoke_olmradialblur*` | Zoom and tiny Rotation are regression-green. `notes/OLMRadialBlur_ASM_FACTS.md` records the sampler/writeback audit for `+0x38/+0x40/+0x48/+0x50`; use it as the fact base for future Inner work. | All current Inner/Edge Fade refs have `Size Variation=0`, so `+0x40` span/gate cannot be identified strongly from PNGs alone. Wait for `refs/reference_requests/radialblur_inner_size_variation_20260606.json` before promoting more Inner changes. |
| `OLMKiraKira` | `notes/OLMKiraKira_ASM_FACTS.md`, `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md`, `cli/OLMKiraKira/`, `refs/scripts/smoke_olmkirakira*` | Keep all-ray two-temp/no-fastpath as the candidate path. `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md` captures `FUN_18114fd90` / `FUN_18114ffd0` scalar and Brightness/Gain facts; do not add more equal-ray sweeps. | Current three refs have equal ray lengths and zero rotation, so ray order, helper scalar, angle mapping, and single-ray crop are entangled. Wait for `refs/reference_requests/kirakira_single_ray_20260606.json`. |
| `OLMSmoother` / `OLMSmoother2` | `notes/OLMSmoother2_ASM_FACTS.md`, `cli/OLMSmoother*`, `refs/scripts/smoke_olmsmoother*` | Prefer OLMSmoother2 `--force-version 1` for v1 compatibility. Standalone v1 is low priority because its classifier over-fires. | `idx0` and plane-split probes both worsened no-key case_0001. Wait for `refs/reference_requests/smoother2_no_key_grid_20260606.json` before more no-key tuning. |
| `OLMColorKey` | `refs/scripts/olmcolorkey_cli.py`, `cli/OLMColorKey/`, `rust/olmcolorkey_cli/`, `mac/OLMColorKey/`, `refs/scripts/audit_olmcolorkey_manifest.py` | RGB, Edge Thin, and exploratory Edge Blur are guarded. Do not deep-implement Replace or non-black non-RGB color spaces from black-key refs. | Current refs have `Enable Replace=0` and only key color 1 enabled. Wait for `refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json` before promoting Replace/Lab94/YUV/YCrCb/multi-key behavior. |

Practical rule: if a subagent edits code, give it a disjoint write scope and a
single smoke target. Otherwise keep subagents read-only and have the parent
agent integrate the finding into `notes/*_ASM_FACTS.md`, CLI diagnostics, and
`smoke_all_algorithm_clis.py`.

2026-06-06 continuation audit: four read-only subagents reran the stop-condition
review for `OLMDirectionalBlur`, `OLMRadialBlur`, `OLMKiraKira`, and
`OLMSmoother2`. All four independently reported that current references are
still useful as regression checks, but not sufficient for more non-guesswork
algorithm promotion on the unresolved paths:

- `OLMDirectionalBlur`: A/B choreography and row-driver ownership are the best
  current IR, but `rotated-aex-full-choreo` / `rotated-aex-exact-rowdriver`
  remain red around `case_0001 mean~=4.44`. Need
  `directionalblur_context_scale_20260606` to replace `--strength-scale auto`
  with recorded `ctx_render_scale` and separate opaque/alpha behavior.
- `OLMRadialBlur`: Zoom, Zoom Offset, and tiny Rotation remain green; Inner and
  EdgeFade remain blocked because all current Inner/EdgeFade refs have
  `Size Variation=0`, `Noise Variation=0`, and `Noise Layer=0`. Need
  `radialblur_inner_size_variation_20260606` before more `+0x40` tuning.
- `OLMKiraKira`: all-ray two-temp/no-fastpath remains the best address-backed
  candidate (`0.8506/1.1570/1.0563`), but the three current refs all have equal
  ray lengths and `Glow Rotation=0`. Need `kirakira_single_ray_20260606` before
  ray order, helper scalar, angle mapping, or crop behavior can be separated.
- `OLMSmoother2`: v1 is effectively covered by `OLMSmoother2 --force-version 1`
  (`0.0055/0.0051/0.0200`). V2 key paths are green/near-green, but no-key
  `case_0001` remains `mean=0.1832`; `idx0` and plane-split diagnostics both
  worsened. Need `smoother2_no_key_grid_20260606` before more no-key tuning.

2026-06-06 continuation follow-up: added
`refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py` as the import-time analysis
hook for `smoother2_no_key_grid_20260606`. It exits 0 with `[SKIP]` while the
request is pending; once a covered manifest is imported, it runs the
OLMSmoother2 C++ CLI and writes/prints max/mean grouped by `Smoothness` and
`Smooth Range`. This is harness readiness only, not an algorithm-tuning change.

2026-06-06 subagent fact-log follow-up: added
`notes/OLMRadialBlur_ASM_FACTS.md` for Rotation sampler/writeback plane
ownership and `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md` for scalar
aggregation/Brightness-Gain flow. Both are read-only audit outputs and do not
promote any new image-diff tuning.

2026-06-06 ColorKey reference follow-up: added
`refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json` after a
read-only audit confirmed that current nine cases all have `Enable Replace=0`,
only key color 1 enabled, and black-key-heavy non-RGB coverage. The request asks
for non-black HSV/Lab76/Lab94/YUV/YCrCb, per-component Lab76/Lab94, Replace,
Color Keep + Replace, multi-key Replace, and optional Edge Blur/transparent-RGB
interaction cases.

## Next Integration Target

Pick the first plug-in with:

- a usable Windows reference set,
- a small enough kernel to extract,
- parameter snapshots in `reference_manifest.json`,
- minimal dependency on AE suites.

Current leading candidates: AE-host validate the new `OLMRadialBlur` Zoom
plug-in path, or continue the remaining `OLMColorKey` Edge Blur/Replace/Lab76
work. `OLMBlur`, `OLMColorKey`, `OLMRadialBlur`, and
`OLMToonDilate` and `OLMDirectionalBlur` now have Mac plug-in builds; all still need AE-host validation.

`ColorKeep` now has a vectorized Python CLI smoke path:

```sh
python3 refs/scripts/smoke_colorkeep_cli.py
```

Last result: `ok=1 fail=0 missing=0`.

`OLMColorKey` RGB/binary-alpha CLI:

```sh
python3 refs/scripts/smoke_olmcolorkey_cli.py
python3 refs/scripts/smoke_olmcolorkey_extended_cli.py
python3 refs/scripts/smoke_olmcolorkey_cpp_cli.py
```

Two Python render paths exist in `refs/scripts/olmcolorkey_cli.py`:

1. Simple path (`render_rgb_binary`): RGB color space, one key color,
   mean-delta threshold, no premultiply/box/edge/replace.
2. Extended path (`render_extended`): premultiplied compare, per-color +
   per-component box keying, Color Keep, and Edge Thin (Distance Type 2).

Current reference results (`python3 refs/scripts/run_reference_test.py ...`):

- `case_0001`: `max=0`
- `case_0002`: `max=0`
- `case_0003`: `max=0`
- `case_0004`: `max=0`
- `case_0005` (Keep=1, Edge Thin Amount=-16): `max=255`, `nz=9860/2073600` (0.476%)
- `case_0006` (Keep=0, Edge Thin Amount=-16): `max=255`, `nz=9860/2073600` (0.476%)
- `case_0007` (Keep=0, Edge Thin Amount=+12): `max=0` (exact)

The C++ AE-portable kernel in `cli/OLMColorKey/main.cpp` covers the same
case_0001..0007 slice. Build with `refs/scripts/build_olmcolorkey_cli.sh`.
`refs/scripts/smoke_olmcolorkey_cpp_cli.py` verifies:

- RGB/simple cases 1..4 exact (`max=0`)
- Edge Thin case_0005/0006 gated at the known erode residual (`mean=0.3031`)
- Edge Thin case_0007 exact (`max=0`)

Edge Blur case_0008/0009 remains Python-only exploratory scaffolding for now.

Mac AE integration: `mac/OLMColorKey/` now builds as `OLM Color Key` with match
name `OLM Color Key`. The render kernel covers the C++ CLI cases 1..7 slice
(RGB/simple key, premultiplied per-color/per-component keying, Edge Thin L1).
Verified with:

```sh
xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -configuration Debug build
file mac/OLMColorKey/Mac/build/Debug/OLMColorKey.plugin/Contents/MacOS/OLMColorKey
codesign --verify mac/OLMColorKey/Mac/build/Debug/OLMColorKey.plugin
```

The binary is universal (`arm64` + `x86_64`). This environment still cannot run
AE-host pixel validation, so final AE behavior must be checked on an AE machine.

### case_0005..0007 algorithm notes (from `decomp/OLMColorKey.aex.c.txt`)

Params for the three: key Color 1 = black `[0,0,0]`, Number of Colors=1,
Premultiplied=1, Color Space=4, Per Color=1, Per Component=1, global
Threshold=1, all per-component thresholds=0, Edge Thin Distance Type=2.

- **Keying.** With Premultiplied=1 the compare uses alpha-weighted RGB. With
  Per Component=1 the comparator is a per-channel box `|cmp_c - key_c| <= eps_c`
  (decomp comparator, struct `+0x34` flag). For these cases the per-component
  thresholds are 0 and the global Threshold normalizes to the 8-bit half-step
  (`0.5/255`, struct `+0x54`), so the effective rule is **exact byte match** to
  the key. Key is black, so `matched = (premult RGB bytes == 0)`. Color Space
  index is irrelevant here because black is invariant under every space
  (decomp shows index 4 = Lab94, not YUV — note for future non-black cases).
  Output is **binary alpha** with premultiplied RGB (RGB zeroed where removed).
  Color Keep=1 keeps matched pixels; =0 keeps the complement.
- **Edge Thin = L1 chamfer.** `FUN_1800058a0` (Distance Type 2) is a two-pass,
  orthogonal-only chamfer => exact L1 / cityblock distance on the binary matte.
  Amount>0 dilates, Amount<0 erodes, by |Amount| px.
- **Dilate is exact** (`matte |= dist_to_matte <= Amount`): case_0007 `max=0`.
- **Erode residual.** `matte &= dist_to_nonmatte > |Amount|+1` is the best L1
  fit (the `+1` is empirical: Amount=16 removes L1<=17). All 9860 mismatches
  sit on the single `L1==17` shell and are "AE keeps, we remove" — the
  diamond-corner pixels. Pure Euclidean is worse (erode ~135k, dilate ~1k off),
  isotropic/anisotropic chamfer weights cannot push erode below 9860, so the
  shell tie is the L1 floor. `ADBE Force CPU GPU=1` is not a render-path
  indicator. The remaining 0.48% is most plausibly an AE project-renderer path
  or distance-contour difference at large erode radius, though an unmodeled CPU
  boundary rule is still possible. To reach `max=0` on erode, replicate AE's
  exact distance contour for this path.

`case_0008..0009` now run through a partial Edge Blur path reconstructed from
`FUN_1800049a0..FUN_1800056f0` and `FUN_1800085b0`. They are guarded by
`refs/scripts/smoke_olmcolorkey_edgeblur_cli.py`, but this is not an exactness
claim:

- `case_0008`: `max=79`, `mean=1.0396` (RGB is now premultiplied by the
  Edge Blur feather weight; remaining differences are mostly alpha contour /
  internal-boundary shape)
- `case_0009`: `max=255`, `mean=1.2503` (Color Space 3 now uses the
  AEX constants from `FUN_180009f50`; remaining residual is boundary /
  transparent-RGB exactness, not gross RGB-space keying)

Direction=3 appears to behave as an inward cosine feather over the post-Edge
Thin keep matte for case_0008: the Edge Blur does not expand the nonzero-alpha
region outward. The comp/frame edge is not treated as an outside-matte neighbor
when seeding the blur boundary. Existing green gates for cases 1-7 still pass
after this exploratory implementation.

The C++ CLI now has the same broad Edge Blur/Lab76 scaffolding, guarded by
`refs/scripts/smoke_olmcolorkey_cpp_edgeblur_cli.py`. Current C++ numbers are
`case_0008 max=142 mean=1.5386` and `case_0009 max=255 mean=1.2503`; this is
useful native regression coverage, but the Python path remains the tighter
measurement for Edge Blur until the remaining distance-contour differences are
resolved.

Rust compatibility CLI: `rust/olmcolorkey_cli` and
`refs/scripts/smoke_olmcolorkey_rust_cli.py` now cover cases 1-9. Results:
RGB cases 1-4 exact, Edge Thin case5/6 `mean=0.3031`, case7 exact, Edge Blur
case8 `max=79 mean=1.0396`, case9 `max=255 mean=1.2541`. Case8 now matches the
Python exploratory path after making Edge Blur's Distance Type 1 use Euclidean
distance in C++/Rust/Mac; case9 exposed a fragile C++ EDT boundary condition
earlier, and after porting the Rust EDT boundary handling back to C++, the C++
CLI reaches the Python exploratory path's `mean=1.2503`. This makes Rust useful
as an independent, memory-safe algorithm oracle for ColorKey while the AE
plug-in remains C++/AE SDK.

2026-06-06 correction: the current Python Edge Blur path was the better
measurement for `case_0008`. Aligning C++/Rust/Mac Edge Blur Distance Type 1
with that path (Euclidean distance to the internal boundary seeds) improves C++
`case_0008` from `max=142 mean=1.5386` to `max=79 mean=1.0396` while preserving
`case_0009 mean=1.2503`. The tightened C++/Rust Edge Blur smoke thresholds now
guard this improvement at `mean<=1.26`.

2026-06-05 C++/Mac update: the C++ Euclidean distance transform used by Edge
Thin Distance Type 3 now uses the Rust CLI's safer 1D EDT boundary handling.
This improves C++ Edge Blur `case_0009` from `mean=1.5398` to `mean=1.2503`
without regressing RGB, Edge Thin, or Edge Blur `case_0008`. The mac plug-in
now also has Chessboard/Euclidean/L1 Edge Thin distance selection instead of
L1-only Edge Thin, and Debug build succeeds.

2026-06-05 update: Edge Blur now scales RGB by the same feather weight as
alpha. This matches the reference premultiplied-looking output (for example,
source gray 141 with output alpha 89 produces RGB about 49) and cuts the
Python residual from case8/case9 `2.4792/1.9554` to `1.0396/1.2503`.

2026-06-05 Mac plugin update: `mac/OLMColorKey` now reads Edge Blur distance
type/direction, exposes Edge Blur Amount over the 0..100 range, and applies the
same Lab76 constants plus RGB/alpha feather scaffold used by the CLI paths.
The plugin builds as a universal `arm64`/`x86_64` bundle and passes
`codesign --verify`; exact AE-host validation is still pending.

2026-06-05 manifest audit: `refs/scripts/audit_olmcolorkey_manifest.py` prints
the ColorKey reference slice with grouped Edge Thin / Edge Blur values. Current
`20260604_olm` cases have `Enable Replace=0` for all nine cases, and no enabled
replace-color slots. Therefore the existing `replace color is not implemented`
guard in the Python/C++ CLIs is not exercised by current Windows PNGs; do not
claim or deep-implement Replace until a targeted Windows reference enables it.

Next OLMColorKey task: tighten remaining Edge Blur boundary/transparent-RGB
handling and confirm the erode shell against references that record
`project_gpu_accel_type` (CUDA vs Software) or a better distance contour model.

`OLMSmoother` C++ CLI (key-off, 8bpc):

```sh
refs/scripts/build_olmsmoother_cli.sh
python3 refs/scripts/smoke_olmsmoother_cli.py
```

The CLI compiles the existing mac port (`mac/OLMSmoother/Mac/OLMSmoother_port.cpp`)
against AE-free shim headers in `cli/OLMSmoother/shim/` (a stub `OLMSmoother.h`
and `AEFX_SuiteHandlerTemplate.h` whose `AEFX_SuiteScoper` is backed by an
in-process `PF_Iterate8` loop), then drives `DispatchRender(..., 8)` on a PNG.
This makes the port runnable without After Effects for the first time. Pixel
byte order in the worlds is AE-native ARGB; "Do Smooth Range" is the Tolerance
slider (cases use 6); "Use Color Key" = 0.

Current results (`smoke_olmsmoother_cli.py`, all three cases): the harness runs
clean but the port does **not** match the reference yet —

- `case_0001`: `max=127`, `nz=30687/518400`
- `case_0002`: `max=127`, `nz=41401/518400`
- `case_0003`: `max=128`, `nz=45417/518400`

Diagnosis: the MLAA classifier **over-fires ~20x**. The reference itself only
changes ~868/1523/2348 px vs the input (it is a subtle edge AA), but the port
modifies ~30k/40k/44k px and matches the reference on only ~25 of the
reference's changed pixels. Two suspects, in priority order:

1. **Render path / reference path mismatch.** The manifests record
   `ADBE Force CPU GPU=1`, but that value is not a render-path indicator. The
   mac port mirrors the Windows `.aex` MLAA (classifier + interp kernel); the
   current AE reference path appears to smooth far fewer pixels. This may be a
   fundamentally different project-renderer path/condition, not just a tuned
   constant.
2. **Classifier threshold / interp kernel.** The port author flagged Stage-4
   uncertainty in `MainInterpKernel8` curve invocation; the over-trigger could
   also be a tolerance-compare scale/sign issue in `Classifier8`/`ColorCompare8`.

Tolerance sweep (case_0001, varying "Do Smooth Range"): tol=6 and tol=30 both
change **30110** px (identical output); tol=100 and tol=255 change **0** px.
So the classifier has a binary cliff between 30 and 100 (all this image's edges
have compare magnitude in ~[30,100)), and **no tolerance value reproduces the
reference's 868 changed px**. The reference's 868-px selection is therefore not
a tolerance-scaled subset of the port's 30110 — it is a structurally different
edge selection. This rules out a simple threshold-scale fix and keeps suspect
(1) open: the current AE reference path selects far fewer edges than the CPU
MLAA path the CLI drives.

Conclusion: OLMSmoother cannot be matched to these references by tuning the CPU
port alone. However, user feedback on 2026-06-06 is that OLMSmoother v1 may be
covered by a mode/compatibility path inside OLMSmoother2. Treat the standalone
v1 port as a diagnostic asset, not the next deep RE target. Before requesting
more alternate AE Project Settings references or digging further into v1, first
verify whether OLMSmoother2 exposes or implements a v1-equivalent mode and
whether that is an acceptable migration path.

2026-06-06 compatibility check: OLMSmoother2 has an explicit `Smoother Version`
popup. `cli/OLMSmoother2/main.cpp` now accepts `--force-version 1` and maps the
v1 manifest labels (`Use Color Key`, `Do Smooth Range`) onto the v2 harness
inputs. `refs/scripts/smoke_olmsmoother2_v1_compat_cli.py` runs the v2 port
against the original OLMSmoother v1 references and passes as a green
compatibility guard:

- `case_0001`: `max=63 mean=0.0055`
- `case_0002`: `max=63 mean=0.0051`
- `case_0003`: `max=124 mean=0.0200`

This is dramatically better than the standalone v1 CLI over-fire (`30k+`
changed pixels), so the current migration policy is: prefer OLMSmoother2
`Smoother Version=1` for v1 compatibility, keep the standalone v1 port only as
diagnostic history, and spend reverse-engineering time elsewhere unless AE-host
testing rejects the v2 compatibility mode.

`OLMToonDilate` (CLI characterized; Mac plug-in build added):

Params reduce to a single knob: **Search Radius** (cases use 13, 27). 8bpc,
images at half comp res (960x540 vs 1920x1080). Behaviour established from the
references (`case_0001..0003`):

- **Opaque pixels never change.** Only transparent pixels (alpha 0) get filled,
  so this is a region grow into the transparent background.
- **Fill color = nearest opaque pixel by Euclidean distance — EXACT** (0 of 3860
  filled pixels wrong on case_0001 using `distance_transform_edt(return_indices)`).
  So the color half of the algorithm is fully solved (nearest-feature copy of
  the source RGBA).
- **Fill mask is NOT a disk.** Filled pixels span Euclid distance 1..~10 with a
  hard cutoff (none beyond ~10 on case_0001; Search Radius 13), yet ~480
  transparent pixels within Euclid<=3 of an opaque edge stay UNFILLED. No single
  radius reproduces the mask (best leaves 2436/3860 wrong). The unfilled-near
  pixels sit on convex/open edges; filled ones cluster in concavities — i.e. the
  fill is a **directional / gap-closing search within Search Radius**, not a
  uniform dilation. `ADBE Force CPU GPU=1` is not a render-path indicator; use
  separately recorded `project_gpu_accel_type` values for CUDA vs Software
  comparisons.

Algorithm (from `decomp/OLMToonDilate.aex.c.txt` FUN_1801a6150, confirmed
empirically): NOT a ray search — it is a **2-pass 8-connected (Chebyshev)
chamfer distance transform** with nearest-source colour propagation.

  - seed = (alpha == 255)   # only fully-opaque pixels are sources
  - R_eff = ceil(SearchRadius * img_width / comp_width)   # downsample scaling
  - fill = (~seed) & (chebyshev_dist_to_seed <= R_eff)
  - colour = nearest opaque pixel's RGBA (Euclidean-nearest; exact)

CLI: `refs/scripts/olmtoondilate_cli.py` (numpy + Pillow + scipy). Verify:

```sh
python3 refs/scripts/smoke_olmtoondilate_cli.py
```

Results (`run_reference_test`, --comp-width 1920):

- `case_0001` (R=13, half-res): `max=255`, `nz=1936/518400` (0.37%)
- `case_0002` (R=13, half-res, AA alpha): `max=255`, `nz=98/518400` (0.019%)
- `case_0003` (R=27, full-res): `max=255`, `nz=32931/2073600` (1.59%)

Chebyshev is decisively the right metric (case_0003: cheb<=27 = 32931 vs
euclid-best = 134259; cheb has a sharp minimum exactly at R_eff). The remaining
residual is a boundary gap scaling with radius, similar in shape to
OLMColorKey erode and OLMSmoother. To close it, an alternate AE reference path
would help determine whether the CPU port is exact or still missing a boundary
rule.

C++ CLI: `cli/OLMToonDilate/main.cpp`, built by
`refs/scripts/build_olmtoondilate_cli.sh`. This is closer to the final macOS
plug-in core than the Python/scipy prototype. It uses an 8-neighbor multi-source
BFS to reproduce the Chebyshev mask and propagates a source pixel coordinate for
the fill colour. Verify:

```sh
refs/scripts/build_olmtoondilate_cli.sh
python3 refs/scripts/smoke_olmtoondilate_cpp_cli.py
```

Mac AE integration: `mac/OLMToonDilate/` now builds as `OLM Toon Dilate` with
match name `ADBE OLMToonDilate`. The plug-in exposes only `Search Radius` and
ports the C++ CLI Chebyshev/BFS kernel into 8/16/32bpc SmartRender plus classic
Render. SmartRender carries `PF_CheckoutResult.ref_width` through pre-render
data so the effective radius scales by comp width like the Windows reference.
AE-host validation is still pending in a real After Effects install. Note that
`case_0004` in the imported ToonDilate reference folder is actually
`OLM RadialBlur`; keep it out of ToonDilate scoring.

Current C++ results (`--comp-width 1920`, gated):

- `case_0001`: `max=255`, `mean=0.4762`
- `case_0002`: `max=255`, `mean=0.0022`
- `case_0003`: `max=255`, `mean=3.0676`

The C++ BFS colour propagation is not the same implementation as scipy's
Euclidean feature transform, but it is closer on cases 2/3 while keeping case 1
unchanged. Use the C++ path for future AE plug-in integration work, and keep
the Python path as a compact algorithm reference.

`OLMDistanceGradation` Python CLI:

```sh
python3 refs/scripts/smoke_olmdistancegradation_cli.py
```

2026-06-05 update from the new `20260605_extra/OLMDistanceGradation` reference:

- Added `refs/scripts/olmdistancegradation_cli.py`, a compact AE-free Python
  implementation of the current Distance Gradation distance-field core.
- The green gate now covers `case_0001..0007`, `case_0009`, `case_0015`,
  `case_0017`, `case_0018`, and `case_0019`, and passes with `max-diff<=7`,
  `mean<=0.11`, `nonzero<=22%`.
- Important PNG/export finding: AE's reference PNGs are premultiplied. The CLI
  multiplies RGB by output alpha for both no-background and background-color
  comparison cases to compare against the exported PNGs, even though the AE
  world render core writes straight RGB.
- Important algorithm finding: the old mac source special-case for
  `In/Out=Inside` and `Inside Threshold=0` was wrong against the Windows
  reference. Removing it changes `case_0003` from `mean=59.2455` to
  `max=1 mean=0.0000`; the same fix was applied to
  `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`.
- Background-color linear cases improved after the PNG premultiply comparison
  fix: `case_0018 max=2 mean=0.0346`, `case_0019 max=2 mean=0.0351`.
- Full-set measurement currently has larger residuals in blur and some
  constant/interpolation cases (`case_0020..0023`, `case_0029` are obvious red
  targets). These are not yet green gates.
- Verified after the source edit:
  `xcodebuild -project mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj -configuration Debug build`,
  universal `arm64/x86_64` binary, and `codesign --verify`.

`OLMBlur` C++ CLI:

```sh
refs/scripts/build_olmblur_cli.sh
python3 refs/scripts/smoke_olmblur_cli.py
```

Current reference results, verified after rebuilding `cli/OLMBlur/olmblur_cli`
with manifest `comp.width` propagated into per-case params so the CLI can match
AE `in_data->downsample_x` behavior:

- `case_0001`: `max=0`
- `case_0002`: `max=0`
- `case_0003` high-radius legacy: `max=1`, `nonzero_px=10753`
- `case_0004`: `max=0`
- `case_0005`: `max=1`, `nonzero_px=1`
- `case_0006`: `max=1`, `nonzero_px=6`
- `case_0007` legacy: `max=1`, `nonzero_px=3`

Tolerance policy is now encoded in `refs/scripts/smoke_olmblur_cli.py`
(`max-diff=1`, `mean=0.01`, `nonzero<=3.0%`). The CLI-verified downsample
scaling and legacy pass-order/all-same behavior have been mirrored into
`mac/OLMBlur/OLMBlur.cpp`.

Mac AE build baseline:

- The local AE SDK is at `/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples`.
- `scripts/setup_ae_sdk_links.sh` creates ignored repo-root symlinks:
  `Headers`, `Util`, and `Resources`.
- With those links present, these existing projects build Debug successfully:
  `ColorKeep`, `OLMBlur`, `OLMDistanceGradation`, `OLMSmoother`, `OLMSmoother2`.
- `OLMBlur.plugin` is a signed universal bundle (`arm64` + `x86_64`) at
  `mac/OLMBlur/Mac/build/Debug/OLMBlur.plugin`.

`OLMRadialBlur` decomp pass:

Initial RE notes are in `notes/OLMRadialBlur_RE.md`. The important structure is
now known: 8-bit render dispatch reads params in `FUN_180008690`, then Type 1
uses `FUN_1800056f0` (Zoom) and Type 2 uses `FUN_180004640` (Rotation). Both
paths transform the source into a polar/radial working buffer, run two blur
passes, then inverse-sample back to the output. Noise is separate
(`FUN_180009380`/`FUN_180009680`) and should be deferred.

Manifest audit helper:

```sh
python3 refs/scripts/audit_olmradialblur_manifest.py
```

First CLI target should be `case_0010`: Rotation, Outer Strength=4,
Inner Strength=0, Repeat Border=1, Ratio=1, Angle=0, Quality=5,
Size Variation=0, Noise Variation=0. This isolates the Rotation coordinate
conversion and angular blur without inner/noise complexity.

An experimental direct Rotation CLI now exists at
`refs/scripts/olmradialblur_cli.py`, with smoke
`refs/scripts/smoke_olmradialblur_rotation_cli.py`. The broad smoke remains
red, but the AEX-shaped polar-grid experiment improves the best direct
`case_0010` probe from `mean=1.3977` to `mean=0.2864`
(`max=255`, `nz=155419/2073600`), better than the identity baseline
`mean=1.1796`. The Strength-1 blur-tail correction improves the tiny target
further to `max=255`, `mean=0.0104`, `nz=33794/2073600`; alpha max residual is
only 1, with sparse boundary/transparent-RGB differences carrying the 255 max.
This confirms the first important mappings: `Strength` is angular-grid samples
(so at Quality=5, Strength=4 becomes a 3-sample blur tail after the source
sample is handled separately), the Gaussian table is generated at length 30000
then re-indexed by blur length, and floor-like 8-bit quantization is closer
than round/ceil. Remaining work is in the detailed validity/weight/sampling
rules in `FUN_180002780` /
`FUN_1800024c0` / `FUN_180001c90`. Rejected probes: reverse polar scatter
direction (`mean=1.2781`) and +/-0.5 center offsets (`mean~0.416`), so the
scaled AE Center is currently the best coordinate interpretation.

The same polar-grid path now runs `case_0001` (Rotation, outer Strength=540,
no inner/no noise) using FFT angular scatter: identity baseline `mean=7.5294`,
polar `mean=1.9039`. This is still red but confirms the structure scales beyond
the tiny Strength=4 probe. Rejected probes for the remaining residual:
angular half/quarter-step shifts worsen to `mean=1.9338..1.9507`, raw straight
final sampling worsens slightly to `mean=1.9045`, and non-alpha-normalized
scatter variants explode to `mean=142.2530`. So the current remaining gap is
not a simple angular grid offset or final sampler normalization issue.

`case_0002` (Rotation, outer Strength=212, Offset Mode=1, Offset=153, no
inner/no noise) now runs as well: identity baseline `mean=6.9395`, polar
with constant additive Offset `mean=1.9582`, and polar with `FUN_1800024c0`'s
radius-dependent Offset Mode=1 span `mean=1.3077`. Ignoring Offset worsens to
`mean=2.6050`, so the current radius-dependent offset model is directionally
correct but still not final; exact handling still belongs in the remaining
validity/weight paths.

C++ Rotation update: `cli/OLMRadialBlur/main.cpp` now dispatches Blur Type=2 to
a native polar-grid Rotation scaffold for outer-only/no-noise/no-size-variation
cases. `refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py` builds the
C++ CLI and verifies `case_0010` at `max=255 mean=0.0104`, matching the Python
tiny Rotation near-match gate. Broad C++ Rotation remains a red measurement:
`case_0001 mean=1.9034`, `case_0002 mean=1.3071`, `case_0010 mean=0.0104`.
`case_0002` improved from `mean=2.6174` after porting radius-dependent Offset
Mode=1 (`FUN_1800024c0` / `variable_scatter_accumulate`) into the C++ slice.
`refs/scripts/smoke_olmradialblur_cpp_rotation_cli.py` records this broad C++
Rotation path as an expected-red measurement scaffold.

2026-06-05 C++ Inner probe update: `cli/OLMRadialBlur/main.cpp` now also runs
nonzero Inner Strength as a measurement-only Rotation path, mirroring Python's
outer-forward / inner-reverse combined scatter and max-contribution alpha model.
`refs/scripts/smoke_olmradialblur_cpp_inner_cli.py` was added and registered in
the aggregate as expected-red. Current C++ results: `case_0011 mean=63.4207`,
`case_0012 mean=15.4790`, `case_0013 mean=20.0603`. This is useful native
coverage but not yet a Mac plugin supported slice; exact Inner/Offset/EdgeFade
validity handling remains unresolved.

2026-06-05 C++ Inner alpha-mode probe update:
`cli/OLMRadialBlur/main.cpp` now parses `outer_edge_fade` /
`inner_edge_fade` and exposes diagnostic `--inner-alpha-mode
max|sum|outer|inner|input`. `refs/scripts/audit_olmradialblur_manifest.py`
now prints both Edge Fade columns; current Inner reference cases `0011..0013`
all have Outer/Inner Edge Fade `0`, so Edge Fade itself is not the cause of
these three residuals. `refs/scripts/smoke_olmradialblur_cpp_inner_alpha_mode_probe_cli.py`
was added and registered as expected-red. Results:

- `max`: `case_0011 mean=63.4207`, `case_0012 mean=15.4790`,
  `case_0013 mean=20.0603` (baseline preserved).
- `sum`: `54.7860 / 17.6602 / 19.8535`.
- `outer`: `63.4207 / 14.4709 / 20.8267`.
- `inner`: `92.1469 / 14.2504 / 21.4453`.
- `input`: `92.1469 / 13.1655 / 22.2481`.

Like the Python probe, no single alpha accumulator explains all Inner cases:
`sum` helps `0011`/`0013`, while `input` helps `0012`. The next likely gap is
the literal `FUN_1800024c0 -> FUN_180001c90` per-source validity/scatter order,
not a simple C++/Mac-ready alpha-mode switch.

2026-06-05 subagent RadialBlur Inner audit:

- `FUN_1800024c0` is a per-source scatter loop, not a destination-row gather.
  It reads a validity byte, a prefiltered alpha/validity value, size/length
  scale, and source RGB before scattering.
- For each valid source cell, AEX calls `FUN_180001c90` outer first and inner
  second for the same source. `FUN_180001c90`'s scatter tail starts at offset
  `1`; the source/base sample is established separately by the
  `FUN_180002780` prepass.
- The current C++ Inner path still approximates this as row weights plus a
  source subtraction. That explains why swapping final alpha accumulators did
  not resolve `0011..0013`.
- Suggested next patch shape: build polar RGBA plus a separate validity plane,
  add a small `FUN_180002780`-shaped prepass buffer for base RGB/denominator/
  max-alpha and per-source scatter alpha, then replace Inner's row convolution
  with a source loop that scatters offsets `1..effective_len-1`. Final RGB
  should normalize by weighted-alpha sum while final alpha comes from the
  separate max-contribution buffer.

2026-06-05 C++ Inner source-scatter/prepass probe:

- Added CLI-only diagnostic `--inner-source-scatter-prepass` to
  `cli/OLMRadialBlur/main.cpp` plus
  `refs/scripts/smoke_olmradialblur_cpp_inner_source_scatter_prepass_cli.py`.
  It is default-off, does not touch the Mac plugin, and was registered as an
  expected-red aggregate measurement.
- The probe replaces the Inner row-gather approximation with a first-pass
  source/base seed plus per-source outer/inner scatter tail. Results:
  `case_0011 max=255 mean=22.1632`,
  `case_0012 max=255 mean=16.6793`,
  `case_0013 max=255 mean=19.8113`.
- Compared with the default C++ Inner baseline
  (`63.4207 / 15.4790 / 20.0603`), this is a major improvement for `0011`,
  a small improvement for `0013`, and a regression for `0012`. The
  source-scatter/prepass hypothesis is therefore likely directionally correct
  but not yet the complete AEX path. Next RadialBlur Inner work should inspect
  `FUN_180002780` validity/prepass details and the dynamic span/weight table
  used by `FUN_180001c90`, rather than port this probe to the Mac plugin.

Mac plugin update: `mac/OLMRadialBlur` now also includes the 8bpc outer-only /
no-noise / no-size-variation Rotation slice with the same radius-dependent
Offset Mode=1 handling. Unsupported Rotation settings still copy input.
`xcodebuild -project mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj
-configuration Debug build CODE_SIGNING_ALLOWED=NO` succeeds.

`case_0011` probes the first inner-blur case (Outer Strength=62, Inner
Strength=478, no noise). Identity baseline is `mean=96.0015`, polar with
`--ignore-inner` is `mean=73.9185`, and the reverse-scatter inner experiment is
`mean=63.4216`. This is a useful improvement but still nowhere near a supported
slice, so `olmradialblur_cli.py --algorithm polar` now refuses inner blur unless
`--ignore-inner` or `--experimental-inner` is passed explicitly.
The CLI also has a measurement-only `--inner-alpha-mode` switch. A 2026-06-05
probe showed `sum` improves only `case_0011` (`mean=54.8108`), while `input`
improves only `case_0012` (`mean=13.1667`), and the current `max` remains best
for `case_0013` (`mean=20.0627`). Treat that as evidence that exact
Inner/Offset/EdgeFade branching is still missing, not as a C++/Mac-ready fix.
Decomp confirms Rotation scales Strength/Offset/EdgeFade by `Quality / 5`, but
the current incomplete inner model gets worse with that applied to `case_0013`
(`mean=21.7408`), so it is available only as measurement flag
`--rotation-quality-scale aex`.

Zoom / Blur Type=1 now has a near-match green hook:
`refs/scripts/smoke_olmradialblur_zoom_cli.py` runs `case_0009` through
`--algorithm zoom-polar`. Identity baseline is `mean=23.0118`; the simple
inward center-ray scaffold reached `max=233`, `mean=21.1533`; the first
polar-grid scaffold, incorrectly scaling Strength by `1 / Quality`, reached
`max=150`, `mean=14.3105`; the current AEX-shaped Zoom path uses the UI
Strength directly as the radial table length and reaches `max=1`,
`mean=0.0058`, passing the gate `max<=1 / mean<=0.01 / nz<=2.1%`.
`refs/scripts/smoke_olmradialblur_zoom_offset_cli.py` also guards
`case_0003..0005` with `--ignore-size-variation`: all three pass at
`max=8`, `mean=0.0145`. This does **not** mean Size Variation is implemented;
it means the current Zoom geometry/Strength/Offset baseline stays close even
when Size Variation=50 is present in the manifest. A useful rejected probe:
making Offset Mode=1 extend the radius length as `Strength+Offset` worsens
case_0003 to `mean=4.0360`; keeping the table length at Strength gives the
near-match.

2026-06-05 Mac plugin update: `mac/OLMRadialBlur` now follows that same
Size Variation no-op policy for the 8bpc Zoom/no-inner/no-noise path instead
of copying the input when Size Variation is nonzero. This does not implement
the actual Size Variation modulation, but it lets the Mac plug-in exercise the
near-match Zoom baseline for `case_0003..0005`-style settings.

2026-06-05 verification refresh:

- `notes/OLMRadialBlur_RE.md` was updated to match current code reality:
  `mac/OLMRadialBlur` now includes both the Zoom/no-inner/no-noise slice and
  the Rotation/no-inner/no-noise/no-size-variation `RenderRotation8` slice.
  Inner, Noise, unsupported Size Variation, and 16/32bpc still copy input.
- Radial C++ smoke refresh:
  - `smoke_olmradialblur_cpp_cli.py`: `case_0003..0005` all OK at
    `max=8 mean=0.0059`.
  - `smoke_olmradialblur_cpp_zoom_cli.py`: `case_0009` OK at
    `max=1 mean=0.0046`.
  - `smoke_olmradialblur_cpp_tiny_rotation_cli.py`: `case_0010` OK at
    `max=255 mean=0.0104`.
- `scripts/build_all_mac_plugins.sh` completed successfully after the recent
  KiraKira/Radial notes refresh. It built and verified universal Debug bundles
  for ColorKeep, OLMBlur, OLMColorKey, OLMDirectionalBlur, OLMRadialBlur,
  OLMKiraKira, OLMToonDilate, OLMDistanceGradation, OLMSmoother, and
  OLMSmoother2.

2026-06-05 AE-free aggregate refresh:

- `python3 refs/scripts/smoke_all_algorithm_clis.py` completed with exit 0.
  All green gates passed, and every registered red measurement produced
  expected `DIFF` output rather than a missing CLI/reference or command crash.
- Stable green/near-green groups confirmed: harness, ColorKeep, OLMBlur,
  OLMColorKey Python/C++/Rust gates, OLMToonDilate Python/C++, OLMRadialBlur
  Zoom Python/C++ and tiny Rotation Python/C++.
- Expected-red groups confirmed and still requiring algorithm work:
  OLMSmoother, OLMRadialBlur broad Rotation and Python/C++ Inner,
  OLMDirectionalBlur direct/rotated probes, and OLMKiraKira
  Python/C++/brightness/box-size probes.
- Current next implementation candidates from the aggregate are
  OLMDirectionalBlur core row/rotate-back behavior, OLMKiraKira exact OpenCV
  warp/boxFilter/crop details, or OLMRadialBlur Inner. OLMSmoother should stay
  out of deep tuning unless alternate AE reference data is obtained, because
  previous analysis points to a CPU/reference path mismatch rather than a
  simple tunable parameter.
- `refs/scripts/smoke_all_algorithm_clis.py` now accepts
  `--profile quick|full`. The default remains `full` for complete red/green
  aggregate coverage. `--profile quick` runs only the green gates for fast
  iteration; on 2026-06-05 it completed with exit 0 across 21 checks after
  adding the Distance Gradation basic gate:
  harness, ColorKeep, OLMBlur, OLMColorKey Python/C++/Rust, OLMToonDilate
  Python/C++, OLMDistanceGradation, OLMSmoother build, and OLMRadialBlur
  Zoom/tiny-Rotation guards.

2026-06-06 verification refresh:

- `scripts/build_all_mac_plugins.sh` completed successfully again. It built all
  10 Debug plug-ins (`ColorKeep`, `OLMBlur`, `OLMColorKey`,
  `OLMDirectionalBlur`, `OLMRadialBlur`, `OLMKiraKira`, `OLMToonDilate`,
  `OLMDistanceGradation`, `OLMSmoother`, `OLMSmoother2`), verified each binary
  has both `arm64` and `x86_64` slices, and ran `codesign --verify` for each
  bundle.
- `python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick` completed
  successfully with 30/30 green checks. This includes the
  `Reference request package`, `Reference request result verifier`, and
  `Reference request status` gates, the `AE validation result verifier`,
  the harness, ColorKeep, OLMBlur,
  OLMColorKey Python/C++/Rust, OLMToonDilate Python/C++, OLMDistanceGradation,
  OLMSmoother build, OLMSmoother2 build/v1 compatibility/key paths/Gamma
  Colors, and RadialBlur tiny Rotation / Zoom / Zoom Offset green gates.
- `refs/scripts/package_reference_requests.py` now includes generated
  `refs/reference_requests/WIN_CODEX_HANDOFF.md` in the request zip. Both the
  all-request package and `--only kirakira_single_ray_20260606` package were
  checked for the handoff file and selected request counts.
- `refs/scripts/verify_reference_request_result.py` validates returned
  reference manifests against the original request JSON, including required
  request cases, PNG/before-frame files, requested effect, and render-set/GPU
  metadata. The synthetic smoke checks both a passing result and a missing-case
  failure.
- `refs/scripts/check_reference_request_status.py` reports each request as
  `covered`, `partial`, or `pending` by scanning `refs/win_references/**`.
  Current status is all six request JSONs pending, and the command prints the
  exact `package_reference_requests.py --pending` handoff command.
- `scripts/package_mac_plugins.sh --skip-build --output
  /tmp/olm_mac_plugins_test.zip` completed successfully after the verified build.
  The zip manifest parsed as JSON, listed all 10 plug-ins, and points to the
  bundled install notes, AE host validation checklist, and AE validation result
  template. The template passes
  `python3 scripts/verify_ae_validation_result.py --allow-incomplete`, a
  synthetic all-pass returned result passes `--require-all-pass`, and a
  synthetic failed-but-actionable result passes schema validation while failing
  the all-pass gate.

## OLMDirectionalBlur

Working image-processing IR: `notes/IR_OLMDirectionalBlur.md`. Use that file
as the implementation target for the current objdump/disasm-first flow;
`notes/OLMDirectionalBlur_ASM_FACTS.md` keeps address-level evidence and this
board keeps chronology/probe history.

`refs/scripts/audit_olmdirectionalblur_manifest.py` summarizes the duplicate
Front/Back parameter groups in the Windows manifest. Current cases:

- `case_0001..0004`: Angle=0, Front Strength=1690, Size Variation=92,
  Back Strength=0, Noise Variation=0.
- `case_0005`: Angle=-99, Front Strength=190, Size Variation=31,
  Sharp Tail=20, Back Strength=0, Noise Variation=0.
- `case_0006..0009`: include Back blur and/or Noise Variation=100.

The first CLI slice should be `case_0005` rather than `case_0001`: it still has
nonzero Angle and Size Variation, but avoids back blur/noise and has much
smaller strength. The next audit step is to map the front/back parameter reader
in `decomp/OLMDirectionalBlur.aex.c.txt`, then implement a deliberately red
measurement CLI similar to RadialBlur.

Initial files:

- `refs/scripts/olmdirectionalblur_cli.py`
- `refs/scripts/smoke_olmdirectionalblur_cli.py`
- `cli/OLMDirectionalBlur/main.cpp`
- `refs/scripts/build_olmdirectionalblur_cli.sh`
- `refs/scripts/smoke_olmdirectionalblur_cpp_cli.py`
- `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_cli.py`
- `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_gather_cli.py`

2026-06-06 update: `rotated-aex-full-choreo` now extends the A/B choreography
probe by rotating normalized padded `B` back into padded `A` before cropping.
It matches `rotated-aex-choreo` on the tracked front-only cases
(`case_0001 mean=4.4483`, `case_0005 mean=1.1703`), so output-side padded
ownership alone does not explain the residual. Next focus remains row-driver
`A/B/denom` ownership or the host populate/output callbacks.

2026-06-06 row-init diagnostic: added `rotated-aex-row-init-straight-zero`,
`rotated-aex-row-init-premul-zero`, and `rotated-aex-row-init-zero`, all covered
by `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_row_init_probe_cli.py`.
Zero-denominator initialization is negative in the current full A/B scaffold:
straight/premul retained `B` both measure `case_0001 mean=4.4702`,
`case_0005 mean=1.1762`; fully zeroed `B+denom` worsens to
`case_0001 mean=4.5240`, `case_0005 mean=1.4931`. Keep the next focus on
`FUN_1800013e0`/`FUN_1800038d0` source/validity/output argument semantics or
host edge callbacks, not another simple denominator-init toggle.

2026-06-06 full-prepass diagnostic: added
`rotated-aex-prepass-full-choreo`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_prepass_full_choreo_cli.py`.
It combines full padded A/B choreography with the `FUN_180001000`-shaped center
prepass and is neutral against `rotated-aex-full-choreo`
(`case_0001 mean=4.4483`, `case_0005 mean=1.1703`). The next useful target is
the exact `FUN_1800013e0` scatter boundary/table-index behavior or host
populate/output callback edge semantics.

2026-06-06 source-driven scatter diagnostic: added
`rotated-aex-exact-scatter-helper`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_exact_scatter_cli.py`.
This keeps the current full A/B choreography but changes the horizontal row
blur from an offset-driven loop to a source-pixel-driven scatter loop shaped
after `FUN_1800013e0`. Result is mixed/minor against full choreography:
`case_0001 mean=4.4392` improves by `0.0091`, while
`case_0005 mean=1.1761` worsens by `0.0058`. Keep source-driven scatter as an
address-level implementation clue, but do not treat it as the dominant residual
until the caller argument roles and host edge/populate callbacks are mapped.

2026-06-06 exact row-driver diagnostic: added
`rotated-aex-exact-rowdriver`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_cli.py`.
It combines full padded A/B choreography, the `FUN_180001000` prepass, and the
`FUN_1800013e0` source-driven scatter path in one probe. Results exactly match
`rotated-aex-exact-scatter-helper`: `case_0001 mean=4.4392`,
`case_0005 mean=1.1761`, while full choreography remains `4.4483/1.1703`.
This clears simple row-driver integration as the residual. Next work should map
exact ASM argument roles, render-context scale, or nonopaque-alpha Windows refs
before more image-only tuning.

2026-06-06 rotate-back denominator-alpha diagnostic: added
`rotated-aex-rotateback-denom-alpha`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_rotateback_denom_alpha_cli.py`.
It keeps the current full A/B choreography and row scatter, but replaces the
rotate-back source alpha with `min(denom, 1.0)` just before the final padded
`B -> A` output rotation. This isolates whether the row driver's max-alpha
buffer is wrongly coupling into `FUN_180001ec0`'s alpha-weighted RGB
interpolation. Result is neutral/negative against full choreography:
`case_0001 mean=4.4483` is exactly unchanged, while
`case_0005 mean=1.1749` worsens from `1.1703`. Keep this as negative evidence:
the remaining DirectionalBlur residual is not explained by replacing
rotate-back source alpha with the denominator plane.

2026-06-06 truncated-span diagnostic: added
`rotated-aex-truncated-span`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_truncated_span_cli.py`.
It switches component/tail gating to the exact `FUN_1800013e0` integer span
shape (`effective_span = int(strength * coeff)`, offsets
`1..effective_span-1`). Result is mixed/minor against full choreography:
`case_0001 mean=4.4467` improves by only `0.0016`, while
`case_0005 mean=1.1749` worsens by `0.0046`. Keep as an ASM fact, not as the
remaining primary error source.

2026-06-06 output-callback diagnostic: direct `objdump` of the callback gap
shows final 8bpc output reads from `params+0x8090`, multiplies RGB by
BrightnessGain (`params+0x28`), clamps RGB to `1.0`, leaves alpha un-gained,
then uses `CVTTSS2SI` truncation after `*255`. Added
`rotated-aex-trunc-output`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_trunc_output_cli.py`.
Result is mixed/minor against full choreography: `case_0001 mean=4.4438`
improves by `0.0045`, while `case_0005 mean=1.1736` worsens by `0.0033`.
Quantization should be kept as an AEX fact, but it is not the dominant
remaining residual.

2026-06-06 pad/full-choreo diagnostic: `objdump` confirms work-buffer offsets
and dimensions come from the diagonal half-span formula stored at
`params+0x8098/0x809c` and `params+0x80a0/0x80a4`. Added
`rotated-aex-pad-full-choreo`, covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_pad_full_choreo_cli.py`.
It combines that exact pad formula with full A/B choreography and is neutral:
`case_0001 mean=4.4483`, `case_0005 mean=1.1703`. So the exact one-pixel-ish
pad/offset difference is not the remaining dominant source.

Parameter reader mapping from `FUN_180006c50`:

- param 1 / match `0001`: Angle, converted from degrees to radians.
- param 2 / match `0002`: Brightness Gain.
- param 3 / match `0003`: Size Variation, stored as value / 100.
- param 5 / match `0005`: Front Blur Strength.
- param 6 / match `0006`: Front Alpha Fade.
- param 7 / match `0007`: Front Sharp Tail, stored as value / 100.
- param 10 / match `0010`: Back Blur Strength.
- param 11 / match `0011`: Back Alpha Fade.
- param 12 / match `0012`: Back Sharp Tail, stored as value / 100.
- param 15+ / matches `0015..0020`: Noise settings and Thickness.

Decomp structure:

- `FUN_180001830`: Gaussian table for the blur/fade lengths. The denominator is
  `2 * (length / 0.5)^2 + epsilon`, not a narrow `length/3` sigma.
- `FUN_180001ec0`: rotate RGBA buffer by Angle with alpha-aware bilinear
  sampling.
- `FUN_1800013e0`: one-sided front/back scatter along the rotated X axis.
- `FUN_1800038d0`: per-row driver; applies Size Variation and Sharp Tail before
  calling front/back scatter.

Current smoke:

```sh
python3 refs/scripts/smoke_olmdirectionalblur_cli.py
```

Current smoke uses the direct image-space probe with `--angle-sign -1
--sample-sign -1 --strength-scale auto --rgb-normalize front-strength`.
The `auto` scale means
`1 / manifest comp.frame_rate` (`1/24` for the Windows reference, after
`run_reference_test.py` copies the top-level comp data into each case params
file). This is still a hypothesis, but it is a better fit than raw Strength and
matches the decomp clue in `FUN_180003c90` where Front/Back Strength is
multiplied by a runtime scale before building the Gaussian tables:
`*(param_6 + 9) = int(*(param_6 + 9) * fVar21)`.

`--rgb-normalize front-strength` is a new diagnostic mode. The older
alpha-sum normalization preserved the input red-channel sum almost exactly
(`case_0001` input R sum `8112060`, candidate `8112038`), while the AEX
reference attenuates it (`6659998`). Dividing by the effective front strength
instead of the accumulated alpha moves cases `0001..0004` closer and is a
strong clue that `FUN_1800013e0` / `FUN_1800038d0` do not behave like a fully
normalized blur.

Baselines and current probe:

- `case_0001` identity: `max=254`, `mean=4.4754`, `nz=69906/518400`.
- `case_0001` direct auto scale + front-strength RGB normalization:
  `max=241`, `mean=4.0897`, `nz=80616/518400`.
- `case_0002` direct auto scale + front-strength RGB normalization:
  `max=241`, `mean=4.0897`, `nz=80616/518400`.
- `case_0003` direct auto scale + front-strength RGB normalization:
  `max=241`, `mean=4.0897`, `nz=80616/518400`.
- `case_0004` direct auto scale + front-strength RGB normalization:
  `max=241`, `mean=4.0900`, `nz=80745/518400`.
- `case_0005` identity: `max=251`, `mean=1.2236`, `nz=45943/518400`.
- `case_0005` direct auto scale + front-strength RGB normalization:
  `max=247`, `mean=1.1931`, `nz=59471/518400`.

For comparison, `--rgb-normalize alpha-sum` remains better on `case_0005`
alone (`mean=1.1838`), but worse on `case_0001..0004` (`mean=4.4483`).
`--rgb-normalize kernel-sum` lands between them (`case_0001 mean=4.2231`,
`case_0005 mean=1.1838`). The current smoke picks `front-strength` because it
best improves the dominant front-only angle-0 group and exposes the likely AEX
attenuation behavior.

The same direct/front-strength probe is now available as a C++ CLI:

```sh
refs/scripts/build_olmdirectionalblur_cli.sh
python3 refs/scripts/smoke_olmdirectionalblur_cpp_cli.py
```

The C++ output matches the Python probe's current DIFF measurements exactly:
cases `0001..0003` `max=241 mean=4.0897`, `0004` `max=241 mean=4.0900`,
and `0005` `max=247 mean=1.1931`. This is not an exact port claim; it is a
faster iteration harness for the next AEX-shaped rotated-buffer/component-map
implementation pass.

2026-06-05 parameter plumbing refresh:

- `cli/OLMDirectionalBlur/main.cpp` now stores `back_sharp_tail` in
  `DirectionalBlurParams` and reads `back_sharp_tail_1` from the grouped AE
  manifest. The Python scaffold and Mac plugin already had this parameter.
- This does not change the current front-only `case_0001..0005` output, because
  back blur is still unsupported in the C++ slice. `smoke_olmdirectionalblur_cpp_cli.py`
  remains the expected red measurement with unchanged values:
  `case_0001..0003 max=241 mean=4.0897`, `case_0004 max=241 mean=4.0900`,
  `case_0005 max=247 mean=1.1931`.
- Keep this as groundwork for implementing `case_0006..0009` back/noise paths;
  it is not evidence that back blur itself is ported.

2026-06-05 back direct probe:

- `refs/scripts/olmdirectionalblur_cli.py` and
  `cli/OLMDirectionalBlur/main.cpp` now have measurement-only direct support
  for `--direction both` and `--ignore-noise-variation`. They apply the same
  one-sided scatter to the back direction with `back_strength` and
  `back_sharp_tail`, and add `--rgb-normalize total-strength`.
- Added `refs/scripts/smoke_olmdirectionalblur_back_probe_cli.py` and
  `refs/scripts/smoke_olmdirectionalblur_cpp_back_probe_cli.py`, then
  registered both in `smoke_all_algorithm_clis.py` as expected-red
  measurements.
- Because all back-reference cases also have Noise Variation or other
  unsupported settings, the probe intentionally ignores noise. Python and C++
  currently match exactly on the probe results:
  `case_0006 max=204 mean=0.8383`, `case_0007 max=204 mean=0.8383`,
  `case_0008 max=250 mean=0.7800`, `case_0009 max=209 mean=3.3248`.
- Existing front-only C++ smoke is unchanged:
  `case_0001..0003 max=241 mean=4.0897`, `case_0004 max=241 mean=4.0900`,
  `case_0005 max=247 mean=1.1931`.
- This creates a useful C++ measurement entry for back blur, but Noise
  Variation and exact Back/Front composition are still not implemented.

Mac AE integration: `mac/OLMDirectionalBlur/` now builds as `OLM
DirectionalBlur` with match name `OLM Directional Blur`. The current render
kernel intentionally covers only the same 8bpc front-only/no-noise direct slice
as the CLI baseline (`Angle`, `Brightness Gain`, `Size Variation`, Front
Strength/Alpha Fade/Sharp Tail, Back Strength/Alpha Fade/Sharp Tail, Noise
Variation params are present). If Back Strength, Alpha Fade, Noise Variation, or
16/32bpc paths are requested, the plug-in copies input to output rather than
pretending the unknown path is ported. Verified:

```sh
xcodebuild -project mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj -configuration Debug build
file mac/OLMDirectionalBlur/Mac/build/Debug/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur
codesign --verify mac/OLMDirectionalBlur/Mac/build/Debug/OLMDirectionalBlur.plugin
```

The binary is universal (`arm64` + `x86_64`). AE-host pixel validation is still
required on an AE machine.

`cli/OLMDirectionalBlur/main.cpp` also has an `--algorithm rotated` path that
implements the same high-level shape as `FUN_180001ec0`/`FUN_1800013e0`:
expand to a diagonal buffer, rotate the source into it, scatter horizontally,
normalize, then rotate back. It is guarded by:

```sh
python3 refs/scripts/smoke_olmdirectionalblur_cpp_rotated_cli.py
```

Current rotated C++ probe: `case_0001 max=254 mean=4.4483`,
`case_0005 max=246 mean=1.2174`. Direct/front-strength remains the better
front-only measurement for cases `0001..0005`, while rotated is the better
structural base for porting `FUN_1800028e0` component maps and
`FUN_1800038d0` row-driver logic.

`--algorithm rotated-gather` adds a simple `FUN_180001000`-style pre-scatter
alpha gather to the rotated path:

```sh
python3 refs/scripts/smoke_olmdirectionalblur_cpp_rotated_gather_cli.py
```

Current result worsens the rotated baseline: `case_0001 max=254 mean=4.8362`,
`case_0005 max=246 mean=1.2796`. This is useful negative evidence: the AEX
pre-gather alone is not enough. The next useful pass should focus on the exact
`FUN_1800038d0` coefficient flow (`param_11`, Size Variation, front/back fade,
and component-map center/half-height terms), not simply adding more blur taps.

`--algorithm rotated-alpha`, `rotated-alpha-in`, and `rotated-alpha-out` split
the `FUN_180001ec0`-style alpha-weighted bilinear rotation hypothesis. RGB is
normalized by the interpolated alpha contribution and the alpha channel stores
that alpha sum. The split probe is useful negative evidence on the current
front-only refs: alpha-weighting the input rotate (`rotated-alpha-in`, and the
legacy combined `rotated-alpha`) worsens to `case_0001 max=255 mean=4.7505`
and `case_0005 max=254 mean=1.3802`, while alpha-weighting only rotate-back
(`rotated-alpha-out`) is numerically identical to plain `rotated`
(`case_0001 max=254 mean=4.4483`, `case_0005 max=246 mean=1.2174`). After
correcting the AEX gather length to use Alpha Fade rather than Blur Strength,
`rotated-aex` lands on the same worse `4.7505` / `1.3802` pair. This keeps the
rotated harness closer to the AEX structure for future transparent/noise refs,
but also shows that simple alpha-aware rotation plus the no-op Alpha Fade
gather is not the missing front-only behavior.

`--algorithm rotated-map` now builds a `FUN_1800028e0`-style connected-component
map from the rotated alpha-valid mask. Each valid pixel carries component area,
minY, centerY, and half-height, and the row scatter uses the AEX-shaped
`param_11` idea: `pow(area / maxArea, Size Variation) * SharpTail(row,
centerY, halfHeight)` scales the effective scatter distance and Gaussian table
index rather than directly multiplying alpha amplitude. On the current
front-only references this is effectively one large component, so it matches
the regular rotated probe: `case_0001 max=254 mean=4.4483`,
`case_0005 max=246 mean=1.2174`. This is still useful because component-map
generation is now covered by `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_cli.py`.

`--algorithm rotated-map-aex` combines component-map coefficients,
alpha-weighted rotate, and the AEX-shaped Alpha Fade gather. The important fix
here is that `FUN_180001000` uses Front/Back Alpha Fade (`+0x4c`/`+0x54`) as
its gather length, not Front/Back Blur Strength. Since current cases 1..5 have
Alpha Fade 0, the gather is effectively no-op; the result is still worse than
plain `rotated` (`case_0001 mean=4.7505`, `case_0005 mean=1.3802`). The
remaining gap is therefore more likely in the exact rotate/validity and
normalization order than in component-map construction alone.

`--algorithm rotated-aex-init` and `rotated-map-aex-init` are negative
diagnostic modes for the AEX buffer-initialization hypothesis. They initialize
the post-scatter weight-sum buffer as zero and keep the copied rotated RGB as
straight color before normalization, mirroring a literal reading of the
`memcpy(_Dst,_Src)` / `FUN_1800013e0` / `param_6[0x1010]` sequence. This does
**not** improve the current refs: both variants measure `case_0001 mean=4.7724`
and `case_0005 mean=1.3862`, slightly worse than `rotated-aex`. So the simple
"center sample excluded from weight-sum" interpretation is not the missing
piece.

Fresh sub-agent/decomp cross-check:

- `FUN_1800038d0` computes `pow(component_area / max_area, SizeVariation)` from
  the `+0x8118` component map, then calls `FUN_180001000` before scatter. That
  means the same component coefficient can affect the Alpha Fade pre-pass, not
  only the scatter pass. Current cases 1..5 have Alpha Fade 0, so this does not
  explain the active front-only residual, but it matters for future cases.
- `FUN_1800013e0` applies `param_11` twice structurally: it shortens the
  effective distance (`param_9 = int(param_9 * param_11)`) and remaps the
  Gaussian index via `int(i / param_11)`. The CLI's `rotated-map` path now has
  this shape for scatter, but the exact row coordinate/span used by Sharp Tail
  is still approximate.
- RGB is normalized after scatter by `param_6[0x1010]`; alpha is a max of the
  weighted source alpha, not divided by that sum.

Sign/scale probe on `case_0005`: current `--angle-sign -1 --sample-sign -1`
is the best direct sign among the four sign combinations at `1/24`; it improves
mean from `1.2283` to `1.1838`. A scale sweep for that sign still bottoms out
near the same residual range rather than approaching exactness, so the blocker
is not just a scalar Strength conversion. The next implementation gap is still
`FUN_1800038d0`'s per-row Size Variation / Sharp Tail / alpha-validity logic.

Additional channel/scale diagnostics:

- Both `case_0001` and `case_0005` inputs are fully opaque (`alpha=255`
  everywhere). Therefore Size Variation cannot be inferred from source alpha;
  it comes from the AEX's internal map at `param_7 + 0x8118` / `FUN_180003370`
  path.
- `case_0001` reference changes only the R channel (`69906` px, alpha/G/B
  unchanged). Current direct candidate changes only R too, but only `27394` px
  versus input.
- `case_0005` reference changes R plus alpha (`11211` alpha pixels, max alpha
  delta `91`). Current direct candidate changes R only and leaves alpha
  untouched, so the missing alpha behavior is likely from the rotate-back /
  validity-mask path rather than the one-sided row scatter alone.
- `FUN_180003c90`'s runtime scale `fVar21` is ambiguous from decomp alone. It
  may be a render/downsample scale rather than frame-rate. However an
  angle-0 fast probe on `case_0001` rejected a simple scale fix:
  `1/24` (`n=70`) gave `mean=4.4597`, while `0.05` gave `4.4975`, `0.1`
  gave `4.8059`, `0.2` gave `5.4185`, and `0.5` (`n=845`) gave `4.7429`.
  Larger length expands the changed region but does not match the AEX contour.
- A fresh `case_0005`-only scale sweep with the current best direct signs
  (`angle=-1`, `sample=-1`) bottoms out slightly lower at `scale=0.08`
  (`mean=1.1640`) than `auto=1/24` (`mean=1.1838`). This is not a global fix:
  on cases `0001..0005`, `auto` averages `mean=3.7954`, `0.06` averages
  `3.8518`, and `0.08` averages `3.9372`, because cases `0001..0004` degrade
  from `mean=4.4483` to `4.6304`. Keep the smoke on `auto`; the missing piece
  is still the AEX component map / row driver, not one scalar.
- A simple "rotate validity mask back and apply it to direct output alpha"
  probe on `case_0005` also worsened the total diff (`mean=1.3070` vs direct
  `1.1838`). It produces an alpha-difference pixel count near the reference,
  but the RGB/alpha coupling is wrong. The alpha behavior needs to come from
  the rotated-buffer scatter/normalize order, not a post alpha mask.
- `FUN_1800028e0` builds the `param_7 + 0x8118` map from the rotated valid
  mask. The decompiler sometimes shows the output argument as `param_6[0x1023]`,
  but the assembly call sites load `R8 = [RBX + 0x8118]`. The map is effectively
  four floats per pixel: component area/max-area factor, min-y, center-y, and
  half-height/span. `FUN_1800038d0` uses these values for Size Variation and
  Sharp Tail. The current CLI approximates this only for no-noise fully-opaque
  refs by treating the whole image as one component and applying a vertical
  Sharp Tail factor.
- The rotated-buffer path now applies the same Sharp Tail approximation in
  rotated space. This brings `case_0001` to the direct path's level
  (`mean=4.4483`), but `case_0005` remains worse than direct
  (`rotated sample=+1 mean=1.2174`, direct sample=-1 `mean=1.1838`). Keep the
  smoke on the direct probe for now; use rotated as the next implementation
  base for the missing alpha/coverage path rather than as the current best
  measurement.
- `rotated-preserve-alpha` is a diagnostic split for RGB vs alpha coupling:
  it uses the rotated-buffer RGB result but restores the original input alpha
  on rotate-back. This improves the current `case_0005` measurement from
  plain rotated `mean=1.2174` to `mean=1.1831`, slightly better than the
  direct/front-strength smoke (`mean=1.1931`), while cases `0001..0004` remain
  at the worse rotated contour (`mean=4.4483..4.4485`). This means the rotated
  RGB path is directionally useful for `case_0005`, but the current rotated
  alpha output over-drops a small region and misses most of the AEX's subtle
  alpha fade. Do not promote this to the main smoke; use it as evidence that
  the next real fix is the exact `FUN_1800038d0` / rotate-back alpha coupling.

Rejected/rough probes:

- Direct `--strength-scale 0.03` was slightly better for `case_0005`
  (`mean=1.2205`) but worse in aggregate across `case_0001..0005` than
  `1/24`.
- The earlier narrow Gaussian approximation (`2 * (length/3)^2`) gave a lower
  probe mean (`case_0001 mean=4.3957`, `case_0005 mean=1.2212`) than the
  decomp-confirmed broad table, but it was not faithful to `FUN_180001830`.
- A simple "blur alpha, then multiply original RGB by blurred alpha" probe is
  worse than the current direct scaffold: `case_0001 mean=6.7194`,
  `case_0005 mean=1.5863` (both signs similar). Although `FUN_180001000`
  writes alpha-like accumulators, the validated path is not a naive alpha-only
  replacement for color sampling.
- `rotated-strict` adds a plain bilinear sampler with `FUN_180001ec0`'s strict
  inner-pixel border rule (`0 < ix < width-1`, `0 < iy < height-1`) without
  alpha-weighted RGB normalization. It matches the worse alpha-weighted/AEX
  split rather than improving the plain rotated baseline:
  `case_0001 mean=4.7505`, `case_0005 mean=1.3802`.
  `rotated-strict-preserve-alpha` is numerically the same useful split as
  `rotated-preserve-alpha` (`case_0001 mean=4.4483`,
  `case_0005 mean=1.1831`). This makes the next suspect the rotate-back alpha
  coupling / output compositing order rather than border clipping alone.
- Full-strength direct probe on `case_0005`: `mean=2.6480`.
- AEX-shaped rotated-buffer probe on `case_0005`: best observed
  `mean=1.2668` with scale 0.05; full-strength rotated was `mean=2.7002`.
- Approximate "Size Variation from alpha" probes were exact no-ops on
  `case_0005`, because the input alpha is fully opaque.

So the current CLI is still only a scaffold. It is better than identity on
case_0005 after the sign fix, but case_0001..0004 remain nearly identity-level
because the current direct sampler lacks the AEX per-row validity and
Size-Variation/Sharp-Tail modulation. The next real work is to prove the exact
runtime scale (`fVar21`) and port `FUN_1800038d0`'s Size Variation / Sharp Tail
alpha scaling before treating DirectionalBlur as validated.

2026-06-05 update: `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_preserve_alpha_cli.py`
was added and included in `smoke_all_algorithm_clis.py` as an expected-red
diagnostic. It keeps the rotated-buffer RGB result but restores the original
input alpha on rotate-back, preserving the best observed `case_0005` rotated
RGB residual (`max=246 mean=1.1831`) while clearly marking that the AEX alpha
path remains unported. Aggregate smoke passes with this red measurement
included.

2026-06-05 alpha-sum probe: `--algorithm rotated-alpha-sum` sums scatter alpha
before rotate-back and clamps it to 1.0. This is now covered by
`refs/scripts/smoke_olmdirectionalblur_cpp_rotated_alpha_sum_cli.py` as an
expected-red measurement. It is effectively negative evidence: `case_0001`
stays at `max=254 mean=4.4483`, while `case_0005` moves only from
`mean=1.2174` to `mean=1.2173` and increases nonzero diff pixels
(`46637 -> 46835`). The missing behavior is still the exact
`FUN_1800038d0` row driver / rotate-back alpha coupling, not a simple scatter
alpha sum.

2026-06-05 row-driver alpha-coeff probe: `--algorithm
rotated-map-alpha-coeff` applies the component-map / row-driver coefficient to
the output-alpha max contribution, leaving RGB accumulation unchanged. This is
covered by `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_alpha_coeff_cli.py`
and registered in `smoke_all_algorithm_clis.py` as an expected-red diagnostic.
It is also negative evidence: `case_0001` stays at `max=254 mean=4.4483`, while
`case_0005` worsens from `rotated-map mean=1.2174` to `mean=1.2276`. The
component-map coefficient should remain modeled as scatter distance / Gaussian
index modulation, not as a direct alpha attenuation.

2026-06-05 direct-map / AEX-pad probes:

- Decomp check: `FUN_180001ec0` rotate-back is alpha-weighted bilinear. It
  computes the bilinear sum of the four source alpha values, normalizes the RGB
  corner weights by that alpha sum, and writes the alpha sum as output alpha.
  The CLI already has an `alpha_weighted_output_rotate` path, but
  `rotated-alpha-out` is identical to `rotated` for current `case_0001` /
  `case_0005`, so these cases do not expose that coupling.
- `--algorithm rotated-aex-pad` uses the AEX-style padded buffer size derived
  from `2 - int(diagonal * -0.5)` instead of `ceil(diagonal)+4`. It is now
  covered by `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_pad_cli.py`
  and is identical to `rotated` on the current refs (`case_0001 mean=4.4483`,
  `case_0005 mean=1.2174`). Working-buffer size is not the visible miss here.
- `--algorithm direct-map` applies component-map Size Variation / Sharp Tail
  modulation to the direct sampler. It is covered by
  `refs/scripts/smoke_olmdirectionalblur_cpp_direct_map_cli.py`. This is a tiny
  positive signal only: `case_0001 mean=4.0897 -> 4.0883`, while `case_0005`
  stays `mean=1.1931`. Row-driver modulation matters, but the main residual is
  still elsewhere in the scatter/normalization model.

2026-06-05 rotated normalization / coefficient-source probes:

- `rotated-map-dest-coeff` was added as a local diagnostic after re-reading
  `FUN_1800038d0` / `FUN_1800013e0`. Using the destination pixel's component-map
  coefficient worsens `case_0005` from `rotated-map mean=1.2174` to
  `mean=1.3063`, while `case_0001` stays `mean=4.4483`. Keep the existing
  scatter-origin/source coefficient model; the current refs expose the
  destination-coeff variant as negative evidence.
- `rotated-front-strength` applies the direct probe's front-strength RGB
  denominator inside the rotated-buffer scaffold. It brings `case_0001` to the
  direct level (`mean=4.0897`) but worsens `case_0005` to `mean=1.2270`.
- `rotated-front-strength-preserve-alpha` keeps that RGB denominator but
  restores the input alpha on rotate-back. This is the best current combined
  front-only C++ diagnostic: `case_0001..0003 mean=4.0897`,
  `case_0004 mean=4.0900`, `case_0005 max=245 mean=1.1927`. It is covered by
  `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_front_strength_preserve_alpha_cli.py`
  and registered as expected-red. This is still not a validated AEX path; it
  mainly shows that the missing behavior is split between RGB denominator and
  alpha/rotate-back coupling.

2026-06-05 asm fact log refresh:

- Added `notes/OLMDirectionalBlur_ASM_FACTS.md` to keep address-level evidence
  separate from image-diff diagnostics.
- `FUN_180003c90` at `180003d39..180003dac` multiplies Front/Back Blur
  Strength and Alpha Fade (`+0x48/+0x4c/+0x50/+0x54`) by a render-context
  ratio read from `ctx+0x11c` / `ctx+0x120`, then truncates to int. The current
  CLI's `--strength-scale auto = 1 / comp.frame_rate` remains a useful PNG
  measurement hypothesis, but it is not the AEX field mapping.
- `FUN_1800038d0` facts are now recorded with addresses: component coefficient
  comes from `pow(map[p].area / max_area, size_variation)`, `FUN_180001000`
  receives that coefficient before scatter, and `FUN_1800013e0` receives
  Sharp Tail multiplied into the coefficient for front/back row scatter.
- Next DirectionalBlur implementation work should map the render-context scale
  and exact rotated buffer/validity setup before promoting any direct or
  front-strength-denominator probe to the Mac plugin.

2026-06-05 rowdriver prepass diagnostic:

- Added `--algorithm rotated-rowdriver-prepass` to
  `cli/OLMDirectionalBlur/main.cpp` plus
  `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_rowdriver_prepass_cli.py`,
  registered as an expected-red aggregate measurement.
- The probe ports the `FUN_180001000`-shaped prepass more literally than the
  older gather modes: component coefficient scales Alpha Fade span and weight
  table index, and source RGB is premultiplied by derived prepass alpha before
  scatter.
- Results are negative and match the already-worse alpha-weighted/AEX split:
  `case_0001 max=255 mean=4.7505`,
  `case_0005 max=254 mean=1.3802`.
- Added companion `rotated-rowdriver-prepass-init` to test the copied-buffer /
  zero-denominator initialization hypothesis. It is also negative:
  `case_0001 max=255 mean=4.7724`,
  `case_0005 max=254 mean=1.3862`.
- Interpretation: the prepass alone is not missing; the remaining gap is
  likely the exact caller buffer choreography around `memcpy(_Dst,_Src)`,
  denominator buffer initialization/normalization, and final rotate-back source
  selection.

2026-06-05 asm buffer-ownership refresh:

- `notes/OLMDirectionalBlur_ASM_FACTS.md` now records the no-noise/front-only
  branch's rotated work-buffer ownership around `FUN_180001ec0`.
- `FUN_180001ec0` reads `RCX/param_1` as source and writes `RDX/param_2` as
  destination. The observed order is: first work buffer populated by the AE
  callback -> rotate A into B -> copy B back to A -> row-driver writes and
  normalizes B -> clear A -> rotate B back into A -> output A by repointing
  `params+0x8090`.
- This removes one ambiguity from the next DirectionalBlur pass: the remaining
  implementation work is not "which final buffer is source?" but faithfully
  reproducing that A/B choreography and the row-driver normalization details.
- 2026-06-06 stop-condition review: A/B choreography, pad/offset, prepass,
  exact scatter/rowdriver, component half-height/center/tail, binary alpha,
  straight RGB, trunc output, truncated span, row init, scale sweep, and sign
  checks are already covered by probes and are mostly neutral/negative. Current
  opaque refs cannot separate remaining alpha/source ownership. Do not keep
  fitting DirectionalBlur via PNG-only sweeps; wait for
  `refs/reference_requests/directionalblur_context_scale_20260606.json`.

2026-06-05 A/B choreography probe:

- Added `--algorithm rotated-aex-choreo` to the C++ CLI plus
  `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_choreo_cli.py`, and
  registered it as an expected-red aggregate measurement.
- The probe builds a padded A buffer first, rotates A into the working B buffer,
  then continues through the existing rotated scatter scaffold. This is closer
  to the asm order than directly rotating the source layer into the working
  buffer.
- Results: `case_0001 max=254 mean=4.4483`,
  `case_0005 max=246 mean=1.1703`. This does not fix the angle-0 group, but it
  improves the diagonal front-only case over plain rotated (`mean=1.2174`) and
  rotated-preserve-alpha (`mean=1.1831`). Keep it as a positive signal for the
  A/B buffer setup while the remaining row-driver/normalization details are
  ported.

## OLMKiraKira

`refs/scripts/audit_olmkirakira_manifest.py` summarizes the three Windows
reference cases. The current set is small:

- `case_0001`: 960x540, Channel=2, Blur Mode=2, Merge mode=1, Brightness=1,
  Strength multiplier=100, ray lengths all 50, white colors, no ramps,
  Highlight Radius=0, Rotation=0.
- `case_0002`: same parameters as `case_0001`, but 1920x1080 input/output.
- `case_0003`: 1920x1080, Brightness Gain=9.4 and Strength multiplier=0.
  This appears to exercise a different brightness/source path, so it is not in
  the first smoke.

Initial files:

- `refs/scripts/audit_olmkirakira_manifest.py`
- `refs/scripts/olmkirakira_cli.py`
- `refs/scripts/smoke_olmkirakira_cli.py`
- `cli/OLMKiraKira/main.cpp`
- `refs/scripts/build_olmkirakira_cli.sh`
- `refs/scripts/smoke_olmkirakira_cpp_cli.py`

Ghidra-confirmed parameter layout:

- `FUN_18114c1a0` registers params with stable IDs matching the AE
  `match_name` suffixes: Glow Rotation=`1`, Brightness Gain=`2`, Vertical
  Length=`3`, Horizontal Length=`4`, Diagonal Length=`5`, Highlight Radius=`6`,
  Glow Opacity=`7`, Channel=`8`, Blur Mode=`9`, Approximated Input=`10`,
  Strength multiplier=`0xb`, Source Opacity=`0xc`, ray colors=`0xd/0xe/0xf`,
  Highlight Color=`0x10`, Merge mode=`0x11`, Use Ramp flags=`0x12/0x14/0x16`
  plus Highlight=`0x18`, Diagonal2 Length=`0x1a`, Fade Out=`0x1b`,
  Diagonal2 Color=`0x1c`, and Diagonal2 Use Ramp=`0x23`.
- `FUN_18114e860` reads those values into the runtime parameter block:
  Brightness at `+0x4`, Strength at `+0x8` after multiplying by the percent
  constant, Fade Out at `+0xc`, ray lengths at `+0x10/+0x18/+0x20/+0x28`,
  Highlight Radius at `+0x30`, Glow Opacity at `+0x38`, Source Opacity at
  `+0x3c`, Channel at `+0x40`, Merge mode at `+0x44`, Blur Mode at `+0x4c`,
  Approximated Input at `+0x50`, and comp/source height-ish data at `+0x854`.
- The Python CLI now mirrors this suffix mapping so duplicated labels such as
  `Use Ramp` do not collapse into one generic key.

Additional Ghidra structure notes:

- `FUN_18114c8f0` is a pixel-depth dispatch area; `FUN_18114cc50`,
  `FUN_18114d220`, and `FUN_18114d7f0` are render-prep variants.
- `FUN_18114f4a0` looks like the KiraKira core. It builds five ray/highlight
  buffers and coordinates the four line directions plus highlight.
- `FUN_181150790` looks like the directional helper: rotate into an axis-aligned
  buffer, blur along that axis, then rotate/crop back. This means the real
  implementation is not just integer-shift accumulation in image space.
- `FUN_181280bc0` is OpenCV `cv::boxFilter` and `FUN_181272ec0` is OpenCV
  `cv::GaussianBlur` (visible in the decompiled error paths). This confirms
  that `Blur Mode` is switching between OpenCV-style blur helpers rather than a
  hand-written ray accumulator.
- Seed helpers match the popup string `Alpha / Luminance / RGB / Brightness`:
  `Channel=1` dispatches to `FUN_18114edf0`, `Channel=2` to `FUN_181150600`,
  `Channel=4` to `FUN_18114ec60`, and the remaining RGB/Color path to
  `FUN_18114ef10`. A later stack-argument pass showed the seed exponent slot is
  the normalized Strength multiplier (`+0x8`, e.g. 100% -> `1.0`), while
  Brightness Gain (`+0x4`) is passed to the final virtual aggregation. The
  current refs all use `Channel=2`, so the smoke uses the CLI's explicit
  `--seed-mode aex` enum dispatch rather than a luma hard-code.
- Candidate ray/color aggregation helpers: `FUN_18114f020`, `FUN_18114f270`,
  `FUN_18114fd90`, and `FUN_18114ffd0`. These appear to scale by reciprocal
  weights and renormalize RGB by alpha, so the current CLI's plain
  `ray / length` normalization is only a rough scaffold.
- 2026-06-05 subagent vtable check: `OLMKiraKiraLuminance` vtable is
  `+0x00 FUN_181150600`, `+0x08 FUN_18114fd90`, `+0x10 FUN_18114ffd0`,
  `+0x18 FUN_18114eda0`, `+0x20 FUN_18114ed90`. In `FUN_18114f4a0`,
  `+0x00` creates the luminance map, `+0x18` returns component count `1`,
  `+0x20` returns a bool/flag `1`, and final aggregation calls `+0x08` when
  `param_15==1` or `+0x10` when `param_15==2`.
- The same vtable check indicates `FUN_18114fd90`'s `param_10` scale is
  **Brightness Gain (`+0x4`)**, not Strength multiplier (`+0x8`). Caller
  assembly loads `+0x4` into the stack slot consumed by the final virtual
  aggregation, while `+0x8` is a different earlier slot. This makes the current
  CLI's `brightness_gain * strength_multiplier` final scale suspect for the
  unresolved `case_0003` path.
- 2026-06-05 stack-argument correction: in `FUN_18114f4a0`, the seed virtual
  call receives the Strength slot as the luminance exponent, and the final
  `+0x08` premul aggregation receives Brightness Gain as the scale. This
  explains why `case_0003` (`Strength=0`, `Brightness=9.4`) still emits stars:
  the seed becomes roughly `luminance^epsilon * alpha`, not zero, and the final
  scale is not multiplied by Strength.
- `Blur Mode=2` in the current refs likely means the approximated Gaussian path,
  not the CLI's linear falloff. The axis blur helper has paths consistent with
  box, repeated box/approximated Gaussian, Gaussian, and a custom recursive
  mode. One visible recursive path uses `L/(L+1)` and `L/(L+1)^2`-style
  constants.
- The CLI now exposes experimental `--falloff box1/box3` plus
  `box1-radius/box3-radius` switches. In `FUN_181150790`, `Blur Mode=2` calls
  the same external 1D blur helper three times, so `box3` is structurally
  plausible. A 2026-06-05 follow-up added `--filter-border` and
  `--auto-length-scale`; using OpenCV-like reflected filtering plus
  `length_scale = input_width / 1920` makes the repeated-box model the best
  current proxy. At `gain=0.72`, `box3 --filter-border reflect
  --auto-length-scale --comp-width 1920` gave `case_0001 max=22 mean=0.8380`
  and `case_0002 max=24 mean=1.1630`. A later border sweep found SciPy
  `mirror` / OpenCV-like `BORDER_REFLECT_101` slightly closer on cases 1/2
  (`case_0001 mean=0.8379`, `case_0002 mean=1.1627`), so the smoke now uses
  `--filter-border mirror`.
- 2026-06-05 C++/Mac update: the native C++ scaffold originally used a
  `(width-1,height-1)` corner extent for `rotate(..., reshape=True)` and
  produced a 1501x1501 intermediate when rotating the 1061x1061 half-res
  diagonal buffer back. SciPy/OpenCV-like reshape uses image bounds
  `[0,height] x [0,width]` with `int(ptp + 0.5)`, which gives 1500x1500.
  Porting that shape rule to `cli/OLMKiraKira/main.cpp` improves C++
  `case_0001` from `max=27 mean=0.9821` to `max=22 mean=0.8382`, matching the
  Python scaffold (`mean=0.8380`) within rounding. `case_0002` remains
  `max=24 mean=1.1630`. The same rotate shape rule is reflected in
  `mac/OLMKiraKira/OLMKiraKira.cpp`; `scripts/build_all_mac_plugins.sh` passes
  afterward.
  (`case_0001 mean=1.4519`, `case_0002 mean=2.1057`) in the smoke test.
- Final merge still needs porting. Current refs have Merge mode `1`
  (`premultiply add` in the menu string). Ghidra suggests this path combines
  source/glow with premultiplied alpha normalization, while another mode is a
  simpler add/clamp path.

Current smoke:

```sh
python3 refs/scripts/smoke_olmkirakira_cli.py
python3 refs/scripts/smoke_olmkirakira_cpp_cli.py
python3 refs/scripts/smoke_olmkirakira_brightness_probe_cli.py
```

The first CLI was a deliberately simple white-ray scaffold: luma seed,
linear falloff, bidirectional vertical/horizontal/two diagonals, no
ramps/highlight radius. A one-sided ray was already much better than identity,
but bidirectional rays matched the star shape much more closely.
The current CLI adds a more AEX-shaped experimental path:

- `--ray-mode axis-rotate` rotates the seed into diagonal axes, applies a 1D
  line blur, then rotates/crops back. This matches the high-level
  shape of `FUN_181150790` better than integer shift accumulation.
- `--compose-mode aex-premul` applies the `FUN_18114e110`/8bpc-style
  premultiply-add final merge for Merge mode `1` (the 16/32bpc variants are
  `FUN_18114ddc0` and `FUN_18114e460` with the same high-level formula).
- Current smoke uses `--seed-mode aex --falloff box3 --gain-scale 0.72
  --ray-mode axis-rotate --compose-mode aex-premul --filter-border mirror
  --auto-length-scale --comp-width 1920`.

Historical/simple scaffold:

- `case_0001` identity: `max=135`, `mean=10.9509`,
  `nz=407490/518400`.
- `case_0001` luma/linear bidirectional ray CLI (`gain=0.95`): `max=60`,
  `mean=2.9395`, `nz=416485/518400`.
- `case_0002` identity: `max=142`, `mean=12.2434`,
  `nz=1711834/2073600`.
- `case_0002` luma/linear bidirectional ray CLI (`gain=0.95`): `max=41`,
  `mean=2.6621`, `nz=1605566/2073600`.

Current axis-rotated/premul scaffold:

- `case_0001`: `max=22`, `mean=0.8379`, `nz=302803/518400`.
- `case_0002`: `max=24`, `mean=1.1627`, `nz=1374328/2073600`.
- `case_0003` Brightness/Strength=0 probe: `max=60`, `mean=1.7073`,
  `nz=1367385/2073600`.

Native C++ scaffold:

- `cli/OLMKiraKira/main.cpp` ports the same parameter mapping, AEX-style
  luminance seed, repeated-box/reflected-border ray model, comp-width length
  scaling, and premultiply-add merge into an AE-portable C++ CLI. The diagonal
  path now uses a bilinear rotate-into-axis buffer, horizontal box blur, rotate
  back, and center crop, matching the high-level shape of Python/SciPy's
  `axis-rotate` proxy and the Ghidra `FUN_181150790` structure.
- `refs/scripts/build_olmkirakira_cli.sh` builds
  `cli/OLMKiraKira/olmkirakira_cli`.
- `refs/scripts/smoke_olmkirakira_cpp_cli.py` is intentionally red:
  `case_0001 max=22 mean=0.8382 nz=302809/518400`,
  `case_0002 max=24 mean=1.1627 nz=1374344/2073600`,
  `case_0003 max=60 mean=1.7073 nz=1367391/2073600`.
  This is close to the Python proxy (`case_0001 mean=0.8379`,
  `case_0002 mean=1.1627`) and is now the better native baseline for future
  Mac plug-in integration.

Mac plug-in scaffold:

- `mac/OLMKiraKira/` is now added with match name `OLM OLM Kira Kira` and a
  parameter layout keyed to the Windows manifest suffix/disk-id order.
- The renderer now uses the all-ray two-temp/no-fastpath candidate: centered
  temp-A ROI copy, in-place-style forward rotation, horizontal REFLECT_101 box
  passes into temp-B, rotate-back, and centered final ROI copy for all four
  rays. Current red probe remains `0.8506/1.1570/1.0563`; build is universal
  and codesign OK.
- Verified 2026-06-05:
  `xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj -configuration Debug build`
  succeeds, the output is a universal `x86_64/arm64` bundle, and
  `codesign --verify mac/OLMKiraKira/Mac/build/Debug/OLMKiraKira.plugin`
  succeeds.
- `scripts/build_all_mac_plugins.sh` now includes `OLMKiraKira` and completed
  with `all mac plugin builds verified (Debug)` after the addition.
- This is a buildable scaffold, not an exact port yet. It inherits the C++ CLI
  all-ray two-temp/no-fastpath discrepancy: `case_0001 mean=0.8506`,
  `case_0002 mean=1.1570`, and `case_0003 mean=1.0563`.

Implementation note: the Python CLI now preserves manifest zero values via a
`float_param()` helper. The earlier `params.get(...) or default` pattern
misread `Strength multiplier=0` as `100`, which hid the real `case_0003`
problem.

Nearby probes with the corrected generated `_params` files: `gain=0.70`
with round quantization gives `case_0001 mean=0.8682`, `case_0002 mean=1.2274`;
`gain=0.72` with the older `reflect` border gave `case_0001 mean=0.8380`,
`case_0002 mean=1.1630`; with the current `mirror` border it gives
`case_0001 mean=0.8379`, `case_0002 mean=1.1627`;
`gain=0.75` gives `case_0001 mean=0.9884`, `case_0002 mean=1.2526`.
`gain=0.72` is the best plausible round-quantized two-case average observed
so far. A `gain=0.70` + ceil probe averaged slightly lower, but ceil
quantization is not adopted because the rest of the port uses round/lround.

`case_0003` reference: identity `mean=73.6249`. After fixing zero-value parsing,
the older axis/premul CLI became identity because it incorrectly used
`brightness_gain * strength_multiplier` as the final glow scale. The corrected
Ghidra stack mapping uses normalized Strength as the seed exponent and
Brightness Gain as the final aggregation scale. With the current repeated-box /
REFLECT_101-style proxy, `case_0003` improves to `max=60 mean=1.7073`. This is
still not exact, but it is now a normal KiraKira ray path rather than a
separate source-only hack.

2026-06-05 update: `refs/scripts/olmkirakira_cli.py` now has experimental
`--strength-override`, `--scale-mode`, `--scale-override`, and
`--seed-exponent-override` knobs so the unresolved `Strength=0` path can be
measured without editing manifests.
`smoke_olmkirakira_brightness_probe_cli.py` now runs `case_0003` with
`--seed-mode aex --falloff box3 --gain-scale 0.72 --ray-mode axis-rotate
--compose-mode aex-premul --scale-mode aex --filter-border mirror
--auto-length-scale --comp-width 1920`. This is still a red probe, but it
improves the case from identity `mean=73.6249` and the older
`max seed + scale_override 16` probe (`max=110 mean=6.4745`) to
`max=60 mean=1.7073`.

Brightness-as-seed-exponent negative probe: forcing `--seed-exponent-override
9.4` on `case_0003` with the same repeated-box path worsens dramatically to
`max=255 mean=58.2944`. Keep the current Strength-as-seed-exponent /
Brightness-as-final-scale model; the remaining case3 miss is more likely in
the exact blur/aggregation path than the seed exponent slot.

Fast sweeps before this correction showed `max` seed at direct scale `16` was
the best empirical probe (`mean=6.4745`), but the stack mapping makes that an
artifact rather than the best model. The remaining open problem is now the
exact OpenCV `Blur Mode=2` kernel/normalization and small crop/border details,
not whether Strength should suppress final glow.

Next KiraKira work is to replace the remaining repeated-box approximation with
the exact `Blur Mode=2` kernel/normalization and tighten the rotate/crop border
behavior.

2026-06-05 merge-mode probe:

- Subagent diff audit found the current C++ residual is RGB-only: alpha diff is
  zero for all three current cases. `case_0001/0002` candidates are slightly
  dark on average, while `case_0003` is slightly bright.
- `cli/OLMKiraKira/main.cpp` now has diagnostic `--compose-mode aex-add-rgb`
  and `--compose-mode aex-screen-rgb` branches. They are intentionally not in
  the aggregate smoke because both are negative evidence:
  - `aex-add-rgb`: `case_0001 max=87 mean=4.6616`,
    `case_0002 max=87 mean=4.8794`.
  - `aex-screen-rgb`: `case_0001 max=87 mean=4.6070`,
    `case_0002 max=87 mean=4.8170`.
- The current premul-average path remains much closer (`case_0001 mean=0.8382`,
  `case_0002 mean=1.1630`). The remaining miss is unlikely to be a simple
  additive/screen Merge mode replacement; keep focus on exact `Blur Mode=2`
  OpenCV kernel size, anchor, border, and normalization.

2026-06-05 box-size probe:

- Ghidra shows the highlight buffer path in `FUN_18114f4a0` expands its size as
  `length * 2 + 1`, while the four ray paths go through `FUN_181150790` and call
  `cv::boxFilter` three times for `Blur Mode=2`.
- Added diagnostic `--box-size-mode length|radius` to
  `cli/OLMKiraKira/main.cpp` and
  `refs/scripts/smoke_olmkirakira_cpp_box_size_probe_cli.py`.
- Applying `2*length+1` uniformly to the ray boxes is negative evidence:
  with the current `mirror` border, `radius` worsens to
  `case_0001 max=53 mean=3.0404`, `case_0002 max=57 mean=3.3702`, versus
  baseline `length` `case_0001 max=22 mean=0.8382`,
  `case_0002 max=24 mean=1.1627`.
- Keep the baseline `length` ray model. The next likely source is exact
  OpenCV warp/boxFilter anchor, border, output crop, or final five-buffer
  aggregation normalization rather than a simple radius-vs-size switch.

2026-06-05 Glow Rotation plumbing:

- The current three Windows reference cases all have Glow Rotation=`0`, so this
  is not expected to improve the present PNG diffs.
- `cli/OLMKiraKira/main.cpp`, `refs/scripts/olmkirakira_cli.py`, and
  `mac/OLMKiraKira/OLMKiraKira.cpp` now add `glow_rotation` to the four ray
  base angles (`90/0/45/-45`). This closes a real parameter-compatibility hole
  for future random cases with nonzero rotation.
- Regression checks after the change:
  - C++ CLI unchanged: `case_0001 max=22 mean=0.8382`,
    `case_0002 max=24 mean=1.1630`, `case_0003 max=60 mean=1.7023`.
  - Python CLI unchanged: `case_0001 max=22 mean=0.8380`,
    `case_0002 max=24 mean=1.1630`.
  - `xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj
    -configuration Debug build` succeeds.

2026-06-05 REFLECT_101 border plumbing:

- A Python border sweep found `--filter-border mirror` slightly better than
  `reflect` on cases 1/2:
  - `reflect`: `case_0001 mean=0.8380`, `case_0002 mean=1.1630`.
  - `mirror`: `case_0001 mean=0.8379`, `case_0002 mean=1.1627`.
  - `nearest`, `constant`, and `wrap` were worse.
- `cli/OLMKiraKira/main.cpp` now parses `--filter-border reflect|mirror` and
  implements the `mirror` path as REFLECT_101-style indexing. The C++ smoke now
  runs with `mirror`: `case_0001 max=22 mean=0.8382`,
  `case_0002 max=24 mean=1.1627`, `case_0003 max=60 mean=1.7073`.
- `mac/OLMKiraKira/OLMKiraKira.cpp` uses the same REFLECT_101-style indexing.
  `xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj
  -configuration Debug build` succeeds after the change.
- This is a small OpenCV-alignment step, not an exact-port claim. It improves
  the simple cases very slightly while `case_0003` gets slightly worse
  (`1.7023 -> 1.7073`), so the exact blur kernel/aggregation remains open.
- Aggregate verification after this change: `python3
  refs/scripts/smoke_all_algorithm_clis.py` exits 0. All green gates pass, and
  every registered red-measurement, including the updated KiraKira
  `mirror`/box-size probes, is observed as `DIFF-observed`.

2026-06-05 rotate/crop probes:

- `refs/scripts/olmkirakira_cli.py` now exposes diagnostic
  `--crop-offset-y`, `--crop-offset-x`, `--rotate-order`, and
  `--rotate-prefilter` options. These are Python-only probes; the C++/Mac
  scaffold still uses the current bilinear center-crop path.
- Crop origin sweep over offsets `[-1, 0, 1]` showed `(0,0)` is clearly best.
  Neighbor offsets pushed cases 1/2 to roughly `mean=1.12..1.48`, so the
  remaining residual is not a simple one-pixel crop-origin mistake.
- Rotation interpolation sweep:
  - `order=0`: `case_0001 mean=0.9622`, `case_0002 mean=1.2078`.
  - `order=1` / current bilinear: `case_0001 mean=0.8379`,
    `case_0002 mean=1.1627`.
  - `order=3 --rotate-prefilter`: improves cases 1/2 to
    `case_0001 max=23 mean=0.8234`, `case_0002 max=25 mean=1.1430`, but
    worsens the Strength=0 case to `case_0003 max=66 mean=2.5628`.
- Added `refs/scripts/smoke_olmkirakira_rotate_probe_cli.py` and registered it
  as an expected-red aggregate measurement. Do not port cubic rotation to
  C++/Mac as the default unless later evidence explains the case3 regression.

2026-06-05 C++ rotate-filter probe:

- Added diagnostic `--rotate-filter bilinear|bicubic` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_rotate_filter_probe_cli.py`.
- The default remains `bilinear`; this probe is measurement-only.
- The C++ `bicubic` path uses a portable Catmull-Rom-style cubic sampler and is
  negative evidence, not an OpenCV/SciPy exact match:
  - `bilinear`: `case_0001 max=22 mean=0.8382`,
    `case_0002 max=24 mean=1.1627`,
    `case_0003 max=60 mean=1.7073`.
  - `bicubic`: `case_0001 max=122 mean=7.9161`,
    `case_0002 max=119 mean=8.0050`,
    `case_0003 max=169 mean=19.6771`.
- This means the Python `order=3 --rotate-prefilter` improvement on cases 1/2
  should not be interpreted as "use any cubic rotate" in the native port. Keep
  the C++/Mac baseline bilinear path and keep looking at exact OpenCV
  warpAffine/boxFilter arguments, anchor/border handling, or final
  normalization.

2026-06-05 C++ rotate-border / warp-mode probes:

- Added diagnostic `--rotate-border edge|constant` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_rotate_border_probe_cli.py`.
  `constant` treats bilinear taps outside the source image as zero, matching
  OpenCV `warpAffine(..., BORDER_CONSTANT)` more closely than the old
  edge-clamped sampler.
- `constant` improves all three C++ reference cases slightly and is now the
  native default:
  - old `edge`: `case_0001 max=22 mean=0.8382`,
    `case_0002 max=24 mean=1.1627`,
    `case_0003 max=60 mean=1.7073`.
  - new `constant`: `case_0001 max=22 mean=0.8381`,
    `case_0002 max=24 mean=1.1623`,
    `case_0003 max=60 mean=1.7003`.
- `mac/OLMKiraKira/OLMKiraKira.cpp` now uses the same constant-zero bilinear
  tap rule. `xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj
  -configuration Debug build` succeeds after the change.
- Added diagnostic `--warp-mode current|opencv-center` plus
  `refs/scripts/smoke_olmkirakira_cpp_warp_mode_probe_cli.py`. A
  `width*0.5`/`height*0.5` OpenCV-center/min-corner affine convention is
  negative evidence for the current references:
  - `current + constant`: `case_0001 mean=0.8381`,
    `case_0002 mean=1.1623`, `case_0003 mean=1.7003`.
  - `opencv-center + constant`: `case_0001 mean=0.8676`,
    `case_0002 mean=1.1658`, `case_0003 mean=1.9845`.
- Keep the current center/crop convention for now. The next KiraKira target is
  still exact OpenCV `boxFilter`/aggregation behavior, not a wholesale affine
  center swap.

2026-06-05 C++ glow-normalize / aggregation probes:

- Added diagnostic `--glow-normalize union|sum` plus
  `refs/scripts/smoke_olmkirakira_cpp_glow_normalize_probe_cli.py`.
  This checks whether RGB should be normalized by the alpha union or by the
  sum of per-ray alpha weights after ray coloring.
- `union` keeps the current best baseline:
  `case_0001 max=22 mean=0.8381`,
  `case_0002 max=24 mean=1.1623`,
  `case_0003 max=60 mean=1.7003`.
  `sum` is strong negative evidence:
  `case_0001 max=41 mean=2.3386`,
  `case_0002 max=48 mean=2.6722`,
  `case_0003 max=133 mean=21.7350`.
- Added diagnostic `--aggregation-mode current|fd90-five|fd90-exact` plus
  `refs/scripts/smoke_olmkirakira_cpp_aggregation_probe_cli.py`.
  `fd90-five` mirrors the decompiled `FUN_18114fd90` shape by aggregating
  five layers (`vertical`, `horizontal`, `diagonal`, zero highlight,
  `diagonal2`) into a fresh output buffer before final source/glow compose.
  `fd90-exact` keeps the same five-layer shape but spells out the
  `FUN_18114fd90`-style `ray > epsilon`, `clamp(ray * brightness)`, RGB add,
  alpha-union, and final RGB normalization order.
- `fd90-five` is effectively neutral against current:
  `case_0001 max=22 mean=0.8381 nz=302780/518400`,
  `case_0002 max=24 mean=1.1623 nz=1373909/2073600`,
  `case_0003 max=60 mean=1.7003 nz=1367180/2073600`.
  `fd90-exact` is also neutral:
  `case_0001 max=22 mean=0.8381 nz=302780/518400`,
  `case_0002 max=24 mean=1.1623 nz=1373909/2073600`,
  `case_0003 max=60 mean=1.7003 nz=1367172/2073600`.
  Current differs only by one non-zero pixel in case 0001. This strongly
  clears final five-buffer aggregation as the main residual source. Next
  KiraKira target should be exact OpenCV `boxFilter` phase/anchor/border or
  exact `warpAffine`/crop sampling details.

2026-06-05 C++ box-anchor probe:

- Added diagnostic `--box-anchor-mode opencv|floor-left|origin|end` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_box_anchor_probe_cli.py`.
  Default `opencv` preserves the existing `anchor=(-1,-1)` / floor-center
  behavior.
- Results:
  - `opencv`: `case_0001 max=22 mean=0.8381`,
    `case_0002 max=24 mean=1.1623`,
    `case_0003 max=60 mean=1.7003`.
  - `floor-left`: `case_0001 max=22 mean=0.8381`,
    `case_0002 max=25 mean=1.2197`,
    `case_0003 max=61 mean=2.5483`.
  - `origin`: `case_0001 max=101 mean=7.6446`,
    `case_0002 max=109 mean=8.5897`,
    `case_0003 max=255 mean=41.1855`.
  - `end`: `case_0001 max=110 mean=7.7687`,
    `case_0002 max=113 mean=8.6222`,
    `case_0003 max=255 mean=41.2080`.
- Anchor/phase is negative evidence. Keep default `opencv`; the remaining
  residual is more likely exact OpenCV `boxFilter` border/rounding/output-depth
  behavior, exact `warpAffine` sampling, or crop coordinates.

2026-06-05 C++ box-normalize probe:

- Added diagnostic `--box-normalize true|false` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_box_normalize_probe_cli.py`.
  It tests the OpenCV `cv::boxFilter(..., normalize=...)` argument for the
  three repeated Blur Mode=2 passes.
- `true` preserves the current best baseline:
  `case_0001 max=22 mean=0.8381`,
  `case_0002 max=24 mean=1.1623`,
  `case_0003 max=60 mean=1.7003`.
- `false` is strong negative evidence:
  `case_0001 max=255 mean=151.5376`,
  `case_0002 max=255 mean=148.1213`,
  `case_0003 max=255 mean=88.8005`.
- Keep normalized boxFilter. After size/anchor/normalize/final aggregation/RGB
  normalize/rotate border/warp center probes, the remaining KiraKira residual
  is most likely exact OpenCV border/rounding/output-depth behavior or
  rotate/crop coordinate details.

2026-06-05 C++ box-output-depth probe:

- Added diagnostic `--box-output-depth float|u8-each|u16-each` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_box_output_depth_probe_cli.py`.
  It quantizes the scalar ray buffer after each normalized box pass to test
  whether OpenCV is effectively casting through integer Mat depth.
- Results:
  - `float`: `case_0001 max=22 mean=0.8381`,
    `case_0002 max=24 mean=1.1623`,
    `case_0003 max=60 mean=1.7003`.
  - `u8-each`: `case_0001 max=22 mean=0.8565`,
    `case_0002 max=24 mean=1.1601`,
    `case_0003 max=60 mean=1.9693`.
  - `u16-each`: `case_0001 max=22 mean=0.8381`,
    `case_0002 max=24 mean=1.1623`,
    `case_0003 max=60 mean=1.7002`.
- `u8-each` is negative evidence despite a tiny case 0002 improvement.
  `u16-each` is effectively neutral and not worth porting. Keep the default
  float path; the remaining residual is more likely exact OpenCV border
  treatment, interpolation/crop coordinates, or another pre/post ray detail.

2026-06-05 C++ crop-mode probe:

- Added diagnostic `--crop-mode floor|ceil|round` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_crop_mode_probe_cli.py`.
  It changes the final center-crop origin after inverse rotation.
- For the current three references all modes are identical:
  `case_0001 max=22 mean=0.8381`,
  `case_0002 max=24 mean=1.1623`,
  `case_0003 max=60 mean=1.7003`.
- The present cases therefore do not expose a floor-vs-ceil crop-origin issue.
  Keep default `floor`. Remaining KiraKira work should focus on exact
  `warpAffine` sampling/output-size math, OpenCV border handling in the
  rotated intermediate, or another pre/post ray detail.

2026-06-05 C++ rotate-size probe:

- Added diagnostic `--rotate-size-mode round|floor|ceil` to
  `cli/OLMKiraKira/main.cpp` plus
  `refs/scripts/smoke_olmkirakira_cpp_rotate_size_probe_cli.py`.
  It changes the rotated intermediate canvas extent rounding for both forward
  and inverse rotation.
- Results:
  - `round`: `case_0001 max=22 mean=0.8381`,
    `case_0002 max=24 mean=1.1623`,
    `case_0003 max=60 mean=1.7003`.
  - `floor`: `case_0001 max=27 mean=0.9949`,
    `case_0002 max=28 mean=1.2704`,
    `case_0003 max=82 mean=4.2024`.
  - `ceil`: `case_0001 max=27 mean=0.9823`,
    `case_0002 max=28 mean=1.2645`,
    `case_0003 max=85 mean=3.9547`.
- `floor`/`ceil` are negative evidence. Keep default `round`. Remaining
  KiraKira residual is less likely output-size rounding and more likely exact
  `warpAffine` pixel sampling/interpolation, OpenCV border behavior in the
  rotated intermediate, or another pre/post ray detail.

2026-06-05 KiraKira asm-first boxFilter/warpAffine note:

- Added `notes/OLMKiraKira_ASM_FACTS.md` as the dedicated objdump fact log for
  this plugin. Keep using `notes/PORTING_BOARD.md` for progress and
  measurements, but put address-level call evidence in the dedicated facts
  page.
- `FUN_181150790` Blur Mode 2 calls `FUN_181280bc0` (`cv::boxFilter`) three
  times. The asm at `18115110a..18115116f`, `181151174..1811511c2`, and
  `1811511c7..181151215` maps to `ddepth=dst.type&7`,
  `ksize=(length,1)`, `anchor=(-1,-1)`, `borderType=4`, and a one-byte
  normalize flag from `[RBP+0x1a0]`.
- 2026-06-06 follow-up objdump pass traced that normalize byte back through the
  caller: `FUN_18114f4a0` calls the seed/descriptor vtable function at `+0x20`
  (`18114f65e..18114f667`) and stores returned `AL` at `[rsp+0x50]`; the ray
  call then copies it to outgoing `[rsp+0x40]`, where `FUN_181150790` receives
  it as `param_9`/`RBP+0x1a0`. For current `Channel=2` refs this vtable slot is
  `FUN_18114ed90`, which returns `1`, matching the normalized boxFilter path.
- `borderType=4` is OpenCV `BORDER_REFLECT_101`, matching the current C++
  smoke's `--filter-border mirror`. The existing negative probes for
  `box-size=radius`, alternate anchors, `normalize=false`, and `u8-each`
  are now also supported by the asm call shape rather than just image diffs.
- `FUN_181297ac0` is the OpenCV `cv::warpAffine` wrapper. The two ray-helper
  calls at `1811508d7..181150941` and `181150f80..181150ff8` pass
  `flags=1` (`INTER_LINEAR`), `borderMode=0` (`BORDER_CONSTANT`), and a zero
  scalar. Remaining KiraKira residual is therefore more likely exact OpenCV
  4.5.5 `warpAffine` destination canvas / dsize / crop behavior, or another
  pre/post ray detail, than a simple `boxFilter` argument mismatch.
- 2026-06-06 follow-up: `FUN_1811512a0` delegates matrix construction to
  `FUN_1812943d0`, which matches OpenCV `cv::getRotationMatrix2D_`
  (`alpha=cos`, `beta=sin`, and the standard
  `(1-alpha)*cx - beta*cy` / `beta*cx + (1-alpha)*cy` translations).
  Added diagnostic `--warp-mode aex-getrot` plus
  `refs/scripts/smoke_olmkirakira_cpp_aex_getrot_probe_cli.py`. The naive
  output-center/inverse-map hypothesis is strong negative evidence:
  `case_0001 max=63 mean=5.9449`, `case_0002 max=68 mean=6.6790`,
  `case_0003 max=255 mean=27.6616`, versus baseline
  `0.8381/1.1623/1.7003`.
  So the next target is not a simple getRotationMatrix2D formula swap; it is
  exact source/destination Mat/ROI placement, dsize/crop behavior, or
  OpenCV 4.5.5 sampling details.
- The same pass added diagnostic `--warp-mode aex-direct-back` plus
  `refs/scripts/smoke_olmkirakira_cpp_direct_back_probe_cli.py` after checking
  that the rotate-back `warpAffine` dsize is the final ray descriptor in
  `FUN_181150790`. The approximation writes the inverse rotation directly into
  the final ray buffer using the observed rotated-buffer center. It is negative:
  `case_0001 max=35 mean=0.9928`, `case_0002 max=43 mean=1.3755`,
  `case_0003 max=255 mean=4.4660`, versus baseline
  `0.8381/1.1623/1.7003`. Keep this as diagnostic evidence; the next target is
  exact Mat/ROI placement rather than adopting direct-back in the port.
- 2026-06-06 follow-up: `FUN_181157ed0` is not a matrix adjustment helper; its
  decomp/asm matches `cv::Mat` move-assignment (`cv::Mat::operator =` strings
  are in the failure path). It copies/moves header and step storage, then clears
  the source header. `FUN_181156cd0` is the ROI/header constructor: its rectangle
  memory layout is OpenCV `Rect(x, y, width, height)`, and it sets
  `rows=height`, `cols=width`,
  `data = src.data + y * step[0] + x * elemSize`. Therefore the
  next KiraKira target is exact ROI/source-destination placement around
  `FUN_181156cd0` and `FUN_18115cfb0`, not `FUN_181157ed0`.
- 2026-06-06 follow-up: `FUN_18115cfb0` itself is OpenCV 4.5.5
  `cv::Mat::copyTo` shape, not KiraKira-specific copy logic. It validates
  channel/type compatibility, creates the destination, and falls through to
  row `memcpy` when no conversion is needed. Existing C++ crop probes
  (`floor`, `ceil`, `round`) all stayed at the baseline
  `case_0001/0002/0003 mean=0.8381/1.1623/1.7003`, so the remaining mismatch is
  not a simple final center-crop rounding issue. Continue at caller-generated
  `Rect` values and exact `warpAffine` dsize/center semantics.
- 2026-06-06 warpAffine detail: `FUN_181297ac0` maps `param_5 & 7` to the
  interpolation mode and checks `param_5 & 0x10` before internally inverting the
  affine matrix. KiraKira passes `param_5=1`, `param_6=0`, and a zero scalar
  pointer for both forward and rotate-back calls, i.e. OpenCV
  `INTER_LINEAR`, no `WARP_INVERSE_MAP`, `BORDER_CONSTANT`, `borderValue=0`.
  This confirms warp border handling is constant-zero even though the
  boxFilter stage uses `BORDER_REFLECT_101`.
- 2026-06-06 AEX frame-warp probe: added diagnostic `--warp-mode aex-frame`,
  which writes forward and rotate-back warps directly into the original frame
  dimensions with center `(width*0.5, height*0.5)`. It is worse:
  `case_0001 mean=1.4465`, `case_0002 mean=1.9139`,
  `case_0003 mean=6.9617`, versus baseline `0.8381/1.1623/1.7003`.
  Therefore the AEX dsize/Rect evidence needs the caller's ROI/temp-Mat
  placement modeled more exactly; a simple full-frame direct warp is not enough.
- 2026-06-06 ROI placement detail: in `FUN_181150790`, the first ROI uses
  `param_3` as the centering frame and `param_2` as the temp size:
  `x=int(param_3.cols*0.5)-param_2.cols/2`,
  `y=int(param_3.rows*0.5)-param_2.rows/2`,
  `width=param_2.cols`, `height=param_2.rows`, followed by `copyTo(param_2)`.
  This is the next exact placement rule to model; current CLI still mostly
  approximates the flow with rotate-canvas/crop probes.
- 2026-06-06 centered-ROI temp probe: added diagnostic
  `--warp-mode aex-roi-temp`, which copies the centered ROI into the AEX-sized
  temp buffer before warping. The naive model is strongly worse:
  `case_0001 mean=5.1944`, `case_0002 mean=5.9919`,
  `case_0003 mean=26.1768`, so do not adopt it. The remaining target is exact
  source/destination Mat orientation and dsize mapping across the two
  `FUN_181297ac0` calls.
- 2026-06-06 warpAffine argument mapping: `FUN_181297ac0` is
  `warpAffine(src, dst, M, dsize, flags, borderMode, borderValue)`, with
  `0x1010000` InputArray wrappers and `0x2010000` OutputArray wrappers. The
  first ray-helper call wraps `R14` as both src and dst and uses matrix
  `[rbp+0x60]`. The rotate-back call wraps `R12` as both src and dst and uses
  matrix `local_f8`; `[rbp+0x60]` is the forward matrix local, not the
  rotate-back source Mat. This corrects the next implementation target: model
  the R14-to-R12 two-temp relationship rather than a one-temp rotate-back path.
- 2026-06-06 in-place temp probe: added diagnostic
  `--warp-mode aex-inplace-temp`, approximating the first same-src/dst
  `warpAffine` wrapper as an in-place rotation of the centered temp buffer,
  followed by temp blur and rotate-back to the full frame. It is strongly
  negative: `case_0001 mean=8.7256`, `case_0002 mean=9.1471`,
  `case_0003 mean=33.4284`, versus baseline
  `0.8381/1.1623/1.7003`. Keep it as evidence only; this rules out the simple
  "centered ROI temp + in-place forward warp" interpretation and points back to
  exact Mat header/object lifetime mapping around `R14`, `[rbp+0x60]`, and
  `R12`.
- 2026-06-06 corrected two-temp probe: after rechecking `FUN_181297ac0`, added
  `--warp-mode aex-two-temp`, which follows the observed `R14 -> R12`
  choreography: ROI copy into `R14`, in-place forward warp on `R14`, blur into
  `R12`, in-place rotate-back on `R12`, then centered ROI copy to the final
  output. It is mixed: `case_0001 mean=0.8531`, `case_0002 mean=1.1555`,
  `case_0003 mean=1.1870`, versus default `0.8381/1.1623/1.7003`. Do not adopt
  it as default yet; it is evidence that the two-temp path matters especially
  for Strength=0, while case1 still needs another exact pre/post ray detail.
- 2026-06-06 Python OpenCV primitive probe: added diagnostic
  `--ray-mode opencv-two-temp` to `refs/scripts/olmkirakira_cli.py` plus
  `refs/scripts/smoke_olmkirakira_opencv_two_temp_probe_cli.py`. This calls
  `cv2.warpAffine(..., INTER_LINEAR, BORDER_CONSTANT)` and
  `cv2.boxFilter(..., ddepth=-1, ksize=(length,1), anchor=(-1,-1),
  normalize=True, BORDER_REFLECT_101)` directly in the same two-temp
  choreography. With temporary Python 3.12 + OpenCV 4.13.0, results are
  `case_0001 mean=0.8504`, `case_0002 mean=1.1570`,
  `case_0003 mean=1.0514`, versus the current Python axis-rotate baseline
  `0.8379/1.1627/1.7073`. This strongly supports moving the native C++/Mac
  ray path toward exact OpenCV primitives/two-temp behavior for case3, while
  keeping case1 as a remaining placement/Mat-header exactness problem.
- 2026-06-06 OpenCV 4.5.5 parity check: created a temporary Python 3.9 venv at
  `/tmp/olm-opencv455-venv` with `opencv-python==4.5.5.64`, `numpy==1.26.4`,
  and Pillow, then ran
  `OLM_PROBE_PYTHON=/tmp/olm-opencv455-venv/bin/python python3
  refs/scripts/smoke_olmkirakira_opencv_two_temp_probe_cli.py`. Results are
  `case_0001 mean=0.8504`, `case_0002 mean=1.1570`,
  `case_0003 mean=1.0514`, matching the prior OpenCV 4.13 measurement and
  closely matching the C++ two-temp/no-fastpath probe
  `0.8506/1.1570/1.0563`. The remaining KiraKira residual is therefore not
  explained by OpenCV version drift between 4.13 and AEX's 4.5.5; keep chasing
  exact Mat/ROI/copyTo aliasing, destination canvas, or final composition
  details.
- 2026-06-06 OpenCV two-temp ROI/alias probe: added
  `--ray-mode opencv-two-temp-alias-roi` and
  `refs/scripts/smoke_olmkirakira_opencv_two_temp_alias_probe_cli.py`. This
  keeps the same OpenCV 4.5.5 two-temp choreography but allocates explicit
  zero temp buffers, writes the centered source ROI into temp-A, and uses
  `dst=temp_a` / `dst=temp_b` for `warpAffine` and `boxFilter`. Results are
  identical to the ordinary OpenCV two-temp probe:
  `case_0001 mean=0.8504`, `case_0002 mean=1.1570`,
  `case_0003 mean=1.0514`. Therefore simple Mat header / ROI view /
  same-destination aliasing is not the remaining residual; focus next on the
  destination canvas, final composition, or another pre/post ray detail.
- 2026-06-06 harness update: the ordinary and ROI/alias OpenCV probes are now
  registered in `refs/scripts/smoke_all_algorithm_clis.py` as
  `optional-red-measurement` entries. Use
  `python3 refs/scripts/smoke_all_algorithm_clis.py --profile opencv` to run
  just these probes. If the selected Python lacks `cv2`, the aggregate reports
  `SKIP missing optional cv2`; set `OLM_PROBE_PYTHON` to an OpenCV environment
  such as the temporary 4.5.5 venv to reproduce the numeric measurements.
- 2026-06-06 two-temp follow-up sweeps: `aex-two-temp` with
  `bilinear-fixed5` is almost neutral (`0.8529/1.1555/1.1822`). Anchor sweep
  keeps OpenCV default best (`opencv 0.8531/1.1555/1.1870`; `floor-left`
  worsens to `0.8531/1.2134/2.1904`; `origin/end` are strongly negative).
  Border sweep is mixed (`mirror 0.8531/1.1555/1.1870`, `reflect
  0.8531/1.1558/1.1818`). So the next exactness target is still
  `warpAffine` destination/canvas or pre/post ray placement, not `boxFilter`
  anchor/border or simple ROI aliasing.
- 2026-06-06 final ROI shift probe: added `aex-two-temp-final-{xm,xp,ym,yp}`
  diagnostics. All one-pixel final-copy shifts are negative:
  baseline `0.8531/1.1555/1.1870`; `x-1 1.1336/1.3811/6.1233`;
  `x+1 1.1276/1.3447/5.9795`; `y-1 1.1166/1.3516/5.9944`;
  `y+1 1.1166/1.3708/6.0968`. This clears the last `R12` -> final ray ROI
  position as the main residual source and points to exact forward/rotate-back
  `warpAffine` behavior or matrix center/scale details.
- 2026-06-06 two-temp direct rotate-back probe: added
  `--warp-mode aex-two-temp-direct-back` and
  `refs/scripts/smoke_olmkirakira_cpp_two_temp_direct_back_probe_cli.py`.
  It keeps the centered ROI -> `R14`, forward warp, and `R14 -> R12` box blur
  choreography, but writes the rotate-back warp directly into the final ray
  descriptor size. It is strongly negative: baseline `aex-two-temp`
  `0.8506/1.1570/1.0563`, direct-back `10.9852/11.6630/50.6637`.
  Therefore the final descriptor/dsize evidence cannot be modeled as a naive
  direct final-size rotate-back with the rotated temp center; keep the current
  temp rotate-back + centered copy model until a tighter asm argument mapping
  explains the dsize relationship.
- 2026-06-06 center-minus-half probe: added
  `aex-two-temp-center-minus-half`, which subtracts 0.5 from the two-temp
  forward/rotate-back matrix center. It is mixed and not adoptable:
  `case_0001 mean=0.8266` improves over `aex-two-temp` `0.8531`, but
  `case_0002 mean=1.1637` and `case_0003 mean=1.7709` worsen from
  `1.1555/1.1870`. Keep this as a red diagnostic only.
- 2026-06-06 caller temp-Mat mapping: `FUN_18114f4a0` actually creates two
  same-sized PF-backed temp descriptors (`[rbp+0x190]` and `[rbp+0x120]`),
  copy-constructs them into `[rbp+0xc0]` and `[rbp+0x60]`, and zeros the copied
  Mat data pointers before calling `FUN_181150790`. The call passes
  `RDX=[rbp]`, `R8=[rbp+0xc0]`, `R9=current ray descriptor`, and stack
  `[rsp+0x20]=[rbp+0x60]`; Ghidra decomp hides part of this stack-arg shape.
  Inside the helper, the first temp (`R14`) is filled from a centered ROI and
  forward-warped in place; the second temp (`R12`) is the blur/output and
  rotate-back canvas, then a centered ROI is copied into the final ray
  descriptor (`param_4`). Also confirmed `FUN_181156b90` is a `cv::Mat`
  copy-constructor shape with refcount increment, while `FUN_181231b80` is the
  PF-backed Mat allocator. Next implementation work should model this two-temp
  zero-filled choreography instead of adding more one-temp warp guesses.
- A temporary CLI probe approximating OpenCV's 5-bit `INTER_LINEAR` table
  (`bilinear-fixed5`) did not improve the current refs:
  `case_0001 mean=0.8384`, `case_0002 mean=1.1624`,
  `case_0003 mean=1.7034`, versus baseline `0.8381/1.1623/1.7003`.
  The probe is now available as `--rotate-filter bilinear-fixed5` in the C++
  CLI and included in `smoke_olmkirakira_cpp_rotate_filter_probe_cli.py`, but
  remains diagnostic-only. Interpolation-table quantization alone is not the
  missing KiraKira piece.

2026-06-05 KiraKira C++ warp-canvas probes:

- Added diagnostic `--rotate-size-mode aex-min4` to
  `cli/OLMKiraKira/main.cpp`. This mirrors the `FUN_18114f4a0` canvas formula
  visible at `18114f78b..18114f7f5`:
  `int(w*abs(cos)+h*abs(sin)+0.5)` / `int(w*abs(sin)+h*abs(cos)+0.5)`,
  clamped to at least `w+4` / `h+4`.
- `aex-min4` is identical to the current default on the current refs:
  `case_0001 max=22 mean=0.8381`,
  `case_0002 max=24 mean=1.1623`,
  `case_0003 max=60 mean=1.7003`.
- Added diagnostic `--axis-fast-path true|false`. Default remains `true`.
  `false` forces 0/90-degree rays through the rotate/crop path too, matching
  the high-level `FUN_181150790` call shape more closely, but it is not a
  global improvement:
  - `--axis-fast-path false --rotate-size-mode aex-min4`:
    `case_0001 mean=0.8354`, `case_0002 mean=1.1847`,
    `case_0003 mean=2.0123`.
  - `--axis-fast-path false` with default round size:
    `case_0001 mean=0.8381`, `case_0002 mean=1.1847`,
    `case_0003 mean=2.1189`.
- Keep the default axis fast path for now. The tiny case1-only improvement is
  outweighed by regressions on case2/case3, so this is diagnostic evidence
  rather than a Mac-port change.

2026-06-06 KiraKira C++ two-temp/no-fastpath probe:

- Added `refs/scripts/smoke_olmkirakira_cpp_two_temp_no_fastpath_probe_cli.py`
  and registered it as a red measurement in `smoke_all_algorithm_clis.py`.
- Important distinction: the earlier `--axis-fast-path false` result above was
  measured on the older/default warp path. Under the corrected
  `--warp-mode aex-two-temp` choreography, forcing 0/90-degree rays through the
  same temp warp/box/warp path gives `case_0001 mean=0.8506`,
  `case_0002 mean=1.1570`, `case_0003 mean=1.0563`.
- This almost matches the Python OpenCV primitive probe
  `0.8504/1.1570/1.0514`, so the portable C++ sampler is close enough for this
  slice. The main KiraKira decision is now model selection: two-temp/no-fastpath
  is much better for Strength=0 case3, slightly worse for case1, and near-tie
  for case2. Do not flip the default blindly; instead use this as the next Mac
  candidate path and keep probing exact AEX conditions that choose/direct the
  fast path.
- Subagent ASM review found no evidence that AEX has a 0/90-degree fast path:
  the caller allocates/zeros the temp Mats and calls `FUN_181150790`, and the
  helper contains forward `warpAffine`, Blur Mode work, and rotate-back
  `warpAffine`. `Strength=0` does not appear to bypass the ray helper; Blur
  Mode=2 only changes the internal boxFilter stage.
- Added `--axis-fast-path-mode true|false|strength-nonzero` and
  `refs/scripts/smoke_olmkirakira_cpp_strength_fastpath_probe_cli.py` to test a
  Strength-gated shortcut hypothesis. With
  `--warp-mode aex-two-temp --axis-fast-path-mode strength-nonzero`, results are
  `case_0001 mean=0.8531`, `case_0002 mean=1.1555`,
  `case_0003 mean=1.0563`. This is useful as a case3 diagnostic, but the ASM
  evidence favors all-ray two-temp/no-fastpath over a Strength-specific fast
  path rule.
- Ported the all-ray two-temp/no-fastpath candidate to
  `mac/OLMKiraKira/OLMKiraKira.cpp`: the Mac plugin now uses centered temp-A
  ROI copy, in-place-style forward `getRotationMatrix2D` warp, horizontal
  REFLECT_101 box passes into temp-B, rotate-back, and centered final ROI copy
  for all four rays, including 0/90-degree rays. This mirrors the current
  best AEX-faithful C++ candidate, not the old direct-axis fast path.
- Verification: `xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj
  -configuration Debug build` succeeded; the built plugin is universal
  x86_64/arm64 and `codesign --verify` succeeds. C++ red probe
  `smoke_olmkirakira_cpp_two_temp_no_fastpath_probe_cli.py` still reports
  `0.8506/1.1570/1.0563`.

2026-06-06 KiraKira subagent ray-isolation request:

- ASM sidecar rechecked `FUN_181150790` and found the next unresolved
  questions are not another simple ROI shift: the helper returns a scalar in
  `XMM0` (`Blur Mode=2` path multiplies it by `length^2`) and the caller stores
  that per-ray scalar before passing the ray/scalar arrays into the vtable
  aggregation path.
- The same review flags angle/length table mapping as underdetermined by the
  current references: all three existing cases have `Vertical/Horizontal/
  Diagonal Length=50`, `Glow Rotation=0`, and no isolated Diagonal2 ray, so
  ray order, base angle, helper scalar, and aggregation argument semantics are
  entangled.
- Added `refs/reference_requests/kirakira_single_ray_20260606.json` for the
  next Windows pass. It asks for Vertical/Horizontal/Diagonal/Diagonal2
  single-ray cases at `Brightness Gain=1 / Strength=100`, the same four at
  `Brightness Gain=9.4 / Strength=0`, plus an optional `Glow Rotation=13`
  diagonal sanity case. Use these refs before deeper image-only tuning of
  KiraKira ray order or angle mapping.
- 2026-06-06 stop-condition review: existing probes already cover boxFilter
  kernel/anchor/normalize/border, rotate/warp canvas/crop/final ROI/direct-
  back/two-temp/no-fastpath/half-pixel variants, OpenCV same-destination
  aliasing, and broad composition/aggregation candidates. Current equal-ray,
  rotation-zero refs cannot isolate ray order, angle mapping, helper scalar /
  `length^2`, or single-ray crop behavior, so do not add more KiraKira
  image-diff toggles until the single-ray request is imported.

2026-06-05 RadialBlur C++ Inner scatter RGB probe:

- Fixed a latent C++ source-scatter probe wrap bug in
  `cli/OLMRadialBlur/main.cpp`: inner direction now uses positive modulo for
  `ai - offset`. Without this, large variable-offset rows such as
  `case_0012` can address before the polar row when the offset exceeds one
  angular revolution. The default non-source-scatter path is unchanged.
- Added diagnostic `--inner-scatter-rgb-mode straight|prepass-premul` plus
  `refs/scripts/smoke_olmradialblur_cpp_inner_scatter_rgb_probe_cli.py`.
  This tests the decomp reading that `FUN_180002780` writes
  `outRGBA = originalRGB * prepassAlpha, outA = prepassAlpha` before
  `FUN_1800024c0` scatters source cells.
- Results:
  - `straight`: `case_0011 max=255 mean=22.1632`,
    `case_0012 max=255 mean=16.6793`,
    `case_0013 max=255 mean=19.8113`.
  - `prepass-premul`: `case_0011 max=255 mean=25.2972`,
    `case_0012 max=255 mean=10.6222`,
    `case_0013 max=255 mean=21.2910`.
- Interpretation: prepass-premultiplied source RGB is relevant for the
  variable-offset Inner case (`0012`) but cannot be adopted alone because it
  worsens the fixed-offset Inner cases. The next useful RadialBlur Inner probe
  is likely the exact `FUN_180002780` source alpha/scale prepass and tail
  length/weight-index pairing, not a global RGB-mode switch.

2026-06-05 RadialBlur C++ dynamic-offset and source-scale probes:

- Added diagnostic `--dynamic-offset-mode current|aex-row|min-radius` plus
  `refs/scripts/smoke_olmradialblur_cpp_dynamic_offset_probe_cli.py`.
  This compares the existing row-index dynamic offset with the explicit
  `FUN_1800024c0` float form and a min-radius denominator variant.
- Results are identical for all three modes:
  `case_0011 max=255 mean=63.4207`,
  `case_0012 max=255 mean=15.4790`,
  `case_0013 max=255 mean=20.0603`.
  Dynamic-offset denominator choice is therefore not exposed as the current
  Inner residual in these references.
- Added diagnostic `--inner-source-scale-mode one|alpha|inv-alpha` plus
  `refs/scripts/smoke_olmradialblur_cpp_inner_source_scale_probe_cli.py`.
  This tests whether the source-scatter prepass should use a simple
  base-alpha-like multiplier instead of fixed `1.0`.
- Results:
  - `one`: `case_0011 mean=22.1632`,
    `case_0012 mean=16.6793`,
    `case_0013 mean=19.8113`.
  - `alpha`: `case_0011 mean=31.9445`,
    `case_0012 mean=20.5490`,
    `case_0013 mean=19.6004`.
  - `inv-alpha`: `case_0011 mean=46.2016`,
    `case_0012 mean=16.8535`,
    `case_0013 mean=21.3305`.
- Interpretation: a simple source-scale substitution is not the missing piece.
  `alpha` gives only a tiny `case_0013` improvement while badly regressing
  `0011/0012`. The remaining useful path is still an exact `FUN_180002780`
  prepass: two directional tail gathers, its own weight tables
  (`0x3a9f0/0x3b990`), and the resulting prepass alpha used by
  `FUN_1800024c0`.

2026-06-05 RadialBlur C++ Inner `FUN_180002780` tail-gather prepass probe:

- Added CLI-only diagnostics `--inner-prepass-mode simple|tail-gather`,
  `--inner-prepass-span-mode strength|offset|edge-fade`, and
  `--inner-prepass-weight-mode row-span|aex-alpha`, exercised by
  `refs/scripts/smoke_olmradialblur_cpp_inner_prepass_mode_probe_cli.py`.
  Defaults remain `simple`/`strength`; no Mac plugin behavior changed.
- This approximates the decompiled `FUN_180002780` prepass as two directional
  tail gathers using the existing gaussian table shape, then feeds the
  resulting prepass alpha into the source-scatter path. The `aex-alpha`
  variant additionally models the decompiled
  `span=int(strength*baseAlpha)` / `weightIndex=int(offset/baseAlpha)` rule,
  currently using polar source alpha as a diagnostic stand-in for AEX's
  separate base/validity buffer.
- Results:
  - `simple/strength/row-span/straight`: `case_0011 mean=22.1632`,
    `case_0012 mean=16.6793`, `case_0013 mean=19.8113`.
  - `tail-gather/strength/row-span/straight`: `case_0011 mean=54.4721`,
    `case_0012 mean=15.8180`, `case_0013 mean=20.7905`.
  - `tail-gather/strength/aex-alpha/straight`: `case_0011 mean=60.4338`,
    `case_0012 mean=15.0235`, `case_0013 mean=20.1088`.
  - `tail-gather/offset/row-span/straight`: `case_0011 mean=22.1632`,
    `case_0012 mean=15.8180`, `case_0013 mean=20.4289`.
  - `tail-gather/edge-fade/row-span/straight`: `case_0011 mean=22.1632`,
    `case_0012 mean=16.6793`, `case_0013 mean=19.8113`.
  - `tail-gather/offset/row-span/prepass-premul`: `case_0011 mean=25.2972`,
    `case_0012 mean=12.6044`, `case_0013 mean=22.3763`.
  - `tail-gather/strength/aex-alpha/prepass-premul`: `case_0011 mean=88.4305`,
    `case_0012 mean=11.7905`, `case_0013 mean=22.1197`.
  - `tail-gather/edge-fade/row-span/prepass-premul`: `case_0011 mean=25.2972`,
    `case_0012 mean=10.6222`, `case_0013 mean=21.2910`.
- Interpretation: the tail-gather/prepass shape is relevant mainly to the
  variable-offset Inner reference (`case_0012`), especially when paired with
  prepass-premultiplied RGB. It is not a globally valid switch: fixed-offset
  Inner cases regress, and `edge-fade/straight` is a no-op because these
  references have Edge Fade = 0. The `aex-alpha` probe is informative but
  negative as currently wired: it improves `case_0012`/`0013` slightly while
  destroying `case_0011`, so AEX's `baseAlpha` buffer is not simply the polar
  source alpha. The next high-value RadialBlur Inner task is exact mapping of
  the `FUN_180002780` `param_4` base/validity buffer and the coupling between
  `FUN_180002780` output RGBA and `FUN_180001c90`/`FUN_1800024c0` scatter
  denominator/max-alpha behavior.

2026-06-05 RadialBlur C++ Inner source-seed probe:

- Decomp mapping around `FUN_180004640` now identifies the relevant polar
  buffers:
  - `param_1+0xe` = sampled polar input RGBA / final normalized output RGBA.
  - `param_1+0x10` = sampled prepass-alpha buffer passed to
    `FUN_1800024c0` as `param_4`.
  - `param_1+0x12` = `FUN_180002780` prepass alpha output / source alpha for
    `FUN_1800024c0`.
  - `param_1+0x14` = base/validity alpha sampled as `1.0` when the
    `param_2+0x44` flag is false, otherwise sampled from `param_2[0x11]`.
  - `param_1+0xf250` = scatter RGB/denominator accumulation buffer.
  - `param_1+0xf252` = final alpha/max-alpha buffer.
- 2026-06-06 subagent ASM/caller audit reconfirmed the call order:
  `FUN_180002780(+0xe,+0x12,+0x14,...,+0xf250,+0xf252)` runs before
  `FUN_1800024c0(+0xe,+0x12,+0x10,validity,...,+0xf250,+0xf252)`. Therefore
  prepass uses `+0x14` as its factor, while scatter uses the prepass-updated
  `+0x12` as contribution alpha and the separately sampled `+0x10` as
  span/gate `param_10`.
- The C++ CLI now wires `--inner-scatter-span-scale-mode source-alpha|input-alpha`
  into `effective_span = int(span * param10)` when no explicit
  `--inner-scatter-param10-plane` override is selected. Re-running
  `refs/scripts/smoke_olmradialblur_cpp_inner_aex_split_probe_cli.py` preserves
  the current red matrix: direct sampled-alpha span/gate helps only isolated
  old-inner cases and regresses Edge Fade, so it remains diagnostic evidence
  rather than an adoptable fix.
- If `+0x14` becomes decisive, request Windows Rotation Inner refs with
  Size Variation / variation-layer factor enabled. Current refs mostly expose
  the constant-1 `+0x14` branch.
- Added diagnostic `--inner-scatter-seed-mode source|none`.
  `source` is the previous heuristic, while `none` tests the literal reading
  that `FUN_1800024c0` only scatters tails via `FUN_180001c90` and does not
  seed the source sample into `0xf250/0xf252`.
- New `seed=none` results:
  - `tail-gather/strength/row-span/prepass-premul/none`:
    `case_0011 mean=95.2980`, `case_0012 mean=14.5244`,
    `case_0013 mean=22.9356`.
  - `tail-gather/strength/aex-alpha/prepass-premul/none`:
    `case_0011 mean=92.2924`, `case_0012 mean=13.4839`,
    `case_0013 mean=22.3592`.
  - `tail-gather/edge-fade/row-span/prepass-premul/none`:
    `case_0011 mean=25.4927`, `case_0012 mean=11.0549`,
    `case_0013 mean=21.3756`.
- Interpretation: removing source seeding is negative overall. It can move
  `case_0012` toward the reference in some variants, but badly increases
  fixed-offset `case_0011` and alpha coverage (`nz`) across cases. The raw
  AEX tail-only observation is therefore not enough by itself; exact behavior
  still depends on how `FUN_180002780`, `0xf250` denominator accumulation, and
  `0xf252` max-alpha are initialized/normalized together. The next RadialBlur
  Inner target should be the final normalization loop (`0xf250 / 0xf252`) and
  the `param_1+0x10` sampled prepass-alpha buffer, not another global seed
  switch.

2026-06-05 RadialBlur C++ Inner final-normalization probe:

- Added diagnostic `--inner-final-alpha-mode max|denom|source` and
  `--inner-rgb-denominator-mode accum|max`, exercised by
  `refs/scripts/smoke_olmradialblur_cpp_inner_final_norm_probe_cli.py`.
- The baseline `max/accum` corresponds to the current AEX reading:
  RGB is normalized by the `0xf250` alpha/denominator channel, while final
  alpha comes from the separate `0xf252` max-alpha buffer.
- Results on the current best-ish source-scatter/prepass variant
  (`tail-gather/edge-fade/row-span/prepass-premul/source`):
  - `final-alpha=max rgb-denom=accum`: `case_0011 mean=25.2972`,
    `case_0012 mean=10.6222`, `case_0013 mean=21.2910`.
  - `final-alpha=denom rgb-denom=accum`: `case_0011 mean=40.4529`,
    `case_0012 mean=13.0741`, `case_0013 mean=21.2045`.
  - `final-alpha=source rgb-denom=accum`: `case_0011 mean=92.4061`,
    `case_0012 mean=13.3025`, `case_0013 mean=22.7382`.
  - `final-alpha=max rgb-denom=max`: `case_0011 mean=58.5261`,
    `case_0012 mean=16.8593`, `case_0013 mean=21.2904`.
- Interpretation: final normalization alternatives are negative. The current
  `0xf250.rgb / 0xf250.a` with final alpha from `0xf252` is still the best
  available model and matches the decomp structure. Remaining Inner residuals
  should be chased in the scatter input and weight paths: `param_1+0x10`
  sampled prepass-alpha, `FUN_180001c90`'s outer/inner table choices
  (`0x68` vs `0x1d528`), direction/index arithmetic, and the base/validity
  buffer used by `FUN_180002780`.

2026-06-05 RadialBlur C++ Inner seed-alpha split probe:

- Added diagnostic `--inner-seed-alpha-mode input|prepass`, exercised by
  `refs/scripts/smoke_olmradialblur_cpp_inner_seed_alpha_probe_cli.py`.
  This separates the `FUN_180002780` seed written to `0xf250`
  (`prepassAlpha * inputRGB`) from the `FUN_1800024c0` tail-scatter source RGB.
- Results on `tail-gather/strength/row-span`:
  - `seed-alpha=input scatter-rgb=straight`: `case_0011 mean=54.4721`,
    `case_0012 mean=15.8180`, `case_0013 mean=20.7905`.
  - `seed-alpha=prepass scatter-rgb=straight`: `case_0011 mean=57.3704`,
    `case_0012 mean=16.6466`, `case_0013 mean=20.9672`.
  - `seed-alpha=input scatter-rgb=prepass-premul`: `case_0011 mean=90.9893`,
    `case_0012 mean=12.6044`, `case_0013 mean=22.6296`.
  - `seed-alpha=prepass scatter-rgb=prepass-premul`: `case_0011 mean=95.0250`,
    `case_0012 mean=13.9110`, `case_0013 mean=22.8340`.
- Interpretation: seed/prepassAlpha separation is negative with the current
  prepass model. The AEX-like `prepass/straight` variant worsens all three
  Inner references, so the remaining error is probably not just the seed
  alpha source. `prepass-premul` still only helps the variable-offset case
  while destroying fixed-offset `case_0011`, so keep it diagnostic-only. Next
  useful work should inspect `FUN_180002780`'s alpha gather itself and
  `FUN_180001c90`'s table/index arithmetic rather than promoting any of these
  modes to the Mac plugin.

2026-06-05 RadialBlur C++ Inner scatter span-scale probe:

- Added diagnostic `--inner-scatter-span-scale-mode one|source-alpha|input-alpha`,
  exercised by `refs/scripts/smoke_olmradialblur_cpp_inner_span_scale_probe_cli.py`.
  This tests the `FUN_180001c90` pattern where `iVar10 = int(effective_span *
  param_10)` and `param_10` appears to come from the `param_1+0x10` sampled
  prepass-alpha buffer.
- Results on the current best-ish source-scatter/prepass variant
  (`tail-gather/edge-fade/row-span/prepass-premul/source`):
  - `scatter-span-scale=one`: `case_0011 mean=25.2972`,
    `case_0012 mean=10.6222`, `case_0013 mean=21.2910`.
  - `scatter-span-scale=source-alpha`: `case_0011 mean=29.8855`,
    `case_0012 mean=12.6410`, `case_0013 mean=21.2560`.
  - `scatter-span-scale=input-alpha`: `case_0011 mean=29.8855`,
    `case_0012 mean=12.6410`, `case_0013 mean=21.2560`.
- Interpretation: simple alpha scaling is negative for `case_0011/0012` and
  only marginally helps `case_0013`. Keep full span (`one`) as the current
  diagnostic baseline. If AEX really scales by `param_1+0x10`, the missing
  piece is the exact prepass-alpha buffer produced/sampled before
  `FUN_180001c90`, not a direct source/input alpha substitute.

2026-06-05 RadialBlur C++ Inner wrap probe:

- Added diagnostic `--inner-wrap-mode circular|aex-next-row`, exercised by
  `refs/scripts/smoke_olmradialblur_cpp_inner_wrap_probe_cli.py`. The decomp
  for `FUN_180001c90`'s inner branch appears to move a negative angle wrap to
  `param_5 + 1`; this probe compares that reading against the current same-row
  circular wrap.
- Results on the same current best-ish source-scatter/prepass variant:
  - `inner-wrap=circular`: `case_0011 mean=25.2972`,
    `case_0012 mean=10.6222`, `case_0013 mean=21.2910`.
  - `inner-wrap=aex-next-row`: `case_0011 mean=26.1534`,
    `case_0012 mean=10.6248`, `case_0013 mean=21.2910`.
- Interpretation: AEX-style next-row wrapping is negative/slightly worse for
  these references, so keep same-row circular wrap as the diagnostic baseline.
  The visible decomp pointer movement is likely an implementation/layout detail
  or only affects a boundary not represented by the current mismatch. Continue
  chasing exact `FUN_180002780` prepass-alpha generation/sampling and weight
  table construction.

2026-06-06 RadialBlur Inner scatter/prepass decomp refresh:

- Re-read `FUN_180001c90`, `FUN_1800024c0`, and `FUN_180002780`.
- `FUN_180001c90(param_2=0)` is the outer scatter: mode at `+0x24`, base
  length/offset at `+0x3a9e8`, table `+0x68`, angular index increments and
  wraps within the same radius row.
- `FUN_180001c90(param_2=1)` is the inner scatter: mode at `+0x2c`, base
  length/offset at `+0x3a9ec`, table `+0x1d528`, angular index decrements and
  the negative-wrap pointer advances to `(radius + 1) * angular_count`.
- Both directions apply mode `1 add dynamic offset`, mode `2 max(base,
  dynamic)`, mode `3 dynamic only`, clamp length to `3000`, then use
  `effective=int(length * param_10)` and table stride `30000/effective`.
- `FUN_1800024c0` calls outer first and inner second for each source cell.
  Dynamic offset is radius-row dependent:
  `int((radial_count / 2) * mode_value / radius_row)`.
- `FUN_180002780` prepass gathers alpha in both directions using separate
  tables `+0x3a9f0` and `+0x3b990`, normalizes by total prepass weight, then
  writes `out.rgb = gathered_alpha * input.rgb`, `out.a = gathered_alpha`.
- Current interpretation: the existing isolated probes are consistent with
  these pieces but no global switch closes the gap. The next useful probe
  should model the exact `param_1+0x10` sampled base/validity buffer and feed
  that into both `FUN_180002780` and `FUN_180001c90` table/index arithmetic,
  rather than trying more final-alpha or seed-mode toggles.

2026-06-06 RadialBlur C++ Inner scatter `param_10` plane probe:

- Added CLI-only diagnostic `--inner-scatter-param10-plane
  one|polar-alpha|prepass-alpha|factor`, exercised by
  `refs/scripts/smoke_olmradialblur_cpp_inner_param10_plane_probe_cli.py`.
  It replaces the old source/input-alpha span scaling inside the
  source-scatter/prepass branch with an explicit `param_10` plane selected
  immediately before `effective_span = int(span * param10)`.
- Fixed measurement baseline:
  `--inner-source-scatter-prepass --inner-prepass-mode tail-gather
  --inner-prepass-span-mode edge-fade --inner-prepass-weight-mode aex-alpha
  --inner-prepass-factor-mode one --inner-scatter-rgb-mode prepass-premul
  --inner-scatter-seed-mode source`.
- Old Inner (`20260604_olm/OLMRadialBlur` cases `0011/0012/0013`) results:
  - `one`: `25.2972 / 10.6222 / 21.2910`.
  - `polar-alpha`: `29.8855 / 12.6410 / 21.2560`.
  - `prepass-alpha`: `29.8855 / 12.6410 / 21.2560`.
  - `factor`: `25.2972 / 10.6222 / 21.2910`.
- Edge Fade (`20260605_extra/OLMRadialBlur_img2` cases `0024/0025/0027`)
  results:
  - `one`: `5.7833 / 4.7930 / 2.3520`.
  - `polar-alpha`: `6.5779 / 5.4893 / 2.8157`.
  - `prepass-alpha`: `7.2705 / 5.7969 / 2.7246`.
  - `factor`: `5.7833 / 4.7930 / 2.3520`.
- Interpretation: alpha-based `param_10` planes are negative with the current
  prepass model. They regress Old Inner `0011/0012` and all Edge Fade cases,
  with only tiny isolated `0013`/`0027` movements. Treat this as a red probe;
  keep `one`/`factor` as the current diagnostic baseline and continue chasing
  exact `param_1+0x10` / `+0x14` buffer construction instead of adopting
  direct alpha scaling.
- Follow-up ownership audit maps those decomp float-pointer offsets to concrete
  byte planes: `+0x38` is polar RGBA from `param_2[0x13]`, `+0x40` is the
  separately sampled scatter span/gate plane from `param_2[0x12]`, `+0x50` is
  factor from `param_2[0x11]` or constant `1.0`, and `+0x48` is the
  prepass-computed alpha written by `FUN_180002780`. So the alpha-param10
  regression should be read as: the AEX span/gate plane exists, but current
  substitutes for its sampler/layer value are wrong; do not keep cycling
  sampled-alpha toggles.
- All tracked old Inner and Edge Fade refs used by this probe have
  `Size Variation=0`, `Noise Variation=0`, and `Noise Layer=0`. Added
  `refs/reference_requests/radialblur_inner_size_variation_20260606.json` to
  request the nonzero Size Variation grid needed to identify `+0x40`; stop
  deeper `+0x40` tuning until that reference exists.

2026-06-06 RadialBlur C++ Inner conditional seed probe:

- Added CLI-only diagnostic `--inner-scatter-seed-mode edgefade-none`, exercised
  by `refs/scripts/smoke_olmradialblur_cpp_inner_conditional_seed_probe_cli.py`.
  It keeps the current source/self seed for fixed Inner references but uses the
  tail-only `none` seed path when either Edge Fade parameter is nonzero.
- Fixed measurement baseline:
  `--inner-source-scatter-prepass --inner-prepass-mode tail-gather
  --inner-prepass-span-mode edge-fade --inner-prepass-weight-mode aex-alpha
  --inner-prepass-factor-mode one --inner-scatter-rgb-mode prepass-premul`.
- Old Inner (`20260604_olm/OLMRadialBlur` cases `0011/0012/0013`) results:
  - `source`: `25.2972 / 10.6222 / 21.2910`.
  - `none`: `25.4927 / 11.0549 / 21.3756`.
  - `edgefade-none`: `25.2972 / 10.6222 / 21.2910`.
- Edge Fade (`20260605_extra/OLMRadialBlur_img2` cases `0024/0025/0027`)
  results:
  - `source`: `5.7833 / 4.7930 / 2.3520`.
  - `none`: `5.1129 / 3.9755 / 1.9204`.
  - `edgefade-none`: `5.1129 / 3.9755 / 1.9204`.
- Interpretation: this is the first simple conditional probe that improves all
  tracked Edge Fade means while preserving the fixed Inner baseline. However,
  `none`/`edgefade-none` greatly increase Edge Fade nonzero coverage, so treat
  it as a red diagnostic for conditional `FUN_180002780`/`FUN_1800024c0`
  writeback semantics rather than an adoptable fix. The next RadialBlur Inner
  task should inspect why Edge Fade prefers tail-only scatter while fixed Inner
  still needs a source/self seed, especially the caller-populated `+0x10`
  alpha plane and final `0xf250/0xf252` coverage coupling.
