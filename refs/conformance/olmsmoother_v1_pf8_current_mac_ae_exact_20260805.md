# OLMSmoother v1 current Mac AE PF8 exact

The accepted `run7` used After Effects `26.3x87` PID `63831` without a
restart. The same process mapped only the current installed OLMSmoother Mach-O
before and after the render. Its SHA-256 was
`44b199789d086b4f52354dd76fb3a3b107180323221718938d8d8580884028c0`.

The 8bpc Software project rendered both a no-effect control and effect-on frame
for each target. Canonical no-key `case_0001` matched exactly, including the
effect PNG SHA-256
`b2c4cf128d89712b6565745a2d451b6ead1a47ad2efa5a4f4c92a402e95e3156`.
Retained Color-Key-enabled `final_random10_olm_smoother_05` read back the PF8
key as RGB `[247,135,193]` and matched exactly at
`5276e925f0e7f6de61532a6f9adc3c33a9c8e7330deb0b96eb83f16a30273776`.
All four decoded RGBA comparisons have zero mismatched pixels; the PNG file
hashes themselves also match their pinned Windows input/reference files.

This closes the two selected PF8 AE-host targets only. The PF16/AEXCompat
boundary remains unchanged, and no other plug-in was operated.
