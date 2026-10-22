status: done

summary:
- Closed bounded finite-HDR scalar Alpha box input admission after restoring original directional RowSum order.
- Seed1 improves197/0/103→207/0/93; fresh seed5 improves193/0/107→203/0/97 (exact/mismatch/refusal).
- Previous exact Smart and all Classic campaign records remain identical;600 sanitized production routes pass.
- 526 independent production cases are exact;6 invalid input/seed cases refuse. Corpus arithmetic outputs are unchanged.
- Two historical corpus inputs change refusal→exact; production replay stays8/8 and Gaussian Length1 retains its one-word counterexample.

facts:

Base `7f825746`. Machine evidence: `reports/fuzz/olmkirakira_smart_C07_finite.json`. Final Mac source SHA256 `9395fa6762317b1f17b2aa4155d5ec58c8249b817730002e7da6f7c719e48b25` binds to both final campaigns, matrices, trace, corpus audit and sanitizer replay. AEX/worker identities remain those in the opacity report. No MAIN, external emulator/worker, ledger, release-gate or other-plugin change; no push/install/rebuild.

| n300/jobs2 | Before E/M/R | After E/M/R | AEX Smart output/reject |
|---|---|---|---|
| seed1 |197/0/103|207/0/93|287/13|
| fresh seed5 |193/0/107|203/0/97|283/17|

The previous after campaign supplies the same-revision remeasurement for this loop. Its largest remaining successful-oracle input group is Alpha/Mode2 HDR10 plus signed9; these are input groups, not presumed root causes.

Gate-off experiments and new boundaries:

1. All finite PF32: index73 (1×9, signed alpha, Strength0) fails. Public-bound source and seed agree; horizontal ray1 first differs, original NaN versus a finite Mac value;6 final words differ. Negative alpha with the clamped fractional exponent creates NaN seeds. This broad rule is not admitted.
2. Nonnegative finite alpha: index14 (1×1, extreme finite input, Strength537) fails at2 words/7 bytes, first output word1 `acab2b3f` versus `0000803f`. Source/seed agree; overflow leads to first-ray AEX `0000c0ff` versus Mac `0000807f`. This broad rule is not admitted.
3. Requiring finite scalar powf seeds exposes a port operation at index155 (PF32 7×11, Strength100, extreme finite contrast). Source/seed/forward warp agree. First helper difference: vertical `helper0_op1_out` word111, AEX `00000000`, Mac `dbb67f3e`;21 helper words differ. Final output differs at2 words/6 bytes, first word106 `fbfa7a3f` versus `0000803f`. The complete original trace binds to public Smart. Restoring RowSum order makes every captured helper, all nine high-level stages and final output exact.

Each rejection provides a distinct new boundary/value. Pre-fix counterexamples are retained; no failed candidate or coordinate/sample correction is promoted.

Original operation and general fix:

- Baseline `RowSum<float,double>` is `18127f3c0`, vtable `1814dcaf0`; SSE4.1 is `1812d6690`, vtable `181531f70`. Their decomp shows direct left-associated sums for sizes3/5. Other one-channel kernels preload a double sum and update `sum + (double(incoming)-double(outgoing))`. Column normalization multiplies by the double reciprocal before float storage.
- The port recomputed each window and divided by length. At extreme contrast, it retained small values lost by the original sliding sum. The recovered Alpha box branch now preserves the original update, direct3/5 branches and reciprocal multiplication. Other channel/mode branches keep their prior boundary.
- Runtime hooks on the length5/6 witness record SSE4.1 entry `1812d6690`: kernel5/width16/channel1×15, kernel6/width14/channel1×16, Highlight kernel7/width7/channel1×11. The baseline-only hook recorded0 calls; baseline execution is not inferred from static symbols.
- Production traces for7/2 and special3/4,5/6 kernels match every captured helper/high-level stage, independently bound to original public output.

The new Smart rule requires PF32 with all four source components finite, alpha nonnegative, and `powf(alpha,max(0.001f,materialized Strength))` finite. RGB may be signed or above1. Full recovered Alpha/Mode1-or2 tuple, declared controls, geometry/layout/default-ramp checks remain. Existing SDR admission stays intact. PF8/PF16, Classic, Gaussian, other channels and negative/nonfinite/overflowing-seed families gain no input admission. This is an operation-domain check, never an expected-output comparison or fitted HDR cutoff.

Sanitized independent matrices:263 cases across1×1/1×9/7×11/9×7, both box modes/merges, Strength{0,1,97,100,537,1000}, random HDR/signed RGB and exact ±maximum-finite/minimum-normal/subnormal/zero/one bit patterns, within the declared finite-seed domain. All263 production outputs are exact. Another263 vary lengths{1,2,3,4,5,6,7,15,50,1000}; all exact. Six negatives (negative alpha, alpha Inf/NaN, RGB NaN/Inf, finite-alpha powf overflow) refuse with balanced callbacks and unchanged destination. All600 final campaign routes rerender under ASan/UBSan and match ordinary builds.

| Corpus inputs | Production Smart before→after | Diagnostic arithmetic |
|---|---|---|
| T06 shrunk39,182 | refusal→exact | unchanged bytes |
| other68, including all8 production inputs | unchanged status/output | unchanged bytes |

The70-input production audit and140-route arithmetic audit pass; changed samples=0. Historical T06 expectations remain historical; production strict replay is8/8 without updates. Gaussian Length1 remains refused in production; gate-off retains exactly word217/byte868, AEX `5cf1563f`, Mac `5df1563f` (one byte). Its diagnostic PASS means the mismatch is preserved, not exact output. The25 fast tests pass; compiled generic-beta ASan/UBSan passes54 internal rows including HD in42.302s. `git diff --check` passes. Scratch remains below5GiB; build outputs are removed before delivery.

inference:

Exact upstream planes, original row operators, runtime dispatch and restored helper/final bytes establish an accumulation-order cause. Domain checks exclude measured NaN/Inf filtering boundaries while admitting finite HDR without an arbitrary magnitude cutoff. Finite probes do not establish all floating inputs, native AE/UCRT, custom ramps, ROI/downsample or other constructors. The emulator retains host math imports.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/summarize_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C07_finite.json`
- `orchestra/reports/C07-kira-smart-r2-finite.md`
- `orchestra/reports/C07-kira-smart-r2.md`

verify:

At this cluster commit:

```sh
s="$PWD/orchestra/state/C07-kira-smart-r2/recheck-finite"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 7f825746:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 5; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 5 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
for family in finite-seed finite-lengths; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family invalid-input --expect-finite-domain --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --family finite-seed --trace-index 155 --gate-off --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family finite-seed --trace-index 155 --require-exact --scratch "$s/trace-after" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
for index in 152 154; do
  "$py" tools/emulation/probe_kirakira_smart_C07.py --family finite-lengths --trace-index "$index" --require-exact --scratch "$s/trace-$index" --report "$s/trace-$index.json" > "$s/trace-$index.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --family gaussian-length1 --scratch "$s/length1-production" --report "$s/length1-production.json" > "$s/length1-production.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --family gaussian-length1 --gate-off --scratch "$s/length1-diagnostic" --report "$s/length1-diagnostic.json" > "$s/length1-diagnostic.log" 2>&1
```

Expected: campaign table;600 sanitized routes/70 corpus comparisons;263+263 exact;6 refusals;140-route arithmetic audit/0 changed samples; bound box difference→all captured stages exact; replay8/8; unchanged Length1 refusal/one-word diagnostic mismatch. Rejected hypotheses are reproduced with `--source "$s/before.cpp" --gate-off --require-exact` and families `finite-alpha`, `finite-nonnegative`, `finite-seed`: expected exit1 at indices73/14/155.

next:
- C07's three-cluster stop condition is met. Seed1 remaining93 refusals:13 without AEX output,80 with output.
- Follow-up: approximation, negative-alpha/NaN filtering, Mode3 Highlight/Length1, scalar/four-channel color constructors. Native AE/UCRT remains separate.
