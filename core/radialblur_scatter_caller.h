#pragma once

#include "radialblur_scatter_tail.h"

#include <cstddef>

namespace olm::radialblur {

struct ScatterCallerContext {
    ScatterTailContext tail;
    int outer_offset_value;
    int inner_offset_value;
};

struct ScatterCallerInput {
    int quality_or_rows;
    int start_radius;
    int end_radius;
    int angular_count;
    const float* source_rgba;
    const float* source_alpha;
    const float* span_gate;
    const unsigned char* valid;
};

// Portable, unwired implementation of the caller contract at AEX RVA
// 0x2520. Source and destination planes are indexed by the absolute radius
// row; start_radius selects the first row visited, rather than rebasing input
// planes to a local zero row.
// Returns false without modifying outputs when the supplied geometry is not
// representable or the destination cannot cover all reached radius rows.
bool scatter_valid_polar_cells(const ScatterCallerContext& context,
                               const ScatterCallerInput& input,
                               const ScatterTailBuffers& buffers);

}  // namespace olm::radialblur
