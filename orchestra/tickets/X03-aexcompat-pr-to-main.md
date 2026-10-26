# X03: AEXCompat: open the PR for the OLM stack and merge it into main (owner-approved)

## Authorization (user, 2026-10-26)
- The user owns AEXCompat and said: put the work into main, via a PR to be safe. For this ticket **you may push branches to GitHub (`origin`), open the PR, and merge it** once the conditions below hold. Do not post issue claim comments. Do not push to GitLab.

## State
- Branch `olm/X01-platform-parity` (worktree `~/Documents/Projects/Personal/04_Tools/AEXCompat-olm-X01`, head `13bda6be`) contains the whole OLM stack:
  - F54: geometry/UHD;
  - F54b: numeric patches;
  - F54c: resident watches;
  - U03: UI sessions;
  - X01/X01b: parity.
- The Japanese GUI guide lives on `olm/X02-gui-guide-ja` (base `97b596d1`; docs only, plus README links; last commit `f48e785f` removed bold).

## Do
1. **Prepare.** In the X01 worktree:
   - merge `olm/X02-gui-guide-ja`;
   - update the guide's "remaining Windows/macOS differences" section (ja and en) to the X01b state, using `analysis/PLATFORM_PARITY_*` and the X01b report in OLM `orchestra/reports/`;
   - keep the docs style: plain Japanese, no bold, no AI-ish phrasing; lint with `~/.claude/skills/yomiyasu/scripts/yomiyasu_lint.py --doc-type manual`.
2. **Sync with main.** `git fetch origin`, then merge `origin/main` into the branch (merge, not rebase). Resolve conflicts carefully. Follow the AGENTS.md conflict-review guidance.
3. **Local checks.** Build per OLM `orchestra/BRIEF.md` (space-free build paths). Run the guest release tests, the harness tests and the GUI-state tests that the stack's reports used. All must pass. Then run AGENTS.md's local review loop: a review pass over `git diff origin/main...HEAD`, fix accepted findings, repeat until none remain. Record the reviewed HEAD SHA.
4. **Push and PR.** Push to `origin` as branch `olm/platform-parity-stack`, then `gh pr create --base main`. The PR body, with real newlines:
   - a summary of each part;
   - tests run;
   - what is untested on Windows;
   - rejected review findings with reasons;
   - the reviewed-boundary SHA;
   - the drafts already written in `orchestra/reports/F54*-evidence/pr-draft.md` and X01's. Merge them into one body.
5. **CI and merge.** Wait for GitHub Actions on the latest head. If CI fails, fix the root cause minimally (with the review loop), push, and wait again. Do not treat external outages (billing, runner) as green; report them as blocked. When CI is green on the latest head, and there are no unresolved review threads or owner comments, merge with `gh pr merge <PR> --merge --delete-branch --match-head-commit <green SHA>`.
6. **Report** the PR URL, merge commit SHA, CI run links, and anything left open (the remaining parity gaps from X01b, which become follow-up issues/tickets).

## Rules
- Never touch the AEXCompat main worktree (on `codex/gitlab-ci`, with an untracked zip) or other people's worktrees. Never force-push main. Do not change OLM plugin sources.
- Use 1-2 processes. Check `memory_pressure` before Rust builds. The stop rule applies. If CI cannot go green within reasonable effort, stop with the PR open and report.
