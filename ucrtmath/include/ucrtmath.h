#ifndef UCRTMATH_H
#define UCRTMATH_H
#ifdef __cplusplus
extern "C" {
#endif
typedef enum { UCRT_NOFMA = 0, UCRT_FMA = 1 } ucrt_mode;
/* Raw binary32 results; round-to-nearest, gradual underflow required.
 * errno and floating-point exception flags are not part of this API. */
float ucrt_expf(float x, ucrt_mode mode);
float ucrt_atan2f(float y, float x, ucrt_mode mode);
float ucrt_powf(float x, float y, ucrt_mode mode);
#ifdef __cplusplus
}
#endif
#endif
