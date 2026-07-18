# Windows Frida Entry-to-Core Batch 20260718

## Purpose

This batch replaces repeated downstream breakpoint discovery with one bounded
entry-to-core survey per unresolved plug-in lane. It does not establish AE
exactness. A hook hit is path evidence only.

## Request identity

- Package: `refs/runtime_trace_packages/windows_frida_entrypoint_batch_20260718.zip`
- SHA-256: `762dbeb0a97df015d86842f0a64ea7b2f81b46199ffa4298e693ee4f4b042df8`
- Transport: Frida Interceptor; no broad Stalker trace
- Host contract: fresh desktop AE process, Software renderer, hash-pinned AEX

The six lanes are OLMBlur 16bpc, OLMDirectionalBlur 8bpc,
OLMDistanceGradation 16bpc, OLMKiraKira 32bpc, OLMRadialBlur 8bpc, and
OLMSmoother2 8bpc. Each lane records up to 64 exported PF entry calls with a
direct `i32` command read. Evidence-backed internal hooks are bounded to one
hit and are optional because mode-specific paths may legitimately skip them.

## Acceptance

A lane is `answered` only when all of the following share one invocation:

- request ID and exact request-package identity;
- AE PID, loaded module base, module filename, and AEX SHA-256;
- Software renderer, declared bit depth, and case ID;
- one module-load event and at least one exported PF entry event;
- a typed `pf_cmd` read on the entry event;
- a successful AE render result and Frida completion after that result;
- no agent error, timeout, mixed identity, stale file, or cardinality failure.

Partial outer returns retain every lane's diagnostics but do not promote any
lane or supersede a narrower pending witness automatically. CDB remains the
next tool only for a Frida-selected callsite requiring instruction stepping,
register interpretation, or a write watchpoint.

## Local verification

- all 10 profile AEX hashes matched checked-in 2025 binaries;
- two independent batch builds produced byte-identical ZIPs;
- 46 Windows witness unit tests passed;
- the synthetic Windows witness smoke passed;
- generated package paths and embedded request IDs were inspected.

Windows execution is still required before this request yields runtime facts.
