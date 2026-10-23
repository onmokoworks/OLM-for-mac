status: done
summary:
- Recover original IPP one-axis border interpolation; admit finite PF32 color box approximation.
- Seed105 Smart283/0/17 →285/0/15; seeds1 and106 stay287/0/13 and282/0/18.
- All285 successful seed105 original Smart renders are exact. Preserve852 prior exact Smart and900 Classic result objects.
- Independent486 exact/12 negative refusals,900 sanitized campaign renders,70 corpus and140 sample comparisons pass.

facts:

Base `00338f78`. The first unrestricted finite color-approximation gate-off matrix produced369 exact/63 mismatches under ASan/UBSan. It covers Channels3/5/6, Modes1/2, both merges, HDR/signed/extreme finite inputs and varied Strength/Fade. First failure matrix5 (source index3149), PF32 7×11:2 differing words/3 bytes; first word87 AEX `01000000`, Mac `00000000` (byte348). This refuted the existing-operation admission hypothesis and supplied a new boundary. No failed case was promoted.

The paired-trace helper previously linked only4 UCRT objects and overrode3 math imports. It now links the7 F46 objects and binds all10 supported imported math functions with their float/double ABI. The original numerical AEX functions still execute. All3 recorded focused traces bind their final raw bytes to the retained public F46 worker.

Before correction, matrix5's earliest raw divergence is reduced-source word40: AEX negative NaN `0000c0ff`, Mac positive NaN `0000c07f` (one differing word). Source-full is exact, and the later reduced glow is exact. Enlarged glow first differs at word0: AEX `00000000`, Mac `0000c0ff`;24 words differ there. Composition differs in2 words. These are explicit raw differences, not tolerance-based stage equality.

Original `FUN_1803238a0`, MAIN `decomp/OLMKiraKira.aex.c.txt` lines714765ff, separates border regions: top/bottom rows execute only horizontal SUB/MUL/ADD, including corners with replicated X indices; left/right borders in interior rows execute only vertical SUB/MUL/ADD. The port previously evaluated both axes everywhere, even on replicated borders. Restore those geometric branches, retaining interior interpolation and all coefficients. This is an operation-level fix, not a coordinate-specific value patch or a general zero-weight shortcut.

The exact scratch candidate is reproducible by applying `tools/emulation/fixtures/kirakira_resize_edges_C50.patch` to the base source. Its gate-off matrix is432/432 exact;54 additional minimum/odd-geometry, length, Highlight, opacity and finite-bit boundary conditions are exact. Corrected trace5 retains its raw source/seed/ray differences, but glow, enlarged glow, composition and final output are exact. Corrected signed matrix40 is exact at every paired stage. Final comparisons remain strictly bit-exact.

Production admits finite PF32 Channels3/5/6 through the existing box-approximation tuple. Gaussian color, nonfinite color, geometry/layout, ramps, controls, angle and work budgets retain their guards. Production432+54 conditions are exact with ASan/UBSan, and12 nonfinite-source negative conditions refuse.

| Seed | Before Smart E/M/R | After | Improved indices |
|---|---|---|---|
|1|287/0/13|287/0/13|none|
|105|283/0/17|285/0/15|199,285|
|106 (fresh)|282/0/18|282/0/18|none|

Each campaign completed300 cases, jobs1, no shrinking, F46, scratch corpus. All852 previous exact Smart result objects and all900 Classic result objects persist. The campaign verifier replays900 Smart cases under ASan/UBSan and matches ordinary hashes/statuses. Corpus table: production8 unchanged; T06 62 unchanged; both-route140 sample comparisons have0 changed samples. No corpus rebaseline is needed. Saved production replay8/8 passes. No claim is made that historical T06 saved expectations are current.26 fast tests pass; compiled sanitizer test54 rows passes (47.371s).

Source SHA256 `13b7fba3bd71a905e11f32cc1d9906330ab9c6eb6743d162f3effa081ee2c835`. Original AEX `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; F46 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. Complete reports/traces/logs and uncompressed hashes: `C50-kira-smart-r1/color/`. Before campaigns are the preceding Gaussian evidence. This commit also retains the Gaussian test logs as `.log.txt` (plain `.log` is gitignored).

inference:

Evaluating an unused axis at an edge can introduce NaN from a nonfinite neighbor; the original branches, bound trace and corrected matrices support this cause. Intermediate NaN sign identity remains unclaimed where original downstream aggregation removes it. The tested domain is supported, not arbitrary native AE/ROI/downsample/custom-ramp behavior. Only one admission hypothesis was refuted, with a new boundary; the stop condition did not occur.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_filtered_C50.py`
- `tools/emulation/probe_kirakira_smart_C07.py` and `trace_kirakira_numeric_F09.py` (F46 trace binding)
- `tools/emulation/fixtures/kirakira_resize_edges_C50.patch`
- Cluster/ticket reports and committed evidence.

verify:

Run at this cluster commit. Expected counts are above. Reuse the Gaussian report's campaign loop with base revision `00338f78` and seeds1/105/106; then run:

```sh
s="$PWD/orchestra/state/C50-kira-smart-r1/recheck-color"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 00338f78:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain color-approx --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain color-approx --boundary --require-exact --scratch "$s/boundary" --report "$s/boundary.json" > "$s/boundary.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain color-approx --negative --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --source "$s/before.cpp" --domain color-approx --gate-off --scratch "$s/old-matrix" --report "$s/old-matrix.json" > "$s/old-matrix.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
for i in 5 40; do
 "$py" tools/emulation/probe_kirakira_filtered_C50.py --domain color-approx --trace-index "$i" --require-exact --scratch "$s/trace$i" --report "$s/trace$i.json" > "$s/trace$i.log" 2>&1
done
"$py" tools/emulation/probe_kirakira_filtered_C50.py --source "$s/before.cpp" --domain color-approx --gate-off --trace-index 5 --scratch "$s/old-trace" --report "$s/old-trace.json" > "$s/old-trace.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --scratch "$s/corpus" --report "$s/corpus.json" > "$s/corpus.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
git diff --check
```

The old matrix intentionally records63 mismatches; old trace5 intentionally records a mismatch and must be public_bound=true. New traces are public_bound=true/exact output; trace40 has no stage divergence. Use the Gaussian report's verifier/replay commands for the generated campaigns and saved production corpus. All tools leave expectations untouched.

next:
- Two clusters closed. Continue nonfinite Alpha approximation; its gate-off evidence is positive but admission is not part of this commit.
- Finite color/scalar Gaussian residuals in seed106 remain a separate future domain.
