#ifndef UCRTMATH_H
#define UCRTMATH_H
#ifdef __cplusplus
extern "C" {
#endif
typedef enum { UCRT_NOFMA = 0, UCRT_FMA = 1 } ucrt_mode;
/* Raw binary32 results; round-to-nearest, gradual underflow required.
 * errno and floating-point exception flags are not part of this API. */
/* OLM-internal Microsoft-behavior functions; see ms/README.md. */
float ucrt_sinf(float x, ucrt_mode mode);
float ucrt_cosf(float x, ucrt_mode mode);
float ucrt_log2f(float x, ucrt_mode mode);
float ucrt_expf(float x, ucrt_mode mode);
float ucrt_atan2f(float y, float x, ucrt_mode mode);
float ucrt_powf(float x, float y, ucrt_mode mode);
#ifdef __cplusplus
}
#endif
#endif
