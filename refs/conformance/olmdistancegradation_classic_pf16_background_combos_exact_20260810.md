# OLMDistanceGradation PF16 background combination boundary

Status: `exact`, bounded actual-AEX helper/callback replay to production.

This crosses four independently observable classic-render branches with
Background Color enabled on a 17x11 source containing a 9x7 transparent
island. The actual 2025 AEX generates the Inside and Outside fields through
`FUN_181174760`; the resulting fields are staged to PF16 and all 187 pixels are
written through actual `FUN_181170480`. Production `RenderBits<PF_Pixel16>`
then matches the complete padded output.

| Case | Active output SHA-256 |
|---|---|
| Inside / RGB / Sphere | `8c8cf232a33325d68b1eafe3462da723f065a9897461b1aaf1f36edac0c9d381` |
| Outside / Layer / Power 2.5 | `7198748cb408938006b28f1cddb0e2e8c986516cb4ddcd7fc09a996730121f18` |
| Both / RGB / Linear | `2ec0411672210c26c669b8f95cb5966623600610670dc4c28641da5c6d683c31` |
| Both / Layer / Constant | `7d5524c0b93359d057c697ea6ea3ac46ba0ca843e2efbb8888ff4c95cb3e47d4` |

All four compare 1,650/1,650 bytes with zero mismatch, including distinct
146/150-byte input/output row strides and unchanged `0xA5` padding. Their
active hashes are pairwise distinct.

The Outside/Layer/Power case exposed one production error: zero-ownership PF16
pixels retained Background RGB below alpha zero. The fix clears those RGB
channels, scoped to the actual typed branch demonstrated here.

Excluded: blur-enabled combinations, other geometry/threshold/color values,
PF8/PF32 extrapolation, PF32 SmartRender, and AE import/export behavior.
