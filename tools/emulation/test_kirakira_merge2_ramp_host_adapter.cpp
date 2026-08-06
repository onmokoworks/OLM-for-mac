#include "../../core/kirakira_merge2.h"

#include <cstdint>
#include <cstdio>
#include <vector>

int main()
{
    std::vector<unsigned char> payload;
    unsigned int byte = 0;
    while (std::scanf("%02x", &byte) == 1)
        payload.push_back(static_cast<unsigned char>(byte));

    std::vector<olm::kirakira::Merge2RampStop> stops;
    if (!olm::kirakira::parse_merge2_ramp_payload(
            payload.data(), payload.size(), stops))
        return 2;
    std::printf("count %zu\n", stops.size());
    for (const auto& stop : stops)
        std::printf("%.9g %.9g %.9g %.9g %.9g\n",
                    stop.position, stop.alpha, stop.red, stop.green, stop.blue);

    // A truncated checkout must fail closed without retaining prior stops.
    if (olm::kirakira::parse_merge2_ramp_payload(payload.data(), 8, stops) || !stops.empty())
        return 3;
    return 0;
}
