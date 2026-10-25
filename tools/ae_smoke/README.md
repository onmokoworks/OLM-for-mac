# Real AE 2026 smoke — A01c continuation

A01 established load/apply only. A01b rendered no pixels. A01c replaces the unsafe
launch lifecycle with **one full-path DoScriptFile dispatch after workspace detection**, a 180-second JSX deadline, and
normal quit only. AE 2025 is excluded. No bundle installation/build occurs.

The pipeline currently prepares **30 default effect cells and 3 I/O controls**
in three depth-specific projects during one GUI session (AE depth is project-wide).
The 90 corpus cells and native-host comparisons remain unimplemented. Do not
interpret an `all` run as completion of the requested 120-cell matrix.

Use a Python environment with numpy, tifffile and OpenEXR. For example:

```sh
python3 -m venv orchestra/state/A01c-real-ae-render-aerender/venv
TMPDIR="$PWD/orchestra/state/A01c-real-ae-render-aerender" orchestra/state/A01c-real-ae-render-aerender/venv/bin/pip install numpy tifffile OpenEXR
orchestra/state/A01c-real-ae-render-aerender/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --stage all --run-id fresh2026
```

Stages use the same `--run-id`:

- `build`: generate deterministic SDR inputs, check exact main executable paths
  using `ps ... comm` (so launch arguments cannot hide a running instance), wait
  up to two hours if busy, check memory free >=30%, launch AE 2026 once, create
  projects/queues and property readbacks, save, close project and `app.quit()`.
  Existing run launch files are rejected to prevent accidental second dispatch.
- `render`: require a complete build manifest; invoke 2026 `aerender -project`
  sequentially with MFR off. All render diagnostics go to depth-specific logs.
- `compare`: decode no-effect TIFF/EXR to packed ARGB and compare against source
  bytes with `compare.py`. Refuse interpretation when controls differ. This does
  **not** yet invoke a native-plugin host or compare effect cells.
- `all`: run those stages in order; stop on any failure.

On a GUI timeout, capture a center crop <=400 KB, request quit once via the full
2026 app path, then fail without retry. No SIGTERM/SIGKILL is sent to AE or its
helpers. If quit is blocked by a dialog, AE remains open for user recovery; do
not rerun. A successful JSX also must exit AE before rendering begins.

A02b adds a fail-closed screen-lock check immediately before GUI dispatch.
While locked the builder waits five minutes between checks, for up to 12 hours,
and records `screen-lock.log`. A02c recognizes an absent lock key as unlocked
only for a logged-in on-console session. A true lock key means locked; other
states, including an explicit false key, remain unknown and refuse launch. After waiting,
the process/memory preflight runs again; the main AE executable must also be
absent after the JSX process exits. Use `--scratch` to keep all generated files
inside the current ticket, for example:

```sh
python tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-priority --stage build --run-id priority --scratch orchestra/state/A02b-real-ae-retest-downsample
```

The output templates are the previously observed local
`TIFF シーケンス (アルファ付き)` and `OLM EXR 32 Float`. The script requests straight
alpha, no working space/linearization, and software GPU mode. Template settings,
import alpha behavior and the full image round trip still require real-host
validation. The decoder rejects HALF EXR channels and unexpected TIFF shape/depth;
16-bit decoding uses nearest inverse full-range scaling to AE's 0..32768 range.
An exhaustive synthetic inverse check is not an AE I/O calibration.

## Popup registration audit

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/popup_audit.py --scratch orchestra/state/A01c-real-ae-render-aerender/popup-recheck
```

This invokes the cached F46 AEX worker serially on the original binaries in MAIN,
tracing `PARAMS_SETUP` without rendering or rebuilding anything. Eight popup
registrations across DirectionalBlur, DistanceGradation and KiraKira match the
A01b source capture (labels, choice count, default). Current AE UI readback is a
separate boundary; `prepare.jsx` records values/min/max if it executes. No claim
is made that ExtendScript can enumerate third-party popup labels.

The cache index labels the original F47 worker `native-plugin-load-only`.
The cached F51 `plugin-host` uses the F47d rendering bridge; a future host matrix
must bind it to the **installed A01 bundle hashes**, input and read-back params,
not silently use another bundle set.

Offline verification:

```sh
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A01c-real-ae-render-aerender/venv/bin/python tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
```

These check main-process detection, the mathematical 16-bit encoding inverse,
and raw byte comparison (including float payloads). They are not AE renders.
See `orchestra/reports/A01c-real-ae-render-aerender.md` for measured results and
remaining work. Historical A01/A01b reports retain their original commands;
the current runner deliberately no longer accepts their unsafe launch options.

## A02 opt-in priority matrix

`--matrix downsample-priority --stage build --run-id priority` uses scratch under
`orchestra/state/A02-real-ae-retest-downsample/` and a separate JSX. The legacy
matrix remains the default. Priority comprises untouched defaults for all ten
plugins at 1920×1080, 1279×719 and 3840×2160, 8 bpc, with render-queue Resolution
Full/Half/Third/Quarter: 120 effects plus 12 independent controls. Inputs are
opaque deterministic RGB patterns with no zero channels. Render settings and
parameter readbacks are saved in `build.json`. AE output geometry must be read
from the rendered images; requested Resolution is not an InData trace.

Use the same matrix/run-id with `--stage render` to invoke aerender serially,
one queue item per process. `render-results.json` records exit status, output
shape/hash, all-black/transparent flags, refusal text and wall seconds (including
startup). `OLM_REFUSAL_TRACE` is set for GUI and per render. Absence of a refusal
tag is not proof of callback execution, particularly for the two Smoothers.

This priority scaffold does not yet implement 16/32 bpc, corpus parameters or
original/native-host comparisons. `--stage compare` is the legacy control
comparison and is not applicable to this matrix. Do not use `--stage all` for
this matrix. Successful frame output alone does not establish exactness.

`--matrix downsample-depths` prepares untouched defaults for 16/32 bpc at
1920×1080 and 1279×719, each at all four queue resolutions (160 effects and
16 controls). Run this separately after priority succeeds. FLOAT EXR output
is required for 32 bpc. This remains an unvalidated real-host scaffold and
contains no corpus cases; generation/codec checks are not AE calibration.

## Unattended AE 2026 launch (A03b)

Build starts the PID-scoped Swift/AX/Vision watcher before dispatch. With AE and
`aerender` absent, it exports `com.Adobe.After Effects.26.3`, copies the on-disk
plist into the run's `dialogs/preferences-*` directory, records both SHA-256
hashes and `defaults read` values in `dialogs/prevention.json`, then writes only
`CrashOccurred=false` and `ForceQuitOccured=false` (Adobe's spelling).
Readback must be `0` for both. Other preferences, projects and auto-saves are
untouched. Preserve the backup directory before deleting a worktree; never import
an entire stale plist to restore these flags. `--no-dialog-prevention` skips
backup/reset while retaining the watcher.

Before dispatch, the runner checks for other AE/aerender processes, an unlocked
console session and at least 30% free memory. Launch uses the full AE 2026 path.
Do not start a second instance or signal AE on failure. The failure handler
captures the owned window and requests normal quit once; if AE remains, stop
and report its PID. Never treat a missing marker or watcher failure as success.

To check prevention with two trivial JSX marker + `app.quit()` launches, use a
fresh scratch directory (the second launch runs only after the first succeeds):

```sh
mkdir -p orchestra/state/A03b-ae-crash-flags-and-ocr
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py \
  --scratch orchestra/state/A03b-ae-crash-flags-and-ocr/fresh-e2e \
  > orchestra/state/A03b-ae-crash-flags-and-ocr/fresh-e2e.log 2>&1
```

Each successful result requires a marker, exit code 0, no remaining AE, no
watcher click, and both flags still false. Native ScreenCaptureKit capture uses
points × backing scale; Vision uses `.accurate`, language correction off. Only
exact allowlisted labels with confidence ≥0.8 can trigger OCR clicks. Evidence
PNGs retain the pixels passed to Vision; capture events record dimensions/scale.

**Live proof remains blocked:** A03b set/read both flags false and captured 2x,
but capture subsequently timed out, the JSX marker was absent, and the normal
quit request timed out. No two-clean-launch or live button-click claim is made.
See [A03b report](../../orchestra/reports/A03b-ae-crash-flags-and-ocr.md) and
[watcher details](ae_dialog_watch/README.md). AE subsequently disappeared; investigate the capture/dispatch boundary before retrying.

A03c adds `--stage prefs` and `--stage prefs --restore` with the same
`--scratch`/`--run-id`. Builds enable scripting after crash-flag prevention and
restore the complete original preference file after AE exits. If AE stays alive,
restoration refuses until it exits. See [preference workflow](ae_dialog_watch/README.md#scripting-preference-a03c).
The A03c live test is blocked by an exact-label OCR failure on the recovery dialog;
two unattended launches remain unproven.

## A02e measured build boundary

The production builder now launches without `-r`, waits for the watcher’s
`workspace-ready`, and sends exactly one full-path DoScriptFile event. Startup
and JSX each have a 180-second budget; clean exit has 60 seconds. The watcher
remains running throughout. Unknown dialogs still stop the run with one normal
quit request and no retry.

AE 26.3 rejects output-module `Color` and `Depth` writes as read-only. The
opt-in downsample builder now records the applied template’s settings without
writing those fields. In the measured 8 bpc build, TIFF was Millions of Colors+,
RGB + Alpha, Premultiplied (Matted). Do not interpret this as calibrated straight
alpha or as validated 16/32 bpc output. Readback and independent controls remain
mandatory.

A02e saved all three priority projects (132 queue items), but the watcher
rejected AE’s script-progress window with its Cancel button as unknown.
No render was attempted, even though the script subsequently wrote complete.
See `orchestra/reports/A02e-real-ae-retest-downsample.md`. Resolve that watcher
boundary before another live run. The aerender stages still need the ticket’s
per-launch prevention/preference lifecycle before a full campaign.

## A02f saved-project reuse

Copy only a completed `build.json` into a fresh ticket-local run directory; leave
its project and footage paths unchanged. The render stage overrides each output
path with `-output` and uses the required `-mfr OFF 100` arguments. It performs
unlocked/idle/memory checks, crash prevention and reversible preference changes
for each invocation. Completed outputs (including black/transparent flags) are
retained on resume; render errors stop the campaign and require a fresh run ID.
A `stop` file in the run directory stops cooperatively between frames.

`compare_downsample.py RUN_DIRECTORY --timeout 15` compares available 8 bpc
frames serially against F53, falling back to the installed bundle over F53's
host when the original is unavailable (and for 4K). Full-resolution controls
are compared to the original raw input. Reduced controls supply a resampled
input proxy. Queue resolution and observed image dimensions are recorded;
these are **not a live InData/checkout trace**. Raw hidden-RGB differences at
zero alpha are classified as premultiplied-export I/O loss, not exactness.
The script resumes existing comparison records and does not launch AE.

The watcher treats Japanese/English script-progress titles as wait-only,
without clicking Cancel. Scripting access is set in indep-general preferences;
progress-dialog suppression is set in the main preferences text file. Both
original files are backed up and restored, with SHA-256 checks.
