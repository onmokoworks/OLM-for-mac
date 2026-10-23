status: done

summary:
- Closed three clusters: scalar Bilateral Power, finite radius-one Bilateral, and generic-radius scalar/vector dispatch.
- Seed1 remains290/0/3/7; seed37 improves279→282 exact and10→7 refusal, with0 mismatch and its1 timeout unchanged.
- Every prior exact output is preserved; only seed37 cases22/25/73 improve refusal→exact.
- Independent2496 exact, sanitizer equality, corpus145 unchanged, final9 beta tests pass.
- Three-cluster stop reached; original failures and unsupported size/domain controls remain separate follow-ups.

facts:
- Starting commit `7f9c2ae051394482a2eae609ccca838e63dd67a8`, branch `orch/C37-dg-smart-r7`. Read AGENT_GUIDE, GOTCHAS, plugin ledger row, compatibility plan and T07/C03/C08/C14/C19/C27/C31/F10/F12 reports. MAIN, original emulator sources and retained workers are read-only.
- F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. Public CPU Unicorn/SDK-shim evidence, not native AE certification.
- Re-measurement uses requested seed1 n300 jobs1 with shrinking disabled to avoid unrelated Classic reduction. Completed: Smart290/0/3/7, original290 success/8 rejection/2 wall timeout. Compared all290 exact result dictionaries/input hashes to C31 final evidence: identical.
- Seed1 residuals31/53/55/108/120/189/192/246: original OpenCV medianBlur assertion `src.depth() == CV_8U`;10/90: original wall timeout. All3 Mac refusals53/189/192 have rejected originals. No seed1 AEX-rendered refusal remains.
- Fresh seed37 n300: Smart279 exact/0 mismatch/10 refusal/10 uncompared/1 budget; original286 success/14 rejection. The10-second Mac timeout is not counted as exact or sanitizer-clean in this initial campaign.
- Largest AEX-rendered refusal family is Bilateral:22 (signed, radius0),25 (SDR, radius12),73 (Power0.01, radius14),199 (HDR, radius988). Additional Box refusals3/288 have sizes3703/2025; existing bounds were not changed.
- Scratch gate-off original22/25/73:22 and73 exact,25 mismatch; all3 sanitizer-identical. Case25 first output byte0/word0 original `acc6e83e`, candidate `aaaaaa3e`;9982 bytes/2924 words differ. Gate-off is diagnostic only.
- Cluster1 case73 takes the already-grounded scalar shape (19x7, radius14). The existing UCRT Power admission copy excludes Bilateral scalar only at the final profile guard. Reusing that same admission copy for this guard retains actual Power rendering, finite SDR source checks, exponent[0.01f,5.0f], radius[3,32], small-image shape, and all layout/lifecycle bounds.
- Independent300 public-original cases: all exact and ASan/UBSan-identical. Geometries/radii7x1/3,1x7/3,7x3/4,19x7/14,17x9/32; all ownership/RGB-or-Layer/background states, inversion variation, exponent0.01/neighbors-of-one/2.25/5, odd padding. Eight boundary controls (out-of-range exponents, radius2/33, infinity, NaN, mask overflow, extended RGB) remain unchanged refusals with sanitizer equality.
- Before/current/sanitized verifier completed all600 campaign cases and145 corpus cases with strict refusal→exact-only changes. Seed1:290 unchanged exact/10 unchanged nonexact. Seed37:280 unchanged exact/19 unchanged nonexact/1 newly exact(case73). The longer180-second render allowance resolves the initial Mac timeout at both revisions; this extra unchanged exact is not credited to the code change. Leak detection disabled.

- Existing beta tests:9 run, OK (17.407s), including their compiled sanitizer coverage. `git diff --check` passes.

| Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
| Saved145 |145 exact|145 exact, identical bytes/status|None|

inference:
- Scalar Bilateral Power refusal was an obsolete admission restriction after UCRT integration. Independent public rendering supports only the existing scalar shape/radius domain; the radius-one Power branch and larger vector-filter shapes are separate.
- Original assertions/timeouts provide no comparable output and do not justify a Mac numerical change. The remaining effective-filter refusal domain is not established exact by this change.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/probe_distancegradation_C37.py`
- `tools/fuzz/summarize_distancegradation_C37.py`
- `reports/fuzz/olmdistancegradation_C37_power.json`
- `orchestra/reports/C37-dg-smart-r7.md`

verify:
Run from this worktree; redirect long command output into scratch logs. Each command below has been executed; expected results are listed above. The helper's other experiment modes are diagnostic, not production promotions.
```sh
s="$PWD/orchestra/state/C37-dg-smart-r7"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/base" --corpus "$s/corpus" --report "$s/base.json"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 37 --jobs 1 --shrink-attempts 0 --scratch "$s/fresh" --corpus "$s/fresh-corpus" --report "$s/fresh.json"
python3 tools/fuzz/probe_distancegradation_C37.py --mode power-scalar --scratch "$s/power" --report "$s/power.json" --write-source "$s/power.cpp" --require-exact
python3 tools/fuzz/probe_distancegradation_C37.py --mode power-scalar --negative --scratch "$s/power-negative" --report "$s/power-negative.json"
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 7f9c2ae --candidate-source "$s/power.cpp" --campaign "$s/base.json" --campaign "$s/fresh.json" --corpus --strict-admission --case-timeout 180 --scratch "$s/power-verify" --report "$s/power-verify.json"
mkdir -p "$s/bin"
ln -sf "$PWD/tools/ucrt_cxx.py" "$s/bin/clang++"
PATH="$s/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'
git diff --check
```
Campaign reruns on promoted source measure current counts; the committed evidence preserves original results. Machine-load-dependent timeouts must be reported separately.

next:
- Continue finite-input radius-one Bilateral matrix and generic-radius first-stage investigation. No production gate or work budget is relaxed for these pending domains.

Cluster 2 — finite radius-one Bilateral (base `99b73247`):

facts:
- Re-measured seed1 after cluster1:290/0/3/7. All300 Smart result dictionaries remain identical to the initial campaign, not just the exact count.
- Gate-off seed37 case22 (15x4, signed samples, Linear, Bilateral Size0) equals the original output with sanitizer equality. Radius0 is the original effective radius1 operation, already restored by C14/C27.
- General input-domain rule now permits finite extended samples through the existing radius-one Bilateral admission predicate. Positive mask-conversion overflow and nonfinite samples remain refused; Power and larger Bilateral radii retain their previous source-domain guards. No output arithmetic or filter dispatch changes in this cluster.
- Independent1944 cases all change refusal→exact and are sanitizer-identical. Nine finite profiles include signed/HDR RGB and alpha, uniform masks, maximum finite RGB/negative alpha, mask-conversion edge8421504, subnormals/cutoff neighbors;7x1/1x7/17x9 geometries; all ownership/RGB-or-Layer/background states; Constant/Linear/Sphere; Size0/1; odd padding. Both source pattern geometries from the existing C14 matrix are retained.
- Six unchanged-refusal controls:Power2.25, radius2, effective Median, infinity, NaN and positive mask overflow. Negative controls test admission only and intentionally do not invoke an original that supplies no required reference.
- All600 campaign and145 corpus before/current/sanitized comparisons pass. Seed1:290 unchanged exact/10 unchanged nonexact. Seed37:281 unchanged exact/18 unchanged nonexact/1 newly exact(case22). This is the180-second verification reference set; initial10-second timeout201 is separately accounted for above. Corpus145 remains byte/status-identical and exact; no rebaseline edits.
- Existing beta tests:9 run, OK (16.687s). No sanitizer diagnostic or disagreement. `git diff --check` passes.

| Cluster2 Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
| Saved145 |145 exact|145 exact, identical bytes/status|None|

inference:
- The finite-source restriction was conservative after ownership/mask and radius-one filter repairs. This promotion reuses those general operations; it does not justify nonfinite effective filters, larger-radius extended inputs or Power source-domain promotion.

changed_files (cluster2):
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/probe_distancegradation_C37.py`
- `reports/fuzz/olmdistancegradation_C37_finite.json`
- `orchestra/reports/C37-dg-smart-r7.md`

verify (additional executed commands):
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/after-power" --corpus "$s/after-power-corpus" --report "$s/after-power.json"
python3 tools/fuzz/probe_distancegradation_C37.py --mode finite-bilateral --scratch "$s/finite" --report "$s/finite.json" --write-source "$s/finite.cpp" --require-exact
python3 tools/fuzz/probe_distancegradation_C37.py --mode finite-bilateral --before-ref 99b73247 --negative --scratch "$s/finite-negative" --report "$s/finite-negative.json"
```
For the combined cluster1+2 source, the executed generation was `candidate(SOURCE.read_text(),'finite-bilateral')` from `probe_distancegradation_C37` while HEAD was99b73247, written to `$s/finite-final.cpp`. Reproduce it by adding `--before-ref 99b73247 --write-source "$s/finite-final.cpp"` to the independent matrix command (same domain and expected1944 exact).
```sh
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 99b73247 --candidate-source "$s/finite-final.cpp" --campaign "$s/base.json" --campaign "$s/fresh.json" --corpus --strict-admission --case-timeout 180 --scratch "$s/finite-verify" --report "$s/finite-verify.json"
PATH="$s/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'
```
Expected:only seed37 case22 changes in this verification; corpus145 unchanged; tests9 pass.

next:
- Generic-radius scalar/vector candidate has passed its independent matrix and import-free IPP leaf check; full campaign regression and negative admission checks are pending. No existing work budget has changed.

Cluster 3 — generic-radius Bilateral scalar/vector dispatch (base `497de6fd`):

facts:
- Re-measured seed1 after cluster2:290/0/3/7; all300 Smart result dictionaries still equal the initial campaign.
- Seed37 case25 is56x42 PF32 SDR, radius12. The gate-off Mac branch skipped the filter outside its previously admitted shapes. The first divergent captured stage is post-filter: first1024 pre-filter words exact; all1024 captured post-filter words differ, first original `aa9c0b3f`, Mac `abaa2a3f`. Full final field2352 words differ; final output2924 words/9982 bytes differ, first original `acc6e83e`, Mac `aaaaaa3e` at byte0.
- Initial trace attempt stopped because existing watches requested more than4096 bytes. The tool now records `plane_capture_bytes` and `plane_total_bytes` and compares only the captured prefix; it does not claim a complete pre/post capture for case25. Its existing per-row field capture still covers the full2352-word final field. Added explicit geometry/blur-size overrides produce independently rendered smaller cases with complete source bytes/parameters in the report.
- Original static dispatch `FUN_1802a1640` and table1815c7540 select generic vector `1806b7d40` for PF32 radii>=3 at width>=16, and scalar `1806be1e0` otherwise. Whole-image padding uses scalar when either dimension is below the kernel diameter; ordinary frames use scalar side tiles, vector top/bottom/interior. The generic kernel keeps circular row-major offsets, border replication, center inclusion, scalar spatial weights, cutoff strictly>-25, and separate float multiply/add. Vector color exponent is `(difference*difference)*-0.5`; scalar is `(-0.5*difference)*difference`.
- Independent17x9/radius3 case derived by explicit prefix reshape from seed37/index25: original public output binds to relocated typed callback, complete pre/post/final field153 words and final output match. Original IPP init/filter18000c280/18000c2f0 reproduces the public post plane without imports or numerical detours. Dispatch counts:1806b7d40 three calls,1806be1e0 two calls. All153 filtered words and8207 original vector-exp inputs match O2, O3 requesting contraction, and ASan/UBSan. Original plane SHA256 `d8c8ebeb3c54c5b7260585e60c0b1d3b9e630ad6879ac1322ad39a599188ebf8`.
- The generic implementation admits only PF32 Smart SDR, Constant/Linear/Sphere, unit downsample, radius3..32 and bounded work. The existing scalar branch remains first and retains its Power promotion. The new domain has a400,000,000 square-kernel-operation ceiling, equal to the existing Median ceiling; no existing work budget is changed. Radius2, radius>32, generic Power and extended/nonfinite generic inputs remain refused.
- Independent252 original-AEX cases all change refusal→exact with sanitizer equality:7x7/r3,15x9/r3,16x9/r3,17x9/r3,33x19/r4,56x42/r12,67x65/r32; all ownership/RGB-or-Layer/background/interpolation states, inversion variation, odd padding. The width15/16/17 and maximum-radius boundaries are included.
- Full seed37/index25 paired trace after the repair: all2352 final field words and all37632 output bytes exact; captured pre/post prefixes exact. This is the original field-operation correction, not an output-byte adjustment.
- Negative first run:7 refusal checks pass; the512x512 work-budget control returns host process exit64 before entering the plugin because the ordinary fuzz host caps dimensions at256. This failed assertion is retained as `vector-negative-host-limit`, not credited as a plugin guard or exact output. A diagnostic-only Adapter raises that scratch host cap to512 for negative tests. Corrected8 controls all remain unchanged refusals, ordinary/sanitized identical, with the work-budget control attributed to `RenderBits:pf32-smart-profile`. No original is required or invoked for these admission-only negative controls.
- Before/current/sanitized verifier passes all600 campaign cases and145 corpus cases. Seed1:290 unchanged exact/10 unchanged nonexact. Seed37:282 unchanged exact/17 unchanged nonexact/1 newly exact(case25). No previously exact output changes. The180-second verification reference set ends283 exact, versus280 before any C37 change; only22/25/73 improve.
- Earlier evidence files were compacted by removing redundant generated parameters, duplicate sanitized result dictionaries and Classic cluster details. A recursive subset comparison against the committed prior artifacts proves all retained values, row counts, hashes and verdicts unchanged. Original full-report SHA256 bindings and reproducible generators remain retained.

| Cluster3 Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
| Saved145 |145 exact|145 exact, identical bytes/status|None|

inference:
- The refusal protects a previously unimplemented generic dispatch, not a host-math discrepancy. The scalar/vector exponential and accumulation order explain the first divergent post-filter stage. No divergent still-host math import was observed, so no `ucrt-math-pending` claim is made.
- These CPU-emulator/public-shim proofs do not establish native AE ROI/downsample, arbitrary UCRT or every unsupported input domain.

changed_files (cluster3):
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/emulation/trace_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_bilateral_C19.py`
- `tools/fuzz/probe_distancegradation_C37.py`
- `tools/fuzz/summarize_distancegradation_C37.py`
- `reports/fuzz/olmdistancegradation_C37_{power,finite,vector}.json`
- `orchestra/reports/C37-dg-smart-r7.md`

verify (additional commands; same scratch environment as above):
```sh
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref 7f9c2ae --seed 37 --index 22 --index 25 --index 73 --experiment gate-off --scratch "$s/gate" --report "$s/gate.json" --write-source "$s/gate.cpp"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --seed 37 --case-index 25 --source "$s/gate.cpp" --scratch "$s/trace25" --report "$s/trace25.json"
python3 tools/fuzz/probe_distancegradation_C37.py --mode vector-radius --before-ref 99b73247 --index 25 --scratch "$s/vector25" --report "$s/vector25.json" --write-source "$s/vector.cpp"
python3 tools/fuzz/probe_distancegradation_C37.py --mode vector-radius --before-ref 99b73247 --scratch "$s/vector-matrix" --report "$s/vector-matrix.json" --require-exact
python3 tools/fuzz/probe_distancegradation_C37.py --mode vector-radius --before-ref 497de6fd --negative --scratch "$s/vector-negative" --report "$s/vector-negative.json" --write-source "$s/vector-final.cpp"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --seed 37 --case-index 25 --geometry 17 9 --blur-size 3 --source "$s/vector.cpp" --scratch "$s/trace17" --report "$s/trace17.json"
PATH="$s/bin:$PATH" '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/trace17.json" --source "$s/vector-final.cpp" --width 17 --height 9 --radius 3 --generic --vector-exp --scratch "$s/vector-leaf-final" --report "$s/vector-leaf-final.json"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --seed 37 --case-index 25 --source "$s/vector-final.cpp" --scratch "$s/trace25-after" --report "$s/trace25-after.json"
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 497de6fd --candidate-source "$s/vector-final.cpp" --campaign "$s/base.json" --campaign "$s/fresh.json" --corpus --strict-admission --case-timeout 180 --scratch "$s/vector-verify" --report "$s/vector-verify.json"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/final" --corpus "$s/final-corpus" --report "$s/final.json"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 37 --jobs 1 --shrink-attempts 0 --scratch "$s/final-fresh" --corpus "$s/final-fresh-corpus" --report "$s/final-fresh.json"
```
Expected: diagnostic gate22/73 exact and25 mismatch; generic25 exact; matrix252 exact; negative8 unchanged refusal; leaf8207 exp/153 plane words exact in all3 builds; complete paired field/output exact. The final candidate differs from the initial verification candidate only in explanatory comments; final campaigns bind the production source. Corpus remains145 exact without edits.

Final facts and stop:
- Final production source SHA256 `0ed446ab4e919ccf6a51bbd058d4d6f2c63d592f1ee7a2396e6e4ec2515158ab` equals the final leaf-check source binding. Final leaf again passes all8207 exponential inputs and153 filtered words at O2/O3/ASan+UBSan; beta tests9 run, OK (17.013s).
- Final n300 seed1:290/0/3/7, all300 Smart result dictionaries identical to baseline. Final n300 seed37:282/0/7/10 plus1 unchanged Mac budget(case201). All279 initial exact dictionaries are identical; only22/25/73 change refusal→exact. Original statuses remain290 success/8 reject/2 budget for seed1,286 success/14 reject for seed37.
- Strict saved-corpus replay completes145, `replay_matches_saved=true`, honoring both saved worker bindings (139 cases:SHA256544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2;6 cases:SHA2563cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261), without worker override or expectation edits.

| Final Smart campaign (10-second per-render allowance) | Exact | Mismatch | Refusal | Uncompared | Mac budget |
|---|---:|---:|---:|---:|---:|
| seed1 before |290|0|3|7|0|
| seed1 final |290|0|3|7|0|
| seed37 before |279|0|10|10|1|
| seed37 final |282|0|7|10|1|

Additional final verification:
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s/final-replay" --report "$s/final-replay.json"
PATH="$s/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'
git diff --check
```
Expected:145 saved-result matches,9 tests OK, clean diff check. All three independent matrices total2496 exact, with sanitizer equality; no case-specific output patches, tolerance or byte correction.

next:
- Three clusters closed: stop under the ticket's three-cluster rule. No remaining seed1 case has a successfully rendered original and nonexact Smart output.
- Fresh seed37 successful-original refusals3/288 have Box sizes3703/2025 outside the existing size<=500 admission; these are size/domain limits, not observed numerical mismatches. Case199 has HDR input and Bilateral radius988 outside the retained finite/radius domains. They need separate scoped investigations, not budget increases.
- Work-budget-exceeding controls also remain protected: seed1/index53 Median square-kernel work3,178,732,410; seed37/index103:43,066,624,320 and index165:3,265,436,736 exceed the unchanged400,000,000 Median ceiling (and are excluded earlier by size/domain guards). Their originals reject. No budget was increased to admit them.
- Original median assertions, original timeouts and Mac timeout201 are not exact outputs. The latter does match at both source revisions under the180-second sanitizer verification allowance; performance remains separate from byte equality.
- MAIN, other plugins, external emulator sources/workers, installed bundles, release gates, ledger and saved corpus expectations remain unchanged. No push, stash, history rewrite or background work is left running. Scratch build trees are removed; logs/reports remain below5GiB.
