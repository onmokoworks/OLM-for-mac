status: done
summary:
- F53 confirms original cropped-input PreRender returns checkout availability, keeps full max bounds, and renders successfully.
- Mac now forwards the requested rectangle and propagates checkout result/max bounds; the equal-world guard is retained.
- Matching nonzero world origins are accepted; the numeric kernel is unchanged.
- Four crop witnesses and 1,000 generated Smart cases have zero mismatches and zero Mac-only refusals; default has zero exact-to-non-exact regressions.
- All 112 corpus cells replay true on both recorded routes; unit modules retain the baseline 5 pass / 13 fail limitation.

facts:

- Read AGENT_GUIDE.md, plugin ledger rows, GOTCHAS.md, compatibility plan, P04c and F53 reports. `memory_pressure` reported 57% free before and during work. Commands use one job, at most two concurrent test/build processes. No oracle rebuild.
- F53 worker SHA256 `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`; AEX SHA256 `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`. Full dependencies and hashes are in `P04c2-evidence/*provenance.json` and campaign reports.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/P04c2-evidence/probe.py --plugin olmsmoother2 --label baseline` was run on unchanged production source, then `--label fixed` on the final source. The script now records both routes; the initial baseline recorded Smart only. Inputs are deterministic `(j*17+31)%256`, PF8, defaults, full layer 40x30, 1:1 sampling. Explicit checkout payload is 20x15; automatic checkout starts from full 40x30 storage. Origins are (0,0) and (3,4).
- All four original calls returned result equal to checkout (`[0,0,20,15]` or `[3,4,23,19]`), max `[0,0,40,30]`, flags 0, then rendered with intact guards and clean sessions. Explicit origin-zero and nonzero outputs share SHA256 `3b82d61392ce504baf7bf23c3ce753f16d6c31fe8bddca9e24c1843824c4685f`. Automatic origin-zero SHA256 `5fb8f554a7952b6b9ac422e8fc8b9d48e446256e085a8c5adec72db2a06d73c0`; automatic nonzero SHA256 `d7edd9b862bf0d24d64f8ae24176a8aa4ea31b9a38de5018b00c0cf993ccd108`.
- Baseline Mac: two explicit-crop refusals at `ValidatePublicWorlds:validate-world-shape@5240`, two automatic-crop mismatches. First automatic mismatch: expected 1,200 bytes, actual 4,800; 4,708 differing bytes; first byte 72, expected `d8`, actual `e7`; expected rect `[0,0,20,15]`, actual `[0,0,40,30]`. Final Mac: four Smart exact, matching rectangles and hashes. Classic remains refused, outside this plugin's Smart contract.
- Initial default experiment exposed the plugin-only harness's uninitialized (empty) output request: 300 Smart refusals. The host now explicitly supplies `{0,0,w,h}`. No production fallback for an empty request was added. The initial counts are retained in `initial-empty-request.json`. The subsequent corrected run is 300/300 exact.

`campaign.py` invokes standard `tools/fuzz/run.py` serially, with `--jobs 1 --budget-minutes 25 --shrink-attempts 0`, both routes. Exact commands and exit codes are retained in `campaign-summary.json` (default row names its corrected rerun). The CLI spelling `--geometry realistic` selects realistic-v1.

| Smart campaign | n | exact | original non-success / Mac refusal | mismatches | Mac-only refusals |
|---|---:|---:|---:|---:|---:|
| default seed 1, before | 300 | 300 | 0 | 0 | 0 |
| default seed 1, final | 300 | 300 | 0 | 0 | 0 |
| realistic-v1 seed 1 | 100 | 61 | 39 | 0 | 0 |
| realistic-v1 seed 20261025 | 100 | 59 | 41 | 0 | 0 |
| realistic-v2 seed 1 | 100 | 100 | 0 | 0 | 0 |
| realistic-v2 seed 20261025 | 100 | 100 | 0 | 0 | 0 |
| odd-even-v1 seed 2026 | 150 | 81 | 69 | 0 | 0 |
| odd-even-v1 seed 2027 | 150 | 76 | 74 | 0 | 0 |

Odd-even uses `--geometry realistic --size-sampler odd-even-v1 --max-size 623`, matching T15b. Original non-successes are reported as `reject` by the runner; they are not successful comparisons or proven returned plugin PF_Err refusals. Default per-index baseline/final comparison: 0 exact-to-non-exact. Classic is refused in all generated cases, as before; this is not a Classic conformance claim.

Standard `--replay` reports are true for existing base 8, T15b 3, P02f 97, and new labelled P04c2 4 cells (112 total), including both recorded routes. No existing expected results were rewritten.

`OLM_TEST_JOBS=1 python3 orchestra/reports/P04c2-evidence/unit_tests.py baseline-units` and `final-units` run all 18 plugin modules serially. Both: 5 pass / 13 fail, same module exit codes. Retained-artifact omissions and source/dependency identity checks account for existing failures; diagnostic tails are committed. The updated ROI contract module passes and runs its C++ probe under ASan/UBSan, covering returned bounds, empty content, matching origins and mismatched-origin rejection. This is not an all-unit-tests-pass claim.

inference:

- For these cropped-input layouts, the old Mac full-frame negotiation was the cause of unequal worlds and refusals. The original performs work on the supplied crop; equivalence to rendering a full frame and cropping afterward is not its demonstrated contract.
- Propagating availability and accepting equal nonzero origins reproduces the measured behavior without changing arithmetic or weakening the equal-dimension guard. Unequal input/output worlds remain rejected.
- Full-resolution reference dimensions do not determine the output allocation. The original's result and max bounds have distinct roles.
- Evidence is CPU Software AEX emulation plus the production Mac source host, not native AE/GPU or installed-bundle certification. `preserve_rgb_of_zero_alpha` retains its previous policy; this ticket measured rectangle negotiation.

changed_files:
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`
- `tools/emulation/olmsmoother2_public_key_gamma_harness_20261001.cpp` (plugin-only request initialization)
- `tests/test_olmsmoother2_roi_fullframe_contract_20260820.py`
- `tests/fuzz_corpus/olmsmoother2/P04c2-cropped-checkout/*.json` (four labelled witnesses)
- `orchestra/reports/P04c2-evidence/` (drivers, before/after observations, provenance, campaign/replay results, unit diagnostics)
- `orchestra/reports/P04c2-smoother2-checkout-negotiation.md`

verify:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/P04c2-evidence/probe.py --plugin olmsmoother2 --label verify
PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/P04c2-evidence/campaign.py
OLM_TEST_JOBS=1 python3 orchestra/reports/P04c2-evidence/unit_tests.py verify-units
git diff --check
```

Expected: witness Smart 4 exact; campaign counts as above, no Smart mismatches or Mac-only refusals; all four standard replay directories true; units 5 pass / 13 existing fails (runner exit 0 means recorded, not all passed); whitespace check succeeds. Drivers redirect child output to ticket scratch and remove temporary build directories. No background task is needed for reproduction.

next:
- Separate maintenance ticket: restore missing retained unit artifacts and reconcile old source-bound attestations without changing release gates here.
- Native AE checkout scheduling remains a separate validation boundary. No remaining cropped-checkout source mismatch was found in this ticket's tested scope.
- No MAIN, external emulator source/cache, ledger, release gate, other plugin sources, or existing corpus expectations changed; no push.
