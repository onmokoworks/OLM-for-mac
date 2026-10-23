# Original noise-table out-of-bounds reads (C45)

The user-approved Mac contract returns **positive `0.0f` for each noise-table
read outside `[0, 101)`**. A valid interpolation endpoint is still read normally.
The allocation remains 101 floats (404 bytes); indices are neither clamped nor
wrapped at the lower bound. All unrelated admission guards remain in place.

| Plugin | Original read RVAs | Trigger |
|---|---|---|
| OLMDirectionalBlur | `0x37f3`, `0x37f8` | Negative normalized Noise Offset can produce a negative signed index after upper-only wrapping. |
| OLMRadialBlur | `0x95cd`, `0x95d8` | The noise generator likewise permits negative signed table indices. |

FACT: Prior C18/C25/C36 and C11/C44 investigations establish the invalid
allocation-relative reads. C45 does not reinterpret adjacent heap bytes as
part of the table or claim native Windows output is defined there. Its public
AEX comparisons use the default F46 Unicorn worker; final-output equality is
not a new memory-read trace.

The C45 report records seed 1 and two fresh n300 campaigns for each plugin.
Exact witnesses, with full parameters, input hashes and before/after provenance,
are `tests/fuzz_corpus/{olmdirectionalblur,radialblur}/C45_*.json`.

Non-comparable exceptions: **none recorded by C45**. No Smart output mismatch
was observed in those campaigns, so no mismatch is excused as a non-zero heap
read. Any future exception requires the actual out-of-range address, read RVA,
non-zero bytes, parameters and oracle identity; output disagreement alone is
insufficient evidence. Historical Classic-route discrepancies are separate
and are not classified as this original bug.

INFERENCE: Deterministic zero semantics remove allocator dependence in the
port. Passing finite emulation campaigns does not establish equality to every
native Windows heap layout or exhaustive parameter coverage.

## RadialBlur Type 3 with zero Noise Variation and no layer (C46)

The deterministic Mac contract initializes the **scatter span to positive
zero** when Noise Type is 3 and Noise Variation is zero (no layer checkout).
The size-factor plane remains separate: Zoom's B150 prepass uses its sampled
size factor when enabled, and literal one when disabled. Rotation likewise
retains its existing size-factor prepass. This is not a neutral procedural
noise substitution and does not change positive-amount layer checkout errors.

FACT: Original `FUN_1800065c0` skips the span writes when Type 3's layer
pointer at owner +0xA8 is null. `FUN_1800045a0` allocates handle storage without
explicit initialization. C17 established this allocation boundary. C46's F46
trace of the committed 7x1 PF8 fixture compares 4096-byte prefixes: polar and
scatter span match, but substituting the zero scatter span for the prepass
factor differs in 442/1024 floats (first AEX 1.0, candidate 0.0). Keeping the
size plane separately makes all three prefixes equal and the public output
exact. Prefix equality is not a claim of a complete intermediate-plane trace.

FACT: The independent C46 matrix's AEX-rendered cases and seed campaigns have
no admitted Smart mismatches with the final rule. Some Type-3 matrix inputs
make the original emulator stop with an invalid memory write; those are
uncompared, not evidence of exactness or a diagnosed non-zero allocation.
See `orchestra/reports/C46-radial-smart-r8.md` and its bound evidence.

INFERENCE: Zero initialization removes dependence on uninitialized allocation
contents, consistent with observed emulator values. Native Windows allocator
contents remain undefined; no native Windows/AE parity is claimed for this bug.
