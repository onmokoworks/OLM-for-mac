Latest attempt: [A02f](A02f-real-ae-retest-downsample.md), checkpoint status partial.
All 132 priority items rendered; 108 raw-exact effects and 12 ColorKeep I/O differences.
16/32 bpc and corpus work continues. Historical attempt below.

status: blocked
summary: AE 2026 launched once but remained at the crash-recovery startup dialog.
  Screen unlocked and System Events UI scripting enabled; AE exposed no accessible windows/buttons.
  No dialog clicked, frame rendered, or original/native comparison performed.
  Ticket-local numpy/tifffile/OpenEXR environment enabled all 12 offline tests to pass.

facts:
- Initial HEAD `cfe71fb3`; clean worktree and empty A02d scratch. Read AGENT_GUIDE, prior A01c/A02b/A02c reports, smoke README, emulator GOTCHAS, compatibility plan and ledger decision rows. No plugin source, installed bundle, MAIN, emulator, release gate or ledger modification.
- Before launch: on-console logged-in session with absent lock key (unlocked), `UI elements enabled=true`, no `MacOS/After Effects$` or aerender process, memory 48% free. Runner repeated memory/lock/busy preflight; retained memory and lock logs are in A02d-evidence.
- Created ticket-local venv with numpy/tifffile/OpenEXR; pip TMPDIR was ticket scratch. Exact build command below. Single full-path AE 2026 dispatch, owned PID 48247. Screenshot shows Japanese crash-recovery options and visible `続行` button. No JSX build marker or project was produced.
- Read-only System Events first path-filter query failed -1700 (AppleScript specifier error); corrected query and PID-scoped queries verified `/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app`. That process reported zero windows, zero UI elements, empty entire contents and missing AX role. Setting only that verified process frontmost succeeded but did not expose its buttons. No -1712/-1719/-25211 occurred. UI scripting remained true. No claim that additional permissions are definitely required.
- Dialog clicks: **0**. No dialogs.jsonl click entry is appropriate because nothing was pressed. No global keystroke, coordinate click, destructive recovery option, app-name/bundle-ID dispatch, or retry launch was used.
- Ten installed executable SHA-256 hashes: [installed.json](A02d-evidence/installed.json). Hashing files does not prove loaded-module identity. Screenshot and process/query logs retained under A02d-evidence.
- Offline tests: pipeline **6/6**, downsample attribution **2/2**, comparator **4/4**, all pass. This fixes the prior environment dependency gap, not an AE rendering result.
- Builder exited **1** at its 180-second deadline, captured a 275,317-byte cropped screenshot, and sent one full-path normal quit event. Quit returned **-1708**; subsequent exact-main process check found no AE or aerender. No SIGTERM/SIGKILL or second quit was sent. See [build log](A02d-evidence/build-run.log), [quit log](A02d-evidence/quit.log), [screenshot](A02d-evidence/blocked.png), [final processes](A02d-evidence/final-processes.json).
- Rendered controls/effects **0/0**; original/native comparisons **0**. Refusal tags, actual InData/downsample geometry, mismatch counts and first mismatch unavailable. No measured black plugin output or plugin bug. No numerical hypotheses refuted; stopped at GUI startup boundary.

NT = not tested, across all requested sizes/defaults/corpus cases. No OK or exact-vs-original claim.

| Plugin | Full 8/16/32 | Half 8/16/32 | Third 8/16/32 | Quarter 8/16/32 |
| --- | --- | --- | --- | --- |
| OLMBlur | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| ColorKeep | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMColorKey | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMDirectionalBlur | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMDistanceGradation | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMKiraKira | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMSmoother2 | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMToonDilate | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMRadialBlur | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMSmoother | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |

| Timing scope | 1080p seconds/frame | 4K seconds/frame |
| --- | --- | --- |
| All ten plugins, Full/Half/Third/Quarter | unavailable | unavailable |

inference:
- The visible crash-recovery dialog plausibly blocks script startup. System Events UI scripting enabled does not ensure this early AE dialog exposes accessible controls. The reason for the empty AX tree is unconfirmed; this is not evidence of a plugin rendering defect or permission denial.
- The checked-in A01c report does not establish the claimed exact I/O calibration. A subsequent successful run must measure controls before classifying effect differences.

changed_files:
- `orchestra/reports/A02d-real-ae-retest-downsample.md`, `orchestra/reports/A02-real-ae-retest-downsample.md`, `orchestra/reports/A02d-evidence/` only. No harness or plugin code changes.

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02d-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02d-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_downsample.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
git diff --check
```
Expected: 6 + 2 + 4 tests pass, whitespace check passes. If scratch has been removed, recreate a ticket-local venv with numpy/tifffile/OpenEXR. These commands do not launch AE.

Actual attempted build (do not repeat against this used run ID):
```sh
TMPDIR="$PWD/orchestra/state/A02d-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02d-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-priority --stage build --run-id priority --scratch orchestra/state/A02d-real-ae-retest-downsample > orchestra/state/A02d-real-ae-retest-downsample/build-run.log 2>&1
```

next:
- Follow-up startup ticket: resolve the visible crash-recovery dialog with no accessible AE controls. A fresh run requires a new run ID and all unlocked/busy/memory checks. Do not retry blindly or force-kill AE.
- Then run priority defaults, calibrate I/O and actual geometry, compare original F53/same-installed-bundle, complete depths and two exact corpus cases per plugin. Preserve untouched DistanceGradation 32 bpc defaults. Corpus/oracle integration remains unimplemented.
- No black-frame/plugin-fix ticket is justified without rendered evidence.

cleanup:
- Scratch is approximately 140 MiB, below 5 GiB; no build trees generated. Local venv and deterministic inputs retained for follow-up, with reproducible launch/input metadata and logs committed. No owned background process remains. No push, stash, or history rewrite.
