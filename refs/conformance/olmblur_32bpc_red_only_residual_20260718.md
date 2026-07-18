# OLMBlur 32bpc red-only residual audit (2026-07-18)

## Verdict

The residual is **not evidence of a red-channel mapping bug**. The case input
contains signal only in red (`R=31812`
nonzero values; `G=B=0`), so an algorithm difference can only appear in red.

The current Mac effect EXR is byte-for-byte the output of the current portable
PF32 core for the full 1920x1080 host input. A bounded current-AEX execution at
the exact tuple `(129.4, 100, repeat=1, bias=1, Legacy=0)` is also byte-exact
with that core.

## Facts

- Windows/Mac no-op FLOAT32 planes: `{'A': 0, 'B': 0, 'G': 0, 'R': 0}`.
- Windows/Mac effect mismatches: `{'A': 0, 'B': 0, 'G': 0, 'R': 201576}`.
- Full Mac effect equals current core: `True`.
- Full current core versus retained Windows effect: `201576` mismatched float words.
- Bounded current AEX repeat=1 equals current core: `True`.
- Pinned actual AEX SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.

## Hypothesis disposition

| hypothesis | result | reason |
| --- | --- | --- |
| channel mapping | rejected | no-op is exact, G/B remain zero, and diverse-ARGB actual-AEX fixtures already pass |
| source stride | rejected | full 1920x1080 current-core output equals the Mac EXR; padded-row adapter fixtures also pass |
| SIMD lane | rejected at the worker boundary for this tuple | bounded current AEX and portable core are byte-exact at repeat=1 |
| reference provenance | only live explanation | retained Windows EXR lacks loaded-AEX SHA and complete color/output attestations |

This does **not** prove that the retained Windows reference is wrong. It means
the current source must not be changed from this red-only artifact: all locally
testable implementation boundaries agree with the pinned current AEX, while the
Windows artifact cannot be bound to that AEX.

## Next evidence

Capture a same-run Windows effect/control FLOAT EXR pair with the loaded
OLMBlur AEX path/SHA-256 and complete working-space, linear-light, and output
module readback. `AE exact` remains unclaimed.
