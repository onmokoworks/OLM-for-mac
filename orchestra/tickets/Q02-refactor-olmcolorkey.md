# Q02-refactor-olmcolorkey: readability refactor of OLMColorKey (bit-exact)

depends: Q00-refactor-native-diff-tool

Read `orchestra/REFACTOR_SPEC.md` first and follow it exactly.

## Scope
- mac/OLMColorKey (2,975 lines, the most magic numbers)

## Do
- Apply the spec's points 1-8 to the files in scope. Record the base SHA, which is the merge base of your branch at start.
- Run gates G1-G6 for this plugin. G1 must cover both archs and both builds, with at least 3,000 cases.
- Report what the spec asks for, plus anything you found suspicious but left alone (possible latent bugs). Do not fix behaviour.

## Resume note (orchestrator, after the first attempt)
- The first attempt stopped with `blocked` because no float-colour sampler exists for ColorKey. The spec now says the 32 bpc depth inputs are the float coverage, so that is not a blocker.
- Reuse the facts from the first attempt, which are in the report at commit `6fc44fc1` (`git show 6fc44fc1:orchestra/reports/Q02-refactor-olmcolorkey.md`):
  - the split plan: Diagnostics, Parameters, Distance, ColorMath, AdmissionFixtures, BlurMath, Pixels, Kernel, Render;
  - the G3 base numbers;
  - the UI tests that read the main cpp.
- Keep UpdateParameterUI and its dispatch in the main cpp.
