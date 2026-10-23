status: partial

summary:
- Two clusters closed: nonfinite/overflow identity-filter inputs and Power exponent-one control equivalence.
- Seed1 Smart E/M/R/U:274/1/18/7 ->281/1/11/7 ->284/1/8/7; fresh seed6 exact266 ->271 ->276. No prior exact bytes change.
- Independent432 cases and original-instruction1144 samples are exact; ordinary/sanitized campaign and corpus outputs agree.
- Power and effective-filter residuals remain under investigation; no native AE/UCRT completion claim.

facts:
- Base `0e3481cbba7c9b63e3c23480d8abb081fe03733f`, branch `orch/C19-dg-smart-r4`. Read AGENT_GUIDE, emulator GOTCHAS, DG forbidden actions, compatibility plan and T07/C03/C08/C14/F10/F12 reports. All fuzz runs use jobs1 (machine limit overrides the ticket example's jobs2).
- Original AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX inspected; no worker rebuild or substitution. MAIN assets and external emulator remain read-only.
- Initial `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0` completes: Smart274 exact/1 mismatch/18 refusal/7 uncompared; original290 success/8 reject/2 budget. Fresh seed6 n300, timeout30: Smart266/1/25/8, original289 success/11 reject.

Cluster 1 — nonfinite/overflow identity-filter PF32:
- Largest refusal family: eight nonfinite PF32 inputs, all rendered by the original AEX. Broad scratch gate-off is rejected:2/8 exact,6 mismatches; ordinary/sanitized results agree8/8. Case116 first output difference is byte20, original word `69830d3f`, Mac `867d253f`;30 words differ.
- Original `FUN_1811749a0` splits alpha and calls `18117c580` with scale255 before thresholding above1. Executing that original conversion maps +/-infinity and tested quiet/signaling NaNs to byte0. Adjacent finite input words `4b008080`/`4b008081` convert to255/0. Scalar/tail/vector-length probes retain actual outputs. The original OpenCV body runs without numerical detours using the existing TLS/FLS/allocator scaffold; runtime imports are recorded, not claimed native Windows execution. An initial call without that scaffold faulted at `1811d8cae`; adding the existing scaffold resolves it.
- Paired case116: first divergent mask is pixel18, original0/Mac1 (3/42 mask bytes differ); first divergent field is word1, original `2ef9e43e`, Mac `f304b53e` (30/42 words differ). Restoring signed-int32 overflow handling before byte saturation makes all8 seed1 diagnostic nonfinite cases exact. Power remains outside production admission.
- Independent432 matrix rejects mask-only admission:393 exact/39 mismatch. Eighteen infinite-alpha and21 nonfinite-RGB cases expose a new arithmetic boundary. Example7x1 Inside RGB: all7 field words agree; first output difference byte19, original NaN `0000c0ff`, Mac `0000c07f`.
- Original callback at `181170f8b` executes `MULSS XMM6,XMM2`: sample `7f800000`, weight `00000000`, result `ffc00000`. Original foreground product at `181170f1c` has the same invalid-operation result, before subsequent background addition. The helper restores that arithmetic operation for infinity times zero; it does not adjust a stored output byte. Finite products retain ordinary float multiplication.
- Direct original-instruction verification executes the unchanged four bytes `f30f59f2` at `181170f8b`, stopping before the next instruction. All1144 source/finite-weight pairs match O2, O3 with contraction requested, and ASan/UBSan: signed zero, subnormals, finite extremes, infinities, NaN payloads and seeded samples. No imports or numerical detours are needed for this instruction.
- Three public-bound proxy/callback traces preserve all21 field words. Both invalid-operation examples become full-output exact; the Outside/NaN control remains exact without changing Outside ownership semantics. The proxy mask comes from the original typed conversion, the real PNG public owner builds the state/field, and pointer-relocated callback replay with original typed source must equal the separate typed public hash. This is explicitly not a natural nonfinite full-owner memory capture (retained worker traces PNG only).
- Production admission retains all geometry, layout, alignment, disjointness, lifecycle and control guards. Extended/nonfinite samples are permitted only for existing identity filters: None or zero-size Box/Gaussian/Median, Constant/Linear/Sphere. Power, effective filters and Bilateral retain their previous restrictions.
- Gate-off and production verification cover seed1 all300, fresh seed6 all300, corpus145 and seven Bilateral/Power/domain negative controls. Every base-exact byte is preserved; every changed case is refusal->exact. Gate/production campaign and corpus records are identical. A first30-second sanitizer run timed out on a pre-existing slow PF16 case; the120-second rerun completes all cases without sanitizer diagnostics or disagreement. No timeout is counted as sanitizer-clean. Leak checking is disabled.
- Independent production matrix432/432 newly exact with ordinary/sanitized equality. It spans7x1/1x7/7x3, infinity/NaN/overflow alpha and nonfinite RGB, Inside/Outside/Both, RGB/Layer, background off/on, Constant/Linear/Sphere, inversion, colors and odd padding. The matrix uses Blur None; zero-size identity-filter behavior retains the prior C08 proof.
- Existing beta9 and transactional2 tests pass. The existing input-domain test now accepts nonfinite RGB on the identity-filter lane and checks refusal on an effective Gaussian lane; layout/overlap/size negatives remain.
- Full fresh seed1 census after promotion completes281/1/11/7, original290/8/2 unchanged. All300 Classic route dictionaries and all274 base-exact Smart dictionaries are unchanged. Case116 now matches all42 mask bytes, all42 field words and its complete672-byte output.
- Strict corpus replay exits0, completed145, `replay_matches_saved=true`; it honors both saved hash-bound worker groups (retained `3cb4855b…` and cache `544ff209…`). No corpus expectation changes.
- Machine evidence: `reports/fuzz/olmdistancegradation_C19_nonfinite.json`. Corpus rebaseline table:

| Corpus | Before | After | Expectation edits |
|---|---|---|---|
| All145 Smart cases |145 exact|145 exact, identical bytes/status|None|


Cluster 2 — Power exponent exactly one (base `b53f051b`):
- Re-measured seed1 after cluster1 is281/1/11/7. Six remaining successful-reference refusals select Power. Broad scratch gate-off renders all six exactly, but this does not validate arbitrary native UCRT powf: the retained worker maps PowF to host `f32::powf` (`guest/crates/aex-guest-worker/src/x64/imports.rs:2685`, read-only retained source). The prior native2.25 closure already establishes a host/native distinction. Fractional exponents stay guarded.
- Three cases (25,68,299) use effective FLOAT32 exponent1. The scratch rule normalizes only Smart PF32 Power/1 to Linear before existing domain/filter admission. This changes no arbitrary-exponent calculation and preserves all existing filter, domain and safety bounds. Source is identical between the verified candidate and production.
- Original case25:91 original powf calls,10 distinct input bit patterns; every exponent is `3f800000` and every return word equals its input. Original mask and all91 field words match, and the pointer-relocated original callback equals the separate typed public hash. Production output is identical. The trace explicitly records the `powf` import substitution; it is not a native UCRT execution claim.
- Independent864-case matrix:576 refusal->exact,288 unchanged refusal, zero admitted mismatch, ordinary/sanitized equality864/864. Three source families (SDR, signed/HDR, nonfinite),7x1/1x7/7x3, all ownership modes, RGB/Layer/backgrounds, four identity filters and SDR Box/Gaussian/Median/Bilateral effective filters. Extended/nonfinite effective-filter controls remain refused.
- Five negative controls at effective power words `3f7fffff`, `3f800001`, `3c23d70a`, `40100000`, `40a00000` remain unchanged refusals. Shared Bilateral negative test now uses Power2.25 explicitly, preserving its arbitrary-Power purpose after Power1 admission.
- Before/current/sanitized-current checks complete seed1 all300, seed6 all300, corpus145 and seven shared negatives. Seed1 exact281->284; seed6 exact271->276. Every prior exact byte is unchanged; every change is refusal->exact. Gate and production campaign/corpus records agree exactly.
- Fresh full seed1 census:284 exact/1 mismatch/8 refusal/7 uncompared, original290 success/8 reject/2 budget unchanged. All300 Classic and281 base-exact Smart dictionaries unchanged. Beta9 and transactional2 pass; strict corpus replay145/145 matches saved. No corpus expectation edits.
- Evidence: `reports/fuzz/olmdistancegradation_C19_power_one.json`.

| Cluster2 corpus | Before | After | Expectation edits |
|---|---|---|---|
| All145 Smart cases |145 exact|145 exact, identical bytes/status|None|

inference:
- The old direct alpha comparison omitted the original conversion's invalid signed-integer result; its effect precedes field construction.
- ARM's positive NaN for an invalid product is an arithmetic compatibility difference. Restoring the observed x86 operation before blending closes the measured boundary; arbitrary native AE/FPU environment equivalence is not inferred.
- Power exponent1 is an exact identity operation on the finite distance field; reuse of Linear admission avoids extending arbitrary host powf behavior. Fractional Power and larger Bilateral remain separate; successful diagnostic cases alone do not authorize broader admission.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tests/test_olmdistancegradation_generic_production_beta_20260820.py`
- `tools/fuzz/verify_distancegradation_smart_C14.py` (ticket-local scratch reuse and configurable sanitizer timeout)
- `tools/fuzz/probe_distancegradation_C19.py`
- `tools/emulation/trace_distancegradation_nonfinite_C19.py`
- `tools/emulation/verify_distancegradation_mul_C19.py`
- `reports/fuzz/olmdistancegradation_C19_nonfinite.json`
- `reports/fuzz/olmdistancegradation_C19_power_one.json`
- `orchestra/reports/C19-dg-smart-r4.md`

verify:
Run from this worktree; all long output goes to ticket scratch.
```sh
s="$PWD/orchestra/state/C19-dg-smart-r4"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s" --report "$s/check1.json" --corpus "$s/check-corpus" > "$s/check1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 6 --jobs 1 --case-timeout 30 --shrink-attempts 0 --scratch "$s" --report "$s/check6.json" --corpus "$s/check6-corpus" > "$s/check6.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 0e3481cb --case-timeout 120 --strict-admission --campaign "$s/check1.json" --campaign "$s/check6.json" --corpus --bilateral-negative --scratch "$s/check" --report "$s/check.json" > "$s/check.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C19.py --experiment production --matrix --require-exact --scratch "$s/check-matrix" --report "$s/check-matrix.json" > "$s/check-matrix.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_nonfinite_C19.py --scratch "$s/check-trace" --report "$s/check-trace.json" > "$s/check-trace.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_nonfinite_C19.py --case-index 116 --scratch "$s/check-mask" --report "$s/check-mask.json" > "$s/check-mask.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/verify_distancegradation_mul_C19.py --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --scratch "$s/check-mul" --report "$s/check-mul.json" > "$s/check-mul.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s" --report "$s/check-replay.json" > "$s/check-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/check-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/check-transactional.log" 2>&1
git diff --check
```
Expected after cluster2: seed1 E/M/R/U284/1/8/7; seed6 exact276, every original base-exact case unchanged; matrix432 newly exact; negative7 unchanged refusals; corpus145 unchanged exact; scalar1144 exact in three builds; all paired masks/fields/outputs exact; tests9+2 pass. Original timeout counts may depend on workstation load and are not numerical matches.

Additional cluster2 matrix and trace:
```sh
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref b53f051b --experiment production --matrix --matrix-family power --strict-admission --scratch "$s/check-power-matrix" --report "$s/check-power-matrix.json" > "$s/check-power-matrix.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref b53f051b --experiment production --matrix --matrix-family power-negative --strict-admission --scratch "$s/check-power-negative" --report "$s/check-power-negative.json" > "$s/check-power-negative.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_nonfinite_C19.py --case-index 25 --scratch "$s/check-power-trace" --report "$s/check-power-trace.json" > "$s/check-power-trace.log" 2>&1
```
Expected: matrix576 newly exact/288 unchanged refusal, negatives5 unchanged refusal,91 original pow calls all identity and exact public output. Historical cluster1 production can be extracted with `git show b53f051b:mac/OLMDistanceGradation/OLMDistanceGradation.cpp` and passed via `--candidate-source` to the shared verifier.

next:
- Continue with the remaining Bilateral mismatch/refusal family. Fractional Power is an unresolved native-library/oracle boundary, not a promoted match. Do not widen arbitrary Power, nonfinite effective filters or native dependency contracts from these witnesses.
