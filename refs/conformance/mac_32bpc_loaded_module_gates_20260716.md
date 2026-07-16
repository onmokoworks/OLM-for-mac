# Mac 32bpc loaded-module gates - 2026-07-16

- Status: host validation hardened
- Correctness promotion: none
- Scope: OLMColorKey and OLMToonDilate Mac runners

## Fact

Both runners now resolve the plug-in bundle to its actual
`Contents/MacOS/<name>` Mach-O executable. After AE execution they require one
live `After Effects` process, an exact executable path in `vmmap`, an unchanged
SHA-256, and an executable modification time older than the AE process.

The installed OLMColorKey executable is the previously recorded candidate
`c3026c5facbdf227bec55c24e7257f0f94db5ddf94ce26cfb5b593681b5ed0ae`.
The nine-case run did not reach rendering because AE displayed an unsaved
generated-project modal. The runner returned fail-closed and no output was
accepted.

The ToonDilate request pins
`c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`,
while the installed current executable is
`d47a81bd8259bd5ca0db31b71a4e0ffd4fef1c037ef31ffd1a922de1775954de`.
The mismatch remains a deliberate execution block.

## Verification

```text
python3 refs/scripts/smoke_olmcolorkey_32bpc_mac_validation_20260715.py
[OK] Mac OLMColorKey 32bpc package smoke passed

python3 refs/scripts/smoke_package_olmtoondilate_mac_32bpc_validation_20260715.py
[OK] isolated ToonDilate Mac 32bpc package smoke
```

These gates prove process/module identity only. They do not prove raw FLOAT
equality or `AE exact`.
