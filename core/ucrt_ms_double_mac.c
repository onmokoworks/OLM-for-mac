/* Xcode's AE prefix header imports Carbon's global `fraction` enum.
 * Keep the standalone, qualified ucrtmath implementation unchanged while
 * giving its private helper a non-conflicting name in this Mac translation unit.
 * This macro is applied after the prefix header, not as a compiler -D flag. */
#define fraction olm_ucrt_double_fraction
#include "../ucrtmath/ms/double.c"
#undef fraction
