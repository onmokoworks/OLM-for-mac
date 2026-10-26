# X01: AEXCompat: no Windows-only or macOS-only features. Audit every asymmetry, then close it

## Why (user request, 2026-10-26)
- The user wants AEXCompat to have no "Windows has it, Mac doesn't" features (or the reverse), in the GUI or the workers.
- Known examples:
  - `docs/WINDOWS_GUI_EFFECT_CHAIN.md`: effect chains appear to be Windows-GUI-only;
  - `analysis/MACOS_WINDOWS_GUI_PARITY_2026-07-25.md`: a parity table with some "Windows-only" rows;
  - the native minihost (Windows) has UI-event dispatch, while the Unicorn guest got it only in OLM's U03;
  - OLM's F52-F54c features (downsample/geometry, negotiated output, cropped checkout, 4K arena, numeric patches, resident watches) live in the Unicorn guest, and the native minihost may lack the equivalents.
- AEXCompat lives at `~/Documents/Projects/Personal/04_Tools/AEXCompat` (remote: GitLab). The user allows direct changes.

## Do
1. **Inventory** (write `analysis/PLATFORM_PARITY_<date>.md` in AEXCompat, plus a copy under OLM `orchestra/reports/X01-…`).
   - Go through GUI features, worker CLI options and commands, host-suite coverage (Drawbot/UI, arbitrary data, color suites…), pixel depths, geometry/ROI, trace/watch facilities, export formats, effect chains and diagnostics.
   - For each item, mark Windows and macOS: yes / no / partial, with code pointers.
   - Classify each gap:
     (a) implementable on the other platform;
     (b) inherently platform-specific — for example, the Windows dependency sealing that exists because native DLLs execute there. Say why, and what the equivalent safety or UX on the other side is;
     (c) intentionally different.
2. **Close the gaps**, one gap per commit with behavioural tests, on branch `olm/X01-platform-parity`. Use your own worktree from the latest stacked OLM branch (`olm/F54c-resident-watches` if it exists, else `olm/F54b-numeric`).
   - **macOS-side additions** (e.g. GUI effect chains on macOS, using the Unicorn guest): implement, build and test fully here.
   - **Windows-side additions** (e.g. geometry/cropped-checkout/4K options in the native minihost): implement as far as possible. Cross-compile check if feasible (`cargo check --target x86_64-pc-windows-msvc` with xwin, or the repo's own approach). Mark each one clearly as **"untested on Windows"** in the report. Do not claim it works.
   - Prefer shared, platform-independent code (like `gui_state.rs`) over duplicated per-platform logic.
3. **Report** what was closed, what remains and why, and the Windows verification needed. Draft the claim comment and PR text (no posting).

## Rules
- Follow AEXCompat `AGENTS.md` and `CLAUDE.md` technical rules. No claim, push or PR (drafts only). Never touch the main worktree or other worktrees. Build per OLM `orchestra/BRIEF.md` (space-free paths).
- The default behaviour of existing commands must not change. OLM's corpora must still replay identically with the registered workers.
- Use 1-2 processes. Commit partial results at least every 30 minutes. The stop rule applies. The inventory plus the first macOS-side gaps closed is already valuable.
