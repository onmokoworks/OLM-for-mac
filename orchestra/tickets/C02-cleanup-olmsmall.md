# C02-cleanup-olmsmall: cleanup round 2 for olmsmall: test code out, admission, per-depth copies, warnings

depends: C01-cleanup-shared-math-and-tests

Follow `orchestra/tickets/C01-cleanup-shared-math-and-tests.md` steps 2-5 and its Done criteria. Scope: Smoother2, ToonDilate, ColorKeep and Smoother v1 `port.cpp` (not the generated files). You may use the shared `core/olm_world_safety.h`. If another C02 ticket edits it at the same time, keep your additions as separate functions so the merge stays simple.
- G1 speed: for intermediate commits, run 500 cases on arm64 for both builds. Run the full 3,000 cases on both archs only once, at the end.
- Do not run the release gate. The orchestrator runs it once after all C02 tickets.
