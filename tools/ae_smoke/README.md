# A01 real AE smoke (staged, incomplete)

The retained result proves AE 2026 registration/application of all ten fresh
bundles, with mapped executable paths and binary hashes. It does **not** prove
rendering, parameter equivalence, Smart dispatch, or pixel equality.
AE 2025 encountered an Adobe sign-in modal. See the ticket report.

Read-only verification (does not launch AE):

```sh
python3 tools/ae_smoke/verify_evidence.py
```

After resolving Adobe sign-in and quitting all AE instances, rerun the load and
parameter probe with a fresh run ID:

```sh
python3 tools/ae_smoke/run_ae_smoke.py --run-id rerun2026 --year 2026
python3 tools/ae_smoke/run_ae_smoke.py --run-id rerun2025 --year 2025
```

The driver checks both writable `OLM-smoke` folders, waits up to two hours for
existing AE processes, checks `memory_pressure >= 30%`, launches one owned AE,
and uses `-r` with a bounded `DoScriptFile` fallback. It captures a screenshot
on timeout, never clicks a dialog, and terminates only its owned process and
identified installation-local descendants. It changes no preferences. Launch
failure may require user sign-in; do not automate credentials.

`--build --install` builds into `~/.cache/olm-emu/A01` and installs into both
allowed folders. Installation intentionally refuses an existing destination;
the original A01 bundles remain installed. Do not use this flag for an ordinary
load rerun. The build script uses one Xcode job.

The probe captures raw ExtendScript property types/values/min/max, plus output
module templates. Popup labels are explicitly `null`: no popup label getter was
implemented. AE built-in compositing properties are included in the raw dump;
do not count them as plugin parameters. Source-declaration comparison remains
incomplete.

## Prepared but not yet validated render stage

Create a scratch virtual environment and deterministic SDR inputs:

```sh
python3 -m venv orchestra/state/A01-real-ae-smoke/venv
TMPDIR="$PWD/orchestra/state/A01-real-ae-smoke" orchestra/state/A01-real-ae-smoke/venv/bin/pip install numpy tifffile OpenEXR
orchestra/state/A01-real-ae-smoke/venv/bin/python tools/ae_smoke/prepare_inputs.py orchestra/state/A01-real-ae-smoke/inputs
python3 tools/ae_smoke/run_ae_smoke.py --run-id defaults --prepare-inputs orchestra/state/A01-real-ae-smoke/inputs/inputs.json
```

`prepare_inputs.py` calls the existing OLMBlur fuzz adapter with seed 1, choosing
one SDR case per depth with both dimensions >= 4. It saves the exact generator
ARGB bytes, full-range unassociated-alpha 16-bit TIFF, and uncompressed float
EXR. Source/file hashes and generator indices are recorded. No expected pixel
values are patched. Import quantization and premultiplication are unproven.

`prepare.jsx` intends to save three projects, each with ten enabled default
plugins and a no-effect control. It requests no working space, no linearization,
Software GPU setting, straight-alpha TIFF 8/16 and float EXR. This preparation
stage has not completed in this ticket. It depends on the observed local
`TIFF シーケンス (アルファ付き)` and `OLM EXR 32 Float` templates. EXR exporter
compression and Preserve-RGB settings must be verified independently.

The aerender invocation, three exact-corpus parameter sets, F47 worker input and
parameter mapping, file-to-ARGB conversion, no-effect I/O checks, and Effect
Controls screenshots remain to be implemented/validated. Do not treat the above
commands as a completed end-to-end matrix.

`compare.py` only compares already normalized packed ARGB files, by exact sample
bytes. It rejects incorrect lengths and reports first x/y/channel and SHA-256.
It does not decode image files, infer transforms, classify a mismatch, or use a
tolerance:

```sh
python3 tools/ae_smoke/compare.py ae.argb host.argb --width 32 --height 24 --depth 16
```

## A01b continuation (blocked before rendering)

See `orchestra/reports/A01b-real-ae-render-compare.md`. The new default scratch
root is `orchestra/state/A01b-real-ae-render-compare/`. Busy detection now uses
`ps` and matches only command lines ending in `MacOS/After Effects`, per the
ticket. Helpers are not treated as a user AE session.

`--stage probe` is the default. `--stage io --prepare-inputs <inputs.json>` attempts
to prepare **control-only** projects using the existing JSX. It does not render,
decode images, or validate an I/O gate. `matrix`, `compare`, `screens` and `all`
are reserved choices that fail explicitly; the whole pipeline is not implemented.
Both the 2025 probe and 2026 preparation timed out in A01b with startup dialogs.
No effect comparison should be inferred from these commands.

`source_popups.py <output.json>` resolves all 20 `PF_ADD_POPUP` declarations from
source string tables across the ten plugins. This covers source popup metadata
only, not the full parameter audit. AE has no third-party popup-label getter in
the existing scripting probe; labels are not claimed as verified in AE.
