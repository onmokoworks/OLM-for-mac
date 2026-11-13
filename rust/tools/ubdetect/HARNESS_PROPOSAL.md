# Proposed AEXCompat fill controls (not implemented in AEXCompat)

The request renderer used by oracle does not expose a common fill-pattern
contract for world padding, unused parameter storage, arbitrary handles, or all
host-suite allocations. This job does **not** modify AEXCompat. It continues
through record's debugger, with fresh owned workers for every trial.

Observed current host source:

* `minihost/src/worker_handle_runtime.cpp:99` clears fresh PF handles; its resize
  path at 222–223 clears replacement storage and copies old data. Other memory
  blocks at 293 use `0xcd` when clearing was not requested.
* `minihost/src/worker_world_registry.cpp:197–198` initializes allocated pixels
  to zero or `0xcd` and clears the descriptor. The Windows x64 layout at
  205–210 puts data at +24, rowbytes +32, width +36, height +40.
* Oracle request cases materialize packed PNG worlds. Fixture-v2 padding/layout
  controls are a different route and are not combined with oracle request
  downsample/context semantics by this tool.

Propose an **explicit diagnostic-only**, per-worker request object:

```json
{"diagnostics":{"memory_fill":{
  "pattern_hex":"3f3f3f3f",
  "world_padding":true,
  "fresh_output_pixels":true,
  "parameter_unused_storage":true,
  "fresh_nonclear_handles":true,
  "fresh_nonclear_suite_allocations":true
}}}
```

Apply fills before copying initialized values. Input and secondary active pixel
bytes, initialized parameter members, handle metadata, pointers, function
pointers, and allocator metadata must remain intact. Param unions require
type-specific masks: mutating the entire param record is not a valid experiment.
Custom arbitrary-data payloads require callback/lifetime knowledge; do not
overwrite an initialized gradient and call its changed output an undefined read.
Honor clear/zero allocation flags and calloc semantics. On resize, poison only
new uninitialized capacity, then preserve the existing logical payload. Never
poison freed storage. Supply padded worlds without altering their active pixels.

Record logical allocation IDs, suite/selector, size, fill range, initialized
mask, pattern, zeroing flags, before/after hashes, and guard verification. A
read-only log of matched lifetimes would let a debugger establish bounds for
new plug-ins without guessing from registers. Every selected scope must report
`applied`, `not_present`, or `unsupported`; silent omission is unacceptable.

Acceptance checks: unchanged active inputs and params across patterns; untouched
defaults preserved; exact known initialized renderers at 8/16/32 bpc; an
intentional unwritten output/padding/handle read detected separately in each
scope; failed or interrupted renders retain logs and private-job cleanup.

## Implemented debugger fallback and remaining coverage

`world_padding` hooks fill only `[data+y*rowbytes+width*pixel_bytes,
data+(y+1)*rowbytes)` for explicit ABI layouts. This works for primary, output,
or secondary worlds once a profile identifies their pointers. `span` with
bounded pointer dereferences supports known unused param/handle bytes.
`allocation` hooks fill a bounded fresh pointer return from a known allocator;
they do not infer realloc/calloc signatures or handle-to-data conversions.
Unit tests exercise all three mechanisms, including active-byte preservation.

Real original coverage here includes the Radial PF Handle Suite's freshly
locked 1,860-byte noise plane and 404-byte table, filled at the plug-in's
post-lock sites. Both patterns render identically with Offset zero. Known
Distance uninitialized stack fields and both blur heap-table underreads are
separately proven by real poison differentials. **No real arbitrary-data,
parameter-unused-byte or padded-secondary-world campaign is claimed.** Those
remain unsupported automatically without additional reviewed profiles or the
host facility above. This proposal is a coverage boundary, not a silent claim
that every memory class has been poisoned.
