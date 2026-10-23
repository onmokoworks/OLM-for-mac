status: done

summary:
- Closed three Smart clusters in separate commits: scalar luminance, four-component color box processing, and scalar maximum RGB.
- Seed 1 improves 222 exact / 0 mismatch / 78 refusal → 254 / 0 / 46; all previous exact Smart outputs persist.
- Fresh-seed checks pass; Classic campaign results remain unchanged. No saved production corpus expectation changes.
- All three clusters pass sanitizer, paired-trace and corpus monotonicity verification. Stop at the requested three closures.

facts:

Resume base `0e3acb0f7d097c4f054dc0a7f1523d9fb307a584`, branch `orch/C16-kira-smart-r4`. Read the shared guide, compatibility plan, emulator gotchas, Kira ledger restrictions and prior triage/fix reports. Verified the WIP and scratch before using them. Fresh seed-1 remeasurement reproduces all 300 previous result objects exactly, including the separate Classic oracle results. Every campaign uses `--jobs 1 --shrink-attempts 0 --shrink-seconds 0` and ticket-local scratch/corpora.

| Cluster | Commit | Seed 1 exact/mismatch/refusal | Independent campaign |
|---|---|---|---|
| resume baseline | 0e3acb0f | 222/0/78 | seed 8: 217/0/83 |
| luminance | bd1f5ece | 229/0/71 | seed 8: 221/0/79 |
| four-component color | 5440e2cb | 248/0/52 | seed 8: 243/0/57 |
| maximum RGB | this report's commit | 254/0/46 | fresh seed 9: 231/0/69 → 236/0/64 |

Seed 8's last measurement is the color commit, not a claimed final-source campaign. Final-source seed 1 and seed 9 have 287/13 and 279/21 successful/rejected original Smart renders respectively. Original rejects are not exact cases. Classic's seed-1 48 mismatches/252 refusals remain unchanged; this ticket targets Smart.

Details, exact reproduction commands, static addresses and machine evidence:

- [Luminance](C16-kira-smart-r4-luminance.md): original FLOAT64 weighted seed, FLOAT32 Fade materialization and powf. Before case 37 first differs at seed word 1 (`9d5b393f` versus `9e5b393f`). Independent case 272 exposes Fade's float-before-multiply boundary; final paired stages are exact. Final independent matrix 288/288.
- [Color](C16-kira-smart-r4-color.md): original four-component powf seed, unnormalized box passes and separate per-ray divisors/aggregation. Initial normalized-planar hypothesis is refuted at case 41 ray0 (`f3bcad43` versus `a0ab013e`), 1068 output differences. Corrected general operations make the complete planes/output exact. Final independent matrices 288+48 exact.
- [Maximum RGB](C16-kira-smart-r4-max.md): original max constructor shares the recovered scalar fade/powf path. Independent case 166 first differs at seed word 3 (`4c57653a` versus `4957653a`), 8 output differences; final paired stages/output are exact. Final independent matrix 288/288.

Machine evidence is committed in `reports/fuzz/olmkirakira_smart_C16_{luminance,color,max}.json`. All original traces must bind to the public Smart worker's output; failed/unbound transport probes are not numerical proofs. Trace corrections drive the original default-ramp producer, correct flags/ramps argument order, and materialize Fade through the original float getter/multiply. No numerical AEX function is detoured.

| Corpus audit | Luminance | Color | Maximum |
|---|---|---|---|
| production 8 inputs | unchanged | unchanged | unchanged |
| historical diagnostic sample changes, 140 route replays per cluster | 12 toward exact | 4800 toward exact | 0 |
| changes away from exact | 0 | 0 | 0 |
| strict production saved replay | 8/8 | 8/8 | 8/8 |

Historical diagnostic expectations remain provenance records; their fresh before/after sample tables are committed. Each cluster also verifies 70 corpus inputs and 600 final sanitized campaign Smart renders: 1800 campaign executions across the three commits. Final independent matrices total 912 exact conditions under ASan/UBSan. Each cluster passes 25 existing fast tests and the compiled 54-row generic sanitizer test including HD; final compiled sanitizer time is 47.460 seconds. `git diff --check` passes. Candidate patches reconstruct their saved scratch source byte-for-byte.

Identities:
- Final Mac source SHA256: `e79043da2bdbcf881fef6f49bbea79a2e637ae5910098472a0a80a2772cf69dc`.
- Original AEX SHA256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained Kira worker SHA256: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX contains Radial workers; the retained Kira worker is used by absolute path without rebuilding.

Regenerable build trees were removed. Cleanup measured 39,658,288 scratch bytes (under 5 GiB); logs, raw trace evidence and reports remain. No ticket probe/campaign process remains. No permission rejection occurred. No release gate, ledger, other-plugin, MAIN asset or external emulator/worker edits; no push, stash, install, merge or history rewrite.

inference:

Paired original operations, independent control/length matrices and fresh seeds support these bounded finite-SDR box admissions. CPU emulation with retained host imports is not native AE/UCRT, arbitrary-input, ROI/downsample or full-plugin compatibility proof. The outstanding approximation, Gaussian and nonfinite/non-SDR operations remain separate.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `core/kirakira_highlight.h`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/probe_kirakira_color_C16.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/fixtures/kirakira_{luminance,max}_C16.patch`
- `reports/fuzz/olmkirakira_smart_C16_{luminance,color,max}.json`
- `orchestra/reports/C16-kira-smart-r4{,-luminance,-color,-max}.md`

verify:

Quick final recheck (per-cluster reports give full before/after and sanitizer commands):

```sh
s="$PWD/orchestra/state/C16-kira-smart-r4/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 9; do
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/seed$seed-corpus" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected seed 1 = 254/0/46, seed 9 = 236/0/64, strict replay 8/8, clean diff check. No tolerance or expectation weakening.

next:
- Requested stop condition reached: three clusters closed.
- Seed-1 residual 46 = 13 original rejects + 33 refusals with original output. Those 33 group into approximation 14, Gaussian 11, non-SDR box 5, and nonfinite input 3 (parameter-family grouping, not claimed shared numerical causes).
- Follow-up priority: embedded IPP approximation coefficient/dispatch recovery; Gaussian Length 1/Highlight and non-Alpha constructors; finite non-SDR color/max domains; NaN propagation; native AE/UCRT and ROI/downsample proof.
