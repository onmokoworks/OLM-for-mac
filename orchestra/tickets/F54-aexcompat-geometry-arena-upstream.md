# F54: AEXCompat itself: upstream the OLM geometry patches, and allow 4K / PF32 full HD

## Why
- The user wants AEXCompat (their emulator, `~/Documents/Projects/Personal/04_Tools/AEXCompat`) to become more complete, and **allowed direct changes to it** (2026-10-25).
- OLM's emulator capabilities currently live only as patch files on source copies: F52 downsample/geometry, F52c negotiated output, F53 cropped checkout, plus F29-F46 fixes (`tools/emulation/aexcompat_patches/`, `~/.cache/olm-emu/src-F5*`).
- The guest refuses dimensions beyond 1920x1080, and PF32 full HD exhausts its data arena (T15b calibration). So OLM cannot compare against the original at 4K.

## Read first
- `AEXCompat/AGENTS.md` and `CLAUDE.md`. Follow their technical rules: one issue per branch, focused tests, Release build + self-test, a local review loop before any PR, behavioural tests and not string-matching tests.
- **Exceptions for this ticket:** do NOT post claim comments, push, or open PRs. Those are outward-facing and need the user's OK. Instead, write the claim text and the PR body as files in the report.
- Do not touch AEXCompat's main worktree (currently on `codex/gitlab-ci` with an untracked zip) or other existing worktrees. Create your own:
  `git -C ~/Documents/Projects/Personal/04_Tools/AEXCompat worktree add ~/Documents/Projects/Personal/04_Tools/AEXCompat-olm-F54 -b olm/F54-geometry-arena origin/main`
  (`git fetch` first is fine).

## Do
1. **Inventory.** List every OLM patch (F29-F53) with what it changes, and whether origin/main already has an equivalent. For F52, F52c and F53, the base was `bd878da6`; origin/main is 113+ commits ahead.
2. **Upstream** the geometry features into AEXCompat proper, as clean, tested changes on top of origin/main:
   - downsample;
   - rowbytes padding;
   - extent_hint and request rect;
   - pixel aspect;
   - negotiated output;
   - cropped checkout.
   Option names and the CLI can follow AEXCompat conventions. Give OLM's fuzz adapters a compatibility mapping, or note the needed adapter change.
3. **Size limits.** Raise the dimension cap and the data arena so that 3840x2160 at PF8/16/32 Smart works for at least OLMBlur, ColorKey and DirectionalBlur. Measure time and memory per case. Keep a 16 GB machine in mind: the arena must be sized per request, not a fixed huge reservation.
4. **Equivalence.** The upstreamed worker must reproduce the F53 worker's outputs byte-for-byte on OLM's corpora (replay at least 2 plugins' full corpora plus F53's survey witnesses). Default options must leave existing AEXCompat tests and outputs unchanged.
5. Build to `~/.cache/olm-emu/worker-F54/` and add an INDEX entry. **Do not** change OLM's default fuzz worker; that switch is a separate decision.
6. **Report** `orchestra/reports/F54-aexcompat-geometry-arena-upstream.md` with:
   - the inventory table;
   - tests run;
   - 4K timings;
   - the AEXCompat branch name and HEAD SHA;
   - the draft claim comment and PR body for the user.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free) before Rust builds, and delete build trees afterwards.
- Make no OLM plugin source changes. Do not touch the release gate or ledger.
- Commit partial results at least every 30 minutes (in both repos as relevant). The stop rule applies. Upstreaming downsample + cropped checkout with equivalence proof is already a success.
