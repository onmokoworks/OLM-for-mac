#include "../core/olm_world_safety.h"

#include <cassert>
#include <cstdint>
#include <cstring>
#include <limits>

using namespace olm::world_safety;

int main()
{
    std::uint8_t storage[128] = {};
    Layout layout = {};
    assert(validate_layout(ConstWorld{storage, 3, 2, 17, 4}, &layout) == Status::ok);
    assert(layout.active_row_bytes == 12 && layout.addressable_bytes == 29 && layout.tight_bytes == 24);
    assert(validate_layout(ConstWorld{storage, 3, 2, 11, 4}) == Status::stride_too_small);
    assert(validate_layout(ConstWorld{storage, std::numeric_limits<std::size_t>::max(), 2, 12, 4}) ==
           Status::arithmetic_overflow);
    assert(validate_layout(ConstWorld{storage, 1, std::numeric_limits<std::size_t>::max(),
                                            std::numeric_limits<std::size_t>::max(), 1}) ==
           Status::arithmetic_overflow);

    assert(ranges_overlap(AddressRange{10, 20}, AddressRange{19, 30}));
    assert(!ranges_overlap(AddressRange{10, 20}, AddressRange{20, 30}));
    assert(require_disjoint(ConstWorld{storage, 4, 2, 8, 1},
                            ConstWorld{storage + 7, 4, 2, 8, 1}) == Status::overlapping_payloads);
    assert(require_disjoint(ConstWorld{storage, 4, 2, 8, 1},
                            ConstWorld{storage + 12, 4, 2, 8, 1}) == Status::ok);

    std::uint8_t input[24], output[32];
    std::memset(input, 0xee, sizeof(input));
    std::memset(output, 0x7b, sizeof(output));
    for (int y = 0; y < 2; ++y)
        for (int x = 0; x < 12; ++x) input[y * 12 + x] = static_cast<std::uint8_t>(y * 20 + x);

    TightStaging staging;
    assert(staging.prepare(ConstWorld{input, 3, 2, 12, 4},
                           MutableWorld{output, 3, 2, 16, 4}) == Status::ok);
    assert(staging.row_bytes() == 12 && staging.width() == 3 && staging.height() == 2);
    std::memset(staging.output_data(), 0x42, 24);
    assert(output[0] == 0x7b); // rendering is atomic until commit
    assert(staging.commit() == Status::ok);
    for (int y = 0; y < 2; ++y) {
        for (int x = 0; x < 12; ++x) assert(output[y * 16 + x] == 0x42);
        for (int x = 12; x < 16; ++x) assert(output[y * 16 + x] == 0x7b); // padding is host-owned
    }

    TightStaging aliasing;
    assert(aliasing.prepare(ConstWorld{storage, 2, 2, 8, 4},
                            MutableWorld{storage, 2, 2, 8, 4}) == Status::overlapping_payloads);
    assert(aliasing.prepare(ConstWorld{storage, 2, 2, 8, 4},
                            MutableWorld{storage, 2, 2, 8, 4}, false) == Status::ok);
}
