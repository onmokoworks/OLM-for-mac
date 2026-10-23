status: done
summary:
- Admit finite PF32 luminance/max input through the existing full-resolution Smart Gaussian tuple.
- Seed1 stays 287/0/13; seed106 improves 283/0/17 to 284/0/16 (case248).
- Independent gate-off and production each pass 612 exact conditions under ASan/UBSan; eight negative conditions refuse.
- Preserve all 570 prior exact Smart and all 600 Classic campaign results, plus 70 corpus results.

facts:

Base f3da6fe1f89f0742a0c57d2c7a41399128c62c14. Campaigns use n300/jobs1/no shrinking and ticket-local scratch corpora. Original Smart output/rejection is 287/13 and 286/14 for seeds1/106. The only new admission is seed106/index248, PF32 2x11 signed Max Gaussian. Output SHA256 0372003a28a4dfb1b72f60b01de78291f53806a2b13334bd9ee78229635ec4e7. No render arithmetic changed.

The public-bound original trace has exact source/source_full, but first differs at seed word3: AEX little-endian 0000c0ff versus Mac 0000c07f, five seed words. Ray2 has 22 NaN-sign differences; all other rays, glow, glow_full, composition and final bytes are exact. No all-stage equality is claimed. Existing aggregation removes these raw internal differences.

Gate-off 576 ordinary +36 boundary and production 576+36 are exact under ASan/UBSan. Eight nonfinite source negative conditions refuse cleanly. The independent matrix includes both scalar constructors, HDR/signed/extreme finite input, both merges, tiny/odd geometry and strength/control boundaries. The production predicate retains IsSmartDirectionalGaussianTuple, including its Fade Out, angle, ramp, geometry and layout restrictions, and scans all source components for finiteness.

| Seed | Before Smart E/M/R | After |
|---|---|---|
|1|287/0/13|287/0/13|
|106|283/0/17|284/0/16|

The campaign verifier passes 600 sanitized Smart renders, checks input/parameter binding, preserves all 570 old exact result objects and admits case248 exactly. An additional comparison confirms all 600 Classic result objects unchanged. Corpus before/after: production8 unchanged; historical T06 62 unchanged; no expectation migration or rebaseline. 26 existing fast tests pass. No compiled standalone sanitizer-test claim; sanitizer evidence comes from independent matrices, campaign replay and corpus renders.

Mac source SHA256 9d8735fd8ae7f7f6c471c340e90dea820d66c1fb4e3fd86725b9de60b5b242c7. Original AEX 60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7. Retained F46 worker 6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903. Compressed full reports and uncompressed SHA256 manifest: C55-kira-smart-r2/scalar/.

inference:

The existing Gaussian pipeline supports this bounded finite-source admission. Internal NaN sign differences are not treated as equal; the public output proves their disappearance for these conditions. This is CPU emulation evidence, not native-AE/all-input proof. Color Gaussian traces have a separate public-binding issue under investigation and are not admitted in this commit.

changed_files:
- mac/OLMKiraKira/OLMKiraKira.cpp
- tools/emulation/probe_kirakira_filtered_C50.py (Gaussian matrices, campaign witness selection and explicit trace-output binding diagnostics; scalar approximation generator prepared for the next cluster)
- This report, ticket report, and scalar evidence directory.

verify:

At this commit, run from the worktree. Expected counts are above. All commands must succeed except no intentionally failed trace is included here.

```sh
s="$PWD/orchestra/state/C55-kira-smart-r2/recheck-scalar"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show f3da6fe1:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/base.cpp"
for seed in 1 106; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-gaussian --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-gaussian --boundary --require-exact --scratch "$s/boundary" --report "$s/boundary.json" > "$s/boundary.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-gaussian --negative --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base.cpp" --campaign-dir "$s" --seeds 1 106 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-gaussian --seed 106 --case-index 248 --trace-index 0 --gate-off --require-exact --scratch "$s/trace" --report "$s/trace.json" > "$s/trace.log" 2>&1
git diff --check
```

Repeat both positive matrices with --source "$s/base.cpp" --gate-off in separate scratch/report paths to reproduce the initial admission experiment (612 exact).

next:
- Continue finite color Gaussian and finite scalar approximation; neither is admitted here.
