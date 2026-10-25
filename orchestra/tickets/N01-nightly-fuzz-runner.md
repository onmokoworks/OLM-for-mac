# N01: one-command overnight fuzz runner (the user starts it before sleeping)

## Do
1. Write `tools/fuzz/nightly.sh`, a single command, plus `tools/fuzz/nightly_summary.py`.
   - Usage: `tools/fuzz/nightly.sh [--hours 7] [--jobs 2]`.
   - It loops over all 10 plugins and these samplers, until the deadline:
     - default;
     - `--geometry realistic`;
     - `--geometry realistic-v2`;
     - `--geometry realistic --size-sampler odd-even-v1 --max-size <the per-plugin maximum in orchestra/reports/T15b-evidence/<plugin>-summary.json>`.
   - Use fresh seeds derived from the date, round-robin, with an n per run of about 10 minutes. Use the contract route (Smart; Classic for Smoother v1).
   - Everything goes under `orchestra/state/nightly/<date>/`. Keep only reports and shrunk witnesses of mismatches or Mac-only refusals, and delete scratch, to keep disk bounded (<2 GB). Check `memory_pressure` before each run and pause while free memory is below 30%.
   - Stop cleanly at the deadline or on SIGINT. Do not leave child emulator processes behind.
   - `nightly_summary.py` prints a short table per plugin and sampler (E/M/R/U), plus the list of new witnesses with their first-difference details. It also writes `summary.md`.
2. Run a 15-minute smoke (`--hours 0.25`) and commit its summary as an example. Document the command in `tools/fuzz/README.md`.

## Rules
- Make no plugin source changes. Do not touch the release gate or ledger. The script must not use more than `--jobs` emulator processes.

## Resume note (orchestrator)
- Your previous run was killed by an orchestrator queue restart (not by anything you did). Your worktree, commits and any uncommitted files are intact. Read your own commits, report draft and `orchestra/state/<ticket>/` first, and continue from there instead of starting over.
