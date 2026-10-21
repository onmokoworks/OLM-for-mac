# OLMSmoother public-guard Universal builds

Verdict: `PASS_ISOLATED_UNIVERSAL_BUILDS_SIGNED_NOT_INSTALLED`

Both OLMSmoother and OLMSmoother2 were built in isolated `/tmp` derived-data and product directories for `x86_64 arm64`. The resulting bundles were ad-hoc signed and passed strict deep `codesign` verification. Their signed executable SHA-256 identities are pinned in the sibling JSON report.

These builds are from the entry-specific admission sources: OLMSmoother v1 publishes only the proven classic map, while OLMSmoother2 publishes only the proven Smart map.

Neither bundle was installed. Installed identity and After Effects smoke remain root-controlled follow-up gates.
