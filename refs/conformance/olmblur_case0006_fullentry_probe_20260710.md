# OLMBlur case_0006 Full-Entry Probe

Date: 2026-07-10

## Scope

`tools/emulation/test_olmblur_case0006_fullentry.py` drives the existing host
model's Legacy `FUN_180005f20` entry with the canonical manifest case. The
16bpc Non-Legacy counterpart is `FUN_180002280` and is covered by the current
complete-worker fixture lane:
`tools/emulation/test_olmblur_worker16_nonlegacy.py`.

- Windows Software 16bpc, 1920x1080
- Blur Amount `5`, Blur Smoothness `100`, Number of Repeat `10`
- Bias Direction `1`, Legacy `0`
- canonical before-effects input and effect output from the checked-in Windows reference set

The PNG decoder verifies IHDR 16-bit RGBA and decodes PNG filter rows without
an 8-bit library conversion. The emulated world stores each pixel as
little-endian `A,R,G,B` words because the entry disassembly reads RGB at world
offsets `+2`, `+4`, `+6` and alpha at `+0`. This is a channel/word-layout check,
not a claim that the local AEX run is Windows truth.

## Result

Run with:

```text
tools/emulation/.venv/bin/python tools/emulation/test_olmblur_case0006_fullentry.py
```

The command output is the run record for this probe, including status,
instruction count, callback sequence, `(314,14)` and `(29,71)` RGBA16 words,
and deterministic semantic SHA-256 hashes. The Windows PNG SHA-256 is
`27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`.

The measured full-frame attempt remained inside Unicorn C execution for the
30-second practical cap and emitted no completed probe record. It was stopped
externally; no local output, witness, or local semantic hash is accepted here.
The existing `fast=True` host mode does not count ordinary guest instructions,
so the measured throughput is only `0 completed frames / 30 s`; an instruction
throughput value is unavailable. The in-process Python alarm is not a reliable
hard stop once Unicorn is executing C code.

### Hard-timeout implementation

The checked-in probe now runs the Unicorn worker in a separate process and
kills its process group after 30 seconds. The equivalent pattern is:

```python
import os, signal, subprocess

p = subprocess.Popen(["tools/emulation/.venv/bin/python",
                      "tools/emulation/test_olmblur_case0006_fullentry.py"],
                     start_new_session=True)
try:
    p.wait(timeout=30)
except subprocess.TimeoutExpired:
    os.killpg(p.pid, signal.SIGKILL)
    raise RuntimeError("OLMBlur case_0006 full-frame probe exceeded 30 s")
```

This is the appropriate hard boundary for future runs because it remains
effective while the child is inside Unicorn's C execution.

The probe deliberately reports local output separately from the canonical
Windows output. It does not convert a local AEX result, a crop, or a host-suite
simulation into Windows conformance evidence. A crop is blocked: although the
blur helpers expose local neighborhood accesses, the full entry sizes its
intermediate planes and loops from the supplied world dimensions, and the
binary evidence does not establish a crop origin/edge contract preserving the
absolute witness coordinates. A halo estimate alone is therefore insufficient.
