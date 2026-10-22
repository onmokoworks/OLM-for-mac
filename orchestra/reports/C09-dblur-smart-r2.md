status: partial

summary:
- Two admission clusters closed: active generated Noise×Size×Fade and noise-disabled active Back Fade×Size.
- Seed1 Smart improves 262 → 273 exact, refusals 35 → 24; the one mismatch and two unavailable references remain.
- Seed2 improves 269 → 274 exact; fresh seed3 improves 269 → 277. No baseline-exact output changes.
- Each cluster passes 956-case production O2/ASan/UBSan regression; the 56 saved corpus results are unchanged.
- Zero-Strength Back Fade is the remaining planned cluster; Front Fade import counterexamples remain excluded.

facts:

Starting revision: `874083a6dfb19581254f9b88f018560c8c3b2373`, branch `orch/C09-dblur-smart-r2`. Read AGENT_GUIDE, the DirectionalBlur ledger restrictions, compatibility plan, emulator GOTCHAS, and T10/F05/F06/F16/C02/F10/F12 reports. No MAIN, original AEX, emulator source/worker, release gate, ledger, other plugin or installed bundle changed. No push, rebuild of the reference worker, history rewrite, stash or permission rejection. Scratch and compiler temporary files stay in `orchestra/state/C09-dblur-smart-r2`.

Scope is original CPU AEX Smart under Unicorn, versus production Mac EffectMain in the existing SDK fake host, full-frame origin zero, unit downsample, raw ARGB, no independent Layer. Classic is separately recorded against its own original reference and is not this ticket's target. PF8 admission does not imply native Windows AE/UCRT, arbitrary inputs, ROI or GPU compatibility.

Bindings: original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`; cached worker SHA256 `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`, path `/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker`. Per-build commands, source/core hashes, original parameters and raw-output hashes are in `reports/fuzz/c09_dblur_smart/`.

**Re-measurement and gate experiment.** Required n300/seed1/jobs2 campaign exits 0: Smart 262 exact / 1 mismatch / 35 refusal / 2 uncompared. Refusal sites: PF8 generic world/profile preflight 21, deep-feature core -1 11, PF8 core -1 1, nonfinite source 2. All 35 have completed Smart AEX counterparts. The two unavailable original renders are indices274/289. Seed1 index84 remains the C02 neutral PF16 import boundary.

Scratch-only omission of the PF8 fallback's feature predicate preserves all numerical code, world/budget checks and the core's negative-index guard. 900 seed1/2/3 O2-versus-ASan/UBSan Smart comparisons agree; all changed outcomes were previously refusals. ASan/UBSan flags include `-fsanitize=address,undefined -fno-sanitize-recover=all`, leak detection disabled.

| Gate-off changed cases | Exact | Mismatch | Still core refusal |
|---|---:|---:|---:|
| Seed1 | 16 | 1 | 4 |
| Seed2 | 13 | 1 | 2 |
| Fresh seed3 | 13 | 0 | 3 |

These are changes relative to the current C02 baseline, not its older pre-Noise baseline. The mismatches are seed1:200 and seed2:152. Negative Offset is not generally admitted merely because some generated tables happen to stay within bounds.

**New dependency boundary, seed2:152.** The existing paired trace executes the real AEX builder, callbacks, rotate, component map, rowdriver and writer; no numerical detours. Its import-free prepass verifies Win64 stack arguments first. All captured rotated/map/divisor/weight/row-output/denominator/alpha stages equal the Mac with double-round expf; their final frame hashes also agree at `b51e2586bcf4bd434afdb43ed34a0cb9abf1a2c490ee21c5cc12293033dc805f`. The worker instead hashes `9d0ebee0d32ec78d68745fd3c90107c1ee52528388230c02fcc40efc81c5e5b1`, one byte different at30895: AEX `f7`, Mac `f6`.

Changing only the fixture's expf import to native-f32 reproduces the worker exactly. All113 expf arguments remain identical. Call57 / Fade92 index52 changes argument LE `e003b8bf` from return `4b31733e` to `4c31733e`. That one weight propagates to62 row-output,17 denominator and13 alpha words. This newly localizes the fresh-seed residual C02 left unresolved. The accepted double-exp-then-float Gaussian contract and writer remain untouched.

**Independent matrices.** The deterministic `C09-independent-<family>-<index>` generator uses new ARGB8 inputs, eight geometries (1×1,1×7,7×1,7×9,17×11,13×19,19×13,11×17), transparent/semitransparent/opaque groups, varied angles, gains, sizes, tails, Noise types1/2, Seed, Offset and Thickness. Extended families vary both Strengths up to4000 and Fade counts1–100. These are independent inputs, not the fuzz corpus or first-pixel reductions. Both public Mac routes are compared numerically to original Smart AEX in these matrices; this deliberately makes no Classic-oracle equivalence claim.

The initial192-case gate matrix has190 exact / 2 mismatch. Both failures are zero-Strength, Front Fade53, Noise on: `fade-only:19` first byte49 `75` → `74`; `fade-only:51` first byte89 `16` → `17`. O2 and sanitizer agree. The paired original trace of19 again has exact incoming planes/maps and double-round weights/row stages; only switching expf reproduces the cached worker. Of53 calls, returns differ at indices3 and25; first argument `3d396cbc`, double-round `e2557c3f`, native-f32 `e3557c3f`. The final worker hash is `b3608a5b146720618a1e852e326fd66ececab1db872a69bfb21be92abf668540`, Mac `00879d04fab8eefffebb7599c51e42e8cb23e50598edb4aac67f71aad67ce0b5`. Thus the broad zero-Strength × Size × Fade admission hypothesis was rejected with a new boundary, not silently broadened from seed success.

**Cluster 1 admission.** The new rule permits the formerly guarded Size×Fade cross only when generated Noise is enabled and at least one Strength is positive. Existing nonnegative Noise Offset and non-Layer requirements remain. Existing retained routes retain precedence; all world, storage, operation-budget, atomic staging and finite/range checks are unchanged. No arithmetic, image-dependent exception, copy shortcut or lookup was added.

Original `FUN_1800038d0` separates the component-map coefficient used by the alpha prepass from the generated-Noise coefficient used by active scatter. MAIN decomp lines1507 onward and the paired trace substantiate use of this existing pipeline. Seed1:45 has exact rotated plane, map, divisor, four weight tables (counts5/4/65/35), row output, denominator, alpha, and final output versus original AEX/native-f32 and the cached Smart worker. This is an active generated-Noise witness, not merely a transparent/copy result.

192 independent active-Noise cases (64 `noise-fade` +128 `active-noise-fade`) are exact at the public production entrypoints, both normal and sanitized. All sampled newly admitted outputs in three campaigns are exact; no unavailable oracle is admitted by this change.

| Smart set | Before E/M/R/U | Cluster1 E/M/R/U | New exact indices |
|---|---|---|---|
| Seed1 n300 | 262/1/35/2 | 269/1/28/2 | 45,48,61,67,77,174,248 |
| Seed2 n300 | 269/1/28/2 | 273/1/24/2 | 69,235,260,270 |
| Fresh seed3 n300 | 269/0/30/1 | 275/0/24/1 | 21,36,129,147,223,230 |
| Saved corpus56 | 54/2/0/0 | 54/2/0/0 | none |

`verify_directionalblur_c02.py` passes956 cases: 900 generated +56 saved, production versus baseline and ASan/UBSan, both public routes. Every base-exact Smart hash is identical; every changed Smart hash moves refusal→exact. Required seed1 `run.py` after exits0 and confirms269/1/28/2. Saved replay exits0,56/56 matches_saved. Corpus before/after: all56 current result dictionaries unchanged on both routes, so no rebaseline is necessary. The three existing tests (general input owner, general features, general feature budget) pass, including the two live O2/sanitized suites; their log is committed.

inference:
- The component-map repair in C02 makes this active generated-Noise cross viable. The three campaigns, independent matrices and paired stages support the bounded admission; they are not an all-input theorem.
- The remaining traced Front Fade differences are imported expf behavior, not evidence to change the frozen Gaussian or proven writer. Successful neighboring feature tuples do not resolve that dependency.
- Negative-Offset out-of-allocation reads and PF32 nonfinite ISA/oracle behavior remain the previously documented external boundaries. No clamp, modulo or emulator-specific NaN policy is introduced.

changed_files:
- mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp
- tools/fuzz/probe_directionalblur_c09_admission.py
- tools/fuzz/verify_directionalblur_c09_matrix.py
- tools/fuzz/verify_directionalblur_c02.py (caller-selected scratch path only)
- tools/emulation/probe_directionalblur_c02_stages.py (caller-selected scratch and independent-matrix inputs)
- reports/fuzz/c09_dblur_smart/*.json and tests.txt
- orchestra/reports/C09-dblur-smart-r2.md

verify:

Run from this worktree. Keep the given worker and MAIN Python paths; do not rebuild/copy them.

```sh
S="$PWD/orchestra/state/C09-dblur-smart-r2"
W=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
B=874083a6dfb19581254f9b88f018560c8c3b2373
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2 --scratch "$S" --worker "$W" --report "$S/recheck.json" --corpus "$S/recheck-corpus" --shrink-attempts 0 > "$S/recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c02.py --baseline "$B" --seeds 1 2 3 --corpus --scratch "$S" --worker "$W" --report "$S/verify-recheck.json" > "$S/verify-recheck.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c09_admission.py --baseline "$B" --scratch "$S" --worker "$W" --report "$S/gate-recheck.json" > "$S/gate-recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c09_matrix.py --baseline "$B" --scratch "$S" --worker "$W" --families noise-fade active-noise-fade --production --report "$S/matrix-production-recheck.json" > "$S/matrix-production-recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c09_matrix.py --baseline "$B" --scratch "$S" --worker "$W" --families fade-only noise-fade plain-fade active-noise-fade back-fade back-fade-zero --report "$S/matrix-gate-recheck.json" > "$S/matrix-gate-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --scratch "$S" --worker "$W" --seed 1 --indices 45 152 168 --gate-off --expf-leaf native-f32 --report "$S/stages-recheck.json" > "$S/stages-recheck.log" 2>&1
for M in double-round native-f32; do
  "$P" tools/emulation/probe_directionalblur_c02_stages.py --scratch "$S" --worker "$W" --seed 2 --indices 152 --gate-off --expf-leaf "$M" --allow-fixture-difference --report "$S/seed2-152-$M-recheck.json" > "$S/seed2-152-$M-recheck.log" 2>&1
  "$P" tools/emulation/probe_directionalblur_c02_stages.py --scratch "$S" --worker "$W" --matrix-case fade-only:19 --gate-off --expf-leaf "$M" --allow-fixture-difference --report "$S/fade-only19-$M-recheck.json" > "$S/fade-only19-$M-recheck.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 2 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$S" --worker "$W" --report "$S/replay-recheck.json" --corpus "$S/replay-unused" > "$S/replay-recheck.log" 2>&1
export PYTHONPATH=tests
export CPLUS_INCLUDE_PATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources'
"$P" -m unittest test_directionalblur_general_input_owner_20261001 test_directionalblur_general_features_20261001 test_directionalblur_general_feature_budget_20261001 > "$S/tests-recheck.log" 2>&1
git diff --check
```

At cluster1: production seed1 269/1/28/2; regression PASS956; production matrix192 exact; gate900 sanitized pairs with the two recorded mismatches; independent gate576 cases with only the two Front Fade53 residuals; three stage final pairs exact (168 has nine differing weight words but identical row/final stages); saved replay56/56; tests3 pass. Oracle wall budgets can vary with machine load and are never counted exact.

next:
- Complete the independently tested Back Fade/no-Noise active and zero-Strength admission clusters in separate commits with before/after tables.
- Preserve Front Fade/noise-disabled and zero-Strength Front Fade guards; the new imported-function counterexamples need native UCRT contract work.

## Cluster 2 — active Back Fade, Noise disabled

facts:
- Baseline `b44aa275` (cluster1). The PF8 fallback now permits Size×Back Fade when Front Fade and Noise are zero and at least one Strength is positive. Other profile, world, budget and core checks remain; no numerical operation changed.
- Original prepass `FUN_180001000` has distinct forward/backward gathers: Front Fade count0 skips its forward loop; Back Fade clamps its extent against the current column. The existing core follows those branches. Seed1:152 has exact captured rotated plane, map/divisor, counts11/4 weights, row output, denominator and alpha against original AEX/native-f32; final bytes are exact. Seed1:168 also has exact image/map/row/final stages, despite nine imported weight words differing (eight of1418 Strength weights and one of83 Back Fade weights). Those differences are retained as dependency data, not corrected or called exact tables.
- The independent `back-fade` matrix tests128 active-Strength inputs, including Front-only, Back-only and both Strengths, both Sharp Tails, Back Fade1–100, nonzero angles and nonopaque groups. All128 public production results equal original Smart AEX on both Mac routes, with O2/ASan/UBSan equality and no sanitizer findings.
- Regression passes956 cases on both public routes. All baseline-exact Smart hashes are unchanged; only refusal→exact changes occur. The required seed1 campaign exits0. All56 saved corpus result dictionaries remain unchanged, including Classic metadata, so there is no corpus rebaseline.

| Smart set | Cluster1 E/M/R/U | Cluster2 E/M/R/U | New exact indices |
|---|---|---|---|
| Seed1 | 269/1/28/2 | 273/1/24/2 | 88,152,168,169 |
| Seed2 | 273/1/24/2 | 274/1/23/2 | 136 |
| Fresh seed3 | 275/0/24/1 | 277/0/22/1 | 195,297 |
| Corpus56 | 54/2/0/0 | 54/2/0/0 | none |

inference:
- This is a separately validated backward-gather family, not general Front Fade admission. Finite evidence supports this rule; it does not establish that Windows expf equals either substitute for arbitrary inputs.
- The zero-Strength prepass-only branch is validated next as its own admission cluster, rather than relying on active-scatter tests alone.

changed_files (cluster2):
- mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp
- tools/fuzz/verify_directionalblur_c09_evidence.py (fast audit of committed acceptance and source bindings)
- reports/fuzz/c09_dblur_smart/{back-after,back-verify,matrix-back-production}.json
- orchestra/reports/C09-dblur-smart-r2.md

verify (same S/W/P environment as above):

```sh
python3 tools/fuzz/verify_directionalblur_c09_evidence.py
python3 tools/fuzz/verify_directionalblur_c02.py --baseline b44aa275 --seeds 1 2 3 --corpus --scratch "$S" --worker "$W" --report "$S/back-verify-recheck.json" > "$S/back-verify-recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c09_matrix.py --baseline b44aa275 --scratch "$S" --worker "$W" --families back-fade --active-only --production --report "$S/matrix-back-recheck.json" > "$S/matrix-back-recheck.log" 2>&1
```

Expected at cluster2: audit PASS; regression PASS956; matrix128 exact; current seed1 campaign273/1/24/2. The audit deliberately checks the current production source against the last committed regression: its initial in-progress invocation rejected the new Back Fade source while only cluster1 evidence was staged; it passes after binding the completed cluster2 evidence.

next: complete the zero-Strength Back Fade cluster, then retain the measured Front Fade, negative-index and nonfinite boundaries for follow-up.
