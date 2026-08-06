# OLMDistanceGradation PF32 Both/Layer/Power exact witness

Actual `DistanceGradation.aex` and Mac production were compared for classic
PF32, 17x11, Both ownership, Layer mode, Power 2.5, no background color.

- Input/output rowbytes: 280/288.
- Internal field SHA-256: `8ac06eb6a3a4329f511a3496e33b13c51ec01c6fb03624f238e545c7536e30ca`.
- Active output SHA-256: `6a0c57df59d4ccf2a170d851fec2b236d3600a46a8521b8029101f1f952ebd25`.
- Padded output SHA-256: `a155960e97efca905be85c9640b5cbc30c890735811c6b63e4c5f31a922cb1ae`.
- Production comparison: 3,168/3,168 bytes, zero mismatches; padding unchanged.

For this whole-owner scalar field, actual Power 2.5 produces the same output
as the existing Linear witness. The dedicated test retains the Power parameter
contract so that equivalence is grounded in an actual-AEX execution.
