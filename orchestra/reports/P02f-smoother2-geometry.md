status: partial
summary:
- Removed Smart downsample refusals; PreRender requests and advertises the complete sampled frame, with ceiling dimensions and 64-bit intermediates.
- Realistic seed 1/n100: 61 exact, 0 mismatches, 0 Mac-only refusals, 39 oracle unavailable (baseline 11/0/50/39).
- Fresh seed 20261024/n100: 55 exact, 0 mismatches, 0 Mac-only refusals, 45 oracle unavailable. All 200 Mac renders succeed.
- Default seed 1/n300 remains 300/300 exact; 105/105 saved corpus comparisons match, including 97 new labelled witnesses.
- Strict ROI/output-allocation fidelity remains unresolved: F52c delivers unequal source/output sizes; this is not evidence of a faithful native AE refusal.

facts:

Production change is confined to `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp::SmartPreRender`.
Classic and the pixel algorithm are unchanged. The existing complete-frame checkout policy is retained,
but the rectangle now uses ceil(full_width * x_num / x_den) and independently ceil(full_height * y_num / y_den).
Positive downsample ratios through 1:1 are admitted. Full-resolution `ref_width/ref_height` remain checked.
No pixel-aspect or extent-based pixel transformation was added.

Commands actually run (from this worktree; TMPDIR was ticket scratch; all drivers are serial):

- `python3 orchestra/reports/P02f-evidence/measure.py --label baseline-realistic`
- `python3 orchestra/reports/P02f-evidence/measure.py --label baseline-default --geometry default --n 300`
- `python3 orchestra/reports/P02f-evidence/measure.py --label candidate-realistic --save`
- `python3 orchestra/reports/P02f-evidence/measure.py --label candidate-fresh --seed 20261024 --save`
- `python3 orchestra/reports/P02f-evidence/measure.py --label candidate-default --geometry default --n 300`
- `python3 orchestra/reports/P02f-evidence/replay.py`: 105/105 saved comparison objects matched (8 existing, 97 new). Explicitly uses F52c, rather than obsolete recorded worker locations; replay provenance records that choice.
- `python3 orchestra/reports/P02f-evidence/roi_probe.py`: full [0,0,7,5] and expanded request [-2,-1,9,7] both return [0,0,7,5], 140 bytes, SHA-256 `bc2eb876877f88980928bd5fe36507a74ca74de698e289d3a2eb9e836ef72178`; subset [2,1,4,3] throws; disjoint request returns empty successfully.
- `python3 orchestra/reports/P02f-evidence/unit_tests.py baseline-units`, `candidate-units`, and `final-units`; results retained separately.
- `OLM_TEST_JOBS=1 python3 -m unittest tests/test_olmsmoother2_roi_fullframe_contract_20260820.py`: 3 tests pass, including ASan/UBSan, PF8/16/32 and divisors 1/2/3/4/8 with an anisotropic 1/3 x 1/2 case.
- `git diff --check`: pass.

The campaigns use the unchanged realistic-v1 sampler, max_size=256, 10-second case timeout,
and registered F52c worker SHA-256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
The AEX SHA-256 is `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
Per-case parameters, geometry, input/output hashes and diagnostics are in compressed result files under
`P02f-evidence/`; source/candidate hashes are in the corresponding provenance JSON.
Default before/after comparison objects are identical for all 300 cases; there is no first mismatch.
First baseline Mac-only refusal: seed 1/index 1, full/sample 1x1, downsample X=1/2 and Y=1/3,
`SmartPreRender:prerender-frame-contract@5321`; the candidate is exact for that witness.
The new corpus is Smart-only; use the supplied replay driver, which preserves each saved route set.

Original arithmetic and ROI evidence:

- Read-only original disassembly/decompilation excerpts and hashes are retained in `P02f-evidence/static.json`.
- Smart worker `0x180001f10` obtains the input/output worlds and calls builder `0x180004e10`.
  That builder allocates its float/class planes using output-world +0x24/+0x28 dimensions.
  It reads Smoothness, Extra Smooth and Smooth Range via integer getter `0x1800014e0` without invoking the inverse-ratio helpers.
- The inverse-ratio helpers at `0x180016870` and `0x1800168d0` have calls in generic parameter-helper functions
  `0x1800078e0`, `0x1800079f0`, and `0x180007b00`. Their existence is not evidence that the smoothing controls require scaling.
- Worker `0x180003eb0` compares the input and all three other image dimensions at `0x180003f16..0x180003f4e`.
  A mismatch branches to `0x180004244`, constructing `std::invalid_argument` from string
  `0x180022410`, decompiled as `Input images do not have the same size.`
- F52c `crates/aex-guest-worker/src/classic.rs:3309` onward reallocates only the output world from PreRender's result rectangle.
  It updates output dimensions/origin, while the checked-out source remains the full sampled world.
  The repeated 7x5 source / 2x2 output probe produces the same `VCRUNTIME exception owned string 0x180022410 is not a live CRT allocation` diagnostic.
  Thus the mismatch reaches an explicit original size check; the exception-transport diagnostic is also emulator-specific.
  Neither result establishes a native AE PF error code or native AE's source checkout dimensions.

Unit baseline/final historical failures (full diagnostics retained in the unit JSON):

- `test_olmsmoother2_ada0_input_differential_20260718.py`: missing retained neighborhood log.
- `test_olmsmoother2_case0012_c280_cce0_mac_helper_boundary_20260718.py`: missing retained parameter JSON.
- `test_olmsmoother2_case07_pf16_unique_public_closure_20260814.py`: stale identity assertions.
- `test_olmsmoother2_case07_public_smart_closure_20260814.py`: identity drift.
- `test_olmsmoother2_case07_unique_direct_oracle_20260814.py`: stale identities.
- `test_olmsmoother2_color_weight_20261001.py`: retained probe dependency hash drift.
- `test_olmsmoother2_current_installed_public_20260813.py`: identity/build-evidence failures including missing SDK Util source in this worktree.
- `test_olmsmoother2_gamma18_keyendpoint_exported_owner_closure_20260812.py`: retained identity validation fails.
- `test_olmsmoother2_gamma_composition_20261001.py`: retained probe dependency hash drift.
- `test_olmsmoother2_key_gamma_hdr_20261001.py`: retained probe dependency hash drift.
- `test_olmsmoother2_pf8_legacy12_public_closure_20260814.py`: stale identity assertion.
- `test_olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.py`: missing retained handoff build identity.
- `test_olmsmoother2_switch_reachability_20261001.py`: retained probe hash drift.

Final unit run: 18 modules, 5 pass and 13 fail; every module has the same failure/error counts as baseline.

The intermediate candidate added an error in the color-weight module because an old negative test
required 1/2 downsample to fail. Its negative input is now a zero denominator; valid preview ratios
are covered positively by the geometry test. No retained hashes or expected pixels were changed.

inference:

- The supported downsample behavior processes the supplied sampled pixels with unchanged smoothing controls.
  Both independent realistic campaigns support this interpretation; they are emulator comparisons, not native AE certification.
- Classify the small-output probe as a **host-triggered unequal-world exception**, not a proven native AE refusal.
  The original size check is real, but whether native AE supplies equal cropped worlds, expanded worlds, or another checkout shape remains unverified.
- Full sampled-frame requests preserve the current unbounded-classifier policy and remove the observed preview black-frame cause.
  They do not reproduce the original's smaller/empty result rectangle negotiation. Successful Mac output on the 84 unavailable oracle cases remains uncompared.
- This is partial, despite meeting the numerical sampled acceptance counts. Removing remaining size/origin checks or inventing a crop algorithm would lack a qualified oracle.

changed_files:
- mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp
- tests/test_olmsmoother2_roi_fullframe_contract_20260820.py
- tests/test_olmsmoother2_color_weight_20261001.py
- tests/fuzz_corpus/olmsmoother2_realistic_P02f/*.json (97 Smart witnesses)
- orchestra/reports/P02f-evidence/* (reproducers, provenance, compressed measurements, static excerpts, unit diagnostics)
- orchestra/reports/P02f-smoother2-geometry.md

verify:

```sh
export TMPDIR="$PWD/orchestra/state/P02f-smoother2-geometry"
export OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/P02f-evidence/measure.py --label verify-realistic
python3 orchestra/reports/P02f-evidence/measure.py --label verify-fresh --seed 20261024
python3 orchestra/reports/P02f-evidence/measure.py --label verify-default --geometry default --n 300
python3 orchestra/reports/P02f-evidence/replay.py
python3 orchestra/reports/P02f-evidence/roi_probe.py
python3 orchestra/reports/P02f-evidence/unit_tests.py verify-units
python3 -m unittest tests/test_olmsmoother2_roi_fullframe_contract_20260820.py
git diff --check
```

Expected: realistic 61 exact/39 unavailable and 55 exact/45 unavailable; zero candidate refusals/errors;
default 300 exact; replay 105/105; ROI probe outcomes described above; geometry tests pass.
Unit modules retain the historical failures listed above; do not interpret the runner's zero exit as an all-tests-pass claim (inspect summary.json).
All drivers run one case/build at a time. No oracle rebuild or installation is required.

next:
- P02f-followup: qualify an oracle that honors source checkout rectangles (requires authorization to change/rebuild the host), or capture native AE source/output world dimensions, origins, rowbytes and PreRender rectangles for the 7x5 -> 2x2 ROI witness.
- Then restore exact original PreRender negotiation and prove cropped/result_rect-sized, empty, and independently expanded output allocations. Keep the current full-sampled implementation as a bounded preview fix until that comparison exists.
- No release gates, ledger entries, other plugins, MAIN or emulator sources were modified; nothing was pushed.
