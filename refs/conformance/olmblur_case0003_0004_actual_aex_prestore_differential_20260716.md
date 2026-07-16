# OLMBlur case 0003/0004 actual-AEX pre-store differential

## FACT

- Pinned actual AEX: `plugins_2025/OLMBlur.aex` / `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- Both retained inputs are decoded identically to little-endian PF16 A,R,G,B with `(PNG word + 1) // 2`; hashes are in the JSON.
- case 0003 Legacy executes `FUN_180005F20` with amount 248.600006103516, smoothness 100, repeat 10, bias 1. All 20 named residual points match portable source conversion bit-for-bit at `0x1800065ae`.
- case 0004 Non-Legacy executes `FUN_180002280` with amount 125.599998474121, smoothness 100, repeat 4, bias 1. Classification: `worker_helper_pre_store_unresolved_fail_closed`.
- case 0004 portable writer-input RGB float32 bits and actual-AEX writer micro-run stored PF16 words are retained in the JSON. The billion-instruction full-worker attempt did not reach the writer.

## INFERENCE

- case 0003 excludes source conversion at the retained coordinates. Its radius-248 x 10 alternating-pass dependency reaches the full 960x540 frame before the first helper, so the probe stops fail-closed before claiming a worker/helper or writer comparison.
- case 0004 excludes source conversion and excludes the writer-store rule conditionally on portable writer inputs. The worker/helper pre-store boundary remains the first unresolved stage; AE export and Windows live behavior remain unproven.

## Tests

```text
python3 tools/emulation/test_olmblur_case0003_0004_actual_aex_prestore_differential_20260716.py
python3 tools/emulation/smoke_olmblur_worker16_legacy.py
python3 tools/emulation/test_olmblur_worker16_nonlegacy.py --export
```

## Changed files

- `tools/emulation/probe_olmblur_case0004_actual_aex_portable.cpp` (new)
- `tools/emulation/test_olmblur_case0003_0004_actual_aex_prestore_differential_20260716.py` (new)
- `refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.json` (new)
- `refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.md` (new)
