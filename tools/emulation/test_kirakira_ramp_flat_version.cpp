#include "../../core/kirakira_merge2.h"

#include <cassert>
#include <cstdint>
#include <cstring>

int main()
{
    const olm::kirakira::Merge2RampStop expected[] = {
        {0.0f, 1.0f, 1.0f, 0.0f, 0.0f},
        {1.0f, 0.25f, 0.125f, 0.5f, 0.875f},
    };
    for (unsigned version : {0u, 1u, 2u, 255u}) {
        unsigned char flat[0x145] = {};
        flat[0] = static_cast<unsigned char>(version);
        const std::uint32_t count = 2;
        std::memcpy(flat + 1, &count, sizeof(count));
        std::memcpy(flat + 5, expected, sizeof(expected));
        olm::kirakira::Merge2RampStop parsed[16] = {};
        std::size_t parsed_count = 0;
        assert(olm::kirakira::parse_merge2_ramp_flat(
            flat, sizeof(flat), parsed, 16, &parsed_count));
        assert(parsed_count == 2);
        assert(std::memcmp(parsed, expected, sizeof(expected)) == 0);
    }
    return 0;
}
