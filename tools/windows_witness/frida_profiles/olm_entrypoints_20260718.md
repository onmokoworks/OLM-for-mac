# OLM Entrypoint Frida Profiles

Audit date: 2026-07-18. Scope is the ten checked-in `Plugins/64/2025/*.aex` files. The JSON is the machine-readable record; this note explains the evidence and the conservatism of the hook sets.

## Binary identity

All ten AEX files are PE32+ x86-64 DLLs. Their SHA-256 values and repository-relative paths are recorded in the JSON. PE export-table inspection found exactly one named export per file: the After Effects host entrypoint. No internal render function was treated as an export merely because it has a Ghidra name.

## Evidence rules

- `FACT` means directly observed in a checked-in PE table, decompilation/disassembly, or a named repository witness/contract.
- `INFERENCE` means an operational interpretation that remains useful for an initial hook set but is not promoted to a proven ABI or semantic name.
- `null` is reserved for facts not statically available. No absolute personal paths are included.
- The classic command numbers visible in the decompilations are retained as evidence, but the JSON does not pretend that a vtable slot is a resolved `Render` or `SmartRender` function.

## Plugin notes

- **OLMBlur:** the decompilation gives the exported dispatch and `FUN_18000a380`; witness reports name the Legacy, PF16 non-Legacy, and PF32 worker entries. The initial set covers dispatch and the three worker families.
- **OLMColorKeep:** the classic entry dispatch calls separate 8-bit and 16-bit callbacks, plus a command-`0x18` path. There is no checked-in statically named SmartRender target, so no fabricated one is listed.
- **OLMColorKey:** the C++ entry dispatch resolves an effect object and invokes vtable slots. The initial set uses the exported entry plus the directly evidenced edge orchestration, thin/erode, and blur helper addresses.
- **OLMDirectionalBlur:** `FUN_180007bd0` is the render owner named by the natural prerender evidence; `FUN_1800038d0`, `FUN_180001ec0`, and `FUN_180006700` are the rowdriver, rotate, and writer-side anchors used by the witness lane.
- **OLMDistanceGradation:** the entry calls `FUN_181173720`; the fieldgen, PF16 wrapper, and compose/writeback addresses are separately grounded by the actual-AEX witness artifacts.
- **OLMKiraKira:** the object-vtable Render/SmartRender targets are unresolved. Mode-2 compose and the Mode-3 Gaussian body are conservative core hooks. The evidenced `0x126685c` Gaussian return address remains in the fact table but is excluded from `initial_frida_hooks`; it is not a function entry.
- **OLMRadialBlur:** the static/render reports directly name the rotation entry, scatter caller, normalization, sampler, and worker boundaries. These are high-signal staged hooks, not a claim that every render mode follows the same path.
- **OLMSmoother2AE:** the object-vtable targets remain unresolved; the producer, typed compose, natural caller, classifier, cardinal dispatcher, and typed helper are directly named by the witness artifacts.
- **OLMSmootherAE:** the classic command-`0xb` render path and its 8-bit/16-bit dispatch cores are statically available. No SmartRender target is resolved in the checked-in evidence.
- **OLMToonDilate:** the entry and effect setup/callback addresses are statically available. The `FUN_180006498` label is marked `INFERENCE` and intentionally excluded from the initial hook set because the witness does not establish it as the production render entry.

## Frida use

Each `initial_frida_hooks` list contains RVAs, to be added to the loaded module base at runtime. Start with entrypoint and dispatch hooks, then enable deeper core hooks only when the run contract supplies the corresponding pixel format and buffer layout. The lists avoid broad function-range tracing and avoid unresolved vtable-slot guesses.

## Validation

The companion JSON was validated with Python's standard `json` parser after creation.
