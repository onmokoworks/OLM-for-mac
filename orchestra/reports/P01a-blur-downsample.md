status: done
summary:
- Smart accepts downsampled worlds and uses the existing float32 X-scale arithmetic.
- Removed Legacy radius-zero copy bypass in all three depths; original passes/writers still run.
- F52 Smart: seed 1 and fresh seed 20261024 each 100/100 exact, zero unavailable.
- Default 300 comparisons unchanged; old 39 and new 43 corpus cases replay exactly.
- Historical unit-suite failures persist unchanged; ASan/UBSan production probe passes.

facts:

Static original-AEX inspection (MAIN `disasm/OLMBlur.aex.asm.txt`, read-only):
- Non-Legacy `0x1800022ee..0x180002315` loads PF_InData+0x11c/+0x120 (X numerator/denominator), converts to float32, DIVSS, MULSS with parameter +0x20 (Amount), stores the scaled float, then CVTTSS2SI truncates toward zero for the radius. Corresponding reads occur at 0x18000377e and 0x180004bf1. The scaled float remains available for the repeated-radius schedule; truncating Amount itself before that schedule would be wrong.
- Legacy `0x180005f67..0x180005fb8` computes the same X ratio, truncates Amount*ratio for radius, and computes sigma from unscaled Amount and Smoothness (+0x24). `0x1800065c9` (bias 1) and `0x1800068a3` (bias 2) multiply sigma by that same ratio before iteration division. Corresponding worker scale reads are at 0x180007347 and 0x180008717. These are scalar float32 operations, not double arithmetic. There is no separate Y-factor use in these six worker scale sequences; Repeat and Bias are not scaled.
- Legacy radius-zero has no corresponding early-copy branch in those original worker setups. Existing Mac helpers can execute the single-center weight with radius zero.

Commands/results:
- F52 sampler, via `python3 orchestra/reports/P01a-evidence/measure.py --seed 1` and `--seed 20261024 --save-witnesses`: unchanged `measure_F52.py --plugin olmblur --n 100` logic, ticket-local scratch, explicit generation seed. Final Smart E/M/R/U = 100/0/0/0 for each seed. Classic E/M/R/U = 3/0/79/18 and 10/0/63/27 respectively (U takes precedence over candidate refusal). Classic was intentionally unchanged: its low-dword parameter ABI and PF32 ownership are separate work, not a cheap reuse of Smart parameters.
- Initial refusal removal alone: seed 1 Smart 98 E, 2 M. First mismatch index 31, PF16 Legacy, full 5x12 -> 3x6, X=1/2, Amount=1, repeat=2, bias=2. 18 words differ; first word 5 original `0000`, candidate `0339`. Original SHA256 `e9d60f76e10221b37bbf75ae2e227afd2f8a5e20fbdeff202d87b7bca451816d`; candidate copied input `aeab2cd5c400c49ebfbf496ae2996dfd7cd18b00eec127fdce20c6713273e85f`. Index 87 has the same radius-zero boundary. Removing the radius-zero bypass closes both. See `P01a-evidence/initial-mismatches.json`.
- F52 worker SHA256 `1be0cb14f6e68ab9276ef37be3a381aae9fb0306914987eb91e1a9d23dd94f4b`; original AEX SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. Full candidate/dependency hashes and 200 result rows are in `P01a-evidence/seed*-summary.json` / `seed*-results.jsonl`.
- `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0` on HEAD baseline and candidate: identical 300/300 result objects, exact→non-exact 0. Both Smart 300 E; Classic 13 E / 287 raw refusals, with 93 unavailable Classic oracles. Evidence: `default-baseline.json`, `default.json`, `regression-summary.json`.
- Standard `run.py --replay`: existing `olmblur` 39/39, added `olmblur_downsample_P01a` 43/43 match saved. New corpus binds F52 worker and packed pixels; covers 8/16/32-bit, Legacy/non-Legacy, symmetric/asymmetric downsample, including radius<1 in all six depth/mode combinations. No expected bytes in existing corpus changed.
- `OLM_TEST_JOBS=1 python3 orchestra/reports/P01a-evidence/unit_tests.py`: all 34 `test_olmblur*.py` files attempted in isolated serial unittest processes. Candidate and HEAD baseline both: 7 exit 0, 24 exit 1, 3 exit 5 (free-function files with no unittest tests). No per-file exit-status changes. Diagnostics retain missing historical handoff/AEX files, stale source/runner hashes and old source-text contracts; these failures are not waived or rewritten. `unit-tests-{baseline,candidate}.json` retains full output.
- Free-function tests additionally invoked: ROI 5/5 pass; historical case0001 2 fail (see `free-tests.json`). Sanitizer initially could not find SDK in worktree; rerun with MAIN SDK include paths below exits 0 and asserts all six odd-geometry cases, with ASan/UBSan enabled. No SDK/assets copied.
- `git diff --check`: exit 0. No native AE session, release-gate changes, ledger edits, oracle rebuild or push.

inference:
- The preview refusal was an admission defect; existing numerical downsample code was already largely faithful. The newly reachable zero-radius Legacy branch exposed a separate premature copy shortcut. The generic pass/writer correction explains the observed differences without coordinate-specific output changes.
- Measurements establish the sampled software-oracle domain, not every native-AE geometry or arbitrary ROI. Classic numerical expansion needs its own ABI ticket.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp`
- `core/olmblur_worker8_legacy.cpp`, `core/olmblur_worker16_legacy.cpp`, `core/olmblur_worker32_legacy.cpp`
- `tests/fuzz_corpus/olmblur_downsample_P01a/*.json` (43 witnesses)
- `orchestra/reports/P01a-blur-downsample.md`, `orchestra/reports/P01a-evidence/*` (reproduction drivers and evidence)

verify:

From this worktree, serially (no writes to MAIN or /tmp):

```sh
export TMPDIR="$PWD/orchestra/state/P01a-blur-downsample"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/P01a-evidence/measure.py --seed 1
python3 orchestra/reports/P01a-evidence/measure.py --seed 20261024
python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/default" --corpus "$TMPDIR/default-corpus" --report "$TMPDIR/default.json"
python3 tools/fuzz/run.py --plugin olmblur --jobs 1 --replay tests/fuzz_corpus/olmblur --scratch "$TMPDIR/replay" --report "$TMPDIR/replay-old.json"
python3 tools/fuzz/run.py --plugin olmblur --jobs 1 --replay tests/fuzz_corpus/olmblur_downsample_P01a --scratch "$TMPDIR/replay" --report "$TMPDIR/replay-downsample.json"
python3 orchestra/reports/P01a-evidence/unit_tests.py
CPLUS_INCLUDE_PATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources' python3 tests/test_olmblur_generic_beta_sanitizers_20260820.py
```

Expected: Smart 100 E for each F52 seed; default Smart 300 E; replay 39/39 and 43/43; historical unittest exit 1 with the counts above; sanitizer exit 0. Do not interpret historical unit failures as a green suite.

next:
- Orchestrator review/merge, then native AE 26.3 preview 1/2 and 1/4 validation of the built plugin.
- Separate Classic ABI/ownership expansion and historical unit-fixture maintenance tickets.
