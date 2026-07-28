# Windows Codex owner retry addendum — OLM direct-evidence batch

Date: 2026-07-28
Owner: Windows Codex
Parent work-order: `WINDOWS_CODEX_OWNER_WORK_ORDER_20260728.md`
Input return: `OLM_WINDOWS_OWNER_FINAL_RETURN_20260728.zip`
State: **HOLD — do not launch After Effects until the user explicitly releases this retry**

Immutable SHA-256 identities:

- original r1 request:
  `809c3760c4e5b1f96e6747f2e9188435b3f2caaca6f229cf0ba061384cbc84ab`
- previous owner final return:
  `55527907af0b66d823d1ca9040c5a037f74d5bc96054c19503661d6b79ff06cc`

## Purpose

Continue the existing three-job owner batch on Windows. Do not ask the user to
carry per-job or per-attempt ZIP files between machines. Repair and test all
three Windows-local runners, retain every attempt locally, and return exactly
one consolidated terminal ZIP after all three jobs have reached `answered` or
`exact_bind_failure`.

This addendum does not reopen already exact OLM slices and does not authorize
Mac, AEXCompat, installed-plugin, preference, cache, modal-dialog, or unrelated
repository work. CLI agreement is diagnostic only and is not AE exact.

## Intake status of the previous final return

The previous archive is not admissible evidence and must remain immutable:

- Its three owner summaries all report `exact_bind_failure`.
- The owner summaries contain an incorrect stated original-request digest
  beginning `809c376e...`; the immutable r1 request actually hashes to the
  `809c3760...` value above. Preserve this as a diagnosed provenance failure
  and use the exact immutable bytes for the next request binding.
- The canonical Mac validator rejects `BATCH_RETURN.json` because it begins
  with a UTF-8 BOM. All JSON members in the next return must be strict UTF-8
  without BOM, duplicate keys, comments, `NaN`, or `Infinity`.
- Do not sanitize or relabel the previous archive. Build the next return from
  new run-specific Windows-local attempts.
- The next return must include the direct evidence files themselves, not only
  filenames and hashes printed in wrapper stdout.

## Job 1 — OLMRadialBlur case_0010

The prior attempt 3 is the only useful chronology. It bound owned AfterFX PID
`34200` and observed both required typed event kinds in the same run, but CDB
did not exit. The outer return therefore omitted the trace contents and the
complete same-run artifact set. Event counts alone do not disclose or prove the
raw cells or sampler word.

Make the smallest debugger-lifecycle repair first:

1. At the second/terminal sampler event, flush the log and use CDB `qd`
   (quit and detach) rather than waiting for incidental debugger exit.
2. Preserve the exact installed AEX path/SHA, owned PID, run ID, coordinates,
   RVAs, typed raw words, retained input, and rendered-artifact bindings.
3. Require a clean CDB exit/detach record before accepting the child.
4. Include the actual CDB trace, parsed direct-event record, raw evidence
   artifact, AE result, and render artifact as direct child members.

Do not infer final writeback, exported-pixel causality, CLI exactness, or AE
exactness from this upstream/sampler witness.

## Job 2 — OLMDirectionalBlur target writer

The prior attempt 3 reached a hardware watch at
`OLMDirectionalBlur+0x6bc7`, then CDB surfaced
`STATUS_SINGLE_STEP (0x80000004)` at the prompt instead of executing the nested
`ba` command. Consequently no `DBR_TARGET_STORE`, four-byte store artifact, or
complete same-run PNG exists. `DBR_TARGET_ARM` and the exception address are
diagnostic provenance, not direct store evidence.

Make a CDB-template-only repair first:

1. When arming the data breakpoint, record the debugger thread identity,
   hardware-breakpoint ID/slot, and exact watched output address.
2. Install an explicit handler for exception `0x80000004`. Accept it only when
   RIP is `writer_entry+0x97` (`+0x6bc7`), the current thread equals the
   recorded arming thread, DR6 identifies the recorded hardware-breakpoint
   slot, and the slot remains bound to the recorded target address.
3. Nonmatching single-step exceptions must continue unchanged and must not
   emit evidence. For an accepted event, clear the exact armed breakpoint
   before capture/exit, capture the four post-store PF8 bytes, emit the
   manifest-bound `DBR_TARGET_STORE` record, flush the log, and detach/quit.
4. Let the same owned AE process finish the PNG and require the existing
   same-run result/artifact checks.
5. If the exception-command form is not reliable in local CDB parse/smoke
   tests, use a thread-scoped execution breakpoint at `+0x6bc7` only after its
   exact CDB syntax and thread filter pass a Windows-local dry run. Retain the
   saved output-address and armed-state gates; do not broaden the capture to
   unrelated stores.

The child remains limited to the declared coordinate `(494,169)` and raw target
writer/store plus same-run artifact presence. It does not prove whole-plugin or
AE exactness.

## Job 3 — OLMDistanceGradation PF16 boundary

The previous return proves only `typed_hit_count == 0`. Its entry breakpoint
silently continued unless `EDX == 438 && R8D == 0`, so it cannot distinguish
wrong coordinate/register assumptions from a wrong RVA or alternate PF16/smart
render dispatch. The loaded module path/base/SHA checks make a stale or wrong
AEX less likely, but do not prove that the contracted callback executed.

Add one bounded diagnostic layer before changing the AEX, cache policy, or
algorithm:

1. At RVA `0x1170480`, count raw entry hits before applying any coordinate
   filter.
2. On the first raw hit, record RIP, RCX, RDX, R8, R9, relevant stack slots
   including `poi(RSP+0x20)`, `poi(RSP+0x28)`, and `poi(RSP+0x30)`, plus a
   bounded stack trace.
3. Preserve the existing typed condition and report
   `raw_entry_hit_count` separately from `typed_hit_count`.
4. Before continuing, include bounded `u`, `!address`, and `lmvm` evidence for
   the resolved absolute address and exact loaded module.
5. Interpret one terminal run as follows:
   - raw entry count greater than zero with typed count zero: repair the
     coordinate/register contract;
   - raw entry count zero with a completed render: inspect the actual
     PF16/smart-render dispatch and grounded callback RVA.

Do not treat PNG export, a completed JSX call, or a zero typed count as a PF16
boundary answer.

## Windows-local construction and safety

1. Before patching, prove that the complete original consolidated request
   batch, all three original child payloads, and the complete prior
   Windows-local source/run roots still exist and match their recorded hashes.
   The returned final ZIP alone is insufficient to reconstruct them. If any
   are absent, stop before AE and request the one original consolidated r1
   batch again; never reconstruct a request from the inadmissible return.
2. Work from immutable copies of the proven prior request and return in a new
   local run root.
3. Patch Windows-local sources and preserve unified diffs, full patched files,
   hashes, test commands, stdout/stderr, and exit codes.
4. Run PowerShell parse tests and supplied Python/package smoke tests without
   AE before the HOLD gate.
5. After explicit user release, run the jobs sequentially. A failure in one
   job must not prevent collection of the later jobs.
6. Retry locally when a bounded runner/debugger repair remains. Preserve failed
   attempts; never edit failure evidence into success.
7. Never automate, dismiss, answer, or toggle modal dialogs.
8. Do not change Adobe preferences or delete caches. Do not broadly kill Adobe
   processes. Cleanup may target only a uniquely owned PID after exact identity
   revalidation; ambiguity must fail closed without termination.

## One-return contract

Return exactly one ZIP after all three jobs are terminal.

The archive must:

- use strict UTF-8 JSON without BOM;
- preserve immutable request manifest/return-contract bytes exactly;
- contain a non-circular `CHECKSUMS.sha256` covering every other member exactly
  once;
- contain each required job exactly once;
- include actual direct evidence files as direct job members;
- bind every accepted observation to the same request, run, owned AE PID,
  installed and loaded AEX path/base/SHA, project/case, renderer, bit depth,
  source, and artifact identities;
- classify a child as `answered` only when its complete same-run contract is
  present and internally consistent;
- otherwise classify it as `exact_bind_failure` with the precise terminal
  stage and reason.

Parent status is `answered` only when all three children are answered,
`partial_success` when at least one is answered and one fails, and
`exact_bind_failure` when none are answered. No child or parent status may be
rounded upward because a breakpoint armed, an event count was nonzero, a PNG
existed, or a wrapper exited zero.
