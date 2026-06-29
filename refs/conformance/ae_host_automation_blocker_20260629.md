# AE Host Automation Blocker 2026-06-29

Status: `resolved`

Scope: Mac AE automation, not an OLM algorithm proof.

## What Happened

AE was not left running. A minimal `DoScriptFile` JSX that only writes a marker
file still blocked before the script completed. The diagnostic classified the
state as `host-blocked-modal-dialog`.

The sampled stack was in `AEDoScriptFileCommand -> U_ReportErrorDialog` with a
modal `UI_MessageBox`, so this is before OLM-specific JSX can report its own
error.

Trying the AE executable `-r minimal.jsx` path also exited without writing the
marker file.

After a normal launch of `Adobe After Effects 2026`, the 2026-06-29 13:57
diagnostic still classified the host as `host-blocked-modal-dialog`. The saved
report is `refs/reports/ae_host_diagnostic_20260629_135747/ae_host_diagnostic.md`;
the sampled stack still contains `UI_MessageBox::RunModal`, `OS_Dialog::ModalLoop`,
and `ModalSession`.

Clearing the visible disk-cache warning moved the host forward: the 2026-06-29
14:00 diagnostic reports `ae-running-no-accessible-window`, with no known modal
stack. However, the bounded `OLMDistanceGradation case_0026` single-case runner
still times out through AppleEvent/DoScript. Its JSX log reaches `load request
manifests` and then does not complete before AppleEvent `-1712`. Evidence:
`refs/reports/ae_single_case_timeout_20260629_1403/`.

The remaining timeout was caused by AE 26.3 ExtendScript `JSON.parse` hanging on
the generated 1.7MB `reference_manifest.json`. A direct probe showed `eval("(" +
text + ")")` parses the same local manifest immediately, so
`scripts/ae_render_single_case.jsx` now uses the legacy parser for local
manifest artifacts. After that change, the bounded `OLMDistanceGradation
case_0026` no-background runner completed and wrote a PNG. Evidence:
`refs/reports/ae_single_case_olmdistancegradation_case0026_no_bg_20260629_1408/`.

## Meaning

This no longer blocks bounded Mac AE validation. The recovered no-background
probe is diagnostic evidence for DistanceGradation, but it does not make the
case `AE exact` and it must not trigger broad PNG tuning.

## Next Allowed Action

Continue with `OLMDistanceGradation case_0026` Mac field-prep / installed-binary
inspection. If the runner regresses, first check for visible AE dialogs, then
check whether a new large manifest is being sent through AE `JSON.parse`.
