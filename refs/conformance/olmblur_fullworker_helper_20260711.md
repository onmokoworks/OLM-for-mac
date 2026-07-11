# OLMBlur Legacy Fullworker Helper Center-Copy Fixtures - 2026-07-11

## Scope

This adds two targeted actual-AEX regression fixtures for the Legacy helper
`all_same` path fixed in `core/olmblur_fullworker_helper.cpp`. The fixture
generator calls the current `OLMBlur.aex` exports directly:

- horizontal: `FUN_1800014f0` at `0x1800014f0`
- vertical: `FUN_180001ea0` at `0x180001ea0`

The AEX SHA-256 recorded in the manifest is
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.

## Witnesses

Both cases use radius `1`, all flags active, carry RGB
`(37.25, 83.5, 129.75)`, and a distinct current center RGB
`(211.5, 17.25, 64.75)`.

| Case | Shape | Witness `(x,y)` | Carry setup | Expected center bytes |
| --- | --- | --- | --- | --- |
| `horizontal_all_same_center_copy` | 4x2, 2 rows | `(0,1)` | row 0 leaves horizontal carry at the constant neighbor RGB; row 1 first center is distinct and its forward neighbor is constant | exact center RGB |
| `vertical_all_same_center_copy` | 3x3, 2 columns | `(1,0)` | column 0 leaves vertical carry at the constant neighbor RGB; column 1 first center is distinct and its forward neighbor is constant | exact center RGB |

At each witness, the center is skipped by the edge scan, every sampled
neighbor compares equal to the persistent carry, and the AEX output is the
current center source. A writer that copied carry RGB on `all_same` would
therefore write `(37.25, 83.5, 129.75)` instead and fail the oracle.

The new expected blob hashes are:

- `horizontal_all_same_center_copy/expected.bin`: `771811a5e446feed2f0eb8445bd33f412efb631c5760eef88ccb7ded3fa807bc`
- `vertical_all_same_center_copy/expected.bin`: `c7d08be0c45a4359b687b94dc73afa3cfb21fc3a96d8210ccb41f46d24776ed4`

The existing six cases remain in the manifest unchanged, including their
expected hashes and parameters.

## Verification

Actual-AEX export:

```text
python3 tools/emulation/test_olmblur_fullworker_helper.py --export
```

Portable byte-exact replay:

```text
c++ -std=c++17 -O2 -ffp-contract=off -fno-fast-math -Icore core/olmblur_fullworker_helper.cpp tools/emulation/replay_olmblur_fullworker_helper.cpp -o /tmp/olmblur_fullworker_helper_replay
/tmp/olmblur_fullworker_helper_replay tools/emulation/fixtures/olmblur_fullworker_helper
```

Output:

```text
PASS horizontal_basic bytes=336
PASS horizontal_flag_break bytes=540
PASS horizontal_large_radius bytes=1092
PASS horizontal_all_same_center_copy bytes=96
PASS vertical_basic bytes=576
PASS vertical_flag_break bytes=864
PASS vertical_large_radius bytes=1848
PASS vertical_all_same_center_copy bytes=108
```

The fixture manifest contains 8 cases total and retains the AEX function
addresses and binary hash above.
