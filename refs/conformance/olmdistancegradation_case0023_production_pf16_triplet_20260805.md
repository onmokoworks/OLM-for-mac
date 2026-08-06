# OLMDistanceGradation case0023 production PF16 triplet

- Status: `exact`
- Scope: retained actual-AEX `FUN_181170480` compose/store fixture versus the Mac production PF16 compose/store leaf.
- AEX identity: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.

The production PF16 scanline now calls a named `compose_pf16_pixel` leaf that contains the same `compose_pixel` and truncating PF16 store operations previously inlined in the loop. The focused harness reads and hash-checks the retained case0023 field world, relocatable refcon scalars, and actual-AEX output triplet.

Exact words in AEX memory order `A,G,R,B`:

- `(414,393)`, field `0.0`: `32768,0,3598,30583`
- `(415,393)`, field `1.0`: `32768,0,32768,0`
- `(416,393)`, field `1.0`: `32768,0,32768,0`

Focused command:

```text
python3 tools/emulation/test_olmdistancegradation_case0023_triplet_production_20260805.py
```

The same-shape production harness and existing PF16 fail-closed boundary test also pass. This proves only the three injected typed compose/store points. It does not prove field generation, host staging, export promotion, full-frame equality, or AE exactness. No AEXCompat change was required.
