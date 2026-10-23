# Configurable resident Smart capture (F46 arithmetic)

`build_C53b.py` verifies the retained F49-v2 source manifest, copies it to
`~/.cache/olm-emu/src-C53b`, applies the adjacent patch, checks at least 30%
free memory, and builds offline/locked with one job. Build files live in the
space-free `~/.cache/olm-emu/build-C53b` and are deleted even on Cargo failure.
The worker and manifest are installed in `~/.cache/olm-emu/worker-C53b-trace`
and registered under the shared INDEX lock. `--rebuild` replaces only this
recipe's own hash-verified source/binary. It is not needed for replay.

The only changes from F49-v2 are resident watch configuration and a 16 MiB
read-only snapshot limit. No math, imports, guest memory writes, or host fixture
behavior changes. This supersedes the F49-specific environment variables on
this worker only.

Set `AEXCOMPAT_RESIDENT_TRACE` to the output JSON file and
`AEXCOMPAT_RESIDENT_WATCHES` to a JSON array file before starting a raw session:

```json
[
  {"id":"polar", "function_rva":45392, "register":"rdx", "size":2361600, "occurrence":1},
  {"id":"accum", "instruction_rva":23578, "register":"rcx", "dereference_offset":16912, "size":2361600, "occurrence":1}
]
```

Addresses and sizes are JSON integers (decimal, relative to the module base).
Exactly one of `function_rva` and `instruction_rva` is required. The latter
names a **direct call instruction**, not an arbitrary instruction. The existing
checkpoint engine reports unsupported indirect/tail-call sites explicitly in
`trace_configuration.unhookable_watches`; this patch does not extend that engine.
Both the before-call and after-return snapshots use the original captured pointer.
`dereference_offset` reads a pointer from register + offset, including offsets
larger than 4096 required by Radial's worker context. It is not a byte slice offset.

Supported registers: `rcx`, `rdx`, `r8`, `r9`, `rax`, `stack5`..`stack8`.
`size` is 1..16777216 bytes; 1..64 watches are accepted. Omit `occurrence` to
capture all occurrences (existing witness-count limits still apply). Zero
occurrence, invalid registers/sizes or missing/ambiguous RVA selectors, unknown fields, and invalid JSON
fail explicitly. Only `SMART_RENDER` is captured; other selectors are unchanged.

Trace files are diagnostics. Require input hashes and complete output hashes
to match a retained untraced original before using a captured arithmetic value.
See `probe_radialblur_c53b_trace.py` and the C53b report for this binding.
