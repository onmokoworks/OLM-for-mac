# G01: release gate v2 after the Q, C and F cleanups: get back to 7/7

## State
- Since R13 (7/7), the refactors (Q, C02) and the fixture removals (F01, RadialBlur `e8c4cb60`) have merged. Every one of them passed G1 (native_diff, 0 differences) and the ON/OFF oracle checks.
- Several workers reported historical source-text tests failing, i.e. tests that grep the plugin source for literals or for fixture code that no longer exists. Their reports are `orchestra/reports/C02-*`, `F01-*` and `Q0*`.

## Do
1. Run the complete release gate v2 (`--state orchestra/state/G01.../gate --jobs 1`).
2. For each failing test, classify it:
   - Source-text / evidence pin: it asserts that a literal, a removed fixture or an old file layout is present. Delete the obsolete assertion, or the whole file when nothing else remains in it. Or update it to the current structure if it still checks something meaningful.
   - Behaviour: render output, refusal tags, UI state, lifecycle. If one of these fails, stop and report it with the first failing case. Do not change production code to make it pass without evidence.
3. Re-run the gate until it is 7/7 or only behaviour failures remain.
4. Report:
   - every test changed or deleted, with a one-line reason;
   - the seven stage results;
   - the totals: lines of production code (non-comment) per plugin now, compared with Q-series start `12622f68`.
