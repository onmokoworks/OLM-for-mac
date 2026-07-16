# OLMColorKey Edge Thin Actual Caller 20260717

This report is a bounded Mac-local Unicorn execution of the hash-pinned Windows
PE. It invokes `FUN_180009000` and observes the native type-2 chain through
`0x180008AD0 -> 0x1800058A0 -> 0x180008320`.

The fixture is a `5x1` PF16 world. The stack edge record is pinned to
`+0x20=8, +0x24=1, +0x28=0, +0x2c=2, +0x40=-2.0f, +0x44=2, +0x48=2`.
The two runs use paired amounts `-1.0f` and `-3.0f`; the erode entry observes
those exact values in `XMM1`, proving caller forwarding for this bounded path.

Exact-address hooks observe the caller callsite `0x18000941D`,
`0x1800058A0` with `XMM3=4000.0f`, and `0x180008320`. Because `RDX` is volatile
across the distance helper, the harness explicitly binds it to the caller's
outgoing stack5 work world at `0x18000941D`. The ERODE hook then records raw
`R9`, `R8D`, `XMM1`, and stack5/6/7 before making any selected-world
repairs. The recorded `RDX` is explicitly named
`RDX_after_callsite_binding`; it is not presented as an untouched native
register value. Native stack/register observations and repaired values are
separate JSON objects.

The seam checks require bound `RDX==native stack5`,
native `R9==original R8/source`, native `stack7==original R9/matched`, and
native `stack6==the exact world passed to FUN_1800058A0`. After that
snapshot, the harness binds explicit source, matched, and sentinel destination
worlds before running native `FUN_180008320`. Distance bytes must remain
unchanged.

The retained output is only an observation of the native leaf after those
explicit repairs. Sentinel integrity and a fixture-pinned output byte pattern
are regression checks; no independent semantic oracle, threshold predicate,
or handle-allocation oracle is claimed here. Leaf semantics remain bounded by
the separate `olmcolorkey_edge_thin_erode_aex_20260717` evidence.

The harness fails closed on any missing native chain hit, raw ABI mismatch,
amount/control mismatch, distance mutation, native/repaired collapse, or
sentinel damage. This is not untouched full
caller-to-leaf execution. It is not an AE exact, threshold, full-host, PNG, or
general Edge Thin semantic claim.

Run:

```sh
python3 tools/emulation/probe_olmcolorkey_edge_thin_actual_caller_20260717.py \
  --json refs/conformance/olmcolorkey_edge_thin_actual_caller_20260717.json
python3 tools/emulation/test_olmcolorkey_edge_thin_actual_caller_20260717.py

python3 tools/emulation/probe_olmcolorkey_edge_thin_actual_caller_20260717.py \
  --json /tmp/olmcolorkey_edge_thin_actual_caller_run1.json
python3 tools/emulation/probe_olmcolorkey_edge_thin_actual_caller_20260717.py \
  --json /tmp/olmcolorkey_edge_thin_actual_caller_run2.json
diff -u /tmp/olmcolorkey_edge_thin_actual_caller_run1.json \
  /tmp/olmcolorkey_edge_thin_actual_caller_run2.json
```
