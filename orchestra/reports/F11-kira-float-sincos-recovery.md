status: done

summary:
- Recovered the embedded float sine/cosine, both reduction branches, original coefficient tables, and float32 workspace extent operation order.
- C60/index 148 and C62/index 78 now have exact Classic diagnostic final bytes; their Smart routes remain refusals. No admission predicate was relaxed.
- 204,190 leaf inputs × two dispatch paths, 26,818 reduction intermediates, and 6,323 caller geometry probes are bit-exact.
- Diagnostic fuzz exact counts improve Classic 198→210 and Smart 98→101; production remains 0 exact / 300 refused per route.
- Corpus audit: 140 route replays, 782 changed samples all toward exact; 25 fast tests plus the existing compiled sanitizer test pass.

facts:

Base: `51b739b4cd7cf4751c0d01ef17f8a8ac54733e10`, branch `orch/F11-kira-float-sincos-recovery`.
Read AGENT_GUIDE, emulator GOTCHAS, compatibility plan, the KiraKira ledger restrictions, F09 evidence, and the worker INDEX. MAIN, external emulator sources/workers, release gates, ledger, other plugins and corpus expectations were not modified. No worker rebuild, push, merge or install.

Machine evidence: `reports/fuzz/olmkirakira_sincos_F11.json`. It records source identities, leaf/geometry hashes, complete before/after target traces, campaign changes, saved-result replays and the 140-route sample audit. Reproduction tools are committed.

Identities:

- Original MAIN `plugins_2025/OLMKiraKira.aex`: SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained public worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX lists RadialBlur workers; this is the KiraKira worker retained by F09.
- Mac source before SHA256 `c3cb49527eaef8f51031487db57d5af56eee5933aa3583f02dd7b9865cd5eaf6`; after `d1c9621d8df3d7bbc25ab52b048fddc6205c33dc26eea10d704eb935708f7b3c`.
- Recovered arithmetic header SHA256 `91b6d89cb75a8fcdb1bc7a72561ae026381b9fa7cb8b104a5ac277fd21ee2753`; coefficient header `33eaa7a31ccde031d242059010b6c201e2f350b01384575eb2386f8b6e201f3c`.

Static and leaf evidence:

1. MAIN Ghidra decomp `FUN_18132b2e0` omits most SIMD return arithmetic. The corresponding disassembly shows `abs(x)<2^-13` (also unordered) returning `{x, 1 - (abs(x)*abs(x))*0.5}` with separate float operations. Otherwise it constructs `{x, float(abs(x)+float(pi/2))}` and calls vector sine. Dispatch global `181827ee8` selects `18132c1b0` or `18132caf0`.
2. The ordinary lane uses the original float `1/pi`, magic-bias integer rounding, four separate pi-reduction products/subtractions, sign-bit parity and a nonfused polynomial. For magnitude above 10000, exponent-indexed reciprocal coefficients feed integer partial products, then the original reconstruction table and polynomial. The scalar integer translation preserves the original separately truncated cross products and unsigned wraparound. The tables are 7,168 bytes of original algorithm coefficients at `18191b100..18191d000`, verified against the loaded AEX; they are not sampled expected outputs.
3. Caller `18114f779..18114f7f5` converts integer degrees to double, multiplies by binary constant `0x3f91df46a2529d39`, converts to float, calls sincos, and computes extents using separate `MULSS`, `ADDSS`, `ADDSS 4`, truncation, and `max(source_extent+4, extent)`. Rendering and budget/helper geometry now use this same calculation. Warp matrix trigonometry is a different owner and was not changed.
4. `probe_kirakira_sincos_F11.py` validates the import-free fifth-argument ABI, all coefficient bytes, 204,190 deterministic inputs on each of dispatch values 1 and 2, and 26,818 captured integer reduction lane values at `18132c7cb`: **zero mismatches**. Inputs include 0.01-degree increments across ±720°, half-radian increments across ±12000, adjacent float words around branch boundaries, signed zero/subnormals, seeded random finite float bit patterns, maximum finite values, infinities and quiet/signaling NaNs. Shared leaf output SHA256 is `d9474d0a355251c940c97bf373897ac9067d99091def56eee14988b19dd3026b`.
5. The same probe executes the actual caller conversion/sincos/extent block through `18114f7f8` for 6,323 angle/dimension tuples: integer degrees −720..720 with 1×9, 9×1 and 31×27, plus 2,000 seeded int32 angles and dimensions 1..4096. Radians, sine/cosine and both extents all match. Combined output SHA256 `f853efdb4bc306f91d0f6155d61434d8094d64d20664a4767751ba718a3bb524`.
6. An earlier 204,182-finite-input translation matched both dispatch paths. Extending it to exceptional inputs exposed two negative-NaN cosine sign differences (`ff800123` first: AEX `230180ff2301c07f`, host arithmetic `230180ff2301c0ff`). The small-branch implementation now explicitly preserves the sign-cleared SSE NaN operand and quiet bit; the full final sweep passes. No rendering expected-value patch was used.

Paired original full-caller traces independently bind to the public worker's output before and after (**2/2 each**):

| Cluster / index | Before first boundary | After measured boundary | Final differing bytes before→after |
|---|---|---|---:|
| C60 / 148, PF16 9×1 | AEX workspace 13×12, Mac 13×13 | All captured source/seed/helper/ray/glow/compose stages exact | 8→0 |
| C62 / 78, PF8 1×9 | AEX workspace 12×13, Mac 13×13 | Workspace, helper and all rays exact; six PF8 glow words still differ | 36→0 |

C60 first final difference before: byte 2, sample 1, AEX `ff45`, Mac `4e47`. Final AEX/Mac SHA256 `42d2fa2c4a87995fdb12478d5d894685848cbb65acd71e1329b6029e56b85eda`.
C62 first final difference before: byte/sample 0, AEX `5e`, Mac `6f`. Final AEX/Mac SHA256 `1218e7890e7fe362ea583290b3613f6cb3535e7de046a9d69d378870442a9c19`.
C62's remaining first float difference is glow word 4: AEX `24ba883f`, Mac `25ba883f`. Its final quantized output is exact. The separate PF8 aggregation issue documented by F09 was not changed.

Campaigns: `--plugin olmkirakira --n 300 --seed 1 --jobs 2`, each using a scratch `--corpus`; E/M/R/U = exact/mismatch/refusal/uncompared:

| Campaign | Classic E/M/R/U | Smart E/M/R/U |
|---|---|---|
| Production before | 0/0/300/0 | 0/0/300/0 |
| Production after | 0/0/300/0 | 0/0/300/0 |
| Diagnostic gates off before | 198/89/0/13 | 98/39/163/0 |
| Diagnostic gates off after, ASan/UBSan | 210/77/0/13 | 101/36/163/0 |

All runs complete with 287 AEX outputs and 13 AEX rejections. No previously exact route regresses. All 300 production result records remain identical. No sanitizer failure is reported. Five diagnostic route records change while remaining mismatches (index 34 both routes, 136/200/232 Classic); the committed evidence retains them. Per-sample monotonicity is asserted for the saved corpus, not these unshrunk campaign inputs.

Orchestrator-visible corpus before/after table (expectations unchanged):

| Shrunk index | Classic | Smart | Changed Classic / Smart typed samples |
|---|---|---|---:|
| 45 | mismatch→exact | mismatch→exact | 371 / 371 |
| 78 (C62) | mismatch→exact | refusal→refusal | 36 / 0 |
| 148 (C60) | mismatch→exact | refusal→refusal | 4 / 0 |
| Other 59 diagnostic cases | unchanged | unchanged | 0 / 0 |
| All 8 production cases | unchanged refusal | unchanged refusal | 0 / 0 |

The independent audit rebuilds both source revisions and checks **140 route replays, 782 changed typed samples, zero changes away from exact**. The existing audit utility gained an optional `--both-routes`; its default behavior is unchanged. Sanitized diagnostic replay independently confirms the route table. Strict saved-result replays exit 1: production matches 6/8 (the inherited Smart COUNTS metadata drift at indices 2/3); diagnostic matches 48/62 (11 inherited F09 improvements plus these three improvements). No saved expectations were silently updated.

Existing tests: generic-beta lane (9), merge2 float oracle (6), outer compose oracle (9), bounded highlight/typed-writer ownership assertion (1): **25 passed**. Existing compiled generic-beta sanitizer test: **1 passed in 43.228 s**, checking its 54 clean/deterministic rows. Its first direct invocation could not find untracked SDK `Util` files in this worktree. Re-running with only that test module's SDK root set to MAIN, while retaining the worktree HARNESS and SOURCE constants, passed. No SDK files were copied and no MAIN files were written. `git diff --check` passes.

inference:

- The C60/C62 geometry mismatch was caused by replacing the embedded float vector-sine construction and float extent operation order with double libm trigonometry/extents. Static instructions, independent leaf/intermediate probes and restored full-caller geometry support the fix separately from final-byte equality.
- The table-driven large-angle branch is required because the original raw fixed ANGLE integer is consumed as degrees. Coefficients and branch arithmetic were recovered generally, without canonical-angle special cases.
- This closes the ticket's numeric clusters on their comparable Classic diagnostic route; it does not admit new production tuples or convert their Smart refusals into comparisons. Native AE/UCRT/GPU behavior and exhaustive float-domain equivalence are not established by these finite CPU-emulator probes.

changed_files:
- `core/kirakira_sincos.h`
- `core/kirakira_sincos_tables.h`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_sincos_F11.py`
- `tools/emulation/audit_kirakira_numeric_corpus_F09.py`
- `tools/emulation/summarize_kirakira_sincos_F11.py`
- `reports/fuzz/olmkirakira_sincos_F11.json`
- `orchestra/reports/F11-kira-float-sincos-recovery.md`

verify:

From this worktree, use the MAIN Python environment by absolute path. Commands below re-check the final implementation and reconstruct the pre-fix source for paired traces/corpus comparisons. Baseline campaigns in the evidence used the same campaign commands before editing, with `before-prod` / `before-gateoff` paths and no sanitizers for the diagnostic baseline.

```sh
s="$PWD/orchestra/state/F11-kira-float-sincos-recovery"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 51b739b4cd7cf4751c0d01ef17f8a8ac54733e10:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
"$py" tools/emulation/probe_kirakira_sincos_F11.py --scratch "$s/leaf-verified" --report "$s/leaf-verified.json" > "$s/leaf-verified.log" 2>&1
"$py" tools/emulation/trace_kirakira_numeric_F09.py --source "$s/before.cpp" --indices 148 78 --scratch "$s/before-trace" --report "$s/before-trace.json" > "$s/before-trace.log" 2>&1
"$py" tools/emulation/trace_kirakira_numeric_F09.py --indices 148 78 --scratch "$s/final-trace" --report "$s/final-trace.json" > "$s/final-trace.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/final-audit-both" --report "$s/final-audit-both.json" > "$s/final-audit-both.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$s/final-prod" --report "$s/final-prod.json" --corpus "$s/final-prod-corpus" > "$s/final-prod.log" 2>&1
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/final-gateoff" --report "$s/final-gateoff.json" --corpus "$s/final-gateoff-corpus" > "$s/final-gateoff.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/final-replay-prod" --report "$s/final-replay-prod.json" --corpus "$s/final-replay-prod-corpus" > "$s/final-replay-prod.log" 2>&1
# Expected exit 1 (6/8 saved records); continue explicitly.
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$s/final-replay-gateoff" --report "$s/final-replay-gateoff.json" --corpus "$s/final-replay-gateoff-corpus" > "$s/final-replay-gateoff.log" 2>&1
# Expected exit 1 (48/62 saved records); continue explicitly.
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
PYTHONPATH=tests python3 - <<'PY' > "$s/final-sanitizer-test.log" 2>&1
import pathlib, unittest
import test_olmkirakira_generic_beta_sanitizers_20260820 as test
test.ROOT = pathlib.Path('/Users/onmk/Documents/Projects/Personal/OLM as')
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test))
raise SystemExit(not result.wasSuccessful())
PY
git diff --check
```

Expected: leaf and geometry counts/hashes above with zero mismatches; both final target hashes exact and bound; 140 audited routes / 782 changed samples toward exact; production and diagnostic counts as in the table; 25 fast tests plus the sanitizer test pass. To regenerate the combined machine evidence after both baseline and final campaign files exist:

```sh
python3 tools/emulation/summarize_kirakira_sincos_F11.py --scratch "$s" --report reports/fuzz/olmkirakira_sincos_F11.json
```

next:
- Separate follow-up: PF8 reciprocal aggregation discrepancy (F09 index 77 regression witness and C62's six glow words); do not widen this fix into aggregation tuning.
- Production/Smart admission remains separate work requiring its own gate-off exact evidence and sanitizer proof. This ticket changes no admission predicates.
- Orchestrator may reconcile saved mismatch expectations using the explicit table above; inherited production COUNTS metadata drift also remains separate.
