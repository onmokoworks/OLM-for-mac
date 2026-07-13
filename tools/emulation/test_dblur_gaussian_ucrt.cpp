#include "../../core/dblur_gaussian.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <initializer_list>

int main()
{
    for (const int count : {96, 240}) {
        for (int index = 0; index < count; ++index) {
            const float value = olm::dblur::gaussian_weight(count, index);
            std::uint32_t bits = 0;
            std::memcpy(&bits, &value, sizeof(bits));
            std::printf("%d %d 0x%08X\n", count, index, bits);
        }
    }
    return 0;
}
