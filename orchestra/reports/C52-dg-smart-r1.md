status: done

summary:
- Closed three clusters in separate commits: finite scalar Bilateral, finite unblurred Power, and large-Box area precision/admission.
- Final seed1 remains290 exact; seed105 improves280→283 exact and6→3 refusals; zero Smart mismatches or prior exact losses.
- Independent2280 exact cases,22 refused boundary controls and sanitizer comparisons pass; final corpus147/147 unchanged.
- S01 unresolved counts are classified as original Median assertions, original timeouts and Mac timeouts.
- Four historical beta-test failures reproduce identically at the starting revision; three-cluster stop reached.

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
- `tools/fuzz/check_distancegradation_beta_C52.py`
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


Cluster2 — finite unblurred Power sources (base `b6be4869`):

facts:
- Remeasured full seed1 after cluster1:290 exact/0 mismatch/3 refusal/1 budget/6 uncompared; all300 Smart result dictionaries equal the initial campaign, not just the exact count.
- Reuse the finite Power admission copy for the existing unblurred/identity-filter predicate. Only the finite extended-sample check changes. Actual UCRT Power rendering, nonfinite and positive alpha-conversion-overflow restrictions remain unchanged.
- Independent ordinary HDR/signed matrix432/432 exact; extreme matrix324/324 exact, all sanitizer-identical. Extreme cases include maximum finite positive/negative RGB, subnormals, alpha8421504 at the mask conversion edge, maximum negative alpha, signed zero and ownership-cutoff neighbors. Main matrix covers three geometries, all ownership/render/background combinations, inversion and exponent0.01/2.25/5.
- Seven negative controls retain refusals with sanitizer equality: exponent0.005/5.01, positive alpha conversion overflow, RGB infinity/NaN, active Median3 and radius-one Bilateral Power.
- Base/current/sanitized verification on185 PF32 campaign cases plus147 corpus cases: seed1 unchanged91 exact+4 nonexact; seed10585 unchanged exact+4 unchanged nonexact+case293 newly exact. The first cluster's case214 remains exact. Corpus147 exact with identical hashes; no expectation edit. No sanitizer diagnostic (leak detection disabled).

|Smart result, fixed initial oracle set|Before cluster2|After cluster2|
|---|---|---|
|seed1 exact/mismatch/refusal/budget/uncompared|290/0/3/1/6|290/0/3/1/6|
|seed105 exact/mismatch/refusal/budget/uncompared|281/0/5/3/11|282/0/4/3/11|
|corpus exact|147|147, same hashes|

inference:
- UCRT Power was already implemented; this residual was an admission restriction on finite input channels, not an arithmetic discrepancy. Infinite/NaN sources and positive mask-conversion overflow are intentionally outside this new rule.

verify (cluster2):
```sh
git show b6be4869:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/scalar.cpp"
for kind in ordinary extreme negative; do
  extra=""
  if [ "$kind" = extreme ]; then extra="--extreme"; fi
  if [ "$kind" = negative ]; then extra="--negative"; fi
  python3 tools/fuzz/probe_distancegradation_C52.py --mode finite-power --source "$s/scalar.cpp" $extra --scratch "$s/power-$kind-work" --report "$s/power-$kind.json" --write-source "$s/power.cpp" --require-exact > "$s/power-$kind.log" 2>&1
done
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref b6be4869 --candidate-source "$s/power.cpp" --campaign "$s/seed1.json" --campaign "$s/seed105.json" --campaign-pf32-only --corpus --strict-admission --case-timeout 180 --scratch "$s/power-verify-work" --report "$s/power-verify.json" > "$s/power-verify.log" 2>&1
```
Expected:432+324 exact,7 unchanged refusals; only case293 newly exact versus cluster1, corpus147 unchanged. Run the shell loop in a POSIX shell (or issue each explicit flag separately).

next:
- Investigate large-Box admission; retain larger-radius Bilateral refusal until independently justified. Historical resource-cap beta tests remain the same documented baseline failures.

Cluster3 — Smart PF32 Box area precision and Size501..4096 admission (base `68c3cef4`):

facts:
- Full seed1 remeasurement after cluster2 again completes300 with290 exact/0 mismatch/3 refusal/1 budget/6 uncompared.
- Initial full-range gate experiment is refuted:24 exact cases then a1x3 Size4096 witness differs by2 words/2 bytes; first byte4/word1, original `00f0ff3e`, candidate `01f0ff3e`. Sanitized output equals ordinary output. The failing diagnostic is retained as `box-full.json.gz`, not promoted.
- Size4096 means kernel8193, integer area67125249; binary32 rounds this to67125248. At Size2048, kernel4097 area16785409 rounds to16785408; Size2047/kernel4095 area16769025 is exactly representable. These are arithmetic facts, not inferred oracle internals.
- First observed divergent stage is the Box filter. Reused C14 paired trace with a new generic explicit-PF32-case input option. Original pre-filter words are0,0.5,1; all3 Mac words match. Post-filter differs at word0 only; original `00f0ff3e`, Mac `01f0ff3e`. Original post-field callback replay equals the separate typed public original output exactly. This same-mask PNG proxy plus typed callback binding is not a natural full-owner typed memory capture.
- A narrower Size<=2047 diagnostic matrix first passes48/48 with sanitizers, establishing a new boundary after the refuted full-range admission. It is superseded by the cause fix below, not the final production limit.
- Smart PF32 Box now retains the integer area in double precision through normalization. Its accumulated numerator, traversal, division and writer are unchanged. The call passes this precision rule only for Smart PF32; existing Classic/PF8/PF16 normalization is unchanged. Existing admitted sizes<=500 have exactly representable areas, so their divisor values are unchanged.
- With double area, the same original pre/post planes and complete output all match (0/3 pre words,0/3 post words,0/12 output words differ). Original source bytes and public callback hash are identical between both traces.
- Raise only the PF32 Box admission bound from500 to the declared4096 maximum. Other filter bounds remain500, and world/control/source checks remain in place. Independent final matrices:48 SDR Linear,144 finite-extreme Linear,144 SDR Power, all336 exact and sanitized-identical. Sizes501/1845/2048/4096 straddle the newly observed area-rounding boundary; geometry7x3/3x1/1x3; all ownership/RGB-or-Layer/background states, inversion variation; Power0.01/2.25/5.
- Eight negative controls still refuse, with sanitizer equality: exponent0.005/5.01, positive alpha conversion overflow, RGB infinity/NaN, Size4097, Gaussian501 and Median501.
- Before/current/sanitized verifier: seed1 PF32 remains91 exact+4 nonexact; seed10586 unchanged exact+3 unchanged nonexact+case285 newly exact. All147 corpus cases remain exact with identical hashes. No expectation edits or sanitizer diagnostic; leak checking disabled.
- Supplementary scalar Bilateral extreme matrix324/324 also passes with sanitizer equality, extending cluster1 evidence to maximum finite RGB, alpha-conversion edges, negative maximum alpha and subnormals. This makes the three promoted independent matrices total2280 exact cases;22 negative controls retain refusals.

|Smart result, fixed initial oracle set|Before cluster3|After cluster3|
|---|---|---|
|seed1 exact/mismatch/refusal/budget/uncompared|290/0/3/1/6|290/0/3/1/6|
|seed105 exact/mismatch/refusal/budget/uncompared|282/0/4/3/11|283/0/3/3/11|
|corpus exact|147|147, same hashes|

inference:
- The rounded area explains the captured filter-stage difference: changing that general normalization operation alone closes the first divergent plane and full output, including the independent area-boundary matrix. No expected-output byte patch or coordinate rule is involved.
- The three original successful-reference refusals214/293/285 are closed. Seed105292 (HDR Bilateral Size392) is still refused; its zero-valued1x1 gate-off result is insufficient proof for broad large-radius admission. Native AE and other depths' large-kernel precision/performance remain outside these bounded claims.

changed_files (additional):
- `tools/emulation/trace_distancegradation_smart_C14.py`: accept a generic explicit PF32 case while retaining original public/callback binding and pre/post-plane checks.
- `orchestra/reports/C52-evidence/box4096-case.json`: full independent trace input.

verify (cluster3):
```sh
git show 68c3cef4:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/power.cpp"
python3 tools/fuzz/probe_distancegradation_C52.py --mode box-full --source "$s/power.cpp" --scratch "$s/box-full-work" --report "$s/box-full.json" --write-source "$s/box-full.cpp" --require-exact > "$s/box-full.log" 2>&1
# Expected exit1 at the retained Size4096 witness, after24 exact cases.
python3 tools/fuzz/probe_distancegradation_C52.py --mode box-exact-area --source "$s/power.cpp" --scratch "$s/box-work" --report "$s/box.json" --write-source "$s/box.cpp" --require-exact > "$s/box.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C52.py --mode box-exact-area --extreme --source "$s/power.cpp" --scratch "$s/box-extreme-work" --report "$s/box-extreme.json" --require-exact > "$s/box-extreme.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C52.py --mode box-exact-area --box-power --source "$s/power.cpp" --scratch "$s/box-power-work" --report "$s/box-power.json" --require-exact > "$s/box-power.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C52.py --mode box-exact-area --negative --source "$s/power.cpp" --scratch "$s/box-negative-work" --report "$s/box-negative.json" > "$s/box-negative.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 68c3cef4 --candidate-source "$s/box.cpp" --campaign "$s/seed1.json" --campaign "$s/seed105.json" --campaign-pf32-only --corpus --strict-admission --case-timeout 180 --scratch "$s/box-verify-work" --report "$s/box-verify.json" > "$s/box-verify.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/trace_distancegradation_smart_C14.py --case-json orchestra/reports/C52-evidence/box4096-case.json --source "$s/box-full.cpp" --scratch "$s/trace-before-work" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/trace_distancegradation_smart_C14.py --case-json orchestra/reports/C52-evidence/box4096-case.json --source "$s/box.cpp" --scratch "$s/trace-after-work" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
```
Expected: final48+144+144 exact,8 refused; verifier only case285 newly exact,147 corpus unchanged; paired trace before0/1/2 and after0/0/0 differing pre/post/output words. Trace commands exit0 when capture succeeds, even for a measured mismatch. Supplementary cluster1 extreme reproduction uses its command above plus `--extreme`, expected324 exact.

next:
- Three clusters closed and final verification completed; no further C52 work.
- Follow-up: PF32 large-radius Bilateral; original Median assertions and original/Mac timeout domains; repair stale F41b beta-cap expectations separately.


Final verification and handoff:

FACT: Final `run.py` campaigns for seeds1/105 complete300 each, exit0, with the exact final table above. All300 seed1 Classic/Smart result dictionaries equal the initial campaign. Seed105 Classic is unchanged for all300; the only changed Smart dictionaries are214/285/293, each refusal→exact. All290+280 initially exact Smart hashes are preserved. Final corpus replay exits0,147/147 `matches_saved=true`; no corpus rebaseline is needed.

FACT: Final production source SHA256 `e4242681e9a6146f8fd827a4bd72de0894cece4985c8508d0bf1bc1cb85d011c`; original AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. Original and final full campaigns/replays, independent matrices, both traces, the refuted full-range experiment, explicit trace input and baseline-test logs are committed under `C52-evidence/`, with a SHA256 manifest. The final audit verifies preservation and the exact three newly admitted indices.

FACT: All launched build/render processes completed. Regenerable build/scratch directories and duplicate generated corpora were removed; retained scratch logs/reports total14,586,969 bytes, well below5GiB. No permission rejection occurred. No MAIN, emulator source/worker, release gate, ledger, other-plugin, corpus expectation, or installed bundle was modified; no push/stash/history rewrite/subagents.

Final quick verification:
```sh
python3 tools/fuzz/audit_distancegradation_C52.py
git diff --check
```
Expected exit0, manifest/matrix/trace/corpus assertions pass; final seed1 counts290 exact/3 refusal/1 budget/6 uncompared, final seed105283 exact/3 refusal/3 budget/11 uncompared, zero mismatch and no prior exact loss. Full remeasurement commands are above; observed wall-time budgets can vary with machine load.

Remaining Smart residuals are explicitly not claimed exact: seed105292 successful-original large-radius Bilateral refusal;158 refusal against an original Median assertion;272 refusal against an original timeout;150 Mac timeout with successful original;205/296 Mac timeouts with original Median assertions; original-only assertion/timeout uncompared outputs. Seed1 retains its original assertion/time-budget domains. No original undefined-memory bug was identified, so no deterministic-semantics change to KNOWN_ORIGINAL_BUGS is warranted.
