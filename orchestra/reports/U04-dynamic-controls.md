status: blocked
summary: |
  Implemented hidden/disabled parity in five production plugins; audited all ten.
  Original UPDATE matrix: 1,321 rows, 2,642 Mac state/reconstruction checks, zero mismatches.
  Seed1 n300 per touched plugin completed; 4,830 before/after render checks had zero changes.
  Pinned-worker corpus replay: 914/915 match; one original RadialBlur SMART_RENDER fails.
  USER_CHANGED has static parity only; native saved-project reload remains unverified.

## facts

Baseline: `a7a82ae5411a8c9f146babc84effe4b49810d8c5`; implementation checkpoint: `1c057128`.
No pixel kernels, release gates, ledger, MAIN, or AEXCompat sources were changed. No worker was rebuilt, no plugin installed, no native AE session operated, and nothing pushed.

### UI implementation and executed evidence

- ColorKeep now hides colors above the count through DynamicStream; its existing USER_CHANGED and UPDATE routes share the handler.
- ColorKey uses HIDDEN for the original P/C/N/R visibility predicates, and DISABLED only on global Threshold, Color, Use Replace and Replace Color as the original does. No names change.
- RadialBlur Noise Layer/Seed/Offset/Thickness now use HIDDEN; Rotation/Zoom strength/offset predicates retain their original disabled behavior.
- KiraKira has UPDATE dispatch and five Use Ramp solid/ramp disabled pairs.
- Smoother2 has UPDATE dispatch in **the production Xcode source** `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`, including key/invert, gamma mode/count, and gamma-color visibility. The old top-level unused source was not changed. The render-only CLI shim remains render-only.
- Existing Blur, DirectionalBlur and DistanceGradation handlers matched the original. Smoother v1 and ToonDilate negative controls had no UI mutation.

Commands actually run:

```sh
python3 tests/ui_oracle/verify.py
python3 tests/ui_oracle/capture_dynamic.py --output orchestra/state/U04-dynamic-controls/extended
python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/final-ui --witnesses tests/ui_oracle/dynamic
python3 tests/ui_oracle/audit_user_changed.py
```

Results:

- U03 fixture integrity: **17 sessions / 174 dispatches**, exit0. This is fixture checking, not a new replay of all U03 drawing events.
- New original capture: **1,321 UPDATE dispatches**, selector errors0. Requests, raw compressed original outputs and original/request/worker SHA256 bindings are committed in `tests/ui_oracle/dynamic/`. Worker SHA256: `e476ba8ddfbda5fc2ef1cda49c700f15c5d09a232930f6a2074d7026f2c406b0`.
- First large capture exposed the worker's **256-event/session limit**, exit1 before dispatch. Splitting into batches of200 resolved it; all final batches succeeded.
- Matrix rows: ColorKeep4, ColorKey836, Blur2, DirectionalBlur3, DistanceGradation363, RadialBlur54, Smoother2 18, KiraKira35, Smoother3, ToonDilate3. ColorKey exercises all25 rows' use/replace toggles across P/C/R; KiraKira includes all32 checkbox combinations; Distance covers all enumerated predicate combinations.
- Mac test compiles actual production handler bodies against the real SDK and recording ParamUtils/DynamicStream suites. **1,321 stateful + 1,321 fresh UI reconstruction checks**, **zero final-state or ordered-mutation mismatches**; first mismatch: **none**. Names and parameter values are unchanged; all Mac acquired stream/effect handles are released. Mutation comparison includes full UI flags, HIDDEN, slots and order. Acquisition/lifetime call sequences are not asserted identical to the original's known ColorKeep stream leak.
- This is a handler test, not full EffectMain execution. Dispatch presence is source-checked. Negative controls assert dispatch absence and run a no-op in the test host.
- USER_CHANGED static audit: **10/10 Mac dispatches agree**. Original ColorKeep selectors13/14 call `180002210`; five C++ effects dispatch selector13 to vtable+0x28, whose methods immediately return; Blur/Directional/Distance/Smoother have no selector13 case. The evidence is explicitly labeled `static_not_execution` in `U04-evidence/user-changed-static.json`.
- The immutable U03 worker's `classic_ui.rs` hardcodes UPDATE selector14 and has no selector13 operation. No executed original USER_CHANGED witness is claimed.
- Full Smoother2 production source passed real-SDK `clang++ -std=c++17 -fsyntax-only` with MAIN's `Headers`, `Headers/SP`, `Util`, `Resources` and `mac/OLMSmoother2` include paths.
- ColorKey's existing parameter-surface test passed. RadialBlur's older source-text test failed its Thickness precision string assertion **on both baseline and candidate**; its other two assertions passed on baseline. This unrelated pre-existing test was not changed.

### Render evidence

Actual AEX generation used `tools/fuzz/run.py --plugin PLUGIN --n 300 --seed 1 --jobs 1` with ticket-local `--scratch`, `--report`, `--corpus`; the four initial runs were followed by:

```sh
python3 tests/ui_oracle/render_regression.py --scratch orchestra/state/U04-dynamic-controls/regression --phase fuzz --only olmkirakira
python3 tests/ui_oracle/render_unchanged.py --base a7a82ae5411a8c9f146babc84effe4b49810d8c5 --scratch orchestra/state/U04-dynamic-controls/render-unchanged
python3 tests/ui_oracle/render_regression.py --scratch orchestra/state/U04-dynamic-controls/corpus-replay --phase corpus
```

An initial `kirakira` adapter-name typo exited1 without running cases; the corrected `olmkirakira` command above completed300. All five final fuzz runs completed300, using worker `worker-F46-pow`, SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.

| Plugin | Smart exact / 300 | Classic exact / mismatch / refusal | Pinned corpus matches |
|---|---:|---:|---:|
| ColorKeep | 300 | 74 / 131 / 95 | 218/218 |
| ColorKey | 300 | 0 / 300 / 0 | 9/9 |
| Smoother2 | 300 | 0 / 0 / 300 | 105/105 |
| KiraKira | 287 | 0 / 48 / 252 | 342/342 |
| RadialBlur | 275 | 2 / 126 / 172 | 240/241 |

KiraKira has13 original Smart rejects with corresponding Mac refusals. RadialBlur has20 original Smart rejects and5 original Smart budgets; those25 are uncompared, not exact. Existing Classic discrepancies were retained. First original mismatch in ColorKeep is seed1 index0, Classic byte8: original `00`, Mac `ff`, 191 differing bytes. ColorKey index0 Classic byte1 is `00`/`93`; RadialBlur index0 Classic byte4 is `00`/`1a`. Full counts/hashes/first differences are in the compressed reports.

Pre-ticket/current Mac comparison: **1,500 generated cases + 915 corpus cases**, two routes each = **4,830 comparisons**, **zero changes in return status, metadata or exact output bytes**. Thus no exact→non-exact transition was introduced on those inputs. Refusal diagnostic source-line numbers are excluded because inserting UI functions shifts them; the initial comparison caught that attribution difference, and the comparison was corrected to test actual status/metadata/output. No output bytes are normalized.

Pinned-original replay completed all915 cases: **914 match saved results**. First and only mismatch:

- `tests/fuzz_corpus/radialblur/C46_seed1_case000280.json`, PF32, **248×1**, index280.
- Its pinned F46 original Smart worker returned reject1: `execution stopped before the guest returned (RIP=0x180002860)`.
- Saved original raw SHA256 was `5a19de28aece7b23b644e5f2533da7f662677e3d6a837b9a96d88a53726487f8`; this run produced no accepted original frame/hash. Mac Smart is consequently `uncompared`; Classic refuses. Mac before/after comparison for the same corpus still matches.
- `replay_matches_saved=false` for RadialBlur; true for the other four plugins. No worker replacement, rebaseline, kernel tuning or speculative retry was performed.

Durable full compressed fuzz/replay reports, UI/render summaries and SHA256 manifest are under `orchestra/reports/U04-evidence/`. Successful temporary render builds/source mirror and UI generated translation units were deleted. Logs remain in ticket scratch; no background process remains at final handoff.

## inference

The captured matrix establishes exact hostless UPDATE state and mutation parity. Static evidence supports unchanged USER_CHANGED behavior, but it is not an executed selector13 differential. Reconstructing UI from saved scalar parameter values establishes that these handlers do not depend on prior UI state; it does **not** establish native AEP persistence, reopen scheduling, or host delivery for effects without SEND_UPDATE_PARAMS_UI.

The corpus failure occurs inside the unchanged original worker before it returns a Smart frame. Coupled with exact before/after Mac results, it does not indicate a UI-induced pixel regression. It still prevents the required **all corpora replay true** acceptance. Status remains blocked rather than promoting a partial acceptance.

## changed_files

- `mac/DynamicControls.h`
- `mac/ColorKeep/ColorKeep.cpp`
- `mac/OLMColorKey/OLMColorKey.cpp`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`
- `tests/ui_oracle/{README.md,mac_host.cpp,compare_mac.py,capture_dynamic.py,audit_user_changed.py,render_unchanged.py,render_regression.py,dynamic/*}`
- `orchestra/reports/U04-evidence/*` and this report.

## verify

From the ticket worktree, using fresh scratch directories:

```sh
python3 tests/ui_oracle/verify.py
python3 tests/ui_oracle/audit_user_changed.py
python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/recheck-ui --witnesses tests/ui_oracle/dynamic
python3 tests/ui_oracle/capture_dynamic.py --output orchestra/state/U04-dynamic-controls/recheck-original
python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/recheck-fresh --witnesses orchestra/state/U04-dynamic-controls/recheck-original
python3 tests/ui_oracle/render_unchanged.py --base a7a82ae5411a8c9f146babc84effe4b49810d8c5 --scratch orchestra/state/U04-dynamic-controls/recheck-render
python3 tests/ui_oracle/render_regression.py --phase fuzz --scratch orchestra/state/U04-dynamic-controls/recheck-fuzz
python3 tests/ui_oracle/render_regression.py --phase corpus --scratch orchestra/state/U04-dynamic-controls/recheck-corpus
```

Expected: fixture verification exit0; static audit10 agreeing rows; UI comparisons2,642 checks with zero mismatches; original capture1,321 successful dispatches; render comparison4,830 unchanged results; five completed n300 campaigns. Corpus command is **currently failing**:914/915 saved-result matches, original RadialBlur failure described above. Emulator time budgets may vary; do not classify a budget/reject as exact.

## next

1. U03 follow-up: authorize selector13 support in a new immutable UI worker, capture USER_CHANGED for all ten plugins, and run the same Mac dispatch matrix.
2. U06 native acceptance: verify actual UPDATE scheduling and save/reopen/undo UI state in Windows/Mac AE, with loaded binary identities.
3. Separate oracle ticket: investigate the pinned F46 RadialBlur C46 index280 execution-stop boundary. Preserve its saved result and Mac kernels; do not rebaseline it from this failed replay.
