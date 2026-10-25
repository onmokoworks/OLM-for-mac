status: blocked
summary: Accessibility preflight returned false; no AE launch or render attempted.
  Fixed absent-lock-key handling for logged-in console sessions; live session is unlocked.
  Six pipeline tests and four comparator tests pass.
  Downsample tests could not import tifffile in the existing MAIN Python environment.
  Full render/corpus/oracle matrix remains unexecuted.

facts:
- Resumed branch `orch/A02c-real-ae-retest-downsample`, initial HEAD `35d61dc9`, clean tree and empty ticket scratch. Read prior A01c/A02/A02b reports and scaffold. The checked-in A01c report does not establish the exact I/O roundtrip claimed in the brief; no calibration assumed.
- `ioreg -n Root -d1` showed `kCGSSessionOnConsoleKey=Yes`, `kCGSessionLoginDoneKey=Yes`, and no lock key. Corrected `screen_locked()` returns false. [Preflight](A02c-evidence/preflight.json) records UTC and no AE main PIDs. Initial `memory_pressure` reported 42% free; subsequent full output retained in [memory.txt](A02c-evidence/memory.txt).
- One read-only `osascript` preflight used `with timeout of 15 seconds` and `tell application "System Events" to get UI elements enabled`. Exit **0**, output **false**, no timeout or permission error code. Exact script/result: [accessibility-preflight.log](A02c-evidence/accessibility-preflight.log). No retry, UI click, screenshot, quit event or AE dispatch was made. No dialog title or requesting-app name was returned. Query launcher was `/usr/bin/osascript` via the Codex execution tool; macOS TCC attribution to a parent application was not observed.
- Ten installed executable SHA-256 values retained in [installed.json](A02c-evidence/installed.json); not loaded-module proof. Installed bundles, MAIN, plugin code, emulator, ledger and release gate were unchanged.
- `PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/ae_smoke/test_pipeline.py`: **6 tests pass** ([log](A02c-evidence/pipeline.log)), including absent key, missing login, explicit false/invalid values, multiple entries, locked session and preserved deadline.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py`: **4 tests pass** ([log](A02c-evidence/compare.log)).
- `PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/ae_smoke/test_downsample.py`: exit **1**, `ModuleNotFoundError: No module named 'tifffile'` ([log](A02c-evidence/downsample.log)); no tests executed. Did not modify MAIN's environment.
- AE launches **0**, rendered frames **0**, original/native comparisons **0**. Refusal tags, first mismatch, AE downsample/InData geometry and frame times unavailable, not zero. No black plugin frame or plugin bug observed. No two numerical hypotheses were tested/refuted; stop is the accessibility precondition.

All sizes/corpus cases remain untested (NT). Resolution columns apply to Full/Half/Third/Quarter respectively. No OK or exact-vs-original claim.

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
| All ten plugins, all resolutions | unavailable | unavailable |

inference:
- Blocker: **needs Accessibility permission** for the osascript/System Events automation execution context. `UI elements enabled=false` is evidence that UI scripting is disabled; it does not identify the responsible application in System Settings or prove Automation denial. The previously reported -1712 did not recur.
- Because automatic startup-dialog handling cannot be relied on with UI scripting disabled, stopped before launching AE. This is a conservative preflight decision, not an AE render failure or an automatic tool approval rejection.
- No I/O, color-management, host-geometry or plugin-bug classification is possible without frames.

changed_files:
- `tools/ae_smoke/run_ae_smoke.py`: absent lock key is unlocked only with logged-in console evidence; true is locked; other states fail closed.
- `tools/ae_smoke/test_pipeline.py`: console/lock regression coverage.
- `tools/ae_smoke/README.md`: corrected lock semantics.
- `orchestra/reports/A02c-real-ae-retest-downsample.md`, `A02-real-ae-retest-downsample.md`, `A02c-evidence/`.

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
git diff --check
```
Expected: 6 and 4 tests pass; whitespace check passes. These checks launch no AE and establish no pixel exactness. Downsample tests need a ticket-local environment containing numpy, tifffile and OpenEXR before rerun; they were not validated here.

next:
- Enable Accessibility for the application macOS identifies as requesting osascript/System Events UI control; the current response did not name that app. If a future query times out, stop per the orchestration rule and report the observed requester. Do not infer the required Settings entry from this report.
- Once UI access works, run the existing priority build/render from this ticket's fresh scratch with AE 2026 full path, unlocked/busy/memory preflights, bounded dialog evidence and single-launch rules. Then calibrate I/O, capture real geometry, compare F53 original/same-installed-bundle, complete depth and two-corpus-case mappings. Preserve untouched DistanceGradation 32 bpc defaults.
- No plugin fix ticket proposed without a measured black frame or bug.

cleanup:
- No background worker, AE or aerender started; no build trees created. Scratch contains only a small test log, below 5 GiB. No push, stash or history rewrite.
