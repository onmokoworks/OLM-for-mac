# OLMKiraKira Mode 3 Gaussian actual-AEX dispatch audit

Status: **captured; emulation witness only; not OpenCV-conformant**

## Scope

This is a bounded audit of the Mode 3 Gaussian call at `0x181272ec0` in the
pinned 2025 AEX. It covers the coefficient allocation, dispatch backing store,
direct and indirect call observations, and the 63 raw `uint32` output words.
No BT.709, ray aggregation, merge mode 1, gain, luma, or final quantization
tuning was used or changed.

Inputs and implementation inspected:

- `tools/emulation/probe_olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.py`
- `core/kirakira_gaussian.h`
- `tools/emulation/test_kirakira_gaussian.py`
- `tools/emulation/test_kirakira_gaussian.cpp`
- `refs/scripts/smoke_kirakira_gaussian.py`

## Facts

- AEX SHA-256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- The local Unicorn run captured one Gaussian entry and one caller-return
  capture, with `Size(0,1)`, `sigmaX=2.5`, `sigmaY=0.0`, kernel size 21, and 63
  output words.
- The dispatch global at `0x181843990` contained `0x40000200` at both entry
  and return. The backing table had 4034 nonzero qwords in its `0x10000`-byte
  scan; the embedded rdata constant range had 1024 nonzero qwords.
- The aligned 84-byte allocation at `0x400104c0` contained the following 21
  coefficient words, all equal to `0x3d430c31` (`0.0476190485060215`, near
  `1/21`):

```text
0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31
0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31
0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31
0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31 0x3d430c31
0x3d430c31
```

- Capstone found 31 memory-indirect callsites in the Gaussian interval, but
  the run executed zero of them and therefore produced zero runtime indirect
  dispatch targets. This is the exact indirect-target capture, not an inferred
  target list. The run recorded 20 unique direct callees, including
  `0x181266730`; its statically visible nested candidates were
  `0x1812754a0`, `0x181275500`, and `0x181275d70`.
- Sigma was preserved at the observed boundaries: `2.5` at
  `0x181266730`, `0x1812754a0`, and `0x181274e10`.

## Raw 63-word output

The actual-AEX return capture was:

```text
0x3e940001 0x3e915b12 0x3e8b94cc 0x3e8a1192 0x3e80e4c0 0x3e6e5a5b 0x3e5e0fc8 0x3e54c8cb 0x3e51a716
0x3f1fbf78 0x3f1f63af 0x3f205feb 0x3f26c115 0x3f251863 0x3f20696a 0x3f1ac981 0x3f1705bd 0x3f15b346
0x3eb549de 0x3eb36db8 0x3eb1fe90 0x3eb1300b 0x3eaf0952 0x3eaa4368 0x3ea6a210 0x3ea59a2d 0x3ea53e63
0x3f0df540 0x3f0e1cb0 0x3f1689af 0x3f1c7319 0x3f2240e7 0x3f1db960 0x3f17eb92 0x3f13f9ea 0x3f12a772
0x3ec6436a 0x3ec68564 0x3ec521b6 0x3ec30676 0x3ec0eb35 0x3ebe9f32 0x3ebb84a9 0x3eba714d 0x3eba1583
0x3eeb0228 0x3efd5108 0x3f06e1e2 0x3f0cafb0 0x3f1277c1 0x3f16ea7d 0x3f1051c0 0x3f0c8dfd 0x3f0b3b85
0x3ed8226d 0x3ed7ed01 0x3ed768b3 0x3ed60562 0x3ed46db8 0x3ed26ada 0x3ecee3ae 0x3ecd7488 0x3ecd18be
```

## Comparisons

The captured input was replayed through the existing portable C++ diagnostic
using `prepare_unicorn_uniform_diagnostic(5)`. Raw `uint32` comparison:

| Comparison | Words | Mismatches | Max ULP |
|---|---:|---:|---:|
| Actual AEX vs portable uniform replay | 63 | 0 | 0 |
| Actual AEX vs OpenCV 4.5.5 `GaussianBlur` | 63 | 63 | 10,645,146 |

The pinned OpenCV oracle and the ordinary portable `HorizontalGaussian` path
still pass the existing 85-word fixture gate exactly: 85/85 words, zero ULP.
The controlled accumulation checks remain intentionally diagnostic: float and
double coefficient double-accumulation differ from OpenCV in 55 and 51 words,
respectively. Those checks do not authorize production tuning.

## Commands and results

```text
python3 tools/emulation/probe_olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.py \
  --output-json /tmp/olmkirakira_dispatch_audit.json \
  --output-md /tmp/olmkirakira_dispatch_audit.md
=> exit 0; status=captured; entry_hits=1; return_hits=1; word_count=63
=> table=0x40000200; table_nonzero_before=4034; runtime_indirect_targets=[]

tools/emulation/.venv-cv455/bin/python tools/emulation/test_kirakira_gaussian.py \
  --output-json /tmp/olmkirakira_gaussian_compare.json
=> exit 0; OpenCV=4.5.5; fixture=85/85; actual-AEX diagnostic=63/63; max_ulp=0

tools/emulation/.venv-cv455/bin/python refs/scripts/smoke_kirakira_gaussian.py
=> exit 0; smoke_kirakira_gaussian=ok
```

## Limit and disposition

This run is decisive for the local Unicorn scaffold: the uniform 21-tap
buffer and output are internally consistent and bit-exact with the portable
uniform replay. It is not proof that the live Windows AEX uses this coefficient
buffer or this SIMD dispatch path. The retained live-AEX evidence has the
kernel entry arguments but no returned 21-word coefficient payload, and
Unicorn 2.1.4 does not execute the AEX AVX/AVX2 path. Therefore the result is
not promoted to a live-Windows or OpenCV conformance oracle, and no production
Gaussian change is justified.
