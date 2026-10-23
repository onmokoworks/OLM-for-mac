status: done

summary:
- Connect Gaussian Highlight to the existing recovered approximation pipeline for all six channels.
- Seed1 Smart277/0/23 →279/0/21; fresh seed21 279/0/21 →280/0/20.
- Preserve all existing exact outputs and Classic campaign results; no corpus sample or expectation changes.
- Independent360 conditions,600 sanitized campaign renders,70 guarded corpus cases and140 sample comparisons pass.

facts:

Base `6a92db2f`. Original AEX and F32 hashes are unchanged from the color Highlight report. The source and full evidence are bound in `reports/fuzz/olmkirakira_smart_C34_highlight_approximation.json`.

Gate-off seed1/index31 (PF16,5×12, Channel5) first differs at reduced source: all48 words differ, first original `801ff33e`, Mac `009cd63e`. The original pipeline's linear source reduction was not selected for Gaussian Highlight. Extending that selector connects existing source reduction, six-channel constructors, scaled radii, separable Gaussian, glow enlargement and full-resolution source composition. Neither Gaussian coefficients nor compose arithmetic change. Final public-bound F32/UCRT traces index31 and215 match all paired stages and output.

Admission retains finite SDR, full-frame dimensions at least4×4, angle/default-ramp/control restrictions and existing conservative Gaussian work/memory estimates. Work-budget thresholds are unchanged. One-pixel reduced IPP workspaces remain excluded.

| Check | Before | After |
|---|---|---|
| seed1 Smart E/M/R |277/0/23|279/0/21; indices31,215|
| seed21 Smart E/M/R |279/0/21|280/0/20; index213|
| Guarded corpus70 |baseline|0 result changes|
| Both-route sample audit140 |baseline|0 changed samples,0 away from exact|
| Production saved replay |8 fixtures|8/8 matches_saved|

Gate-off288 controls and production288 controls pass; boundary72 passes on the candidate and final source. These sanitizer builds cover all six channels, three depths, small/large radii, odd dimensions,4×4 minimum and radii reduced to zero. Five one-away controls refuse. Final campaign audit rerenders600 Smart cases under ASan/UBSan and reproduces all campaign hashes. All600 Classic result objects remain identical. Existing25 fast tests and the compiled54-row sanitizer test pass (44.705s). No hypothesis was refuted in this cluster.

inference:

This establishes a bounded CPU-emulation closure, not unrestricted native AE/UCRT, arbitrary source values, ramps or ROI/downsample compatibility. No first divergence at a still-host math import was observed. There is no reason to rebaseline unchanged corpus samples.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C34_highlight_approximation.json`
- This report and ticket summary.

verify:

Run at this cluster commit. Expected seed1=279/0/21, seed21=280/0/20; matrix288+72 exact, negatives5 refusal; audits600 sanitized campaign renders/70 guarded corpus/140 sample comparisons; saved replay8/8.

```sh
s="$PWD/orchestra/state/C34-kira-smart-r8/recheck-approx"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 6a92db2f:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 21; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in approximation-gaussian-highlight approximation-gaussian-highlight-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-gaussian-highlight-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 21 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
for index in 31 215; do
 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/probe_kirakira_smart_C07.py --ucrt-math --campaign-seed 1 --trace-index "$index" --require-exact --scratch "$s/trace$index" --report "$s/trace$index.json" > "$s/trace$index.log" 2>&1
done
```

Assert every saved replay row matches. Trace public_bound=true and first_divergent_stage=null. Original index31 first divergence is reproduced by adding `--source "$s/before.cpp" --gate-off` and removing `--require-exact` in a separate scratch directory. Fast/compiled sanitizer commands are those in C29's final report, using this ticket's scratch.

next:
- Two clusters closed. Seed1 residual21 includes13 original rejects and8 successful-oracle refusals: non-SDR39/52/86/179/272 and nonfinite63/116/126.
- Investigate the three-case nonfinite cluster next; retain intermediate NaN evidence even when final bytes match.
