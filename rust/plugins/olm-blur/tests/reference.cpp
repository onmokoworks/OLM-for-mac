#include "core/olmblur_worker_orchestration.h"
#include "core/olmblur_worker8_legacy.h"
#include "core/olmblur_worker16_nonlegacy.h"
#include "core/olmblur_worker16_legacy.h"
#include "core/olmblur_worker32_nonlegacy.h"
#include "core/olmblur_worker32_legacy.h"
extern "C" void blur_reference(const void* src, void* dst, size_t w, size_t h,
    int depth, bool legacy, float amount, float smoothness, size_t repeat, size_t bias, float scale) {
    using namespace olm::blur;
    if (depth == 8) {
        if (legacy) worker8_legacy::render((const uint8_t*)src,(uint8_t*)dst,w,h,{amount,smoothness,repeat,bias,scale});
        else worker::render_8bpc_nonlegacy((const uint8_t*)src,(uint8_t*)dst,w,h,{amount*scale,smoothness,repeat,bias});
    } else if (depth == 16) {
        if (legacy) worker16_legacy::render((const uint8_t*)src,(uint8_t*)dst,w,h,{amount,smoothness,repeat,bias,scale});
        else worker16::render_nonlegacy((const uint8_t*)src,(uint8_t*)dst,w,h,{amount*scale,smoothness,repeat,bias},nullptr);
    } else {
        if (legacy) worker32_legacy::render((const float*)src,(float*)dst,w,h,{amount,smoothness,repeat,bias,scale});
        else worker32::render_nonlegacy((const float*)src,(float*)dst,w,h,{amount*scale,smoothness,repeat,bias});
    }
}
