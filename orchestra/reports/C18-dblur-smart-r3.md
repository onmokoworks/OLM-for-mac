status: partial

summary:
- Closed PF8 negative-Offset refusal cases whose invalid generated cells are never sampled.
- Seed1 Smart improves 275→278 exact; mismatch1/uncompared2 unchanged, refusals22→19.
- Fresh seed4 retains272 exact/1 mismatch/26 refusal/1 uncompared; all prior exact hashes and all56 corpus records remain unchanged.
- Independent192 negative-Offset cases yield132 newly exact and60 clean refusals;656-case production regression is sanitizer-clean on both routes.
- Deep negative-Offset, imported expf, and nonfinite boundaries remain under investigation.

facts:
- Base `992918f5722b1444ce4dbc3fffd352fbb353bb81`, branch `orch/C18-dblur-smart-r3`. Read AGENT_GUIDE, DirectionalBlur ledger row, compatibility plan, GOTCHAS and T10/F05/F06/F16/C02/C09/F10/F12 reports. MAIN/emulator sources and cached workers are read-only; no release gate, ledger, other-plugin operations, installation, push, stash or history rewrite.
- Original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`; cached worker SHA256 `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`. Full command/build/source/hash records are committed under `reports/fuzz/c18_dblur_smart/`.
- Required n300/seed1 campaign ran before and after with jobs1 (machine limit takes precedence over ticket example jobs2), scratch corpora, no shrinking. Both exit0. Baseline Smart275/1/22/2, after278/1/19/2 (E/M/R/U). Classic3/275/22/0→3/278/19/0; its original zero-output owner remains a distinct oracle, not a Smart numerical reference.
- Extended the F16 original-builder/full-render allocator probe with instruction-level reads of the generated field. Generator emits row-major cells with exactly two table reads per cell (MAIN decomp `FUN_1800034e0`, lines1460–1494). All observed field reads originate in original sampler `FUN_180003370`, RVA342a/344b/3452/3460 or3487. Original rowdriver samples only nonzero-alpha scatter pixels (decomp lines1549–1564). Type1 reads all four neighbors, including zero-weight neighbors; Type2 reads one.

| Seed1 case | Invalid generated cell indices | Sampled distinct cells | Invalid cells sampled |
|---|---|---:|---|
|167|7|1|none|
|183|8|1|none|
|222|12|9|none|
|246|27 cells; full list in sampling.json|19|53,102,119,167|

- All four unmodified fixture outputs equal the cached Smart worker. Counterfactual padding0→1 changes1/1/1/26 generated float words respectively but zero final bytes. The new sampled-cell evidence, not the unchanged final bytes alone, supports the three admissions. Case246 stays refused even though padding happened not to change final pixels.
- PF8 constructs a demanded-cell mask from the rotated source alpha, actual processed row count, cell-size divisions and Noise Type. It reuses the output float allocation for the mask, so no extra live buffer is added. The generator consumes both random draws for every cell, and calculates only demanded cells. Any demanded out-of-range table index still returns failure before dereference. All calculated samples, interpolation, component map, Gaussian weights, rowdriver and writers are unchanged. Deep and Radial callers retain the eager generator default; no Radial code changes.
- `verify_directionalblur_c02.py` now snapshots the baseline noise header as well as cpp sources, preventing current-header leakage into the baseline, and accepts jobs1 (default). Regression exits0:656 cases (seed1+fresh4+56 saved), O2/ASan/UBSan on both public routes, no sanitizer failures. Strict settings use `-fno-sanitize-recover=all`, `halt_on_error=1`, leak detection disabled. Only167/183/222 move refusal→exact;246 changes refusal error516→core512 while remaining refused.
- Independent192 C09-derived image/control combinations use newly assigned negative offsets -1/-18/-36/-72/-360/-720/-32768.132 previously refused cases render exactly on both Mac routes against original Smart;60 remain refused, ordinary/sanitized results identical. No newly admitted mismatch. This is finite emulation/fake-host evidence, not native Windows allocator certification.
- Existing input-owner/features/feature-budget tests:3 tests pass (39.509s). `git diff --check` passes.
- Unchanged seed1:84 mismatch: two PF16 words/two bytes, first byte2508, AEX `6841` → Mac `6941`; C09 directly traced the expf import boundary. No Gaussian/writer changes were made here.

| Smart set | Before E/M/R/U | After E/M/R/U | New exact |
|---|---|---|---|
|seed1 n300|275/1/22/2|278/1/19/2|167,183,222|
|fresh seed4 n300|272/1/26/1|272/1/26/1|none|
|saved corpus56|54/2/0/0|54/2/0/0|none|

Corpus rebaseline table:54 exact→identical exact,2 mismatch→identical mismatch; all56 route-aware saved dictionaries unchanged, no corpus edits.

inference:
- Eager rejection of an invalid cell outside the rowdriver's demand set is unnecessary for defined output. Skipping that calculation preserves every consumed random sample and avoids importing emulator allocator contents into the port.
- An invalid demanded cell remains an external/undefined dependency even if a particular final image masks its effect. No offset clamp, wrap, per-case predicate, expected-byte correction or tolerance is introduced.

changed_files:
- core/dblur_noise.h
- core/dblur_frontonly.cpp
- mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp
- tools/emulation/probe_directionalblur_f16_allocator.py
- tools/fuzz/verify_directionalblur_c02.py
- tools/fuzz/verify_directionalblur_c18_demand.py
- reports/fuzz/c18_dblur_smart/{baseline,pf8-after,demand-verify,demand-matrix,sampling}.json and tests.log
- orchestra/reports/C18-dblur-smart-r3.md

verify:
```sh
S="$PWD/orchestra/state/C18-dblur-smart-r3"
W=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
B=992918f5722b1444ce4dbc3fffd352fbb353bb81
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --scratch "$S" --worker "$W" --report "$S/recheck.json" --corpus "$S/recheck-corpus" --shrink-attempts 0 > "$S/recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c02.py --baseline "$B" --seeds 1 4 --jobs 1 --corpus --scratch "$S" --worker "$W" --report "$S/verify-recheck.json" > "$S/verify-recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c18_demand.py --baseline "$B" --scratch "$S" --worker "$W" --report "$S/matrix-recheck.json" > "$S/matrix-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_f16_allocator.py --indices 167 183 222 246 --scratch "$S" --worker "$W" --report "$S/sampling-recheck.json" > "$S/sampling-recheck.log" 2>&1
export PYTHONPATH=tests
export CPLUS_INCLUDE_PATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources'
"$P" -m unittest test_directionalblur_general_input_owner_20261001 test_directionalblur_general_features_20261001 test_directionalblur_general_feature_budget_20261001 > "$S/tests-recheck.log" 2>&1
git diff --check
```
Expected at PF8 commit: campaign278/1/19/2, regression PASS656, matrix PASS192 (132 exact/60 refusal), trace table above, tests3 pass. Oracle budget counts can vary with load; unavailable references never count exact.

next:
- Investigate the same demand boundary in the PF16/PF32 negative-Offset core refusals, keeping each integration separately verified.
- Preserve expf/Front Fade and nonfinite guards pending their native dependency contracts.
