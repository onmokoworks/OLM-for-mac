# Milestone 2: FUN_180004640 rotation-driver attempt

- Binary: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
- Synthetic input: 16x16 RGBA float worlds, param_1[0]=90.0 (iVar29 = 360/90 = 4), angle=0, center=(8,8)

## Execution outcome

- Completed to RET: **True**
- Instructions executed: 914220 (cap 30000000)
- Wall clock: 1.55s

## Witnessed handle-pointer writes

- `param_1[0xf254]` (omp_get_max_threads, raw int): 1
- `param_1[0xf250]`: `0x40004370` (written, non-zero handle ptr)
- `param_1[0xf252]`: `0x40004700` (written, non-zero handle ptr)
- `param_1[0xe]`: `0x400047f0` (written, non-zero handle ptr)

## Witness dump (typed, per polar cell)

f250 -> RGBA plane (4f/cell); f252 -> weight plane (1f/cell); +0xe -> normalized output (4f/cell). Input worlds carry a gradient `pixel(col,row) = (col/W, row/H, 0.5, 1.0)`, so the values below are the rotation kernel's actual sampled/weighted/normalized output and vary by polar cell -- e.g. R rises across cells as the sampler walks the gradient, and `+0xe(out)` is the per-cell normalization of f250 by the reference channel.

```
cell    0: f250(RGBA)=(0.5, 0.5, 0.5, 1.0) f252(w)=(1.0,) +0xe(out)=(0.5, 0.5, 0.5, 1.0)
cell    1: f250(RGBA)=(0.5, 0.5, 0.5, 1.0) f252(w)=(1.0,) +0xe(out)=(0.5, 0.5, 0.5, 1.0)
cell    2: f250(RGBA)=(0.5, 0.5, 0.5, 1.0) f252(w)=(1.0,) +0xe(out)=(0.5, 0.5, 0.5, 1.0)
cell    3: f250(RGBA)=(0.5, 0.5, 0.5, 1.0) f252(w)=(1.0,) +0xe(out)=(0.5, 0.5, 0.5, 1.0)
cell    4: f250(RGBA)=(0.5625, 0.5, 0.5, 1.0) f252(w)=(1.0,) +0xe(out)=(0.5625, 0.5, 0.5, 1.0)
cell    5: f250(RGBA)=(0.5625, 0.5, 0.5, 1.0) f252(w)=(1.0,) +0xe(out)=(0.5625, 0.5, 0.5, 1.0)
```

## Host suite activity

- Imports exercised: ['atan2f', 'cos', 'expf', 'omp_get_max_threads', 'sin']
- callback `PFHandle.dispose`: 8 call(s)
- callback `PFHandle.lock`: 8 call(s)
- callback `PFHandle.new`: 8 call(s)
- callback `PFHandle.unlock`: 8 call(s)
- callback `SPBasic.AcquireSuite`: 32 call(s)
- callback `SPBasic.ReleaseSuite`: 32 call(s)

## param_2 offsets actually read (dynamic trace)

`['0x0', '0x8', '0x28', '0x30', '0x44', '0x54', '0x58', '0x5c', '0x60', '0x64', '0x68', '0x6c', '0x70', '0x74', '0x78', '0x7c', '0x90', '0x98', '0xa0']`

