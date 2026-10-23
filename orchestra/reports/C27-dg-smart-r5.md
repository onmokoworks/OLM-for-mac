status: done

summary:
- Closed three clusters: small-image scalar Bilateral, finite signed/HDR Box/Gaussian admission, and radius-one vector Bilateral.
- Seed1 Smart E/M/R/U:284/1/8/7 ->286/0/7/7 ->287/0/6/7; final vector correction preserves287/0/6/7.
- Fresh seed7 exact278->282; fresh seed8 exact285->286. Every prior exact byte is preserved.
- Independent matrices and original-IPP leaf checks pass with sanitizers; corpus145 remains exact with no expectation edits.
- Three-cluster stop reached. Fractional Power/native-UCRT and other unmeasured domains remain open.

facts:
- Base `a96ed24cbc9c49127215b9ea01bccad0499ce0f2`, branch `orch/C27-dg-smart-r5`. Read AGENT_GUIDE, emulator GOTCHAS, DG ledger forbidden actions, compatibility plan and T07/C03/C08/C14/C19/F10/F12 reports. Reused C19 WIP probe/trace code without merging its branch.
- Original AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. MAIN assets and emulator source are read-only; no worker rebuild. These are CPU Unicorn/public SDK-shim comparisons, not native AE/UCRT certification.
- Cluster1 initial and final `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0` both complete. Original Smart290 success/8 reject/2 budget remains unchanged. Before284/1/8/7, after286/0/7/7. Exact dictionary/RAW equality holds for all284 prior Smart exacts and all300 Classic dictionaries. Only case7 refusal->exact and case200 mismatch->exact change.
- Case200 (239x1 PF8, Bilateral18): pre-filter239/239 words agree; post-filter128 words differ, first word original `feff4b42`, prior Mac `00004c42`. First final difference is byte28, original `de`, prior Mac `dd`, with45 differing bytes. The old PF8 path omitted the filter. This is a filter-stage correction, not output rounding.
- Original IPP init/filter at `18000c280`/`18000c2f0` reproduces the complete public post-filter plane and dispatches to `1806be1e0`, without imports or numerical detours. Candidate output and sanitizer output are exact.
- Original `FUN_1802a1640` selects the padded scalar path when width or height is less than `2*radius+1`. The circular row-major kernel, center inclusion, cutoff strictly greater than -25, border replication and separate float operations are restored. Disassembly at `1806be3d8..1806be3ed` multiplies color by spatial weight, then sample by that weight, and accumulates separately. Eighteen direct dispatch probes cover both sides of the shape boundary at radii3/4/7; optimized dispatch appears outside the admitted shape.
- Case7 (23x24 PF32, Bilateral17): same-mask PNG public trace plus relocated original typed callback binds to the separate typed public output. All552 pre/post words and final output agree. Its original IPP body independently reproduces552/552 post words without imports. This proxy binding is explicitly not a natural typed-input full-owner capture.
- Both original IPP-bound planes match O2, O3 with contraction requested, and ASan/UBSan. The existing exponential helper is checked at8217 FLOAT32 inputs over [-25,0], including original consumed inputs and cutoff neighbors; all8217 outputs match the original import-free body in all three builds. Leak detection disabled.
- Independent324 public original-AEX cases span PF8/PF32, radii3/4/7/17/18/32, horizontal/vertical/2D geometries, all three ownership modes and Constant/Linear/Sphere, RGB/Layer/background/inversion variation and odd padding. All324 exact and sanitizer-identical:162 PF32 refusal->exact;162 PF8 outputs unchanged exact. No admitted mismatch.
- Before/candidate/sanitized candidate verification completes seed1 all300 and corpus145. All changes are asserted exact, not merely baseline-preserving. Seven existing Bilateral negative controls remain unchanged refusals with sanitizer equality. Arbitrary Power, extended/nonfinite effective-filter inputs, radius2, larger radii, PF16 and other dispatch shapes retain their prior policy.
- Fresh seed7 n300 completes278/1/12/9 before; before/current/sanitized verification completes all300 and adds exact cases103/280 only (both refusal->exact), yielding280/1/10/9. No sanitizer diagnostics or timeout; unchanged large PF8 Median case169 takes substantially longer under sanitizers.
- Strict corpus replay exits0, completed145, `replay_matches_saved=true`, honoring both hash-bound worker groups. Beta9 and transactional2 tests pass. Machine evidence: `reports/fuzz/olmdistancegradation_C27_bilateral.json`.
- Candidate arithmetic was copied unchanged to production; only the radius-one comment block was relocated to its correct function afterward.

| Corpus replay | Before | After | Expectation edits |
| --- | --- | --- | --- |
| All145 Smart cases |145 exact|145 exact, identical statuses and bytes|None|


Cluster 2 — finite signed/HDR Box/Gaussian (base `91ebe80e`):
- Re-measured after cluster1:286/0/7/7. Diagnostic gate-off of remaining successful-reference refusals64/124/125/180 makes all four exact with sanitizer equality. Three are fractional Power and are not promoted.
- Case64 (12x3 PF32 signed, Gaussian13, Constant/Inside/Layer) has all36 pre/post words and all144 output words exact in the paired original public/callback trace. The final production trace repeats this equality. Admission changes only the finite-input domain of existing admitted Box/Gaussian paths; positive alpha conversion overflow, nonfinite inputs, Median, Bilateral, arbitrary Power, controls, layout, ROI and work budgets retain prior guards.
- First broad hypothesis (allow finite extended input on every admitted effective filter) is rejected by seed1 case192: its45x29 Median19 original throws OpenCV `src.depth() == CV_8U` assertion while the diagnostic candidate renders. Its864 small-kernel matrix rows all pass, demonstrating why the campaign check is required. This hypothesis never reaches production. Restricting the rule to Box/Gaussian keeps case192 refused and exact case64 admitted.
- Narrow independent matrix864:648 refusal->exact,216 unchanged Median refusals, sanitizer equality864/864, zero admitted mismatch. It includes nine signed/HDR/extreme/conversion/subnormal profiles;7x1/1x7/7x3; three ownership and interpolation modes; RGB/Layer/background/inversion variation; Box2 and Gaussian1/7/13; odd padding. The original renders all864; the216 Median controls are deliberately outside the new rule.
- Before/current/sanitized checks complete seed1 all300, fresh seed7 all300, corpus145 and seven Bilateral negative controls. Only case64 (seed1) and46 (seed7 HDR Gaussian26) change refusal->exact; exact286->287 and280->281 respectively. Corpus145 and all7 negatives are unchanged. No sanitizer diagnostic or timeout; leak checking disabled.
- Final full seed1 census exits0:287/0/6/7, original290 success/8 reject/2 budget unchanged. All300 Classic dictionaries and286 prior-exact Smart dictionaries are byte-identical. Strict corpus replay completes145 with `replay_matches_saved=true`; beta9 and transactional2 pass; diff check passes. Source differs from the verified scratch candidate only by explanatory comments.
- Case124 original callback records29 `powf` imports, six distinct inputs, exponent bits `3e5d4132`; mask/field/output bind exactly to the retained public worker. Both comparison paths substitute math. This is an observed import dependency, NOT a measured first divergence from native UCRT. Cases124/125/180 remain guarded pending F28/general native-UCRT evidence (`ucrt-math` unresolved). No fixed pow table is generalized.
- Evidence: `reports/fuzz/olmdistancegradation_C27_finite.json`. Cluster2 corpus table:145 exact before ->145 exact after, identical bytes/status, zero expectation edits.


Cluster 3 — radius-one vector IPP (base `95dabce4`):
- The prior full seed1 census is287/0/6/7; all its successful-reference refusals are fractional Power. Continued with fresh seed7 case292 (21x23 PF32 Bilateral Size0). All483 pre-filter words agree, but198 post-filter words differ (first original `4dd7543e`, Mac `4bd7543e`), causing185 output-word differences (first byte20, original `96f0273e`, Mac `95f0273e`).
- Original API dispatch records three calls to vector body `1806b6b40` and two calls to scalar side-tile body `1806bd600`. Its complete post-filter plane reproduces the public trace without numerical detours or imports. Original `1802a1640` selects scalar padding below3 pixels in either dimension; at width16+ the top/bottom/interior tiles select vector math and one-column side tiles select scalar math. This is a general dispatch boundary, not an expected-value coordinate patch.
- First divergent operation: original vector exponential `180ba5780` versus the scalar exponential previously used everywhere. Among251 recorded four-lane calls,374 consumed lanes differ from scalar math. First differing input bits `bd4ccccd`: vector output `3f7383c5`, scalar `3f7383c6`. Both original bodies execute without imports; this is embedded IPP, not a UCRT import substitution.
- Restore the bounded [-0.5,0] vector polynomial using original coefficients at `1815f0600..1815f0880`, float MULPS/ADDPS rounding, and the original integer exponent-bit construction. It changes the mathematical exponential operation before accumulation, never a final pixel byte. The existing scalar operation remains on scalar tiles.
- First candidate (`vector-one-v1`) is rejected: post90 words/output77 words still differ. The decompiler flattened the denominator expression; disassembly `1806b6fae/6fd0/7020` proves top+left, then right, then bottom, matching the existing accumulation. Separately its O3 contraction-requested leaf differs at484/8205 words (first expected `14a3793f`, actual `15a3793f`). Volatile float products enforce the original separate operations; no global compiler flag or rounding toggle is introduced. New instruction/leaf boundary evidence resolves both errors rather than repeated guesses.
- Final vector exponential8205/8205 and full483-word IPP post plane match O2, O3 with contraction requested, and ASan/UBSan on arm64. Original public/callback paired traces are now exact at every pre/post/output word for seed7 case292 (483/483/1932 words) and fresh seed8 case104 (340/340/1360 words).
- Independent matrix360/360 public original-AEX cases are exact, sanitizer-identical;36 mismatch->exact,324 unchanged exact. It covers widths1/15/16/17/21/31/32/33; heights1/2/3/5/7/17/23; both Size0/1; two mask patterns; Constant/Linear/Sphere; Inside/Outside/Both; RGB/Layer/background/inversion and odd padding. No admission rule changes in this cluster.
- Fresh seed8 n300 before this correction:285/1/7/7, original292 success/8 reject. Full before/current/sanitized replays cover seed1/7/8 (900 cases), corpus145 and seven negative controls. Seed1 exact287 remains287 with no changed case; seed7 exact281->282 only at292; seed8 exact285->286 only at104. Every previously exact byte is preserved. Current counts: seed1 287/0/6/7; seed7 282/0/9/9; seed8 286/0/7/7. Final seed1 count is independently preserved by all300 before/current comparisons against the preceding full census; no new oracle result is inferred for failed references.
- Final strict corpus replay exits0,145 completed, `replay_matches_saved=true`; ordinary/sanitized corpus145 all unchanged exact. Beta9 and transactional2 pass. No sanitizer diagnostic, disagreement or timeout; leak detection disabled. Production source is byte-identical to the verified scratch candidate. Evidence: `reports/fuzz/olmdistancegradation_C27_vector.json`.

| Cluster3 corpus | Before | After | Expectation edits |
| --- | --- | --- | --- |
| All145 Smart cases |145 exact|145 exact, identical bytes/status|None|

inference:
- The absent generic Bilateral operation caused the measured PF8 residual; the same restored scalar operation justifies bounded PF32 admission under the original scalar dispatch condition.
- Untested dispatch shapes, arbitrary UCRT Power, and nonfinite-source effective filters require separate evidence. The successful matrix is not a claim of universal Bilateral equivalence.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/probe_distancegradation_C19.py`
- `tools/fuzz/verify_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_blur_C14.py`
- `tools/emulation/trace_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_bilateral_C19.py`
- `tools/emulation/trace_distancegradation_dispatch_C27.py`
- `tools/emulation/trace_distancegradation_nonfinite_C19.py`
- `reports/fuzz/olmdistancegradation_C27_vector.json`
- `reports/fuzz/olmdistancegradation_C27_finite.json`
- `reports/fuzz/olmdistancegradation_C27_bilateral.json`
- `orchestra/reports/C27-dg-smart-r5.md`

verify:
Run from this worktree. All commands use ticket-local scratch and at most one worker per campaign.
```sh
s="$PWD/orchestra/state/C27-dg-smart-r5"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s" --report "$s/check1.json" --corpus "$s/check-corpus" > "$s/check1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 7 --jobs 1 --case-timeout 30 --shrink-attempts 0 --scratch "$s" --report "$s/check7.json" --corpus "$s/check7-corpus" > "$s/check7.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref a96ed24c --strict-improvement --campaign "$s/check1.json" --campaign "$s/check7.json" --corpus --bilateral-negative --case-timeout 120 --scratch "$s/check" --report "$s/check.json" > "$s/check.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref a96ed24c --experiment production --matrix --matrix-family bilateral --strict-improvement --require-exact --scratch "$s/check-matrix" --report "$s/check-matrix.json" > "$s/check-matrix.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_blur_C14.py --index 200 --scratch "$s/check-trace200" --report "$s/check-trace200.json" > "$s/check-trace200.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --case-index 7 --scratch "$s/check-trace7" --report "$s/check-trace7.json" > "$s/check-trace7.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/check-trace200.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 239 --height 1 --radius 18 --scratch "$s/check-ipp200" --report "$s/check-ipp200.json" > "$s/check-ipp200.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/check-trace7.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 23 --height 24 --radius 17 --scratch "$s/check-ipp7" --report "$s/check-ipp7.json" > "$s/check-ipp7.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_dispatch_C27.py --report "$s/check-dispatch.json" > "$s/check-dispatch.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s" --report "$s/check-replay.json" > "$s/check-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/check-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/check-transactional.log" 2>&1
git diff --check
```
Expected final seed1:287/0/6/7; fresh seed7:282/0/9/9, original completion counts unchanged; matrix324 exact, negative7 unchanged refusal, corpus145 exact unchanged, direct planes239+552 exact and exp8217 exact in each build. Oracle timeout counts may depend on machine load.

Additional cluster2 verification:
```sh
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref 91ebe80e --experiment production --matrix --matrix-family separable --strict-admission --scratch "$s/check-separable" --report "$s/check-separable.json" > "$s/check-separable.log" 2>&1
git show 95dabce4:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/cluster2.cpp"
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 91ebe80e --candidate-source "$s/cluster2.cpp" --strict-admission --campaign "$s/check1.json" --campaign "$s/check7.json" --corpus --bilateral-negative --case-timeout 120 --scratch "$s/check-domain" --report "$s/check-domain.json" > "$s/check-domain.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --case-index 64 --scratch "$s/check-trace64" --report "$s/check-trace64.json" > "$s/check-trace64.log" 2>&1
```
Expected matrix648 newly exact/216 unchanged refusal, sanitizer equality864/864; only seed1 case64 and seed7 case46 newly exact relative to91ebe80e. The rejected broad experiment is reproducible with `--experiment finite-filter`; `finite-separable` reproduces the admitted rule.

Additional cluster3 verification:
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 8 --jobs 1 --case-timeout 30 --shrink-attempts 0 --scratch "$s" --report "$s/check8.json" --corpus "$s/check8-corpus" > "$s/check8.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 95dabce4 --strict-improvement --campaign "$s/check1.json" --campaign "$s/check7.json" --campaign "$s/check8.json" --corpus --bilateral-negative --case-timeout 120 --scratch "$s/check-vector" --report "$s/check-vector.json" > "$s/check-vector.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref 95dabce4 --experiment production --matrix --matrix-family vector-one --strict-improvement --require-exact --scratch "$s/check-vector-matrix" --report "$s/check-vector-matrix.json" > "$s/check-vector-matrix.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --seed 7 --case-index 292 --scratch "$s/check-vector292" --report "$s/check-vector292.json" > "$s/check-vector292.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --seed 8 --case-index 104 --scratch "$s/check-vector104" --report "$s/check-vector104.json" > "$s/check-vector104.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/check-vector292.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 21 --height 23 --radius 1 --vector-exp --scratch "$s/check-vector-leaf" --report "$s/check-vector-leaf.json" > "$s/check-vector-leaf.log" 2>&1
```
Expected:360 matrix exact;900 campaign comparisons preserve all prior exact bytes and change only seed7 case292/seed8 case104 to exact relative to95dabce4; negative7 unchanged; corpus145 unchanged; vector leaf8205 exact and complete483-word plane exact in all three builds. Both paired public traces are exact. `--experiment vector-one-v1` reproduces the rejected denominator/contraction candidate; `vector-one` reproduces the final source from95dabce4.

next:
- Stop under the three-closed-cluster rule. No claim of full-plugin, arbitrary native AE/UCRT, ROI/downsample or universal ISA conformance.
- Remaining seed1 AEX-rendered refusals124/125/180 use fractional Power; preserve the native-UCRT/F28 boundary. Their diagnostic host-substituted exactness does not prove native UCRT, and no native first divergence was measured here.
- Original-rejected seed1 cases53/189/192 are not promotion candidates. Fresh-seed nonfinite effective filters and other larger/radius-two Bilateral domains remain separate follow-up work.
- All work stayed in this worktree; MAIN assets, emulator source/workers, release gates, ledger, other plugins and installed bundles are unchanged. No push, merge, history rewrite or stash. Scratch remains below5GiB; temporary build directories are removed and no background task is left running.
