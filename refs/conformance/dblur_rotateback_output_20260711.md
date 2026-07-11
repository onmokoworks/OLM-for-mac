# DirectionalBlur rotate-back output investigation

- Status: `bounded_helper_only`
- Binary: `plugins_2025/OLMDirectionalBlur.aex`
- Full `FUN_180004a20` render: blocked by the missing 8bpc host callback/world fixture.

## ABI and ownership

At `0x180005628`, the actual call is:

```text
RCX = RSI                         source RGBA float buffer B
RDX = R15                         destination RGBA float buffer A
R8D = dword ptr [RBX+0x80a0]      width
R9D = dword ptr [RBX+0x80a4]      height
[RSP+0x20] = -float [RBX+0x24]    angle in the caller shadow area
CALL FUN_180001ec0
[RBX+0x8090] = R15                 publish A for host output
```

This is a five-argument Windows x64 ABI: source pointer, destination pointer,
width, height, and a stack-passed `float` angle. `R15` is the destination work
buffer, not the host world. The host/world pointer is `R13` in
`FUN_180004a20`; the output callback later consumes the published `R15` through
`param_6+0x8090`. `0x1800057a2` is the render-function return, not the helper's
semantic output boundary.

## Bounded Unicorn result

The companion script hooks `FUN_180001ec0` entry and the AEX return trampoline
using cleared 960x540 float buffers with opaque zero-RGB input. It records the
real entry registers, stack angle slot, and destination bytes/floats at
`(494,169)` and `(579,169)`. Those values are helper-only continuation values,
not claimed full-render output.

The full-render target values remain `not captured`; no values are inferred
from the earlier rowdriver boundary witness.

## Next exact fixture

The next local fixture must provide the 8bpc `FUN_180004a20` entry state,
`param_6` fields `+0x8078`, `+0x8080`, `+0x8088`, `+0x8090`, dimensions
`+0x80a0/+0x80a4`, and both PF Iterate8 populate/output callbacks. Hooks should
capture at `0x180005628` and immediately after the helper returns, before the
`+0x8090` publication is consumed. Without that host layout, a full-render
target byte/float claim would be unsupported.
