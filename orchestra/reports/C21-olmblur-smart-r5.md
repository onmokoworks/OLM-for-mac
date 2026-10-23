status: done
summary:
- Three clusters closed in separate commits: PF32 non-Legacy, PF16 non-Legacy and PF16 Legacy expf coefficients with higher-repeat admission.
- Seed 1 Smart 220/3/77 -> 281/2/17; fresh seed 7 234/3/63 -> 277/1/22 (exact/mismatch/refusal).
- All 454 original exact cases preserved; all per-commit normal/sanitized campaign objects agree, with no newly admitted mismatches.
- Four independent 720-row matrices exact; each commit passes 92 retained controls and seven unit checks; strict corpus replay 39/39.
- Stop at three closed clusters. PF32 Legacy frozen-fixture conflict and nonfinite propagation remain; no native AE/UCRT promotion.

facts:
Base d16f4071faf9a30e65bafe4c62dd3caeaef0cb4e, branch orch/C21-olmblur-smart-r5. Read AGENT_GUIDE, OLMBlur ledger restrictions, GOTCHAS, compatibility plan and previous triage/fix reports. All fuzz/matrix campaigns use jobs=1. At most two task build/emulator processes run concurrently. MAIN, external emulator and cached worker remain read-only; no release-gate, ledger, other-plugin, installation or push changes.

Oracle: MAIN/plugins_2025/OLMBlur.aex SHA256 f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b. Worker: /Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker SHA256 9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7. Machine evidence: reports/fuzz/olmblur_C21_pf32.json and olmblur_C21_diagnostics.json (full provenance, result objects, traces and matrices).

Baseline `run.py --plugin olmblur --n 300 --seed 1 --jobs 1` with explicit cached worker and scratch corpus reproduced 220/3/77. Largest refusal depth/Legacy groups: PF32 non-Legacy 28, PF16 non-Legacy 21, PF32 Legacy 15, PF16 Legacy 13. Sanitized small-gate-off: seed 1 288 exact / 12 mismatch, seed 7 290 / 10; no sanitizer errors. Seed-1 transitions are 220 exact preserved, 68 refused->exact, 9 refused->mismatch, 3 mismatches unchanged. Broad gate removal is not promoted.

The C12 tracer had the C15-documented import-registration defect: the loader installs expf directly, bypassing the overridden register_import_impl. It now explicitly binds pow/powf/expf after base table creation. Corrected direct-AEX outputs bind to the cached worker for indices 40/71/182/258. First differing helper-input field is weights:

| Seed-1 index | Depth | Helper event | Word | AEX little-endian bits | Mac bits |
|---:|---:|---:|---:|---|---|
| 40 | 16 | 12 | 4 | 96501b3d | 97501b3d |
| 71 | 32 | 12 | 4 | 96501b3d | 97501b3d |
| 182 | 32 | 0 | 54 | a7a97c3f | a8a97c3f |
| 258 | 32 | 84 | 3 | b9e1c63d | b8e1c63d |

The original builder calls binary32 expf; the core evaluated binary64 exp and rounded afterward. Only PF32 non-Legacy is changed in this first cluster. Native-expf scratch candidates separately pass all 80 retained controls for each non-Legacy depth; this does not override C15's rejected Legacy candidate. PF32 candidate gate-off changes exactly indices 63/71/182/258 to exact on seed 1, and 53/165/224/228/261 on seed 7. All 288/290 preceding gate-off exact cases stay exact; other result objects are unchanged. Post-fix paired traces 71/182/258 bind, have no observed helper-input difference and exact final output.

Admission: small PF32 non-Legacy frames, legal Amount/Smoothness/Bias and Repeat 1..10, active ARGB components in [-16,16]. No clamping, output patch, case-specific coefficient selection or reference table. Existing exact-fixture precedence, source-domain scan, parameter/world/storage/downsample/work checks remain. Legacy and nonfinite domains are not expanded.

| Campaign | Before E/M/R | After E/M/R | Refusal->exact | Mismatch->exact |
|---|---|---|---:|---:|
| seed 1 n300 | 220/3/77 | 246/3/51 | 26 | 0 |
| seed 7 n300 | 234/3/63 | 253/1/46 | 17 | 2 |

Both complete normal/sanitized result sets agree (600 cases, 1,200 route executions); all original oracles, Classic results and 454 base-exact Smart results remain identical. Independent SDR matrix: 695 exact maintained / 25 mismatch->exact, 720/720. Signed-HDR matrix: 691 exact maintained / 29 mismatch->exact, 720/720. Both use six geometries, ten Amount boundaries including adjacent floats and 1000, Repeat 1/2/3/4/9/10, both Bias values, three Smoothness values, typed random/edge/opaque/transparent sources and odd padding. HDR has independent seed 21321026, every ARGB channel signed, extrema +/-16, signed zeros and subnormal/normal boundaries. All matrix builds use ASan/UBSan and host source/guard/lifecycle assertions.

Corpus baseline and final sanitized strict replay: 39/39 matches_saved; 37 exact->exact, 2 mismatch->mismatch; no rebaseline. verify_blur_C21.py passes both campaign object comparisons, matrix assertions, paired final trace and retained controls 12+80. Seven existing Classic/generic tests pass; bash -n and git diff --check pass.

inference:
- The paired trace identifies coefficient generation as the first observed divergence, not a final writer correction. Native binary32 expf closes this measured non-Legacy PF32 domain.
- The old C12 direct/cached divergence for these witnesses was a tracer import-boundary error; it is not evidence of a Windows dependency failure.
- This is original CPU AEX emulation versus public Mac fake-host execution. Native Windows UCRT, native AE/GPU and arbitrary ROI/downsample equivalence are not established.

changed_files:
- core/olmblur_worker32_nonlegacy.cpp
- mac/OLMBlur/OLMBlur.cpp
- tools/emulation/trace_olmblur_stages_C12.py
- tools/fuzz/blur_campaign_C12.py
- tools/fuzz/verify_blur_radius_C12.py
- tools/fuzz/probe_blur_expf_C21.py
- tools/fuzz/verify_blur_C21.py
- tools/fuzz/recheck_blur_C21.sh
- reports/fuzz/olmblur_C21_pf32.json
- reports/fuzz/olmblur_C21_diagnostics.json
- orchestra/reports/C21-olmblur-smart-r5.md

verify:
At the PF32 commit, from this worktree:
```sh
bash tools/fuzz/recheck_blur_C21.sh d16f4071faf9a30e65bafe4c62dd3caeaef0cb4e base pf32 32
```
Expected: campaign table above, 454 baseline exact preserved, matrices 695/25 and 691/29, final trace all exact/no helper difference, corpus 39/39 unchanged, retained 12+80, seven tests OK. Driver is serial/jobs=1, scratch-only and does not rebaseline unless C21_REBASELINE is explicitly set. Initial validation used the same constituent commands; the first SDR matrix used --native-expf-depth 32 --diagnostic-after before production was changed, and the HDR matrix used final production admission.

To reproduce the pre-fix trace at any subsequent revision:
```sh
s="$PWD/orchestra/state/C21-olmblur-smart-r5"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_stages_C12.py --source-revision d16f4071faf9a30e65bafe4c62dd3caeaef0cb4e --scratch "$s" --report "$s/nonlegacy-before.json" --indices 40 71 182 258 > "$s/nonlegacy-before.log" 2>&1
```
Expected: all four cached_binding=true; first differing weights listed above. Diagnostic expf candidates use `blur_campaign_C12.py --blur-native-expf-depth 32 --blur-small-off --blur-sanitize` at the baseline source revision; no production file is mutated.

next:
- Continue PF16 non-Legacy coefficient repair and higher-repeat admission, then remaining Legacy/nonfinite clusters.
- Preserve the C15 Legacy PF32 frozen-fixture counterexample; do not globally substitute expf on that lane.


Second cluster — PF16 non-Legacy (predecessor 5f6e8ac5):

facts:
The same original expf operation is restored in core/olmblur_worker16_nonlegacy.cpp. Admission now permits all legal non-Legacy Repeat schedules for PF16 with arbitrary uint16 source. Other numerical operations and all geometry/storage/budget/lifecycle guards remain. The original index-40 first coefficient difference is recorded above; final paired trace binds to the cached worker, has no observed helper-input differences and exact full output.

| Campaign | PF32 predecessor E/M/R | PF16 E/M/R | Refusal->exact | Mismatch->exact |
|---|---|---|---:|---:|
| seed 1 n300 | 246/3/51 | 268/2/30 | 21 | 1 |
| seed 7 n300 | 253/1/46 | 268/1/31 | 15 | 0 |

All 499 predecessor exact campaign cases preserved. Every normal/sanitized result object agrees across both seeds (1,200 sanitized route executions); Classic/oracle results unchanged. Diagnostic candidate gate-off maintains all 292/295 preceding exact cases and fixes one additional mismatch on each seed (1: index 40; 7: index 37). Independent full-uint16 720-row sanitized matrix: 711 exact->exact, 9 mismatch->exact, zero residual. Its parameter/geometric domain is the same as the first cluster's SDR matrix, with full uint16 random/edge values.

Corpus table: 37 exact->exact, 1 mismatch->exact (seed1_case000040_1e01a8a5cbd2.json), 1 mismatch->mismatch (PF32 Legacy nonfinite). The corrected saved case preserves input, parameters, reduction history, original-route oracles and Classic results; C21_updates retains its previous full result. Final strict sanitized replay is 39/39, 38 exact / 1 mismatch. Retained 12+80 and seven unit checks pass. Machine evidence: reports/fuzz/olmblur_C21_pf16.json plus updated diagnostics. No Legacy numerical source is changed by this commit.

inference:
The same coefficient operation explains the PF16 first divergence. These results support all legal small PF16 non-Legacy schedules without a Repeat-specific exclusion. They do not resolve Legacy or nonfinite PF32.

changed_files (second commit):
- core/olmblur_worker16_nonlegacy.cpp
- mac/OLMBlur/OLMBlur.cpp
- tests/fuzz_corpus/olmblur/seed1_case000040_1e01a8a5cbd2.json
- reports/fuzz/olmblur_C21_pf16.json
- reports/fuzz/olmblur_C21_diagnostics.json
- orchestra/reports/C21-olmblur-smart-r5.md

verify (at the PF16 commit):
```sh
bash tools/fuzz/recheck_blur_C21.sh 5f6e8ac5 pf32 pf16 16
```
Expected campaign table above, 499 predecessor exact maintained, matrix 711/9, final paired trace exact/no helper difference, corpus 38 exact/1 mismatch with strict replay 39/39, retained 12+80 and seven tests. No rebaseline flag is needed against committed expectations. Initial validation used the same constituent commands and the pre-promotion diagnostic matrix with --native-expf-depth 16 --diagnostic-after.

next:
Investigate Legacy PF16 higher repeats. The larger Legacy PF32 cluster retains C15's frozen-fixture coefficient conflict; its separate scratch candidate is being rechecked before any further promotion.


Third cluster — PF16 Legacy (predecessor 82e692eb):

facts:
The largest remaining group after the second commit was PF32 Legacy (seed 1: 15 refusals plus 2 mismatches; seed 7: 21 refusals plus 1 mismatch). A separate scratch-only native-expf candidate reproduces the C15 negative control: baseline retained 80/80, PF32 Legacy candidate 78/80, both failures are optional-checkin variants of legacy_24x24_smooth37_5. Both calls return zero and preserve guards/source, but exact=0. No coefficient-contract reinterpretation or fixture rebaseline is made, and core/olmblur_worker32_legacy.cpp remains unchanged. This unresolved reference/math-contract conflict blocks that promotion, so the investigation proceeds to PF16 Legacy. The independently tested PF16 Legacy candidate retains all 80 checks with no sanitizer stderr.

PF16 Legacy matrix case 292 (25x1, Amount 3.000000238418579, Smoothness 62.5, Repeat 3, Bias 1) binds the direct original AEX to the cached worker. Its first divergent helper field is weights at event 0: two symmetric words differ, first word 1, AEX 3d9b0f3f versus Mac 3c9b0f3f. The symmetric weight builder calls binary32 expf; the old port rounds binary64 exp. After correcting that operation, the same full output is exact and every observed helper input/output agrees. No integer conversion or final-store tweak is added.

Admission now permits all legal small PF16 Legacy Repeat schedules with arbitrary uint16 source values. The PF32 Legacy gate and bounded PF32 source scan remain unchanged. Existing exact owners, parameter/world/downsample/storage/budget checks and callback lifecycle stay intact.

| Campaign | PF16 predecessor E/M/R | Final E/M/R | Refusal->exact | Mismatch->exact |
|---|---|---|---:|---:|
| seed 1 n300 | 268/2/30 | 281/2/17 | 13 | 0 |
| seed 7 n300 | 268/1/31 | 277/1/22 | 9 | 0 |

All 536 predecessor exact campaign cases preserved. Every normal/sanitized result object agrees across both seeds; Classic/oracle results unchanged. Gate-off full result objects are unchanged by the PF16 Legacy coefficient fix on both seeds; the relevant PF16 Legacy subsets are 41/41 and 34/34 exact with sanitizers. Independent 720-row Legacy matrix supplies the actual numerical counterexamples: 716 exact->exact and 4 mismatch->exact (including 292), no residual and no sanitizer finding. It spans the same six geometries, ten Amount boundaries, six Repeat values, both Bias values, three Smoothness values, random/edge/opaque/transparent full-uint16 sources and odd padding.

Final corpus is unchanged by this third commit: 38 exact->exact and 1 mismatch->mismatch. Strict sanitized replay 39/39, no further expectation edits. Retained 12+80 and seven unit checks pass; bash syntax and git diff --check pass. Machine evidence: reports/fuzz/olmblur_C21_legacy16.json and updated diagnostics (pre-fix paired trace, both gate-off campaigns, rejected PF32 candidate and passing PF16 candidate).

Final totals versus ticket baseline:

| Seed | Initial E/M/R | Final E/M/R | Baseline exact preserved | Refusal->exact | Mismatch->exact |
|---|---|---|---:|---:|---:|
| 1 | 220/3/77 | 281/2/17 | 220 | 60 | 1 |
| 7 | 234/3/63 | 277/1/22 | 234 | 41 | 2 |

Independent transitive comparison verifies all 454 initial exact results, all Classic results and all original-route oracle objects unchanged. Matrix total across the three clusters is 2,880 sanitized comparisons (PF32 SDR/HDR 720 each, PF16 non-Legacy 720, PF16 Legacy 720). These are bounded evidence, not exhaustive domain or native-Windows proof. Remaining seed-1 mismatches are indices 99 (PF32 Legacy nonfinite payload) and 272 (PF32 Legacy coefficients). Remaining refusals: 15 PF32 Legacy and 2 PF32 non-Legacy nonfinite. Seed 7 retains 21 PF32 Legacy refusals, 1 PF32 non-Legacy nonfinite refusal and 1 PF32 Legacy mismatch.

inference:
The first divergent coefficient operation and exact repaired stages support the PF16 Legacy numerical change. Full uint16 admission is supported by both seed campaigns and independent boundary matrix. The PF32 Legacy fixture conflict is not proof of native Windows UCRT behavior, and no per-case math selection is introduced to hide it.

changed_files (third commit):
- core/olmblur_worker16_legacy.cpp
- mac/OLMBlur/OLMBlur.cpp
- tools/emulation/trace_olmblur_legacy_C15.py
- tools/fuzz/blur_campaign_C12.py
- tools/fuzz/probe_blur_expf_C21.py
- tools/fuzz/recheck_blur_C21.sh
- tools/fuzz/verify_blur_legacy_C15.py
- reports/fuzz/olmblur_C21_legacy16.json
- reports/fuzz/olmblur_C21_diagnostics.json
- orchestra/reports/C21-olmblur-smart-r5.md

verify (at final commit):
```sh
bash tools/fuzz/recheck_blur_C21.sh 82e692eb pf16 legacy16 16 legacy
```
Expected final campaign table, 536 predecessor exact maintained, matrix 716/4, paired trace case 292 exact/no helper difference, corpus 39/39 unchanged, retained 12+80 and seven tests. Initial validation used these constituent commands; the numerical matrix was generated before promotion with --native-expf-depth 16 --diagnostic-after.

Reproduce the rejected PF32 Legacy candidate at the final revision:
```sh
s="$PWD/orchestra/state/C21-olmblur-smart-r5"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/probe_blur_expf_C21.py --legacy --depth 32 --scratch "$s" --report "$s/legacy32-rejected.json" > "$s/legacy32-rejected.log" 2>&1
```
Expected baseline retained 80/80; candidate status error/returncode 4 with precisely the two legacy_24x24_smooth37_5 exact=0 lines. The diagnostic records the rejection and does not edit production or corpus.

next:
- Three clusters closed; stop under the ticket loop threshold. No further numerical edits are proposed here.
- Follow-up: reconcile PF32 Legacy native-expf/captured binary64-exp reference contracts before broad admission; keep the frozen fixture as a negative control.
- Follow-up: locate the first individual PF32 nonfinite arithmetic/NaN propagation difference, preserving payload/sign semantics without output-byte correction.
- Native AE/UCRT, GPU, arbitrary ROI/downsample and larger finite PF32 values remain separate unverified domains.

Final hygiene: all temporary build directories are automatically removed; scratch contains 24,146,831 bytes of logs, reports and scratch corpora, under 5 GiB. No task background build/emulator remains. No MAIN/external-worker/release-gate/ledger/other-plugin change, push, stash or history rewrite.
