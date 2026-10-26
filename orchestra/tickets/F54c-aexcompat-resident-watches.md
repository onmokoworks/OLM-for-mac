# F54c: AEXCompat upstream: C53b-style configurable resident watches (pointer dereference, large planes) that work with geometry / cropped checkout

## Why
- N03 RadialBlur (`orchestra/reports/N03-radialblur-v2-mismatch.md`) found the first divergence already in the pre-B150 polar plane. It could not trace further back, because F54b's watches (F49 style: `AEXCOMPAT_SMART_TRACE_WATCH=rva,bytes,first|all`) cannot dereference pointers and are capped at 1 MiB.
- C53b's resident watches (`AEXCOMPAT_RESIDENT_TRACE/WATCHES`, see `tools/emulation/aexcompat_patches/` and the C53b/R06 reports) can do both, but they live in a separate worker that rejects geometry arguments.

## Do
- On a new stacked AEXCompat branch `olm/F54c-resident-watches` (own worktree, from F54b's branch), port the C53b resident watch facility into the upstream worker:
  - watches at an RVA with an optional pointer-chain dereference (register- or stack-relative bases as C53b had);
  - per-watch byte limits up to the full plane size;
  - first/all hits;
  - JSON plus raw dumps.
  It must work together with the geometry, cropped-checkout and 4K options.
- Behavioural tests: reproduce C53b's retained RadialBlur stage captures (R06 recipe) byte-for-byte on the non-geometry cases, and show a cropped-geometry capture works.
- Same AEXCompat rules as F54/F54b: follow AGENTS.md; no claim, push or PR (drafts only); build per BRIEF.md (space-free paths); register `~/.cache/olm-emu/worker-F54c/`.
- Equivalence: worker-F54c must still equal F53 on all OLM corpora with tracing off. Reuse F54b's full-corpus driver.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Make no OLM plugin changes. The stop rule applies.
