status: blocked

summary:
- Implemented and verified the requested synthetic-stack UB repair in both Smoother v1 memory adapters; output bytes stay identical.
- Fatal ASan/UBSan corpus replay improves from 0/29 to 29/29 `matches_saved`, with no remaining sanitizer failures.
- Seed-1 n-300 fuzz results are unchanged on both routes: 62 exact, 29 mismatch, 95 refusal, 114 uncompared.
- Overall ticket acceptance is blocked only by requirement 1: the retained numerical mismatches remain, and their oracle-host cause is not proven. No speculative pixel correction was made.

facts:

Base commit: `0e1057f39e5d24858e483c440c0e6d2a1fdbfd5a`; branch `orch/F22-smoother-classifier-stack-ub`. Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the Smoother v1 ledger row, compatibility plan, and T11's two cluster rows and `SM1-CLASSIFIER-STACK-UB` evidence. Only this worktree was modified.

**Cause and audit.** Before editing production, the ordinary corpus replay returned 29/29 `matches_saved`; the fatal `-O2 -fsanitize=address,undefined -fno-sanitize-recover=all` replay failed all 29 cases on both routes (58 candidate errors). Both minimal witnesses report:

```
OLMSmoother_port.cpp:1359:70: runtime error: index 123145302311056 out of bounds for type 'const uint8_t[384]'
```

That index is `kStack + 0x90`, not a stack-array offset. The saved original-AEX disassembly in `refs/conformance/olmsmoother_v1_classifier8_tail_cfg_20260805.json` records `0x18000896c: 4863842490000000`, `movsxd rax, dword ptr [rsp + 0x90]`; the generated translation calls `M.read32(R.rsp+0x90)`. At `0x180008cb7`, `894c2470` stores `ecx` to `[rsp+0x70]`. The port must translate these integer guest addresses before native pointer addition. Original instruction order, generated CFGs, stack sizes, register values, and table/state/world overlays are unchanged.

Audited both synthetic-stack memory adapters and their generated callers:

| Adapter | Repaired pointer expressions | Other audited operations |
|---|---|---|
| `Classifier8TailMemory` | 32/64-bit read and write: 4 sites | Byte indexing already subtracts before pointer formation; all widths now share a subtraction-based range check |
| `SubHandler8Memory` (also shared by PF16 generated paths) | 16/32/64-bit read and write plus `ptr`: 7 sites | Byte indexing already safe; replaced the addition-based range check |

All 11 `stack+a-kStack` expressions become `stack+(a-kStack)`. Bounds now require `a >= kStack`, `n <= sizeof(stack)`, and `a-kStack <= sizeof(stack)-n`, avoiding wrap in `a+n`. Native fallbacks continue to use `memcpy`; module-table and host-field mappings are unchanged. The local stack initializer uses bounded literal offsets; generated `ptr` calls retain their existing typed output argument contract. This is an audit of these helpers, not a claim that arbitrary invalid native addresses are safe.

**Before/after campaign.** Ran the exact `run.py --plugin olmsmoother --n 300 --seed 1 --jobs 2` command below before and after, each with a separate scratch corpus. Both completed all 300 cases. All 300 input hashes and all 300 complete result dictionaries are identical (including both route output hashes/status/metadata and oracle results).

| Route | Exact before → after | Mismatch before → after | Refusal before → after | Uncompared before → after |
|---|---:|---:|---:|---:|
| Classic (original advertised owner) | 62 → 62 | 29 → 29 | 95 → 95 | 114 → 114 |
| Mac Smart wrapper versus original Classic | 62 → 62 | 29 → 29 | 95 → 95 | 114 → 114 |

PF16's 114 original-worker failures remain `legacy new-world requested unsupported DEEP_PIXELS`. PF32's 95 original rejects and Mac refusals remain unsupported-depth probes. Neither population is counted as exact. No admission guard was relaxed.

**Corpus before/after table.** No corpus file was modified. Per-case baseline result dictionaries, first differences, output hashes, and equality booleans are committed in `reports/fuzz/olmsmoother_f22_stack_ub.json`.

| Replay | Before | After |
|---|---:|---:|
| Ordinary `matches_saved` | 29/29 | 29/29 |
| Fatal ASan/UBSan `matches_saved` | 0/29 | 29/29 |
| Fatal ASan/UBSan candidate errors, Classic / Smart | 29 / 29 | 0 / 0 |
| Ordinary complete case result changed | — | 0/29 |
| Ordinary exact / mismatch, each route | 0 / 29 | 0 / 29 |

Both target representatives are sanitizer-clean after the repair, with exactly their pre-fix output. The following differences against the frozen worker remain on both routes:

| Retained case | First differing byte | Original worker → Mac | Differing bytes before → after |
|---|---:|---|---:|
| `seed1_case000000_eaba52d5eacc.json` (1×19) | 64, alpha at (0,16) | `41` → `00` | 4 → 4 |
| `seed1_case000006_92552f06afe6.json` (1×3) | 0, alpha at (0,0) | `c6` → `ce` | 4 → 4 |

**Fresh original-AEX and intermediate checks.** Re-ran `compare_olmsmoother_classifier8.py` with both representatives and all 29 owner-corpus cases. The 22 pixels × four directions give **88/88 equal classifier results**. The independent retained original `PF_Cmd_RENDER` host matches the repaired Mac output on **29/29** cases and the frozen worker on **0/29**. This reproduces T11's host disagreement; it does not locate its first differing internal stage or establish which host matches native Windows AE. The existing oracle and corpus were preserved.

SHA256 provenance:

| Artifact | SHA256 |
|---|---|
| MAIN original `plugins_2025/OLMSmoother.aex` | `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82` |
| Indexed frozen worker | `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2` |
| Production source before | `ca645f6221c8d9ece748e200b5cd9b716ac7c73b8eaaf5935fde6394f7ece8b6` |
| Production source after | `abe5cee8947cd08133b85cc477c4366c058404d067ddfac5c61680f2998bda86` |
| 1×19 Mac before = after = independent original host | `e4f44ecd351477f9861716f65c27796d24403ed225a363f1f6e4db89d880db3c` |
| 1×19 frozen worker | `f08a7d4dc586eee162a6bc89d8a3a7e8b9762628c8ee9b9166ae9e051d90d39a` |
| 1×3 Mac before = after = independent original host | `490b976bf36201c4ba4731b7550a741f9974a17354ddee7f9eca79860da1a998` |
| 1×3 frozen worker | `71a368f23d17753295e7423d46a50325de390846956a8d24fbc40e387ac0cb6f` |

**Tests.** Five existing fast checks passed: the three functions in `test_olmsmoother_v1_pf16_classifier_direction_pair_20260806.py`, plus `GenericClassicBeta.test_source_uses_bounded_transactional_world_safety` and `test_sanitized_odd_sd_all_tolerances_and_determinism`. One new fatal-ASan/UBSan test passes at `-O2`: every valid byte offset for each supported access width in both adapters, byte-for-byte store footprint, unaligned native fallback, first/last valid accesses, crossing-end/oversized/wrapping range checks, and every valid `ptr` offset. The HD/4K performance-oriented tests were not run.

The initial pytest invocation could not start because neither the MAIN emulation venv nor system Python has pytest. Ran the existing unittest cases and plain test functions directly instead; no installation or MAIN change. The initial sanitizer wrapper omitted propagation of `run.main()`'s return code; baseline findings above come from the actual report/candidate diagnostics, not that wrapper exit code. Corrected it to `sys.exit(run.main())` and reran the final sanitizer replay successfully.

inference:

- Integer-offset translation fixes the demonstrated C++ UB while preserving the intended guest memory semantics. The sanitizer and byte-equality results support this for the tested inputs.
- UB is not established as the cause of the retained pixel discrepancies: ordinary output remains identical after repair, and two original-code hosts still disagree. Do not tune the port against that unresolved boundary.
- The specific F22 UB goal and acceptance items 2–4 are satisfied. Requirement 1 is not: the frozen-worker target cases remain mismatched, and the responsible host behavior has not been isolated. The report is therefore `blocked`, not an assertion of full numerical completion. No two refuted numerical hypotheses were pursued.

changed_files:
- `mac/OLMSmoother/Mac/OLMSmoother_port.cpp` — both memory adapters' offset translation and overflow-safe range checks.
- `tests/test_olmsmoother_v1_synthetic_stack.py` — sanitizer-backed helper boundary coverage.
- `tools/fuzz/replay_olmsmoother_sanitized.py` — standard corpus evaluator with fatal ASan/UBSan, unchanged comparison semantics.
- `tools/fuzz/compare_olmsmoother_classifier8.py` — allow its explicit `--scratch` anywhere under this worktree's `orchestra/state`, so F22 does not write T11 scratch.
- `reports/fuzz/olmsmoother_f22_stack_ub.json` — compact before/after evidence, per-campaign-case input/result digests, per-corpus-case results, provenance, and fresh original-AEX comparisons.
- `orchestra/reports/F22-smoother-classifier-stack-ub.md` — this report.

verify:

Run from this worktree. These commands reproduce the after state without modifying committed corpus or evidence. The before campaign/replay used the same commands before editing production, with `before-*` report names and `before-corpus`. Baseline production is available at the base commit above; do not reset this worktree to reproduce it.

```sh
set -e
s="$PWD/orchestra/state/F22-smoother-classifier-stack-ub"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
worker=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
python3 tools/fuzz/run.py --plugin olmsmoother --n 300 --seed 1 --jobs 2 \
  --worker "$worker" --scratch "$s" --budget-minutes 10 \
  --report "$s/verify-fuzz.json" --corpus "$s/verify-corpus" > "$s/verify-fuzz.log" 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother --jobs 2 --worker "$worker" \
  --replay tests/fuzz_corpus/olmsmoother --scratch "$s" --corpus "$s/unused-corpus" \
  --budget-minutes 10 --report "$s/verify-replay.json" > "$s/verify-replay.log" 2>&1
python3 tools/fuzz/replay_olmsmoother_sanitized.py --plugin olmsmoother --jobs 2 \
  --worker "$worker" --replay tests/fuzz_corpus/olmsmoother --scratch "$s" \
  --corpus "$s/unused-corpus" --budget-minutes 10 \
  --report "$s/verify-sanitized.json" > "$s/verify-sanitized.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" \
  tools/fuzz/compare_olmsmoother_classifier8.py --jobs 2 --worker "$worker" \
  --scratch "$s/verify-classifier" \
  --corpus tests/fuzz_corpus/olmsmoother/seed1_case000006_92552f06afe6.json \
  --corpus tests/fuzz_corpus/olmsmoother/seed1_case000000_eaba52d5eacc.json \
  --owner-corpus tests/fuzz_corpus/olmsmoother \
  --report "$s/verify-classifier.json" > "$s/verify-classifier.log" 2>&1
python3 tests/test_olmsmoother_v1_synthetic_stack.py > "$s/verify-helpers.log" 2>&1
PYTHONPATH="$PWD/tests" python3 -m unittest -v \
  test_olmsmoother_v1_generic_classic_beta_20260820.GenericClassicBeta.test_source_uses_bounded_transactional_world_safety \
  test_olmsmoother_v1_generic_classic_beta_20260820.GenericClassicBeta.test_sanitized_odd_sd_all_tolerances_and_determinism \
  > "$s/verify-existing.log" 2>&1
python3 - <<'PY' > "$s/verify-direction.log" 2>&1
import runpy
m = runpy.run_path('tests/test_olmsmoother_v1_pf16_classifier_direction_pair_20260806.py')
for name, test in m.items():
    if name.startswith('test_'):
        test()
        print('PASS', name)
PY
git diff --check
```

Expected: all commands exit 0; campaign completes 300 with the route counts above; ordinary and sanitized replay each have 29/29 `matches_saved`; classifier 22/22 pixels and 88/88 directions; owner 29 Mac-equal / 0 frozen-worker-equal; six total test checks pass. Sanitizer replay JSON contains the exact build command and uses fatal sanitizer options. Original-AEX checks are local emulation, not native AE proof.

next:
- Orchestrator can review and merge the isolated byte-preserving UB fix. Resolve the separate `SM1-ORACLE-HOST-BOUNDARY` ticket before claiming the two numerical clusters exact: compare natural builder/world/callback/dispatch/writeback state across the two original hosts.
- `SM1-ORACLE-PF16` remains responsible for the cached emulator's unsupported `DEEP_PIXELS` callback. No worker rebuild was attempted.
- No release gates, forbidden-action lists, corpus records, other-plugin code, MAIN, emulator source, or installed plugins were changed. No push or history rewrite. Scratch stayed below 5 GiB; regenerable build outputs were removed after checks.
