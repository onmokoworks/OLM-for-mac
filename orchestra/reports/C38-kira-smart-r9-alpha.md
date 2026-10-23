status: done

summary:
- Admit finite PF32 Alpha Gaussian and approximation inputs using existing recovered pipelines.
- Seed1 Smart285/0/15 →287/0/13; fresh seed25 289/0/11 →293/0/7.
- All287 successful seed1 AEX Smart renders are exact;13 original rejections remain uncompared.
- Independent630 exact,12 negative refusals,600 sanitized campaign renders and1200 historical routes pass.

facts:

Base `2cca6ea7`. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. All campaigns n300/jobs1/no shrinking.

Seed1/index179 (signed Alpha Gaussian) and272 (HDR Alpha approximation) were exact with final admission disabled. Final public-bound F32/UCRT traces for both match every paired stage: full/reduced source, seed, all five rays, glow/full glow, composition and final output. First divergent stage=null. The Alpha constructor18114edf0 and the recovered separable Gaussian/resize pipelines already execute the original operations. This commit changes only finite PF32 source admission, preserving the existing Gaussian/approximation tuple and all layout, geometry, ramp and work limits. No renderer arithmetic changes.

Independent gate-off576 and production576 conditions are exact under ASan/UBSan. The three families are full-resolution Gaussian, box approximation and Gaussian approximation, with HDR/signed/finite-extreme inputs, six strengths, both merge modes and varied geometries. Boundary54 is exact: singleton axes for full Gaussian,4×4/4×9/9×4 approximation, length1/2/15/1000, Highlight up to500, opacity0, subnormals, signed zero and maximal finite values.12 nonfinite inputs remain refused. No hypothesis was refuted in this cluster.

| Check | Before | After |
|---|---|---|
| Seed1 Smart E/M/R |285/0/15|287/0/13;179,272 improved|
| Seed25 Smart E/M/R |289/0/11|293/0/7;29,47,85,276 improved|
| Both-route sample comparisons140 |baseline|0 changed samples|

The13 seed1 original-Smart rejections classify as11 OpenCV resize `inv_scale_x > 0` assertions (28,56,100,103,121,124,206,228,246,248,270) and2 IPP `IwException` throws (57,117). They are not exact results and are not promoted. Seed25 additionally retains successful-oracle refusal222, nonfinite Alpha box approximation, outside this finite-source admission.

Final600 Smart sanitizer replays reproduce campaign hashes and preserve every previous exact output; all600 Classic result objects are unchanged. Additional1200 sanitized historical route renders preserve568 previously exact Smart hashes from seed23/24 and all earlier rendered Classic hashes. Additional admissions match cached F32 oracle hashes (seed23:52,93,160,206,225; seed24:71,207). These are execution counts, not an exhaustive-domain claim.

Guarded F32 corpus70 has one refusal→exact (T06 seed1/index272),69 unchanged. Both-route sample audit140 has0 changed samples. Production saved replay8/8 passes. T06 saved matches39/62 →38/62 before migration →39/62 after migration, verified against complete recorded replay/current saved results. The23 failing paths remain identical. The one updated fixture `seed1_case000272_cf5cfa58c159.json` now records raw SHA256 `b2d1126ad56d2812f2f99dcc365aaac0ce29d4b5cd6cd27b6d70266ad970259b`; input/reduction fields and previous result/provenance history are preserved.26 fast tests pass; compiled sanitizer test passes (43.129s). Full T06 replay exits1 for inherited drift; it is not claimed green.

Final source SHA256 `9a0417738cb50f27aa9cab4383a9c8df6db91b7b6cf2683c4b0b54ce3f331a67`. Machine evidence: `reports/fuzz/olmkirakira_smart_C38_alpha.json`.

inference:

The existing Alpha pipeline supports the tested finite PF32 source domain. All successful-oracle seed1 residuals are closed, which does not establish complete native AE/UCRT, arbitrary ramps, ROI/downsample or other source-domain compatibility. No divergence at a still-host math import was observed. Work-budget boundaries are unchanged.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C38_alpha.json`
- One T06 fixture, this report, ticket summary, and explicit color-report reproduction commands.

verify:

Run at this cluster commit. Expected counts above. MAIN and retained workers stay read-only.

```sh
s="$PWD/orchestra/state/C38-kira-smart-r9/recheck-alpha"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/emulation/snapshot_kirakira_C34.py --revision 2cca6ea7 --scratch "$s/base" > "$s/snapshot.log" 2>&1
for seed in 1 25; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in finite-alpha-filtered finite-alpha-filtered-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family finite-alpha-filtered-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base/before.cpp" --campaign-dir "$s" --seeds 1 25 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/base/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
for i in 179 272; do
 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index "$i" --ucrt-math --require-exact --scratch "$s/trace$i" --report "$s/trace$i.json" > "$s/trace$i.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
```

Gate-off576: repeat the matrix command using `--source "$s/base/before.cpp" --gate-off`, separate scratch/report. Both traces must be public_bound=true/first_divergent_stage=null. Production replay expects8/8. Saved T06 replay uses the same command with its directory; retain the documented inherited failures. Historical seed23/24 checks use `tools/emulation/verify_kirakira_history_C34.py --campaign PATH_TO_C38_BRIGHTNESS_AFTER_SEED23 --campaign PATH_TO_C38_COLOR_AFTER_SEED24 --scratch "$s/history" --report "$s/history.json"` after reproducing those earlier campaigns; expect1200 sanitized routes and no regression. Fast/compiled sanitizer commands are in the final ticket summary.

next:
- Three clusters closed; stop as requested.
- Suggested follow-up: nonfinite Alpha approximation (fresh seed25/index222), independently tracing resize/seed/filter before any promotion. Leave work budgets to F41b and host-math divergences to F42/F43.
