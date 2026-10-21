status: blocked

summary:
- Restored PF32 seed eligibility to alpha == 1 or unordered NaN; finite HDR alpha and infinities are not seeds.
- Fresh seed 1 Smart improves 277/300 -> 300/300; fresh seed 2 improves 276/300 -> 300/300. Classic remains 300/300 no-write on each seed.
- All 300 original corpus cases and all 23 T13 reduced cases now match the original AEX. Historical corpus observations are retained.
- All 64 boundary witnesses and 87 intermediate seed maps are exact; 1,974 ASan/UBSan public renders are clean and 13 tests pass.
- Status is blocked solely because automatic approval review rejected final scratch cleanup; the worker brief requires blocked after any permission rejection.

facts:

Base `c736e6767627de32bdb39e30f8904ee0b1c9a3ab`, branch `orch/F21-toondilate-pf32-seed`. Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, ToonDilate ledger rows, the compatibility plan, and T13's `TD-PF32-SEED` evidence. No release gates, ledger, other plug-ins, MAIN, original AEX, emulator sources or installed host were modified. No push or history rewrite. Final cleanup was rejected by automatic approval review; details below. No admission guard was relaxed.

The original decompilation at MAIN `decomp/OLMToonDilate.aex.c.txt:476042` initializes each distance to `0xffffffff`, then selects zero on comparison with the 1.0 constant. The committed verifier independently disassembles the original bytes at `0x1801a698e`: `UCOMISS XMM0,XMM6`, then `CMOVE EDX,EBX` at `0x1801a6991`. The decompiler's equality expression alone does not express unordered behavior. T13's real worker hook at `0x1801a69a3` is reused for fresh seed-distance captures; the import-free five-argument ABI check, input immutability and direct-worker/public-output equality are asserted.

Identities:

| Artifact | SHA256 |
|---|---|
| Original OLMToonDilate AEX | `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3` |
| Indexed prebuilt worker | `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2` |
| Before production source | `7d0d63cb807bc31cd917a01361419248e7939d4f0e43fd84ef951cd50c653c4a` |
| After production source | `509b1c1b3c60bc25f80bb65bcdc46cfcee51d8732a54e2a771f44577ec30f258` |

**Fresh campaigns.** Ran `python3 tools/fuzz/run.py --plugin olmtoondilate --n 300 --seed SEED --jobs 2 --worker "$w" --scratch "$s" --corpus "$s/CORPUS" --report "$s/REPORT.json" > "$s/REPORT.log" 2>&1` with the exact substitutions below; `$s`/`$w` are defined in verify. All output was redirected to ticket scratch.

| Source / SEED | CORPUS | REPORT |
|---|---|---|
| before / 1 | corpus-before | before-seed1 |
| before / 2 | corpus-before2 | before-seed2 |
| after / 1 | corpus-after | after-seed1 |
| after / 2 | corpus-after2 | after-seed2 |

 Baseline reports are committed as `reports/fuzz/olmtoondilate_F21_before_seed{1,2}.json`; after reports are in scratch and their hashes/changed rows are bound in the committed verification JSON.

| Population | Smart before exact / mismatch | Smart after exact / mismatch | Classic before / after | Regressions |
|---|---:|---:|---:|---:|
| seed 1, n 300, jobs 2 | 277 / 23 | 300 / 0 | 300 / 300 no-write | 0 |
| seed 2, n 300, jobs 2 | 276 / 24 | 300 / 0 | 300 / 300 no-write | 0 |

All original per-route oracle dictionaries remain identical before/after. The verifier checks every input hash and index, unchanged Classic results, and that every changed Smart result moves from mismatch to exact. Classic no-write is measured relative to each host's initial destination (AEX zero, Mac `0xee`); it is not a numerical exact-image claim. No refusals or framework errors occurred in the four campaigns.

First pre-fix mismatches:

| Seed / index | Input | Different bytes / words | First byte / word | AEX -> Mac word, little endian |
|---|---|---:|---|---|
| 1 / 15 | PF32 signed, 9x19 | 908 / 240 | 128 / 32 | `0000803f` -> `dabfd93f` |
| 2 / 30 | PF32 HDR, 14x14 | 1638 / 472 | 16 / 4 | `0000803f` -> `3f40fe40` |

Both are now zero-difference, as are all other cases in these two campaigns.

**Corpus before/after table.** Before the fix, the standard `run.py --replay tests/fuzz_corpus/olmtoondilate` command completed 300/300 with `replay_matches_saved=true`. The committed verifier replays both corpora against fresh original AEX outputs, the reconstructed before source (hash-checked against the campaign), current production, and sanitized production. It asserts every saved before/oracle hash, then requires current exactness.

| Retained corpus | Cases | Before Smart exact / mismatch | After Smart exact / mismatch | Changed toward exact | Classic before / after |
|---|---:|---:|---:|---:|---:|
| `tests/fuzz_corpus/olmtoondilate` | 300 | 277 / 23 | 300 / 0 | 23 | 300 / 300 no-write |
| `tests/fuzz_corpus/olmtoondilate_T13` | 23 | 0 / 23 | 23 / 0 | 23 | 23 / 23 no-write |

No corpus expectations were rewritten. The verification JSON contains a per-file before/after table with input, candidate and oracle hashes, first mismatch, and original/Mac seed maps for every reduced case. This is an explicit current-result overlay on the retained historical mismatches, so plain replay against historical saved results is expected to report differences after the fix. The T13 profiles (HDR index 46, signed index 220, nonfinite index 17) and all other 20 shrunk cases are exact after the fix.

**Boundary and sanitizer results.** Executed the verifier command below with `--report reports/fuzz/olmtoondilate_F21_verification.json`; it exited 0 / PASS. Original instruction bytes are `0f2ec60f44d3`. All 23 reduced-case masks and all 64 boundary masks equal the corresponding production seed arrays; direct-worker and public AEX final bytes also agree for all 87 captures. The source-instrumented candidate's final bytes equal the uninstrumented candidate.

Boundary coverage: 16 raw alpha words x horizontal/vertical two-pixel geometry x both pixel orders, radius 2, 3-byte input and 5-byte output padding. Words: `3f7fffff`, `3f800000`, `3f800001`, `40000000`, `7f7fffff`, `ff7fffff`, `7f800000`, `ff800000`, `7fc12345`, `ffc12345`, `7f812346`, `ff812346`, `00000000`, `80000000`, `00000001`, `80000001`. These cover the immediate FLOAT32 neighbors of 1, finite HDR and signed maxima, both infinities, both signs of quiet/signaling NaNs, signed zeros and minimum subnormals. Inputs are packed from integer words to avoid Python quieting signaling NaNs. Full ARGB bytes, including NaN payloads, are compared exactly.

| Alpha word | Captured original seed distance | Before -> after |
|---|---|---|
| `3f7fffff` (below 1) | `ffffffff` | exact -> exact |
| `3f800000` (1) | `00000000` | exact -> exact |
| `3f800001` (above 1) | `ffffffff` | mismatch -> exact |
| `7f800000` (+infinity) | `ffffffff` | mismatch -> exact |
| `ff800000` (-infinity) | `ffffffff` | exact -> exact |
| `7fc12345`, `ffc12345` (quiet NaNs) | `00000000` | mismatch -> exact |
| `7f812346`, `ff812346` (signaling NaNs) | `00000000` | mismatch -> exact |

Boundary total: 32 exact / 32 mismatch before, 64 exact / 0 mismatch after. Both Classic builds preserve all 64 destinations. Production sanitizers use ASan+UBSan, abort-on-error, leaks disabled, `-O1 -fno-fast-math -ffp-contract=off`. All 1,974 sanitized renders (600 campaign cases + 323 corpus cases + 64 boundaries, each on both routes) equal uninstrumented current output, with zero process/sanitizer errors. The two campaigns alone contribute 1,200 of these renders. No gate-off experiment was needed because no admission guard changed.

**Existing tests.** Initial requested subset: 10 passed, 2 failed. Both failing methods also fail against the pre-fix production source (baseline typed tests: 5 passed, 2 failed): stale expectations named `RenderWorld` instead of the existing `RenderTileWorld`, used the old row-byte variable name, and captured tile-worker code as part of the admission function. Updated those source-text assertions to the actual existing call/variables/function boundary, without changing production guards. Updated the portable Python model's stale PF32 predicate. A new compiled-production test replays all captured raw boundary witnesses against their original-AEX hashes, including NaN payloads. Final command is the three-file pytest subset shown below: **13 passed in 5.13 seconds**, exit 0. The initial MAIN venv and system Python lacked pytest; a scratch-only venv with pytest 9.1.1 supplied the test runner. No MAIN environment was modified.

inference:
- The measured PF32 residuals are caused by seed initialization. Equality-or-NaN reproduces the original ZF selection; `>= 1` incorrectly seeds HDR/+infinity and rejects NaNs. This is a general predicate correction, not a sample/coordinate patch.
- These results establish the listed emulated CPU/fake-SDK contracts. They do not establish all-input compatibility, native Windows/AE, floating-point exception-state parity, or arbitrary native ROI/downsample behavior.
- No numerical hypothesis was refuted. The pytest dependency and stale source-text checks were test-environment/assertion issues, not failed numerical hypotheses.

changed_files:
- `mac/OLMToonDilate/OLMToonDilate.cpp`
- `tests/test_olmtoondilate_typed_core.py`
- `tests/test_olmtoondilate_generic_beta.py`
- `tools/fuzz/verify_toondilate_F21.py`
- `reports/fuzz/olmtoondilate_F21_before_seed1.json`
- `reports/fuzz/olmtoondilate_F21_before_seed2.json`
- `reports/fuzz/olmtoondilate_F21_verification.json`
- `orchestra/reports/F21-toondilate-pf32-seed.md`

verify:

Run from this worktree; the original AEX and SDK remain in MAIN and the indexed worker is used without rebuilding. Commands regenerate current campaigns and independently recheck the historical baseline source/results from committed evidence:

```sh
s="$PWD/orchestra/state/F21-toondilate-pf32-seed"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
for seed in 1 2; do
  python3 tools/fuzz/run.py --plugin olmtoondilate --n 300 --seed "$seed" --jobs 2 \
    --worker "$w" --scratch "$s" --corpus "$s/recheck-corpus-$seed" \
    --report "$s/after-seed$seed.json" > "$s/recheck-seed$seed.log" 2>&1
done
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" \
  tools/fuzz/verify_toondilate_F21.py --scratch "$s" --report "$s/recheck-verification.json" \
  > "$s/recheck-verification.log" 2>&1
tail -5 "$s/recheck-verification.log"
python3 -m venv "$s/test-venv"
PIP_CACHE_DIR="$s/pip-cache" "$s/test-venv/bin/python" -m pip install pytest==9.1.1 \
  > "$s/pytest-setup.log" 2>&1
"$s/test-venv/bin/python" -m pytest -q --tb=no -p no:cacheprovider \
  tests/test_olmtoondilate_typed_core.py tests/test_olmtoondilate_generic_beta.py \
  tests/test_olmtoondilate_roi_safety.py > "$s/tests.log" 2>&1
tail -2 "$s/tests.log"
git diff --check
```

Expected: pytest 13 passed; both campaigns Smart 300 exact, Classic 300 no-write, no mismatch/refusal/framework error. Verification asserts corpus 323/323 Smart exact and Classic no-write, all 87 traced masks equal, 64/64 boundary outputs exact, both seed campaigns unchanged or improved, and no sanitizer errors. Timestamps, build paths and binary hashes may vary. No tolerance.

next:
- Numerical work and acceptance checks are complete. Orchestrator review/merge remains; native AE/Windows and wider ROI/radius/performance coverage are separate follow-up work. No admission-gate change is justified by this ticket.
- Cleanup blocker: automatic approval review rejected the final combined report-update/cleanup command with `rm -f style commands are not permitted. Use a safer approach`. The intended deletion targets were the ticket-created `test-venv`, pip cache and generated verifier bytecode. Nothing in that rejected command executed. No retry or permission escalation was attempted; this report update was issued separately. Per the worker brief's explicit rejection rule, final status is blocked even though the fix and checks passed.
- Native harness builds were already removed automatically by temporary-directory scopes. The scratch dependency environment/cache remains (about 34 MiB total scratch, below 5 GiB), and the generated ignored bytecode may remain. Orchestrator can finish that housekeeping through its approved workflow. No installed host or source dependency was touched.
