status: partial

summary:
- First cluster closed: finite PF32 luminance/Max box admission.
- Seed1 Smart282/0/18 →284/0/16; fresh seed23 280/0/20 →285/0/15.
- Zero admitted mismatches; preserve all previous exact outputs.
- Continuing with the remaining successful-oracle refusals.

facts:
- Shared contract, Kira ledger row, GOTCHAS, compatibility plan and prior triage/fix reports read.
- Initial n300/seed1/jobs1 reproduces282 exact/0 mismatch/18 refusal; original Smart287 success/13 rejection.
- Detailed commands, hashes, boundary values and validation: [brightness cluster](C38-kira-smart-r9-brightness.md).
- No MAIN/external emulator/worker/release gate/ledger/other-plugin changes, push or stash.

inference:
- Remaining families are admission candidates, not proven general compatibility.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C38_brightness.json`
- This report and brightness report.

verify:
- Run the exact reproduction block in the brightness report at its commit. Expected seed1=284/0/16; seed23=285/0/15,612 independent exact conditions,8 negative refusals,600 sanitized campaign renders,70 guarded corpus rows,140 unchanged sample comparisons.

next:
- Investigate finite four-component box, then signed Alpha Gaussian/HDR Alpha approximation.
