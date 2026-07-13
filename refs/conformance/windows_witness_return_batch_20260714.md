# Windows witness return batch: common launcher failure

Date: 2026-07-14

## Verdict

This batch is `answered_partial` at the transport level but contains no plugin
witness. All four returns fail closed at `cdb_launch` with the same missing
field: `cdb_bootstrap_exit`.

The diagnostics do show that AfterFX.exe was launched and observed by process
enumeration. They do not show the CDB bootstrap marker, queue bootstrap marker,
plugin load claim, typed capture, or render artifact. These returns must not
change any plugin correctness status.

## Returns

| Plugin/request | Return SHA-256 | Status | Evidence missing |
| --- | --- | --- | --- |
| OLMBlur case0006 | `9ab9ec0ca3ce0c75e8ab294af21fea5921f0dcaae0bec10d42777abe51425bee` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |
| OLMDirectionalBlur row755 | `15565688cf7aedc386ec49f867e94e40092290376021f0af8e1f2ca7ac0e62b5` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |
| OLMDistanceGradation case0026 | `2bf25d4e1f42eb7da821dcfa82085d7dd48d562485298ec0c87b07e9b790472c` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |
| OLMSmoother2 case0012 | `b0bdd40f04c50079d76a5b6de8c8e285da2fea40d89f1f67baca130532bb72a3` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |

## Observed common facts

- The launcher uses CDB with `-o -pd -g -G -cf boot.cdb`.
- The observed AfterFX command line is `AfterFX.exe -r queue.jsx`.
- `bootstrap_host_image_marker_observed=false`.
- `queue_bootstrap_marker_observed=false`.
- No returned artifact was produced.
- The same failure appears across four different plugins, so this batch cannot
  distinguish plugin behavior.

## Decision

Reopen the common Windows launcher gate. Do not send additional plugin witness
requests through this launcher until a minimal real-Windows gate observes both
the CDB bootstrap exit and the queue binding marker. The next fix must preserve
the archived CDB output and `boot.log` so a failed gate is diagnosable.

## Replacement gate sent

The launcher was changed locally to start `AfterFX.exe -r <queue>` directly
under CDB, leave the initial breakpoint enabled, emit an explicit initial-break
marker, and detach with `qd`. The old `cmd.exe` child wrapper and
`ld:AfterFX.exe` filter are no longer used.

The minimal gate package sent to Windows is
`windows_witness_launcher_gate_direct_afterfx_20260714.zip` with SHA-256
`703253f6507e68654a1984884ff81e3b40115cc6f455989b0ccc11ddf84c61d1`.
It reuses only the DG case0026 package as a launch vehicle; no DG algorithm
claim is made from this gate.
