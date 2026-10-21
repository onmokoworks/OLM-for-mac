# OLMRadialBlur Type 3 exported upstream boundary (2026-08-14)

Status: `PASS_STATIC_UPSTREAM_EXPORTED_TYPE3_DESTINATION_UNINITIALIZED_TYPED_OWNER_RETAINED`

The pinned Windows AEX exported render constructs its local render-info object at `RSP+0x40`, but does not initialize the Noise Layer destination member at `+0xa8` before calling the parameter materializer. Noise Type 3 loads that member at `0x1800088b6`; the downstream helper forwards it as the destination of the fixed 0x78-byte PF_LayerDef copy at `0x180019f20`.

Therefore the exported Type 3 route is not a usable numerical oracle. The bounded typed Windows owner remains the authority for the existing 45 exact Mac public rows. Production admission is unchanged and every unlisted source/Layer/tuple/geometry/layout remains fail-closed.

This is static AEX evidence only. It does not claim native Windows AE execution or durable dynamic crash registers/addresses.
