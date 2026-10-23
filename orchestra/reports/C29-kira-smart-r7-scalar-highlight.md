status: done

summary:
- Recover scalar Mode3 Highlight's separable Gaussian and sigma-zero small kernels.
- Seed1 Smart269/0/31 → 272/0/28; fresh seed17 264/0/36 → 266/0/34.
- Preserve every base-exact Smart and every Classic campaign result.
- Independent204 final conditions,600 sanitized campaign renders and140 corpus route comparisons pass.

facts:

Base `395e5d8af90321982f0493bc052f09e671bd8368`. All campaigns n300, jobs1, no shrinking, ticket-local scratch/corpora. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`. Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. Machine evidence: `reports/fuzz/olmkirakira_smart_C29_scalar_highlight.json`.

Original AEX at `18114f964` constructs Size(2*r+1,2*r+1); `18114fa14` zeroes XMM3 (sigmaX), stores zero sigmaY, and calls GaussianBlur `181272ec0` with border4. Existing Mac skipped this branch. Seed1/index213 first diverges at ray4; source and seed match. The first general separable diagnostic makes indices213 and235 exact through all paired stages.

The independent144-condition diagnostic initially yields109 exact/35 mismatches, concentrated at radii1–4. PF8 matrix index3 (radius4) binds to F32 and first differs at ray4, word0 original `43fbbe3e`, candidate `4282bf3e`;77 ray words differ. Restoring sigma-zero fixed3/5/7/9-tap coefficients and the original small-row symmetric addition order yields144/144 exact under ASan/UBSan. The generic rejected proposal is reproducible with `tools/emulation/fixtures/kirakira_highlight_generic_C29.patch` applied to the base source.

A separate60-condition singleton/tiny matrix initially yields54 exact/6 mismatches. PF32 17×1/index50 binds to F32, seed matches, ray4 first word1 is original `42bde13d`, candidate `43bde13d`;6 ray words differ. Collapsing each singleton axis to the original identity filter makes60/60 exact. The rejected uncollapsed helper is preserved as `kirakira_highlight_no_axis_C29.patch`. Each refutation supplied a new intermediate boundary; the two-refutations-without-new-boundary stop condition did not occur.

Final public-bound traces seed1 indices48/213/235 and singleton index50 have all paired stages exact. The old Python trace used host powf, which produced a hidden one-word seed discrepancy on index48 even though PF8 output matched. The optional `--ucrt-math` now binds expf/powf/atan2f to the same independent UCRT FMA implementation as F32; it fixes that diagnostic discrepancy. Scratch source relocation also resolves the new ucrtmath include. Other imports are unchanged.

Admission extends finite-SDR, full-frame, non-approximated Mode3 to scalar Channels1/2/4 with Highlight. Existing controls, angles, ramps and source/layout validation remain; checked work and memory estimates include both separable passes and repeated reflection. Four-component Highlight remains refused. No final-sample correction or coordinate exception is added.

| Measurement | Before → after |
|---|---|
| seed1 Smart E/M/R |269/0/31 →272/0/28; admissions48,213,235|
| seed17 Smart E/M/R |264/0/36 →266/0/34; admissions36,162|
| Original output/reject |287/13 (seed1),284/16 (seed17), unchanged|
| Production8 guarded corpus |unchanged; saved replay8/8|
| Historical diagnostic62, both routes |34 changed samples, all toward exact;0 away|
| Guarded Smart corpus70 |only unchanged or refusal→exact|

Final boundary60 and production144 are sanitizer builds. The singleton patch only changes one-pixel axes; the144 geometries have neither singleton axis. Final-source audit reproduces all600 campaign Smart outputs under ASan/UBSan.25 fast tests and the compiled54-row sanitizer test pass (48.575s). Five one-away controls refuse. The first negative fade probe used1% (still supported); correcting it to50% establishes the intended outside-domain test without changing production.

inference:

These bounded CPU-emulation observations support the scalar Highlight branch. They do not prove all floating inputs, native AE/UCRT, custom ramps, ROI/downsample or all source geometries. Double exp remains a host import, but no first divergence was observed there in this matrix. No math-pending claim is inferred from its mere presence.

changed_files:
- `core/kirakira_highlight_gaussian.h`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/{probe_kirakira_smart_C07,trace_kirakira_numeric_F09,verify_kirakira_admission_F10}.py`
- `tools/emulation/fixtures/kirakira_highlight_{generic,no_axis}_C29.patch`
- `reports/fuzz/olmkirakira_smart_C29_scalar_highlight.json`
- `orchestra/reports/C29-kira-smart-r7{,-scalar-highlight}.md`

verify:

Run from this cluster commit, with MAIN read-only assets available. All expected counts are above. Commands redirect long output; inspect tails. The exact existing fast and compiled-test invocations are the C28 final report commands, with `clang++` resolved through `tools/ucrt_cxx.py` for the UCRT library link.

```sh
s="$PWD/orchestra/state/C29-kira-smart-r7/recheck-scalar"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 395e5d8af90321982f0493bc052f09e671bd8368:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 17; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in gaussian-highlight-scalar gaussian-highlight-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-highlight-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 17 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
for index in 48 213 235; do
 "$py" tools/emulation/probe_kirakira_smart_C07.py --ucrt-math --campaign-seed 1 --trace-index "$index" --require-exact --scratch "$s/trace$index" --report "$s/trace$index.json" > "$s/trace$index.log" 2>&1
done
git diff --check
```

Check every replay `matches_saved`, not just exit status. The independent source, seeds, parameters, worker and output hashes are retained in the machine report.

next:
- One cluster closed. Investigate the five successful-oracle non-SDR box refusals next; retain NaN boundaries and skip invalid-op NaN-sign-only work assigned to F38.
