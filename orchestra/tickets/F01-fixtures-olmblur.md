# F01-fixtures-olmblur: remove fixture-specific paths from OLMBlur (production fixture admissions noted by C02)

Read `orchestra/FIXTURE_REMOVAL.md` and `orchestra/REFACTOR_SPEC.md` (gates, size limits). Follow the method exactly. Scope: this plugin's `mac/` folder and the `core/` headers that only it uses.

Report:
- the predicates you found, split into fixture and general;
- the Smart and Classic counts of the ON/OFF oracle campaigns;
- the G1 numbers;
- the code lines before and after.

## Resume note
- First attempt: `git show 03192244d4bfe5942abf4d9bae3f775e4eddd2c4:orchestra/reports/F01-fixtures-olmblur.md`. OFF gave 324 Smart exact. ON gave 239 exact plus 85 padding-canary errors. Under the decision now in FIXTURE_REMOVAL.md, remove the fallback, then finish the deletion and the gates. Source-text tests that pin the fallback or the 0xA5 padding copy may be deleted; list them.
