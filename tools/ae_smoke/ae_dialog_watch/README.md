# AE 2026 dialog watcher (A03; live validation blocked)

`run_ae_smoke.py --stage build` compiles this Swift helper into the run's
`dialogs/` directory, waits for its permission/readiness handshake, and only
then launches the full-path AE 2026 executable. Python supplies **only its own
Popen PID**. The watcher never discovers/adopts an existing AE instance.
It stops cooperatively after the build lifecycle; it sends no process signals.
The runner retains busy/lock/memory checks and the 180-second JSX deadline.

**Not yet validated for unattended production use.** A03b obtained native 2x
captures but then encountered a capture timeout, missing JSX marker and normal
quit timeout. No live AX/OCR click or clean second launch was established.
See `orchestra/reports/A03b-ae-crash-flags-and-ocr.md`.

## Prevention

With no AE/aerender running, `prepare_launch` exports effective CFPreferences and
copies the on-disk 26.3 plist into the run's `dialogs/preferences-*` directory.
It logs hashes and before values, writes only `CrashOccurred` and
`ForceQuitOccured` false, then logs `defaults read` results (both must be `0`).
The explicitly authorized domain is `com.Adobe.After Effects.26.3`; unexpected
versions fail closed. Projects, auto-saves and all other keys are untouched.
Preserve these backups before deleting scratch. `--no-dialog-prevention` skips
this step. A03b measured both flags changing from `1` to `0`; prevention of the
recovery dialog and clean startup remain unproven.

## Native helper

- macOS 14+ / Xcode Swift compiler, AppKit, ApplicationServices, Vision,
  ScreenCaptureKit. No third-party Python dependencies.
- CGWindowList enumerates AE PID windows with ID, layer, bounds and title;
  geometry changes are logged. AXObserver subscribes to creation/focus events,
  records notifications and pumps its run loop while polling CG windows.
- ScreenCaptureKit filters by the exact AE window ID and owner PID; captures
  exclude shadow and cursor and use content points × native backing scale.
  Vision recognizes Japanese and English with `.accurate`, language correction
  off. Evidence PNGs preserve native pixels. Capture dimensions/scale are logged.
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
- At most ten clicks. Each successful attempt saves window-only native-resolution
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

Expected: 12 watcher tests and 6 existing pipeline tests pass; the latter needs
numpy. Compilation output is redirected to `swift-build.log` in scratch. This
checks policy, OCR on A02d's saved image, centres with a negative monitor origin,
overlap rejection, and lifecycle failures. It does not prove live clicks.

Manual read-only helper commands after compilation:

```sh
orchestra/state/A03-ae-dialog-watcher/recheck/ae-dialog-watch permissions
orchestra/state/A03-ae-dialog-watcher/recheck/ae-dialog-watch ocr orchestra/reports/A02d-evidence/blocked.png
```

## Real test

Follow the [unattended procedure](../README.md#unattended-ae-2026-launch-a03b).
The test now enables crash-flag prevention for both launches, requires zero
clicks, reads flags after exit, and rejects nonzero exit codes. A03b did not
achieve clean quit or marker execution; live recovery/OCR clicks remain unproven.
Do not manufacture a crash by force quitting. A controlled flag-only recovery
experiment must wait for successful clean lifecycle verification.

## Scripting preference (A03c)

The smoke build and two-launch test now enable file/network scripting after
crash-flag prevention, while AE/aerender are absent. `prefs.py` copies the original
26.3 `indep-general.txt`, hashes it, inserts/updates only
`Main Pref Section v2 / Pref_SCRIPTING_FILE_NETWORK_SECURITY = 01`, and logs
readback in `prefs/scripting-prefs.json`. CR/LF/CRLF and other bytes are preserved.
Finally, after AE exits, the **whole original file** is restored and hash-checked;
AE's incidental preference changes during this test are consequently discarded.
If AE remains alive, restore refuses and preserves the backup for later recovery.
Never reuse a prefs directory for enabling; this protects the original backup.

Explicit commands (use the same scratch/run-id for restoration):

```sh
python3 tools/ae_smoke/run_ae_smoke.py --stage prefs --scratch orchestra/state/A03c-ae-scripting-pref-and-live-proof --run-id manual
python3 tools/ae_smoke/run_ae_smoke.py --stage prefs --restore --scratch orchestra/state/A03c-ae-scripting-pref-and-live-proof --run-id manual
```

The marker JSX catches write errors and always invokes `app.quit()` in `finally`.
The test requires the exact marker including runtime scripting value 1.
A03c's live attempt was blocked **before marker execution** by a recovery dialog:
native 1050×746 OCR read `綂行` at confidence 0.30, not the allowed `続行`.
No click or second launch occurred. Normal quit removed AE and the original
preference file was restored exactly. This does not establish runtime acceptance
of the scripting setting or unattended launch success. See
`orchestra/reports/A03c-ae-scripting-pref-and-live-proof.md` for evidence.

Offline preference checks (no installed preference writes):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_prefs.py orchestra/state/A03c-ae-scripting-pref-and-live-proof/check
```

Expected: 3 tests pass, covering newline/value variants, ambiguous sections,
backup integrity, repeat-enable refusal, busy restore refusal and exact restore.

A03d adds the OCR-only `crash_recovery_layout` rule. It requires one exact
high-confidence Japanese recovery title and the three exact high-confidence
non-Continue labels, in their displayed order with a common vertical band.
There must be exactly four OCR boxes in that band; the remaining box must be
strictly left of Manage Plugins, non-destructive, and overlap no other box.
The rule is re-evaluated on a fresh capture before a centre click. Recovery
surfaces cannot fall back to the generic label policy when this rule fails.
No low-confidence Japanese spelling is added to the allowlist.

`test_e2e.py` now permits only this rule on the first launch and still requires
zero clicks on the second. It inventories the requested AE state roots before
prevention, before launch, during recovery (if observed), and after exit.
The optional `snapshot-hook`/`snapshot-request`/`snapshot-ready` files let the
live probe take its read-only inventory before the recovery click; a 30-second
barrier timeout blocks the click. `crash_snapshot.py DESTINATION` can also run
independently. Inventories stream SHA-256 reads and record missing roots/errors.
No additional crash-marker deletion is implemented: A03d's live attempts did
not reproduce recovery and could not establish a causal marker.
