status: done
summary:
- Added Japanese primary GUI guide and matching English translation in an isolated AEXCompat worktree stacked on X01.
- Covered startup, selection, controls/reset/live render, viewers, depth, chains, export, diagnostics and errors.
- Recorded actual X01 Windows/Mac differences; did not claim X01b parity or Windows runtime verification.
- Linked both guides from both READMEs; existing screenshot unchanged.
- Committed AEXCompat documentation as `4cb4d31cd5266f68d3c6ffa609178302751ce54f`.

facts:
- AEXCompat worktree: `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-X02`; branch: `olm/X02-gui-guide-ja`.
- Base: `olm/X01-platform-parity`, `97b596d19ea37bf3c7a9b1bc5468ada6fc87e89b`. `git merge-base HEAD olm/X01-platform-parity` returned that SHA before commit.
- Read OLM AGENT_GUIDE and X01 ticket/report, AEXCompat AGENTS/CLAUDE, X01 inventory, GUI source, export implementation and existing chain documentation. No plugin kernel was in scope.
- `git fetch gitlab`, `gh issue list --state open --limit 5 --json number,title`, and `gh pr list --state open --limit 5 --json number,title` completed; outputs retained in ticket scratch. These were context reads, not claims or posts.
- `python3 /Users/onmk/.claude/skills/yomiyasu/scripts/yomiyasu_lint.py --doc-type manual docs/GUI_GUIDE_JA.md` completed with exit 0. Initial: 0 errors, 9 warnings, 6 info. Final: 0 errors, 7 warnings, 0 info. Removed unnecessary commas, changed software 版 to バージョン, and simplified a negative comparison sentence in both languages.
- Retained final lint warnings deliberately: one bold-frequency warning (UI labels and ARGB distinction), one 正本 warning (literal primary-text designation), five repeated ます warnings (consistent procedural/explanatory Japanese). Lint counts are not a readability score. Only the requested lint was run; no claim of completing the full yomiyasu rewrite/check workflow.
- Inline local-link check: 10 guide links checked, 0 broken; each README contains 2 guide links.
- `git diff --cached --check`: exit 0. Committed scope: 4 documentation files, 288 insertions; each guide is 142 lines.
- `git diff --exit-code 97b596d1 -- docs/images/aexcompat-gui.png`: exit 0. No screenshot created or replaced.
- Independent review required by AEXCompat AGENTS found two documentation errors: missing CMake in Mac build prerequisites and Windows header Reset incorrectly named Reset All. Both were accepted and fixed in both languages. Complete re-review returned no findings; no rejected or unaddressed findings. Reviewed commit boundary: `4cb4d31cd5266f68d3c6ffa609178302751ce54f`.
- Review ran sequentially while this worker launched no other process. No build, GUI runtime, Windows runtime, emulator, AE comparison or numerical conformance test was run for this docs-only change. First pixel mismatch: not applicable.
- SHA-256 Japanese guide: `1fffea799f90a527bf82bad035bbab33cb43752a2c1c6fde9d2fc0dcab6045ab`.
- SHA-256 English guide: `ec1a844019ef98d23ae8f79840175e13b50c3e17b300acfd2c64e954da5e34b5`.
- SHA-256 unchanged image: `c1f14b1e12dd6f0ab0ca269cfd55243852ea0edfbe1f7e54421afc510d4dae6e`.
- No push, claim, PR, MAIN edit, worker build, cache registration, release gate or ledger change. No background process or regenerable build tree was started. Logs only under this ticket's ignored scratch; no `/tmp` writes were requested.

inference:
- Source evidence supports a unified guide with explicit capability limits, rather than instructions implying full GUI parity. In particular, Mac deep artifacts cannot be described as Windows chain PNG/raw exports: the channel order and formats differ.
- Source-reviewed instructions are appropriate for this documentation ticket; OS runtime usability and pixel equality still need their own evidence.

changed_files:
- AEXCompat `docs/GUI_GUIDE_JA.md` (new primary guide).
- AEXCompat `docs/GUI_GUIDE.md` (new translation).
- AEXCompat `README.md` and `README.en.md` (guide links only).
- OLM `orchestra/reports/X02-aexcompat-gui-guide-ja.md` (this report).

verify:
Run the following from the AEXCompat X02 worktree. No builds are needed.

```sh
cd "$HOME/Documents/Projects/Personal/04_Tools/AEXCompat-olm-X02"
git diff --check 97b596d1 HEAD
# Expected: exit 0, no output.
git diff --stat 97b596d1 HEAD
# Expected: 4 files changed, 288 insertions; README files and two guides only.
git diff --exit-code 97b596d1 HEAD -- docs/images/aexcompat-gui.png
# Expected: exit 0, no output (existing image unchanged).
python3 "$HOME/.claude/skills/yomiyasu/scripts/yomiyasu_lint.py" --doc-type manual docs/GUI_GUIDE_JA.md
# Expected with the current local lint: exit 0; error 0, warn 7, info 0.
shasum -a 256 docs/GUI_GUIDE_JA.md docs/GUI_GUIDE.md docs/images/aexcompat-gui.png
# Expected: the three hashes above.
python3 - <<'PY'
import re
from pathlib import Path
count = 0
for name in ['docs/GUI_GUIDE_JA.md', 'docs/GUI_GUIDE.md']:
    p = Path(name)
    for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
        q = p.parent / target.split('#')[0]
        if not q.exists():
            raise SystemExit(f'BROKEN {p}: {target}')
        count += 1
print(f'Guide local links: {count} checked, 0 broken')
for name in ['README.md', 'README.en.md']:
    print(name, 'guide links:', len(re.findall(
        r'\]\(docs/GUI_GUIDE(?:_JA)?\.md\)', Path(name).read_text())))
PY
# Expected: 10 guide links, 0 broken; 2 guide links in each README.
```

next:
- Orchestrator: review AEXCompat `olm/X02-gui-guide-ja` stacked on the X01 commit, and merge through the assigned workflow. Nothing was pushed.
- After X01b, revise the short differences section and affected procedures in both languages together; do not remove limits until corresponding behavior is verified.

Draft claim (not posted):
X02: document the GUI at X01 commit 97b596d1 in primary Japanese and English translation. Scope is two guides and README links. Acceptance is source-checked UI/export instructions, explicit OS gaps, Japanese manual lint, valid local links and independent review. Depends on X01; X01b will update remaining differences.

Draft PR (not posted):
Title: Add Japanese GUI guide and English translation
Base: `olm/X01-platform-parity`
Head: `olm/X02-gui-guide-ja`

Users need one GUI guide for Windows and Mac, including concrete limitations in the current X01 implementation. Add a Japanese primary guide and matching English translation, and link both from both READMEs. Cover startup through export and troubleshooting, including Windows chains versus Mac single-effect rendering and RGBA versus ARGB raw output.

Validation: Japanese lint completed (0 errors, 7 intentional warnings, 0 info); 10 guide links valid; both READMEs link both guides; diff whitespace check passed; existing screenshot unchanged. No runtime or parity claim. Independent review fixes were applied and the full change re-reviewed clean. Reviewed boundary: `4cb4d31cd5266f68d3c6ffa609178302751ce54f`. No rejected findings. No issue number invented, no claim or PR posted.
