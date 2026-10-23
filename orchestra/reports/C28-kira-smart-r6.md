status: partial

summary:
- One Smart cluster closed: luminance/max directional Gaussian.
- Seed1 Smart263/0/37 → 264/0/36; fresh seed14 262/0/38 → 264/0/36.
- Previous exact output and corpus samples persist; sanitizer checks pass.
- Investigation continues toward the requested three clusters.

facts:
- Base `1ccc9cd494617dde93a1b9eb3882de0c2aa9d25c`; branch `orch/C28-kira-smart-r6`.
- Read shared guide, compatibility plan, emulator gotchas, Kira restrictions and previous triage/fix reports. Used MAIN assets/reference workers read-only by absolute path.
- [Scalar Gaussian report](C28-kira-smart-r6-scalar-gaussian.md) gives exact commands, first-stage bits, identities and before/after counts.
- Independent final648 conditions exact,7 negative refusals,900 sanitized campaign renders,70 guarded corpus inputs and140 sample-route comparisons pass. Strict production replay8/8. Existing25 fast tests and compiled54-row generic sanitizer test pass.

inference:
- Evidence supports the bounded CPU-emulation cluster, not whole-plugin/native AE/UCRT compatibility.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C28_scalar_gaussian.json`
- `orchestra/reports/C28-kira-smart-r6{,-scalar-gaussian}.md`

verify:
- Run the exact sequential commands in the linked cluster report at its commit. Expected seed1=264/0/36, seed13=255/0/45, seed14=264/0/36; previous exact unchanged; strict replay8/8.

next:
- Four-component directional Gaussian, then remaining approximation owners.
