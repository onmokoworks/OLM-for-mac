status: partial

summary:
- Cluster 1 restores Smart mask conversion overflow and invalid weighted-sample arithmetic, then admits nonfinite/overflow PF32 identity-filter inputs.
- Captured seed1 Smart E/M/R/U improves 274/1/18/7 -> 281/1/11/7; fresh seed6 exact266 ->271. No prior exact bytes change.
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

inference:
- The old direct alpha comparison omitted the original conversion's invalid signed-integer result; its effect precedes field construction.
- ARM's positive NaN for an invalid product is an arithmetic compatibility difference. Restoring the observed x86 operation before blending closes the measured boundary; arbitrary native AE/FPU environment equivalence is not inferred.
- Power exponent1 is a candidate separate identity rule. Fractional Power, effective filters and larger Bilateral remain separate; successful diagnostic cases alone do not authorize broader admission.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tests/test_olmdistancegradation_generic_production_beta_20260820.py`
- `tools/fuzz/verify_distancegradation_smart_C14.py` (ticket-local scratch reuse and configurable sanitizer timeout)
- `tools/fuzz/probe_distancegradation_C19.py`
- `tools/emulation/trace_distancegradation_nonfinite_C19.py`
- `tools/emulation/verify_distancegradation_mul_C19.py`
- `reports/fuzz/olmdistancegradation_C19_nonfinite.json`
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
Expected at cluster1: seed1 E/M/R/U281/1/11/7; seed6 exact271, every original base-exact case unchanged; matrix432 newly exact; negative7 unchanged refusals; corpus145 unchanged exact; scalar1144 exact in three builds; all paired masks/fields/outputs exact; tests9+2 pass. Original timeout counts may depend on workstation load and are not numerical matches.

next:
- Continue the ticket loop with remaining Power refusal cluster, then effective-filter/Bilateral residuals. Do not widen arbitrary Power, nonfinite effective filters or native dependency contracts from these witnesses.
