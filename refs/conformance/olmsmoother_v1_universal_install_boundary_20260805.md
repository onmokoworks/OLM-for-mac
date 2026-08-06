# OLMSmoother v1 macOS-11-targeted universal install boundary

The canonical-PF8-exact plus retained Color-Key-enabled PF8 standalone v1
source builds successfully as a universal `x86_64 arm64` Mach-O with deployment
target `11.0`. The bundle
was installed recoverably into the sole MediaCore `OLMSmoother.plugin`
location and ad-hoc signed; strict deep verification passes. The installed
Mach-O SHA-256 is
`44b199789d086b4f52354dd76fb3a3b107180323221718938d8d8580884028c0`.
The previous installed bundle (Mach-O SHA-256
`2f39684812ac8a1eb2b18790f63b4ee5edceb391d8e2706b7e8f0bb8f45c365e`)
is preserved at
`handoff/mac_plugin_backups/mediacore_20260805_olmsmoother_before_macos11_deployment_fix/OLMSmoother.plugin`.

The portable fixed-fixture lane passes all 16 tests. The canonical no-key
case_0001 stays full-frame exact, with Windows reference and portable PNG
SHA-256
`b2c4cf128d89712b6565745a2d451b6ead1a47ad2efa5a4f4c92a402e95e3156`.
Retained Windows PF8 case `final_random10_olm_smoother_05` with Color Key
enabled is also full-frame exact at
`5276e925f0e7f6de61532a6f9adc3c33a9c8e7330deb0b96eb83f16a30273776`.
The actual Windows key-mask callback and production implementation match on
all six direct vectors. The retained case contains no exact key-color input
pixels, so the direct callback gate supplies the active key-mask proof.

After Effects was not running during the safe replacement. A subsequently
started AE PID `63831` mapped the exact installed path and hash both before and
after the accepted PF8 host run. Canonical no-key case0001 and retained
Color-Key-enabled case05 both passed their control and effect-on decoded RGBA
gates with zero mismatched pixels; their PNG file hashes also match the pinned
Windows files. The separate AEXCompat PF16 typed-session gap is unchanged.
