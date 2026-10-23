status: done

summary:
- Closed three Smart refusal clusters in separate commits: finite Legacy, nonfinite Legacy, nonfinite non-Legacy.
- Seed 1 improves 283/0/17 -> 300/0/0; fresh seed 43 improves 281/0/19 -> 300/0/0 (exact/mismatch/refusal).
- All 564 baseline exact cases are preserved; all 600 final ordinary/sanitized result objects agree.
- Independent matrices and retained controls pass; strict corpus stays 39/39 exact with no rebaseline.
- No numeric core or work-budget change; stop at the three-cluster threshold.

facts:
Base `c1d1f1943e2e3c9ab6e62e1094ba279643f73385`, branch `orch/C32-olmblur-smart-r7`. Read AGENT_GUIDE, OLMBlur ledger restrictions, compatibility plan, GOTCHAS, T09/C05/C10/C12/C15/C21/C24 and F10/F12/F31/F38 reports. No changes to MAIN, emulator, cached workers, release gates, ledger, other plugins, numeric core or work budget. All campaigns use jobs=1; at most two build/emulator workloads. Scratch and compiler temporary files are ticket-local.

Oracle: `/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker`, SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`. Original MAIN `plugins_2025/OLMBlur.aex` SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. Full source/core/candidate provenance and measured transitions are in `orchestra/reports/C32-evidence/`.

First cluster (finite Legacy): extends the existing small-frame Legacy admission to PF32. The existing [-16,16] ARGB source scan, all parameter/world/storage/downsample/work guards and exact-fixture precedence remain. Source samples are never modified. F31 already restored `ucrt_expf` in the PF32 Legacy coefficient builder; F38 already restored generated-NaN signs in the helpers. No arithmetic operation is changed by this ticket.

| Campaign | Baseline E/M/R | Gate-off E/M/R | Finite Legacy E/M/R |
|---|---|---|---|
| seed 1 n300 | 283/0/17 | 300/0/0 | 296/0/4 |
| seed 43 n300 | 281/0/19 | 300/0/0 | 296/0/4 |

All original-route oracle objects and Classic results remain identical. Seed-1 refusals: 13 finite Legacy, 2 nonfinite Legacy, 2 nonfinite non-Legacy. Seed-43 refusals: 15 finite Legacy, 1 nonfinite Legacy, 3 nonfinite non-Legacy. Work-budget refusals: 0 in both measured campaigns; budget unchanged. No first mismatching output or stage exists in these completed gate-off campaigns.

Executed baseline `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0`; sanitized baseline seed43 and gate-off seeds1/43 via `blur_campaign_C12.py`; explicit ticket scratch/report/corpus destinations. Initial gate-off setup failed because the older diagnostic build lacked the new UCRT include tree/library. Added a scratch symlink and UCRT static library link; rerun completed. This was a build-scaffold error, not a numerical hypothesis or permission rejection.

Independent original-AEX matrices via `verify_blur_C32.py` (F32, serial, ASan/UBSan, odd strides, full public Smart entry):
- Finite Legacy: 720 exact; 480 prior exact unchanged, 240 refusals become exact. Six geometries, ten Amount values including adjacent FLOAT32 boundaries and 1000, Repeat 1/2/3/4/9/10, both Bias values, Smoothness 1/62.5/100, independent signed HDR random/edge sources in [-16,16], signed zeros/subnormals.
- Nonfinite diagnostic: 384 exact; 193 prior exact unchanged, 191 refusals become exact. Four geometries, four Amounts, three Repeats, both Bias/Legacy modes, signed infinities, distinct signed quiet/signaling NaNs, plus mixed finite/HDR/subnormal inputs. This supplements an initial 192-row all-nonfinite run, also exact; final committed evidence is the expanded run.
- Each matrix's retained positive replay: 80/80 exact, exit 0, empty sanitizer stderr. Source, guards, callback lifecycle and padding assertions are inherited from the public hosts. Leak detection is disabled; ASan/UBSan abort on findings.
- Seven existing Classic/generic unit checks pass. Python AST syntax, shell syntax and `git diff --check` pass.

inference:
The prior C24 math/oracle barriers have been resolved sufficiently for these measured admission domains by F31/F32/F38. The evidence supports widening the general gate; it is not a new numeric fix or proof of arbitrary native Windows/AE/GPU behavior. Larger finite PF32 values remain outside the small-frame verified domain. No per-case/coordinate/output correction is used.

changed_files:
- mac/OLMBlur/OLMBlur.cpp — finite PF32 Legacy admission.
- tools/fuzz/blur_campaign_C12.py — UCRT include tree for scratch variants.
- tools/fuzz/triage_olmblur.py — UCRT library linkage for diagnostic builds.
- tools/fuzz/verify_blur_C32.py — independent serial sanitized matrices and retained replay.
- tools/fuzz/summarize_blur_C32.py — strict campaign/oracle/exact-preservation and corpus assertions.
- tools/fuzz/recheck_blur_C32.sh — serial sanitized campaign/replay driver.
- orchestra/reports/C32-evidence/*.json — measured provenance, transitions and matrices.
- orchestra/reports/C32-olmblur-smart-r7.md — report.

verify:
From this worktree, at the first-cluster commit:
```sh
bash tools/fuzz/recheck_blur_C32.sh finite
s="$PWD/orchestra/state/C32-olmblur-smart-r7"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/legacy-recheck.json" --before c1d1f194 --mode legacy --require-exact
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/nonfinite-recheck.json" --before c1d1f194 --mode nonfinite --gate-off --require-exact
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820
```
Expected campaigns 296/0/4 each; strict corpus replay 39/39 unchanged; finite matrix 720/720, diagnostic nonfinite 384/384, retained80/80 per matrix, seven tests pass. Full campaign logs remain in scratch. No rebaseline command is needed.

next:
Promote nonfinite Legacy, then nonfinite non-Legacy as separate clusters, retaining the finite magnitude boundary and all work/storage guards.

Second cluster — nonfinite Legacy (predecessor `705558c9`):

facts:
The source predicate now accepts exponent-all-ones PF32 words for Legacy, preserving their bits, while retaining [-16,16] for finite words. Quiet/signaling NaNs and infinities take the normal renderer; no canonicalization or output patch is introduced. Non-Legacy retains its previous finite-only gate. Existing diagnostic bypasses accept the additional source-policy argument.

Independent production Legacy-only matrix: 192/192 exact, 99 prior exact unchanged and 93 refusal->exact; retained80/80, empty sanitizer stderr. Unlike the earlier gate-off matrix, this uses the actual production admission. Larger finite inputs are tested separately; the bound is unchanged. Seven static source-contract tests remain applicable.

changed_files (second cluster):
- mac/OLMBlur/OLMBlur.cpp — Legacy-only nonfinite source admission using raw exponent classification.
- tools/fuzz/blur_campaign_C12.py and tools/fuzz/verify_blur_legacy_C15.py — diagnostic source-scan bypass accommodates the policy argument.
- tools/fuzz/verify_blur_C32.py — per-Legacy-mode production matrix and out-of-domain probes.
- orchestra/reports/C32-evidence/legacy*.json and this report.

verify (second-cluster commit):
```sh
bash tools/fuzz/recheck_blur_C32.sh legacy
s="$PWD/orchestra/state/C32-olmblur-smart-r7"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/legacy-production-recheck.json" --before 705558c9 --mode nonfinite --legacy-value 1 --require-exact
```
Expected matrix192/192 and retained80/80; corpus39/39 unchanged. Campaign counts below are recorded after completion.

Additional second-cluster verification: 32 independent out-of-domain source cases (next FLOAT32 above +16, below -16, positive/negative maximum finite, each ARGB channel and both Legacy modes) remain refusal->refusal, with successful AEX renders. Retained80/80 passes again. Seven source-contract unit tests pass. First-cluster corpus table is 39 exact->exact, zero other changes; no rebaseline was performed.

Second-cluster campaign results: seed1 296/0/4 -> 298/0/2 (two admissions); seed43 296/0/4 -> 297/0/3 (one admission). All 592 predecessor exact cases are preserved; original-route oracles and Classic results unchanged. These are sanitized production campaigns, not gate-off totals.
Second-cluster strict replay: 39/39 matches_saved, 39 exact->exact, zero expectation changes. `summarize_blur_C32.py --phase legacy --previous finite` passes all preservation assertions. No production sanitizer finding.

Third cluster — nonfinite non-Legacy (predecessor `0286619e`):

facts:
Both PF32 modes now use the verified exponent-all-ones source admission; the temporary Legacy-only boolean is removed. Finite words still require [-16,16]. No numerical core or work-budget change. Production non-Legacy matrix192/192 exact: 97 prior exact unchanged, 95 refusal->exact; retained80/80 exact with empty sanitizer stderr. Seven existing source-contract tests pass.

changed_files (third cluster):
- mac/OLMBlur/OLMBlur.cpp — non-Legacy nonfinite source admission, comments updated.
- orchestra/reports/C32-evidence/nonlegacy-nonfinite-matrix.json, final campaign evidence, and this report.

verify (final revision):
```sh
bash tools/fuzz/recheck_blur_C32.sh final
s="$PWD/orchestra/state/C32-olmblur-smart-r7"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/nonlegacy-production-recheck.json" --before 0286619e --mode nonfinite --legacy-value 0 --require-exact
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/outside-recheck.json" --before c1d1f194 --mode outside
for seed in 1 43; do
 python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed "$seed" --jobs 1 --worker /Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker --shrink-attempts 0 --scratch "$s" --corpus "$s/normal-corpus" --report "$s/normal$seed.json" > "$s/normal$seed.log" 2>&1
done
```
Expected production matrix192/192 exact; out-of-domain32/32 refused; retained80/80 per matrix. Final campaign and replay measurements are recorded below after completion.

Final campaign facts:

| Seed | Ticket baseline E/M/R | Finite Legacy | Nonfinite Legacy | Final / normal O2 |
|---|---|---|---|---|
| 1 | 283/0/17 | 296/0/4 | 298/0/2 | 300/0/0 |
| 43 | 281/0/19 | 296/0/4 | 297/0/3 | 300/0/0 |

All 600 final normal-O2 and ASan/UBSan result objects are identical, including Classic and both original-route oracle objects. No admitted mismatch, sanitizer error, or work-budget refusal appears in these campaigns. Third-cluster exact preservation is 595/595; transitive baseline exact preservation is 564/564. These are measured local CPU-AEX/fake-host results, not full-domain/native-AE completion.

Execution note: while the final shell driver was running, adding explicit F32 selection changed its text. Bash completed both campaigns but then failed to parse the replay command (`unexpected EOF while looking for matching quote`). The final script passes `bash -n`; the already completed 600 campaign results were retained and the exact replay command was run separately. No numeric hypothesis, oracle, source expectation or renderer was changed to address this shell failure. Final comparisons and corpus assertions are run after the standalone replay completes. Earlier first/second-cluster shell drivers completed normally.

Third-cluster tool changes also pin F32 explicitly in the reproduction driver/matrix tool and assert ordinary/sanitized equality in `summarize_blur_C32.py`. Corpus replay intentionally uses each saved record's hash-bound worker, including historical workers, rather than replacing its oracle contract.

Final inference / next:
- Three refusal clusters are closed in separate commits; stop at the ticket threshold. No remaining seed1/43 Smart residual is observed.
- Small-frame finite values beyond [-16,16], arbitrary larger-image source domains, ROI/downsample, native AE/GPU and full Windows dependency equivalence remain outside this promotion. A future ticket may investigate wider finite PF32 admission; do not change the pending work-budget policy.
- No core/worker arithmetic or saved corpus expectation changed. No release/ledger/other-plugin/MAIN changes, push, stash, history rewrite or emulator rebuild.

Final verification completed: standalone sanitized corpus replay39/39 matches_saved, all39 Smart exact, no rebaseline. Both final aggregator invocations pass (`--previous legacy` and `--previous base`). Final expected campaign result is300/0/0 for each seed in both build modes. Per-commit corpus table:39 exact->exact at finite, Legacy-nonfinite and final revisions, zero changed expectations. All Python syntax checks, shell syntax and `git diff --check` pass. Scratch is11,549,983 bytes; no regenerable build directory or task background process remains. All started emulator/build commands completed. No permission rejection occurred.

Evidence recheck after the full commands above, if baseline and predecessor scratch reports are retained:
```sh
python3 tools/fuzz/summarize_blur_C32.py --scratch orchestra/state/C32-olmblur-smart-r7 --phase final --previous legacy --report orchestra/state/C32-olmblur-smart-r7/verified-final.json
python3 tools/fuzz/summarize_blur_C32.py --scratch orchestra/state/C32-olmblur-smart-r7 --phase final --previous base --report orchestra/state/C32-olmblur-smart-r7/verified-transitive.json
```
Expected predecessor preservation595/595; baseline preservation564/564; refusal->exact2+3 and17+19 respectively; all600 ordinary/sanitized result objects identical and strict corpus39/39.
