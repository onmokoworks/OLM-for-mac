status: partial

summary:
- Cluster 1: admit finite-SDR PF32 Smart Power through the already-supported identity/Box/Gaussian/small-Median filter rules using shared UCRT math.
- Seed 1 Smart exact 287→290; fresh seed 32 exact 281→282. No prior exact changes, no admitted mismatch.
- All 1260 independent Power cases match AEX and ASan/UBSan; five excluded controls remain refused; corpus 145 remains exact.
- PF16 mask conversion is under separate investigation; no PF16 production change in this commit.

facts:
- Initial HEAD `3781f6320be08bb475dbbc39d2cb192808ce7c40`, branch `orch/C31-dg-smart-r6`. Read shared guide, GOTCHAS, plugin forbidden-action row, compatibility plan and T07/C03/C08/C14/C19/C27/F10/F12/F31/F37 reports. MAIN and emulator sources remain read-only; no worker rebuild, push, stash or history rewrite.
- F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. These are CPU Unicorn/public SDK-shim results, not native AE certification.
- Initial default-shrinking run was interrupted after it spent time reducing unrelated Classic mismatches; no completed result is claimed. The no-shrink rerun completed all 300: Smart 287 exact/0 mismatch/6 refusal/7 uncompared, AEX Smart 290 successful/8 rejected/2 budget. Only successful-reference refusals are indices 124/125/180, all Power. Remaining refusals 53/189/192 have rejected AEX references.
- Scratch gate-off at indices 124/125/180: all three exact and sanitizer-identical. The old variant builder initially failed to resolve `../../ucrtmath/include/ucrtmath.h`; the helper now relocates this include just like its existing core includes. No production behavior is changed by this helper repair.
- Broad Power admission including Bilateral is rejected by independent 7x1/Inside/RGB/Size1/Power0.01: original first differing word `475eec3d`, candidate `00000000`, byte4/word1, 37 bytes/10 words different. Sanitized candidate agrees with ordinary candidate. This diagnostic never enters production.
- Final rule leaves Bilateral excluded. It also excludes newly admitting Median Size>2, following the previously witnessed original CV_8U assertion boundary. It copies parameters only for filter admission; rendering retains the actual Power mode and exponent. Existing Power source/layout guards retain finite SDR. Finite exponent range is [0.01f,5.0f]; other owner/control/work-budget guards remain.
- Independent matrix: 1260 exact, all sanitizer-identical. Three geometries (7x1/1x7/7x3), all ownership modes, RGB/Layer, both backgrounds, five exponent boundary values (0.01, neighbors of 1, 2.25, 5), identity and Box/Gaussian/Median filters, odd padding. Final narrowed candidate replays all 1260 original hashes exactly; five Bilateral/Median3/Median500/out-of-range exponent controls remain unchanged refusals. No tolerance or output-byte correction is used.
- Before/current/sanitized-current verification covers all 300 seed1 and all 300 seed32 cases, plus corpus145. Seed1: 287 unchanged exact, 3 refusal→exact, 10 unchanged nonexact. Seed32: 281 unchanged exact, 1 refusal→exact (index180), 18 unchanged nonexact. A first fresh-seed sanitizer run hit a 30-second wall timeout, not a sanitizer diagnostic; rerun with 180-second per-render allowance completed. Leak detection disabled.
- Fresh seed32 baseline: 281 exact/1 mismatch/12 refusal/6 uncompared. Its existing PF16 case96 mismatch is unchanged by Power admission (4 words, first byte202024/word101012, original `5027`, Mac `d332`). Its independent mask investigation is not part of the Power change.
- Beta tests: 9 run, OK, including existing compiled sanitizer coverage. Strict corpus replay completed145 with `replay_matches_saved=true`, honoring saved worker hashes. `git diff --check` passes.

| Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
| Saved 145 cases |145 exact|145 exact, identical status and bytes|None|

inference:
- The successful-reference seed1 refusals were stale admission restrictions after UCRT powf integration. General filter admission can be reused within the independently tested Power domain.
- The Bilateral counterexample prevents extending this rule to every filter. No cause is inferred from final bytes alone.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/verify_distancegradation_smart_C08.py`
- `tools/fuzz/probe_distancegradation_C19.py`
- `tools/fuzz/probe_distancegradation_C31.py`
- `tools/fuzz/summarize_distancegradation_C31.py`
- `reports/fuzz/olmdistancegradation_C31_power.json`
- `orchestra/reports/C31-dg-smart-r6.md`

verify:
From this worktree, set `s="$PWD/orchestra/state/C31-dg-smart-r6"`, create it, and set TMPDIR/TMP/TEMP to it. Redirect long command output into `$s` logs. Use jobs1. Exact executed command lines and source/hash bindings are preserved by the evidence and commands below; no expectation edits are required.
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/base" --corpus "$s/corpus" --report "$s/base.json"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 32 --jobs 1 --shrink-attempts 0 --scratch "$s/fresh" --corpus "$s/fresh-corpus" --report "$s/fresh.json"
python3 tools/fuzz/probe_distancegradation_C19.py --scratch "$s/power" --report "$s/power.json" --before-ref 3781f6320be08bb475dbbc39d2cb192808ce7c40 --experiment power-ucrt --matrix --matrix-family power-ucrt --strict-admission --require-exact --write-source "$s/power-final.cpp"
python3 tools/fuzz/probe_distancegradation_C31.py --scratch "$s/power-final" --report "$s/power-final.json" --source "$s/power-final.cpp" --reference "$s/power.json" --before-ref 3781f6320be08bb475dbbc39d2cb192808ce7c40
python3 tools/fuzz/verify_distancegradation_smart_C14.py --scratch "$s/verify" --report "$s/verify.json" --before-ref 3781f6320be08bb475dbbc39d2cb192808ce7c40 --candidate-source "$s/power-final.cpp" --campaign "$s/base.json" --campaign "$s/fresh.json" --corpus --strict-admission --case-timeout 180
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s/replay" --report "$s/replay.json"
mkdir -p "$s/bin"
ln -sf "$PWD/tools/ucrt_cxx.py" "$s/bin/clang++"
PATH="$s/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'
git diff --check
```
The first two commands on the updated source measure the updated counts; original counts/hashes are retained in the committed evidence. Expected: seed1 290/0/3/7; seed32 282/1/11/6; independent1260 exact; negative5 refused; corpus145 unchanged; tests9 pass. Timeout verdicts must be reported if they vary with machine load.

next:
- Continue the independent PF16 first-stage mask discrepancy and inspect remaining fresh-seed refusals. Bilateral Power remains excluded. Original exceptions/time budgets are not exact outputs.
