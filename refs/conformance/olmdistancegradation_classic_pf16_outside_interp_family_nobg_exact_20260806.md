# OLMDistanceGradation classic PF16 Outside interpolation family

Status: `exact`, bounded actual-AEX function replay to production.

This extends the classic PF16 `Outside + RGB + no background + no blur`
boundary from a Sphere pair to the complete public interpolation family:

- Constant, Linear, Sphere, and Power 2.5;
- Invert off and on for every interpolation;
- 17x11 source with a 9x7 transparent island, thresholds 4/4;
- input/output rowbytes 146/150 with all `0xA5` padding unchanged.

The thick transparent island produces distance levels 1 through 4. Therefore
the eight outputs are independent discriminators, rather than a binary field
on which Linear, Sphere, and Power collapse to the same result.

Actual AEX `FUN_181174760` field SHA-256:

- non-Constant: `b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112`
- Constant: `13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf`

Actual AEX `FUN_181170480` active-output SHA-256:

| Interpolation | Invert off | Invert on |
|---|---|---|
| Constant | `5030551e163c16bec51f84ffbafd29c1544da95a6999916268189560b0ef4689` | `070af26f37cd39052ab7a47ee18ea9c3ca0238d68afcd7c09a03460ed8f42973` |
| Linear | `c1c1f7b88fe7f49642815e62649254152a361f00d2a26bd453a809aaedc61850` | `c1424a239fbc3814ac63d6b87119c54f46239742fb2b648b5f2fccad1dd5a0fd` |
| Sphere | `ea19a4fda3714aa90158eaf22465af7a7d584e512e9787e0e7b760ebcbfdf3e7` | `fa99bf9d4284a748f6ad3549a56581d40f8f38332857c54bc7fdb91e0166c989` |
| Power 2.5 | `527250c88eca3ee69a43c4f097c0e3953839f5c2bdd986be9e554c33cb315f26` | `864950cf175ed9a124a00f9ca2d23fbdb98a7807e0b1489bd203901f391c71df` |

Production `RenderBits<PF_Pixel16>` matches all 1,650 output bytes in each of
the eight cases. No production or AEXCompat change was required.

Focused command:

```text
tools/emulation/.venv/bin/python tools/emulation/test_olmdistancegradation_classic_pf16_outside_interp_family_nobg_20260806.py
```

Excluded: background composition, Layer mode, Inside/Both ownership, blur,
other thresholds/geometries/depths, host resize, and AE import/export behavior.
