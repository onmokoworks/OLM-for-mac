status: partial
summary: |
  Corrected ColorKeep/ColorKey/RadialBlur visibility and added KiraKira/Smoother2 UPDATE dispatch.
  All 1,321 original UPDATE matrix rows match Mac state and ordered UI mutation calls.
  Fresh UI reconstruction from parameter values also matches all 1,321 rows.
  Render regression is running; native saved-project reload and USER_CHANGED oracle remain unverified.

## facts

Baseline: a7a82ae5411a8c9f146babc84effe4b49810d8c5.
`python3 tests/ui_oracle/verify.py`: 17 sessions, 174 dispatches; fixture integrity passed.
`python3 tests/ui_oracle/capture_dynamic.py --output orchestra/state/U04-dynamic-controls/extended`: 1,321 original UPDATE dispatches, selector errors zero. The worker limit is 256 events/session; requests are split into batches of 200. Original requests, compressed outputs, original/worker SHA256 bindings are in `tests/ui_oracle/dynamic/`.
`python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/ui-extended --witnesses tests/ui_oracle/dynamic`: 1,321 stateful checks + 1,321 fresh UI reconstruction checks, zero state or ordered mutation mismatches. Compiles extracted production handler bodies with real Mac SDK types and recording ParamUtils/DynamicStream suites. All acquired streams/effects released. Negative controls check absence of UI dispatch and execute a no-op in the test host.
No pixel kernels changed. Native AE was not operated. No USER_CHANGED execution is available in the pinned U03 worker (classic_ui.rs hardcodes selector14).

## inference

The results prove hostless UPDATE handler parity for the supplied values. Fresh state reconstruction is not a saved-AEP reopen test. Native scheduling of plugins without SEND_UPDATE_PARAMS_UI remains unproven. U03's missing selector13 prevents original-vs-Mac USER_CHANGED acceptance with the authorized immutable worker.

## changed_files

- `mac/DynamicControls.h` and UI-only changes in ColorKeep, ColorKey, KiraKira, RadialBlur, Smoother2 production Mac source.
- `tests/ui_oracle/{mac_host.cpp,compare_mac.py,capture_dynamic.py,render_unchanged.py,dynamic/*}`.
- This report.

## verify

```sh
python3 tests/ui_oracle/verify.py
python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/recheck --witnesses tests/ui_oracle/dynamic
python3 tests/ui_oracle/render_unchanged.py --base a7a82ae5411a8c9f146babc84effe4b49810d8c5 --scratch orchestra/state/U04-dynamic-controls/render-recheck
```
Expected UI: 1,321 original rows, 2,642 checks, zero mismatches. Render command still being validated at checkpoint.

## next

Finish render checks; add original selector13 support in a separately authorized U03 follow-up and perform native saved-project reload/scheduling checks in U06.
