status: partial

summary:
- Re-measured seed1 and seed105, n300: Smart290/280 exact, zero mismatches; every historical exact hash preserved.
- S01 unresolved counts mix original Median assertions, original timeouts and Mac timeouts; attribution is retained separately.
- Closed bounded scalar Bilateral finite-source admission: seed105 case214 refusal→exact, zero admitted mismatches.

facts:
- Base HEAD `59b4273d640e30d23fc76ea58374c59874af609c`; branch `orch/C52-dg-smart-r1`.
- Read AGENT_GUIDE, GOTCHAS, compatibility plan, DG ledger row and prior DG triage/fix reports. MAIN assets and emulator sources are read-only. Retained F46 worker SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`; no rebuild.
- Full compressed measurements and provenance are in `C52-evidence/`, bound by `manifest.json`. Commands use jobs1, scratch under this worktree, and disabled shrinking to avoid unrelated Classic reduction.
- Initial campaigns (`run.py --plugin olmdistancegradation --n 300 --seed {1,105} --jobs 1 --shrink-attempts 0`) exit0. Counts below are mutually exclusive by Mac verdict; original failures overlap refusals/budgets.

| Seed | Smart exact | mismatch | refusal | Mac budget | uncompared | AEX ok/reject/budget |
|---|---:|---:|---:|---:|---:|---|
|1|290|0|3|1|6|290/8/2|
|105|280|0|6|3|11|285/12/3|

- Compared seed1 with C47 and seed105 with S01: all290/276 historical exact cases retain identical hashes. Seed105 cases125/245 have already improved refusal→exact before this ticket, and the S01 retry cases50/123 are exact. No numerical gain is credited to C52 for those four cases.
- Seed1 refusals53/189/192 all have rejected originals. Seed105 successful-reference refusals214/285/292/293 all become exact in scratch with the two PF32 profile/source gates off, with identical ASan/UBSan outputs. Output byte counts16/1040/16/1904 respectively, zero differences. This is diagnostic only.
- Initial corpus replay exits0:147/147 saved comparisons match. No corpus expectation is changed.

S01 attribution, including the two seed105 framework retries:

|Seed|uncompared: AEX CV_8U assertion|uncompared: AEX timeout|Mac timeout (AEX ok/reject)|refusal (AEX ok/reject/timeout)|
|---|---:|---:|---|---|
|101|10|0|0/1|5/4/0|
|102|9|0|2/1|3/2/0|
|103|10|2|0/0|3/2/0|
|104|7|0|0/0|5/0/0|
|105|9|2|1/2|6/1/1|

- Every S01 Smart original rejection carries the OpenCV `src.depth() == CV_8U` Median assertion (15/12/12/7/12 by seed). Assertions are not timeouts. No corresponding successful reference exists to justify a numerical port change. The original assertion boundary was already recorded by C31/C37; this is not newly identified undefined memory behavior.

inference:
- S01 unresolved totals cannot be interpreted as one timeout cluster or evidence of a Mac numerical defect. The scalar Bilateral source-domain guard appears stale within the existing bounded kernel domain; independent checks, rather than the zero-valued1x1 witness alone, are required before admission.
- CPU Unicorn/public SDK-shim comparisons are not native AE certification. Non-comparable original failures remain non-exact evidence.

changed_files:
- `tools/fuzz/audit_distancegradation_C52.py`
- `tools/fuzz/probe_distancegradation_C52.py`
- `orchestra/reports/C52-evidence/`
- `orchestra/reports/C52-dg-smart-r1.md`

verify:
```sh
python3 tools/fuzz/audit_distancegradation_C52.py
git diff --check
```
Expected: manifest matches, prior exact hashes preserved, attribution tables above.

Re-measure from the worktree root (all original assets/workers resolved in place):
```sh
s="$PWD/orchestra/state/C52-dg-smart-r1/recheck"
mkdir -p "$s"
for seed in 1 105; do
  python3 tools/fuzz/run.py --plugin olmdistancegradation --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --scratch "$s/seed$seed-work" --corpus "$s/seed$seed-corpus" --report "$s/seed$seed.json" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s/corpus-work" --report "$s/corpus.json" > "$s/corpus.log" 2>&1
```
Expected: complete300 each, zero Smart mismatches, corpus147/147 matches saved; timeout counts may vary with machine load and are not exactness.

next:
- Continue finite unblurred Power and large-Box source/control refusals; larger Bilateral remains unproven.


Cluster1 — finite scalar Bilateral source admission:

facts:
- Added one finite-source admission alternative using the existing scalar-shape predicate (radius3..32, either dimension at most twice radius, full-resolution Smart PF32). Power is normalized only in the local admission copy, within its existing finite[0.01f,5.0f] range. The actual rendering parameters/operations are unchanged.
- Existing nonfinite-source and positive alpha-to-int32 overflow restrictions remain. Independent negative controls: Power0.005/5.01, alpha conversion overflow, RGB infinity/NaN, radius2/33 all still refuse;7/7 sanitized-identical.
- Independent Power432 plus Constant/Linear/Sphere432 public-original cases:864/864 exact,864 sanitized-identical. Four source profiles cover HDR/signed RGB and alpha;7x1/r3,1x7/r8,7x3/r32; all3 ownership modes, RGB/Layer, both backgrounds and inversion variation, padded strides.
- C14 verifier compares base/current/sanitized-current on all95+90 PF32 campaign cases and147 corpus cases. Seed1:91 exact preserved/4 nonexact unchanged. Seed105:84 exact preserved/5 nonexact unchanged/1 newly exact(index214). Corpus147 remains exact and unchanged. No expectation edits. The change is confined to a PF32 Smart input-domain predicate; other depths are unchanged by construction.

|Smart result, fixed initial oracle set|Before|After|
|---|---|---|
|seed1 exact/mismatch/refusal/budget/uncompared|290/0/3/1/6|290/0/3/1/6|
|seed105 exact/mismatch/refusal/budget/uncompared|280/0/6/3/11|281/0/5/3/11|
|corpus exact|147|147, same hashes|

inference:
- This is a stale finite-source restriction, supported by independent public outputs; no arithmetic correction, sample table, or original undefined-read claim is needed.

changed_files (additional):
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`: finite scalar-source predicate only.

verify (cluster1, from worktree root):
```sh
s="$PWD/orchestra/state/C52-dg-smart-r1/recheck"
mkdir -p "$s"
git show 59b4273d640e30d23fc76ea58374c59874af609c:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/base.cpp"
python3 tools/fuzz/probe_distancegradation_C52.py --mode finite-scalar --source "$s/base.cpp" --scratch "$s/scalar-work" --report "$s/scalar.json" --write-source "$s/scalar.cpp" --require-exact > "$s/scalar.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C52.py --mode finite-scalar --linear --source "$s/base.cpp" --scratch "$s/linear-work" --report "$s/linear.json" --require-exact > "$s/linear.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C52.py --mode finite-scalar --negative --source "$s/base.cpp" --scratch "$s/negative-work" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 59b4273d640e30d23fc76ea58374c59874af609c --candidate-source "$s/scalar.cpp" --campaign "$s/seed1.json" --campaign "$s/seed105.json" --campaign-pf32-only --corpus --strict-admission --case-timeout 180 --scratch "$s/verify-work" --report "$s/verify.json" > "$s/verify.log" 2>&1
```
Expected:432+432 exact,7 refused, sanitizer equality, only case214 newly exact against initial campaigns,147 corpus unchanged. The campaign paths must be generated using the remeasurement commands above; for the exact original before table decompress the retained seed reports instead.

FACT: Existing beta suite runs9 tests, with4 identical pre-existing failures at both base59b4273d and scalar candidate: compiled exits46/75 from `pf32_blurred_budget_rejects`, plus stale text assertions for `kSeparableWorkBudget` and `input->width > 4096`. F41b removed these caps. The base replay helper substitutes only the requested source revision; no source rollback or test weakening is used. Logs are retained. This does not contradict the864 independent plus332 before/current/sanitized comparisons, which have no sanitizer errors (leak detection disabled).

Additional reproduction:
```sh
mkdir -p "$s/bin"
ln -sf "$PWD/tools/ucrt_cxx.py" "$s/bin/clang++"
PATH="$s/bin:$PATH" python3 tools/fuzz/check_distancegradation_beta_C52.py --ref 59b4273d640e30d23fc76ea58374c59874af609c --scratch "$s/base-beta" > "$s/base-beta.log" 2>&1
```
Expected exit1,9 tests/4 baseline failures described above. Repairing historical cap tests is a separate follow-up. Retained C52 audit exits0 and `git diff --check` passes.
