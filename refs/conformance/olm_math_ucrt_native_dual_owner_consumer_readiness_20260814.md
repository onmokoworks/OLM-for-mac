# Native UCRT dual-owner consumer readiness

Status: `PASS_SYNTHETIC_VALIDATED_RETURN_CONSUMER_AEX_MAC_DIRECT_14_OF_14`.

The exact consumer intended for the future 1,344-row return was exercised end-to-end with the strict analyzer's synthetic test fixture. One clean AEXCompat release worker and one derived table drove Directional exported AEX versus Mac production direct (6/6) and Distance exported AEX versus Mac RenderBits (8/8), full RAW exact. Directional records 996 expf and 47,514 double-pow table lookups, so both imported-math families are exercised. The synthetic UCRT identity is explicitly test-only and is not native Windows evidence. No public route was promoted, and AE/network/install state was untouched.
