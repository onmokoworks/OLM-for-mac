status: done

summary:
- Connect Channel 4's scalar maximum-RGB seed to the recovered float parameter/fade/powf and box pipeline.
- Seed 1 improves 248/0/52 → 254/0/46; fresh seed 9 improves 231/0/69 → 236/0/64.
- Candidate and final production independent matrices each pass 288/288 exact under ASan/UBSan.

facts:

Base: `5440e2cb`. After color recovery, Channel 4 has six SDR box refusals across Modes 1 and 2, all with successful original Smart outputs: indices 22,45,64,142,192,273. These all become exact; all previous seed-1 Smart exact results and all Classic records remain identical.

Original constructor `18114ec20` selects `18114ec60`: choose maximum RGB, clamp the scalar strength to its original float minimum, call the same `1811501b0` fade/powf helper as luminance, and multiply by alpha. The original FLOAT32 percentage and Fade getter operations are already recovered in the preceding scalar cluster. The port connects this constructor to those operations and to the recovered RowSum/reciprocal normalization. The admission extends the existing luminance rule to maximum-RGB, keeping finite SDR, non-approximated box modes, full-frame/layout, control and default-ramp restrictions. The shared predicate is renamed `UsesRecoveredSeedPipeline` now that all six box channels have separate grounded constructors.

Public-bound paired evidence:
- Campaign case 22 was already diagnostically exact before admission; it is a positive refusal witness, not a numerical counterexample.
- Independent `max-controls` index 166 (PF32 7×11) before: source exact, first seed mismatch at word 3 (AEX `4c57653a`, Mac `4957653a`); 16 seed words differ. Final output differs at 8 words, first word 226 (AEX `3cc9703e`, Mac `3bc9703e`).
- Final source: every paired source/seed/ray/glow/composed stage and final output are exact. Public output SHA256 `f38416161504318fddf6893c6967e06390d95e04367cad6248c3b3aa7278bf42`; before output SHA256 `d79c239f9e4a3167328291d9a0fa78366daff7dacc475fc1ee26318981c8ba53`.
- Candidate gate-off matrix: 288 exact conditions across 3 depths, both box modes/merges, three geometries, Strength/Glow/Source controls, fixed colors/default ramps and Fade 0/0.001/0.1/0.5/1.
- Original AEX/worker identities and CPU/import-substitute limitations are unchanged from the preceding cluster reports.

Final verification facts:
- Final-source matrix: 288 exact. Before/after verifier: 600 sanitized campaign Smart renders and 70 corpus inputs pass. Previous exact Smart and every Classic record are identical.
- Corpus sample audit: 140 route replays, zero changed samples/statuses; no rebaseline needed. Strict production replay: 8/8 saved fixtures.
- Existing 25 fast tests pass. The compiled generic ASan/UBSan test passes all 54 rows, including HD, in 47.460 seconds. No sanitizer abort/error.
- Original Smart outputs/rejects: seed 1 = 287/13, seed 9 = 279/21. Improved seed-1 indices: 22,45,64,142,192,273. Fresh-seed improvement indices and full source/worker identities are bound in `reports/fuzz/olmkirakira_smart_C16_max.json`.
- Final source SHA256: `e79043da2bdbcf881fef6f49bbea79a2e637ae5910098472a0a80a2772cf69dc`.

inference:

This is a separate scalar constructor closure supported by its original operation order, paired trace and independent controls. It does not establish nonfinite/HDR maximum seeds, approximation, Gaussian, custom ramps or native Windows UCRT/AE.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `reports/fuzz/olmkirakira_smart_C16_max.json`
- `orchestra/reports/C16-kira-smart-r4-max.md`
- `orchestra/reports/C16-kira-smart-r4.md`
- Prior cluster report links/reproduction clarification
- `tools/emulation/fixtures/kirakira_{luminance,max}_C16.patch`

verify:

At this cluster commit:

```sh
s="$PWD/orchestra/state/C16-kira-smart-r4/recheck-max"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 5440e2cb:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 9; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family max-controls --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 9 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --gate-off --family max-controls --trace-index 166 --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family max-controls --trace-index 166 --require-exact --scratch "$s/trace-after" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected seed 1 248/0/52 → 254/0/46; matrix 288 exact; trace before public-bound seed difference and 8 output differences, after every paired stage exact. Seed 9 improves 231/0/69 → 236/0/64; audit 600 sanitized routes/70 corpus inputs; sample audit 140 routes unchanged; strict replay 8/8.

next:
- Stop after this third validated cluster. Remaining Gaussian, IPP approximation, nonfinite filtering and non-SDR color constructors need separate work.

The original max gate-off candidate is preserved as
`tools/emulation/fixtures/kirakira_max_C16.patch` against `5440e2cb`.
Apply it to `$s/before.cpp` with `patch -o "$s/candidate.cpp" "$s/before.cpp" < tools/emulation/fixtures/kirakira_max_C16.patch`, then run the max-controls matrix with `--source "$s/candidate.cpp" --gate-off --require-exact`; expected 288 exact.
