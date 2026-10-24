status: done
summary:
- Restored original full-layer Smart checkout negotiation, rectangle union, and RETURNS_EXTRA_PIXELS.
- Smart ignores extent_hint for filtering, as the original workers do; numerical/downsample/Legacy radius-zero code is unchanged.
- Realistic-v1 seed 1 and fresh seed 20261025: each Smart 100 exact, 0 mismatches/refusals/unavailable.
- Default seed 1/n300: all result objects unchanged; all 118 corpus cases replay match saved.
- Unit file outcomes unchanged; sanitizer passed. Classic was not changed.

facts:

Original binary evidence (MAIN read-only, excerpts in `P02h-evidence/original-geometry-disassembly.txt`):
- `entryPointFunc` SmartPreRender, 0x18000ab01..0x18000ab85: loads InData width/height at +0xfc/+0x100, constructs [0,0,width,height], calls rectangle union 0x18000bd90 on the incoming request, and passes the expanded request to checkout_layer. It does not downsample those bounds or apply pixel aspect.
- 0x18000ab94 writes the 16-bit flag 1 at PreRenderOutput+0x22 (SDK RETURNS_EXTRA_PIXELS). 0x18000aba5/0x18000abba union the checkout result/max-result rectangles into the output.
- 0x18000bd90..0x18000be04 implements min-left/top, max-right/bottom union with empty-rectangle handling, reproduced directly in the plugin.
- Worker decomp `FUN_180002280` reads input width/height (+0x24/+0x28) and processes the full input; its output writer indexes world-local coordinates. The existing generic extent guard was not an original filtering rule. No pixel-aspect arithmetic was added.

Executed commands/results (all serial internally, at most two processes concurrently):
- `python3 orchestra/reports/P02h-evidence/check.py baseline`: baseline realistic-v1 seed 1/n100 Smart 30 exact / 70 refusals / 0 mismatches; original Smart available for all 100. Refusals: generic-input-world 55, generic-output-world 15. First refusal index 0: PF8, sampled 11x7, full 21x19, downsample X=1/2 Y=1/3, extent [9,0,10,6], request [5,4,6,5]. Original negotiates output [0,0,11,7], SHA256 `ed1807b58ba4784ae8434ba3b99b7fd5a50c17be298eeae473e34fbf22faad2a`.
- `python3 orchestra/reports/P02h-evidence/check.py candidate` and `... candidate --fresh`: final realistic-v1 seed 1 and 20261025 each Smart 100/100 exact, zero refusal/mismatch/unavailable. First pixel mismatch: none. The first baseline-refused case now has the same original output rectangle and raw hash. Classic results remain outside this ticket's contract: seed 1 raw 3 exact/97 refusals with 17 unavailable oracles; fresh 6 exact/94 refusals with 23 unavailable oracles.
- Default seed 1/n300 before/after: 300 identical complete result objects; Smart 300 exact; exact-to-nonexact 0. Classic 13 exact/287 raw refusals, 93 unavailable oracles, unchanged.
- Final candidate executable SHA256 `e55dc3cbdff56c4839507c73147f7fdecdff34c5639d5f22628ee01785b651be`; source SHA256 `9c4245d786ae88f677f971d086d8709aea763c23cdceeb12a632b7277fb944da`. All three final campaigns record those hashes. F52c worker SHA256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`; AEX SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/P02h-evidence/corpus.py`: saved 36 labelled realistic-v1 cases, covering all 3 depths x 2 Legacy states x 6 padding choices. Packed inputs, geometry, result and worker provenance are committed separately from older corpus sets.
- `python3 orchestra/reports/P02h-evidence/replay.py`: olmblur 39/39, olmblur_downsample_P01a 43/43, olmblur_realistic_P02h 36/36 match saved. No older corpus modified.
- `python3 orchestra/reports/P02h-evidence/check.py baseline --units` and `... candidate --units`: 34 isolated serial unittest files; before and after 7 exit 0, 24 exit 1, 3 exit 5, no per-file exit change. Full diagnostics retained in units-{baseline,candidate}.json. Failures include absent historical artifacts, source/runner hash expectations and old source-text contracts.
- Free functions additionally invoked directly: ROI 5/5 pass; historical case0001 2 failures, consistent with P01a. ASan/UBSan production probe command below exits 0 (six odd-geometry cases).
- `git diff --check`: exit 0. Scratch is below 5 GiB; temporary build trees cleaned. No oracle rebuild, MAIN modification, gate/ledger edit, AE launch, push, or background process left running.

Historical unittest files returning 1, unchanged:
- `test_olmblur_16bpc_typed_exact_contract_20260805.py`
- `test_olmblur_8_16bpc_max1_residual_family_20260718.py`
- `test_olmblur_classic_current_install_smoke_20260812.py`
- `test_olmblur_classic_public_entry_closure_20260812.py`
- `test_olmblur_classic_public_real_sdk_20260813.py`
- `test_olmblur_colorkey_classic_render_bitdepth_dispatch_20260716.py`
- `test_olmblur_current_installed_complete_admission_union_20260813.py`
- `test_olmblur_current_installed_public_closure_20260813.py`
- `test_olmblur_pf16_7x5_public_admission_20260813.py`
- `test_olmblur_pf16_7x5_universal_candidate_20260813.py`
- `test_olmblur_pf16_legacy_retained_universal_candidate_20260813.py`
- `test_olmblur_pf16_retained_repeat2_universal_candidate_20260813.py`
- `test_olmblur_pf16_worker_sources_public_admission_20260813.py`
- `test_olmblur_pf16_worker_sources_universal_candidate_20260813.py`
- `test_olmblur_pf32_retained_public_closure_20260813.py`
- `test_olmblur_pf32_retained_universal_candidate_20260813.py`
- `test_olmblur_pf32_retained_universal_candidate_v2_20260813.py`
- `test_olmblur_pf8_retained_exported_public_owner_20260813.py`
- `test_olmblur_pf8_retained_public_admission_20260813.py`
- `test_olmblur_pf8_retained_universal_candidate_20260813.py`
- `test_olmblur_retained_public_universal_candidate_v3_20260813.py`
- `test_olmblur_retained_public_universal_candidate_v4_20260813.py`
- `test_olmblur_smart_public_admission_20260813.py`
- `test_olmblur_smart_public_admission_build_20260813.py`

inference:
- The output-world refusal was caused by incorrect PreRender negotiation: passing an ROI through allocated a smaller output than the full-input worker supports. Restoring the original full-layer checkout closes it without inventing cropped-filter arithmetic or weakening the equal-world storage safety checks.
- Expanded result bounds, non-full extents, padding, downsampling and aspect choices in realistic-v1 are now exact in the sampled domain. This is local software-oracle evidence, not native AE validation or a claim for arbitrary malformed/cropped worlds outside the original negotiation.
- No hypothesis was refuted: the first binary-grounded implementation closed all 70 observed refusals.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp`
- `tests/fuzz_corpus/olmblur_realistic_P02h/*.json` (36)
- `orchestra/reports/P02h-evidence/*` (reproduction drivers, baseline/candidate/replay results, diagnostics, original instruction excerpt)
- `orchestra/reports/P02h-blur-geometry.md`

verify:

From this worktree:
```sh
export TMPDIR="$PWD/orchestra/state/P02h-blur-geometry"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/P02h-evidence/check.py candidate
python3 orchestra/reports/P02h-evidence/check.py candidate --fresh
python3 orchestra/reports/P02h-evidence/replay.py
python3 orchestra/reports/P02h-evidence/check.py candidate --units
CPLUS_INCLUDE_PATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources' python3 tests/test_olmblur_generic_beta_sanitizers_20260820.py
git diff --check
```
Drivers use `tools/fuzz/run.py --plugin olmblur --geometry realistic --n 100 --seed {1,20261025} --jobs 1 --shrink-attempts 0` and default seed 1/n300, with ticket-local scratch/report paths. This uses the same qualified realistic-v1 sampler as measure_F52c.py and the registered F52c worker, without rebuilding it.
Expected: Smart 100 exact for each realistic seed; default Smart 300 exact; corpus 39+43+36 match; unittest counts above (driver records failures rather than treating them as passes); sanitizer and diff check exit 0.

next:
- Orchestrator review/merge; validate zoomed/partly-visible comps and 1/2, 1/4 previews in native AE 26.3.
- Historical fixture maintenance and Classic ABI work remain separate tickets.
