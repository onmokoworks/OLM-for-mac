# Binary-Grounded IR: OLMBlur

## Feature

- Plug-in: OLM Blur
- Feature/path: alpha-masked repeated blur, legacy and non-legacy paths
- Bit depth: 8bpc and the declared seven-case 16bpc slice are AE exact;
  declared 32bpc `case_0001..0005` is AE exact against runtime-bound Windows
  Software references
- Reference set:
  - `refs/win_references/20260604_olm/OLMBlur`
  - normalized Software refs under
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur`
- Current status:
  - packaged 8bpc Mac AE return is exact for `case_0001..0007`
  - AE-free CLI remains exact for normalized Software `case_0001/0002/0004/0005`
  - AE-free CLI keeps useful `max=1` residual witnesses for
    `case_0003/0006/0007`
  - 16bpc Mac AE validation is 0/7 exact, but a 2026-06-26 endian-fix
    reverify proved that 6/7 residuals are only near 1 LSB in AE 16bpc output
    terms, appearing as `max_diff=2` in exported PNG space rather than the
    previously reported 512-step family
  - `case_0007` keeps the same near-1LSB family plus a remaining
    Legacy border/seed anomaly (`max_diff=383` at the localized witness)
  - historical 16bpc writeback/border investigations remain useful IR, while
    untested 32bpc `case_0006..0007` remain unpromoted
  - 2026-07-27 fresh-project FLOAT EXR comparison closes declared 32bpc
    `case_0001..0005`; case 0003 and case 0004 require the binary-grounded
    float-exponent/binary64-`exp` coefficient path
- 2026-06-22 provenance audit confirms the packaged AE-host candidates are
  exact against the 20260618 normalized refs for all seven cases; the large
  differences in `case_0001..0004` are only against the older 20260604
  reference generation.
- Cross-feature canonicalization audit:
  `refs/reports/software_reference_canonicalization_8bpc.md` now verifies the
  same normalized-reference decision alongside OLMColorKey and
  OLMDistanceGradation. OLMBlur is `normalized-software-exact` for 7/7 cases;
  only the older 20260604 generation drifts on `case_0001..0004`.
- 2026-06-24 decision matrix:
  `refs/reports/olmblur_decision_matrix_20260624/decision_matrix.md`
  consolidates the current rule as `preserve-normalized-ae-exact`: normalized
  8bpc is 7/7 exact, old-reference drift is limited to 4 cases, and the
  remaining AE-free CLI `max=1` witnesses are diagnostic. Do not change the
  passing AE behavior from these residuals; only continue them as
  binary-grounding work for accumulation/helper or Legacy border/all-same
  state.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| OLM Blur applies blur to pixels with `alpha > 0`. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMBlur__OLMBlur__doc__OLMBlurUserManualEN.txt`. | manual-backed |
| Color Key workflow makes boundary-only blur by creating the alpha/matte region first. | Official manual and product page. | manual-backed |
| Non-legacy path uses repeated Gaussian-like separable passes with decaying radius. | `cli/OLMBlur/main.cpp`, `mac/OLMBlur/OLMBlur.cpp`, and current normalized refs. | binary-grounded / CLI-confirmed |
| Non-legacy radius path uses `pow(double,double)` then float sigma. | `notes/CONFORMANCE_LEDGER.md` and current CLI implementation. | binary-grounded / CLI-confirmed |
| Legacy writeback currently uses `floor(x + 0.5)`. | Binary `.rdata` constant `0.5`, decomp/port notes. | binary-grounded |
| Non-legacy writeback currently uses a compatibility `nearbyint` shim. | Current CLI/Mac implementation; exact for normalized `case_0001..0005`. | CLI-confirmed but not final binary explanation |
| 16bpc standard writer adds `0.5`, passes through the clamp/helper, truncates with `CVTTSS2SI`, then stores 16-bit channel words. | `disasm/OLMBlur.aex.asm.txt` around `180002fad..18000302e`: `MOVSS` loads `0.5`, `ADDSS`, helper call, `CVTTSS2SI`, `MOV word ptr [RBX+...]`. | binary-grounded |
| Legacy/alternate 16bpc writer uses a later direct `CVTTSS2SI` word-store family. | `disasm/OLMBlur.aex.asm.txt` around `1800031f9..`; matches the earlier runtime-trace location family for Legacy `case_0007`. | binary-grounded / runtime-trace |
| 2026-06-29 ASM writer audit makes the 16bpc writer split reproducible: standard word writer is `round-add-helper-truncate-word-store`, alternate word writer is `direct-memory-truncate-word-store`, and the known `+0x7fdf` family is an 8bpc byte-store analogue. | `scripts/analyze_olmblur_16bpc_asm_writer.py`, `refs/conformance/olmblur_16bpc_asm_writer_audit_20260629.md`, and smoke `python3 refs/scripts/smoke_analyze_olmblur_16bpc_asm_writer.py`. | binary-grounded / reproducible-audit |
| `refs/scripts/verify_manifest.py` previously misread ImageMagick 16-bit RGBA output with the wrong endianness. | 2026-06-26 local audit: direct `magick txt:-` witness at `(466,173)` is `28869`, while the old verifier path decoded it as `50544`; forcing `-endian MSB` or reading little-endian raw fixes the discrepancy. | binary-grounded tooling fact |
| After the endian fix, current Mac AE 16bpc OLMBlur residuals are mostly near 1 LSB in AE 16bpc output terms, not broad 512-step quantization. | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` and `refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_2335_endian_fix.md`: non-Legacy cases are `max_diff=2`, while Legacy `case_0007` is `max_diff=383`. | AE-validation diagnostic |
| 2026-06-27 full-image remeasure shows the near-1LSB family is sign-mixed, not one-directional. | Local comparison of the normalized Windows 16bpc refs in `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/` against `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmblur_exact/candidate/`: global nonzero channel deltas are `-2:463`, `+2:1478`, and `+383:3` (Legacy only). | AE-validation diagnostic |
| 2026-06-28 Mac AE rerun reproduces the same 16bpc family on the current plug-in. | `refs/conformance/olmblur_16bpc_mac_ae_rerun_20260628.md`: `case_0001..0006` are sign-mixed `max_diff=2`; `case_0007` is `max_diff=383` with the localized Legacy border/seed witness at `(0,0)`. `case_0003` was re-rendered as a single-case request because the full AE batch did not write it cleanly, but the single PNG compares to the same `max_diff=2` result. | AE-validation diagnostic |
| 2026-06-28 word-delta audit narrows the 16bpc residual to one internal word for the non-Legacy family. | `refs/conformance/olmblur_16bpc_word_delta_audit_20260628.md`: all nonzero `case_0001..0006` exported channel deltas are `+/-2`, which infers `+/-1` in AE's 0..32768 PF_Pixel16 word domain. `case_0007` mostly shares that family but keeps a separate `(0,0)` `-383` exported / about `-192` word Legacy witness. | AE-validation diagnostic |
| 2026-06-29 writer-contract audit proves the current Mac source does not literally match the Windows standard 16bpc writer contract. | `refs/conformance/olmblur_16bpc_writer_contract_audit_20260629.md`: Mac non-legacy `store16` uses `nearbyintf(v)` then clamp/cast, while Windows standard 16bpc asm is `+0.5 -> helper -> CVTTSS2SI -> word store`. But all six non-Legacy 16bpc cases are still sign-mixed one-word residuals, so this source-vs-asm mismatch is real but not yet sufficient to justify a blind global writer swap. | binary-grounded / source-vs-asm audit |
| 2026-06-29 bounded Mac AE probe confirms the live installed non-Legacy plug-in is executing the `nearbyint`-family 16bpc writer at runtime. | `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/probe_report.md` and `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/blur_debug.txt`: `(314,14)` logs raw `1100.5` with `floor05=1101`, `nearby=1100`, and stored `1100`; `(29,71)` logs raw `363.5` with `floor05=364`, `nearby=364`, and stored `364`. This is the expected ties-to-even signature for `nearbyintf`. | Mac-AE runtime witness |
| 2026-06-29 live-probe audit ties the internal `store16` witnesses directly to the exported 16bpc PNG deltas. | `refs/conformance/olmblur_16bpc_live_probe_audit_20260629.md`: positive exported values follow `2 * stored_word - 1`, so non-Legacy `+/-1` internal-word disagreements appear as exported `+/-2`, and Legacy `case_0007 (0,0)` stored `192` appears as exported `383`. | binary-grounded / host-runtime audit |
| 2026-06-29 Legacy stage probe narrows the `case_0007 (0,0)` anomaly to the horizontal Legacy pass, not the writer or the vertical pass. The same-day CLI control also rejects a broad `truncated_window => passthrough` rule because it worsens Legacy `case_0007` to `max=90`, so any border exception must be narrower than generic sample-window truncation. | `refs/conformance/olmblur_legacy_stage_probe_20260629.md`: `(0,0)` stays `all_same=1` and `out=center` through vertical passes, but horizontal `iter=3` is the first place where `all_same` flips to `0` and output becomes nonzero. By final store, raw is already `191.976715`. | binary-grounded / host-runtime stage audit + local control rejection |
| 2026-06-29 decomp-backed Legacy carry-prev rule materially improves the active residual. | `refs/conformance/olmblur_legacy_carry_prev_probe_20260629.md`: `FUN_1800014f0` / `FUN_180001ea0` keep the previous comparison RGB outside the inner pixel loop with sentinel `DAT_18000d27c = -1.0f`. Porting that rule removes the old `(0,0)` spill, preserves exact 8bpc cases, reduces old 8bpc `case_0007` from 3 residual pixels to 1, and reduces Mac AE 16bpc `case_0007` to `max=1` / one remaining pixel. | binary-grounded / implementation-improved |
| 2026-06-29 last-pixel follow-up shows the remaining 8bpc and 16bpc Legacy witnesses are both half-step boundary cases, not renewed structural mismatches. | `refs/conformance/olmblur_last1px_family_probe_20260629.md`: old 8bpc `case_0007 (488,941)` is `250.499985` while neighbor `(488,942)` is `250.500015`; current Mac AE 16bpc `case_0007 (345,672)` is exactly `12544.5` on blue, producing Mac stored word `12545` / exported `98` while Windows exported `97` implies internal word `12544`. This favors a tiny pre-store float delta over a proven global writer-rule mismatch. | binary-grounded / runtime witness |
| 2026-06-29 current-baseline audit freezes the active Mac-side witness bundle across all remaining OLMBlur proof lanes. Non-Legacy `case_0006` remains sign-mixed at the exact live witnesses (`314,14 => 2199 vs 2201`, `29,71 => 727 vs 725`) while the live probe confirms `nearbyint` storage from raw `.5` values. Legacy `case_0007` 16bpc keeps only the one-word blue half-step (`345,672 => 25089 vs 25087`), and the current workspace CLI rerun of old normalized 8bpc `case_0007` keeps only one red pixel low at `(488,941)` while `(488,942)` matches. This is the baseline to compare against the next Windows final-word runtime witness. | `refs/conformance/olmblur_current_word_baseline_20260629.md` and `scripts/analyze_olmblur_current_word_baseline.py`. | baseline freeze / current-workspace evidence |
| 2026-06-30 writer-only hypothesis audit proves that a blind `nearbyint -> floor05` swap cannot explain all active OLMBlur witnesses. | `refs/conformance/olmblur_writer_only_hypothesis_20260630.md` and `scripts/analyze_olmblur_writer_only_hypothesis.py`: non-Legacy `(314,14)` prefers `floor05`, but `(29,71)` is writer-rule-irrelevant, Legacy 16bpc `(345,672)` prefers `nearby`, and old 8bpc `(488,941)` is still below the half-step under both local writer rules. This tightens the remaining ask to actual Windows pre-store/helper values rather than a source-only writer rewrite. | current-workspace audit / decision-boundary |
| For 16bpc Non-Legacy `case_0004`, the hash-pinned AEX guest caller schedules 48 helper calls with H/V-agreed radii `[125,36,10,2]`. Actual-AEX one-output strips match the portable helper for all four radii and both directions. The host-callback and Mac coefficient sets differ only at iteration 1 indices 57/70 by one ULP; portable full-cone A/B moves both retained pre-store values from `22037.498046875/26373.498046875` to `22037.5/26373.5`, changing grounded writer predictions exactly from observed Mac words to Windows reference words. Callback coefficients are not independently Windows CRT truth, so this grounds the residual mechanism and candidate gate, not AE exact. | `refs/conformance/olmblur_case0004_staged_helper_replay_20260716.json`; `refs/conformance/olmblur_case0004_mac_generation_audit_20260716.json`; `refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.json`. | binary-grounded caller schedule + helper micro differential / coefficient-sensitivity closure |
| The narrow production candidate preserves the float32 exponent input and changes only `expf(x_f32)` to `(float)exp((double)x_f32)`. It matches all `177/177` declared callback-backed coefficient words, restores both predicted case-0004 words, passes source/helper/cone regressions, and builds Universal arm64/x86_64. It remains an AE-validation candidate because callback coefficients are not independently Windows CRT truth. | `refs/conformance/olmblur_case0004_exp_double_candidate_20260716.json`; `mac/OLMBlur/OLMBlur.cpp`. | implementation candidate / regression-grounded / AE validation pending |
| For 16bpc Legacy `case_0003`, the hash-pinned caller emits 120 helper calls as ten `H x 6, V x 6` iterations at radius 248. Actual-AEX one-output helpers match portable C++, and a native full-frame replay with captured coefficients predicts all 20 Windows residual words. The current 16bpc Legacy float-exp coefficients differ at 16/4970 words; double-exp-to-float matches 4970/4970, while exact Legacy control `case_0007` changes 0/110 coefficient words. Only the 16bpc Legacy worker is changed and the Universal build succeeds. | `refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.md` / `.json`; `core/olmblur_worker16_legacy.cpp`. | implementation candidate / callback-backed binary schedule / AE validation pending |
| 2026-06-30 Windows databreak witness resolves the surviving 16bpc Legacy half-step point `(345,672)` directly. | `refs/conformance/olmblur_case0007_16bpc_windows_b_witness_20260630.md`: Windows blue pre-store float is `12544.498046875`, `cvttss2si` produces `12544`, and the final stored word is `0x3100`. This confirms that the Mac/Windows split at this witness is a pre-store float delta before truncation, not a remaining uncertainty about the local Legacy writer rule. | windows-runtime witness / resolved-legacy-half-step |
| 2026-07-01 consolidated `case_0007` half-step audit keeps the Legacy family split by bit depth instead of treating it as one unresolved lane. | `scripts/analyze_olmblur_case0007_halfstep_family.py`, `refs/scripts/smoke_analyze_olmblur_case0007_halfstep_family.py`, and `refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.md`: normalized 16bpc `(345,672)` is now closed as `12544.5` on Mac versus Windows `12544.498046875 -> 12544`, while old normalized 8bpc `(488,941)` remains below the half-step on the Mac side and still needs a Windows pre-store float rather than a writer rewrite. | reproducible half-step family audit |
| 2026-06-29 pending final-word proof contract is now tied to the latest bundled Windows runtime summary, and the 2026-06-30 narrow package cuts that ask down to the two sign-mixed non-Legacy `case_0006` witnesses only. The imported older Windows `case_0006` pre-writeback fact at `(498,940)` remains useful proof context, but it is not the same lane as the current normalized current-word witnesses `(314,14)` and `(29,71)`, so the live helper/pre-store package is still required. | `refs/conformance/olmblur_pending_final_word_proof_20260629.md`, `refs/runtime_trace_packages/olm_runtime_trace_olmblur_case0006_helper_prestore_witness_20260630.zip`, `refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/runtime_trace_summary_olmblur_repeat_threshold_20260629_235638.json`, and `scripts/analyze_olmblur_pending_final_word_proof.py`. | proof-contract / latest-bundle-grounded |
| 2026-06-30 the first focused `case_0006` helper/pre-store return imported successfully as a failure-mode witness, not as the requested pixel witness. | `refs/reports/runtime_trace_summary.md`, `refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_witness.md`, and the share return `olmblur_case0006_helper_prestore_witness_20260630_return_windows.zip`: AE rendered the case under Software mode, but the debugger never captured `TARGET_OLMBLUR_CASE0006_*`; the recorded blockers were AE Crash Repair / startup modal interruption and an unresolved `bu OLMBlur+0x2fad` that did not bind before `ModLoad`. This keeps the lane classified as "values still missing", not "Windows disagrees at helper/pre-store". | windows-runtime failure witness / retry-contract |
| 2026-06-30 before-effects source provenance now agrees with the live helper split at the two remaining non-Legacy witnesses. | `refs/conformance/olmblur_case0006_nonlegacy_helper_witness_20260630.md` and `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006_before_effects.png`: both centers `(314,14)` and `(29,71)` are black/opaque, but the nearby bright support differs by axis and offset. A local replay of iter1 vertical accumulation reproduces the same directional split as the live Mac helper witness, which strengthens the conclusion that `case_0006` is already divergent in helper-local source support rather than only at final writeback. | source-provenance / helper-prestore reinforcement |
| Non-legacy `case_0006` residual is already present before byte writeback. | 2026-06-20 Windows CDB return: `(498,940)` pre-writeback red is `185.49998474121094` while the Mac CLI baseline is exactly `185.5`; final Windows byte is `185`. | runtime-trace |
| Non-legacy blur helpers are structurally plain weighted contiguous-span accumulators, unlike the Legacy `all_same`/carry-prev family. | `decomp/OLMBlur.aex.c.txt` `FUN_180001000` / `FUN_180001980`: when center alpha is nonzero, they accumulate left/right or up/down until radius or first alpha-zero boundary, normalize by `1/sumW`, and do not carry an `all_same` state or special border sentinel. This matches the current Mac/CLI non-Legacy loop shape closely enough that the active `case_0006` lane should be treated as helper-local float/span evidence, not as a likely missing Legacy-style structural branch. | binary-grounded / 2026-06-30 helper audit |
| The active center is included with `weights[0]`; an inactive center copies source RGB. Each side stops at its first inactive flag, clamps by edge/radius, and zero total weight writes positive zero. | `core/olmblur_helper.cpp`, `tools/emulation/fixtures/olmblur_helper/`, and `refs/conformance/olmblur_helper_cpu_fixture_20260710.md`: six actual-AEX horizontal/vertical fixtures replay byte-exact through the portable core. This rejects an earlier prose-only “center excluded” reading. | binary-grounded / portable helper exact |
| Dispatch selects `FUN_180001000/FUN_180001980` for Non-Legacy and `FUN_1800014f0/FUN_180001ea0` for Legacy at every 8/16/32bpc worker. Bias value `1` orders horizontal then vertical; value `2` reverses the order. | `refs/conformance/olmblur_fullworker_branch_map_20260711.md`, grounded at `FUN_18000a380` and the property block offsets `+0x20..+0x30`. | binary-grounded / cross-depth dispatch |
| The Legacy `14f0/1ea0` helper pair uses centered weights, strict interior checks, direction-local flag breaks, carried previous RGB initialized to `-1`, and asymmetric inactive-center behavior (`14f0` copies, `1ea0` leaves destination untouched). | `core/olmblur_fullworker_helper.*`, `tools/emulation/fixtures/olmblur_fullworker_helper/`, and `refs/conformance/olmblur_fullworker_helper_20260711.md`: six direct actual-AEX fixtures, including large radius and partial offsets, replay byte-exact. | binary-grounded / portable helper exact |
| Mac direction order matches AEX, but Mac full-plane helper calls do not encode the AEX worker's six subpass offsets and plane swaps. Helper-level exactness is therefore insufficient for full-worker equivalence. | `refs/conformance/olmblur_fullworker_branch_map_20260711.md`; AEX Legacy 16bpc mode-1 block `0x18000662d..0x180006878` and mode-2 block `0x18000690d..0x180006b58`. | binary-grounded / implementation gap |
| 8bpc Non-Legacy `FUN_180003710` stages A,R,G,B bytes, splits each directional pass into six contiguous chunks, swaps float RGB planes, applies repeat decay/weights, and writes `floor(rgb+0.5)` while retaining copied alpha. | `core/olmblur_worker_orchestration.*`, `tools/emulation/fixtures/olmblur_worker_orchestration/`, and `refs/conformance/olmblur_worker_orchestration_20260711.md`: two complete A/R/G/B output buffers replay byte-exact against actual AEX, including a large-radius reverse-direction case. | binary-grounded / complete worker slice exact |
| 32bpc Non-Legacy `FUN_180004b80` uses the same six-subpass orchestration on raw float32 A/R/G/B, treats any nonzero alpha (including negative) as active, preserves copied alpha, and writes RGB without clamp or quantization. | `core/olmblur_worker32_nonlegacy.*`, `tools/emulation/fixtures/olmblur_worker32_nonlegacy/`, and `refs/conformance/olmblur_worker32_nonlegacy_20260711.md`: two complete float buffers replay byte-exact against actual AEX without EXR oracle. | binary-grounded / complete worker slice exact |
| 2026-07-27 fresh-project AE proof closes declared 32bpc Legacy `case_0003`. `FUN_180009e10` forms a float32 exponent and imports `expf`; Windows UCRT and macOS libSystem differ at 8/2490 coefficient words by one ULP, while Windows UCRT matches binary64 `exp` followed by a float32 cast at 2490/2490. The old Mac path reproduces 54,235 native full-frame word deltas (max 4), and the bounded float-exponent/double-`exp` path matches Windows at all 33,177,600 native words. With the final Mach-O `a0b3a138...495279d` mapped by `vmmap`, fresh Mac AE `26.3x87` matches the ETW-bound Windows AEX for both no-effect and effect-on at `0/8,294,400` FLOAT32 word mismatches. Saved-AEPX zero-second disk-cache returns were rejected because the instrumented dispatch was never entered. | `refs/conformance/olmblur_32bpc_case0003_ae_exact_20260727.md` / `.json`; `core/olmblur_worker32_legacy.cpp`. | binary-grounded CRT root cause / runtime-bound / AE exact |
| 2026-07-27 fresh-project AE proof closes declared 32bpc Non-Legacy `case_0004`. The no-effect control is exact before the change, while the old effect output differs at 5,439/8,294,400 FLOAT32 words (max 4). The retained coefficient audit localizes the first old-path split to AEX-derived `0x3ecaa909` versus macOS `expf` `0x3ecaa908`; preserving the float32 exponent and evaluating binary64 `exp` before the float32 cast matches 177/177 declared coefficient words over radii `[125,36,10,2]`. With final Mach-O `c6a9e54b...e3d9d83e` mapped by `vmmap`, fresh Mac AE matches the ETW-bound Windows AEX for both no-effect and effect-on at `0/8,294,400`; seven complete actual-AEX Non-Legacy worker fixtures remain exact. | `refs/conformance/olmblur_32bpc_case0004_ae_exact_20260727.md` / `.json`; `core/olmblur_worker32_nonlegacy.cpp`. | binary-grounded coefficient boundary / runtime-bound / AE exact |
| 2026-07-27 fresh-project AE proof closes declared 32bpc Non-Legacy `case_0005` without another core change. The older retained Windows pair is rejected because its no-effect frame already differs from the fresh Mac control at 63,644 words; a path-normalized same-AEPX recapture makes both control and effect exact at `0/8,294,400`. Windows ETW binds `AfterFX.com` PID `44300` to AEX SHA `f0611785...e96e5b`, and Mac `vmmap` binds PID `24997` to Mach-O `c6a9e54b...e3d9d83e`. Effect-on differs from control at the same 2,165,806 words on both hosts. | `refs/conformance/olmblur_32bpc_case0005_ae_exact_20260727.md` / `.json`. | runtime-bound / reference-contract audit / AE exact |
| 2026-07-27 fresh-project AE proof closes declared 32bpc Non-Legacy `case_0006` without another core change. Canonical replacement of only the platform-specific AEPX `fileReference` elements makes the Mac/Windows projects byte-identical. Both control and effect are exact at `0/8,294,400`, with Windows ETW binding `AfterFX.com` PID `46876` to AEX SHA `f0611785...e96e5b` and Mac `vmmap` binding PID `26758` to Mach-O `c6a9e54b...e3d9d83e`. Effect-on differs from control at the same 5,911,831 words on both hosts. This 32bpc promotion supersedes only the old 32bpc unpromoted status, not the separate historical 16bpc provenance record. | `refs/conformance/olmblur_32bpc_case0006_ae_exact_20260727.md` / `.json`. | runtime-bound / same-contract / AE exact |
| 16bpc Non-Legacy `FUN_180002280` uses PF_Pixel16 A/R/G/B staging, the exact `1000/1980` helpers in six subpasses, and a `+0.5` then truncating/clamped word writer. | `core/olmblur_worker16_nonlegacy.*`, `tools/emulation/fixtures/olmblur_worker16_nonlegacy/`, and `refs/conformance/olmblur_worker16_nonlegacy_complete_worker_20260711.md`: two complete PF16 buffers replay byte-exact against actual AEX. | binary-grounded / complete worker slice exact |
| The PF16 writer is experimentally distinguished from nearest-even, not only inferred from asm. | `tools/emulation/test_olmblur_writer16_half_ties_20260713.py` executes actual AEX `0x1800030e2..0x180003123`; raw float32 `1100.5` stores `1101`, while nearest-even would store `1100`. See `refs/conformance/olmblur_writer16_half_ties_actual_aex_20260713.md`. This closes writer semantics but not the live pre-store float or AE host boundary. | binary-grounded / writer semantics closed |
| 2026-07-13 actual-AEX dependency-cone worker replay for normalized 16bpc Non-Legacy `case_0006` returns from entry `0x180002280` with helper calls `[120,120]` (the expected six-chunk worker schedule per witness), and every retained source-staging, helper ABI/plane/origin/offset, helper-output, final pre-store float, and stored-word observation is bit-exact against the current portable worker at `(314,14)` and `(29,71)`. This is not full-frame equivalence evidence. | `refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.md` / `.json`; AEX SHA-256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`; dimensions `1920x1080`; parameters `blur=5.0`, `smoothness=100.0`, `repeat=10`, `bias=1`, `legacy=0`. | binary-grounded / actual-AEX dependency-cone fact |
| The same full-worker replay does not close Windows-vs-Mac conformance: `(314,14)` AEX/portable stored RGB is `[2201,2201,2201]`, matching the Windows PNG, but `(29,71)` is `[727,727,727]` while the Windows PNG is `[725,725,725]`. No same-run Windows typed helper/pre-store values exist, so the first Windows internal difference remains unknown. | `refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.md` / `.json`. The AEX `pow`, `powf`, and `expf` calls use loader host-backed libm callbacks; native Windows CRT math is not exercised. | binary-grounded limitation / no source-or-kernel diagnosis |
| 2026-07-13 full-worker evidence freezes unjustified changes: do not alter Non-Legacy helper accumulation, six-chunk orchestration, plane swaps, offsets, radius/order, or the 16bpc writer from the `(29,71)` PNG delta; do not substitute native-CRT math or tune toward PNG. Any reopen requires same-run Windows helper/pre-store evidence that localizes the first internal difference. | The full-worker report's dependency-cone limitation and `first_windows_internal_difference_reason`, together with the existing source-candidate and closeout gates below. | decision / source-and-kernel freeze |
| 2026-07-16 bounded actual-AEX audit narrows the two remaining current-plugin 16bpc red cases without claiming exactness. For Legacy `case_0003`, all 20 residual coordinates match retained-PNG-to-PF16 staging bits, but radius 248 x repeat 10 makes the dependency cone full-frame, so helper/pre-store is not locally bounded. For Non-Legacy `case_0004`, both residual coordinates match staging, and isolated actual-AEX writer micro-runs store the portable pre-store inputs exactly; a dependency-cone worker attempt still hit the one-billion-instruction cap before writer. The first unresolved boundary is therefore worker/helper pre-store, not source conversion, and the writer exclusion is conditional on the portable inputs. | `refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.json`. | binary-grounded staging + writer micro-boundary / worker pre-store blocked |
| 8bpc Legacy `FUN_180007300` stages A/R/G/B, uses the exact `14f0/1ea0` carry helpers with centered weights in six subpasses, and writes `floor(rgb+0.5)` while preserving alpha. Partial nonzero alpha is active; zero alpha exercises the horizontal-copy/vertical-untouched asymmetry. | `core/olmblur_worker8_legacy.*`, `tools/emulation/fixtures/olmblur_worker8_legacy/`, and `refs/conformance/olmblur_worker8_legacy_20260711.md`: three complete buffers, including mixed alpha, replay byte-exact. | binary-grounded / complete worker slice exact |
| 2026-06-30 live Mac AE helper witness proves the current non-Legacy `case_0006` pair diverges before `store16` even on the installed plug-in. With identical support geometry at both tracked points, the final iteration still reaches `vertical out_norm = 0.0335845947` at `(314,14)` versus `0.0110931396` at `(29,71)` before the later `1100.5 -> 1100` / `363.5 -> 364` word stores. | `refs/conformance/olmblur_case0006_nonlegacy_helper_witness_20260630.md` and `/tmp/olmblur_case0006_helperdebug_20260630/blur_debug.txt`. | Mac-AE runtime witness / helper-prestore proof |
| 2026-07-01 reproducible provenance audit keeps `case_0006` out of source-surgery territory. | `scripts/analyze_olmblur_case0006_reference_provenance.py`, `refs/scripts/smoke_analyze_olmblur_case0006_reference_provenance.py`, and `refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.md`: canonical 2026-06-25 Windows ref and handoff expected mirror are byte-identical; the known Mac single-case and batch exports disagree with that canonical file in different directions at the tracked points; no same-run Windows current-AEX export is present in-tree, so the outcome stays `current-aex-export-missing` and the lane remains provenance/export-first. The same audit now also freezes the local alias structure, which removes one source of confusion: `handoff/.../results/bitdepth16_olmblur_exact/case_0006.png` is byte-identical to the tracked `mac_single_export`, while `handoff/archive/.../results/bitdepth16_olmblur_exact/case_0006.png` is byte-identical to the tracked endian-fix `mac_batch_export`; those are not new third/fourth provenance classes. | reproducible provenance audit / alias freeze |
| 2026-07-01 current-AEX export contract is now machine-readable as well as prose. | `scripts/analyze_olmblur_case0006_current_aex_export_contract.py`, `refs/scripts/smoke_analyze_olmblur_case0006_current_aex_export_contract.py`, and `refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md`: freezes the exact same-run Windows artifact this lane still needs, the four 16-bit witness points to compare first, and the only three allowed interpretations when that export finally lands: `A` canonical match, `B` Mac-export-class match, or `C` neither-known-artifact. Until a Windows current-AEX export is imported, the audit stays `awaiting-windows-current-aex-export` and keeps `case_0006` behind a provenance gate. | reproducible provenance contract / return classifier |
| 2026-07-01 source-candidates audit freezes the implementation order across the remaining OLMBlur lanes. | `scripts/analyze_olmblur_source_candidates.py`, `refs/scripts/smoke_analyze_olmblur_source_candidates.py`, and `refs/conformance/olmblur_source_candidates_audit_20260701.md`: `case_0006` stays behind a non-source provenance/export gate until a same-run Windows current-AEX export or contradictory witness appears; if that gate is broken, reopen the non-Legacy writer boundary before helper accumulation. Legacy `case_0007` remains split by bit depth: normalized 16bpc stays closed as a Windows pre-store float delta, while old normalized 8bpc `(488,941)` is the only carry-prev/helper lane that may reopen. | reproducible source-order freeze |
| 2026-07-01 closeout-gate audit consolidates the remaining OLMBlur work into one reopen rule. | `scripts/analyze_olmblur_closeout_gate.py`, `refs/scripts/smoke_analyze_olmblur_closeout_gate.py`, and `refs/conformance/olmblur_closeout_gate_audit_20260701.md`: `case_0006` is still a provenance/export gate, normalized 16bpc Legacy `case_0007` is closed as a Windows-side pre-store float delta, and only old normalized 8bpc `case_0007 (488,941)` remains eligible for another Windows pre-store/helper ask. The decision is explicit: `do-not-reopen-source-without-two-specific-external-proofs`. | consolidated closeout boundary / source-freeze |
| 2026-07-10 fresh Mac AE export provenance converges; the supposed matching Windows internal witness is retracted. | `refs/conformance/olmblur_mac_export_provenance_result_20260710.md` proves two single-case and two batch runs produce identical stable Mac hashes per case, while canonical verification remains `0/7` with `max_diff=2`. `refs/conformance/olmblur_case0006_unverified_windows_value_audit_20260710.md` then proves the old `answered` return never captured its CDB target and manually populated `windows_*` fields without a new debug artifact. Windows pre-store/store at `(314,14)` and `(29,71)` is unknown. Until a true AEX address-bound chain exists, neither helper nor writer changes are justified. | Mac-AE repeated runtime + invalid Windows evidence correction / source-freeze |
| Legacy `case_0007` uses the later `OLMBlur+0x7FDF` writeback family. | 2026-06-20 Windows CDB return hit `(0,0)`, `(488,941)`, and `(488,942)` at the Legacy writeback family. | runtime-trace |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `Blur Amount` | Base radius/extent. | Scaled by comp/image width in the CLI/mac path. | current implementation |
| `Blur Smoothness` | Legacy sigma multiplier; non-legacy smoothness participates in radius/weights through current port logic. | Clamp/scale follows current C++ port. | current implementation |
| `Number of Repeat` | Number of repeated separable blur iterations. | Minimum 1 in CLI parsing. | current implementation |
| `Bias Direction` | Pass order. | Vertical: horizontal then vertical; Horizontal: vertical then horizontal. | current implementation |
| `Legacy` | Selects legacy kernel/iteration path. | Boolean. | current implementation |

## Kernel / Loop Shape

### Shared Setup

1. Load RGB as floats.
2. Load alpha mask as `1` when source alpha is nonzero, else `0`.
3. Allocate two RGB buffers and two alpha masks.
4. Apply separable blur passes according to Legacy and Bias Direction.
5. Store output RGB; output alpha behavior follows the current port path.

### Non-Legacy Path

Current implementation:

1. Compute `decay = pow(3.0 / blur_amount, 1.0 / (repeat - 1))` when
   `repeat > 1`.
2. For `iter = 0..repeat-1`:
   - `radius_d = blur_amount * pow(decay, iter)` using double pow.
   - `radius = (long)radius_d`.
   - stop when radius is zero.
   - `sigma = float(radius_d) / 3.0`.
   - form the exponent in float32, evaluate binary64
     `exp(static_cast<double>(exponent))`, and cast the result to float32.
   - run two 1D passes in the order selected by `Bias Direction`.

### Legacy Path

Binary-grounded update (2026-07-11): the complete Legacy workers are now
portable and byte-exact against actual AEX complete-buffer fixtures for 8bpc
`FUN_180007300`, 16bpc `FUN_180005f20`, and 32bpc `FUN_1800086d0`. Each depth covers basic,
large-radius reverse-direction, and mixed-alpha fixtures. Their six-subpass
orchestration, carry/validity state, bias order, and final word/byte writer are
therefore no longer inferred from PNG residuals. See
`refs/conformance/olmblur_worker8_legacy_20260711.md` and
`refs/conformance/olmblur_worker16_legacy_complete_worker_20260711.md` and
`refs/conformance/olmblur_worker32_legacy_complete_worker_20260711.md`.

The `all_same` branch copies the current center source RGB; persistent carry
RGB is comparison state only. This is grounded directly by both Legacy helper
decompilations and closes case 0007 at 8bpc and 16bpc. The formal 16bpc Mac AE
batch is now exact for all seven cases. The remaining 8bpc case 0003 is a
large-radius/repeat fixture gap or reference-provenance lane; do not tune it
from PNG alone.

Current implementation:

1. `radius = (long)blur_amount`.
2. `sigma_base = ((blur_amount * smoothness) / 100.0) * (blur_amount / 3.0)`.
3. For `iter = 1..repeat`:
   - `sigma = sigma_base / iter`.
   - build symmetric weights.
   - run two legacy 1D passes in the order selected by `Bias Direction`.

## Sampling / Boundary

- Non-legacy pass clamps sample span to available pixels on each side.
- Legacy helpers exclude coordinate zero from the backward sample side and
  retain comparison RGB across pixels. When all sampled RGB values match that
  comparison state, they copy the current center source RGB, not the carry.
- 2026-06-20 runtime trace did not isolate the Legacy `all_same` state or direct
  border inclusion rule. It did prove that the residual pixels differ before
  byte output, so broad writeback-only fixes are not justified.
- Alpha mask participates in the blur helper; exact per-pass alpha ownership is
  part of the remaining proof for residual cases.

## Channel / Writeback Rules

- RGB is blurred; alpha is used as a mask/validity channel.
- Legacy writeback: `floor(value + 0.5)`.
- Non-legacy current compatibility writeback: `nearbyint`.
- The non-legacy `nearbyint` rule is not final binary-grounded truth because
  the Windows AEX writeback constant is still known to be `0.5`; the remaining
  mismatch likely belongs in accumulation/order before writeback.
- A 2026-06-30 decomp pass strengthens that boundary. The Windows non-Legacy
  helpers (`FUN_180001000` / `FUN_180001980`) do not show the Legacy
  `all_same`/carry-prev machinery at all: they are straightforward contiguous
  weighted accumulators that stop at radius or the first alpha-zero barrier and
  then normalize by `1/sumW`. So for the surviving non-Legacy `case_0006`
  family, the highest-value proof is now helper-local span/float state at the
  witness pixels, not reopening Legacy-style border heuristics.
- 16bpc validation should not be treated as a kernel-tuning signal yet. After
  fixing the verifier endianness, the Mac AE residuals for `case_0001..0006`
  shrink to `max_diff=2`, which is consistent with about one AE 16bpc output
  unit once exported to PNG. Next proof belongs in final rounding/writeback,
  not blur-kernel radius/order.
- The 2026-06-28 word-delta audit makes that more concrete: every nonzero
  `case_0001..0006` exported channel delta is `+2` or `-2`, and all affected
  exported values are odd on both sides. Inferred internal PF_Pixel16 word
  deltas are therefore only `+1` or `-1`.
- The same 2026-06-27 remeasure rules out a trivial global writeback swap as a
  complete explanation: the surviving near-1LSB family contains both `+2` and
  `-2` channel deltas in the exact same validation batch, including mixed-sign
  Legacy witnesses such as `case_0007` around `(1693,220)` and `(1450,227)`.
  So a one-line `round`/`trunc` replacement is not yet justified.
- The 2026-06-29 writer-contract audit sharpens that rule. There is now a
  concrete source-vs-asm mismatch for non-Legacy `store16`
  (`nearbyintf(v)` in Mac source vs `+0.5 -> helper -> CVTTSS2SI` in Windows
  asm), but because the observed 16bpc family is sign-mixed one-word across
  all non-Legacy cases, that mismatch is still not enough to justify a blind
  global `nearbyintf -> floorf(v + 0.5f)` swap without a pre-writeback/helper
  proof.
- The bounded Mac AE probe on 2026-06-29 removes one remaining uncertainty:
  the installed Debug plug-in really is taking the `nearbyint` path at
  runtime. On non-Legacy `case_0006`, half-way value `1100.5` stores as
  `1100`, while `363.5` stores as `364`, exactly the ties-to-even pattern.
  That rules out "stale installed binary" as the reason for the current
  sign-mixed one-word 16bpc family. It still does not prove the residual is
  writeback-only, because Windows already showed a pre-writeback float witness
  for `case_0006`.
- A live Mac AE helper witness on 2026-06-30 resolves that remaining local
  ambiguity. The two active non-Legacy `case_0006` witnesses do not stay equal
  until `store16`; their helper-local outputs already differ materially from
  the first iteration onward, and the last vertical pass still lands at
  `0.0335845947` vs `0.0110931396` before those values become `1100.5` and
  `363.5`. So the active lane is now firmly "helper-local source/accumulation
  provenance" rather than "writer-only rule". See
  `refs/conformance/olmblur_case0006_nonlegacy_helper_witness_20260630.md`.
- A 2026-06-29 Legacy retry adds the companion fact for `case_0007`: the
  problematic `(0,0)` witness is not being created by `floorf(v + 0.5f)` vs
  `nearbyintf(v)`. The live Mac AE plug-in already has raw/stored `~192` at
  that coordinate before/through the writer, which matches the earlier
  exported-PNG anomaly size and points the investigation back to Legacy
  border/seed/all-same state rather than final quantization.
- The 2026-06-29 live-probe audit closes the loop between internal AE words
  and the exported PNGs. At positive witness points the exported 16bpc PNG
  channel is `2 * stored_word - 1`, so the known non-Legacy one-word family
  really does explain exported `+/-2`, while Legacy `(0,0)` stored word `192`
  explains exported `383` exactly. This means the observed PNG sizes are now
  evidence about internal state, not just symptoms.
- The 2026-06-29 Legacy stage probe narrows `case_0007 (0,0)` further than
  that. The value is introduced in the Legacy horizontal pass, first at
  `iter=3` when `all_same` flips from `1` to `0` for the corner witness. The
  vertical pass keeps reporting `all_same=1` and simply preserves the center
  value. So the remaining Legacy target is horizontal border/all_same state,
  not vertical accumulation or final writer behavior.
- A same-day local CLI control helps fence off one tempting over-generalization:
  forcing passthrough for every Legacy truncated sample window
  (`sample_count < 2*radius+1`) leaves the exact cases intact but blows up
  Legacy `case_0007` to `max=90`, `mean=0.0125`, `nonzero=8052/2073600`.
  So the surviving border explanation cannot be "all truncated windows are
  passthrough"; if Windows has a border special-case, it is narrower.
- A later same-day decomp re-read found a stronger explanation: the Windows
  Legacy helpers do not reset their previous-comparison RGB every pixel.
  `FUN_1800014f0` and `FUN_180001ea0` seed from `DAT_18000d27c = -1.0f` and
  carry the last consumed sample forward through the helper scan. Porting that
  rule collapses the old `case_0007 (0,0)` anomaly and leaves only a narrow
  one-pixel family.
- A final 2026-06-29 follow-up narrows that one-pixel family further. Old
  8bpc `case_0007` now differs only at `(488,941)` where the live CLI raw
  value is `250.499985`; the adjacent `(488,942)` is already `250.500015` and
  rounds up to the Windows value. Current Mac AE 16bpc `case_0007` differs
  only at `(345,672)` blue, where the live raw value is exactly `12544.5`, so
  Legacy `floor(x+0.5)` stores `12545` while the Windows exported PNG implies
  internal word `12544`. This is now best understood as a tiny pre-store float
  delta target, not as evidence for reopening the retired structural blocker or
  blindly swapping the global Legacy writer rule.
- The 2026-06-29 proof plan turns that into explicit next witnesses:
  `refs/reports/olmblur_16bpc_proof_plan_20260629/proof_plan.md`.
  Non-Legacy `case_0006` should stay the primary 16bpc target with a positive
  one-word witness at `(314,14)` and a negative one-word witness at `(29,71)`;
  the job is to prove whether those diverge before `store16` or only inside the
  final helper/store path. Legacy `case_0007` should stay split into
  `(0,0)` border/seed/all-same versus a smaller shared-family witness such as
  `(951,7)`.
- The refreshed 2026-06-29 pending-final-word contract tightens that even
  further using the latest bundled Windows runtime summary. `case_0006` is now
  anchored by Windows pre-writeback RGB hex
  `0x1.72fffe0000000p+7 / 0x1.44a3c20000000p-4 / 0x1.44a3c20000000p-4`
  versus current Mac CLI `0x1.73p+7 / 0x1.44a3c6p-4 / 0x1.44a3c6p-4`, while
  `case_0007` is explicitly tied to the Legacy `OLMBlur+0x7FDF` writeback
  family and the surviving half-step witnesses `(345,672)` and `(488,941)`.
  That means the next useful Windows return is only the helper/pre-store
  boundary at those points; broad kernel tuning is no longer an allowed
  interpretation.
- `case_0007` still needs Legacy-specific proof: it shares the same tiny
  rounding family in most pixels, but keeps a localized Legacy border/seed
  anomaly (`max_diff=383`) at a small witness set. Do not change the general
  blur kernel from this case alone.
- The localized `case_0007 (0,0)` anomaly is consistent across bit depths.
  Exported 16bpc PNG `max_diff=383` corresponds to about `191` AE 16bpc units,
  which is the same order as the earlier 8bpc Legacy witness where Windows
  pre-writeback blue was about `1.5528` before truncating to final `0`. Treat
  this as the same Legacy border/seed issue scaled by bit depth, not as a new
  16bpc-only kernel branch.

## Conformance Cases

| Case | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| `case_0001/0002/0004` | 8bpc | `CLI exact` in current smoke | 2026-06-21 rerun: exact (`max=0`); packaged Mac AE validation is exact | Preserve AE behavior; only revisit true binary-grounded writeback if CLI residual closure becomes necessary |
| `case_0003` | 8bpc | AE exact / guarded CLI residual | 2026-06-21 rerun: CLI `max=1 mean=0.0052`; 2026-06-19 AE pixel return `max=0` | Treat as host-path exact but keep runtime/writeback proof open |
| `case_0005` | 8bpc | `CLI exact` in current residual smoke | 2026-06-21 rerun: exact (`max=0`); packaged Mac AE validation is exact | Preserve AE behavior; add 16/32bpc references |
| `case_0006` | 8bpc | AE exact / residual diagnostic | 2026-06-20 Windows trace: AEX pre-writeback red at `(498,940)` is `185.49998474121094` (`0x1.72fffe0000000p+7`), Mac CLI baseline is exactly `185.5` (`0x1.73p+7`), and Windows final byte is `185`; 2026-06-19 AE pixel return `max=0` | Accumulation/helper order proof before changing the passing AE plug-in path |
| `case_0007` | 8bpc | AE exact / residual diagnostic | 2026-06-20 Windows trace: Legacy writeback family `OLMBlur+0x7FDF`; `(0,0)` pre RGB `[0,0,~1.5528]`, final `[0,0,0,255]`; `(488,941/942)` pre red just above `250.5`, final `251`. After the 2026-06-29 carry-prev port, Mac CLI removes the old `(0,0)` spill and leaves only `(488,941)` one red-channel unit low. A same-day rerun shows `(488,941)=250.499985` while `(488,942)=250.500015`, so the remaining witness is now a pure half-step boundary case. | Close the final narrow Legacy witness with a Windows pre-store float witness before changing any global writer rule |
| `case_0001..0006` | 16bpc | not exact / one-word diagnostic | 2026-06-28 current Mac AE rerun: all six failing cases remain `max_diff=2`; word-delta audit infers only `+/-1` PF_Pixel16 word deltas, sign-mixed, so a global rounding-direction change is not justified. 2026-06-29 bounded Mac AE probe on `case_0006` confirms the live installed plug-in stores `1100.5 -> 1100` and `363.5 -> 364` on the non-Legacy path, matching ties-to-even `nearbyint` behavior. | Inspect final pre-writeback float/helper/store order before changing blur math |
| `case_0007` | 16bpc | narrow residual / Legacy diagnostic | 2026-06-28 current Mac AE rerun originally showed a localized Legacy border/seed anomaly (`max_diff=383`) at `(0,0)`. A 2026-06-29 bounded Mac AE retry captured the live Legacy writer witness `raw=191.976715 -> stored=192`, proving the anomaly was pre-store. The same-day stage probe localized it to the horizontal Legacy pass. A later same-day decomp-backed carry-prev port (`FUN_1800014f0` / `FUN_180001ea0`) then removes the old `(0,0)` anomaly entirely: live Mac AE probe now has `(0,0) raw=0 stored=0`, and the normalized Windows 16bpc comparison falls to `max=1` with only one remaining pixel at `(345,672)` blue `98` vs `97`. A final same-day bounded probe shows the surviving blue raw value is exactly `12544.5`, which Mac Legacy stores as `12545`; the Windows PNG implies internal word `12544`, so the remaining target is now a pre-store float witness, not a broad writer mismatch. | Close the last one-pixel Legacy family with a Windows pre-store float witness; old border/all-same blocker is retired |

Mac baseline traces for the normalized Software residual witnesses are stored
under `refs/reports/olmblur_trace_baseline_20260619_030633_mac/`. These logs
should be compared with Windows AEX runtime values before changing writeback or
Legacy border rules.

The 16bpc word-delta audit is reproducible and should not remain a hand-edited
note:

```bash
python3 scripts/analyze_olmblur_16bpc_word_delta.py
python3 refs/scripts/smoke_analyze_olmblur_16bpc_word_delta.py
python3 scripts/analyze_olmblur_16bpc_asm_writer.py
python3 refs/scripts/smoke_analyze_olmblur_16bpc_asm_writer.py
python3 scripts/analyze_olmblur_16bpc_writer_contract.py
python3 refs/scripts/smoke_analyze_olmblur_16bpc_writer_contract.py
python3 scripts/analyze_olmblur_pending_final_word_proof.py
python3 refs/scripts/smoke_analyze_olmblur_pending_final_word_proof.py
```

2026-06-20 Windows overnight return:

- Bundle: `handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`
- Blur trace package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_20260620_overnight.zip`
- Imported comparison:
  `refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold_20260620/olmblur_repeat_threshold.md`
- Conclusion: the return is enough to reject a pure output-rounding diagnosis
  for `case_0006/0007`. It is not enough to rewrite Legacy border/all_same
  behavior, and the packaged Mac AE slices are already exact, so no production
  OLMBlur change should be made from this trace alone.
- The trace comparison helper now treats placeholders such as `0x...`,
  `not isolated`, `unknown`, and selector strings like
  `floorf(value + 0.5) | cvt/trunc | other` as non-evidence. Real hex-float
  values such as `0x1.72fffe0000000p+7`, numeric final bytes, and booleans
  still count. This keeps sparse returns at
  `trace-structure-present-values-missing` while preserving the existing
  2026-06-20 runtime focus classifications.

2026-06-21 Mac-side rerun:

- `smoke_olmblur_cli.py` still passes: `case_0001/0002/0004` exact,
  `case_0005` exact, residual witnesses `case_0003 max=1 mean=0.0052`,
  `case_0006 max=1 mean=0.0000`, and `case_0007 max=1 mean=0.0000`.
- `smoke_compare_olmblur_trace.py` still passes and classifies the next focus
  as `nonlegacy-accumulation-or-writeback`.
- No code change was made: the runtime trace already proves `case_0006` differs
  before byte output, so changing a writeback rounding rule would be
  under-grounded and could break the AE-exact packaged plug-in slice.

2026-06-22 reference provenance audit:

- `scripts/analyze_olmblur_reference_provenance.py` compares the 2026-06-19
  AE-host candidates against the older 20260604 refs and the 20260618
  normalized Software refs.
- `scripts/analyze_soft_reference_canonicalization.py` includes the same
  OLMBlur check in the cross-feature 8bpc Software audit:
  `refs/reports/software_reference_canonicalization_8bpc.md`.
- Latest report:
  `refs/reports/olmblur_reference_provenance_20260622_025614/audit.md`.
- Machine classification:
  `normalized-software-exact-with-legacy-drift`.
- All seven candidates are exact against the normalized refs.
- Old-reference drift is limited to non-legacy `case_0001..0004`:
  - `case_0001`: old-ref `max=59 mean=1.287920525`
  - `case_0002`: old-ref `max=59 mean=1.287920525`
  - `case_0003`: old-ref `max=14 mean=1.727592593`
  - `case_0004`: old-ref `max=58 mean=1.268115355`
- `case_0005..0007` are exact against both old and normalized refs.
- Interpretation: do not tune the plug-in toward the older non-legacy
  `case_0001..0004` PNGs. The remaining `max=1` CLI witnesses are useful for
  binary-grounding accumulation/writeback, but they are not current 8bpc AE
  failures.

2026-06-24 decision matrix:

- `scripts/analyze_olmblur_decision_matrix.py` combines the provenance audit,
  cross-feature canonicalization, and repeat-threshold runtime trace.
- Latest report:
  `refs/reports/olmblur_decision_matrix_20260624/decision_matrix.md`.
- Machine decision: `preserve-normalized-ae-exact`.
- Normalized 8bpc: 7/7 exact.
- Legacy drift: 4 old-reference cases (`case_0001..0004`).
- CLI residuals: `diagnostic-max1`, with 4 nonzero pixels across
  `case_0006/0007`.
- Runtime classification: `prewriteback-or-helper-state`; `case_0006` differs
  before byte output (`0x1.72fffe...` vs `0x1.73p+7`), and `case_0007` is in
  the Legacy `OLMBlur+0x7FDF` writer family with border/all-same still
  unisolated.
- Action: preserve the passing normalized 8bpc AE behavior. Do not change
  writeback rounding or Legacy borders from these witnesses unless a later
  binary proof isolates the helper state and proves the AE path is wrong.

## Open Questions

- True non-legacy final accumulation/writeback order.
- Legacy border/all-same state for the remaining three pixels.
- 16bpc final rounding/writeback rule, including why most residuals differ by
  only about one AE output unit while exported PNGs show `max_diff=2`.
- Legacy 16bpc border/seed state for `case_0007`.
- 32bpc Software reference behavior.
- Whether closing the AE-free CLI max=1 diagnostic is worth another narrow
  helper/border trace after 16bpc is checked.
