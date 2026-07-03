# Windows AE addProperty Stall Diagnostics

Date: `2026-07-03`

This request starts from the now-proven fact that the Windows runtime-trace
runner reaches all of these stages for both exact cases:

- AE launch
- startup scripts
- JSX invocation
- request-dir resolution
- request JSON load
- case-id resolution
- dispatch start
- target plugin module load

The first non-advancing point is after:

- `about_to_add_effect ...`
- target `.aex` module load

and before:

- `effect_added ...`
- any parameter set logs
- `saveFrameToPng returned`
- `run_complete.json`

## Scope

Use the same two exact cases:

- `directionalblur_context_scale_20260606`
  - `db_existing_case_0001_software_pair`
- `smoother2_legacy_full_current_aex_recapture_20260621`
  - `legacy_case_0004_current_aex`

Do not use plugin-local witness breakpoints.

## Required question

Why does control fail to return to JSX across `effectParade.addProperty(...)`?

## Required evidence

For each case, return:

1. exact candidate string passed to `addProperty`
2. whether the JSX `try { addProperty(...) } catch (...) { ... }` returns
3. if it returns:
   - returned effect name / matchName
   - or exact caught exception string
4. if it does not return:
   - exact last log line before the stall
   - any hidden/modal window titles created after `about_to_add_effect`
   - any screenshot or window-title dump that proves a dialog exists
   - first-chance exception summary between `about_to_add_effect` and timeout
   - whether the target module emitted additional loads or secondary DLL loads
   - whether AE stayed responsive or entered a modal/message loop

## Strong hints

- Keep instrumentation host-level.
- If possible, emit one breadcrumb immediately before the `addProperty` call and
  one immediately after it. The absence of the second breadcrumb is evidence.
- If possible, arm a narrow exception logger only after module load and stop
  after the first few first-chance exceptions so the return is readable.
- If any version-mismatch / duplicate-install / missing-dependency dialog
  appears, return that verbatim. That is a valid answer.

## Acceptance

A satisfactory answer must classify one of:

- `addProperty returned success`
- `addProperty threw a catchable AE/ExtendScript error`
- `addProperty entered a modal/dialog path`
- `addProperty never returned and AE stayed inside native/plugin init`

“Module loaded” alone is no longer enough.
