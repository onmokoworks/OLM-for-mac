status: done

summary:
- Connect four-component Gaussian Highlight to the recovered seed, separable Gaussian and color aggregator.
- Seed1 Smart275/0/25 →277/0/23; fresh seed20 280/0/20 →281/0/19 (exact/mismatch/refusal).
- All previous exact Smart outputs and all600 Classic campaign results are unchanged.
- Independent204 conditions,600 sanitized campaign renders,70 guarded corpus cases and140 sample comparisons pass.

facts:

Base `67a34ff3d82f316810dd1f9df8b2648c5dc59bd2`. Seed1 remeasurement reproduces275 exact/0 mismatch/25 refusal; original Smart renders287 and rejects13. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.

Gate-off seed1/index59 first differs at seed: original1664 bytes versus Mac416; first word original `2209be38`, Mac `cb95a33d`. The unconnected four-component constructor fell through to the scalar seed, and Highlight was omitted. Its final output differs385 words, first word1 original `f87d4a3e`, Mac `5ff4903e`.

Original caller `FUN_18114f4a0`, MAIN decomp lines3524020–3524065, writes `(2*r+1)^2` into the Highlight normalizer before Mode3 calls GaussianBlur. The new branch applies the existing separable Gaussian to each component and retains that normalizer. No coefficient, compose arithmetic or final sample is adjusted. Public-bound F32/UCRT paired traces for indices59 and62 match source, seed, every ray, glow and composition. Existing work/memory limits retain the four-component multiplier.

| Check | Before | After |
|---|---|---|
| seed1 Smart E/M/R |275/0/25|277/0/23; indices59,62|
| seed20 Smart E/M/R |280/0/20|281/0/19; index239|
| Guarded corpus70 |baseline|0 result changes|
| Both-route sample audit140 |baseline|0 changed samples,0 away from exact|
| Production saved replay |8 fixtures|8/8 matches_saved|

The gate-off144-condition matrix and final production144-condition matrix are all exact under ASan/UBSan. Final candidate boundary60 (including singleton axes and small kernels) is all exact; five negative controls remain refused. The final600-case sanitizer replay reproduces campaign hashes. Existing25 fast tests pass; compiled54-row sanitizer test passes (45.023s). Machine evidence is `reports/fuzz/olmkirakira_smart_C34_color_highlight.json`. No corpus expectation changes are necessary. No hypothesis was refuted in this cluster.

inference:

These are bounded original-AEX CPU-emulation closures. Native AE/UCRT, nonfinite/non-SDR inputs, arbitrary ramps and ROI/downsample are not established by these checks. Four-component planar execution matches the observed separable operations; no still-host math divergence was observed.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C34_color_highlight.json`
- This report and the ticket summary.

verify:

Run at this cluster commit. All long output belongs in ticket scratch. Expected counts are in the table above.

```sh
s="$PWD/orchestra/state/C34-kira-smart-r8/recheck-color"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 67a34ff3d82f316810dd1f9df8b2648c5dc59bd2:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 20; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in gaussian-highlight-color gaussian-highlight-color-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-highlight-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 20 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
```

Assert all8 replay rows have `matches_saved=true`. Paired trace command (run for59 and62):

```sh
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/probe_kirakira_smart_C07.py --ucrt-math --campaign-seed 1 --trace-index 59 --require-exact --scratch "$s/trace59" --report "$s/trace59.json" > "$s/trace59.log" 2>&1
```

Expected public_bound=true and first_divergent_stage=null. To reproduce the original missing-constructor mismatch, add `--source "$s/before.cpp" --gate-off`, omit `--require-exact`, and use a separate scratch/report. Existing fast/compiled sanitizer commands are those in C29's final report, with scratch relocated here.

next:
- One cluster closed. Investigate Gaussian Highlight approximation (seed1 indices31/215) next.
