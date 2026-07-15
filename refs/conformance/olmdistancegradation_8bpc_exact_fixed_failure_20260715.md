# OLMDistanceGradation 8bpc Exact-Coordinate Return

- Status: `accepted_exact_bind_failure`
- Classification: `target-coordinate-not-observed-and-aex-hash-unbound`
- Request satisfied: no
- Algorithm evidence: no
- Source ZIP SHA-256: `ccc11da41921d37edd529a29becdaf29eabdda14b6fbb74cbc92394a1dd9fbe5`

## Facts

- AE 25.2 rendered all three named cases successfully at 8bpc with working space None and linear blending disabled.
- CDB armed absolute PF8 and PF32 callback breakpoints and continued execution.
- The PF8 entry condition EDX=397 and R8D=281 emitted no target marker.
- The return does not retain an AEX SHA-256 or a complete typed field/compose/store chain.

## Boundary

- Static callback ABI evidence identifies EDX/R8D as x/y at PF8 entry, but this return cannot decide whether AE skipped the target through its iterate ROI or whether host coordinate mapping differs.
- A broad coordinate-liveness census is required before another exact-coordinate capture.

## Next Action

run a hash-pinned PF8 coordinate-liveness census for the same three cases; collect total/min/max/first hits, target-neighborhood hits, output pointers, PF32 count, and same-run identity
