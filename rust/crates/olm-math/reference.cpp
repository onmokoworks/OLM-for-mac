// Test-only C++ reference calls. The archive member is not linked by production.
#include "core/olm_exact_math.h"
extern "C" float olm_cpp_float(int op, float x, float y, int mode) {
    auto m = static_cast<ucrt_mode>(mode);
    switch(op) {
    case 0: return ucrt_sinf(x,m); case 1:return ucrt_cosf(x,m);
    case 2:return ucrt_log2f(x,m);case 3:return ucrt_expf(x,m);
    case 4:return ucrt_atan2f(x,y,m);case 5:return ucrt_powf(x,y,m);
    case 6:return olm::x86_float::sse_add(x,y);
    case 7:return olm::x86_float::sse_sub(x,y);
    case 8:return olm::x86_float::sse_mul(x,y);
    case 9:return olm::x86_float::sse_div(x,y);
    case 10:return olm::x86_float::sse_min(x,y);
    default:return olm::x86_float::sse_max(x,y);
    }
}
extern "C" double olm_cpp_double(int op,double x,double y,int mode) {
    auto m=static_cast<ucrt_mode>(mode);
    switch(op){case 0:return ucrt_sin(x,m);case 1:return ucrt_cos(x,m);case 2:return ucrt_exp(x,m);default:return ucrt_pow(x,y,m);}
}
