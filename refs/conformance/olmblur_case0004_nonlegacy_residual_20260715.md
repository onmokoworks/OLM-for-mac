# OLMBlur 16bpc Non-Legacy case_0004 residual

## Scope

- Mac AE 16bpc, Non-Legacy (`Legacy=0`)
- `Blur Amount=125.599998474121`, `Number of Repeat=4`, `Bias Direction=1`
- Candidate: `/tmp/olmblur_16bpc_candidates_c76c687c/*case_0004.png`
- Expected: request `expected/*case_0004.png`

## Facts

- Raw PNG comparison has exactly two differing samples, both red:
  `(411,258)` candidate `44073`, expected `44075`; `(458,314)` candidate
  `52745`, expected `52747`. Alpha, green, and blue are exact.
- Exported PNG words map to AE PF16 words as `2 * word - 1`. The residual is
  therefore one internal word low at each point: `22037` vs `22038`, and
  `26373` vs `26374`.
- Replaying the current `core/olmblur_worker16_nonlegacy.cpp` against the
  decoded case input, with exported source words converted back to the
  0..32768 PF16 domain, gives pre-store float bits `0x46ac2aff` and
  `0x46ce0aff`, or `22037.498046875` and `26373.498046875`. The worker stores
  `22037` and `26373`, reproducing the candidate words exactly.
- At both points `floorf(value + 0.5f)` and nearest-even produce the same
  word for the reproduced portable-worker floats. This does not bind the live
  Mac or Windows pre-store floats.
- The actual-AEX Non-Legacy complete-worker fixtures remain unchanged and
  continue to validate `FUN_180002280`, including the actual writer loop and
  helper entry points.

## Classification

Current evidence does not justify a worker, writer, or global-rounding change.
The expected image is one internal word higher at both coordinates, but final
PNG words and a portable replay do not identify whether that delta is from AE
host/source quantization, worker/helper arithmetic, or a platform-specific
float state. Same-run Mac and Windows captures of pre-store float bits, writer
input, stored PF16 word, and exported PNG word are the decisive next proof. Do
not change `olmblur_worker16_nonlegacy.cpp`, the shared helper, or the
writeback rule from this evidence.

## Reproduction

```text
c++ -std=c++17 -O2 -ffp-contract=off \
  tools/emulation/probe_olmblur_case0004_worker16.cpp \
  core/olmblur_helper.cpp core/olmblur_worker16_nonlegacy.cpp \
  -o /tmp/probe_olmblur_case0004_worker16
python3 tools/emulation/test_olmblur_case0004_nonlegacy_replay.py
```

The regression decodes the retained request `before_effects` PNG as big-endian
16-bit RGBA, maps each exported word to AE PF16 with `(word + 1) // 2`, and
rewrites the pixels as little-endian A,R,G,B in a `TemporaryDirectory` before
compiling and running the probe. It asserts the raw pre-store float bits and
stored words at both residual coordinates.

This is conditional portable replay evidence only. It is an independent audit
of the retained request input and portable worker; it is not live Mac/Windows
pre-store binding and does not disprove the writer or global rounding behavior
universally.
