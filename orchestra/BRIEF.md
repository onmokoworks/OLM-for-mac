# Worker brief (read first, obey strictly)

You are a worker on the OLM Mac port: Windows AE `.aex` plugins re-implemented on
macOS with **bit-exact output** as the bar. An orchestrator assigns you ONE ticket,
reviews your diff, and merges it. Stay inside the ticket.

## Where things are
- You run inside a git worktree on branch `orch/<ticket-id>`. Commit there only.
- MAIN checkout (read-only for you): `/Users/onmk/Documents/Projects/Personal/OLM as`.
  Untracked assets (original AEX binaries under `refs/`, Python venvs
  `tools/emulation/.venv`, `.venv-cv455`) live only in MAIN — use them by absolute
  path, never copy them.
- Emulator source: `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat*`
  (read-only). Prebuilt reference workers: `/Users/onmk/.cache/olm-emu/INDEX.json` (use these
  by absolute path; do not rebuild unless your ticket says so).
- Shared contract: `AGENT_GUIDE.md`. Per-plugin forbidden actions:
  `notes/CONFORMANCE_LEDGER.md` (grep the plugin section; do not read the whole file).
- Plan and goal: `docs/COMPATIBILITY_ANALYSIS_PLAN_JA.md`.
- Ground truth = the original AEX run in the Unicorn emulator (`tools/emulation/`,
  read `tools/emulation/GOTCHAS.md`), then static `decomp/` / `disasm/`.

## Hard rules
1. Never write to `/tmp`. Scratch goes to `<worktree>/orchestra/state/<ticket-id>/`
   (gitignored). Anything needed to reproduce a result must be committed.
2. Disk: keep your scratch under 5 GiB. Delete regenerable build outputs when done.
3. Fix causes in general code. No per-coordinate / per-case expected-value patches,
   no tolerance, no PNG look-matching, no "final byte" tweaks.
4. Fact vs inference: label them. Never invent numbers. A mismatch is data.
5. Do not touch the release gate files, the ledger's forbidden-action lists, or
   other plugins' code unless the ticket says so.
6. Do not push. Do not modify MAIN. Do not rewrite git history.
7. Long commands: run them with output redirected to a log in your scratch dir and
   read only the tail / a summary. Do not dump huge JSON into your context.
8. Stop condition: if two distinct hypotheses are refuted without a new boundary
   value, STOP and report `status: blocked` with what you tried. Do not loop.

## Deliverable (required, even when blocked)
Write `orchestra/reports/<ticket-id>.md` in your worktree and commit it, with:

```
status: done | blocked | partial
summary: <=5 lines
facts: commands run + their real results (counts, hashes, first mismatch)
inference: your interpretation, labeled
changed_files: list
verify: exact command(s) the orchestrator should run to re-check, with expected result
next: what remains / suggested follow-up ticket
```

If any tool call is rejected (permissions) or you must stop for any reason, still
write and commit the report with `status: blocked` before ending. Never end silently.
