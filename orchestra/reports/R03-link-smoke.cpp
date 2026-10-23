#include "ucrtmath/include/ucrtmath.h"
int main() {
    volatile float f = 0.0f;
    volatile double d = 0.0;
    return !(ucrt_expf(f, UCRT_FMA) == 1.0f && ucrt_powf(2.0f, 3.0f, UCRT_FMA) == 8.0f &&
             ucrt_atan2f(f, 1.0f, UCRT_FMA) == 0.0f && ucrt_sin(d, UCRT_FMA) == 0.0 &&
             ucrt_cos(d, UCRT_FMA) == 1.0 && ucrt_pow(2.0, 3.0, UCRT_FMA) == 8.0);
}
