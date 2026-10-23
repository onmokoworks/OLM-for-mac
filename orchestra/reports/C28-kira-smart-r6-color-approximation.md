status: done

summary:
- Recover four-component box approximation and helper-scaled aggregation normalizers.
- Seed1 Smart266/0/34 → 269/0/31; fresh seed16 258/0/42 → 264/0/36.
- Previous exact outputs persist;310 historical diagnostic samples change only toward exact.
- Independent828 final conditions,600 sanitized campaign renders and70 corpus inputs pass.

facts:

Base `37e21ddf`; n300/jobs1/no shrinking/ticket-local scratch and corpora. Original Smart output/reject287/13 (seed1) and275/25 (seed16). Admissions: seed1 indices214,222,282; seed16 indices32,51,107,151,187,261. Machine evidence: `reports/fuzz/olmkirakira_smart_C28_color_approximation.json`; original AEX and retained worker identities remain unchanged.

Seed1/index214, PF16 34×23, Channel6/Mode1/approximation: base reduced-source word0 is original `4617203f` versus Mac `002c763f`;744 source words and55 final words differ. Connect C22's recovered linear resize/full-resolution composition to the C16 four-component seed/filter owner.

A diagnostic retaining raw UI lengths as aggregation divisors makes source, seed and all rays exact but first differs at glow word0 (`0fd01440` original, `7b31ab3f` candidate);690 glow words and524 final words differ. Original caller normalizers are `[204,5,6,23,9]`, corresponding to half-resolution helper lengths and the scaled Highlight kernel area. Raw controls were408,10,12,47 and Highlight2. Computing normalizers from the same scaled lengths used by the helpers makes every stage and final output exact. The failed raw-normalizer candidate is retained as `kirakira_color_approx_raw_normalizer_C28.patch`; no sample-value correction occurs.

Final public-bound traces cover campaign214 (Channel6/Mode1), fresh seed16/index151 (Channel5/Mode2), independent approximation-color/index330 (Channel3), and Highlight/index107 (PF32 Mode2/Radius500). All full source/seed/ray/glow/composition/output stages are exact. Original numerical bodies/import scaffold are unchanged. This does not claim native UCRT.

Admission adds Channels3/5/6 to existing finite-SDR box approximation, retaining dimensions≥4, full-frame/layout, parameter, angle and default-ramp boundaries. Directional Gaussian approximation remains excluded. Color aggregation uses helper-scaled Length or its Mode2 cubic normalizer, and scaled Highlight kernel-area with the recovered Mode2 repeated squares. Full-resolution color paths use scale1 and preserve their values.

Independent gate-off boundary288 conditions pass. Final production432 controls+288 length/odd/minimum geometry+108 Highlight conditions (through500) are exact under ASan/UBSan;18 unsupported conditions refuse. Sanitized campaign replay covers600 Smart renders and70 corpus inputs. Existing25 tests and the compiled54-row generic sanitizer test pass (44.865s).

| Corpus comparison | Before → after / expectation action |
|---|---|
| Saved production8 |unchanged; strict8/8, no rebaseline needed|
| Guarded diagnostic62 |61 unchanged; shrunk214 refusal→exact|
| Diagnostic214 Classic and Smart samples |155 mismatching samples per route→0;310 total changes all exact|
| Other sample comparisons |unchanged;140 total route comparisons;0 away from exact|

Historical diagnostic expectations remain preserved as historical observations. Production expectations, inputs and oracle provenance are unchanged. Both diagnostic patch fixtures reconstruct their recorded failed-source bytes exactly. Every one of the original263 seed1 exact result objects and all300 Classic result objects remain identical at the final source.

inference:

The helper lengths and normalizer arrays provide the causal boundary for this approximation cluster. Fresh/independent matrices support the bounded promotion, not arbitrary floating inputs, Gaussian approximation, native AE/UCRT or ROI/downsample. The raw-normalizer hypothesis was refuted with a new intermediate boundary, so the stopping condition did not occur.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/fixtures/kirakira_color_approx_raw_normalizer_C28.patch`
- `reports/fuzz/olmkirakira_smart_C28_color_approximation.json`
- `orchestra/reports/C28-kira-smart-r6{,-color-approximation}.md`

verify:

At this cluster commit, sequential commands (expected counts in the tables above):

```sh
s="$PWD/orchestra/state/C28-kira-smart-r6/recheck-color-approx"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 37e21ddf:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 16; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
for family in approximation-color approximation-color-boundary approximation-color-highlight; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-color-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 16 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --gate-off --campaign-seed 1 --trace-index 214 --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 214 --require-exact --scratch "$s/trace-after" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family approximation-color --trace-index 330 --require-exact --scratch "$s/trace-color" --report "$s/trace-color.json" > "$s/trace-color.log" 2>&1
git diff --check
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 16 --trace-index 151 --require-exact --scratch "$s/trace-mode2" --report "$s/trace-mode2.json" > "$s/trace-mode2.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family approximation-color-highlight --trace-index 107 --require-exact --scratch "$s/trace-highlight" --report "$s/trace-highlight.json" > "$s/trace-highlight.log" 2>&1
```

Reproduce the failed candidate after that setup:

```sh
patch -o "$s/raw-normalizer.cpp" "$s/before.cpp" < tools/emulation/fixtures/kirakira_color_approx_raw_normalizer_C28.patch
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/raw-normalizer.cpp" --gate-off --campaign-seed 1 --trace-index 214 --scratch "$s/raw-trace" --report "$s/raw-trace.json" > "$s/raw-trace.log" 2>&1
```

Expected first divergence glow/word0 and524 final words differing. Final traces are public-bound with no divergent stage; strict replay has8/8 `matches_saved`.

next:
- Three requested clusters closed; stop this ticket.
- Seed1 residual31 =13 original rejects +18 successful-oracle refusals: Gaussian6, approximation4, non-SDR box5, nonfinite3. These are parameter-family groupings, not proved shared root causes.
