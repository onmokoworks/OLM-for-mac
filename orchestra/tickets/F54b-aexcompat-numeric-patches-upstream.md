# F54b: AEXCompat upstream: the F29-F46 numerical patches and F32 legacy worlds, until the upstream worker equals F53 on every corpus

## Facts (`orchestra/reports/F54-aexcompat-geometry-arena-upstream.md`)
- F54 upstreamed geometry and UHD/PF32-full-HD storage on branch `olm/F54-geometry-arena` (worktree `~/Documents/Projects/Personal/04_Tools/AEXCompat-olm-F54`). ColorKey and Smoother2 corpora and the F53 crop witnesses are byte-exact.
- Blocked:
  - Blur and RadialBlur arithmetic differ from F53;
  - Smoother's legacy DEEP_PIXELS world (F32) is missing.
  The numerical patches F29/F30/F44/F45/F46 (SSE NaN order, UCRT math and others, in `tools/emulation/aexcompat_patches/`) are not upstream yet.

## Do
- On the same AEXCompat branch (or a stacked branch `olm/F54b-numeric`), port the remaining OLM patches into AEXCompat proper, one patch per commit with behavioural tests: F29, F30, F32, F44, F45, F46, and any others the F54 inventory lists as missing.
- Goal: the upstream worker reproduces F53 byte-for-byte on **all** OLM corpora for all 10 plugins (replay every `tests/fuzz_corpus/*` set with the matching flags against both workers and diff the results). Then measure 4K for all 10 plugins.
- Same AEXCompat rules as F54:
  - follow `AGENTS.md`;
  - use your own worktree;
  - no claim, push or PR — drafts only;
  - build under `~/.cache/olm-emu/build-F54b/` (no spaces);
  - register `~/.cache/olm-emu/worker-F54b/`.
- Do not switch OLM's default oracle. Report the equivalence table so the orchestrator can decide on the switch.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free) before Rust builds. Commit partial results at least every 30 minutes. The stop rule applies.
