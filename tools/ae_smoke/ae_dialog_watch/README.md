# AE 2026 dialog watcher (A03; live validation blocked)

`run_ae_smoke.py --stage build` compiles this Swift helper into the run's
`dialogs/` directory, waits for its permission/readiness handshake, and only
then launches the full-path AE 2026 executable. Python supplies **only its own
Popen PID**. The watcher never discovers/adopts an existing AE instance.
It stops cooperatively after the build lifecycle; it sends no process signals.
The runner retains busy/lock/memory checks and the 180-second JSX deadline.

**Not yet validated for unattended production use.** The first real run produced
no JSX marker. The initial watcher exited prematurely during app registration;
its executable-path liveness check and Python fail-closed check were subsequently
fixed and tested offline, not re-tested against AE. No live AX/OCR click or clean
second launch was established. See `orchestra/reports/A03-ae-dialog-watcher.md`.

## Prevention investigation

Before inspection, A03 backed up the `26.*` preference directories, adjacent
versioned plists and AE 2026 logs. The on-disk 26.3 plist had Boolean
`CrashOccurred=true` and `ForceQuitOccured=true`; no deterministic causal switch
was established. A read-only probe during the launch saw AE's main project
window, despite these pre-launch disk values. This does not prove there was no
earlier recovery dialog. The 26.3 text preferences did not reveal a confirmed
home-screen suppression setting. Auto-saves and projects were not changed.

Consequently `prepare_launch` is intentionally **observation-only**: it exports
and backs up the effective versioned CFPreferences domain before reading the two
candidate flags, and records `changes: []`. It does not edit preferences, move
projects, reset settings, or clear recovery/autosave folders. The safe deterministic
prevention switch remains unknown; the fallback is dialog detection.
Backups made by this function persist under
`~/.cache/olm-emu/ae-dialog-watch/backups/<timestamp>/` with a SHA-256 and manifest.
`--no-dialog-prevention` skips even this inspection/backup for the pending-recovery
test. No unvalidated preference toggle is silently enabled.

## Native helper

- macOS 14+ / Xcode Swift compiler, AppKit, ApplicationServices, Vision,
  ScreenCaptureKit. No third-party Python dependencies.
- CGWindowList enumerates AE PID windows with ID, layer, bounds and title;
  geometry changes are logged. AXObserver subscribes to creation/focus events,
  records notifications and pumps its run loop while polling CG windows.
- ScreenCaptureKit filters by the exact AE window ID and owner PID; captures
  exclude shadow and cursor. Vision recognizes Japanese and English.
- Known dialog context is required in addition to an exact allowlisted label.
  Unknown non-splash/non-workspace windows stop the watcher. Ambiguity stops;
  there is no fuzzy substitution for Japanese OCR errors.
- The A02b button allowlist is exact (NFKC/outer whitespace normalization only).
  Destructive labels are substring-blocked, including reset, save refusal,
  purchase/sign-out, safe mode and plugin-management controls. Overlap against
  any forbidden OCR/AX box rejects the candidate. Low-confidence OCR is rejected.
- Prefer AXPress for enabled buttons in the matching AX window. Otherwise verify
  foreground PID, fresh window bounds and fresh OCR, check occlusion, and post
  CGEvent mouse down/up **to the owned PID**, never global keyboard events.
- At most ten clicks. Each successful attempt saves window-only <=400,000-byte
  PNGs and before/after JSONL records (time, PID, bounds, OCR, label, method).
  The next capture must show the old dialog gone; failure stops without repeating
  the click. If no AE window remains for the after screenshot, this is recorded
  as unverified and stops, never substituting another application's screenshot.
- Missing permissions, failed/blank capture, unknown dialogs, failed verification
  or premature watcher exit fail the build. Neither the helper nor Python grants
  TCC permissions or dismisses system permission prompts.

The allowlist covers labels, not every possible localized dialog body. Context
variants absent from `Policy.knownDialog` require a reviewed fixture before adding.
Only the retained A02d image has a measured Vision fixture result so far: Vision
recognizes the recovery heading, but can misread the reduced `続行` label; the
policy correctly refuses that misread. No coordinate fallback exists.

Apple API references: [ScreenCaptureKit screenshot manager](https://developer.apple.com/documentation/screencapturekit/scscreenshotmanager),
[Vision text recognition](https://developer.apple.com/documentation/vision/vnrecognizetextrequest).

## Re-check without launching AE

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py \
  --scratch orchestra/state/A03-ae-dialog-watcher/recheck
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py
```

Expected: 10 watcher tests and 6 existing pipeline tests pass; the latter needs
numpy. Compilation output is redirected to `swift-build.log` in scratch. This
checks policy, OCR on A02d's saved image, centres with a negative monitor origin,
overlap rejection, and lifecycle failures. It does not prove live clicks.

Manual read-only helper commands after compilation:

```sh
orchestra/state/A03-ae-dialog-watcher/recheck/ae-dialog-watch permissions
orchestra/state/A03-ae-dialog-watcher/recheck/ae-dialog-watch ocr orchestra/reports/A02d-evidence/blocked.png
```

## Real test (follow-up; fresh scratch required)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py \
  --scratch orchestra/state/A03-ae-dialog-watcher/fresh-e2e \
  > orchestra/state/A03-ae-dialog-watcher/fresh-e2e.log 2>&1
```

Both launches disable prevention. The script checks the A02b preconditions,
launches once, writes a marker via JSX and requests `app.quit()`. Only after a
successful first run does it attempt the next launch and require zero dialog
clicks. An absent pending recovery dialog is **not** proof of the live OCR path;
inspect the first run's before/after events. Do not fabricate a crash, restore old
flags, force-quit AE, or repeat a failed launch without investigating its boundary.
