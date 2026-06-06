# OLM Port Sub-Agent Assignments

This note records the parent/child split for parallel OLM porting work.
Sub-agents are useful for read-only objdump/Ghidra/decomp/PNG-reference audits;
the parent agent owns implementation, verification gates, documentation
integration, and commits.

Reusable dispatch prompts for new agents live in
`notes/PARALLEL_AGENT_RUNBOOK.md`.

## Operating Rules

- Parent agent keeps the canonical status in `notes/PORTING_BOARD.md` and
  plugin-specific IR/ASM notes.
- Sub-agents should not edit implementation files unless the parent explicitly
  grants a disjoint write scope.
- Sub-agent findings must cite the files, commands, or reference requests that
  support them.
- Do not deep-tune from PNG residuals alone. If the next discriminating evidence
  is a Windows AE reference request, stop that plugin and ask for that package.
- Returned findings should be folded back into an IR or ASM facts note before
  implementation changes are promoted.

## Active 2026-06-06 Parallel Audit

| Plugin area | Agent | Scope | Expected output |
| --- | --- | --- | --- |
| `OLMDirectionalBlur` | `019e99be-1aad-7392-81a8-7aceed96535b` / Tesla | Read `notes/IR_OLMDirectionalBlur.md`, `notes/OLMDirectionalBlur_ASM_FACTS.md`, current C++/Python probes, decomp/disasm as needed. | IR checkpoints, measured status, stop condition, one non-guesswork next action. |
| `OLMRadialBlur` | `019e99be-41c0-7960-be4f-e9eb65d10a27` / Anscombe | Read `notes/OLMRadialBlur_RE.md`, C++/Python probes, Inner/EdgeFade refs and request JSON, decomp/disasm as needed. | Green vs red slices, Zoom/Rotation/Inner/EdgeFade IR facts, stop condition, one next action. |
| `OLMKiraKira` | `019e99be-59f1-7710-b08d-ed4963911ab1` / Goodall | Read `notes/OLMKiraKira_ASM_FACTS.md`, current C++/Python/OpenCV probes, single-ray request, decomp/disasm as needed. | Two-temp/all-ray facts, measured status, stop condition, one next action. |
| `OLMSmoother` / `OLMSmoother2` | `019e99be-719f-7171-b4a5-2e1cc1082dd9` / Schrodinger | Read `notes/OLMSmoother2_ASM_FACTS.md`, v1/v2 CLI and Mac bridge, no-key-grid request, Smoother refs. | Whether v1 is covered by v2 compatibility, measured status, no-key-grid unblocker, one next action. |

## Active 2026-06-06 Continuation Audit

The continuation pass reuses the same plug-in ownership model, but asks each
agent to decide whether any no-new-reference work remains worth doing before
the parent spends more implementation time.

| Plugin area | Agent | Scope | Expected output |
| --- | --- | --- | --- |
| `OLMDirectionalBlur` | `019e99d0-d239-7e91-a9ee-fda087e63c75` / Zeno | Read `notes/IR_OLMDirectionalBlur.md`, `notes/OLMDirectionalBlur_ASM_FACTS.md`, current probes, and `refs/reference_requests/directionalblur_context_scale_20260606.json`. | Current IR status, whether refs are sufficient, next action after refs arrive, any worthwhile no-ref action. |
| `OLMRadialBlur` | `019e99d0-ea50-7611-8d7c-2053e1e8232f` / Ohm | Read `notes/OLMRadialBlur_RE.md`, Inner/EdgeFade probes, and `refs/reference_requests/radialblur_inner_size_variation_20260606.json`. | Green/red slice map, whether Inner/EdgeFade refs are sufficient, next action after refs arrive, any worthwhile no-ref action. |
| `OLMKiraKira` | `019e99d0-ff94-7850-9e7e-8bd8bbc38202` / Pascal | Read `notes/OLMKiraKira_ASM_FACTS.md`, current two-temp/OpenCV probes, and `refs/reference_requests/kirakira_single_ray_20260606.json`. | Best candidate path, current residuals, next action after single-ray refs arrive, any worthwhile no-ref action. |
| `OLMSmoother` / `OLMSmoother2` | `019e99d1-17ec-7af3-9a6f-bf09e142d458` / Parfit | Read `notes/OLMSmoother2_ASM_FACTS.md`, v1/v2 CLI status, and `refs/reference_requests/smoother2_no_key_grid_20260606.json`. | v1 compatibility status, no-key v2 blocker, next action after grid refs arrive, any worthwhile no-ref action. |

## Current Stop Conditions

- `OLMDirectionalBlur`: wait for
  `refs/reference_requests/directionalblur_context_scale_20260606.json` if
  render-context scale / premul / alpha ownership cannot be separated from the
  current opaque references.
- `OLMRadialBlur`: wait for
  `refs/reference_requests/radialblur_inner_size_variation_20260606.json` if
  Inner `+0x40` span/gate plane and Size Variation coupling remain ambiguous.
- `OLMKiraKira`: wait for
  `refs/reference_requests/kirakira_single_ray_20260606.json` if equal-ray,
  rotation-zero references cannot isolate ray order, angle mapping, helper
  scalar, or crop/placement behavior.
- `OLMSmoother2`: wait for
  `refs/reference_requests/smoother2_no_key_grid_20260606.json` if no-key v2
  residual cannot be assigned to class-plane firing, sample-plane choice,
  color-space handling, or writeback.
- `OLMColorKey`: wait for
  `refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json` before
  promoting Replace, non-black HSV/Lab94/YUV/YCrCb, per-component Lab76/Lab94,
  or multi-key replacement behavior beyond the current RGB/Edge Thin/Edge Blur
  scaffolds.

## 2026-06-06 Focused Fact-Log Follow-Up

After the continuation audit, the parent kept implementation local and delegated
two disjoint note-only audits:

| Plugin area | Agent | Write scope | Result |
| --- | --- | --- | --- |
| `OLMKiraKira` scalar aggregation | `019e99e6-98d1-7823-a231-2e1152ccaeb4` / Sartre | `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md` | Added confirmed/ambiguous facts for `FUN_18114fd90`, `FUN_18114ffd0`, five-ray scalar setup, Brightness/Gain flow, and source/glow opacity ordering. |
| `OLMRadialBlur` sampler/writeback | `019e99e6-b0fb-7141-8fde-ae628a4a46d9` / Volta | `notes/OLMRadialBlur_ASM_FACTS.md` | Added sampler helper and plane ownership facts for `FUN_180001270`, `FUN_180001520`, `FUN_180001800`, `FUN_180001950`, `FUN_180002780`, and `FUN_1800024c0`. |

The parent also added `refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py`, a
green request smoke that skips while `smoother2_no_key_grid_20260606` is pending
and turns into grouped max/mean analysis when the Windows refs are imported.

## 2026-06-06 ColorKey Reference Gap Audit

| Plugin area | Agent | Scope | Result |
| --- | --- | --- | --- |
| `OLMColorKey` Replace/color-space gap | `019e99ea-9fed-7373-8c55-e85b44ac2929` / Darwin | Read current ColorKey notes, manifest audit, refs, Python/C++ CLI, and Mac plug-in source. | Confirmed current refs cover RGB exact, Edge Thin gated, and Edge Blur exploratory paths, but all current cases have `Enable Replace=0`, only key color 1 enabled, and insufficient non-black color-space coverage. Parent added `olmcolorkey_replace_colorspace_20260606.json`. |

## 2026-06-06 AE Host / Reference Workflow Audit

| Area | Agent | Scope | Result |
| --- | --- | --- | --- |
| Non-blocked next action | `019e9a49-3546-7571-a382-6c2a4824b8bf` / Fermat | Read progress board and green smoke coverage for support/low-risk plugins. | Recommended advancing AE-host pixel validation first, with OLMBlur as the lowest-risk target. Avoided more PNG-only tuning for currently stopped hard paths. |
| AE-host return flow | `019e9a49-4ae7-7e32-89ca-4c64e780baae` / James | Read package, handoff, and AE return verifier scripts. | Confirmed the one-shot return verifier is ready, then identified gaps: template filename handling, clearer returned pixel grouping docs, and a release-style `--require-all-pixel-requests` gate. Parent implemented those fixes. |
| Pending reference workflow | `019e9a49-5edc-7872-89af-972adad10a21` / Averroes | Read request JSONs, packaging/import scripts, and request smokes. | Confirmed all six pending requests are packageable/import-checkable. Recommended processing `smoother2_no_key_grid_20260606` first if multiple returned requests arrive, because it has the most isolated current blocker and a dedicated grid smoke. |

## Reusable Prompt Shape

Ask each sub-agent for:

1. Current best-supported algorithm IR checkpoints.
2. Exact measured status and the commands or notes that prove it.
3. Whether the stop condition still holds and which reference request unblocks
   it.
4. One next parent action that is backed by objdump/decomp/IR evidence.

## 2026-06-06 Third Parallel Stop-Line Audit

This pass was launched after adding `notes/PROGRESS_MATRIX.md`. It keeps all
agents read-only and asks whether there is any non-guesswork work left before
the pending Windows references arrive.

| Plugin area | Agent | Scope | Expected output |
| --- | --- | --- | --- |
| `OLMDirectionalBlur` | `019e99f3-c4e1-7521-a6f1-f006e9cb6a88` / Boyle | `notes/IR_OLMDirectionalBlur.md`, `notes/OLMDirectionalBlur_ASM_FACTS.md`, `refs/reference_requests/directionalblur_context_scale_20260606.json`, `cli/OLMDirectionalBlur/main.cpp`, directional smoke scripts. | Current metrics, whether existing refs can support non-guesswork implementation, one asm-backed next action or hard stop. |
| `OLMRadialBlur` Inner/EdgeFade | `019e99f3-dc5b-7780-84d0-fa5c6fbb6ced` / Faraday | `notes/OLMRadialBlur_RE.md`, `notes/OLMRadialBlur_ASM_FACTS.md`, RadialBlur Inner request JSONs, `cli/OLMRadialBlur/main.cpp`, Inner smoke scripts. | Green/red slice map, sufficiency of current refs for `+0x40/+0x48/+0x50`, one asm-backed next action or hard stop. |
| `OLMKiraKira` | `019e99f3-fd1d-7ac0-9620-f198c925d4d9` / Franklin | `notes/OLMKiraKira_ASM_FACTS.md`, `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md`, `refs/reference_requests/kirakira_single_ray_20260606.json`, Python/C++ KiraKira CLIs and smokes. | Best candidate path, current residuals, current-ref sufficiency, one asm-backed next action or hard stop. |
| `OLMSmoother` / `OLMSmoother2` | `019e99f4-16f0-7721-bf93-51382708f15b` / Ampere | `notes/OLMSmoother2_ASM_FACTS.md`, `refs/reference_requests/smoother2_no_key_grid_20260606.json`, Smoother CLIs and Mac port. | v1-via-v2 status, no-key blocker status, whether standalone v1 should stay low priority, one asm-backed next action or hard stop. |
| `OLMColorKey` | `019e99f4-346a-7eb2-811d-0230331167d0` / Kepler | ColorKey Replace/color-space request and smoke, manifest audit, C++/Rust/Mac ColorKey code. | Guarded behavior map, current-ref sufficiency for Replace/non-RGB, one reference-backed next action or hard stop. |

### Third Audit Results

All six active agents from this round were closed after returning final reports.
No implementation files were edited by sub-agents in this pass.

| Plugin area | Result | Parent action |
| --- | --- | --- |
| `OLMDirectionalBlur` | Current binary facts support the A/B buffer choreography, alpha-weighted rotate sampler, row prepass, scatter ownership, and `ctx+0x11c/0x120` render-scale read. Existing opaque refs cannot separate context scale, straight/premul source RGB, or alpha side-channel behavior. | Keep implementation stopped until `directionalblur_context_scale_20260606` is imported; then remeasure `rotated-aex-full-choreo` and `rotated-aex-exact-rowdriver` using manifest/context scale. |
| `OLMRadialBlur` Inner/EdgeFade | ASM ownership for Rotation buffers is strong: `+0x38` polar RGBA, `+0x40` span/gate, `+0x48` prepass alpha, `+0x50` prepass factor. Current Size Variation 0 refs cannot identify the true `+0x40/+0x50` semantics. | Keep Inner/EdgeFade promotion stopped until `radialblur_inner_size_variation_20260606` is imported; compare only a small set of plane hypotheses across size and alpha-grid cases. |
| `OLMKiraKira` | All-ray two-temp/no-fastpath remains the best binary-backed candidate. BoxFilter length/anchor/border and Brightness-vs-Strength split are mostly confirmed; final five-buffer aggregation is not the main residual. Equal-ray, zero-rotation refs still entangle ray order, helper scalar, crop, and angle mapping. | Keep equal-ray tuning stopped until `kirakira_single_ray_20260606` is imported; then isolate vertical/horizontal fast path, diagonal angle table, and helper scalar in that order. |
| `OLMSmoother` / `OLMSmoother2` | `OLMSmoother2 --force-version 1` remains the preferred v1 compatibility route for current refs. v2 key paths are guarded; no-key `case_0001` should not be tuned after negative idx0 and plane-split diagnostics. | Keep standalone v1 low priority and wait for `smoother2_no_key_grid_20260606`; then run `refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py` first. |
| `OLMColorKey` | Current refs cover RGB exact, Edge Thin, and exploratory Edge Blur, but all have `Enable Replace=0`, only one enabled key color, and insufficient non-black color-space coverage. Python/C++/Rust reject Replace and Mac does not yet apply replace colors. | Wait for `olmcolorkey_replace_colorspace_20260606`; then run the manifest audit and request smoke before implementing the smallest RGB Replace/no-edge slice. |
| `OLMDistanceGradation` | Constant-before-blur is decomp-backed, and current C++/Python already apply it. The wider blur radius used for `case_0029` is Windows-reference-fit evidence rather than fully decomp-proven, but it is guarded by the blur smoke. | Keep current production path and guard; only tighten the blur kernel with stronger OpenCV/binary evidence. |

## 2026-06-06 Fourth Parallel Stop-Line Audit

This pass was launched after the AE pixel validation preset commit
`578380c`. It keeps the same read-only policy and asks whether each hard
plug-in still has any objdump/decomp-backed move before the pending Windows
reference package returns.

| Plugin area | Agent | Scope | Expected output |
| --- | --- | --- | --- |
| `OLMDirectionalBlur` | `019e9a34-0828-7f43-be44-514f475604e6` / Herschel | `notes/IR_OLMDirectionalBlur.md`, `notes/OLMDirectionalBlur_ASM_FACTS.md`, `refs/reference_requests/directionalblur_context_scale_20260606.json`, current directional Python/C++ probes, decomp/disasm as needed. | IR checkpoints, exact metrics, whether a non-guesswork move exists before refs, and the exact stop/unblock condition. |
| `OLMRadialBlur` Inner/EdgeFade | `019e9a34-1eac-7902-a803-6c44db80213a` / Kuhn | `notes/OLMRadialBlur_RE.md`, `notes/OLMRadialBlur_ASM_FACTS.md`, `refs/reference_requests/radialblur_inner_20260605.json`, `refs/reference_requests/radialblur_inner_size_variation_20260606.json`, current radial probes, decomp/disasm as needed. | Green/red slice map, buffer/plane facts, current-ref sufficiency, and the exact ref evidence needed. |
| `OLMKiraKira` | `019e9a34-38ee-75b0-94ab-3381ed1007b9` / Aquinas | `notes/OLMKiraKira_ASM_FACTS.md`, `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md`, `refs/reference_requests/kirakira_single_ray_20260606.json`, current Python/C++/OpenCV probes, decomp/disasm as needed. | Best candidate path, ruled-out probes, whether any non-guesswork move remains before single-ray refs, and exact unblocking evidence. |
| `OLMSmoother` / `OLMSmoother2` | `019e9a34-5018-7593-9f08-a8053857a275` / Sagan | `notes/OLMSmoother2_ASM_FACTS.md`, `refs/reference_requests/smoother2_no_key_grid_20260606.json`, v1/v2 CLI and smoke scripts, decomp/disasm as needed. | v1-via-v2 coverage, exact metrics, no-key v2 stop condition, and exact unblocking evidence. |

Parent-side status at launch:

- `python3 refs/scripts/check_reference_request_status.py` reports all six
  active requests pending.
- `python3 refs/scripts/package_reference_requests.py --pending --output
  /tmp/olm_reference_requests_pending.zip` regenerated the Windows handoff
  package successfully.

### Fourth Audit Results

All four agents were closed after returning read-only reports. No sub-agent
edited implementation files.

| Plugin area | Result | Parent action |
| --- | --- | --- |
| `OLMDirectionalBlur` | A fresh exact-rowdriver probe reconfirmed that the AEX-shaped rowdriver remains red: full choreography `case_0001/0005 mean=4.4483/1.1703`, exact scatter/rowdriver `4.4392/1.1761`. Binary-backed facts still point at `ctx+0x11c/0x120` render scale, premul/straight RGB, and alpha side-channel ambiguity. | Do not tune from current opaque refs. Wait for `directionalblur_context_scale_20260606`, especially actual context scale or render/downsample metadata plus non-opaque alpha hard-edge/ramp cases. |
| `OLMRadialBlur` Inner/EdgeFade | Zoom and tiny Rotation remain guarded green (`case_0009 max=1 mean=0.0046`, Zoom Offset `max=8 mean=0.0059`, tiny Rotation `mean=0.0104`). Inner/EdgeFade remains red (`0011/0012/0013 mean=25.2972/10.6222/21.2910`; EdgeFade best `5.1129/3.9755/1.9204`). ASM ownership for `+0x38/+0x40/+0x48/+0x50` is strong, but current refs all have `Size Variation=0`. | Wait for `radialblur_inner_size_variation_20260606`; use the returned nonzero Size Variation and alpha cases to isolate `+0x40` span/gate and `+0x50` factor semantics before promoting Inner changes. |
| `OLMKiraKira` | Best candidate remains all-ray `aex-two-temp`/no-axis-fast-path. Default C++ is `case_0001/0002/0003 mean=0.8381/1.1623/1.7003`; no-fast-path two-temp is `0.8506/1.1570/1.0563`. Probes ruled out simple full-frame/ROI-temp/in-place-temp, one-pixel final crop fixes, final five-buffer aggregation, non-normalized box filter, bad anchors, and bicubic rotation. | Wait for `kirakira_single_ray_20260606`; isolated vertical/horizontal/diagonal rays are needed to decide ray order, angle table, scalar semantics, and crop/canvas behavior. |
| `OLMSmoother` / `OLMSmoother2` | Standalone v1 remains red (`mean=1.0145/1.3083/1.4269`), but `OLMSmoother2 --force-version 1` covers current v1 refs (`mean=0.0055/0.0051/0.0200`). v2 key and gamma gates pass; no-key `case_0001 mean=0.1832` has no remaining safe single-case tuning after idx0 and plane-split probes worsened. | Keep standalone v1 low priority. Wait for `smoother2_no_key_grid_20260606`, then run `refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py` first. |
