status: partial
summary:
- Closed the PF8 Front Fade × Size admission cluster after the UCRT math integration.
- Seed1 Smart improves 286→290 exact, 12→8 refusal; zero mismatches and two uncompared remain.
- Fresh seed6 improves 278→286 exact; all 619 baseline-exact outputs and all 56 saved corpus records are preserved.
- Gate-off 600, independent matrix 576, production matrix 576 and regression 656 pass with strict ASan/UBSan comparisons.
- Negative-Offset allocator and nonfinite boundaries remain guarded; fresh-seed pre-existing angle mismatch is under investigation.

facts:

Base `3781f6320be08bb475dbbc39d2cb192808ce7c40`, branch `orch/C30-dblur-smart-r5`. Read AGENT_GUIDE, the DirectionalBlur ledger row, compatibility plan, GOTCHAS, T10/F05/F06/F16/C02/C09/C18/C25/F37 and F10/F12 methodology. MAIN, external emulator sources, cached workers, other plugins, release gates and ledger are unchanged. No rebuild of a worker, push, stash, history rewrite or permission rejection.

F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`. Full command arrays, provenance, report hashes, changed cases and source hashes are in `orchestra/reports/C30-evidence/measurements.json`. Scope is original CPU AEX Smart versus Mac public EffectMain in the fake host, full-frame typed ARGB; this is not native AE or all-input equivalence.

The initial n300 seed1 campaign reproduces F37 exactly. Largest residual is six negative-Offset core refusals (4/7/127/246/280/284). C18/C25 establish actual invalid table demand in every case, including final-output dependence on counterfactual allocator padding for 4/280. Those prior facts are reused, not claimed as new runs. No unsafe gate-off dereference is attempted.

The next cluster is PF8 Front Fade × Size. Scratch-only feature-gate removal preserves all core safety guards and numerical operations. Seed1 cases73/78/175/200 and fresh seed6 cases46/113/200/203/227/228/259/274 were evaluated (the complete measured change list in JSON is authoritative). All 600 O2/sanitized pairs agree; all 12 admissions are raw-byte exact against F32. The previous C25 case200 11-byte expf mismatch is now zero. Current `core/dblur_gaussian.h` calls `ucrt_expf` for both weight entrypoints. No Gaussian or writer arithmetic is changed.

Independent C09 matrices cover six families, 576 cases, varied geometry/ARGB/angle/gain/Size/Fades/tails, generated Noise and zero/active Strength. Both gate-off and production matrices are all exact against Smart on both Mac routes, including all sanitizer comparisons. The production change removes only the obsolete Size×Fade predicate; Layer, demanded-noise-index, budget, world and finite-input guards remain.

| Smart set | Before E/M/R/U | After E/M/R/U |
|---|---|---|
|seed1 n300|286/0/12/2|290/0/8/2|
|fresh seed6 n300|278/1/20/1|286/1/12/1|
|saved corpus56|55/1/0/0|55/1/0/0|

All 656 regression cases pass O2 versus ASan/UBSan on both public routes; all 619 baseline-exact hashes are unchanged. Exactly12 output transitions are refusal→exact. Strict sanitizer flags include `-fsanitize=address,undefined -fno-sanitize-recover=all`, halt_on_error=1, leak detection disabled. Corpus replay is56/56 matches_saved; no corpus rebaseline is necessary:55 exact→identical exact,1 mismatch→identical mismatch. Retained corpus case236 differs at byte3, AEX71/Mac72. Seed6 case234 retains201 differing bytes/192 words, first byte0 AEX `40a1b93d`, Mac `2fa1b93d`. Classic seed1 changes4/284/12/0→4/288/8/0 relative to its distinct Classic oracle; no Classic compatibility claim.

Nonfinite diagnostic bypass (production policy unchanged): cases109/299 differ in2808/1919 bytes and969/728 float words; first byte6 AEX `0000803f` / Mac `0000c07f`, and byte20 AEX `0000803f` / Mac `4523c17f`. Only89/94 differing words are NaN-sign-only; the entire residual is not labeled F38. Both O2/ASan/UBSan comparisons pass.

Existing paired Python traces have equal populated planes and first captured divergence at rotation:440/310 words. The first words are invalid-op NaN sign, `0000c0ff` versus `0000c07f`, at byte2084/1824. Per ticket, no invalid-op sign fix is attempted. These traces do NOT bind to F32: fixture final bytes differ from F32 by421/312 bytes, first byte32 in both. The F29 library path recorded in instruction-provenance.json is absent; the installed Python fixture uses older Unicorn and host math. These stage observations are diagnostic, not a replacement F32 oracle. Do not infer that later nonfinite differences are all F38.

inference:
- The retained Size×Fade refusal is obsolete after UCRT integration; two seeds and independent matrices justify general admission within existing safety bounds.
- The negative-Offset residual remains allocator-dependent. Nonfinite admission requires F32-bound stages and the F38 invalid-op boundary to be resolved before broader conclusions.
- One cluster is closed so far. The two-refutations stop rule has not been reached.

changed_files:
- mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp
- tools/fuzz/verify_directionalblur_c09_matrix.py (jobs1 default, explicit --jobs)
- tools/fuzz/probe_directionalblur_c30_nonfinite.py
- tools/fuzz/summarize_directionalblur_c30.py
- orchestra/reports/C30-evidence/measurements.json
- orchestra/reports/C30-dblur-smart-r5.md

verify:

Run sequentially from this worktree, with logs redirected as below. All commands listed were run and exited0. Expected results are the tables/counts above; timing-related uncompared results must remain reported honestly.

```sh
S="$PWD/orchestra/state/C30-dblur-smart-r5"
W=/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
B=3781f6320be08bb475dbbc39d2cb192808ce7c40
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
# The baseline campaign was run at B with the same options and baseline.json/corpus outputs.
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --scratch "$S" --report "$S/after.json" --corpus "$S/after-corpus" --shrink-attempts 0 > "$S/after.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c09_admission.py --baseline "$B" --seeds 1 6 --jobs 1 --scratch "$S" --worker "$W" --report "$S/gate.json" > "$S/gate.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c09_matrix.py --baseline "$B" --scratch "$S" --worker "$W" --families fade-only noise-fade plain-fade active-noise-fade back-fade back-fade-zero --jobs 1 --report "$S/matrix-gate.json" > "$S/matrix-gate.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c09_matrix.py --baseline "$B" --scratch "$S" --worker "$W" --families fade-only noise-fade plain-fade active-noise-fade back-fade back-fade-zero --jobs 1 --production --report "$S/matrix-production.json" > "$S/matrix-production.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c02.py --baseline "$B" --seeds 1 6 --jobs 1 --corpus --scratch "$S" --worker "$W" --report "$S/verify.json" > "$S/verify.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 1 --replay tests/fuzz_corpus/olmdirectionalblur --worker "$W" --scratch "$S" --report "$S/replay.json" --corpus "$S/replay-corpus" > "$S/replay.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c30_nonfinite.py --scratch "$S" --worker "$W" --report "$S/nonfinite.json" > "$S/nonfinite.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --indices 109 299 --nonfinite-off --expf-leaf native-f32 --powf-leaf native-f32 --allow-fixture-difference --scratch "$S" --worker "$W" --report "$S/nonfinite-stages.json" > "$S/nonfinite-stages.log" 2>&1
python3 tools/fuzz/summarize_directionalblur_c30.py --scratch "$S" --output orchestra/reports/C30-evidence/measurements.json > "$S/summary.log" 2>&1
git diff --check
```

next:
- Investigate the first rotation divergence of fresh seed6:234, without changing base-exact outputs.
- Retain the six allocator-dependent refusals and two nonfinite refusals. F38 handles invalid-op NaN sign; a matching Python trace library/math binding is also required for broader nonfinite work.
