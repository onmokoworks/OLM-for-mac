#pragma once

#include <cstddef>

namespace olm::radialblur {

struct ScatterTailContext {
    int outer_mode;
    int inner_mode;
    int outer_base_length;
    int inner_base_length;
    const float* outer_table;
    const float* inner_table;
};

struct ScatterTailInput {
    int direction;
    int caller_distance;
    int angular_index;
    int radius_row;
    int angular_count;
    float source_alpha;
    float source_r;
    float source_g;
    float source_b;
    float span_gate;
};

struct ScatterTailBuffers {
    float* scatter_rgba;
    float* max_alpha;
    std::size_t cell_count;
};

// Portable, un-wired implementation of AEX FUN_180001c90. The caller owns
// context tables and destination initialization. The proven contract assumes
// valid table/buffer dimensions. Unlike the AEX, this portable entry returns
// early if its computed destination reaches cell_count; that bounds bailout
// is an intentional safety divergence outside the conformance fixture domain.
void scatter_tail(const ScatterTailContext& context,
                  const ScatterTailInput& input,
                  const ScatterTailBuffers& buffers);

}  // namespace olm::radialblur
