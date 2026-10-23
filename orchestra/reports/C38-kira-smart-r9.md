status: partial

summary:
- Two clusters closed: finite scalar brightness box and finite color box.
- Seed1 Smart282/0/18 →285/0/15; fresh seed23/24 confirmations pass.
- Zero admitted mismatches; preserve all previous exact outputs.
- One T06 refusal→exact rebaseline;23 inherited discrepancies preserved.

facts:
- Shared contract, Kira ledger row, GOTCHAS, compatibility plan and prior triage/fix reports read.
- Initial n300/seed1/jobs1 reproduces282 exact/0 mismatch/18 refusal; original Smart287 success/13 rejection.
- Detailed commands, hashes, boundary values and validation: [brightness cluster](C38-kira-smart-r9-brightness.md) and [color cluster](C38-kira-smart-r9-color.md).
- No MAIN/external emulator/worker/release gate/ledger/other-plugin changes, push or stash.

inference:
- Remaining families are admission candidates, not proven general compatibility.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C38_brightness.json`
- `tools/emulation/probe_kirakira_color_alpha_C38.py`, color evidence/report and one T06 fixture.
- This report and brightness report.

verify:
- Run the exact reproduction block in the brightness report at its commit. Expected seed1=284/0/16; seed23=285/0/15,612 independent exact conditions,8 negative refusals,600 sanitized campaign renders,70 guarded corpus rows,140 unchanged sample comparisons.

next:
- Investigate signed Alpha Gaussian/HDR Alpha approximation (179/272).
