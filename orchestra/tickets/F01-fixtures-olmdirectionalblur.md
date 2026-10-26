# F01-fixtures-olmdirectionalblur: remove fixture-specific paths from OLMDirectionalBlur (90 size literals, about 20 Tuple/Exact helpers in _admission.inc and _dispatch.inc)

Read `orchestra/FIXTURE_REMOVAL.md` and `orchestra/REFACTOR_SPEC.md` (gates, size limits). Follow the method exactly. Scope: this plugin's `mac/` folder and the `core/` headers that only it uses.

Report:
- the predicates you found, split into fixture and general;
- the Smart and Classic counts of the ON/OFF oracle campaigns;
- the G1 numbers;
- the code lines before and after.
