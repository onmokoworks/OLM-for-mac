status: blocked
summary:
- Reproduced seed1 n300 Smart: 290 exact / 0 mismatch / 8 refusal / 2 uncompared.
- Six allocator-dependent refusals retain the existing safety guards.
- Finite-gate bypass and rotation generated-NaN correction both fail exact admission; O2/ASan/UBSan agree.
- Python paired traces still fail F32 final-output binding; no production change or cluster closure is claimed.
- Stopped after two rejected admission hypotheses without a new trustworthy stage boundary.

facts:

Base `7f9c2ae051394482a2eae609ccca838e63dd67a8`, branch `orch/C36-dblur-smart-r6`. Read AGENT_GUIDE, DirectionalBlur ledger rows, compatibility plan, GOTCHAS, T10/C18/C25/C30 and F38 reports. MAIN, emulator source, cached workers, production sources, corpus expectations, release gates and ledger remain unchanged. No worker rebuild, push, stash, history rewrite or permission rejection.

The required campaign completed all300 cases, exit0, jobs1, shrink-attempts0. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`. Raw typed CPU AEX Smart is compared with public Mac EffectMain in the fake host; no native AE/GPU claim. Committed `C36-evidence/measurements.json` retains provenance, residual inputs/controls, result hashes, first mismatches, stage summaries and build command arrays.

| Smart set | Before E/M/R/U | Final E/M/R/U |
|---|---|---|
|seed1 n300|290/0/8/2 (C30 report)|290/0/8/2 (new run)|
|saved corpus|56 exact (C30 report)|unchanged files; not rerun here|

No production or corpus rebaseline was made. Consequently no base-exact output is changed by this ticket; this is source identity, not a new full sanitizer regression claim.

Largest cluster is cases4/7/127/246/280/284: six core refusals. C18/C25 already demonstrated actual invalid generated-noise table demand in every case and final-output dependence on counterfactual allocator padding in4/280. Those are reused prior facts, not new measurements. No unsafe gate-off read or budget change was attempted. Cases274/289 again exhaust the original Smart oracle budget; they remain uncompared, not Mac mismatches or exact cases.

Hypothesis1: the current nonfinite numerical path could be admitted without correction. Existing C30 scratch-only finite-gate bypass exits0 but reproduces both mismatches. Hypothesis2: correcting generated default NaNs at rotation is sufficient for admission. New scratch-only probe changes only the four rotation arithmetic helpers to call the existing operand-aware generated_nan helper, retaining operation order and all other core guards. It also exits0 but neither witness becomes exact.

| Seed1 case | Gate bypass bytes / words | Rotation correction bytes / words | Sign-only words before→after | First final mismatch after correction |
|---|---:|---:|---:|---|
|109|2808 / 969|2680 / 880|89→0|byte6, word1: AEX `0000803f`, Mac `0000c0ff`|
|299|1919 / 728|1834 / 634|94→0|byte20, word5: AEX `0000803f`, Mac `4523c17f`|

Both experiments compare identical O2 and ASan/UBSan results for both witnesses. Flags include `-fsanitize=address,undefined -fno-sanitize-recover=all`, halt_on_error=1, leak detection disabled. No sanitizer diagnostic occurred. This is four checked witness/build pairs across the experiments, not broad nonfinite correctness. The original probe exit0 means its measurement assertions passed, not pixel equivalence.

The existing paired trace exits0 using the explicit diagnostic `--allow-fixture-difference`. Populated planes agree, with first captured differences at rotation:440/310 float words; first byte2084/1824, AEX fixture `0000c0ff`, Mac `0000c07f`. However fixture final output differs from F32 by421/312 bytes, first byte32 in both. These are the same unresolved C30 boundaries. They cannot certify a first divergent stage against the authoritative F32 run. Diagnostic native-f32 imports are not a proof of UCRT equivalence; no new still-host math divergence is established or repaired here.

inference:
- Rotation correction removes the observed final sign-only differences but is insufficient for general nonfinite admission. Payload/selection and downstream operation semantics remain unresolved; these are not all default-NaN sign errors.
- Six cases depend on an invalid-demand allocator boundary and two need a trace harness bound to F32. Further numeric edits without that binding would be speculative.
- Both admission hypotheses are refuted and the stage probe supplies no new authoritative boundary. The ticket's stop condition applies. Zero clusters closed; Smart exact does not increase.

changed_files:
- tools/fuzz/probe_directionalblur_c36_nan.py
- orchestra/reports/C36-evidence/measurements.json
- orchestra/reports/C36-dblur-smart-r6.md

verify:

Run sequentially from this worktree. All four measured commands exited0. Expected results are the campaign and diagnostic tables above; oracle timing may vary. The new probe's final provenance-only metadata addition was made after its measured numerical run; it does not alter compilation or evaluation.

```sh
S="$PWD/orchestra/state/C36-dblur-smart-r6"
W=/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --scratch "$S" --report "$S/baseline.json" --corpus "$S/baseline-corpus" --shrink-attempts 0 > "$S/baseline.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c30_nonfinite.py --scratch "$S" --worker "$W" --report "$S/nonfinite.json" > "$S/nonfinite.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --indices 109 299 --nonfinite-off --expf-leaf native-f32 --powf-leaf native-f32 --allow-fixture-difference --scratch "$S" --worker "$W" --report "$S/stages.json" > "$S/stages.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c36_nan.py --scratch "$S" --worker "$W" --report "$S/rotation-nan.json" > "$S/rotation-nan.log" 2>&1
git diff --check
```

next:
- Restore a paired-trace dependency/math setup whose complete nonfinite outputs bind to cached F32, then locate the first remaining arithmetic/selection divergence with and without the scratch rotation correction.
- Keep allocator-dependent cases refused pending allocator-independent semantics; do not emulate padding or change the work budget.
- No fresh-seed promotion/regression campaign is warranted for these rejected experiments. Any future admission must pass seed1, fresh seed, sanitizer and preserved-exact replay checks.

Hygiene: all started command sessions completed. Temporary compilation directories were removed by their context managers. Regenerable scratch corpus removed; logs/reports retained below5GiB. No background process remains.
