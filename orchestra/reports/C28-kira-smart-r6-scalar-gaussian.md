status: done

summary:
- Connect the recovered luminance/max scalar constructor to directional Gaussian Smart rendering.
- Seed1 Smart263/0/37 → 264/0/36; seed13 remains255/0/45 (exact/mismatch/refusal).
- Final independent648 conditions exact;7 negative refusals; seed14 improves262/0/38 → 264/0/36.

facts:

Base `1ccc9cd494617dde93a1b9eb3882de0c2aa9d25c`. Re-measurement uses n300, seed1, jobs1, no shrinking, ticket-local scratch/corpus. Original Smart produces287 outputs and13 rejects. Gaussian is the largest remaining parameter-family group (9 successful-oracle refusals); those group labels do not establish shared root causes.

Seed1/index12, PF16 2×18, Channel4/Mode3/no Highlight: base gate-off output is exact, but seed word34 differs (`38a15b3f` original, `37a15b3f` Mac), followed by ray3 word33 (`47c6223e` versus `46c6223e`). The final pixel match does not establish intermediate correctness. The existing C16 scalar constructor already recovers FLOAT32 percentage/fade materialization and powf, while the Gaussian Max path still selected its legacy double constructor. Connecting that existing constructor and scalar Gaussian workspace contract makes every paired stage exact. No math approximation or imported implementation is changed; native UCRT remains unproved.

Final public-bound traces for campaign12 (Max) and independent gaussian-scalar/index300 (luminance) match source, seed, all five rays, glow, composition and output. Both traces execute original numerical bodies. The existing host-powf scaffold matches the retained worker and is explicitly not native UCRT evidence.

Admission remains finite SDR/full-frame, non-approximated Mode3, Highlight0, Channels1/2/4, existing bounded controls/default ramps/angle and combined workload limits. Channels2/4 additionally require internal Fade in[0,0.2f]. Classic admission is unchanged.

The independent gate-off matrix passes576 conditions under ASan/UBSan. Final production repeats all576 and adds72 minimum/odd geometry and Length1/2/50/1000 conditions;7 unsupported conditions refuse. Existing25 fast tests pass; the compiled54-row generic sanitizer test passes in45.273s. Seed1 preserves all263 previously exact Smart result objects and all Classic result objects. Seed13 has no newly eligible tuple, so seed14 is additionally measured rather than treating seed13 as positive new-domain evidence.

Fresh seed14 admits indices51 and174; its original Smart output/reject is286/14. Seed1 admits12. All previous Smart exact and all Classic result objects remain unchanged across900 campaign rows. The sanitizer campaign verifier independently renders900 Smart routes. Machine evidence: `reports/fuzz/olmkirakira_smart_C28_scalar_gaussian.json` retains identities, comparisons, stage traces and logs. Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` (absolute path in provenance, no rebuild).

| Corpus comparison | Before → after |
|---|---|
| Production8 + diagnostic62, guarded Smart | all unchanged |
| Full140-route sample audit |0 changed samples;0 away from exact|
| Strict saved production replay |8/8 matches_saved; no rebaseline needed|

inference:

The shared constructor, bound stage comparisons and independent controls support this bounded directional scalar Gaussian connection. They do not establish Highlight, four-component Gaussian, arbitrary floating inputs, custom ramps, ROI/downsample or native AE/UCRT compatibility.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C28_scalar_gaussian.json`
- `orchestra/reports/C28-kira-smart-r6-scalar-gaussian.md`

verify:

Run at this cluster commit, sequentially:

```sh
s="$PWD/orchestra/state/C28-kira-smart-r6/recheck-scalar"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 1ccc9cd494617dde93a1b9eb3882de0c2aa9d25c:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 13 14; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
for family in gaussian-scalar gaussian-scalar-boundary; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-scalar-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 13 14 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --gate-off --campaign-seed 1 --trace-index 12 --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 12 --require-exact --scratch "$s/trace-after" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family gaussian-scalar --trace-index 300 --require-exact --scratch "$s/trace-luma" --report "$s/trace-luma.json" > "$s/trace-luma.log" 2>&1
git diff --check
```

Expected matrices576+72 exact,7 refusals; final traces public-bound/all stages exact. Check every `matches_saved` in replay, not just its exit status.

next:
- Investigate remaining four-component Gaussian and approximation owners.
