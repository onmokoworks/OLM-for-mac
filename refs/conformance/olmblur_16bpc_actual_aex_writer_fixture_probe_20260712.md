# OLMBlur 16bpc actual-AEX writer fixture probe (2026-07-12)

## FACT

- `plugins_2025/OLMBlur.aex` SHA-256 is
  `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- The actual-AEX Non-Legacy 16bpc worker fixtures both execute successfully:
  `16bpc_nonlegacy_basic` and `16bpc_nonlegacy_large_radius_reverse`.
- The 16bpc writer loop is at `0x1800030e2..0x18000311f`. The nearby
  `0x180002ff1` loop is the 8bpc branch and is not reached by these fixtures.
- A scratch Unicorn hook captured all three pre-write RGB floats and final
  stored RGB words for every output pixel: 144 + 324 = 468 pixels.
- Every store agrees with both `trunc(float32(v + 0.5f))` and nearest-even.
  There are zero captured values for which those two candidate rules differ.
- The committed fixture exporter still reproduces its expected hashes:
  `28d648118306c3ed9bedbcd7e99c7af8f8bc26813b701b366c56b966f3a3e846`
  and `64355b2ce493e3d318de8fa09f45234b98236029347b62e9d09e4ef8cb98a4bc`.

## CLASSIFICATION

`binary-grounded / non-discriminating-fixture`. The actual writer instruction
family is confirmed, but these synthetic fixtures contain no half-tie and
therefore cannot decide the live `case_0006` residual. A global writer swap is
not justified. The next writer experiment must reconstruct one live residual
coordinate (including its upstream accumulation state) or inject a controlled
half-tie only as a writer microtest, clearly separated from conformance.

## COMMANDS

- `python3 tools/emulation/test_olmblur_worker16_nonlegacy.py --export`
- Scratch hook run: `python3 /tmp/olmblur_writer_probe.py`
