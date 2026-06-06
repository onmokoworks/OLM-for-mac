# Parallel Agent Runbook

Updated: 2026-06-06

This runbook is the parent-agent dispatch sheet for the OLM Tools port. Use it
when launching sub-agents so parallel work stays narrow, evidence-backed, and
easy to merge back into the canonical notes.

## Parent Responsibilities

- Keep `notes/PORTING_BOARD.md`, `notes/PROGRESS_MATRIX.md`, and plugin
  ASM/IR notes canonical.
- Own all implementation changes, smoke registration, package verification, and
  commits unless a worker is explicitly given a disjoint write scope.
- Stop a plugin path when the next discriminating evidence is a pending Windows
  reference request.
- After any returned Windows refs or AE-host validation bundle, run
  `scripts/intake_olm_return.py` first, then decide which plugin-specific agent
  to wake.

## Standard Sub-Agent Output

Ask every sub-agent to return exactly these four items:

1. Current best-supported IR checkpoints.
2. Exact measured status, with commands or note/file references.
3. Whether the stop condition still holds and which request or AE result
   unblocks it.
4. One parent action backed by objdump/decomp/IR evidence.

Sub-agents should not return broad prose, speculative parameter tuning, or
"looks close" claims without a smoke command and metric.

## Dispatch Matrix

| Slice | Agent mode | Write scope | Best prompt focus | Stop / unblock |
| --- | --- | --- | --- | --- |
| `OLMBlur` | worker or verifier | Usually none; parent owns package scripts | AE-host pixel validation using bundled `olmblur_request.zip`; watch for max=1 residual regressions. | Returned AE-host PNGs and `AE_VALIDATION_RESULT*.json`. |
| `OLMColorKey` covered cases | verifier | none | Confirm RGB/Edge Thin/Edge Blur gates and Mac package request coverage. | AE-host covered-case PNG return. |
| `OLMColorKey` Replace/colorspace | explorer until refs arrive | none | Audit returned `olmcolorkey_replace_colorspace_20260606` and propose smallest implementable RGB Replace slice. | `refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json` covered. |
| `OLMToonDilate` | verifier | none | AE-host pixel validation for cases 1-3; only revisit boundary residual if host drift exceeds guarded CLI residual. | Returned AE-host PNGs. |
| `OLMDistanceGradation` | bounded worker candidate | parent-approved specific files only | Tighten one existing-ref slice at a time, preferably with decomp/OpenCV evidence. | Do not broaden beyond guarded cases without a new smoke. |
| `OLMSmoother` v1 | explorer | none | Verify v1-via-v2 compatibility remains acceptable; avoid standalone v1 unless user requires it. | AE-host rejection of v2 compatibility or explicit user request. |
| `OLMSmoother2` no-key | explorer until refs arrive | none | After import, run grid smoke and group residual by Smoothness/Smooth Range before implementation. | `smoother2_no_key_grid_20260606` covered. |
| `OLMDirectionalBlur` | explorer until refs arrive | none | Reconcile context scale, premul/straight RGB, alpha ownership from returned refs. | `directionalblur_context_scale_20260606` covered. |
| `OLMRadialBlur` Zoom/outer Rotation | verifier | none | Keep green Zoom/Zoom Offset/tiny Rotation gates and AE-host validation path honest. | AE-host result or regression. |
| `OLMRadialBlur` Inner/EdgeFade | explorer until refs arrive | none | Use nonzero Size Variation refs to isolate `+0x40/+0x48/+0x50` planes. | `radialblur_inner_size_variation_20260606` covered. |
| `OLMKiraKira` | explorer until refs arrive | none | Use single-ray refs to isolate ray order, angle table, scalar, crop/canvas. | `kirakira_single_ray_20260606` covered. |

## Ready-To-Paste Prompts

### AE Host Validation Verifier

Read `scripts/package_mac_plugins.sh`, `scripts/package_olm_handoff.sh`,
`scripts/verify_ae_host_return.py`, `refs/scripts/smoke_ae_host_return_verifier.py`,
and `notes/PROGRESS_MATRIX.md`. Do not edit. Report whether the Mac-side
package and verifier can accept a returned AE host zip/folder containing
`AE_VALIDATION_RESULT*.json` and pixel PNGs. Include the exact verification
command and any missing documentation or smoke gap.

### Pending Reference Import Auditor

Read `refs/reference_requests/*.json`,
`refs/scripts/package_reference_requests.py`,
`refs/scripts/import_and_check_win_reference.py`,
`refs/scripts/check_reference_request_status.py`, and
`refs/scripts/smoke_reference_requests_after_import.py`. Do not edit. Report
whether the pending requests are packageable/import-checkable, which returned
request should be processed first, and the exact post-import command sequence.

### Plugin Stop-Line Auditor

Read the plugin's IR/ASM notes, current CLI, smoke scripts, and its pending
request JSON. Do not edit. Report the best-supported IR, current measured
metrics, whether existing refs can support non-guesswork implementation, and
the first action after the pending request is imported.

### Bounded Worker

You are not alone in the codebase; do not revert or overwrite changes outside
your assigned files. Implement only the named slice, edit only the assigned
files, and run only the specified smoke. Return changed paths, command output
summary, and any residual risk.

## Parent Triage Order

0. To print the current canonical Windows/Mac handoff, run:
   `python3 scripts/print_current_handoff.py`
1. If AE-host validation results arrive, run:
   `python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass`
2. If Windows reference results arrive, run:
   `python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick`
3. Run `python3 refs/scripts/check_reference_request_status.py` and pick the
   newly covered request with the largest unblock value.
4. Run `python3 refs/scripts/next_reference_actions.py` to get the prioritized
   request-specific smoke and parent/sub-agent action.
   Use `python3 refs/scripts/next_reference_actions.py --json` when spawning an
   agent; `next_action` includes `plugin_area`, `mode`, `read_files`,
   `write_scope`, `smoke_command`, and a ready-to-paste `agent_prompt`.
5. Spawn exactly one plugin-specific explorer for the newly covered request.
6. Parent integrates the finding into IR/ASM notes, implements the smallest
   backed change, and runs the plugin smoke followed by
   `python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick`.
