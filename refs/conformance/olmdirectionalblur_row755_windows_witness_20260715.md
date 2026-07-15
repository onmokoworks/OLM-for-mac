# OLMDirectionalBlur row755 Windows witness conformance note

Date: 2026-07-15

The Windows witness request remains the narrow angle-0 row755 case. Production
evidence observed `row_end=2176`; the request now requires that value in the
same run as rowdriver coverage and the single pre-normalization capture.

That capture binds destination RGBA float32, denominator float32, and alpha/
valid float32 state together, with address arithmetic and byte counts checked
for all three typed exports. The CDB probe refuses to capture unless the
observed maximum row end is 2176. The stride remains 2206 because it is the
row stride, not the row-driver end.

The smoke fixture rejects row-end drift, missing typed-state fields, address or
identity drift, incomplete rowdriver coverage, missing artifacts, and a
`DBR_BIND_FAILURE`-only trace. No diagonal, variation, or algorithm-source
claim is introduced by this package.
