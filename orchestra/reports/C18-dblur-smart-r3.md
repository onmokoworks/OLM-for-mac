status: done

summary:
- Closed three depth-specific demand-admission clusters in separate PF8/PF16/PF32 commits, preserving the original random stream and every demanded sample.
- Seed1 Smart improves275→285 exact, refusals22→12; mismatch1 and uncompared2 unchanged.
- Fresh seed4 improves272→276 exact; all baseline-exact hashes and all56 corpus records remain unchanged.
- Each commit passes656-case O2/ASan/UBSan regression;576 independent typed cases and final56/56 replay pass with zero newly admitted mismatches.
- Invalid demanded cells, Front Fade/expf and nonfinite boundaries remain refused or explicitly mismatching; no all-input/native-AE completion claim.

facts:

Cluster1 — PF8:
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
- reports/fuzz/c18_dblur_smart/{baseline,pf8-after,demand-verify,demand-matrix,sampling}.json and tests-pf8.txt
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

## Cluster 2 — PF16 demand validation

facts:
- Baseline `9a0e4eb7`. Extracted the identical PF8 demanded-cell computation into `generate_demanded_noise`, then connected the PF16 pipeline to it. PF32 remains eager at this commit. No further public guard or arithmetic change.
- The allocator probe now accepts exact raw typed input before world allocation, matching the established C02 transport, plus seed/import selection and an observation mode without historical PF8-specific expectations. It still drives the real builder/worker and checks fixture equality against the original public Smart worker. No numerical AEX detour is added.
- Native-f32 expf trace, seed1:62: invalid generated cells2/7, one sampled cell, no intersection. Seed1:108: invalid cells4/5/6, no sampled cells. Seed1:127 control:12 invalid cells,16 sampled cells, intersection27/30/31/33. All three fixture outputs equal the cached worker. Padding changes intermediate fields but zero final bytes;127 still refuses because its invalid samples are used.
- Independent negative-Offset matrix, PF16 typed source:192 cases,132 exact/60 refusal,21 new refusal→exact, identical O2/ASan/UBSan results on both public routes. Already-rendered baseline outputs are unchanged.

inference:
- PF16 uses the same original rowdriver/sampler contract, but a separate populate/rotation pipeline. The typed trace and independent typed matrix support its own integration; PF8 output equality alone was not used as proof for PF16.

changed_files (cluster2):
- core/dblur_frontonly.cpp
- tools/emulation/probe_directionalblur_f16_allocator.py
- tools/fuzz/verify_directionalblur_c18_demand.py
- reports/fuzz/c18_dblur_smart/pf16-*.json and tests-pf8.txt/tests-pf16.txt
- orchestra/reports/C18-dblur-smart-r3.md

verify (same S/W/P setup):
```sh
python3 tools/fuzz/verify_directionalblur_c02.py --baseline 9a0e4eb7 --seeds 1 4 --jobs 1 --corpus --scratch "$S" --worker "$W" --report "$S/pf16-verify-recheck.json" > "$S/pf16-verify-recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c18_demand.py --depth 16 --baseline 9a0e4eb7 --scratch "$S" --worker "$W" --report "$S/pf16-matrix-recheck.json" > "$S/pf16-matrix-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_f16_allocator.py --indices 62 108 127 --observe --expf-leaf native-f32 --scratch "$S" --worker "$W" --report "$S/pf16-sampling-recheck.json" > "$S/pf16-sampling-recheck.log" 2>&1
```
The required campaign and existing three-test commands are as above. All commands must exit0; unavailable oracle outputs remain separate.

next: independently validate PF32 demand, preserving the nonfinite input guard.

PF16 completion facts: required campaign exits0, Smart282/1/15/2; regression PASS656; existing tests3 pass in38.220s. Seed1 new exact62/108/282/296; fresh seed4 new exact84/113/177/184. Corpus54 exact→identical exact and2 mismatch→identical mismatch, all56 saved result dictionaries unchanged, no rebaseline. All base-exact hashes are unchanged. The fast committed-evidence audit `python3 tools/fuzz/verify_directionalblur_c18_evidence.py` also passes and binds final source hashes.

| Smart set | PF8 E/M/R/U | PF16 E/M/R/U |
|---|---|---|
|seed1|278/1/19/2|282/1/15/2|
|fresh seed4|272/1/26/1|276/1/22/1|
|corpus56|54/2/0/0|54/2/0/0|

Additional changed file: tools/fuzz/verify_directionalblur_c18_evidence.py (fast audit, no rendering or expectation updates).

## Cluster 3 — PF32 demand validation and final acceptance

facts:
- Baseline `3b8f5c7e`. Connected only the PF32 generated-Noise branch to the same demanded-cell helper. The nonfinite input guard, float operations, sampler, Gaussian tables and writer remain unchanged. The separate typed pipelines are validated as three admission clusters, not as three unrelated numerical causes.
- Original raw-PF32 traces, native-f32 expf:52 and124 each have one invalid generated cell and one sampled cell, with no intersection. Control7 has257 invalid generated cells,596 sampled cells,98 invalid sampled cells; its core refusal is retained. All three original fixture outputs match the cached Smart worker. Counterfactual padding changes intermediate fields but zero final bytes; that does not authorize7.
- Independent PF32 matrix192 cases:132 exact/60 refusal,21 new refusal→exact, no new mismatch; both public routes match their sanitized builds. Across all three depths the independent matrices total576 cases/2,304 current ordinary-and-sanitized route executions, with396 exact cases and180 clean refusals. Existing already-rendered matrix outputs are unchanged.
- Regression exits0, PASS656: seed1 new exact52/124/125, fresh seed4 unchanged, all56 corpus cases unchanged. All baseline-exact Smart hashes remain identical. Required final n300 campaign exits0, Smart285/1/12/2; Classic4/284/12/0. Classic's zero-output oracle remains explicitly separate.
- Final route-aware corpus replay exits0,56/56 matches_saved. The complete corpus before/after table remains54 exact→identical exact,2 mismatch→identical mismatch; no corpus file changed or rebaseline was necessary.
- Existing input-owner/features/feature-budget tests3 pass in43.579s. Sanitizers are strict ASan/UBSan, zero reports; `git diff --check` and the committed-evidence/source audit pass.

| Smart set | PF16 E/M/R/U | Final E/M/R/U | New exact |
|---|---|---|---|
|seed1 n300|282/1/15/2|285/1/12/2|52,124,125|
|fresh seed4 n300|276/1/22/1|276/1/22/1|none|
|corpus56|54/2/0/0|54/2/0/0|none|

Final residual facts:12 refusals are negative-Offset/core cases4/7/127/246/280/284, PF8 Front Fade guards73/78/175/200, and nonfinite PF32 cases109/299. This ticket directly traces invalid sampled cells for7/127/246; it does not invent a native allocator trace for4/280/284. Seed1:84 remains exactly two differing bytes/two PF16 words, first byte2508, AEX `6841` versus Mac `6941`. Its C09 unshrunk import-boundary evidence remains applicable because Gaussian and row arithmetic did not change. Original Smart274/289 remain budget/unavailable references.

inference:
- Three independently verified typed integrations close the requested bounded loop. The operation is general demand analysis, not a coordinate/case allowlist; read cells are determined by the current rotated source, processed rows and Noise Type.
- Used invalid samples still lack an allocator-independent contract even when a final image happens to hide them. Imported expf and nonfinite ISA/oracle semantics remain separate unresolved dependencies. No clamp/wrap, tolerance, final-byte patch, native Windows equivalence, GPU/ROI/lifecycle certification, or complete plugin compatibility is claimed.

changed_files (cluster3):
- core/dblur_frontonly.cpp
- tools/fuzz/verify_directionalblur_c18_evidence.py
- reports/fuzz/c18_dblur_smart/{pf32-after,pf32-verify,pf32-matrix,pf32-sampling,final-replay}.json and tests-pf32.txt
- orchestra/reports/C18-dblur-smart-r3.md

verify (same S/W/P setup; final source):
```sh
python3 tools/fuzz/verify_directionalblur_c18_evidence.py
python3 tools/fuzz/verify_directionalblur_c02.py --baseline 3b8f5c7e --seeds 1 4 --jobs 1 --corpus --scratch "$S" --worker "$W" --report "$S/pf32-verify-recheck.json" > "$S/pf32-verify-recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c18_demand.py --depth 32 --baseline 3b8f5c7e --scratch "$S" --worker "$W" --report "$S/pf32-matrix-recheck.json" > "$S/pf32-matrix-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_f16_allocator.py --indices 52 124 7 --observe --expf-leaf native-f32 --scratch "$S" --worker "$W" --report "$S/pf32-sampling-recheck.json" > "$S/pf32-sampling-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 1 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$S" --worker "$W" --report "$S/replay-recheck.json" --corpus "$S/replay-unused" > "$S/replay-recheck.log" 2>&1
```
Also run the top campaign/three-test commands. Expected final:285/1/12/2 seed1,276/1/22/1 seed4, PASS656, matrix132 exact/60 refusal, three original-fixture matches with the sampling intersections above, replay56/56, tests3 pass. To reproduce earlier intermediate tables, run their commands at the corresponding commit; final-source comparison against an earlier baseline includes later depth improvements.

next:
- Preserve used-negative-index safety refusals. Any further reduction requires a stronger dependency proof, not substituting allocator bytes or guessing from final equality.
- Follow up the recorded native-UCRT expf contract for84 and guarded Front Fade, and native-ISA/nonfinite oracle contract for109/299.
- No new boundary-free refutation loop, permission rejection or unfinished background process occurred. The loop ends after the three validated depth clusters.

Final scratch after deleting regenerable campaign corpora: **13,154,514 bytes**, below5 GiB. Temporary build contexts removed their build trees; logs/reports are retained.
