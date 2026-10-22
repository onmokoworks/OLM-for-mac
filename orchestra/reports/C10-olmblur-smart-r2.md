status: done

summary:
- Closed three typed small-frame Smart refusal clusters: default Amount 5 / Repeat 2 / non-Legacy, separately for PF32 SDR, PF16 and PF8.
- Seed 1 Smart improves 102/13/185 -> 122/13/165; fresh seed 4 improves 103/8/189 -> 126/8/166 (exact/mismatch/refusal).
- All 205 original base-exact campaign cases and Classic results remain byte-identical; 13 saved refusals become exact, with historical results retained.
- Each commit passes sanitizer campaigns, independent matrices, corpus replay and 12 retained controls; final corpus replay is 39/39.
- Stop at the requested three-cluster threshold. Existing numerical mismatches and other refusals remain unresolved.

facts:

Base: `99aafc300203ca9ee3de7f3c8e4bfdafc497995b`, branch `orch/C10-olmblur-smart-r2`. Read AGENT_GUIDE, plugin ledger restrictions, GOTCHAS, compatibility plan, T09/F15/F17/F18/C05 and F10/F12 methodology. MAIN, original AEX, external emulator and cached workers were read-only. No release gate, ledger, other-plugin, installed bundle, history or push changes. No numeric core changes. All temporary files were under this ticket's scratch (18 MiB at final verification), below 5 GiB; disposable build directories are removed automatically.

Machine evidence is in `reports/fuzz/olmblur_admission_C10_{pf32,pf16,pf8}.json`. Each file contains before/after/gate-off campaign provenance, exact-preservation assertions, every changed campaign result, complete corpus comparisons, the independent/negative matrix and retained controls. Commits: PF32 `9ebb348c`; PF16 `23e9cda5`; PF8 is this final commit. Each depth uses a separate typed worker and was validated/committed before changing the next depth's admission.

| Identity | SHA256 |
|---|---|
| Original MAIN `plugins_2025/OLMBlur.aex` | `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` |
| INDEX cached `radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker` | `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7` |

The worker path is `/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker`. Its historical name does not change the original Blur AEX being executed. Source, core and candidate hashes are retained in each evidence file.

**Measured campaigns.** Commands use `--plugin olmblur --n 300 --seed {1,4} --jobs 2`, scratch corpora and disabled shrinking. Baselines use ordinary `run.py`; initial gate-off uses the pre-change C05 wrapper. C10's wrapper supports reproducing arbitrary source revisions, sanitizers and the expanded gate-off. ASan/UBSan use abort-on-error and no recovery; leak checking is disabled, not claimed.

| Seed / build | Smart exact | mismatch | refusal | sanitizer abort |
|---|---:|---:|---:|---:|
| 1 baseline | 102 | 13 | 185 | 0 |
| 4 baseline | 103 | 8 | 189 | 0 |
| 1 gate-off | 257 | 41 | 0 | 2 |
| 4 gate-off | 275 | 25 | 0 | 0 |
| 1 PF32 ordinary and sanitized | 110 | 13 | 177 | 0 |
| 4 PF32 ordinary and sanitized | 109 | 8 | 183 | 0 |
| 1 PF16 ordinary and sanitized | 117 | 13 | 170 | 0 |
| 4 PF16 ordinary and sanitized | 119 | 8 | 173 | 0 |
| 1 PF8 final ordinary and sanitized | 122 | 13 | 165 | 0 |
| 4 PF8 final ordinary and sanitized | 126 | 8 | 166 | 0 |

Classic stays 13/0/287 (seed 1), 20/0/280 (seed 4). All 600 AEX Smart inputs succeed. The verifier checks all input hashes, original-route results, Classic results and existing exact bytes; every newly admitted result must equal both original Smart and gate-off results. Ordinary/sanitized result objects must match in full. Any change other than refusal -> exact is rejected. Per-commit new exact counts are 8/6, 7/10, 5/7 for seeds 1/4; respectively 205, 219 and 236 immediately preceding exact cases are preserved. There are 1,200 sanitized campaign route executions per commit, 3,600 total, with zero production sanitizer findings. Gate-off's two PF8 Legacy exceptional-conversion findings remain excluded, as in T09/C05.

**Admission rule and implementation.** Small frames (both dimensions <=24) may enter the existing generic worker at raw Amount exactly 5, Repeat exactly 2, Legacy off, either Bias, and any legal Smoothness. PF8 accepts uint8 samples; PF16 accepts full uint16 samples. PF32 additionally requires all source ARGB components finite in [0,1], including signed zero. Source values are not matched to fixtures or expected outputs. Existing geometry/storage/work/full-frame/downsample/callback checks and exact-fixture precedence remain. The PF32 scan runs only after input-storage validation and uses memcpy for odd byte strides. The normal typed numerical worker runs unchanged; this is not a copy shortcut.

Static basis: MAIN `decomp/OLMBlur.aex.c.txt`, `FUN_180004b80` (line 1968), `FUN_180002280` (789) and `FUN_180003710` (1379) implement separate typed non-Legacy workers. Their decay construction is powf(3/Amount,1/(Repeat-1)); the default schedule executes iteration powers 0 and 1. Smoothness does not enter this non-Legacy calculation. `FUN_180009b40` materializes Amount as float and Smoothness as a signed high word, already repaired by C05. This rule does not establish arbitrary Amount/Repeat libm equivalence.

**Observed boundary, retained rather than patched.** The initial diagnostic independent matrix has 727 exact / 9 mismatch, sanitizer clean: PF8 240/240, PF16 240/240, finite PF32 240/240, nonfinite PF32 7/16. First nonfinite failure: matrix index 727, PF32 1x23, 39 differing bytes / 10 words, first byte 100, AEX `2143c5ff` versus Mac `4523c17f` (different NaN payloads). No paired intermediate-stage location is claimed and no numerical correction was made. All nonfinite inputs remain outside the new PF32 admission, including seven accidental exact cases. Signed/HDR finite input is also conservatively outside this bounded rule despite those matrix successes.

**Independent and boundary validation.** The reproducible matrix uses eight geometries (singleton, short/long rows and columns, 2x3, 5x7, 24x24), both Bias values, Smoothness 1/62.5/100, random/edge/opaque/transparent/wide typed sources and odd padding. Observed PF16 inputs span 0..65535. Final admitted rows: PF8 240, PF16 240, PF32 SDR 192, all exact. PF32 outside-domain rows: 64 clean refusals. Separate one-away Amount/Repeat/Legacy and per-channel SDR boundaries include signed subnormals, 1+1 ULP, largest finite float, both infinities, quiet/signaling NaNs. That matrix has two existing integer single-pass exact controls and 41 expected clean refusals. Host assertions check source/padding preservation, unchanged output on refusal and balanced callbacks.

| Commit's full independent matrix | Exact | Refusal | Mismatch/error |
|---|---:|---:|---:|
| PF32 | 252 | 484 | 0 |
| PF16 | 462 | 274 | 0 |
| PF8 final | 672 | 64 | 0 |

The early matrices include old integer-singleton admissions; they are not counted as new promotion. Each matrix and its 43 boundary rows execute with sanitizers. At each commit, the original six 24x24 depth/Legacy fixtures with optional checkin present/absent pass 12/12, including active bytes, padding, guards and callback counts. Existing Classic/generic unit checks pass 7/7 at each commit; only the pre-existing source-text admission assertion was updated. `git diff --check` passes.

**Corpus rebaseline.** Original input bytes, parameters, geometry and reductions are unchanged. Only refusal -> exact expectations are updated, and each retains its complete previous result in `C10_updates`.

| Saved Smart cases | Before | PF32 commit | PF16 commit | PF8 final |
|---|---:|---:|---:|---:|
| Exact | 15 | 15 | 25 | 28 |
| Mismatch | 11 | 11 | 11 | 11 |
| Refusal | 13 | 13 | 3 | 0 |

PF32: all 39 results unchanged. PF16: ten default-tuple rows (indices 5, 74, 114, 122, 128, 181, 191, 203, 230, 234) improve. PF8: three rows (8, 159, 271) improve. Classic results and original-route hashes remain identical throughout. Initial replays correctly report 29/39 then 36/39 saved matches for those intentional improvements. After each narrow rebaseline, sanitized strict replay is 39/39, 78 route executions; final 28 exact / 11 mismatch are not a claim that all corpus cases are exact.

Reproduction checks also ran the final C10 gate-off wrapper and the `23e9cda5` source-revision wrapper with seed 1, n=40, jobs=2: both reproduce all 40 prior complete result objects. Counts are 35 exact / 5 mismatch gate-off, and 16 exact / 1 mismatch / 23 refusal for the predecessor. The verifier was rerun without `--rebaseline` after corpus updates; historical results were correctly matched and all assertions passed.

inference:

- The gate-off, fresh-seed, independent typed matrices and unchanged worker branches support these bounded default-schedule admissions. They are finite CPU-AEX/fake-host evidence, not universal input equivalence, native Windows UCRT/AE, installed Mac AE, GPU or ROI/downsample certification.
- Unrestricted PF32 admission is refuted by the new nonfinite boundary. The first divergent arithmetic operation for those payload differences remains unlocated; no patch or tolerance conceals them.
- Three typed refusal domains have closed, meeting this ticket's stop threshold. This does not close the existing numerical mismatch signatures or the rest of the generic-small-fixture guard.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp` — default-schedule admission plus PF32 SDR guard; no renderer arithmetic changed.
- `tests/test_olmblur_generic_beta_lane_20260820.py` — existing predicate assertion updated.
- `tools/fuzz/blur_admission_campaign_C10.py` — revision/sanitizer/gate-off campaigns.
- `tools/fuzz/verify_blur_small_C10.py` — deterministic independent and one-away boundary matrices.
- `tools/fuzz/verify_blur_admission_C10.py` — monotonic campaign/corpus checks, narrow rebaseline, retained controls.
- `tests/fuzz_corpus/olmblur/seed1_case{000005,000074,000114,000122,000128,000181,000191,000203,000230,000234}_ced0f1718a01.json` — ten PF16 refusal -> exact records, prior results retained.
- `tests/fuzz_corpus/olmblur/seed1_case{000008,000159,000271}_92552f06afe6.json` — three PF8 refusal -> exact records, prior results retained.
- `reports/fuzz/olmblur_admission_C10_{pf32,pf16,pf8}.json` — separate per-commit evidence.
- `orchestra/reports/C10-olmblur-smart-r2.md` — this report.

verify:

From this worktree, the following reproduces the final commit's predecessor, gate-off, final production/sanitizers, independent matrices, corpus transitions and retained controls. It does not edit the checkout/corpus. The previous source is read from git; core files are unchanged. Historical replay intentionally exits 1 because three saved results improved; the final replay must exit 0. Logs and generated corpora stay in this ticket's scratch.

```sh
s="$PWD/orchestra/state/C10-olmblur-smart-r2"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker
for seed in 1 4; do
  python3 tools/fuzz/blur_admission_campaign_C10.py --blur-source-revision 23e9cda5 --plugin olmblur --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/pf16-$seed.json" --corpus "$s/pf16-$seed-corpus" > "$s/pf16-$seed.log" 2>&1
  python3 tools/fuzz/blur_admission_campaign_C10.py --blur-small-off --blur-sanitize --plugin olmblur --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/off-$seed.json" --corpus "$s/off-$seed-corpus" > "$s/off-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/pf8-$seed.json" --corpus "$s/pf8-$seed-corpus" > "$s/pf8-$seed.log" 2>&1
  python3 tools/fuzz/blur_admission_campaign_C10.py --blur-sanitize --plugin olmblur --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/pf8-san-$seed.json" --corpus "$s/pf8-san-$seed-corpus" > "$s/pf8-san-$seed.log" 2>&1
done
python3 tools/fuzz/verify_blur_small_C10.py --diagnostic --scratch "$s" --report "$s/matrix-off.json" > "$s/matrix-off.log" 2>&1
python3 tools/fuzz/verify_blur_small_C10.py --admitted-depths 8 16 32 --scratch "$s" --report "$s/matrix-pf8.json" --require-exact > "$s/matrix-pf8.log" 2>&1
python3 tools/fuzz/verify_blur_small_C10.py --admitted-depths 8 16 32 --boundary-only --scratch "$s" --report "$s/boundaries-pf8.json" --require-exact > "$s/boundaries-pf8.log" 2>&1
python3 tools/fuzz/blur_admission_campaign_C10.py --blur-source-revision 23e9cda5 --blur-sanitize --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/pf16-replay.json" --corpus "$s/replay-corpus" > "$s/pf16-replay.log" 2>&1
python3 tools/fuzz/blur_admission_campaign_C10.py --blur-sanitize --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/pf8-replay.json" --corpus "$s/replay-corpus" > "$s/pf8-replay.log" 2>&1
python3 tools/fuzz/verify_blur_admission_C10.py --scratch "$s" --report "$s/recheck-pf8.json" --before pf16 --after pf8 --base 23e9cda5 --admitted-depths 8 16 32 > "$s/recheck-pf8.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820 > "$s/tests-pf8.log" 2>&1
git diff --check
```

Expected: final Smart 122/13/165 and 126/8/166, all ordinary/sanitized results equal; gate-off 257/41/2 sanitizer aborts and 275/25/0. Diagnostic matrix 727 exact / 9 mismatch; production matrix 672 exact / 64 refusal; boundary matrix 2 exact / 41 refusal. Verifier: 5/7 new exact for this final commit, all predecessor exact preserved, three corpus improvements, 12 retained controls. Final strict replay 39/39; seven unit checks OK. No `--rebaseline` is needed to recheck committed expectations.

The original 102/13/185 and 103/8/189 baselines can be regenerated with the same campaign wrapper and `--blur-source-revision 99aafc300203ca9ee3de7f3c8e4bfdafc497995b`; the per-commit reports retain the complete transitive monotonicity checks. To recheck an earlier commit in isolation, use its report's exact commands at that commit. All report/core/AEX hashes are preserved; freshly compiled Mach-O hashes may differ.

next:
- Follow up on remaining Smart generic-small-fixture refusals (seed 1: 165; seed 4: 166), especially other repeated schedules and Legacy paths.
- Locate paired intermediate differences for PF32 nonfinite payloads and Legacy exceptional-value writers before expanding those domains. Keep the gate-off PF8 NaN/Inf sanitizer counterexamples excluded.
- Existing Smart numerical mismatches remain 13/8 in the two campaigns and 11 in the saved corpus. Native AE/UCRT, GPU and ROI/downsample verification remain separate work.
