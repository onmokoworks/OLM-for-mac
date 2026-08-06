# OLMDistanceGradation PF32 Constant + Blur exact witness

The actual classic PF32 owner is executed at 17x11 with Inside ownership, RGB,
Constant interpolation, Blur No Scale, Blur Size 2, and no background color.
It reaches field generation, the embedded `cvSmooth` box-filter path, and the
owner writer without AE.

- Input/output rowbytes: 280/288.
- Pre-blur binary field SHA-256: `564293cbd022462e7f24a4ba689fa0fa8804c33610992f675ece73d9c13e8de9`.
- Active output SHA-256: `4cf21885d6bd3c3635d0451fa22c6a3abf9e42d67c4f10dc7590ec2f1ad3350f`.
- Padded output SHA-256: `6cf47e585d1068649827d28c49ca9a0f634090727ad25bccdef9933d3c92ae0b`.
- Production comparison: 3,168/3,168 bytes, zero mismatches; padding unchanged.

The actual path uses a normalized `(2*size+1)^2` box filter with replicated
borders and a single area division. Its PF32 writer stores blurred field in
A/R/G and the unblurred binary field in B for this branch.
