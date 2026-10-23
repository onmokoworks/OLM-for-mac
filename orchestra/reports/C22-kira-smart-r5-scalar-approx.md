status: done

summary:
- Connect recovered luminance/max scalar constructors to active box approximation and restore IPP's direct dimension ratio.
- Seed1 Smart260/0/40→263/0/37; fresh seed12 262/0/38→264/0/36.
- Every previous Smart exact and Classic campaign record persists; saved corpus expectations/samples are unchanged.
- Final576 independent conditions and600 campaign renders pass ASan/UBSan; strict saved replay8/8.

facts:

Base `8207f109`. Machine evidence: `reports/fuzz/olmkirakira_smart_C22_scalar_approx.json`. All campaigns use n300/jobs1, no shrinking and ticket-local corpus/scratch. Seed1 admissions:7,148,247. Seed12 admissions:134,173. Original Smart output/reject:287/13 and289/11. AEX/retained worker identities are unchanged from the first cluster; neither is rebuilt or modified.

Bound traces and general operation:

- Seed1/index7, PF32 23×24: first base difference is reduced-source word0, original `2eb51b3f`, Mac `4c657d3f`;526 reduced-source words and1113 final words differ. Connecting the existing recovered scalar constructor/controls and resize makes source/seed/all rays/glow/outer writer exact, public-bound.
- The initial scalar candidate passes288 independent controls under sanitizers, but the extended boundary matrix rejects index148 after148 exact rows. PF8 31×23 has one final byte difference at1061, original `fe`, candidate `fd`. This candidate is not promoted.
- Its public-bound trace identifies reduced-source word91 first: original `b556623d`, candidate `b356623d`; six source words differ. At the center column of31→15 resize, reciprocal-of-ratio scale is double `0x1.0888888888888p+1`, coordinate14.999999999999998, index14, float coefficient1. Direct31/15 is `0x1.0888888888889p+1`, coordinate15.000000000000002, index15, coefficient bits `0x27000000`. Separate float subtraction/addition makes the index14/coefficient1 formulation observably different from reading index15.
- Original `1806e7d20` horizontal table hooks capture index60 (four RGBA words per source pixel) and coefficient `00000027` at that column. Full horizontal indices/coefficients and interior vertical coefficients comprise26 entries for31×23→15×11 and50 for the reverse resize. All76 equal direct source/destination ratio calculation; `check_kirakira_resize_coefficients_C22.py` independently verifies the captured tables.
- The general resize scale is corrected for every recovered approximation owner, including Alpha. The failed scalar candidate is retained as `kirakira_scalar_resize_reciprocal_C22.patch`. Direct-ratio candidates pass288 ordinary and192 boundary conditions; the final production repetition also passes those480 and the existing Alpha boundary96, all under ASan/UBSan.
- Final traces for campaign7, independent active-Max323, and boundary148 bind to original public Smart, and every paired stage/output is exact. No original numerical function is detoured, and no expected sample/coordinate appears in production code.

Smart admission adds Channels2/4 to the recovered Alpha/box approximation controls, with finite SDR input, internal Fade in[0,0.2f], both dimensions≥4 and all previous layout/frame/angle/default-ramp/color/control restrictions. Percentage/Fade/seed materialization reuses C16's recovered operations. Classic admission and other approximation constructors remain unchanged.

| Validation | Result |
|---|---|
| Final scalar controls |288 exact, ASan/UBSan|
| Final scalar minimum/odd geometry and Length1/2/50/1000 |192 exact, ASan/UBSan|
| Alpha boundary regression after direct-ratio correction |96 exact, ASan/UBSan|
| Negative conditions |18 refusals|
| Campaign verifier |600 sanitized Smart renders, previous exact unchanged|
| Production corpus verifier |70 inputs, unchanged|
| Sample audit |140 route replays,0 changed samples|
| Strict production saved replay |8/8|
| Fast tests |25 passed|
| Compiled generic sanitizer |54 rows includingHD,1 test passed in46.022s|

No corpus rebaseline is needed. The first cluster's two diagnostic patch fixtures were converted to zero-context unified diffs to avoid whitespace warnings from embedded context; all three diagnostic patches reconstruct the recorded candidate source bytes exactly. This is a fixture representation change, not a renderer change. Final staged diff check passes.

inference:

Original coordinate tables and public-bound first-stage traces explain the new counterexample independently of the final byte. Independent matrices/fresh seeds support the bounded scalar admission. Native AE/UCRT, arbitrary floating inputs/geometry, nonfinite/HDR, other constructors, custom ramps and ROI/downsample remain separate.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/check_kirakira_resize_coefficients_C22.py`
- `tools/emulation/fixtures/kirakira_scalar_resize_reciprocal_C22.patch`
- `tools/emulation/fixtures/kirakira_resize_{linear,difference}_C22.patch` (representation only)
- `reports/fuzz/olmkirakira_smart_C22_scalar_approx.json`
- `orchestra/reports/C22-kira-smart-r5{,-scalar-approx}.md`

verify:

```sh
s="$PWD/orchestra/state/C22-kira-smart-r5/recheck-scalar-approx"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 8207f109:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 12; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
for family in approximation-scalar approximation-scalar-boundary approximation-boundary; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-scalar-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 12 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_smart_C07.py --family approximation-scalar-boundary --trace-index 148 --require-exact --scratch "$s/trace" --report "$s/trace.json" > "$s/trace.log" 2>&1
python3 tools/emulation/check_kirakira_resize_coefficients_C22.py --trace "$s/trace.json" --report "$s/coefficients.json" > "$s/coefficients.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family approximation-scalar --trace-index 323 --require-exact --scratch "$s/max-trace" --report "$s/max-trace.json" > "$s/max-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected: campaign counts/table above;576 exact matrix conditions;18 refusals;600 sanitized routes/70 corpus inputs;140 unchanged route replays; both traces all-stage exact;76 exact coordinate entries;8/8 strict replay. Reproduce the rejected hypothesis with `patch -o "$s/candidate.cpp" "$s/before.cpp" < tools/emulation/fixtures/kirakira_scalar_resize_reciprocal_C22.patch`, then trace148 with `--source "$s/candidate.cpp" --gate-off` instead of `--require-exact`; expect the recorded source/final mismatch.

next:
- Requested stopping condition reached: three separately committed clusters.
- Seed1 remaining37 =13 original rejects +24 successful-oracle refusals: Gaussian9, approximation7, non-SDR box5, nonfinite3 (parameter families, not asserted common causes).
- Follow-up: Gaussian Highlight/color owners; four-component approximation; non-SDR/NaN propagation; native AE/UCRT and ROI/downsample.
