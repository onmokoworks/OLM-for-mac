# Binary-bound memory contracts

Profiles bind SHA-256, route and exact instruction bytes. The automatic set is
`distance.json`, `directional.json`, `radial.json`. `radial-host.json` is selected
explicitly to isolate host-suite allocations from underread interventions.
These are reviewed layouts, not a name-based blacklist or a negative-offset
rule. New binary hashes require new inspection; they do not inherit old RVAs.

## Static grounds and dynamic checks

* Distance: `.codex-jobs/A-diag/report.md` §3. EffectMain RVA `0x1174bd0`
  allocates 0x660 stack bytes. The classic8 branch starts at `0x1174dfd`;
  refcon lives at RSP+0x1b0. The probe fills its previously unwritten +0x18
  through +0xc3, before the branch initializes +0/+8/+0x10/+0xc4/+0xdc.
  Saved registers, return address, cookie and initialized pointer fields are
  excluded. The callback reads +0x90 at `0x117087d`, +0xc0 at `0x1170895`, and
  background floats at +0xac/+0xb0/+0xb4. These are unused-classic-route
  observations; SmartFX is AE's declared route for this plug-in.
* Directional: generator RVA `0x34e0` writes owner+0x20=100 at `0x357f`,
  allocates 101 floats, and fills them. At `0x37e4` it sign-extends the
  truncated index into RCX; `0x37e7` loads the table pointer into RAX.
  `0x37f3` reads `[RAX+RCX*4]`; `0x37f8` reads `[RAX+RCX*4+4]`.
* Radial: generator RVA `0x9380` sets owner+0x20=100 at `0x93ed`, increments
  the allocation count at `0x9449`, allocates via `0x9970`, and locks via
  `0x98d0`. Loop `0x94d0..0x94f8` initializes all 101 floats.
  `0x95a4` sign-extends the index, `0x95ab` loads the table pointer, and
  `0x95cd` / `0x95d8` read the right / left endpoint respectively.

Disassembly was inspected from the exact local PE files using pefile/capstone.
No original binary was copied or changed. `core/dblur_noise.h` and the supplied
Directional/Radial reports independently describe this 101-entry contract.

Each read hook computes the signed effective endpoint independently; index -1
has a valid right endpoint 0. Valid elements are never changed. Only the four
bytes of an observed invalid operand are replaced. `RestoringDebugger` restores
the original bytes at record's INT3 reinsertion point after single-stepping,
while other threads are still suspended. The event records `restored:true`;
failed restoration is incomplete evidence. The original instruction executes
unchanged, rather than substituting a calculated result in a register.

Default patterns are repeated `00` and `3f`: finite f32 zero and approximately
0.747. Both also distinguish the classic byte-valued branch fields. Users may
provide other 1–16-byte patterns, but crashes/timeouts remain inconclusive.

## Extending a profile

Every hook has `name`, hex `rva`, exact `instruction`, `kind`, and a `basis`
explaining ownership, lifetime and which bytes may be changed. Set
`undefined_contract:true` only when that argument is established; arbitrary
mutation of an initialized input is not UB evidence. False contracts produce
false conclusions; the tool cannot infer C++ object lifetimes from raw bytes.

Address expressions contain `reg`, optional `deref` offsets (each loads a
64-bit pointer), and a final `offset`. Size expressions are nonnegative byte
counts, signed 32-bit fields addressed by an expression, or `{ "mul": [...] }`.
Each span and total bytes written are bounded at 16 MiB. At most 10,000 hook
events are accepted; exceeding a budget aborts the owned worker and makes the
classification inconclusive, never a truncated success.

Kinds:

* `span`: `address`, `size`. Suitable for reviewed stack regions, unused param
  fields, arbitrary-handle storage before initialization, or fresh locked
  host-suite buffers. Pointer values themselves are not blindly poisoned.
* `world_padding`: `address` of a world, `pixel_bytes`, and explicit `layout`
  offsets for `data`, `rowbytes`, `width`, `height`. Supports primary/output/
  secondary worlds; only positive strides are currently accepted.
* `allocation`: known allocator entry, `size_reg`, optional `size_scale`.
  The matched thread/RSP return supplies RAX. Null is logged and not written.
* `oob_read`: `table` address, signed `index_reg`, optional `index_add`, `count`.
  Currently four-byte elements; the original read address and index are logged
  even in read-only observer mode. Out-of-bounds events are direct evidence
  under the binary-bound object contract.

The instruction hooks use record's existing debugger API, including its return
matching and thread suspension. Changes to that API require rerunning the
restoration test and the real qualification suite.
