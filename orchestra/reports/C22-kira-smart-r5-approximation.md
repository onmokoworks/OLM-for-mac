status: done

summary:
- Recover active Alpha/box approximated-input resize and full-resolution source composition.
- Seed 1 Smart 254/0/46 → 258/0/42; fresh seed 10 243/0/57 → 252/0/48 (exact/mismatch/refusal).
- Prior Smart exact and all Classic campaign records persist. No saved corpus expectations change.
- Independent 240 conditions exact under ASan/UBSan; 18 negative refusals; 600 sanitized campaign renders and 70 corpus inputs pass.

facts:

Base `0b95856c`, after C16. All campaigns use `--jobs 1 --shrink-attempts 0 --shrink-seconds 0` and ticket-local scratch/corpora. The initial seed-1 run measures 287 successful original Smart outputs and 13 original rejects; fresh seed 10 has 285/15. Original rejects are not exact cases. Seed-1 new admissions are 70,112,113,177; the machine report retains all nine seed-10 transitions.

Machine evidence: `reports/fuzz/olmkirakira_smart_C22_approximation.json`, including source/worker/AEX identities, paired stages, complete corpus comparisons, campaign transitions and sanitizer logs. AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained Kira worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX lists Radial workers; the retained Kira worker is used by absolute path, without rebuilding. Strict saved replay selects its saved Kira worker despite the preliminary default-worker log.

First-stage evidence and experiments:

- Current base, seed1/index70 PF16 6×17: full-resolution source exact; reduced source first differs at word0, original `80b7793e`, Mac `009a183f`; 357 final words differ. Original trace binds to public Smart.
- Reconstructed C13 weighted-sum bilinear candidate: reduced source/seed/rays/glow exact; first enlarged-glow difference word35, original `cfea863e`, candidate `ceea863e`; six final words differ.
- Original destination-write PCs identify IPP `1803238a0` edge and `1806e6e80` interior interpolation. Disassembly at `180323baf/bb3/bb9` and `1806e6ed9/ee3/ee9` uses separate subtraction, multiplication and addition: `a + (b-a)*weight`. This general operation makes case70 all-stage exact.
- Independent ASan/UBSan matrix rejects the float-coordinate candidate after 53 exact cases: index161, PF16 7×11, two final words differ, first word158 original `f162`, candidate `f062`. Its bound trace identifies reduced-source word8 as the first difference (`22cecc3e` versus `1ececc3e`).
- Compute the coordinate/fraction in double, then narrow the fractional coefficient to float. This makes index161 all-stage exact. Final original vertical-row hooks capture 8+15+5+9 coefficient words across both resizes of the two witnesses; all 37 equal that operation. Original numerical functions are not detoured. Both final traces bind to public Smart and every paired stage/output is exact.
- The two rejected arithmetic candidates are reproducible from the base source using committed `kirakira_resize_{linear,difference}_C22.patch`. Neither was admitted.

The production operation uses explicit-dimension reciprocal scales, replicated boundaries and separate float SUB/MUL/ADD. The original owner resizes glow, then composes against the original full-resolution source. Recovery is restricted to Alpha/Mode1-or2 approximation; other approximation owners retain their existing operations. Smart admission reuses the bounded Alpha box controls, default ramps, colors, finite SDR input, full-frame/layout/angle/work limits and additionally requires both dimensions≥4. Classic admission is unchanged. No per-image expected values, tolerance, or output-byte corrections occur.

| Validation | Result |
|---|---|
| Final independent active matrix | 144/144 exact, ASan/UBSan |
| Minimum/odd geometry and Length1/2/50/1000 matrix | 96/96 exact, ASan/UBSan |
| Small workspace / unsupported controls / HDR negatives | 18 refusals |
| Campaign before/after verifier | 600 sanitized Smart renders; 70 corpus inputs; pass |
| Production saved corpus | 8/8 unchanged, strict replay |
| Historical diagnostic corpus, both routes | 3742 changed samples, all toward exact; zero away |
| Full sample audit | 140 route replays |
| Existing fast tests | 25 passed |
| Compiled generic sanitizer | 54 internal rows including HD, 1 test passed in 43.226s |

Seed-1 ordinary campaign precedes cosmetic const/indent cleanup; final-source sanitizer campaign replay independently verifies all its exact hashes. Final seed10, matrices, traces, corpus and compiled checks bind the final source. `git diff --check` passes.

inference:

The first-stage differences, original instruction order, coefficient observations and independent matrices support this bounded CPU-emulation rule. They do not prove arbitrary float/geometry, non-Alpha approximation, native AE/UCRT, custom active ramps, ROI/downsample or all-plugin compatibility.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/fixtures/kirakira_resize_{linear,difference}_C22.patch`
- `reports/fuzz/olmkirakira_smart_C22_approximation.json`
- `orchestra/reports/C22-kira-smart-r5{,-approximation}.md`

verify:

At this cluster commit, sequential commands (the base source and every generated artifact stay in ticket scratch):

```sh
s="$PWD/orchestra/state/C22-kira-smart-r5/recheck-approximation"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 0b95856c:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 10; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
for family in approximation-active approximation-boundary; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-active-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 10 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 70 --require-exact --scratch "$s/trace70" --report "$s/trace70.json" > "$s/trace70.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family approximation-active --trace-index 161 --require-exact --scratch "$s/trace161" --report "$s/trace161.json" > "$s/trace161.log" 2>&1
git diff --check
```

Expected: counts and corpus table above; both traces public-bound/all stages exact. Candidate reproduction uses `patch -o "$s/candidate.cpp" "$s/before.cpp" < tools/emulation/fixtures/kirakira_resize_difference_C22.patch` and the same trace161 command with `--source "$s/candidate.cpp" --gate-off` instead of `--require-exact`; expect the recorded reduced-source and final mismatch.

next:
- One cluster closed. Seed1 residual42 = 13 original rejects + 29 successful-oracle refusals.
- Continue Gaussian and other constructor/approximation families; retain the unproved non-SDR/nonfinite boundaries.
