# A02c: real AE 2026 retest of the fixed bundles: preview resolutions, odd sizes, 32 bpc, timing (aerender)

## Why
- Real AE showed **black** for OLM Blur and ColorKey (and others) at preview resolution 1/2 and 1/4, because plugin refusals return `PF_Err_BAD_CALLBACK_PARAM`.
- P01-P04 fixed that in the emulator: every case the original renders is now exact, including downsample, odd sizes, ROI, PF32 and DistanceGradation's 32 bpc defaults.
- This ticket checks the same things in **real After Effects 2026**. The user is busy, so this replaces their manual retest.

## State (facts)
- The installed bundles are the HEAD 62f97f6c Universal builds in `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/`. Do not replace them. The same builds sit in `~/.cache/olm-emu/AEretest3/xcode/<Plugin>/products/`.
- Read `orchestra/reports/A01c-real-ae-render-aerender.md` and `tools/ae_smoke/README.md`.
  - A01c built `run_ae_smoke.py --year 2026 --stage build|render|compare|all`. It uses one GUI JSX build step (comps, render queue, save `.aep`, `app.quit()`) and then **aerender**.
  - A01c made the no-effect I/O round trip exact.
- `OLM_REFUSAL_TRACE=<file>` set in the environment of the AE or aerender process makes 8 of the plugins (all but the two Smoothers) log refusal tags.

## Resume note (A02 first attempt)
- A02 timed out because **the Mac screen was locked**. AE's GUI cannot start a JSX while the session is locked, and the "black" capture was the lock screen. Its downsample-priority matrix scaffold and per-frame logging are merged (`tools/ae_smoke/`, `--matrix downsample-priority`); see `orchestra/reports/A02-real-ae-retest-downsample.md`.
- **Precondition before any AE launch:** the screen must be unlocked. Check it with
  `ioreg -n Root -d1 -a | plutil -extract IOConsoleUsers.0.CGSSessionScreenIsLocked raw - 2>/dev/null`
  (or grep `CGSSessionScreenIsLocked` in `ioreg -n Root -d1`). While it is locked, wait: poll every 5 minutes, up to 12 hours, and never launch AE meanwhile. If it is still locked after 12 hours, stop with status blocked.
- After AE quits, also check that it really quit: no `MacOS/After Effects$` process.

## Do
1. **Matrix.** Extend the A01c build/render stages, opt-in and keeping the old matrix reproducible:
   - render-queue **Resolution**: Full, Half, Third and Quarter (this is how `in_data->downsample` reaches the plugin in a render);
   - comp sizes 1920x1080 and **1279x719** (odd), plus 3840x2160 for the 8 bpc defaults;
   - 8/16/32 bpc;
   - for each of the 10 plugins, the default params plus 2 exact corpus cases (`tests/fuzz_corpus/<plugin>/`). Include DistanceGradation with **untouched defaults at 32 bpc** (P04a).
   - Priority: 8 bpc defaults at all 4 resolutions for all 10 plugins first.
2. **Render** with aerender, with `OLM_REFUSAL_TRACE` set. For every frame, record:
   - render success or error;
   - any refusal tag;
   - whether the output is all black or transparent where the input is not;
   - seconds per frame, taken from aerender's log or wall time.
3. **Compare.**
   - **(a) Against the original.** For frames at or below 1920x1080, run the original AEX on the F53 oracle (`~/.cache/olm-emu/worker-F53-geom/`) with the same input pixels, params and **the same downsample**. Read the downsample from the AE render, and read the in_data geometry from a scratch trace if needed. Compare with AE's output using `tools/ae_smoke/compare.py`.
   - **(b) Fallback.** Where the oracle cannot run, compare against the F47/F53 bundle host with the same bundle.
   - Classify each difference: I/O conversion, color management, host geometry (report the AE value), or plugin bug. Give a minimal repro for each plugin bug.
4. **Report** `orchestra/reports/A02-real-ae-retest-downsample.md` with:
   - a per-plugin table of resolution × depth → OK / black / error / exact-vs-original;
   - a timing table at 1080p and 4K.
   For every black frame or plugin bug, propose a fix ticket in `next`.

## Rules (from A01/A01b/A01c; strict)
- **Never SIGKILL or SIGTERM After Effects.** The GUI is used once per run: one JSX does everything and ends with `app.quit()`.
  - If the done marker has not appeared within 3 minutes, take a `screencapture` (cropped, at most 400 KB), try `osascript` quit **once** using the full app path, then stop and report. Do not retry in a loop.
- Address AE only by its full path: `"/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app"`. Never use the app name or bundle id, because AE 2025 shares the bundle id. Use one dispatch per launch.
- **Busy check:** match the main executable only (`MacOS/After Effects$`). If an AE you did not start is running, the user is working: wait (poll every 5 minutes, up to 2 hours) and never touch it.
- Run at most one AE or aerender at a time. Check `memory_pressure` (≥30% free).
- Use AE 2026 only. Make no plugin source changes. Do not touch the release gate or ledger. Do not change or remove the installed bundles.
- Keep PNG/EXR evidence small (crop or downscale; at most 400 KB per file).
- Commit partial results at least every 30 minutes. The stop rule applies. "8 bpc defaults at 4 resolutions for all 10, with no black frames" is already a valuable result.

## Resume note (orchestrator)
- Your previous run was killed by an orchestrator queue restart (not by anything you did). Your worktree, commits and any uncommitted files are intact. Read your own commits, report draft and `orchestra/state/<ticket>/` first, and continue from there instead of starting over.

## Dialog handling update (user request, 2026-10-25; replaces "screenshot and stop" for known AE alerts)
- You may **dismiss AE alert dialogs automatically** with `osascript` + System Events, scoped to the AE 2026 process only. Address the process by its full app path or bundle path, and never touch other apps' windows.
- **Allowlisted buttons only:** `OK`, `続行`, `Continue`, `閉じる`, `Close`, `後で`, `Later`, `スキップ`, `Skip`, `今はしない`, `Not Now`. Use them only on startup and alert dialogs: crash recovery, missing or duplicate plugin warnings, preview-control warnings, the home screen, update or what's-new prompts.
- **Never click** anything destructive or irreversible: `削除` / `Delete`, `保存しない` / `Don't Save`, `置き換え` / `Replace`, `リセット` / `Reset`, `アンインストール`, purchase/sign-out buttons. Do not type credentials.
- Before each click, take a `screencapture` crop (≤400 KB) and log the dialog title, its text and the button you pressed to `orchestra/reports/A02b-evidence/dialogs.jsonl`. Allow at most 10 clicks per AE launch. For an unknown dialog, or one with none of the allowlisted buttons, take a screenshot and stop, as before.
- System Events needs macOS Accessibility permission. If osascript reports it is not allowed (error -1719 / -25211), stop and report `blocked: needs Accessibility permission for <process>`. The user will grant it.
- The still-valid rules: never SIGKILL/SIGTERM AE; the screen must be unlocked before any launch; use one AE instance only.

## Resume note 2 (orchestrator, A02c)
- **Lock detection fix:** macOS only includes `CGSSessionScreenIsLocked` in `IOConsoleUsers` while the screen is locked. When `kCGSSessionOnConsoleKey=Yes` and `kCGSessionLoginDoneKey=Yes` are present and `CGSSessionScreenIsLocked` is **absent**, the session is **unlocked**. Treat absent as unlocked, true as locked, and anything else as unknown. Fix `wait_unlocked` accordingly.
- A02b's System Events queries timed out (-1712). The likely cause is a pending macOS permission prompt (Automation or Accessibility) waiting for the user. If it happens again, stop and report `blocked: needs Automation/Accessibility permission`, naming the app that asked. Do not retry in a loop.
- Continue from A02b's merged scaffold (`tools/ae_smoke/`, `orchestra/reports/A02b-*`).
