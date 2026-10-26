# Q03-refactor-olmkirakira: readability refactor of OLMKiraKira (bit-exact)

depends: Q00-refactor-native-diff-tool

Read `orchestra/REFACTOR_SPEC.md` first and follow it exactly.

## Scope
- mac/OLMKiraKira plus core/kirakira_*.h and RampPresets.h (keep the U02b/U04 UI behaviour; tests/ui_oracle must still pass)

## Do
- Apply the spec's points 1-8 to the files in scope. Record the base SHA, which is the merge base of your branch at start.
- Run gates G1-G6 for this plugin. G1 must cover both archs and both builds, with at least 3,000 cases.
- Report what the spec asks for, plus anything you found suspicious but left alone (possible latent bugs). Do not fix behaviour.
