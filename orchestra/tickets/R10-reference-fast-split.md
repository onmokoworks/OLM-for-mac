depends: P07a-parallel-helper-kirakira
# R10: keep a faithful reference implementation next to every speed optimization, plus a reference-vs-fast differential test

## Why (orchestrator decision, from a user discussion)
- P05a-c and P07a put speed optimizations (fast paths, SIMD, caches, threading) directly into the faithful reconstruction. The faithful form should stay readable and buildable, and it gives us a second oracle.
- **Two-stage verification.** "Original AEX == reference" is checked on the emulator, which is slow and capped at 1920x1080 (and PF32 full HD fails). "Reference == fast" can then be checked natively, at any size (1080p, 4K) and in large numbers.
- P05b's once-per-angle trig table **restores** the original's structure, so it is the reference, not an optimization.

## Do
1. **Build switch.** Add `OLM_REFERENCE_BUILD` (a compile definition). When it is set, every optimized function uses its faithful sequential/scalar form:
   - restore the pre-optimization code from git history next to the fast code, as a separate function in the same file;
   - do not duplicate whole files; the fast path stays the default;
   - threading already collapses with `OLM_PARALLEL_MAX=1`, but the reference build must not need the env var.
   Cover these optimizations:
   - DirectionalBlur P05a: `core/dblur_rowdriver.cpp` fast paths, channel SIMD, row partitions, rotation `-O2` flags;
   - RadialBlur P05b: `RadialScatterSIMD.h`; keep the trig table;
   - OLMBlur P05c: 2 lanes;
   - ColorKey P05c: Lab key cache;
   - Smoother P05c: bounded stack clears;
   - KiraKira P07a: threading/helper.
   Find the exact pre/post commits with `git log` (merges f05c36af, 738aed52, c7e63a63, and P07a's merge).
2. **Differential harness.** Build `tools/perf/ref_vs_fast.py`:
   - build each plugin's test host twice (reference and fast);
   - run the same generated cases through both, and compare raw output bytes and rects;
   - generate the cases with the fuzz generators: default, realistic-v1/v2, odd-even-v1 with a large `--max-size` (up to 3840x2160), and all depths;
   - it needs no oracle.
   Run per plugin at least: 200 small cases, 20 cases at 1080p, and 5 at 4K, including the heaviest corpus params. All must be byte-identical. For threaded code, also run under the fast build with `OLM_PARALLEL_MAX` set to 1, 2 and 8.
3. **Hook.** Document the harness in `tools/perf/README.md`. Make it runnable for one plugin in under ~10 minutes, so later speed tickets (P07b-e) can use it as their main acceptance step.

## Acceptance
- The reference build of each plugin passes default fuzz seed 1 n100 against the oracle (Smart; Classic for Smoother v1), with the same results as the fast build. Its corpora replay true.
- The fast build is unchanged: same output hashes as before R10 on default seed 1 n300 for each touched plugin.
- ref_vs_fast reports all byte-identical, with the case counts above.
- Release bundles still build with the fast path (`tools/fuzz/build_F47_bundles.py`), and timings are not regressed (spot-check with the P00b driver under `lockf -k ~/.cache/olm-emu/bench.lock`).

## Rules
- Use 1-2 processes, and check `memory_pressure` (≥30% free).
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, and do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies; do the plugins one by one, starting with DirectionalBlur.
