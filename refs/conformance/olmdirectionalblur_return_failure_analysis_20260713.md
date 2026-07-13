# OLMDirectionalBlur return failure analysis (2026-07-13)

## FACT

- `20260713_083933...quoted_jsx_ae_pause.zip` stopped before any JSX log or
  ready marker. It does not identify an AEX or row755 failure.
- `20260713_091000...nospace_jsx_cdb_syntax.zip` proves the no-space JSX path,
  AE 2025 case setup, pause handshake, exact AEX hash, PID/module base, CDB
  attach, and breakpoint arming. Its CDB log then reports `Malformed string`
  for the oversized `+0x5554` command and `Numeric expression missing` for
  `&&`; no row plane was captured.
- The later desktop and `095200` runners replaced the 21 inline writes with a
  nested CDB script, but their only material launch difference is
  `-ArgumentList @('-m','-r',$jsxLaunch)` versus one prejoined string. Both
  returned `ae_pause` without `ae_render.log`; `return_01...zip` also records a
  separate invocation where `$PSScriptRoot` was empty during parameter-default
  evaluation.
- The current common launcher serializes Windows arguments itself, launches
  AE through a CDB-tracked `cmd.exe` wrapper, and requires an atomic queue
  bootstrap marker bound to run ID, work/package roots, queue SHA-256, desktop
  session, and the same AE PID. The existing standalone package
  `refs/runtime_trace_packages/windows_witness_olmdirectionalblur_row755_20260713.zip`
  contains the same launcher bytes as commit `a6730b53` (launcher SHA-256
  `ffb9150712372d4d2f5d8d5882b088ff85949975097f6d8d117d7c3ca922bd06`).
- The older batch member
  `windows_witness_batch_20260713/jobs/005_olmdirectionalblur_row755_20260713.zip`
  contains a different, stale launcher (SHA-256
  `9804050e5626465f30f970f7fca9014a84a6bf546cbdcd89fc10a1566ae84a25`).
- The worktree legacy runner's newly added strict marker regex expects three
  separate lines, while its JSX writes one line beginning `ready case_id=...`.
  That runner would reject a valid marker after launch; the common launcher
  uses compatible substring checks.

## INFERENCE

- There are two independent failure classes: the answered no-space startup
  experiment failed in legacy CDB synthesis, while later `ae_pause` returns
  failed in the invocation/launcher path before the corrected nested CDB could
  be exercised. Neither is evidence against the requested runtime addresses.
- More quoting changes to the legacy runner are low-value: PowerShell 5.1
  `Start-Process -ArgumentList` flattening and external relay invocation have
  already produced contradictory outcomes. The common launcher's bootstrap
  evidence is the minimum useful discriminator for the next run.

## Next request

Do not resend either legacy row755 package or batch job `005`. Run the existing
standalone common-launcher package above from a logged-in interactive Windows
desktop with AE fully closed. Pin the package ZIP SHA-256 to
`99f78ae835a2786b9bcb3ccd7914bb6ccaa917353d5a460bfe384036f4a99c4b`.
Require the generated return ZIP even on failure, including
`afterfx_process_diagnostics.json`, bootstrap CDB script/trace, launch wrapper,
launched queue JSX, `queue_bootstrap.log`, ready marker, resolved probe, CDB
stdout/stderr/trace, AE log/result, and validation status. Classify failure at
the first missing gate (`cdb_launch`, `cdb_child_tracking`, `jsx_launch`,
`queue_binding`, `readiness`, `desktop_process_discovery`, `cdb_arm`, or
`cdb_capture`) rather than reporting generic `ae_pause`.
