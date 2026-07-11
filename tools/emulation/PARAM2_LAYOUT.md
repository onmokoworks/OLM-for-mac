# param_2 context-struct layout (FUN_180004640)

Derived statically from `decomp/OLMRadialBlur.aex.c.txt` (FUN_180004640 and the FUN_1800045a0/43c0 handle helpers) and corroborated dynamically by a MEM_READ trace during the bounded emulation run (`test_m2_rotation.py`). The `read?` column marks offsets the trace actually observed being read before execution stopped.

`param_2` is the plugin's own render-context struct (not a raw AE `PF_InData`); however `*param_2` behaves like a `PF_InData*` in that `*(*param_2 + 0x180)` is the PICA `SPBasicSuite` (AcquireSuite/ReleaseSuite), matching the AE SDK `AE_GeneralPlug.h`/`SPBasic.h` pattern. `param_2[1]`'s +0x24/+0x28 int fields behave like a world's width/height (cf. `PF_LayerDef`/`PF_EffectWorld` in `AE_Effect.h`).

| byte off | C expr | type | read? | meaning |
|----------|--------|------|-------|---------|
| 0x00 | `*param_2` | void* | yes | P0: *(P0+0x180) = SPBasicSuite dispatch (AE PF_InData-like). Used by all handle-alloc helpers. |
| 0x08 | `param_2[1]` | void* | yes | param_2[1]: pointer to a struct with width @+0x24 and height @+0x28 (output world geometry / PF_LayerDef-like). |
| 0x28 | `param_2[5]` | double | yes | center X (-> param_1[0xf24e], byte 0x3c938). |
| 0x30 | `param_2[6]` | double | yes | center Y (-> param_1[0xf24f], byte 0x3c93c). |
| 0x44 | `byte @0x44` | uint8 | yes | flag: if 0, alpha channel is forced to 1.0 (0x3f800000); else sampled via param_2[0x11]. |
| 0x54 | `float @0x54` | float | yes | -> param_1[9]. |
| 0x58 | `param_2[0xb]` | int32 | yes | -> param_1[10] scaling term (param_2[0xb]). |
| 0x5c | `float @0x5c` | float | yes | -> param_1[0xb]. |
| 0x60 | `param_2[0xc]` | int32 | yes | -> param_1[0xc] scaling term (param_2[0xc]). |
| 0x64 | `int @0x64` | int32 | yes | -> param_1[0xea7a] scaling term. |
| 0x68 | `param_2[0xd]` | int32 | yes | -> param_1[0xea7b] scaling term (param_2[0xd]). |
| 0x6c | `int @0x6c` | int32 | yes | -> param_1[0xf24c] / kernel size for FUN_18000b680. |
| 0x70 | `param_2[0xe]` | int32 | yes | -> param_1[0xf24d] / kernel size for FUN_18000b680 (param_2[0xe]). |
| 0x74 | `byte @0x74` | uint8 | yes | flag: selects sampler pair (0 -> FUN_180001800/FUN_180001270, else FUN_180001950/FUN_180001520). |
| 0x78 | `param_2[0xf]` | float | yes | -> param_1[5] (used as a divisor; must be non-zero). |
| 0x7c | `int @0x7c` | int32 | yes | rotation angle in degrees; feeds cos()/sin() (double). |
| 0x88 | `param_2[0x11]` | void* | - | param_2[0x11]: input world for alpha sampling. |
| 0x90 | `param_2[0x12]` | void* | yes | param_2[0x12]: input world (second sampler target). |
| 0x98 | `param_2[0x13]` | void* | yes | param_2[0x13]: input world (first sampler target). |
| 0xa0 | `param_2[0x14]` | void* | yes | param_2[0x14]: output world data base. |

## Notes on AE SDK header correspondence

- `*(*param_2 + 0x180)` -> `SPBasicSuite*` (`SPBasic.h`): first two function pointers are `AcquireSuite(name, version, out)` and `ReleaseSuite(name, version)`. The plugin acquires "PF Handle Suite" v2 (`PF_HandleSuite1` in `AE_Effect.h`).
- `PF_HandleSuite1` table order used here: [0]=`host_new_handle`, [+8]=`host_lock_handle`, [+0x10]=`host_unlock_handle`, [+0x18]=`host_dispose_handle`.
- Angle @+0x7c is stored as an int (degrees) and converted to double before `cos`/`sin`; note the AE SDK typically passes angles as `PF_Fixed`/`PF_FpLong`, so this int is likely a pre-rounded degree value the plugin computed upstream.
