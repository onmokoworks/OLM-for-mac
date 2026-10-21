# OLMDirectionalBlur Type 2 natural 64×36 AEXCompat closure — 2026-08-12

The pinned AEXCompat worker and the public Mac `EffectMain` SmartPreRender→SmartRender route are raw exact for the bounded Noise Type 2 tuple at PF8/PF16/PF32. The proof binds the worker, AEX, source crop, typed input transport, production/core sources, all 21 public parameter checkouts/checkins, input/output lifecycle, optional missing Noise Layer, active bytes, and output padding. Production admits rowwise active-source SHA-256 only for zero, constant, impulse, checker, and the pinned crop, all raw exact across every depth.

- PF8: `777321d706587010a88f8e03a00bc6704ec9e7e3445aed5cd915192fe3f4f7f0`
- PF16: `7fad7744f5fa4fee9a92bfa953164a5d39ee6c6fffe9689b2df9f78629581c5f`
- PF32: `8ae8187087f4133b806ff7488ed47c9f2152e34a7fcc1bbe56f7c8f1e3a9d2cf`

Only the PF16/PF32 NV25 64×36 lane was newly promoted; its preexisting PF8 control is now narrowed to the same five exact sources, while other admission lanes and the older 16×16 Noise×Size matrix are unchanged. Sixty PF16/PF32 rejection cases cover every production predicate parameter field, scales, geometry, null data, short/huge rowbytes, source first/middle/last bit flips and an unlisted source. Four equivalent PF8 source mutations/unlisted controls also fail closed, all with input and output untouched.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py`
