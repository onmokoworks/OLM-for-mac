# OLM Port Progress Matrix

Updated: 2026-06-06

This is the parent-owned progress matrix for the OLM Tools Apple Silicon port.
Percentages are engineering estimates, not release claims. A plugin is only
100% when Windows-reference behavior is implemented, AE-free CLI gates pass,
the macOS AE plugin builds, and returned AE-host validation confirms the effect.

## Percent Snapshot

| Plugin | Estimate | Current proof | Main remaining risk | Best next action |
| --- | ---: | --- | --- | --- |
| ColorKeep | 80% | Synthetic CLI smoke is green; Mac project builds in aggregate. | No Windows OLM reference set for this helper. | Keep as support utility unless a real ColorKeep ref set appears. |
| OLMBlur | 88% | C++ CLI smoke is green: cases 1/2/4 exact, all 7 guarded; Mac project builds; AE pixel validation request/return verifier exists and is bundled into the Mac plug-in package. | Small max=1 residual on non-exact blur cases; returned AE-host PNG validation still pending. | Send the Mac package to AE host and use bundled OLMBlur pixel request as the first host validation target. |
| OLMColorKey | 72% | RGB cases 1-4 exact; Edge Thin case 7 exact, cases 5/6 guarded; Edge Blur cases 8/9 guarded; C++ and Rust CLIs pass; Mac project builds; AE pixel validation request is bundled for current covered cases. | Replace, multi-key, and non-RGB color-space behavior lack returned refs. | Use bundled ColorKey pixel request for AE-host covered-case validation; wait for `olmcolorkey_replace_colorspace_20260606` before promoting Replace/non-RGB behavior. |
| OLMToonDilate | 72% | Python and C++ cases 1-3 pass guarded residual gates; Mac project builds; AE pixel validation request is bundled for valid ToonDilate cases. | Boundary residual remains; case 4 belongs to RadialBlur. | Use bundled ToonDilate pixel request for AE-host validation; only revisit if host validation exposes larger drift. |
| OLMDistanceGradation | 79% | All 29 effect-bearing cases from `20260605_extra` pass guarded smokes: 12 basic, 16 extended non-blur, and Blur Mode case_0029; Mac project builds; basic 12-case AE pixel validation request is bundled for host validation. | Case_0029 is still a near-match, not exact; GPU/OpenCV path ambiguity possible. | Use bundled DistanceGradation basic pixel request for AE-host validation; tighten Blur Mode only with binary-backed OpenCV details. |
| OLMSmoother | 55% | Standalone v1 CLI exists; OLMSmoother2 `--force-version 1` matches v1 refs closely. | Standalone v1 classifier over-fires; v1 may be redundant if v2 compatibility is accepted. | Treat v1 as covered by v2 compatibility unless user requires a separate faithful v1 plugin. |
| OLMSmoother2 | 65% | Key paths cases 2-4 are green; gamma cases guarded; no-key case 1 improved to mean 0.1832; Mac project builds. | No-key residual cannot be separated by current idx0/plane-split probes. | Wait for `smoother2_no_key_grid_20260606` before more no-key tuning. |
| OLMDirectionalBlur | 40% | Python/C++ direct and rotated scaffolds exist; Mac project builds; red probes are registered. | Current opaque refs cannot separate render-context scale, premul, alpha ownership, and residual row/populate behavior. | Wait for `directionalblur_context_scale_20260606` unless a new ASM-only argument fact appears. |
| OLMRadialBlur | 55% | Zoom and tiny Rotation are green in Python/C++; Mac project builds; Inner diagnostics are registered. | Inner/Edge Fade and Size Variation coupling remain ambiguous; current Inner refs have Size Variation 0. | Wait for `radialblur_inner_size_variation_20260606` before promoting more Inner changes. |
| OLMKiraKira | 40% | Python/C++ two-temp all-ray candidate is measured; Mac project builds; red probes are registered. | Current refs have equal ray lengths and zero rotation, entangling ray order, scalar, crop, and angle behavior. | Wait for `kirakira_single_ray_20260606` before more equal-ray tuning. |

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
| `OLMDirectionalBlur` | Read-only explorer until refs return. | ASM/IR argument facts, stop-line review, smoke metrics. | PNG-only parameter fitting. |
| `OLMRadialBlur Inner` | Read-only explorer until Size Variation refs return. | Buffer ownership facts for `+0x40/+0x48/+0x50`, red metric map. | Promoting Inner heuristics from Size Variation 0 refs. |
| `OLMKiraKira` | Read-only explorer until single-ray refs return. | Facts around `FUN_181150790`, scalar aggregation, crop/canvas hypotheses. | More equal-ray sweeps without new evidence. |
| `OLMSmoother2` | Read-only explorer until no-key grid refs return. | v1-via-v2 status, no-key blocker audit, writeback/sample facts. | Standalone v1 rabbit holes unless explicitly required. |
| `OLMColorKey` | Read-only or bounded implementation after ColorKey refs return. | Replace/color-space coverage audit and per-case promotion plan. | Implementing Lab94/YUV/YCrCb replacement from black-key refs. |
| `OLMDistanceGradation` | Bounded worker candidate. | Promote one omitted existing-ref slice at a time. | Broad refactors without per-case gates. |
| `OLMBlur` / `OLMToonDilate` | Verification worker candidate. | Package/AE-validation prep and regression checks. | Spending RE time before host validation asks for it. |

Parent agent owns integration, implementation merges, smoke updates,
`notes/PORTING_BOARD.md`, commits, and deciding when to ask the user for new
Windows references.

## Current Pending Reference Requests

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
python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick
python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
```

If multiple returned requests arrive at once, process
`smoother2_no_key_grid_20260606` first. It is the most isolated current
algorithm blocker: v2 key/gamma paths are already guarded, no-key `case_0001`
is the remaining residual, and
`refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py` is ready to group the
returned grid by Smoothness and Smooth Range.
`refs/scripts/next_reference_actions.py` encodes this priority order and prints
the next request-specific smoke plus the parent/sub-agent action after imports.

For the first low-risk AE-host pixel validation target, package OLMBlur
standalone:

```sh
python3 scripts/package_ae_pixel_validation_request.py --preset olmblur --output /tmp/olm_ae_pixel_validation_olmblur.zip
```

`scripts/package_mac_plugins.sh` also embeds current covered-case requests at
`AE_PIXEL_VALIDATION/` in the Mac plug-in package manifest. Current bundled
pixel request presets are `olmblur`, `olmcolorkey`, `olmtoondilate`, and
`olmdistancegradation`.

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
bundle binary, embeds the four current `AE_PIXEL_VALIDATION` request zips, and
passes `scripts/verify_mac_plugin_package.py`.

2026-06-06 current handoff after adding DistanceGradation pixel validation and
AE-host package autodetect:

```sh
scripts/package_olm_handoff.sh --output /tmp/olm_port_handoff_20260606_current.zip
python3 scripts/verify_olm_handoff_package.py /tmp/olm_port_handoff_20260606_current.zip
```

The verified handoff contains the six pending Windows reference requests plus
the four bundled AE pixel validation requests:
`olmblur`, `olmcolorkey`, `olmtoondilate`, and `olmdistancegradation`.

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
