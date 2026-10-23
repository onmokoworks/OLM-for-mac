status: blocked
summary:
- Rewrote the five generic admission entries for R02/F41b, retaining Classic refusals and storage/control checks.
- Replayed and rebaselined 64 Kira files with R04 history; all 111 Smart results are exact.
- Fixed real-pytest skipif interop; skipped functions remain incomplete (exit 77).
- Supplemental AEX checks: 50 exact; Radial witness 62 uncompared with two workers. Stopped and retained both failures.
- No production or link-recipe changes.

facts:

- `bash scripts/setup_ae_sdk_links.sh` succeeded, creating worktree-only SDK links.
- `tools/fuzz/rebaseline_R04.py --use-reports --apply` used completed original-AEX replays and the existing `rebaseline_corpus.py --production-rebaseline R04`. 64 changed files: Smart 46 refusal→exact and 18 mismatch→exact. The other 47 remained exact. Classic: 31 mismatch→refusal, 21 mismatch→mismatch (ten in migrated nested files), 59 refusal→refusal. Primary oracle objects were unchanged. Missing `oracles` objects came from replay, not manual edits. Every changed file and its before/after result is retained in `R04-corpus-transitions.json` and listed below.
- Fresh `tools/fuzz/rebaseline_R04.py` after migration: zero changed results across 111 cases; Smart 111 exact, Classic 21 mismatch / 90 refusal. No Smart mismatch or downgrade; no first differing byte.
- Initial real-pytest invocation was unavailable (`No module named pytest`); installed pytest only under ticket scratch. The first rewritten suite had 36 pass / two shared ColorKeep failures because the new full-frame flag check expected zero iterator calls. Diagnostic showed all five outputs/canaries exact with `ih=1`; corrected the lifecycle assertion to one, without changing pixel expectations.
- Six affected test modules under real pytest: **39 passed, 16 subtests passed**, 22.17 seconds. After extending the Radial side/area Smart-versus-Classic checks: its test passed again in 3.99 seconds.
- Stdlib gate loader: **21 tests passed**, exit 0. The existing true-skip regression now raises if incorrectly executed; added true/false string-mark coverage. Both true skips return 77 and false conditions execute normally.
- ColorKeep's five DEEP-bit mutations now require successful rendering, exact bytes bound to retained actual-AEX input/output SHA-256 values, padding/header/input integrity, and checkout/checkin/iterator counts. The negative matrix still has 49 expectations: 44 refusals plus five exact renders. Generic and ROI gate entries share this check.
- Policy comments cite R02 merge `8857fbc3077b355f036b0ea2dadc846a9cf507bd` and F41b merge `7a0cd797d52c9564c1f89191488f095c73f11b02`.
- Supplemental verification initially failed to serialize raw input bytes; fixed the evidence writer to record input SHA-256. A repeat exposed an existing Radial build directory; the driver now clears only its regenerable plugin scratch before compiling. Neither was a pixel failure.
- `tools/fuzz/verify_admission_R04.py`: 48 ColorKeep Smart flag combinations (all 3 depths × 4 input flags × 4 output flags), one Blur and one Distance seed-777 Smart render are exact; zero measured byte differences in these 50 cases. Radial 62 is uncompared; 104/235 were not attempted after the fail-closed assertion.
- The first supplemental Radial seed-1/index-62 run with current F46 worker returned before guest completion at RIP `0x180001df0`; candidate rendered with SHA-256 `d3d08c4296f99ebc15bfa4e2cb2d9c2dc9890e68802bbcc177a5187d08027042`. Status **uncompared**, not exact and not a measured mismatch. Its diagnostic is preserved in the verification artifact. The final driver uses F41b's recorded F32 worker for its Radial witnesses; all other supplemental witnesses use current F46. The retained F32 retry also stopped, at RIP `0x1800020d2`, with the same candidate hash. Both full diagnostics and provenance are in `R04-verification.json`. No additional hypothesis/retry was attempted; the required Radial exact-output evidence could not be completed, so this ticket is blocked despite its passing assertion/loader/corpus checks.
- Removed regenerable replay/admission build directories; remaining scratch is 17 MiB, including logs and the scratch-only pytest installation. No background process remains.
- Tests/replays use ticket-local TMPDIR and serial emulator calls (`--jobs 1`), with `OLM_TEST_JOBS=2` as requested. MAIN and emulator source remain read-only. Pytest was installed only into ticket scratch because MAIN's Python has no pytest. No release gate, ledger, plugin production or link-recipe edits; no push/stash/history rewrite.

inference:

The failures were stale admission expectations and loader interoperability, not evidence of a new Smart byte regression. Blur/Distance source-contract tests retain their original structural scope; Radial's budget probe checks admission without allocating/rendering UHD frames. Supplemental exact renders are finite witnesses, not proof of all newly unbounded sizes/workloads. Classic Kira mismatches remain visible and need separate investigation. The current-worker Radial oracle stop remains outside exactness claims.

changed_files:

- `scripts/run_olm_generic_beta_gate.py`
- `tests/test_run_olm_generic_beta_gate.py`
- `tests/test_colorkeep_roi_tile_beta_20260820.py` (also fixes the generic entry's shared invocation)
- `tests/test_olmblur_generic_beta_lane_20260820.py`
- `tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py`
- `tests/test_olmradialblur_generic_budget_20260821.py`
- `tools/fuzz/rebaseline_R04.py`
- `tools/fuzz/verify_admission_R04.py`
- `orchestra/reports/R04-corpus-transitions.json`
- `orchestra/reports/R04-verification.json`
- `orchestra/reports/R04-assertion-drift-and-corpus.md`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000000_7b627ae38e84.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000019_adfc483da30a.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000037_5519cfe5118f.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000041_7a92937fc12d.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000054_355f2250700a.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000061_40fe8eb50b78.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000062_b6bb40614122.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000073_4f1e82dc18ba.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000076_61a73c823feb.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000108_9332f7469a93.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000129_159b5af62622.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000136_35a64376a42c.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000157_83728685d1c5.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000176_ed932f6d4eb0.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000187_0d2cbbba5947.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000193_4cf67a0bac86.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000208_4be8b44983da.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000214_6020fd6e3138.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000215_d81b5494a2ea.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000218_c8559073f5c3.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000262_8ffc7f00a26a.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000282_c2aada9e34cb.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000288_b4089a689802.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000008_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000026_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000031_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000034_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000035_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000036_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000040_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000044_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000046_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000047_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000055_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000058_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000063_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000065_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000070_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000084_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000091_adfc483da30a.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000098_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000112_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000113_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000133_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000140_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000151_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000153_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000163_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000174_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000177_ed932f6d4eb0.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000180_96ddd38c09b6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000195_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000200_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000213_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000222_92552f06afe6.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000236_adfc483da30a.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000237_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000239_83728685d1c5.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000247_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000250_83728685d1c5.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000261_ced0f1718a01.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000263_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000267_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions/seed1_case000289_ced0f1718a01.json`

verify:

Run from this worktree (commands are sequential):

```sh
S="$PWD/orchestra/state/R04-assertion-drift-and-corpus"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=2
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
bash scripts/setup_ae_sdk_links.sh
"$PY" -m pip install --target "$S/pytest" pytest > "$S/pip.log" 2>&1
export PYTHONPATH="$S/pytest"
"$PY" -m pytest -q tests/test_colorkeep_generic_beta_20260820.py tests/test_colorkeep_roi_tile_beta_20260820.py tests/test_olmblur_generic_beta_lane_20260820.py tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py tests/test_olmradialblur_generic_budget_20260821.py tests/test_run_olm_generic_beta_gate.py > "$S/tests-final.log" 2>&1
"$PY" scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_run_olm_generic_beta_gate.py > "$S/stdlib-loader.log" 2>&1
"$PY" tools/fuzz/rebaseline_R04.py > "$S/recheck.log" 2>&1
"$PY" tools/fuzz/verify_admission_R04.py > "$S/admission.log" 2>&1
git diff --check
```

Expected: pytest 39 tests pass; stdlib loader 21 tests pass; corpus audit `changed: 0`, Smart exact 111, Classic mismatch 21 / refusal 90. The supplemental driver currently exits 1 at Radial index 62 after reporting 48+1+1 exact cases; expected retained result is uncompared at RIP `0x1800020d2` (the stop location may vary with execution resources). It fails closed on any non-exact result. Inspect reference-worker provenance and logs. Use `--apply` only to reproduce the migration on the pre-R04 parent, not for verification of this commit.

next:

Orchestrator: merge alongside R03's link repairs and rerun the aggregate generic gate. Resolve the Radial original-worker guest-stop boundary and complete the supplemental exact-output assertions before marking R04 done. Existing Kira Classic mismatches require a separate ticket; no production fixes or evidence suppression belong to R04.

orchestrator note: the supplemental driver now asserts Radial seed1/148 (C49) exact under F46 and accepts only an original guest stop for 62/104/235. Orchestrator run: 148/104/235 exact, 62 uncompared (oracle stop); ColorKeep 48, Blur 1, Distance 1 exact. Unblocked.
