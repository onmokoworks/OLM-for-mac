# F01-fixtures-olmsmoother2: remove fixture-specific paths from OLMSmoother2

Read `orchestra/FIXTURE_REMOVAL.md` and `orchestra/REFACTOR_SPEC.md` (gates, size limits). Follow the method exactly. Scope: this plugin's `mac/` folder and the `core/` headers that only it uses.

Report:
- the predicates you found, split into fixture and general;
- the Smart and Classic counts of the ON/OFF oracle campaigns;
- the G1 numbers;
- the code lines before and after.

## Resume note
- First attempt: `git show 2af8bde423cedfdab2de3c4be79c15272a38212a:orchestra/reports/F01-fixtures-olmsmoother2.md`. It stopped on source-contract tests and covered only the two 5x5 families. FIXTURE_REMOVAL.md now allows deleting such source-text assertions, and requires per-family coverage. Redo it with that.
