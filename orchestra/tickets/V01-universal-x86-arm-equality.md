# V01: Intel (x86_64) slice == Apple Silicon (arm64) slice after the speed work

## Why
- Every bundle is Universal. F51 proved x86_64 == arm64 bit-exact, but since then P05a-c, P07a-e and R10 added SIMD paths (`RadialScatterSIMD.h`, DirectionalBlur channel SIMD), IEEE fast paths and GCD threading. On x86_64 these compile to different instructions and may take different code paths (`#if __aarch64__` / NEON vs SSE).
- If the x86_64 slice differs, Intel Mac users get output that does not match the Windows version.

## Do
1. Build fresh Universal bundles at HEAD (`tools/fuzz/build_F47_bundles.py`). Run the same cases through the **x86_64 slice under Rosetta** and the arm64 slice natively, and compare output bytes and rects. Read `orchestra/reports/F51-*` for the existing x86 host (`~/.cache/olm-emu/worker-F51-x86host/`) and how it loads a bundle slice. Rebuild it if needed (a host change only).
2. Coverage per plugin (all 10):
   - default fuzz seed 909 n100;
   - realistic-v1 and realistic-v2 seed 909 n100;
   - odd-even-v1 seed 2026 n50 (T15b flags);
   - the P00b heavy presets at 1080p and 4K, 8/16/32 bpc;
   - for threaded plugins, `OLM_PARALLEL_MAX` 1, 2 and 8 on both slices.
3. Also compare the x86_64 slice against the original oracle (F53) on the default and realistic-v1 n100. That is direct evidence for Intel users.
4. Grep the sources for architecture conditionals (`__aarch64__`, `__x86_64__`, `__SSE`, `arm_neon.h`, `immintrin`) and list each one with the function it guards, in the report.

## Acceptance
- 0 byte differences between slices. Any difference: give a minimal repro and the source line, and fix it if it is clearly local (e.g. a missing x86 path), keeping the arm64 output and R10 `ref_vs_fast` unchanged. Otherwise report it.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Do not touch the release gate or ledger. Commit partial results at least every 30 minutes. The stop rule applies.

## Resume note (orchestrator)
- Your previous run was killed by an orchestrator queue restart (not by anything you did). Your worktree, commits and any uncommitted files are intact. Read your own commits, report draft and `orchestra/state/<ticket>/` first, and continue from there instead of starting over.
