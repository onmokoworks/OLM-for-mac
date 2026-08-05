# OLMRadialBlur case0009 production chain (2026-08-05)

Status: `internal_pf32_exact`

The production `RenderZoomTyped<PF_PixelFloat>` path was invoked from a
1920x1080 PF32 host fixture built from the retained case0009 PNG. Every
observable stage matches its retained actual-AEX identity:

- eligibility: `861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7`
- preblur polar RGBA: `fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef`
- span plane: `2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f`
- source scalar plane: `13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce`
- normalized polar RGBA: `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
- final internal PF32 RGBA frame: `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`

The 1717-entry production Gaussian table also remains exact on arm64 and
x86_64 with SHA-256
`82d66d41ebba38e15638fd369acdf3a218a9160d39b0ad12a2aad482df8242d8`.

This is an internal production-path result. It does not establish Mac AE
host output equality. The next boundary is a hash-bound Mac AE Software PF32
render of case0009 against the Windows AE reference.

Verification:

```sh
python3 tools/emulation/test_olmradialblur_production_outer_inputs_20260805.py
python3 tools/emulation/test_olmradialblur_zoom_weights_contract_20260718.py
```
