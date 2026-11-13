# DirectionalBlur no-op copy witness (round three)

## Original AEX: static observation

`OLMDirectionalBlur.aex` SHA-256:
`d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
Image base is `0x180000000`. `witness_noop.py` verifies this identity and emits
address/byte/instruction records; `directional-noop-abi` binds the offsets to
the compiled Windows x64 SDK types.

- Smart dispatch calls the 8-bpc wrapper at `0x180004a20` from
  `0x180007d04`; the adjacent branches dispatch 16 bpc to `0x180003c90` and
  32 bpc to `0x1800057b0`.
- At `0x180004a9d`, load `in_data->utils` from offset `0xb0`.
- `0x180004aa4..0x180004ab4` pass null source/destination rectangles, the
  source/destination worlds, and `effect_ref` from offset `0xb8`.
- At `0x180004abb`, call `[utils + 0x40]`. The ABI witness asserts that this
  is **PF_UtilCallbacks::copy**, the legacy PF_COPY callback. It is not a
  World Transform suite function or an AEX-local memcpy.
- A nonzero copy error exits. Otherwise `0x180004ac9..0x180004b3c` scale and
  truncate four integer lengths. `0x180004b50..0x180004b64` exit when all four
  are zero. There is no second pixel write on that branch.

## Harness behavior and runtime corroboration

The inspected AEXCompat source wires `Sources::copy` to `diag_copy_world`
(`minihost/src/l2_main_entry.inc`, around lines 522 and 790), which calls
`private_copy_world_area8`. `copy_resampled` in
`worker_pf_world_transform_runtime.cpp` uses one active-row `memmove` for
full equal-size rectangles. Its World Transform `copy_world8` instead uses a
scratch buffer and two passes. This describes the inspected harness source,
not undocumented native AE internals.

The original's measured default frames advance the successful `copy` counter
by exactly one each (cumulative counts 1..6 per six-frame batch), corroborating
the static branch. The direct Rust packed-world
path reports zero such calls and must match complete output hashes. Cropped,
padded, or differing-origin cases call the same legacy callback as the original
so that host-specific layout behavior is retained.

## Equivalent optimization and limits

Only non-overlapping, equal-size, tightly packed worlds with matching origins
and full extent hints use the direct path. All active bytes, including alpha,
hidden RGB and float payloads, are copied. Packed worlds at all depths use a single contiguous copy. The measured 8-bpc
row-copy variant was slower despite matching the observed host granularity. No
copy threads or intermediate pixel allocation are used.

The four integer-control checkouts use stack records checked in at the same
address before copying. Metadata strings, parameter vectors and boxed records
are absent from this probe. Active filters still read the complete parameter
set and keep transactional output staging.

Static analysis does not observe native AE execution. The native host's
internal PF_COPY implementation/padding policy remains unknown; fallback
through its original callback avoids substituting a guessed padding policy.
REA tools were unavailable, and its CLI rejected the installed Node version;
no Node upgrade or MCP configuration change was made. The local PE/Capstone witness and compiled
ABI witness provide the static evidence instead.

## Repeated default measurements

`perf_defaults.py --size 1920x1080 --depths 8,16,32 --blocks 8` runs eight
independent batches per side/depth, each with one warmup and five measured frames.
Original/before/candidate order reverses each pair and rotates between pairs.
All 432 frame outputs (including warmups) match within depth. The paired previous
build includes the required main merge, so this isolates the no-op change from
that shared update as far as shared-machine timing permits.

| bpc | Original median / min ms | Before median / min ms | Candidate median / min ms | Candidate/original |
|---|---:|---:|---:|---:|
| 8 | 3.5091 / 3.0959 | 3.5340 / 2.8319 | 3.3407 / 2.9265 | 0.9520 |
| 16 | 4.0463 / 3.4203 | 3.9532 / 3.2682 | 3.9027 / 3.3764 | 0.9645 |
| 32 | 5.7429 / 5.1249 | 4.7613 / 4.2649 | 4.9190 / 4.1977 | 0.8565 |

[Compact block evidence](defaults-round3.json) retains every timed sample and
order. Candidate won 5/8 block medians at 8 and 16 bpc and 8/8 at 32 bpc:
there is still timing overlap, so the pooled medians do not imply a uniform
per-block win. The row-copy experiment remains in local evidence; its 8-bpc
median was 3.4090 ms versus 3.2962 original and 3.1741 before. No observations
were dropped from either campaign.
