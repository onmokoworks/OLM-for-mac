status: done

summary:
- Recover Channel 2 scalar luminance/box operations and admit finite SDR Smart inputs under the existing layout/ramp/workload limits.
- Seed 1 improves 222/0/78 → 229/0/71; fresh seed 8 improves 217/0/83 → 221/0/79 (exact/mismatch/refusal).
- Previous exact Smart results and all Classic records remain identical. No saved corpus expectations change.
- Public-bound traces identify both the weighted-sum seed and Fade Out FLOAT32 materialization boundaries.

facts:

Base: `0e3acb0f7d097c4f054dc0a7f1523d9fb307a584`. The resume WIP contained only the luminance-controls probe family and removal of the obsolete collision report. Its scratch arithmetic candidate was not production code. Remeasurement (`--jobs 1`) reproduces all 300 saved result objects, including 222 Smart exact, 78 refusals, and 287 successful original Smart renders / 13 original rejects. Classic has 48 mismatches and 252 refusals against its separate oracle; these unrelated route results are retained unchanged.

Machine evidence: `reports/fuzz/olmkirakira_smart_C16_luminance.json`; source, AEX and worker hashes are bound there. AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained Kira worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX lists RadialBlur workers; the unchanged retained Kira worker is used by absolute path.

Static original operations: constructor `181150600` sums green×0.7152 + red×0.2126 + blue×0.0722 in FLOAT64, then narrows once. `1811501b0` uses powf(value, exponent), or powf(value/fade,2)×powf(fade,exponent), then the constructor multiplies by alpha. `18114e860` materializes the Fade slider as FLOAT32 and multiplies by FLOAT32 constant at `181486c18` (0.2). The port now uses those operations in the recovered scalar pipeline, including the existing FLOAT32 percentage materialization, exponent clamp, RowSum and reciprocal normalization. The Smart rule reuses Alpha box controls with Channel 2, finite SDR input, and internal Fade in [0, FLOAT32(0.2)]. No nonfinite/HDR, approximation, Gaussian or custom-ramp admission is added.

- Seed 1 case 37 before: source exact; first seed difference word 1, AEX `9d5b393f`, Mac `9e5b393f`; 21 seed words and 5 final PF8 samples differ. Weighted-sum/powf candidate makes all paired stages and final bytes exact, public-bound.
- Initial independent candidate: 272 exact, then index 272 differs in one PF32 output word, AEX `f4c1593f`, Mac `f6c1593f`. It was not promoted. The resumed earlier run's apparent extra mismatch was an empty reference after an AEX wall timeout, not numerical evidence.
- The repaired trace binds index 272 to public Smart. Its first seed difference is word 30, AEX `d5e1e33d`, candidate `d9e1e33d`. Applying FLOAT32 Fade conversion resolves every paired stage and final output.
- Trace corrections: original default ramp producer `18123abf0` now constructs ramp payloads; flags precede ramps in full-caller arguments. Previous zero flags/zero ramps concealed the swapped ABI. Fade now follows the original builder; unbound intermediate traces are rejected, with their original error retained. No AEX numerical body is replaced. Host powf remains a retained import substitute, not native UCRT proof.
- Independent luminance matrix: 288 exact under ASan/UBSan, with three depths, tiny/odd geometry, both box modes/merges, Strength 0..1000, both opacities, default ramps/fixed colors, and five Fade values. The first run used the candidate before narrowing the Fade guard; final-source repetition also passes all 288 conditions.
- Before/after verifier: 600 sanitized campaign Smart renders and 70 corpus inputs pass. Existing fast tests: 25 passed. Compiled generic sanitizer test: 1 passed (54 internal rows including HD), 43.625 seconds. Strict production replay passes all 8 saved fixtures.

| Corpus | Before → after | Saved expectations |
|---|---|---|
| production 8 inputs | identical statuses and bytes | unchanged |
| historical diagnostic 62 inputs, both routes | indices 37 and 54 improve by 3 samples per route; 12 samples total, all toward exact | historical expectations retained |
| remaining diagnostic inputs | identical bytes | unchanged |

The full sample audit covers 140 route replays and rejects any changed sample not equal to its reference. Campaign improvement indices: seed 1 = 37,44,54,55,115,160,183; seed 8 indices are recorded in machine evidence. Original Smart success/reject is 287/13 and 288/12 respectively. All old exact hashes and all Classic results persist.

inference:

The original scalar constructor/parameter operations explain the two measured seed boundaries. The independent matrix and fresh campaign support this bounded admission, not all floating inputs, native Windows UCRT/AE, ROI/downsample or four-channel seed equivalence. The largest Channel 6 group requires a different seed/filter/aggregation representation and remains open.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `reports/fuzz/olmkirakira_smart_C16_luminance.json`
- `orchestra/reports/C16-kira-smart-r4-luminance.md`
- `orchestra/reports/C16-kira-smart-r4.md`

verify:

Run from this worktree (all scratch/build outputs are ticket-local). Commands are sequential and use one campaign job.

```sh
s="$PWD/orchestra/state/C16-kira-smart-r4/recheck-luminance"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 0e3acb0f:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 8; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family luminance-controls --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 8 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family luminance-controls --trace-index 272 --require-exact --scratch "$s/trace" --report "$s/trace.json" > "$s/trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected: campaign counts above; matrix 288 exact; audit PASS 70 corpus/2 campaigns; sample audit 140 routes, 12 improved samples, none away; trace public-bound/all stages exact; strict replay 8/8.

next:
- Continue the largest Channel 6/four-plane group. Three-cluster ticket stopping criterion is not yet met.
