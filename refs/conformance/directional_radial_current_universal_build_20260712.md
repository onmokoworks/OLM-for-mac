# DirectionalBlur / RadialBlur current universal builds (2026-07-12)

The previous Debug products predated their current source files. Both projects
were rebuilt without changing source behavior:

- `OLMDirectionalBlur`: universal arm64/x86_64, SHA-256
  `5daf9e97e63c8d4e47a24e8f8d8638167a6a3e495e5ca5f7a42fbdd860dcd9b0`.
- `OLMRadialBlur`: universal arm64/x86_64, SHA-256
  `d59f166216b5eff290d902f01866ea6d507fcc31ec2beb264ee789b2b2cc482a`.

Both `xcodebuild ... -configuration Debug build CODE_SIGNING_ALLOWED=NO`
commands ended in `BUILD SUCCEEDED`. The products were not installed and this
is not an AE-exact promotion.
