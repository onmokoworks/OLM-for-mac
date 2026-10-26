depends: F54c-aexcompat-resident-watches
# N03b: RadialBlur realistic-v2 mismatches: trace with F54c resident watches and fix

## Facts
- `orchestra/reports/N03-radialblur-v2-mismatch.md`: the divergence is first observed in the pre-B150 polar plane (the complete PF16 plane, and a PF32 prefix). The earlier source/sampling stages could not be watched with F54b.
- F54c adds C53b-style resident watches (pointer dereference, full planes) that work with cropped geometry: `~/.cache/olm-emu/worker-F54c/`.

## Do
Do what `orchestra/tickets/N03-radialblur-v2-mismatch.md` asks, using F54c:
- capture the source/sampling stages before B150 for both witnesses;
- find the first differing value and its cause (likely how the cropped checkout origin or extent enters the polar sampling);
- fix it in the general path.
The acceptance criteria are the same as in N03.

## Rules
- Use 1-2 processes. Change only RadialBlur sources. Do not touch the release gate or ledger. The stop rule applies.
