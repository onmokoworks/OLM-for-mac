# OLMColorKey 32bpc case_0002 AE exact

`OLMColorKey/case_0002` is AE exact for the declared 32bpc
default-parameter no-op profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Output: `OLM EXR 32 Float`, uncompressed RGBA FLOAT, `1920x1080`,
  Preserve RGB
- Supplied input SHA-256:
  `918ec046892f851d4693d5e1f8ad7a13b622c371b824e3a2bd5315a0fa84c5e7`

Mac AE created one project containing an effect-free control comp and an
effect comp. Replacing only the three platform-specific AEPX
`fileReference` elements makes the Mac and Windows projects byte-identical
at SHA-256:

`2bd8754d393a33e7b00f8338ef38f3e299833fc1815d7dfa19b1a7486ab83234`

Windows rendered both embedded queue items in one `aerender` process. Kernel
Process ETW binds `aerender` PID `31472` to `AfterFX.com` PID `42568`, then
records the load and unload of the current Windows AEX on PID `42568`:

`9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`

Mac `vmmap` binds AE PID `36364` to the installed Mach-O:

`c3026c5facbdf227bec55c24e7257f0f94db5ddf94ce26cfb5b593681b5ed0ae`

Semantic FLOAT32 word comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows control vs Mac control | 0 / 8,294,400 | 0 |
| Windows effect vs Mac effect | 0 / 8,294,400 | 0 |
| Windows effect vs control | 0 / 8,294,400 | 0 |
| Mac effect vs control | 0 / 8,294,400 | 0 |

Windows reports that effect-control conversion may reset controls when it
opens the Mac-created AEPX. This does not generalize away: it is accepted
only for this case because the 217 render parameters in the Windows-captured
case vector are all the declared plugin defaults. The critical discriminator
values are Threshold `0`, Edge Thin Amount `0`, and Edge Blur Amount `0`;
the case is intentionally a no-op on both hosts. A non-default ColorKey case
must not reuse this warning disposition.

The older bulk Windows return remains rejected because its no-effect control
already differs from the current Mac input world. The other eight declared
32bpc ColorKey cases remain unpromoted. Machine-readable evidence is in
`refs/conformance/olmcolorkey_32bpc_case0002_ae_exact_20260727.json`.
