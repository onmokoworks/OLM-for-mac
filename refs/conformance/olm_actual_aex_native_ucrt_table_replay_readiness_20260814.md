# Actual-AEX native UCRT table replay readiness

Status: `READY_NATIVE_TABLE_REPLAY_HOST_SUBSTITUTE_DUAL_OWNER_PLUMBING_PROVEN`.

The patch cleanly applies to the pinned AEXCompat source and the patched `aex-guest-worker` passes `cargo check` in a temporary clean clone. Separate clean release builds have also driven the same macOS-host substitute table through six Directional and eight Distance exported-AEX cells and their matching Mac replays, all full-RAW exact. With a table present, exact `expf`/`powf` keys are required and a missing key stops emulation; host math is not a fallback. Those controls prove plumbing only, not native UCRT results. After the native 1,344-row return arrives, its same table must drive six Directional and eight Distance exported-AEX cells and the matching Mac public replays before any production promotion. AE and network state were not changed.
