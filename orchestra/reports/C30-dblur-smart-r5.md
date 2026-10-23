status: blocked
summary:
- Closed two clusters in separate commits: PF8 Front Fade admission and the original AEX angle-conversion constant.
- Final seed1 Smart:290 exact /0 mismatch /8 refusal /2 uncompared (baseline286/0/12/2); fresh seed6:287/0/12/1 (baseline278/1/20/1).
- Saved corpus improves55→56 Smart exact; only one record is rebaselined, mismatch→exact; final replay56/56.
- Each fix passes656-case O2/ASan/UBSan regression; independent matrices576 and294 pass, and65536 original angle-builder inputs match the restored formula.
- Stopped before a third closure: remaining seed1 refusals require allocator semantics or F38/nonfinite oracle work; no unsafe or NaN-policy promotion.

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
- The first commit closes one cluster. Final disposition and the second cluster are recorded below. The two-refutations stop rule was not reached.

changed_files:
- mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp
- tools/fuzz/verify_directionalblur_c09_matrix.py (jobs1 default, explicit --jobs)
- tools/fuzz/probe_directionalblur_c30_nonfinite.py
- tools/fuzz/summarize_directionalblur_c30.py
- orchestra/reports/C30-evidence/measurements.json
- orchestra/reports/C30-dblur-smart-r5.md

verify:

Run sequentially from this worktree, with logs redirected as below. These first-cluster measurements cover base→3ff5f734 and all commands exited0. Recheck those snapshots for the first-cluster table; final-source commands follow below. Expected results are the tables/counts above; timing-related uncompared results must remain reported honestly.

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
- The seed6:234 investigation is resolved by the second cluster below.
- Retain the six allocator-dependent refusals and two nonfinite refusals. F38 handles invalid-op NaN sign; a matching Python trace library/math binding is also required for broader nonfinite work.

Second cluster — original angle-conversion constant (facts):

Baseline `3ff5f734` (first cluster). The existing paired original-AEX probe for seed6:234 binds its complete final output exactly to F32, hash `b24b0ab602651ce28e2060b1bd7efe752bafd33803458c7ab35d231177a5275d`. Populated input agrees; rotation is the first divergent captured image plane:788 float words. First byte716, AEX `2237fe3c`, port `1838fe3c`. The original builder records angle radians -6.946410179138184 for the materialized control -488; the former port formula gives -6.946410655975342. This precedes the sin/cos import, so it is not classified as ucrt-math-pending.

Binary inspection of `FUN_180006c50` shows float→double conversion followed by ADD90, DIV180, MULconstant and double→float rounding. `MULSD` at0x180006d18 reads binary64 at0x18000b360, bytes `f1d4c853fb210940`, exactly the double literal3.14159265. The old full-precision π constant was incorrect. Restored that constant in `core/dblur_frontonly.cpp` for its PF8/PF16/PF32 angle conversions, preserving operation order. No trig, Gaussian, writer or per-case operation was changed.

The committed leaf probe executes the original seven instructions at0x180006cfd..0x180006d24 for all65536 signed-short angles. All65536 agree with the restored formula;896 disagree with the old full-precision formula. This is a scalar conversion proof, not all-input render equivalence. Constants, decoded instruction bytes, instruction/output hashes and every old mismatch are retained in `C30-evidence/angles.json`.

After the constant fix, seed6:234 has zero final-byte differences; populated/rotated/map/divisor/row-output/denominator/alpha-max/writer-plane all agree. The diagnostic fixture's captured2500-entry weight table still differs by14 words from UCRT weights (native-f32 diagnostic import versus current UCRT); both other captured weight tables and every captured output plane agree. Do not describe every diagnostic stage as exact or tune those weights: complete fixture output binds to F32 both before and after.

Independent294-case public matrix:49 angles (all15 affected integer angles in[-720,720], their ±1 neighbors and4 anchors),2 independent generated ARGB/control templates, PF8/PF16/PF32. All294 are exact on both Mac routes against original Smart, normal/sanitized identical. Prior mismatches resolved:PF16=23, PF32=30, PF8=0; all241 already-exact outputs preserved. Additional PF8 evidence is the saved corpus case236 at materialized angle308, now exact.

| Smart set | After first fix E/M/R/U | Final E/M/R/U |
|---|---|---|
|seed1 n300|290/0/8/2|290/0/8/2|
|fresh seed6 n300|286/1/12/1|287/0/12/1|
|saved corpus56|55/1/0/0|56/0/0/0|

Second656-case regression exits0; all631 baseline-exact hashes are unchanged and both changed outputs become exact. Separate56-case O2/ASan/UBSan rebaseline exits0. Only `tests/fuzz_corpus/olmdirectionalblur/seed1_case000236_911964b2d8a0.json` changes expectation: Smart one differing byte→zero; Classic's distinct oracle still mismatches but its observed output is updated faithfully. Input/pixels/controls/original provenance are preserved. Final corpus replay56/56 matches_saved. Corpus transition table:55 exact→identical exact;1 mismatch→exact. Seed1 is re-measured at290/0/8/2.

Second-cluster inference:
- A shortened original constant changes float rounding at specific angle boundaries; full-precision π is not interchangeable with that binary contract. The original instructions, paired planes and independent renders justify the general constant repair.
- Two clusters are closed. The remaining seed1 refusal families are the six already-proven invalid-demand allocator cases and two nonfinite cases whose first diagnostic difference is an invalid-op sign boundary assigned to F38. Broader nonfinite conclusions remain blocked by Python/F32 fixture disagreement. No additional safe admission or third cluster is claimed.
- Stop reason: unresolved external/ISA/oracle boundaries in the remaining seed1 candidates, not a time limit or repeated-hypothesis threshold. One broad nonfinite admission experiment was refuted; the angle investigation supplied a new boundary and succeeded.

Additional changed_files:
- core/dblur_frontonly.cpp
- tools/emulation/probe_directionalblur_c30_angle_builder.py
- tools/fuzz/verify_directionalblur_c30_angles.py
- tools/fuzz/summarize_directionalblur_c30.py (--angles evidence mode)
- tests/fuzz_corpus/olmdirectionalblur/seed1_case000236_911964b2d8a0.json
- orchestra/reports/C30-evidence/angles.json
- orchestra/reports/C30-dblur-smart-r5.md

Final-source verify (same S/W/P environment as above; run sequentially, jobs1):

```sh
B=3ff5f734
"$P" tools/emulation/probe_directionalblur_c30_angle_builder.py --aex '/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMDirectionalBlur.aex' --report "$S/angle-builder.json" > "$S/angle-builder.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c30_angles.py --baseline "$B" --scratch "$S" --worker "$W" --report "$S/angle-matrix.json" > "$S/angle-matrix.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c02.py --baseline "$B" --seeds 1 6 --jobs 1 --corpus --scratch "$S" --worker "$W" --report "$S/angle-verify.json" > "$S/angle-verify.log" 2>&1
# This was the measured one-record rebaseline; it is idempotent on final sources.
python3 tools/fuzz/verify_directionalblur_c02.py --baseline "$B" --seeds --jobs 1 --corpus --rebaseline --scratch "$S" --worker "$W" --report "$S/angle-rebaseline.json" > "$S/angle-rebaseline.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --scratch "$S" --report "$S/angle-after.json" --corpus "$S/angle-corpus" --shrink-attempts 0 > "$S/angle-after.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 1 --replay tests/fuzz_corpus/olmdirectionalblur --worker "$W" --scratch "$S" --report "$S/angle-replay.json" --corpus "$S/angle-replay-corpus" > "$S/angle-replay.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --seed 6 --indices 234 --core-ref "$B" --expf-leaf native-f32 --powf-leaf native-f32 --allow-fixture-difference --scratch "$S" --worker "$W" --report "$S/seed6-stages.json" > "$S/seed6-stages.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --seed 6 --indices 234 --expf-leaf native-f32 --powf-leaf native-f32 --allow-fixture-difference --scratch "$S" --worker "$W" --report "$S/angle-stages.json" > "$S/angle-stages.log" 2>&1
python3 tools/fuzz/summarize_directionalblur_c30.py --angles --scratch "$S" --output orchestra/reports/C30-evidence/angles.json > "$S/angle-summary.log" 2>&1
git diff --check
```

Expected all exit0:65536 builder conversions,294 exact matrix cases,656 regression cases/631 preserved exact,56 rebaseline and56 replay records, campaign290/0/8/2. The original before-stage command ran before editing the core; `--core-ref 3ff5f734` reproduces that core without checkout. Numerical records/hashes are in angles.json; timing/build-directory metadata can differ on re-run.

Final next:
- Negative-Offset follow-up needs allocator-independent semantics or a proven demand exclusion; never fill invalid reads with emulator padding.
- Resolve F38 invalid-op NaN sign and restore an F32-equivalent Python trace dependency before general nonfinite admission; later payload/minimum semantics are not yet certified.
- Two timed-out seed1 Smart oracle cases274/289 remain uncompared, not exact. No native AE, installed bundle, GPU, ROI or arbitrary-input completion claim.

Final hygiene: all started command sessions completed; no background workload remains. Temporary build trees were automatically removed and regenerable scratch corpora deleted. Scratch retains logs/reports only, 16329229 bytes (<5GiB). `git diff --check` passes.
