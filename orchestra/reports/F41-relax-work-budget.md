status: blocked

summary:
- Inventoried Mac resource caps across all ten plugins; seven have work/size caps.
- RadialBlur work-only removal gains six exact Smart outputs across two n300 seeds, but exposes four Classic mismatches and two unverified Smart outputs.
- Production source is restored byte-for-byte; no relaxation is promoted.
- All 502 baseline-exact route results retain their hashes; restored production replays 35/35 saved corpus entries.
- Remaining plugins, overflow replacement and abort polling are unfinished. This is a qualification blocker, not a completed F41 implementation.

facts:

FACT: Started on `orch/F41-relax-work-budget` at
`5ba4f94a79a7d3e159138c16ddf51f4b0c6f4cb0`. Read `AGENT_GUIDE.md`,
`tools/emulation/GOTCHAS.md`, compatibility plan and the plugin decision-matrix
rows in the ledger. MAIN, emulator sources and retained workers were read-only.
No release-gate/ledger edits, push, stash, history rewrite or permission rejection.

FACT: Inventory commands:

```sh
rg -n 'budget|OUT_OF_MEMORY' mac --glob '*.{cpp,h,hpp}'
rg -n '4096|2160|1024.*1024|[Bb]udget|[Ll]imit[Bb]ytes|[Mm]ax.*[Pp]ixel' core --glob '*.{h,cpp}'
rg -n '4096|2160|[Mm]ax.*(Bytes|Pixels|Work|Dimension)|[Bb]udget|[Ww]orking.set|[Ss]ize-too-large' mac --glob '*.{cpp,h,hpp}'
rg -n 'PF_Err_OUT_OF_MEMORY|budget|[Bb]udget' mac --glob '*.mm' --glob '*.c'
```

Last command found no matches. `PF_TABLE_SZ_16=4096`, diagnostic path-buffer
sizes and Smoother2's `steps - 1` traversal budget are not render refusals.
Source line numbers below refer to the starting revision. **All guards remain
in production.** The disposition column records the implementation still needed,
not a claim that these edits passed qualification.

| Plugin / location | Guard inventory | Disposition / reason |
| --- | --- | --- |
| RadialBlur `CheckedRadialGenericBudget`, cpp:1078–1191 | Side 4096; area 4096×2160; estimated live bytes 1 GiB (including 64 MiB reserve); 350M work units, including Rotation offset scatter. Both `generic-budget` and `smartrender-generic-budget` return OOM. | Work-only removal tested and rejected as a blanket change; retain pending route qualification. Size/live-byte caps are policy limits to remove after actual integer/allocation bounds are audited. No original 350M limit established. |
| DirectionalBlur `core/dblur_generic_budget.h` | Side 4096; area 4096×2160; 3 GiB live estimate with 64 MiB reserve; 350M units in `EstimateRender` and `EstimateGeneralDeepRender`, including Layer/Fade/Noise. Mac tags: PF8/PF16/PF32 neutral-world-or-budget, PF16/PF32 feature-world-or-budget, PF16/PF32 layer-budget, smart-generic-world-or-budget. | Policy ceilings should be removed; mixed world/parameter/overflow validation must remain. Keep the signed-int diagonal-square bound: production core independently checks the same arithmetic boundary (`dblur_frontonly.cpp:172,456,650`). No candidate tested. |
| Blur cpp:1374–1386 `ClassicCopyGeometry` | 4096×2160 side envelope, 3840×2160 area. | Policy size caps to remove; positive/equal dimensions and multiplication overflow remain. |
| Blur cpp:1594,1623–1632 generic admission | 4096×2160 dimensions, 640 MiB/64 pixel estimate, 3.6B work units over pixels×radius×repeat. | Policy caps to remove after cancellation and allocation audit. Comment explicitly says synchronous workers have no host abort callback. Do not equate a watchdog timeout with AE cancellation. |
| KiraKira cpp:1470–1490 | Generic full-frame and Smart-owner side 4096 and area 4096×2160. Minimum 9×7 generic / positive Smart-owner dimensions also occur here. | Remove upper policy limits after rotated extent/cast/product audit. Preserve minimum/profile rules: these are separate numerical admission rules. |
| KiraKira cpp:1532–1608 | Mode-3 peak 1 GiB and 12B work units (Gaussian taps, reflection folds, warp and compose). | Remove estimated-work/live-byte ceilings; retain real allocation/extent safety. Checked estimator additions are not evidence of a Windows allocation limit. No candidate tested. |
| ToonDilate cpp:382–384 | 3 GiB input plus staged-output span (`beta-working-set`). | Remove policy ceiling; preserve independently checked row/span/address/vector limits. |
| ToonDilate cpp:485,627 | Effective radius/halo 4096 in render and pre-render. | Replace policy limit only after exact ceil-to-A_long, halo addition and distance-walker bounds are audited against original semantics. Finite/nonnegative radius and UI radius 0..100 are separate guards to retain. |
| DistanceGradation cpp:1761–1767 | PF32 Smart blurred admission: 1.2B separable work; 400M median work (kernel squared). | Remove work-only limits; retain controls/source-domain restrictions and exact allocation/kernel arithmetic checks. |
| DistanceGradation cpp:1776–1779 | PF32 Smart world side 4096, area 4096×2160. | Remove policy caps; keep typed layout, disjointness and overflow validation. |
| Smoother v1 cpp:4031–4035 | `world-geometry-envelope`: side 4096, area 4096×2160. | Remove policy cap after contour/index/staging arithmetic audit; preserve unsupported PF32, full-frame, depth and layout guards. |
| ColorKeep, ColorKey, Smoother2 | No work/size refusal found by the inventory searches. | Keep real allocation, layout and numerical-profile guards. Smoother2's scan `budget` is algorithmic traversal, not resource refusal. |

FACT: Other `OUT_OF_MEMORY` sites are actual null allocations, bad_alloc catches,
world/row/span/polar byte-product overflows, or vector representability checks.
They were not bypassed. Specific examples: ToonDilate beta-row/span-overflow,
tile-span-overflow, world-pixel/vector/row/span checks; KiraKira
world-allocation-overflow and handle failures; Blur per-depth size products and
staging catches; RadialBlur zoom/rotation-polar-size-overflow and allocation
catches. RadialBlur noise-plane-failure is also **not** a work cap: it can denote
an invalid-index/prepass failure, per C33, and remains untouched.

FACT: The sole numerical experiment changes
`kMaxWork = UINT64_C(350000000)` to `UINT64_MAX`. Geometry, byte caps,
overflow checks, controls, source admission and render arithmetic are unchanged.
The candidate was built before restoring the source; each running harness owns
its compiled executable. The committed reproduction script instead redirects
the build to a scratch-only source snapshot, resolving quoted includes to the
unchanged worktree files. A one-case real-worker smoke run confirms that driver
builds and completes. Absolute includes change its source hash, not the
experiment's work-limit edit.

FACT: Original RadialBlur AEX SHA256:
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Retained F32 worker SHA256:
`c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
Production/restored source SHA256:
`e8c4ab8d1c577aac225b5009061ab3b33808ea8b69c829d299c11db43f4f7b74`.
Measured work-only source SHA256:
`f007e555c6072b70d32d61a6a351118051ba4fe1e1f45fe9c7a19d59074633cc`.
Calibration is 4/6; fresh original CPU outputs, not archived calibration images,
are used for comparisons. Native Windows/AE equivalence is not claimed.

| RadialBlur n300 | Before E/M/R/U | Work-only experiment E/M/R/U |
| --- | --- | --- |
| Seed 1 Classic | 1/119/180/0 | 1/121/178/0 |
| Seed 1 Smart | 253/0/45/2 | 257/0/39/4 |
| Fresh seed 41023 Classic | 3/124/173/0 | 3/126/171/0 |
| Fresh seed 41023 Smart | 245/0/54/1 | 247/0/52/1 |

FACT: Input hashes and parameters agree per index. All 254 seed-1 and 248
fresh-seed baseline-exact **route results** preserve their raw output hashes.
Smart exact gains: seed 1 indices 48/104/148/235; seed 41023 indices 10/115.
New Classic mismatches:

| Seed / index | Differing bytes | First byte | AEX → Mac hex |
| --- | ---: | ---: | --- |
| 1 / 48 | 254 of 260 | 0 | `00` → `c3` |
| 1 / 104 | 135439 of 135608 | 0 | `00` → `7f` |
| 41023 / 10 | 4 of 4 | 0 | `00` → `ed` |
| 41023 / 115 | 2016 of 2016 | 0 | `00` → `4a` |

FACT: Seed-1 original Smart is 275 ok / 20 reject / 5 budget in **both** runs;
budget indices 4/62/117/280/298. Newly admitted indices 62/117 become
uncompared, not exact, in the candidate. Fresh original Smart is 271 ok /
25 reject / 4 budget before, 272 ok / 25 reject / 3 budget after. Budget indices
56/57/77/194 before and 56/57/194 after. Index 77's oracle timing variation is
not an exact gain. All Classic oracles return ok. Case timeouts remain 10 seconds,
jobs 1 per campaign; at most two processes run concurrently. Oracle budget is
a harness limit, **not evidence that Windows refuses the input**.

FACT: An additional unmodified DirectionalBlur seed-1 n300 baseline completes:
Classic 4/288/8/0, Smart 290/0/8/2; original Classic 300 ok, Smart 298 ok /
2 budget. No DirectionalBlur candidate or fresh-seed result is claimed.

FACT: Restored production RadialBlur corpus replay is 35/35 complete saved
matches, preserving both routes' saved statuses/hashes (not claiming all
Classic results are exact). No other corpus replay or all-plugin campaign was
performed. No sanitizer run is claimed.

FACT: All seven started campaign/replay/smoke processes exited zero and were
reaped. No background process remains. Runner-owned build trees were cleaned;
no `build` directory remains under the scratch root. Scratch totals 16 MiB,
below 5 GiB. `git diff --check` passes and production has no diff.

FACT: Inspected MAIN's RadialBlur decomp `FUN_1800056f0` (starting line 2363),
allocation/handle helpers and the AE callback declarations. No named
abort/progress hit in RadialBlur/Blur decomp establishes polling behavior;
`+0x18` calls inspected in the handle helpers are handle disposal, not an abort
callback. A complete original polling audit is unfinished. No callback behavior
was invented or changed.

inference:

INFERENCE: A blanket work-only removal fails the ticket's “every newly admitted
output exact” requirement even though every measured newly admitted Smart output
with a successful oracle is exact. Classic and Smart need separate qualification.
Retaining Classic refusal is permissible, but these measurements alone do not
establish a general non-budget numerical admission rule. The two repeatedly
unverified Smart outputs also prevent claiming all new admissions are exact at
the mandated unchanged timeout. Therefore no production relaxation is promoted.
This is one rejected blanket hypothesis, **not** a claimed two-hypothesis stop.
No first-divergent intermediate boundary was obtained and no numerical cause is
assigned from final-byte mismatches.

changed_files:
- `tools/fuzz/probe_work_budget_F41.py`: reproducible scratch-only work-limit experiment.
- `tools/fuzz/summarize_work_budget_F41.py`: hash/status comparisons and compact provenance.
- `orchestra/reports/F41-relax-work-budget.evidence.json`: measured counts, transitions, first mismatches and oracle failures.
- This report. No production files changed.

verify:

Exact campaign commands used were `python3 tools/fuzz/run.py` with the arguments
below, for both baseline and the temporary work-only source. The committed probe
reproduces the latter without editing production. Use a fresh scratch parent and
redirect every long command. Do not run more than two campaigns concurrently.

```sh
S="$PWD/orchestra/state/F41-relax-work-budget/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
for SEED in 1 41023; do
  python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed "$SEED" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/base-radialblur-$SEED" --corpus "$S/base-corpus-$SEED" --report "$S/base-radialblur-$SEED.json" > "$S/base-radialblur-$SEED.log" 2>&1
  python3 tools/fuzz/probe_work_budget_F41.py --plugin radialblur --n 300 --seed "$SEED" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/work-radialblur-$SEED" --corpus "$S/work-corpus-$SEED" --report "$S/work-radialblur-$SEED.json" > "$S/work-radialblur-$SEED.log" 2>&1
done
python3 tools/fuzz/run.py --plugin radialblur --jobs 1 --replay tests/fuzz_corpus/radialblur --scratch "$S/replay-radialblur" --report "$S/replay-radialblur.json" > "$S/replay-radialblur.log" 2>&1
python3 tools/fuzz/summarize_work_budget_F41.py --state "$S" --output "$S/evidence.json" > "$S/summary.log" 2>&1
git diff --check
```

Expected: the four Classic counterexamples above persist; zero pixel/hash losses
among baseline exact rows; 35/35 saved corpus matches. Counts can vary with oracle
timeouts, which must remain visible rather than being relabeled exact. The fuzz
runner exits zero for a completed measurement even when pixels mismatch.
The summary records losses rather than hiding them or requiring a green result.

Additional measured baseline command:

```sh
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/base-olmdirectionalblur-1" --corpus "$S/directional-corpus" --report "$S/base-olmdirectionalblur-1.json" > "$S/base-olmdirectionalblur-1.log" 2>&1
```

next:
- F41 remains open. Qualify a route-aware RadialBlur relaxation without exposing
  Classic mismatches, and obtain valid oracle evidence for seed-1 62/117 within
  the existing timeouts. Do not special-case indices or return expected bytes.
- Audit real overflow/allocation and original abort polling before removing
  upper dimension/live-memory caps. Then implement and run both requested seeds
  and corpus replay for every changed plugin; the other six capped plugins are
  not qualified by this ticket's RadialBlur measurements.
- Final-byte Classic differences require a distinct owner/intermediate-stage
  investigation if numerical compatibility is pursued; do not invent a math fix.
