# F01-fixtures-olmkirakira: remove fixture-specific paths from OLMKiraKira (98 literal-equality chains, fixture mentions)

Read `orchestra/FIXTURE_REMOVAL.md` and `orchestra/REFACTOR_SPEC.md` (gates, size limits). Follow the method exactly. Scope: this plugin's `mac/` folder and the `core/` headers that only it uses.

Report:
- the predicates you found, split into fixture and general;
- the Smart and Classic counts of the ON/OFF oracle campaigns;
- the G1 numbers;
- the code lines before and after.

## Resume note
- First attempt: `git show 1de66c96177d4a72d328b000a8fca5cb380e3b49:orchestra/reports/F01-fixtures-olmkirakira.md`. Blanket OFF changes admission, so keep those conditions. The narrow 32x18 / three-Gaussian-leaf removal passed the focused oracle campaign. FIXTURE_REMOVAL.md now allows deleting source-text assertions that pin removed fixture code, so finish that narrow removal and run the gates.
