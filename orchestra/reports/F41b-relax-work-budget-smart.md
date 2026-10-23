status: done

summary:
- Relaxed Smart resource policy caps in six plugins, with one production commit per plugin; Classic admission remains on its existing policy.
- All 3,417 baseline-exact Smart outputs retain their hashes across seed 1 and fresh seed 41123, n300 each.
- Eight newly admitted RadialBlur outputs are exact, including two targeted 120-second retries; no Smart mismatch was observed.
- All 583 saved corpus entries replay with their saved results, including Classic results.
- High-work RadialBlur Rotation Override remains refused because the retained oracle still cannot complete that domain's witness.

facts:

FACT: Started at `fe2cdd91626a525cd63dbd5d3c55058a1edf98fc` on
`orch/F41b-relax-work-budget-smart`. Read `AGENT_GUIDE.md`, F41's report,
`tools/emulation/GOTCHAS.md`, the compatibility plan, and the relevant ledger
rows. No MAIN, emulator source, release-gate, ledger, or other-plugin edits;
no push, stash, history rewrite, or permission rejection.

Production commits:

| Plugin | Commit | Smart change / preserved arithmetic |
| --- | --- | --- |
| RadialBlur | `61d706b2` | Removes side/area/live-byte ceilings and qualified work ceiling; carries Smart ownership through `RenderWorld`. Checks actual FLOAT32 radius conversion, +2 and inclusive span; retains checked products and sums. Rotation Override with estimated work above 350M remains refused. |
| Blur | `6f68613d` | Removes Smart-only side/area, 640 MiB estimate and 3.6B work ceilings. Retains pixel multiplication and vector representability; `ClassicCopyGeometry` is unchanged. |
| DirectionalBlur | `3f7cb9e0` | Threads explicit Smart policy through world, neutral, feature, Layer and PF8 fallback estimates. Removes policy dimension/area/live-memory/work limits on Smart. Preserves the signed-int diagonal-square bound and checked allocations/sums; default policy is Classic. |
| KiraKira | `31f383b9` | Removes Smart owner size caps and generic Mode-3 / Smart directional Gaussian memory/work caps. Retains minimum/profile rules; adds checks for actual rotated extent casts, `2*n` reflection arithmetic and vector sizes. Classic helpers default to the old limits. |
| ToonDilate | `30fb5aeb` | Removes Smart working-set and effective-radius/halo 4096 policies. Retains ceil-to-A_long, row/span/address/vector checks and existing halo addition handling. Classic render retains its 4096 comparison. |
| DistanceGradation | `2199163c` | Removes PF32 Smart separable, median and bilateral work caps and side/area policies. Retains controls/kernel domain, typed layout, disjointness, multiplication and long-index-plane vector checks. |

FACT: The current inventory also found caps added since F41: KiraKira's
`IsSmartDirectionalGaussianTuple` and DistanceGradation's general bilateral
400M work limit. Both are included. Searches of ColorKeep, ColorKey and
Smoother2 found no resource refusal needing relaxation; table constants and
path buffer lengths are not caps. They are unchanged and not claimed tested
here. Smoother v1 is Classic-only and outside this Smart-only ticket.

FACT: Measured Smart E/M/R/U below. E = exact, M = mismatch, R = Mac refusal;
U = remaining unverified results (including a Mac timeout where noted).
These are fresh baselines, not F41's older-source counts.

| Plugin | Seed | Before E/M/R/U | After E/M/R/U (10s campaign) |
| --- | ---: | --- | --- |
| RadialBlur | 1 | 255/0/43/2 | 258/0/40/2 |
| RadialBlur | 41123 | 258/0/41/1 | 261/0/36/3 |
| Blur | 1 | 300/0/0/0 | 300/0/0/0 |
| Blur | 41123 | 300/0/0/0 | 300/0/0/0 |
| DirectionalBlur | 1 | 290/0/8/2 | 290/0/8/2 |
| DirectionalBlur | 41123 | 281/0/18/1 | 281/0/18/1 |
| KiraKira | 1 | 275/0/25/0 | 275/0/25/0 |
| KiraKira | 41123 | 280/0/20/0 | 280/0/20/0 |
| ToonDilate | 1 | 300/0/0/0 | 300/0/0/0 |
| ToonDilate | 41123 | 300/0/0/0 | 300/0/0/0 |
| DistanceGradation | 1 | 290/0/3/7 | 290/0/3/7 |
| DistanceGradation | 41123 | 288/0/5/7 | 288/0/5/7 |

FACT: DistanceGradation seed 41123's U comprises six uncompared outputs and
one Mac timeout, before and after. No baseline-exact result becomes U, R or M.
The other five changed plugins besides RadialBlur have no admission transitions
in these campaigns. The generator's maximum dimension is 256: these campaigns
do not constitute HD/UHD or exhaustive newly unbounded-domain coverage.

FACT: Final RadialBlur gains are seed 1 indices 62/104/235 and seed 41123
indices 6/62/63/188/235. Fresh-seed 62/63 were U at 10 seconds; rerunning only
those cases at `--case-timeout 120` produces exact outputs in 14.3716 and
15.3735 seconds. Combining those paired retries gives fresh-seed after
**263/0/36/1**. All eight gains have an actual original-AEX comparison.
There is no first differing byte: no Smart mismatch occurred.

FACT: Seed-1 case 62's longer original retry rendered successfully (raw SHA256
`d3d08c4296f99ebc15bfa4e2cb2d9c2dc9890e68802bbcc177a5187d08027042`).
Seed-1 case 117 still stopped after 20.0198 seconds with
`execution stopped before the guest returned (RIP=0x180002cc3)` despite the
120-second case timeout. The harness labels this `reject`; that label does
**not** establish a Windows refusal. The first focused retry used a preliminary
Mac snapshot without the final Smart forwarding and is used only for its
oracle evidence. Final Mac equivalence is established by the committed-source
campaigns and the final-source fresh-seed retries. The final implementation
retains the prior work refusal for Rotation with either Offset Mode Override
and estimated work above 350M, rather than selecting coordinates or indices.

FACT: An earlier Smart work-only candidate measured 260/0/37/3 and 262/0/35/3.
Its exact source SHA256 is
`f93f92061e60be120adf7602c1e43ee222ac44262752c7031fa7df19a8810d83`;
the committed `.work-only.patch` reconstructs it from `fe2cdd91` (hash checked).
It was not promoted as the final policy because it admits the unverified
Override witness. The final RadialBlur source SHA256 is
`b290a0277023b1d394c10a8532e3d4f84540a25ff408f63d6d5a4b884355aad2`.
The baseline source SHA256 is
`b3be29426ad1adb7e716c050a81dcdbc1706c76bb6861242c71156761f089f56`.

FACT: Campaign original worker is the retained F32 executable, SHA256
`c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
RadialBlur AEX SHA256 is
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
All plugin/AEX/source/worker bindings, raw transition hashes, original failure
diagnostics, retry results and report hashes are in the evidence JSON.
Corpus replay uses each corpus's recorded worker, not an overwritten reference.

| Corpus | Saved matches |
| --- | ---: |
| RadialBlur | 35/35 |
| Blur | 39/39 |
| DirectionalBlur | 56/56 |
| KiraKira | 8/8 |
| ToonDilate | 300/300 |
| DistanceGradation | 145/145 |

FACT: Inspected original decomp Smart/typed workers and indirect calls, including
RadialBlur `FUN_1800040f0`, typed dispatch and `FUN_1800056f0`, and the Blur and
DirectionalBlur typed owners. Calls at Handle Suite +0x18 are disposal, not
PF_ABORT. SDK `PF_InData` starts with inter, with abort/progress at +0x18/+0x20
and Win64 effect_ref at +0xb8. A streaming scan of direct callback expressions
finds zero direct abort/progress-shaped calls in all six decomp files. The
committed audit script reproduces that limited scan; it explicitly does not
prove absence of aliased callbacks or library polling. No original polling
site was established by this inspection, so no invented polling or watchdog
was added. Pixel algorithms are not changed to compensate for timeouts.

FACT: Each production commit was followed by both requested n300 campaigns;
all used jobs 1, with at most two emulator/build processes at once. Corpus
replays completed successfully. Compile smoke checks passed for DirectionalBlur,
KiraKira, ToonDilate and DistanceGradation; a KiraKira local scope compile error
was corrected before its production commit. The retained-source snapshot
runner also built and rendered an exact one-case smoke. No sanitizer run or
native Windows/AE run is claimed. All started processes are reaped; runner-owned
build trees were deleted. Scratch is 24 MiB (below 5 GiB). `git diff --check`
passes. No two distinct numerical hypotheses were refuted.

inference:

INFERENCE: Removing policy checks while retaining the same worker arithmetic
preserves the measured exact domain and admits eight verified RadialBlur
outputs. The remaining Rotation Override refusal is a qualification boundary,
not an inferred AEX limit. The static callback inspection does not justify
adding a specific original abort polling point; further alias/callback tracing
would strengthen that negative evidence. Finite small-frame campaigns are not
proof of all large renders or native AE behavior.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `mac/OLMBlur/OLMBlur.cpp`
- `core/dblur_generic_budget.h`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `mac/OLMToonDilate/OLMToonDilate.cpp`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/run_smart_budget_F41b.py`: Smart-only campaigns, selected original generator indices, retained RadialBlur source snapshots; normal corpus replay stays in run.py.
- `tools/fuzz/summarize_smart_budget_F41b.py`: provenance, counts, exact-hash preservation and admission transitions.
- `tools/fuzz/audit_smart_abort_F41b.py`: explicitly limited direct callback scan.
- `orchestra/reports/F41b-relax-work-budget-smart.work-only.patch`
- `orchestra/reports/F41b-relax-work-budget-smart.evidence.json`
- This report.

verify:

Run from this worktree with a fresh scratch directory. The generation commands
below are the commands used before and after each plugin's change (baseline at
the earlier source revision). RadialBlur baselines used `run.py`, checking both
routes; the final campaigns use the Smart-only wrapper. Commands are sequential
and use jobs 1. The fuzzer's zero exit code means measurement completed, so inspect
its counts as well as exit status.

```sh
S="$PWD/orchestra/state/F41b-relax-work-budget-smart/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
for PLUGIN in radialblur olmblur olmdirectionalblur olmkirakira olmtoondilate olmdistancegradation; do
  for SEED in 1 41123; do
    python3 tools/fuzz/run_smart_budget_F41b.py --plugin "$PLUGIN" --n 300 --seed "$SEED" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/$PLUGIN-$SEED" --corpus "$S/corpus-$PLUGIN-$SEED" --report "$S/$PLUGIN-$SEED.json" > "$S/$PLUGIN-$SEED.log" 2>&1
  done
  python3 tools/fuzz/run.py --plugin "$PLUGIN" --jobs 1 --replay "tests/fuzz_corpus/$PLUGIN" --scratch "$S/replay-$PLUGIN" --report "$S/replay-$PLUGIN.json" > "$S/replay-$PLUGIN.log" 2>&1
done
python3 tools/fuzz/run_smart_budget_F41b.py --plugin radialblur --indices 62,63 --n 2 --seed 41123 --case-timeout 120 --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/retry-fresh" --corpus "$S/retry-corpus" --report "$S/retry-fresh.json" > "$S/retry-fresh.log" 2>&1
python3 tools/fuzz/run_smart_budget_F41b.py --plugin radialblur --indices 62,117 --n 2 --seed 1 --case-timeout 120 --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/retry-original" --corpus "$S/retry-original-corpus" --report "$S/retry-original.json" > "$S/retry-original.log" 2>&1
git diff --check
```

Expected: zero Smart mismatches; counts as above subject to visible oracle
wall-time variation; fresh targeted retries exact; seed-1 62 exact and 117 Mac
refusal; all six corpus replays match saved results (583 total). Never relabel
an oracle timeout exact. The source snapshot option can compile a `git show`
export from an earlier revision without changing production; it rewrites
quoted includes to absolute paths, so its snapshot source hash differs.

To reproduce the retained report comparison and direct callback scan:

```sh
python3 tools/fuzz/summarize_smart_budget_F41b.py --state orchestra/state/F41b-relax-work-budget-smart --output "$S/evidence.json" > "$S/summary.log" 2>&1
python3 tools/fuzz/audit_smart_abort_F41b.py --decomp '/Users/onmk/Documents/Projects/Personal/OLM as/decomp' --output "$S/abort-direct-scan.json" > "$S/abort-direct-scan.log" 2>&1
```

Expected summary: 3,417 final-campaign baseline-exact hashes preserved, zero lost;
direct callback scan: zero matches in its explicitly limited expressions.

next:
- Obtain an oracle capable of completing high-work Rotation Override, beginning
  with seed 1/index 117, before relaxing its retained work guard.
- Follow up with large-frame boundary/performance and native-AE cancellation
  witnesses; no HD/UHD or exhaustive alias-based abort audit is claimed here.
- Existing Classic numerical residuals and pre-existing Smart unverified cases
  remain outside this resource-policy qualification; do not reinterpret them
  as exact.
