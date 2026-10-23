status: done

summary:
- Connect the original four-component constructor and aggregation to directional Gaussian.
- Seed1 Smart264/0/36 → 266/0/34; fresh seed15 261/0/39 → 263/0/37.
- Every previous Smart exact and Classic campaign result persists; corpus samples unchanged.
- Independent396 final conditions,600 sanitized campaign renders and70 corpus inputs pass.

facts:

Base `d7fb906c`. All campaigns n300/jobs1/no shrinking, ticket-local corpus/scratch. Original Smart output/reject287/13 for both seeds. New admissions: seed1 indices77,186; seed15 indices188,289. Machine evidence: `reports/fuzz/olmkirakira_smart_C28_color_gaussian.json`; original AEX and retained worker identities are unchanged from the scalar report.

Seed1/index77, PF8 18×18, Channel5/Mode3: base first diverges at seed representation (1296 Mac bytes versus5184 original bytes), and all1296 final bytes differ. The recovered C16 color constructor supplies four FLOAT32 components; independent planar Gaussian calls reproduce all interleaved ray planes.

One diagnostic hypothesis incorrectly made the color aggregation normalizer1 for Gaussian because its filter is normalized. Its source, seed and all rays are exact, but glow first differs at word3: original `e684973d`, candidate `e684173f`;324 glow words and553 final bytes differ. The original caller captures normalizers `[8,0,0,0,0]` (`0000004100000000000000000000000000000000`). The directional helper returns Length independently of its filter normalization. Retaining the original Length divisor makes all stages/output exact. This is a newly measured intermediate boundary, not an output-byte adjustment. The rejected candidate is reconstructible with `kirakira_gaussian_color_unit_normalizer_C28.patch`.

Final public-bound traces for seed1/index77 and seed15/index188 are exact across source, four-component seed, all rays, glow, composed and output. Helper trace labels denote planar Mac components versus interleaved original buffers, so only complete interleaved ray planes are claimed paired for color filtering.

Admission extends finite-SDR, full-frame, non-approximated Mode3/Highlight0 to Channels3/5/6. The existing color constructor ignores Fade and uses FLOAT32 strength+1. Existing control/angle/ramp limits remain; workload and storage estimates conservatively account for four components. Classic admission is unchanged. No math import implementation changes.

Independent gate-off288 controls+108 length/alias/geometry boundaries are exact under ASan/UBSan. Final production repeats all396;7 unsupported conditions refuse. Before/after verification replays600 sanitized Smart campaign renders and70 guarded corpus inputs. All previous exact result objects and all Classic result objects persist. Existing25 tests and the compiled54-row sanitizer test pass (44.974s).

| Corpus comparison | Before → after |
|---|---|
| Production8 + diagnostic62, guarded Smart |all unchanged|
| Full140-route sample audit |0 changed samples;0 away from exact|
| Strict saved production replay |8/8; no rebaseline needed|

inference:

The original four-component constructor, captured Length normalizers and independent matrices support this bounded directional Gaussian cluster. Highlight Gaussian, approximation, arbitrary floating inputs, native AE/UCRT and ROI/downsample remain unproved. The unit-normalizer hypothesis was refuted with a new boundary; the stopping condition did not occur.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/fixtures/kirakira_gaussian_color_unit_normalizer_C28.patch`
- `reports/fuzz/olmkirakira_smart_C28_color_gaussian.json`
- `orchestra/reports/C28-kira-smart-r6{,-color-gaussian}.md`

verify:

At this cluster commit, sequential commands (expected campaigns and matrix counts above):

```sh
s="$PWD/orchestra/state/C28-kira-smart-r6/recheck-color"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show d7fb906c:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 15; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
for family in gaussian-color gaussian-color-boundary; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-color-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 15 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --gate-off --campaign-seed 1 --trace-index 77 --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 77 --require-exact --scratch "$s/trace-after" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 15 --trace-index 188 --require-exact --scratch "$s/trace-color" --report "$s/trace-color.json" > "$s/trace-color.log" 2>&1
git diff --check
```

Reproduce the failed hypothesis after the above scratch setup:

```sh
patch -o "$s/unit-normalizer.cpp" "$s/before.cpp" < tools/emulation/fixtures/kirakira_gaussian_color_unit_normalizer_C28.patch
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/unit-normalizer.cpp" --gate-off --campaign-seed 1 --trace-index 77 --scratch "$s/unit-trace" --report "$s/unit-trace.json" > "$s/unit-trace.log" 2>&1
```

Expected public-bound first divergence glow/word3,553 differing final bytes. Final traces have no divergent stage. Check all8 `matches_saved` flags in replay.

next:
- Two clusters closed; investigate four-component box approximation next.
