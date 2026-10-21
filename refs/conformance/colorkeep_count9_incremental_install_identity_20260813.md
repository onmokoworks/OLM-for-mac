# ColorKeep count9 incremental install identity — 2026-08-13

ColorKeep source `3ff3a4d4319f5b3b5519e517fcf591be417c97e4e9dd62117fe4e42f66ebdfd3` was unchanged while the isolated Debug Universal candidate `fcd501dae5e62aaa0bb8c022cc55c3a6735e3021d465b42b80c939f33624dd77` was built with deployment target 11.0, ad-hoc signed, staged, and atomically exchanged into MediaCore with `renameatx_np(RENAME_SWAP)`. Both Mach-O slices and Info.plist declare 11.0; both slices export EffectMain.

The accepted identity manifest is `869a5e88ab34b3b26cc4a3786edb6de93f0e10c88b69c33f6e8d7afb6f18da90`. Only the ColorKeep row fields `sha256`, `source_bundle`, and `source_sha256`, plus `accepted_at` and `installed_after`, changed; the other nine plugin rows are exact. The old executable `262b73e656d4363dce0de6f0fe819fabf461e157ca7cedd98cad107c8db87fe8` remains in three full-inventory durable copies. Two post-install all-ten preflight collections found one Universal, strict-signature-valid, identity-exact bundle per plugin and zero After Effects processes.

The inventory claim covers path, type, POSIX mode, size, file SHA-256, and symlink target. It does not claim mtime, xattr, ACL semantics, Developer ID, notarization, AE load/render, fresh AE smoke, or release readiness.
