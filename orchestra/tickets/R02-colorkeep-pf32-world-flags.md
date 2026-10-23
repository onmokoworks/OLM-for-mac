# R02: ColorKeep shipped bundle refuses PF32 because of its world-flag guard (found by F47d)

## Facts (F47d, `orchestra/reports/F47d-native-plugin-all.md`)
- The real Universal Release ColorKeep `.plugin` refuses all 35 PF32 cases in seed 1 n100 with
  `ColorKeepValidateWorldPair:world-flags-or-bounds@216`. The source-candidate harness gives 100
  exact on the same cases.
- The host (AEXCompat `FramePixelFormat::world_flags`) sets `PF_WorldFlag_DEEP` for PF16 *and* PF32.
  OLMBlur, KiraKira and Smoother2 accept that. ColorKeep requires DEEP only for PF16.
- The original ColorKeep AEX renders these PF32 cases exactly under the same host. So the original
  tolerates DEEP on float worlds, and the Mac guard is stricter than the original.

## Do
1. From the decomp, find what the original ColorKeep checks on world flags and pixel format. Also
   find what AE actually sets on 32-bpc worlds: check the SDK headers/docs (`PF_WorldFlag_DEEP`
   semantics, the PixelFormat suite) and how the other OLM Mac ports handle it.
2. Make ColorKeep's validation identify the depth the same way the original does: use the
   pixel-format suite or rowbytes/width, as the original does. Do not rely on a flag combination
   the original doesn't check.
3. Verify:
   - The source candidate is unchanged: seed 1 n300, all exact.
   - The bundle candidate (F47d bridge, `tools/fuzz/verify_F47d.py --plugins colorkeep`) is 100/100 exact.
   - The ColorKeep corpus replays.
- Use 1-2 processes. Do not touch the release gate/ledger.
