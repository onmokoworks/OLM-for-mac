# OLM Port Progress Matrix

Updated: 2026-06-18 (status correction below supersedes the 2026-06-06 snapshot)

> Historical only. Percentages and pending-request statements below are not a
> current roadmap. Use `notes/PORTING_ROADMAP.md`,
> `notes/CONFORMANCE_LEDGER.md`, and
> `refs/reports/pending_runtime_trace_packages.md`.

This is the parent-owned historical progress matrix for the OLM Tools Apple
Silicon port.

Current conformance tracking has moved to `notes/CONFORMANCE_LEDGER.md`.
Definitions live in `notes/AE_EXACT_CONFORMANCE.md`.

Do not read old percentages, `green`, or `complete-ish` language as completion
claims. The only completion status is `AE exact`: Mac AE output must match the
Windows AE Software reference with zero diff for the declared bit-depth profile.
`CLI exact`, `off-by-1 candidate`, and tolerance-gated smokes are intermediate
evidence only.

## 2026-06-17 status correction (read first)

2026-06-18 AE-host smoke update: After Effects 26.2.1x2 on macOS 15.7.2
successfully loaded, applied, and rendered one 64x64 PNG frame for all 10
macOS Debug plug-ins from the local MediaCore install. The host-smoke result is
`handoff/ae_host_validation_20260618/AE_VALIDATION_RESULT_minimal_load_apply_20260618.json`;
the packaged return
`handoff/ae_host_validation_20260618/olm_ae_host_validation_result_minimal_20260618.zip`
passes `scripts/verify_ae_host_return.py ... --require-all-pass`. This is a
host load/apply/render smoke, not the bundled per-reference pixel validation.
Fixes needed to reach this state:
move the backup plug-ins out of MediaCore to avoid duplicate effect scanning,
and align PiPL `AE_Effect_Version` with each plug-in's code `PF_VERSION`.
2026-06-18 install-safety follow-up: `scripts/install_mac_plugins_to_mediacore.sh`
now provides the preferred local install path. It requires AE to be closed by
default, backs up existing expected OLM bundles under MediaCore into ignored
`handoff/mac_plugin_backups/`, installs only the freshly packaged bundles, and
verifies exactly one installed bundle plus matching binary SHA-256 per plug-in.
It also supports
`scripts/install_mac_plugins_to_mediacore.sh --audit-only` to list duplicate or
missing expected OLM bundles currently visible under MediaCore before touching
the install.
`scripts/package_mac_plugins.sh` and `scripts/package_olm_handoff.sh` now point
operators to this script instead of relying only on manual copy.

2026-06-18 later local AE automation note: after the ColorKey pixel-validation
debug pass, `osascript ... DoScript` began timing out before writing even a
minimal `AE_PING.txt`. This reproduced after temporarily moving all local OLM
plug-ins out of MediaCore, so the immediate blocker is AE automation/session
stability, not a proven OLM-only load failure. The current MediaCore OLM bundles
were restored from freshly verified Debug builds, with the previous install
saved under `handoff/ae_plugin_installed_backup_20260618_043614/`. Treat bundled
AE pixel validation as deferred until AE ping is stable again.

AE pixel-validation harness fix from the same debug pass:
`scripts/ae_pixel_validation_render.jsx` now resolves params by exact
`matchName` before display name, skips null/no-value params, removes stale PNGs
before render, and requires the PNG mtime to be newer than the render start.
This prevents old half-rendered case PNGs from being counted as fresh success.

2026-06-18 non-hard tightening pass: use
`python3 refs/scripts/smoke_all_algorithm_clis.py --profile nonhard` to verify
the stable/non-hard gate set without spending time on the current hard
RadialBlur/KiraKira/DirectionalBlur diagnostics. The profile covers
ColorKeep, OLMBlur, OLMColorKey Python/C++/Rust plus Replace/color-space,
OLMToonDilate Python/C++, OLMDistanceGradation basic/extended/blur, and
OLMSmoother2 v1/key/gamma/no-key gates. It passed 22/22 checks after adding
expanded DistanceGradation AE pixel request packaging.

Two things changed since the 2026-06-06 snapshot below; treat the snapshot's
percentages and "wait for refs" stop-lines as superseded where they conflict.

**1. Correctness bar is AE exact, not subjective %.** The "% estimate" column
and tolerance-gated language below are retired. A released path is judged by
Mac AE render output against the Windows AE Software reference for the declared
bit depth. `exact(0)` in an AE-free CLI is strong intermediate evidence, not
final completion. `off-by-1` is not complete; it is a rounding/quantization
candidate that still needs evidence. CUDA/GPU renders are excluded from the
current exactness bar. "covered" in the reference status only means the
reference set is complete; it does NOT mean the port matches.

**2. Reference returns.** All listed request packages are now covered/imported:
DirectionalBlur, KiraKira, ColorKey Replace/color-space, RadialBlur Inner,
RadialBlur Inner Size Variation, and Smoother2 no-key grid. There are no
pending Windows reference requests at the moment; use
`refs/scripts/next_reference_actions.py` for the current post-import order.

Measured-bar results so far (software set, `max_diff`):

| Plugin / path | result |
| --- | --- |
| OLMColorKey RGB nonblack remove/keep | exact(0) |
| OLMColorKey LAB76 per-component | exact(0) |
| OLMColorKey LAB76 nonblack remove | exact(0) — FIXED 2026-06-14 (was max=255) |
| OLMColorKey HSV nonblack remove | exact(0) — IMPLEMENTED 2026-06-14 (per-space comparator) |
| OLMColorKey Lab94 nonblack + per-component | exact(0) — IMPLEMENTED 2026-06-14 (CIE94 comparator) |
| OLMColorKey YUV nonblack | exact(0) — IMPLEMENTED 2026-06-14 |
| OLMColorKey YCrCb nonblack | exact(0) — IMPLEMENTED 2026-06-14 |
| OLMColorKey ALL 6 color spaces | 9/9 returned color-space cases exact(0) |
| OLMColorKey edge-blur transparent rgb | near (max=8, 0.25% px) — separate edge-blur issue |
| OLMColorKey Replace (RGB/Lab76/two-key/dilate, keep+remove) | 5/5 replace-active cases exact(0) — IMPLEMENTED 2026-06-14. ctx+0x24=Color Keep; replace only paints in Keep mode |
| OLMColorKey edge-thin erode / edge-blur | FAIL (max 255/61) — pre-existing edge residuals, NOT replace; blockers in ASM_FACTS |
| OLMKiraKira single-ray | BT.709 seed and ray-helper stages now match Windows trace through box passes / rotate-back / final copy; `FUN_18114fd90` aggregation is grounded at center/up/right. 2026-06-25 compose audit rejects `0.60`, inverse-trace-inspired `0.5811/0.5436`, direct scale override, and premultiplied compose as global fixes. Remaining residual is merge-mode-1 compose/writeback or final quantization, not luma, boxFilter window, `FUN_181150790` helper choreography, fd90 aggregation, or a global compose-scale change. |
| OLMDirectionalBlur context-scale refs | fr24/fr30 and software/CUDA rows collapse to identical metrics; frame-rate scaling is rejected. Current residual is not fixed by straight RGB, binary alpha, denom-alpha rotate-back, plain rotate sampling, host callbacks, first-rotate validity, or the final `denom > 0` guard. |

2026-06-14 ColorKey LAB fix (landed, measured): the non-per-component keying
distance in `cli/OLMColorKey/main.cpp` averaged raw per-channel diffs without the
per-channel `comp_scale` normalization that the per-component path uses, so for
LAB76 the [0,1] `Threshold` never matched LAB-magnitude distances (nothing keyed
-> input passed through, max=255). Fixed by dividing each channel diff by
`comp_scale[c]` in the mean (RGB `comp_scale=1` so RGB stays exact; per-component
LAB already exact confirmed `comp_scale` is the right normalizer). Result:
`ck_lab76_nonblack_remove_cyan` max=255 -> 0. No regression: RGB/per-component
exact, edge-thin (case5/6) and edge-blur (case8/9) gated smokes still ok=2/2.

2026-06-17 ColorKey Mac/Rust parity follow-up: the exact C++ HSV/Lab94/YUV/YCrCb
converters/comparators were promoted into `mac/OLMColorKey/OLMColorKey.cpp` and
`rust/olmcolorkey_cli/src/main.rs`. Rust now matches the returned software and
CUDA ColorKey Replace/color-space cases exact(0) across 24 checked frames, and
the Mac project builds. Remaining ColorKey work is AE-host validation plus the
separate Edge Thin erode / Edge Blur residuals.

---

Original 2026-06-06 snapshot follows. Percentages are engineering estimates, not
release claims, and are retained for history only.

## Archived Legacy Status Snapshot

The table below is retained only as historical context. Do not use the
percentage estimates as current status.

| Plugin | Legacy note | Current proof | Main remaining risk | Best next action |
| --- | ---: | --- | --- | --- |
| ColorKeep | 80% | Synthetic CLI smoke is green; Mac project builds in aggregate. | No Windows OLM reference set for this helper. | Keep as support utility unless a real ColorKeep ref set appears. |
| OLMBlur | 88% | C++ CLI smoke is green: cases 1/2/4 exact, all 7 guarded; Mac project builds; AE pixel validation request/return verifier exists and is bundled into the Mac plug-in package. | Small max=1 residual on non-exact blur cases; returned AE-host PNG validation still pending. | Send the Mac package to AE host and use bundled OLMBlur pixel request as the first host validation target. |
| OLMColorKey | 86% | RGB cases 1-4 exact; returned Replace/color-space set shows C++ exact for simple Replace and all 6 color spaces; Mac plug-in implements Replace plus HSV/Lab94/YUV/YCrCb comparator parity and builds; Rust CLI matches the returned 24 software/CUDA ColorKey frames exact(0); Edge Thin/Blur guarded gates pass. | AE-host validation is pending; Edge Thin erode and Edge Blur residuals need separate binary-backed work; 16/32-bit host color-space parity is build-covered but not PNG-validated. | Package/return AE-host validation for ColorKey, or deep-dive the known Edge Thin/Edge Blur residuals with decomp evidence. |
| OLMToonDilate | 72% | Python and C++ cases 1-3 pass guarded residual gates; Mac project builds; AE pixel validation request is bundled for valid ToonDilate cases. | Boundary residual remains; case 4 belongs to RadialBlur. | Use bundled ToonDilate pixel request for AE-host validation; only revisit if host validation exposes larger drift. |
| OLMDistanceGradation | 79% | All 29 effect-bearing cases from `20260605_extra` pass guarded smokes: 12 basic, 16 extended non-blur, and Blur Mode case_0029; Mac project builds; basic 12-case AE pixel validation request is bundled for host validation. | Case_0029 is still a near-match, not exact; GPU/OpenCV path ambiguity possible. | Use bundled DistanceGradation basic pixel request for AE-host validation; tighten Blur Mode only with binary-backed OpenCV details. |
| OLMSmoother | 55% | Standalone v1 CLI exists; OLMSmoother2 `--force-version 1` matches v1 refs closely. | Standalone v1 classifier over-fires; v1 may be redundant if v2 compatibility is accepted. | Treat v1 as covered by v2 compatibility unless user requires a separate faithful v1 plugin. |
| OLMSmoother2 | 78% | No-key grid is near-exact across Smooth Range 1/2/3 (`max<=9`, tiny nz); key paths and gamma cases pass guarded gates; v1 refs are covered by `--force-version 1`; Mac project builds. | Older mixed 20260605 cases remain non-exact under strict thresholds, and AE-host validation is still pending. | Treat no-key as solved to current reference precision; keep guarded regression gates and move Smoother2 toward AE-host validation/integration. |
| OLMDirectionalBlur | 45% | Python/C++ direct and rotated scaffolds exist; Mac project builds; context-scale refs are covered; gaussian divisor is binary-confirmed; returned refs reject frame-rate scaling and obvious alpha/RGB toggles; first `FUN_180001ec0` invalid handling, 8bpc host callbacks, rowdriver ownership, and final `denom > 0` guard are mirrored. | Residual is beyond the broad toggles already tested; needs a new concrete binary fact before more PNG tuning. | Park unless a fresh Ghidra/objdump fact appears; spend active Ghidra time on RadialBlur/KiraKira. |
| OLMRadialBlur | 66% | Zoom and tiny Rotation are green in Python/C++; Mac project builds; Inner and Size Variation refs are covered; Ghidra confirms max/denom writeback, Quality/5 span scaling, source-scatter/prepass ownership, AEX next-row inner wrap, Edge Fade prepass tables, 30000-entry Gaussian table constants, and float-oriented grid ownership; the C++ CLI now defaults Inner through that AEX-backed path; scatter stats show span-minus-one removes exactly one write per active source. Ghidra DB labels now name `FUN_180001c90` as `RadialBlur_scatter_tail_by_direction` and `FUN_1800024c0` as `RadialBlur_scatter_valid_polar_cells`. | Full Inner still has nontrivial residuals; `--inner-scatter-span-minus-one` improves low-span/Quality together but loop-only/table-only/scatter-population probes do not justify default promotion because the helper itself does not visibly subtract one. AEX-style float Gaussian and float grid diagnostics barely move metrics, so neither table nor broad coordinate precision drift is the main residual. | No new Windows refs needed now. Next binary action is the runtime trace documented in `notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md`: on `rb_inner_only_strength_small`, break at `OLMRadialBlur.aex+0x26e5`, step into `+0x1c90`, and prove whether effective span becomes `32` or `31`; promote nothing until that fact is known. Then inspect exact sampler validity or helper state ownership rather than Gaussian/grid precision. |
| OLMKiraKira | 48% | Python/C++ two-temp all-ray candidate is measured; Mac project builds; returned single-ray refs close broad ray-order/scalar/compose ambiguity; strength0 brightness scale is near/exact; fixed1024/u16/opencvtab rotate-filter diagnostics reject simple coordinate quantization and simple coefficient-table rounding as the missing piece. Later BT.709 trace work grounds the seed, OpenCV helper stages, and `FUN_18114fd90` aggregation at representative points. The 2026-06-25 compose audit rejects global gain/premul shortcuts. | Remaining residual is now localized after aggregation: merge-mode-1 compose/writeback, channel-dependent attenuation, or final quantization/export behavior. A global compose scale tweak is rejected by Software-set metrics. | Do not reopen luma, boxFilter, ray-helper choreography, fd90, or broad ray toggles. Next Windows proof, if needed, should hit the internal compose/prewriteback site; Mac-side work should focus on extracting that site from asm/static traces rather than broad PNG fitting. |

## Overall Estimate

The port is roughly 62% complete as an AE-free, Mac-buildable migration effort:

- All 10 macOS plugin projects build in aggregate.
- Green CLI gates cover the simpler or partially isolated behavior.
- Hard paths now have registered red diagnostics instead of invisible failure.
- Six targeted Windows reference requests are pending for non-guesswork
  promotion of the remaining difficult paths.

It is not release-complete because AE-host validation is still absent and the
hard procedural effects remain partially scaffolded.

## Parallelization Policy

Use subagents aggressively, but with narrow ownership:

Reusable dispatch prompts and parent/child handoff rules are in
`notes/PARALLEL_AGENT_RUNBOOK.md`.

| Agent slice | Mode | Allowed output | Avoid |
| --- | --- | --- | --- |
| `OLMDirectionalBlur` | Ghidra/objdump explorer. | `FUN_180001000`, rowdriver scatter, final-normalization facts, stop-line review, smoke metrics. | PNG-only parameter fitting or broad alpha/RGB/host-callback/first-rotate toggles already rejected or mirrored by current facts. |
| `OLMRadialBlur Inner` | Implement bounded C++ CLI changes only when backed by covered refs and Ghidra facts. | Buffer ownership facts for `+0x40/+0x48/+0x50`, covered Size Variation refs, red metric map. | Promoting Inner heuristics that improve one request while regressing Edge Fade/full Inner. |
| `OLMKiraKira` | Bounded compose/writeback implementation/audit. | BT.709 seed, OpenCV helper stages, `FUN_18114fd90` aggregation, compose inversion metrics, single-ray smoke metrics. | More luma/boxFilter/ray-helper/global-scale sweeps; trace evidence already separates those. |
| `OLMSmoother2` | AE-host/Mac integration validation. | v1-via-v2 status, no-key grid near-exact metrics, writeback/sample facts. | More no-key PNG tuning unless host validation exposes a fresh mismatch. |
| `OLMColorKey` | Read-only or bounded implementation after ColorKey refs return. | Replace/color-space coverage audit and per-case promotion plan. | Implementing Lab94/YUV/YCrCb replacement from black-key refs. |
| `OLMDistanceGradation` | Bounded worker candidate. | Promote one omitted existing-ref slice at a time. | Broad refactors without per-case gates. |
| `OLMBlur` / `OLMToonDilate` | Verification worker candidate. | Package/AE-validation prep and regression checks. | Spending RE time before host validation asks for it. |

Parent agent owns integration, implementation merges, smoke updates,
`notes/PORTING_BOARD.md`, commits, and deciding when to ask the user for new
Windows references.

## Current Pending Reference Requests

(2026-06-17: all listed requests are now covered/imported, including the
RadialBlur Inner software recaptures. This section is kept as historical
workflow context; use `refs/scripts/next_reference_actions.py` for the current
post-import action order.)

- `directionalblur_context_scale_20260606`
- `kirakira_single_ray_20260606`
- `olmcolorkey_replace_colorspace_20260606`
- `radialblur_inner_20260605`
- `radialblur_inner_size_variation_20260606`
- `smoother2_no_key_grid_20260606`

Run:

```sh
python3 scripts/print_current_handoff.py
python3 refs/scripts/check_reference_request_status.py
python3 refs/scripts/next_reference_actions.py
python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending_20260606.zip
```

When returned refs are imported, run the relevant request smoke first, then the
quick aggregate:

```sh
python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick --dispatch-dir /tmp/olm_reference_dispatch
python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick --dispatch-dir /tmp/olm_reference_dispatch
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
```

The no-key grid has since been measured and is near-exact to current Windows
reference precision (`max<=9`, very sparse changed pixels). Do not process it
as the next algorithm blocker unless new AE-host validation contradicts that
status. `refs/scripts/next_reference_actions.py` now prioritizes the remaining
post-import action order and prints the next request-specific smoke plus the
parent/sub-agent action. With `--dispatch-dir`, it also writes per-request
`SUBAGENT.md` files for the covered and still-pending actions.

For the first low-risk AE-host pixel validation target, package OLMBlur
standalone:

```sh
python3 scripts/package_ae_pixel_validation_request.py --preset olmblur --output /tmp/olm_ae_pixel_validation_olmblur.zip
```

`scripts/package_mac_plugins.sh` also embeds current covered-case requests at
`AE_PIXEL_VALIDATION/` in the Mac plug-in package manifest. Current bundled
pixel request presets are `olmblur`, `olmcolorkey`, `olmtoondilate`,
`olmdistancegradation`, `olmdistancegradation_extended`, and
`olmdistancegradation_blur`. The extra DistanceGradation requests cover the
16 extended non-blur cases and Blur Mode `case_0029`, so AE-host pixel
validation now mirrors the CLI coverage instead of only the basic 12-case slice.

After the AE host returns rendered PNGs, verify them against the packaged
Windows expected frames:

```sh
python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass
python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass --require-all-pixel-requests
python3 scripts/verify_ae_host_return.py /tmp/olm_port_handoff_20260606_current.zip path/to/returned_ae_host.zip --require-all-pass
python3 scripts/verify_ae_host_return.py /tmp/olm_port_handoff_20260606_current.zip path/to/returned_ae_host.zip --require-all-pass --require-all-pixel-requests
python3 scripts/verify_ae_pixel_validation_result.py /tmp/olm_ae_pixel_validation_olmblur.zip path/to/returned_ae_pngs_or_zip
```

Use `--require-all-pixel-requests` only when the AE host intentionally returned
all bundled pixel validation requests. For a first partial pass, omit it and the
verifier will check returned groups while reporting missing pixel groups as
`[SKIP]`.

2026-06-06 package verification:

```sh
scripts/package_mac_plugins.sh --skip-build --output /tmp/olm_mac_plugins_clean_20260606.zip
```

This used the already verified Debug build products to create a clean AE-host
handoff zip with no `__MACOSX`, `._*`, or `.DS_Store` entries. The package
contains all 10 macOS plug-ins, preserves executable zip metadata for each
bundle binary, embeds the current `AE_PIXEL_VALIDATION` request zips, and
passes `scripts/verify_mac_plugin_package.py`.

2026-06-06 current handoff after adding DistanceGradation pixel validation and
AE-host package autodetect:

```sh
scripts/package_olm_handoff.sh --output /tmp/olm_port_handoff_20260606_current.zip
python3 scripts/verify_olm_handoff_package.py /tmp/olm_port_handoff_20260606_current.zip
```

The verified handoff contains the runtime-trace/reference handoff material plus
the bundled AE pixel validation requests:
`olmblur`, `olmcolorkey`, `olmtoondilate`, `olmdistancegradation`,
`olmdistancegradation_extended`, and `olmdistancegradation_blur`.

Combined handoff:

```sh
scripts/package_olm_handoff.sh --output /tmp/olm_port_handoff_20260606.zip
```

This creates a single clean zip containing
`olm_reference_requests_pending.zip`, `olm_mac_plugins_Debug_clean.zip`, a
README, and a manifest. The script verifies the nested Mac plug-in package and
the top-level handoff with `scripts/verify_olm_handoff_package.py`.

## 2026-06-06 Parallel Audit Results

Consolidated stop lines and post-reference actions are tracked in
`notes/PARALLEL_IR_AUDIT_20260606.md`.

- `OLMKiraKira` / Franklin: current C++ default smoke remains a red/probe path
  around `case_0001 mean=0.8381`, `case_0002 mean=1.1623`,
  `case_0003 mean=1.7003`; all-ray two-temp/no-fastpath is
  `0.8506/1.1570/1.0563`. The asm-backed primitive details
  (`ksize=(length,1)`, OpenCV anchor, `BORDER_REFLECT_101`) are already folded
  into the candidate, but the equal-ray, zero-rotation refs cannot isolate ray
  order, helper scalar, or single-ray crop. Stop implementation promotion until
  `kirakira_single_ray_20260606` is imported.
- `OLMDirectionalBlur` / Boyle: `rotated-aex-exact-rowdriver` exactly matches
  `exact-scatter-helper` at `case_0001 mean=4.4392`,
  `case_0005 mean=1.1761`, while `rotated-aex-full-choreo` is still around
  `4.4483/1.1703`. Current refs cannot separate the render context scale read
  from `ctx+0x11c/ctx+0x120`, straight/premultiplied source RGB, and alpha
  side-channel behavior. Stop implementation tuning until
  `directionalblur_context_scale_20260606` is imported.
- `OLMRadialBlur` / Faraday: ASM ownership for the Inner/EdgeFade buffers is
  strong (`+0x38` polar RGBA, `+0x40` scatter span/gate, `+0x48` prepass
  alpha, `+0x50` prepass factor). Current C++ Inner source-scatter/prepass is
  still red at `case_0011/0012/0013 mean=25.2972/10.6222/21.2910`; EdgeFade
  seed removal improves to `5.1129/3.9755/1.9204` but conflicts with older
  Inner coverage. Existing refs have `Size Variation=0`, so they cannot
  identify real `+0x40` or Size Variation behavior. Stop tuning until
  `radialblur_inner_size_variation_20260606` is imported.
- `OLMSmoother` / Ampere: standalone v1 remains red, but
  `OLMSmoother2 --force-version 1` covers current v1 refs at
  `case_0001/0002/0003 mean=0.0055/0.0051/0.0200`, so standalone v1 should
  stay low priority unless AE-host testing rejects the compatibility route.
  v2 key paths are guarded (`case_0002 mean=0.0216`, `case_0003 exact`,
  `case_0004 mean=0.0189`), while no-key `case_0001 mean=0.1832` should not be
  tuned further until `smoother2_no_key_grid_20260606` is imported.
- `OLMColorKey` / Kepler: current refs cover only `Enable Replace=0`, one
  enabled key color, RGB exact paths, Edge Thin, and exploratory Lab76 Edge
  Blur. C++ and Rust explicitly reject Replace, and Mac reads `enable_replace`
  without applying replace colors. HSV/Lab94/YUV/YCrCb are not distinguishable
  from current black-key refs. Stop Replace/non-RGB promotion until
  `olmcolorkey_replace_colorspace_20260606` is imported, then run the dedicated
  request smoke and manifest audit.
