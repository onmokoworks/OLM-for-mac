# Windows runtime returns fail-closed intake (2026-07-13)

## Decision

All five returned archives are retained, but none is promoted to runtime or
algorithm proof. Each return explicitly reports a bind/launch failure and is
therefore classified fail-closed.

## Returns

| Request | Status | Failure boundary | SHA-256 |
| --- | --- | --- | --- |
| OLMDirectionalBlur row 755 | `exact_bind_failure` | `ae_pause`: ready marker not written | `86dc83105e04cf8c9d7240aa088e2dc873ea0533dde34e88263465853c7048b3` |
| OLMSmoother2 case 0012 live config | `exact_bind_failure` | `bind`: module/base and c280/cce0/writer hooks unresolved | `6979b0cb3bf1b44e1678aa2bb9242eb808c68e0d0db35e16b4aa660ca8dc6d51` |
| OLMDistanceGradation case 0026 live field/source | `exact_bind_failure` | `typed_capture`: zero typed records and no same-run identity | `e8724dca9cf409c67294462e6a1824c7f1f8c8b1391a7493211dc4ea436cbb3a` |
| OLMDistanceGradation 8bpc typed boundary | `exact_bind_failure` | `typed_boundary`: no marker at `(397,281)` for cases 0001/0015/0029 and no shared run/AEX identity | `e3e42ba54f2f4aac0771b9c72ee796a5364c0623c58f3092f950de38addb4d9d` |
| OLMKiraKira Mode 3 live Gaussian | `exact_bind_failure` | `ae_ready`: ready marker timed out before CDB started | `0ea9380047ed7dd1e5d154b0f1f8fa35d76ae14976cdb0e9e5b4d826bf03b1f7` |

The retained archives are under `refs/windows_returns/20260713/` with their
original returned filenames. These failures contain no pixel or intermediate
value that may be used to tune production code.

The two later returns are currently retained in the NAS exchange area. The
hashes above are the stable intake identity; moving an archive between `new`
and `old` does not change its classification.

## Next action

Do not resend the same unattended SSH/session-0 path. AE-dependent runners
must start from the logged-in Windows desktop. Before CDB attaches, require a
fresh run marker, module path/base, and the request's ready marker; abort the
trace if any prerequisite is absent.

For the DistanceGradation retry, prove hook liveness before requiring the
three typed coordinate markers. For the KiraKira retry, make AE readiness a
separate preflight and do not report a Gaussian classification unless CDB
captured all 21 coefficient words in the same hash-pinned run.
