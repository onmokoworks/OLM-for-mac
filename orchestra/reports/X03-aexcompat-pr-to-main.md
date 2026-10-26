status: done
summary:
- Merged the OLM AEXCompat stack and bilingual GUI guides into GitHub main through PR #1790.
- Updated X01b guide procedures/remaining gaps, fixed stack formatting and a Windows-CI trace-encoding performance failure.
- Local release/harness/GUI-state/real-AEX checks passed; final GitHub Actions passed all 21 jobs on the reviewed head.
- Merge commit cb3bb76827b55f84dfc58cfcd06fb78553b6309b; no OLM plugin/release-gate changes or oracle replacement.

facts:
- PR: https://github.com/onmokoworks/AEXCompat/pull/1790
- Reviewed/green head: `e483fc65ebd6bb7c66932d15c3922472690309e9`.
- Merge: `cb3bb76827b55f84dfc58cfcd06fb78553b6309b`, merged 2026-10-26T02:27:59Z.
- Final CI: https://github.com/onmokoworks/AEXCompat/actions/runs/40258815367 — completed/success, 21 successful jobs, none failed.
- First CI: https://github.com/onmokoworks/AEXCompat/actions/runs/40257857610 — failed only Windows guest full-plane snapshot test. Retained job details in `X03-evidence/ci-first.json`; final details in `ci-final.json`.
- Started X01 worktree clean at `13bda6be`, branch `olm/X01-platform-parity`. `git worktree list`, AGENTS/CLAUDE, OLM guide/brief and X01/F54 reports read. GitHub issues/PRs inspected read-only; no claim comment or follow-up issue posted. Ticket explicitly authorized GitHub push/PR/merge.
- Independent review of `git diff origin/main...13bda6be` found no actionable correctness findings before integration. `git merge --no-edit olm/X02-gui-guide-ja` produced `4d8eb2be51d6282634010a4d35ed95af6003b627` without conflicts; `git show --remerge-diff` had no resolution delta. `git fetch origin` then `git merge --no-edit origin/main` reported Already up to date; main `8d102ae4` was already an ancestor.
- `16a35f3e`: update both GUI guides for chains/4K/output layout and remaining X01b gaps, format guest x64 engine/tests/trace for the all-files CI gate. Reviewer found the guide incorrectly called the final Mac chain raw artifact RGBA; following the final writer showed ARGB. Accepted and fixed in both languages as `08300c3f`; amended diff reviewed with no findings. No rejected findings.
- Japanese lint: `python3 ~/.claude/skills/yomiyasu/scripts/yomiyasu_lint.py --doc-type manual docs/GUI_GUIDE_JA.md` exit 0, 0 errors, 5 sentence-ending warnings and 1 primary-language info; reviewed and retained natural manual wording. No bold introduced. All 10 local guide links resolve.
- CI-equivalent rustfmt of all 244 tracked Rust files: initially exit 1 on three inherited stack files; after formatting exit 0. `git diff --check` passed.
- Reproduction script: `X03-evidence/checks.sh`. Rust/Cargo 1.93.1, one build job and one test thread, space-free cache target/TMPDIR. Initial memory free 53%; subsequent observed values 43–51%. First full guest Release suite: 719 library + 10 CLI + 8 math tests passed, 0 failures, 3 ignored. Guest Release build passed.
- Harness: 87 passed / 0 failed / 5 ignored, including GUI-state tests. Shared artifacts: 8 passed. Shared decoded input: 2 passed. Newly built worker / original ColorKeep chain: 5 passed. UHD admission + real 8/16/32-bpc rendering: 2 passed. Resident ARGB16 GUI export: 1 passed.
- Windows harness target `cargo check --target x86_64-pc-windows-msvc`: exit 0. macOS harness Release build: exit 0. Production native dispatcher compiled with portable coordinate test and executed: exit 0. These local checks do not constitute Windows native runtime or visual GUI QA.
- Frozen UI replay with the new pre-CI-fix worker: 17 sessions / 174 operations / 0 semantic mismatches. Ten KiraKira sessions retain differing inactive serializer tails; no full raw equality claim. Worker identities and per-session counts are in `X03-evidence/ui-summary.json`; frozen expected traces/manifests unchanged. No successful-output byte mismatch was found in the transport checks; these are not an OLM/AE arithmetic corpus replay.
- First CI Windows guest result: 709 passed / 1 failed / 3 ignored. Failure: `resident_snapshot_exceeds_old_plane_cap`, `ExecutionCrash`, RIP `0x10000000`, first instruction `RET`, while capturing a 132,710,400-byte plane. No expected bytes were changed. Default wall timeout was retained.
- Common `bytes_to_hex` used `format!` and a temporary allocation per input byte. `e483fc65` uses one reserved output allocation and ASCII digit lookup, preserving output and every limit. Added behavior test for empty input, leading zeros, lowercase sample and all 256 byte values. Independent review of the entire delta since `08300c3f` found no issues; no rejected findings.
- Same Mac debug full-plane test: passed before in 25.26 s, after in 12.08 s. Post-fix full guest Release suite: 720 library + 10 CLI + 8 math passed, 0 failures, 3 ignored. New hex test passed in debug. Release worker rebuilt successfully. Unaffected harness checks were not repeated after this trace-only fix.
- Final Windows CI guest: 711 library passed / 0 failed / 3 ignored, including full-plane snapshot; CLI 10 and math 8 passed. Standard native/probe/Python/Rust/macOS jobs all green. Machine-readable log hashes/test summaries: `X03-evidence/local-checks.json`.
- Pushed only `origin` branch `olm/platform-parity-stack`, first at `08300c3f`, then reviewed correction `e483fc65`. PR body was submitted/updated through `--body-file` with real newlines; combines F54 draft and F54b/F54c/X01/X01b material, Windows limits, rejected-findings disposition and reviewed SHA.
- Immediately before merge, GraphQL confirmed head `e483fc65`, 0 comments, 0 reviews, 0 review threads, no further pages. Retained `X03-evidence/review-gate.json`. Executed `gh pr merge 1790 --repo onmokoworks/AEXCompat --merge --delete-branch --match-head-commit e483fc65ebd6bb7c66932d15c3922472690309e9`; exit 0. `gh pr view` reports MERGED and the merge SHA above (`merge.json`). Post-merge open PR list empty; issue list inspected without expanding scope.
- Never modified the AEXCompat main checkout or other people's worktrees, OLM MAIN, plugin sources, ledger, release gate, existing registered cache entries, or GitLab. No force push, rebase, stash or issue claim. No permission rejection occurred. The first gh log-download command declined terminal escape rendering; repeated with `--allow-escape-sequences` to a scratch log; this was a display-format guard, not a permission denial.
- Disposable build tree peaked approximately 2.1 GiB and was deleted with Python shutil.rmtree after checks. Scratch logs/UI replay occupy about 13 MiB. All launched build/test processes completed; no task-owned background process remained. No new durable oracle was needed or installed. Local X01 branch remains clean and available; only remote PR branch was deleted.

inference:
- The Windows failure was consistent with per-byte hex formatting/allocation consuming the existing time bound during a large host-side capture. The lower local runtime and successful unchanged-limit Windows test support the general encoding fix; no timeout-policy change or test weakening was needed.
- Green CI establishes the repository's tested boundary, not universal AE equality or completion of the remaining platform gaps. Merging the experimental tracing functionality does not qualify F54c as the default OLM oracle.

changed_files:
- AEXCompat docs/GUI_GUIDE_JA.md, docs/GUI_GUIDE.md; README.md/README.en.md imported with X02.
- AEXCompat guest/crates/aex-guest-worker/src/x64/{engine.rs,tests_cases.rs,trace.rs}: stack formatting; final two also contain hex optimization/test.
- OLM orchestra/reports/X03-aexcompat-pr-to-main.md.
- OLM orchestra/reports/X03-evidence/{checks.sh,pr-body.md,local-checks.json,ui-summary.json,ci-first.json,ci-final.json,review-gate.json,merge.json}.

verify:
From the OLM X03 worktree, inspect merge/CI without writing either main checkout:

```sh
gh pr view 1790 --repo onmokoworks/AEXCompat --json state,mergeCommit,headRefOid
# MERGED; merge cb3bb76827b55f84dfc58cfcd06fb78553b6309b; head e483fc65ebd6bb7c66932d15c3922472690309e9
gh run view 40258815367 --repo onmokoworks/AEXCompat --json status,conclusion,headSha
# completed, success, e483fc65ebd6bb7c66932d15c3922472690309e9
AEXCOMPAT_SOURCE="$HOME/Documents/Projects/Personal/04_Tools/AEXCompat-olm-X01" \
X03_LOG_DIR="$PWD/orchestra/state/X03-aexcompat-pr-to-main/recheck" \
sh orchestra/reports/X03-evidence/checks.sh
# All PASS; current guest 720 + 10 + 8, harness 87, artifacts 8, decode 2,
# chain 5, UHD 2, resident export 1; existing ignored tests remain explicit.
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/aexcompat_patches/verify_X01b_parity.py \
  --worker "$HOME/.cache/olm-emu/build-X03/target/release/aex-guest-worker" \
  --main "$HOME/Documents/Projects/Personal/OLM as" \
  --output orchestra/state/X03-aexcompat-pr-to-main/ui-recheck
# 17 sessions, 174 operations, semantic_mismatches 0; raw inactive tails reported separately.
```

The recheck script recreates the disposable build cache. Delete that cache after verification; do not register or replace an existing oracle. Timing is machine/load dependent. The recorded pre-fix and post-fix tests are distinct evidence, not a promised runtime threshold.

next:
- Suggested follow-up tickets: native instruction/RVA/pointer-chain/full-plane watches with bounded reads and paired fixtures; paired native/guest ROI/negotiated-geometry behavior; Mac interactive custom-UI canvas/font rasterization; per-suite/version/slot audits including ACE and arbitrary streams; deep previews/additional image chooser formats/audio/timeline/shared diagnostics.
- Execute original-AEX Windows click/drag/keydown and native deep-chain/AE parity witnesses. Standard CI passed but does not establish those specific original-AEX behaviors.
- Preserve F54c's known qualification blockers: two RadialBlur wall-limit status differences and selector-entry zero-capture boundary. Full OLM corpus equivalence/default-oracle promotion remains separate work. No issues were opened or claimed by this ticket.
