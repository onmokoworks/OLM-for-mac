# OLMBlur Helper CPU Fixture - 2026-07-10

## Verdict

The portable AE-free helper in `core/olmblur_helper.cpp` matches the actual
Windows AEX functions `FUN_180001000` and `FUN_180001980` byte-for-byte for six
typed function fixtures.

| Fixture | Direction | Covered rule | Exact bytes |
| --- | --- | --- | ---: |
| `basic` | horizontal | ordered weighted traversal | `60` |
| `inactive_copy` | horizontal | inactive center copies source | `36` |
| `direction_break` | horizontal | first inactive flag stops one side | `60` |
| `edge_radius_clamp` | horizontal | radius exceeds edge extent | `24` |
| `zero_denominator` | horizontal | positive-zero output | `36` |
| `nonzero_offset` | vertical | column offset and pass count | `180` |

## Binary-grounded correction

An earlier prose audit described the center as excluded. The AEX decompile and
the exact fixtures instead prove that an active center participates with
`weights[0]`; right/bottom neighbors then use `weights[d]`. An inactive center
takes the source-copy branch.

The core is compiled with floating-point contraction disabled. Accumulators and
operation order remain float32/SSE-style.

## Verification

```bash
python3 refs/scripts/smoke_olmblur_cpu_fixture.py
```

The smoke regenerates all six fixtures through the actual AEX, compiles the
portable C++ replay, compares every output byte, and verifies the deterministic
readiness record.

## Boundary

This is function-scope `binary-grounded` exactness. It does not establish the
full worker `FUN_180005f20` host-buffer/PF Handle contract, case_0006 output, or
Mac AE exactness.
