# Q01-refactor-olmradialblur: readability refactor of OLMRadialBlur (bit-exact)

depends: Q00-refactor-native-diff-tool

Read `orchestra/REFACTOR_SPEC.md` first and follow it exactly.

## Scope
- mac/OLMRadialBlur (6,520 lines, the largest; if one pass is too big, finish a coherent part and report partial with a plan)

## Do
- Apply the spec's points 1-8 to the files in scope. Record the base SHA, which is the merge base of your branch at start.
- Run gates G1-G6 for this plugin. G1 must cover both archs and both builds, with at least 3,000 cases.
- Report what the spec asks for, plus anything you found suspicious but left alone (possible latent bugs). Do not fix behaviour.
