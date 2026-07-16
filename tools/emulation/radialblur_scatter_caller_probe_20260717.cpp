#include "radialblur_scatter_caller.h"

#include <cmath>
#include <iostream>
#include <limits>
#include <vector>

int main() {
    constexpr int kRows = 3;
    constexpr int kAngles = 4;
    std::vector<float> outer(30000, 1.0f), inner(30000, 1.0f);
    const olm::radialblur::ScatterTailContext tail{
        1, 3, 2, 3, outer.data(), inner.data()};
    const olm::radialblur::ScatterCallerContext context{tail, 4, 6};
    std::vector<float> source_rgba(kRows * kAngles * 4, 0.0f);
    std::vector<float> source_alpha(kRows * kAngles, 0.0f);
    std::vector<float> span_gate(kRows * kAngles, 0.0f);
    std::vector<unsigned char> valid(kRows * kAngles, 1);
    const std::size_t active = kAngles;
    source_rgba[active * 4 + 0] = 2.0f;
    source_rgba[active * 4 + 1] = 3.0f;
    source_rgba[active * 4 + 2] = 5.0f;
    source_alpha[active] = 0.5f;
    span_gate[active] = 1.0f;
    std::vector<float> scatter(kRows * kAngles * 4, 0.0f);
    std::vector<float> maximum(kRows * kAngles, 0.0f);

    const bool ran = olm::radialblur::scatter_valid_polar_cells(
        context, {8, 1, kRows, kAngles, source_rgba.data(), source_alpha.data(),
                  span_gate.data(), valid.data()},
        {scatter.data(), maximum.data(), maximum.size()});
    if (!ran || scatter[(active + 1) * 4 + 1] == 0.0f || maximum[active + 1] == 0.0f ||
        scatter[1] != 0.0f || maximum[1] != 0.0f) {
        std::cerr << "unexpected adapter output\n";
        return 1;
    }
    std::vector<float> bounded_scatter(4, 7.0f);
    std::vector<float> bounded_maximum(1, 9.0f);
    if (olm::radialblur::scatter_valid_polar_cells(
            context, {8, 1, kRows, kAngles, source_rgba.data(), source_alpha.data(),
                      span_gate.data(), valid.data()},
            {bounded_scatter.data(), bounded_maximum.data(), bounded_maximum.size()}) ||
        bounded_scatter[0] != 7.0f || bounded_maximum[0] != 9.0f) {
        return 1;
    }

    struct GateCase {
        const char* name;
        unsigned char valid_value;
        float alpha_value;
        float span_value;
        bool expect_negative_write;
    };
    const GateCase gates[] = {
        {"valid=0", 0, 0.5f, 1.0f, false},
        {"alpha=0", 1, 0.0f, 1.0f, false},
        {"span=0", 1, 0.5f, 0.0f, false},
        {"alpha=NaN", 1, std::numeric_limits<float>::quiet_NaN(), 1.0f, false},
        {"span=NaN", 1, 0.5f, std::numeric_limits<float>::quiet_NaN(), false},
        {"alpha=-0.5", 1, -0.5f, 1.0f, true},
        {"span=-1", 1, 0.5f, -1.0f, false},
    };
    for (const GateCase& gate : gates) {
        std::vector<unsigned char> case_valid = valid;
        std::vector<float> case_alpha = source_alpha;
        std::vector<float> case_span = span_gate;
        case_valid[active] = gate.valid_value;
        case_alpha[active] = gate.alpha_value;
        case_span[active] = gate.span_value;
        std::vector<float> case_scatter(scatter.size(), 0.0f);
        std::vector<float> case_maximum(maximum.size(), 0.0f);
        if (!olm::radialblur::scatter_valid_polar_cells(
                context, {8, 1, kRows, kAngles, source_rgba.data(), case_alpha.data(),
                          case_span.data(), case_valid.data()},
                {case_scatter.data(), case_maximum.data(), case_maximum.size()})) {
            std::cerr << gate.name << " rejected\n";
            return 1;
        }
        bool negative_write = false;
        for (float value : case_scatter) {
            negative_write = negative_write || value < 0.0f;
            if (!gate.expect_negative_write && value != 0.0f) return 1;
        }
        if (negative_write != gate.expect_negative_write) return 1;
        for (float value : case_maximum) {
            if (value != 0.0f) return 1;
        }
    }

    const olm::radialblur::ScatterTailContext wrap_tail{
        1, 3, std::numeric_limits<int>::max(), 0, outer.data(), inner.data()};
    std::vector<float> wrap_scatter(kAngles * 4, 7.0f);
    std::vector<float> wrap_maximum(kAngles, 9.0f);
    const olm::radialblur::ScatterTailInput wrap_input{
        0, 1, 0, 0, kAngles, 1.0f, 2.0f, 3.0f, 5.0f, 1.0f};
    olm::radialblur::scatter_tail(
        wrap_tail, wrap_input, {wrap_scatter.data(), wrap_maximum.data(), wrap_maximum.size()});
    for (float value : wrap_scatter) {
        if (value != 7.0f) return 1;
    }
    for (float value : wrap_maximum) {
        if (value != 9.0f) return 1;
    }
    std::cout << "PASS\n";
    return 0;
}
