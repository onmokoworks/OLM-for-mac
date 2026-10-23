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
