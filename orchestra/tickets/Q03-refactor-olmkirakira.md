# Q03-refactor-olmkirakira: readability refactor of OLMKiraKira (bit-exact)

depends: Q00-refactor-native-diff-tool

Read `orchestra/REFACTOR_SPEC.md` first and follow it exactly.

## Scope
- mac/OLMKiraKira plus core/kirakira_*.h and RampPresets.h (keep the U02b/U04 UI behaviour; tests/ui_oracle must still pass)

## Do
- Apply the spec's points 1-8 to the files in scope. Record the base SHA, which is the merge base of your branch at start.
- Run gates G1-G6 for this plugin. G1 must cover both archs and both builds, with at least 3,000 cases.
- Report what the spec asks for, plus anything you found suspicious but left alone (possible latent bugs). Do not fix behaviour.

## Resume note (orchestrator)
- The previous attempt stopped only because the old spec required the release gate per ticket. The revised spec drops that: the gates are G1, G2 (Mac side), G4 (Xcode plus the plugin's text/UI tests) and G5 (warnings). The orchestrator runs the release gate and packaging at the end.
- Tests that were already failing at base (verify by running them at base) do not block. List them in the report.
- Notes from the previous attempt: `git show a80300da696d07d549b24efb79fa46182c2661d7:orchestra/reports/Q03-refactor-olmkirakira.md`. A split that already passed G1 there can be redone the same way.
- Start by merging `codex/public-beta-roi` into your branch, so that you begin from the current tree.
