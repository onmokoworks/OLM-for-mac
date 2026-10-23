status: done

summary:
- Restored Smart PF8 Bilateral dispatch and Size0 float staging; removed C40's half-tie refusal.
- Radius-one weights now honor the original strict exponent > -25 cutoff.
- Both target witnesses match all pre/post float words and final output bytes.
- All five C40 admission losses recover. Fresh seeds 1/44/45/46/47, n300 each: zero Smart mismatches; corpus 146/146 matches saved results.

facts:
- Starting HEAD `e5d53c1772eefdd8bdcefb792b01d4873303c457`, branch `orch/C43-dg-bilateral-last-bit`.
- Read AGENT_GUIDE, GOTCHAS, compatibility plan and the DistanceGradation ledger row. No release gate, ledger, other plugin, MAIN or external emulator source edits; no rebuild of reference workers, push, stash, history rewrite, or subagents.
- Final production source SHA256 `8a13dc9d113ef735f0d11e4f6d9ce6a914621b1d508e67cb442f0eb4ce8cbd63`. Target output SHA256s: case 2 `c7f3ed695bd7f22776182458d8f2ed460e24520dc0179f7b018a01f433a8b735`, case 70 `cc455be735c5b8110f6eb542508ba4e0e04660c1956a1d7d992259d7bc80729e`.
- Current default is prebuilt F46, SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. C40 cached oracles bind F45 independently.
- Case70 baseline public trace: pre-plane 336/336 words exact; post-plane 195 differing words, first word 4 original `0100ff42` versus Mac `0000ff42`; output eight differing bytes, first 232 original `39` versus Mac `38`.
- Direct IPP invocation on case 2's saved original pre-plane reproduces the public post-plane SHA256 `e3fb7fca7dc6442bbe8d7919bdaaa8a8e9a03853051334e60cf0d4ee45969c29`, dispatch `1806bd600`. The pre-change Mac radius-one body differs at 167 words, first word 0 original `0000aa42`, Mac `0000c07f` (NaN).
- Original disassembly `1806bd7ba..1806bd84f` explicitly skips exponent calls at/below -25. Mac's radius-one body lacked this cutoff. The bounded scalar exp implementation itself matches 8196 tested FLOAT32 inputs in all three builds (O2 strict, O3 contraction enabled, ASan/UBSan).
- Before the cutoff fix, the first internal-loop difference is pixel 0 right weight (loop word 2): original `00000000` (zero), Mac `000080ff` (negative infinity); 616/1014 loop words differ in every build. The first pixel numerator and denominator consequently become negative infinity in Mac. This is the first paired in-loop divergence, before normalization and output conversion.
- Adding the cutoff yields case 2 post-plane 169/169 exact. Paired internal hooks at `1806bd84f` (T/L/R/B weights) and `1806bd8aa` (numerator/denominator) match 1014/1014 words across all three builds. Pixel 106 has weights 1/0/1/1, numerator 599.163330078125 (`74ca1544`), denominator 2.819591999053955 (`32743440`); DIVSS produces `01805443`.
- Direct filter invocations use the original IPP exponential and report no imports; replacing it with UCRT exp was not indicated by the captured boundary. Scalar radius-one disassembly uses separate MULSS/ADDSS and DIVSS, matching the existing noncontracting Mac operations.
- Case70's existing general IPP body matches 336/336 post-plane words in all three builds on the original pre-plane. Direct original dispatch counts are `1806b7d40`:3 and `1806be1e0`:2. Scalar exponential probes match 8217/8217 words. The production PF8 route previously skipped this body because its admission predicate was PF32-only.
- Final production public plane traces for case 2 and case 70 match every pre/post word and every output byte. No exp backend, accumulation order, normalization operator, or FMA policy change was necessary beyond the missing cutoff and dispatch/staging restoration.
- Initial C19 probe failed to link newly introduced UCRT pow symbols. Added the same local UCRT library build/link dependency used by the public adapter. This is a diagnostic harness repair, not a numerical hypothesis failure. No tool permission rejection occurred.

- `run.py --replay tests/fuzz_corpus/olmdistancegradation --jobs 1` completed 146/146. Initially only `seed45_case000002_C39.json` changed, Smart refusal -> exact, with unchanged original-AEX route results and unchanged Classic result. Rebaselined only this witness, preserving prior rebaseline history. Final replay completed 146, requested 146, `replay_matches_saved=true`, exit0.
- `verify_distancegradation_C40.py --baseline-dir orchestra/reports/C40-evidence --source "$s/candidate.cpp"` completed all 1200 cases, `acceptance_met=true`, no exact losses, no Smart mismatches. Recovered seed 1 indices 4/9/146, seed 44 index 275 and seed 45 index 245 are each exact. This initial comparison used the numerically identical scratch candidate before removing unused half-tie bookkeeping (retained as `C43-evidence/cached-candidate.cpp.gz` for exact source-hash reproducibility); final production is separately exercised by fresh campaigns and final plane/loop/replay checks.

Fresh F46 campaigns (`run.py --seed <seed> --n 300 --jobs 1 --shrink-attempts 0`), all exit0 and complete 300:

| Seed | Smart exact | mismatch | refusal | budget | uncompared |
|---|---:|---:|---:|---:|---:|
| 1 | 290 | 0 | 3 | 1 | 6 |
| 44 | 277 | 0 | 9 | 1 | 13 |
| 45 | 280 | 0 | 11 | 2 | 7 |
| 46 | 280 | 0 | 13 | 1 | 6 |
| 47 | 287 | 0 | 4 | 0 | 9 |

All five recovered cases and both target witnesses are also individually exact in these fresh campaigns. Timing-budget outcomes are not numerical improvements. Uncompared/refusal/budget rows are not counted as exact; existing Classic mismatches remain outside this ticket.

- All diagnostic/compiler/campaign/replay processes exited; regenerable scratch directories and generated corpus copies were deleted. Retained scratch is 10188859 bytes (< 5 GiB). Python AST parsing and `git diff --check` pass. No tool permission rejection occurred.

inference:
- The target residuals arose from omitted filter execution and an omitted color-weight cutoff, rather than a final quantization rule or a different exp implementation. The last-bit value emerges from the original float operations on the original field.
- Case70 has no old Mac filter-loop word to compare: the loop was skipped. Its first paired differing boundary is therefore the post-filter plane, and the existing body becomes exact when actually dispatched.
- These finite campaigns and traces are bounded local CPU-AEX evidence; they do not establish native AE or universal Bilateral conformance. Existing refusals/uncompared cases remain outside exact evidence.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/emulation/trace_distancegradation_bilateral_C19.py`
- `tools/fuzz/verify_distancegradation_C40.py`
- `tests/fuzz_corpus/olmdistancegradation/seed45_case000002_C39.json`
- This report and `orchestra/reports/C43-evidence/` (complete compressed reports and the cached-comparison candidate source).

verify:
```sh
s="$PWD/orchestra/state/C43-dg-bilateral-last-bit"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/verify_distancegradation_C40.py --baseline-dir orchestra/reports/C40-evidence --scratch "$s/recheck" --report "$s/recheck.json" > "$s/recheck.log" 2>&1
for seed in 1 44 45 46 47; do
  python3 tools/fuzz/run.py --plugin olmdistancegradation --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --budget-minutes 90 --scratch "$s/fresh$seed" --corpus "$s/corpus$seed" --report "$s/fresh$seed.json" > "$s/fresh$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --budget-minutes 90 --scratch "$s/replay" --report "$s/replay.json" > "$s/replay.log" 2>&1
py="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python"
"$py" tools/emulation/trace_distancegradation_blur_C14.py --seed 45 --index 2 --scratch "$s/trace2-final" --report "$s/trace2-final.json" > "$s/trace2-final.log" 2>&1
"$py" tools/emulation/trace_distancegradation_blur_C14.py --seed 44 --index 70 --scratch "$s/trace70-final" --report "$s/trace70-final.json" > "$s/trace70-final.log" 2>&1
"$py" tools/emulation/trace_distancegradation_bilateral_C19.py --scratch "$s/body2-final" --trace "$s/trace2-final.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --report "$s/body2-final.json" --width 169 --height 1 --radius 1 --loop-trace > "$s/body2-final.log" 2>&1
"$py" tools/emulation/trace_distancegradation_bilateral_C19.py --scratch "$s/body70-final" --trace "$s/trace70-final.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --report "$s/body70-final.json" --width 16 --height 21 --radius 7 --generic > "$s/body70-final.log" 2>&1
git diff --check
```
To reproduce the pre-change in-loop divergence (expected 616 differing loop words and 167 differing post-plane words in each build):
```sh
git show e5d53c1772eefdd8bdcefb792b01d4873303c457:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/before.cpp"
"$py" tools/emulation/trace_distancegradation_bilateral_C19.py --scratch "$s/before-loop2" --trace orchestra/reports/C39-evidence/dg-trace.json --source "$s/before.cpp" --report "$s/before-loop2.json" --width 169 --height 1 --radius 1 --allow-mismatch --loop-trace > "$s/before-loop2.log" 2>&1
```

Expected: cached verification `acceptance_met=true`, no exact losses; each fresh campaign complete 300 with zero Smart mismatches; corpus complete 146 and `replay_matches_saved=true`; both paired pre/post/output planes exact; direct body/exp probes and the 1014-word radius-one loop comparison exact in all three builds. Budget/refusal/uncompared counts can vary with shared-machine load. The diagnostic commands exit nonzero on word differences (no tolerance); campaign observation commands can exit0 while retaining non-exact classifications.

To reproduce the exact cached-comparison source hash, decompress `orchestra/reports/C43-evidence/cached-candidate.cpp.gz` into `$s/cached-candidate.cpp` and add `--source "$s/cached-candidate.cpp"` to the cached verifier command. Final production removes only the now-unused half-tie bookkeeping beyond this candidate.

next:
- No remaining work for this ticket acceptance. General native AE, unsupported/refused fields, and existing Classic mismatches remain separate work; do not infer universal or native-AE conformance from these bounded CPU-AEX campaigns.
