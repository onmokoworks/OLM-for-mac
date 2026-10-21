status: blocked

summary:
- Implemented and measured a scratch-only Smart owner geometry candidate; production admission remains unchanged.
- All 163 tiny request refusals clear the geometry checks, but their successful AEX subset is 99 exact / 51 mismatch after tuple bypass; 13 have no reference output.
- All 28 tiny shrunk witnesses become Smart mismatches identical to their existing Classic mismatches. Geometry alone cannot meet acceptance.
- Production before/after: Classic 0 exact / 300 refused and Smart 0 exact / 300 refused; all 300 complete result records unchanged. Sanitized experiments had no sanitizer failures.
- Fast subset: 25 passed. Additional historical closure validation fails its pre-existing source-hash binding. Neither corpus was updated.

facts:

Base: `a95eebfc`, branch `orch/F04-kira-tiny-smart-owner`. `git rebase codex/public-beta-roi` returned **already up to date**; F03 is present through merge `d2f4ddf8`. No history was rewritten. Read the shared guide, emulator GOTCHAS, compatibility plan, KiraKira ledger restrictions, T06 and F03 reports. MAIN, original binaries, external emulator source, release gates, ledger and other plugins were not modified. No worker was rebuilt, no native AE install or push was performed.

Machine evidence: `reports/fuzz/olmkirakira_tiny_owner_F04.json`. It contains per-case baseline and experimental output records, before/after corpus records, target indices, selected geometry traces, all 30 original-AEX pre-render captures, dependency/build hashes and test logs. The committed experiment generates a separate translation unit inside scratch; it never rewrites `mac/OLMKiraKira/OLMKiraKira.cpp`.

Provenance:

- Original AEX, read from MAIN `plugins_2025/OLMKiraKira.aex`: SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained session worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Inspected `/Users/onmk/.cache/olm-emu/INDEX.json`; it indexes RadialBlur-specific builds, not this retained KiraKira worker. Used the same existing KiraKira worker as T06/F03 by absolute path.
- Production source before and after: SHA256 `99c68ea7028cc9b11311476fd0d9f50e11086f0f7591b09cf53fe89bf50297a3`; byte-identical to `git show HEAD:mac/OLMKiraKira/OLMKiraKira.cpp`.
- Public comparison: original AEX CPU Smart versus Mac public EffectMain Classic/Smart fake SDK host, full frame, origin 0, downsample 1:1, packed ARGB oracle versus recorded independent Mac strides. No native AE, Windows UCRT, ROI/tile or GPU equivalence is claimed.

Observed owner boundary:

1. In production, `GenericBetaRenderDimensions`, Smart predata validation and Smart world validation all consume `IsGenericBetaFullFrameDimensions`, whose lower bound is 9×7. The request-only experiment bypasses only `request-not-admitted`. All 163 requests then use the historical 5×3 normalization and fail `checkout-geometry`. Remaining 137 Smart cases fail tuple/source admission. This reproduces T06 after F03.
2. The candidate separates storage geometry from render admission: an owner predicate accepts positive dimensions within the existing 4096-side/DCI-area cap. Only the three Smart owner dimension uses consume it. Existing 1:1 checks, request containment, checkout reference checks, world dimensions/origins, byte-span/format/overlap validation and tuple/helper predicates remain. Existing 5×3/32×18 handling and ROI rules are not broadened by a new tile path. The normalizer, stored dimensions and checked-out worlds now agree for tiny full frames.
3. With tuple admission retained, every tiny request reaches `SmartRender:tuple-or-source`; all 300 Smart cases still refuse. Exactly 163 complete records change because checkout/parameter lifecycle proceeds farther. This is a geometry result, **not** exact output evidence.
4. With both final tuple/source gates bypassed in that scratch candidate, Classic and Smart produce identical hashes on **all 300 cases**, including the 13 without successful AEX output. Classic result dictionaries and all AEX dictionaries equal the original T06 all-gates-off campaign in 300/300 cases. The candidate changes no arithmetic or helper fallback.

Original-AEX geometry evidence:

- MAIN disassembly/decompilation: `18114c8c0` calls `181151710`, then sets output flags at `+0x22` to 1. `181151710` copies the 44 request bytes unchanged, calls `checkout_layer` with layer/index 0 and time/step/scale from InData, then merges the returned result/max rectangles through `181234f10`. There is no 5×3 or 9×7 normalization in this original pre-render owner.
- Ran that original owner under Unicorn with an installed host callback, no numerical detours. Checked the ABI first with the original `1812309f0` scalar address leaf. Ten geometries × depths 8/16/32: **30/30** preserve the request bytes and return the checkout result/max rectangles, with flags 1. Geometries: 1×1, 1×9, 9×1, 3×3, 4×5, 5×3, 8×7, 9×6, 9×7, 32×18. The callback supplies full-frame content/ref dimensions; this proves the observed request/rect behavior, not arbitrary host behavior or rendered pixels.
- Mac diagnostic trace, seed 1/index 8: request `0,0,10,2` → checkout ref `10×2`, result/max `0,0,10,2` → predata `10×2` → input/output `10×2`, origins `0,0`, rowbytes `56/51` → world validation succeeds → render succeeds after tuple bypass. Its numerical result still differs from AEX. Paired first-differing numerical stages were not measured.

Campaigns actually run (all n=300, seed=1, jobs=2; E/M/R/U = exact/mismatch/refusal/uncompared):

| Campaign | Classic E/M/R/U | Smart E/M/R/U | Tiny Smart E/M/R/U | Sanitizer failures |
|---|---|---|---|---|
| Production before | 0/0/300/0 | 0/0/300/0 | 0/0/163/0 | not enabled |
| Request guard only bypassed | 0/0/300/0 | 0/0/300/0 | 0/0/163/0 | not enabled |
| Consistent owner, tuple guards retained | 0/0/300/0 | 0/0/300/0 | 0/0/163/0 | 0 |
| Consistent owner, tuple guards bypassed | 184/103/0/13 | 184/103/0/13 | 99/51/0/13 | 0 |
| Production after | 0/0/300/0 | 0/0/300/0 | 0/0/163/0 | not enabled |

All campaigns: 287 AEX successes / 13 AEX rejections; complete, no framework errors. Owner experiments use `-fsanitize=address,undefined -fno-sanitize-recover=all`; no sanitizer aborts, other crashes or new output/padding/input/lifecycle guard failures. Leak detection is disabled as in T06/F03. Sanitizer cleanliness does not turn the 51 new mismatches into exact results. Against the F03 all-gates-off boundary (Smart 85/52/163/0), consistent geometry adds **99 exact, 51 mismatch, 13 uncompared**. Every production before/after result dictionary is unchanged, not merely its route status or exact count.

First newly exposed tiny mismatch: seed 1/index 8, PF8, 10×2. **48/80 bytes differ**, first byte 1 = pixel (0,0), red: AEX `ac`, Mac `b0`. AEX SHA256 `c9756ce9c0788c621582829142ee12038dbc71a632a0e3517fc53b09bdb0fbe5`; both Mac routes `5ddf3bd2bbc9127df4593c1f45cefba1fab7c401e41f77771b1d01235fc06315`.

Shrunk corpus replay, using the sanitized consistent-owner/tuple-bypass experiment:

| Corpus subset | Count | Saved Smart → candidate Smart | Classic / AEX records | Complete saved-result matches |
|---|---:|---|---|---:|
| Tiny witnesses | 28 | refusal → mismatch | unchanged | 0/28 |
| Other witnesses | 34 | mismatch → mismatch, same bytes | unchanged | 34/34 |
| Total | 62 | no newly exact witness | unchanged | 34/62 |

The 28 affected clusters are C02, C03, C04, C06, C08, C11, C12, C14, C15, C16, C23, C24, C25, C26, C27, C30, C31, C32, C38, C40, C53, C56, C57, C58, C59, C60, C61, C62. All newly returned Smart hashes equal their existing Classic hashes. Exit 1 is expected because this experiment does not match the saved refusal records. No expected records were changed.

Representative default-family boundaries (all three are Blur Mode 2 in their saved parameter records; do not infer a Mode-3 fallback cause):

| Cluster / index | Geometry / depth | Differing bytes | First byte; AEX → Mac word, little endian |
|---|---|---:|---|
| C60 / 148 | 9×1 / 16 | 8/72 | 2; `ff45` → `4e47` |
| C61 / 116 | 3×3 / 32 | 26/144 | 4; `c7827f3f` → `0000803f` |
| C62 / 78 | 1×9 / 8 | 36/36 | 0; `5e` → `6f` |

C60 AEX/Mac hashes: `42d2fa2c4a87995fdb12478d5d894685848cbb65acd71e1329b6029e56b85eda` / `cf9a9aa66e2056e078776b1c9052f66ce7534ce75e572b0bd65ffce7bdb82c03`.
C61: `f4550c426aa33fe7fdb5fcb4ce3ff4fda8de335e7e6ed128024fca0b9fac1396` / `ef8e375caaad4d1b0c228d654fc8d09d22a6a0e98fdc78a66f8c10b653288065`.
C62: `1218e7890e7fe362ea583290b3613f6cb3535e7de046a9d69d378870442a9c19` / `9a5d716fcb27216f061f4eeba24bb850fecaa8059459247c133cd7c7289a2acd`.

Production corpus replay before/after (no production edit; both fresh replays are identical):

| Index | Classic before → after | Smart before → after | Fresh Smart COUNTS before → after | Matches saved corpus |
|---|---|---|---|---|
| 0 | refusal → refusal | refusal → refusal | `1 1 1 26 26` unchanged | yes |
| 1 | refusal → refusal | refusal → refusal | `0 0 0 0 0` unchanged | yes |
| 2 | refusal → refusal | refusal → refusal | `1 1 1 25 25` unchanged | no: saved `1 1 1 0 0` |
| 3 | refusal → refusal | refusal → refusal | `1 1 1 26 26` unchanged | no: saved `1 1 1 0 0` |
| 7 | refusal → refusal | refusal → refusal | `1 1 1 27 27` unchanged | yes |
| 8 | refusal → refusal | refusal → refusal | `0 0 0 0 0` unchanged | yes |
| 16 | refusal → refusal | refusal → refusal | `0 0 0 0 0` unchanged | yes |
| 38 | refusal → refusal | refusal → refusal | `1 1 1 26 26` unchanged | yes |

Both strict production replays exit 1 with 6/8 matches, reproducing F03's two pre-existing lifecycle-only differences. Fresh before/after results are identical in 8/8. Corpus updates: **none**.

Tests:

- Fast existing subset: **25 passed**, exit 0: generic beta lane (9), merge2 float oracle (6), outer compose oracle (9), bounded production writer-owner assertion (1).
- Also attempted `test_olmkirakira_public_smart_bounded_closure_20260812` in the same unittest invocation. It fails during setUpClass before its tests execute: retained evidence expects source SHA256 `abf826dd450bcf879585ae786222ba5d5212d11dd9b292c6ba23d379014baeab`, while unchanged current/HEAD source is `99c68e...97a3`. The other 25 tests passed in that invocation. Did not rewrite the retained conformance report or relax the identity check; reran the independent fast subset successfully.
- Parsed both probe scripts with Python AST; executed both and the evidence summarizer. `git diff --check` passes.

inference:

- The 9×7 render-admission predicate is incorrectly coupled to Smart storage ownership for tiny full frames. Separating those concerns produces consistent geometry, as demonstrated by traces and equality with Classic, but does not establish numerical compatibility.
- Hypothesis 1, “removing the request gate suffices,” is refuted by 163 checkout failures. Hypothesis 2, “consistent owner geometry suffices for target exactness,” is refuted by 51/150 original tiny output mismatches and all 28 shrunk tiny mismatches. No numerical algorithm hypothesis was patched or tuned. Stop here rather than expanding into another plugin-core fix.
- The remaining differences are shared with Classic, so a Smart-only request/predata correction cannot explain or resolve them. Their algorithm/dependency cause remains unproven; this is **not** an outside-port finding.
- The ticket explicitly permits admission relaxation only when newly unblocked cases are exact and sanitizer-clean. Only the sanitizer condition holds. Therefore the candidate is retained as a reproducible scratch experiment, not promoted into production. Acceptance (1) fails; (2) has no regression; (3) has no F04 production changes but retains the existing strict-replay failure and rejects candidate refusal→mismatch changes; the selected fast tests pass, with the additional historical test failure disclosed above.

changed_files:
- `tools/fuzz/probe_kirakira_tiny_owner_F04.py`
- `tools/emulation/probe_kirakira_tiny_pre_geometry_F04.py`
- `tools/fuzz/summarize_kirakira_tiny_owner_F04.py`
- `reports/fuzz/olmkirakira_tiny_owner_F04.json`
- `orchestra/reports/F04-kira-tiny-smart-owner.md`

verify:

Run in this worktree. All generated files stay in ticket scratch; long output is redirected. Commands below are the commands run, with shared arguments factored for readability. Do not enable shell `set -e` across the explicitly expected exit-1 replays/test attempt.

```sh
f04_scratch="$PWD/orchestra/state/F04-kira-tiny-smart-owner"
mkdir -p "$f04_scratch"
export TMPDIR="$f04_scratch" TMP="$f04_scratch" TEMP="$f04_scratch" PYTHONDONTWRITEBYTECODE=1
f04_python='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$f04_python" tools/emulation/probe_kirakira_tiny_pre_geometry_F04.py --aex '/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMKiraKira.aex' --report "$f04_scratch/aex-pre-geometry.json" > "$f04_scratch/aex-pre-geometry.log" 2>&1

for phase in before after; do
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$f04_scratch" --report "$f04_scratch/$phase.json" --corpus "$f04_scratch/$phase-corpus" > "$f04_scratch/$phase.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$f04_scratch" --report "$f04_scratch/corpus-$phase.json" --corpus "$f04_scratch/unused-corpus" > "$f04_scratch/corpus-$phase.log" 2>&1
  # Replay above: expected exit 1, 6/8 saved matches (unchanged F03 metadata).
done

python3 tools/fuzz/probe_kirakira_tiny_owner_F04.py --experiment request --details "$f04_scratch/request-details.json" --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$f04_scratch" --report "$f04_scratch/request.json" --corpus "$f04_scratch/request-corpus" > "$f04_scratch/request.log" 2>&1
python3 tools/fuzz/probe_kirakira_tiny_owner_F04.py --experiment owner --sanitizers --details "$f04_scratch/owner-details.json" --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$f04_scratch" --report "$f04_scratch/owner.json" --corpus "$f04_scratch/owner-corpus" > "$f04_scratch/owner.log" 2>&1
python3 tools/fuzz/probe_kirakira_tiny_owner_F04.py --experiment owner-tuples --sanitizers --details "$f04_scratch/owner-tuples-details.json" --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$f04_scratch" --report "$f04_scratch/owner-tuples.json" --corpus "$f04_scratch/owner-tuples-corpus" > "$f04_scratch/owner-tuples.log" 2>&1
python3 tools/fuzz/probe_kirakira_tiny_owner_F04.py --experiment owner-tuples --sanitizers --details "$f04_scratch/clusters-details.json" --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$f04_scratch" --report "$f04_scratch/clusters.json" --corpus "$f04_scratch/unused-corpus" > "$f04_scratch/clusters.log" 2>&1
# Expected exit 1: 34/62 complete saved results, 28 Smart refusal -> mismatch.

PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer test_olmkirakira_public_smart_bounded_closure_20260812 > "$f04_scratch/fast-tests.log" 2>&1
# Expected exit 1: 25 pass; additional closure class has source-identity setup error.
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$f04_scratch/fast-subset.log" 2>&1
python3 tools/fuzz/summarize_kirakira_tiny_owner_F04.py --scratch "$f04_scratch" --report "$f04_scratch/summary.json" > "$f04_scratch/summary.log" 2>&1
git diff --check
```

Expected: AEX pre geometry 30/30; production 0 exact/300 refused per route before and after; request-only 163 checkout failures; owner-only 300 Smart tuple/source refusals; owner+tuple-bypass 184/103/0/13 on each route with zero sanitizer errors; tiny subset 99/51/0/13; fast subset 25/25. Summarizer asserts all 300 production results unchanged, all 8 fresh production replay records unchanged, unchanged T06 Classic/oracle results and identical candidate Classic/Smart output hashes. Printed summary: `cluster_changes=28`, `production_results_unchanged=300`, tiny `exact=99, mismatch=51, uncompared=13`.

next:
- A separate numerical ticket must capture paired intermediate values for retained tiny Mode-2 witnesses C60/C61/C62, starting at source/seed, rotated geometry, directional filtering and compose. Do not assume Mode-3 fallback or tune final bytes. The same Classic/Smart mismatches make Classic a usable simpler Mac owner for that investigation.
- Once those residuals are closed, reuse the committed geometry candidate and re-run the newly admitted subset before promoting a production request/owner relaxation. Keep ROI/downsample and unrelated tuples separate.
- Orchestrator should reconcile the inherited production corpus lifecycle records and historical closure source identity independently; this worker did not bless either stale expectation.
