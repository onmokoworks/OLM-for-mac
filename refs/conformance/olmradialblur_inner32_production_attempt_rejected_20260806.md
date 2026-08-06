# OLMRadialBlur PF16 Rotation Inner=32 production attempt — rejected

The bounded production attempt is **not production evidence** and was fully reverted.

The current portable two-stage path reached byte-exact final internal RGBA and padded PF16 output for the 9×7 fixture, but its required accumulation and max-alpha planes differed from the pinned actual-AEX planes. Both tested helper interpretations were rejected:

- backward angular scatter with next-radius-row underflow: accum `44fdb158…21d2`, max `a43f0297…67c1`;
- forward same-row scatter: accum `e9cb35df…264d`, max `1b7f9994…8a28`.

Actual-AEX expects accum `d12cf7c4…6364` and max `1753e637…4fa1`. Final-output agreement cannot promote either candidate because it does not preserve the captured internal contract. Nonzero Inner therefore remains fail-closed in production.

The remaining boundary is the per-call traversal and store behavior of `FUN_180001c90`. The companion discriminator records the first actual max-plane change and the state missing for a direct helper replay.
