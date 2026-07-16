#include "../../core/radialblur_scatter_tail.h"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::uint32_t read_u32(std::istream& input) {
    std::uint32_t value = 0;
    input.read(reinterpret_cast<char*>(&value), sizeof(value));
    if (!input) throw std::runtime_error("truncated fixture vector");
    return value;
}

std::int32_t read_i32(std::istream& input) {
    return static_cast<std::int32_t>(read_u32(input));
}

float read_f32_bits(std::istream& input) {
    std::uint32_t raw = read_u32(input);
    float value;
    std::memcpy(&value, &raw, sizeof(value));
    return value;
}

std::uint32_t bits(float value) {
    std::uint32_t raw;
    std::memcpy(&raw, &value, sizeof(raw));
    return raw;
}

void write_table(std::vector<float>& table, double start, double increment) {
    for (std::size_t i = 0; i < table.size(); ++i) {
        volatile float value = static_cast<float>(start + static_cast<double>(i) * increment);
        table[i] = value;
    }
}

struct Fixture {
    std::string name;
    int direction;
    int mode;
    int base_length;
    int caller_distance;
    int angular;
    int radius;
    int angular_count;
    float span_gate;
    float source_alpha;
    float source_r;
    float source_g;
    float source_b;
    std::vector<std::pair<std::uint32_t, float>> initial_max;
    std::vector<std::uint32_t> expected_scatter;
    std::vector<std::uint32_t> expected_max;
};

Fixture read_fixture(std::istream& input) {
    const std::uint32_t name_size = read_u32(input);
    Fixture fixture;
    fixture.name.resize(name_size);
    input.read(fixture.name.data(), static_cast<std::streamsize>(name_size));
    if (!input) throw std::runtime_error("truncated fixture name");
    fixture.direction = read_i32(input);
    fixture.mode = read_i32(input);
    fixture.base_length = read_i32(input);
    fixture.caller_distance = read_i32(input);
    fixture.angular = read_i32(input);
    fixture.radius = read_i32(input);
    fixture.angular_count = read_i32(input);
    fixture.span_gate = read_f32_bits(input);
    fixture.source_alpha = read_f32_bits(input);
    fixture.source_r = read_f32_bits(input);
    fixture.source_g = read_f32_bits(input);
    fixture.source_b = read_f32_bits(input);

    const std::uint32_t max_seed_count = read_u32(input);
    fixture.initial_max.reserve(max_seed_count);
    for (std::uint32_t i = 0; i < max_seed_count; ++i) {
        fixture.initial_max.emplace_back(read_u32(input), read_f32_bits(input));
    }
    const std::uint32_t scatter_count = read_u32(input);
    fixture.expected_scatter.reserve(scatter_count);
    for (std::uint32_t i = 0; i < scatter_count; ++i) {
        fixture.expected_scatter.push_back(read_u32(input));
    }
    const std::uint32_t max_count = read_u32(input);
    fixture.expected_max.reserve(max_count);
    for (std::uint32_t i = 0; i < max_count; ++i) {
        fixture.expected_max.push_back(read_u32(input));
    }
    return fixture;
}

bool run_fixture(const Fixture& fixture, std::string& failure) {
    constexpr std::size_t table_size = 30000;
    std::vector<float> outer(table_size), inner(table_size);
    write_table(outer, 0.001f, 0.000031);
    write_table(inner, 0.007f, 0.000047);

    if (fixture.expected_scatter.size() % 4 != 0 ||
        fixture.expected_max.size() * 4 != fixture.expected_scatter.size()) {
        failure = "buffer shape mismatch";
        return false;
    }
    const std::size_t cell_count = fixture.expected_max.size();
    std::vector<float> scatter(fixture.expected_scatter.size(), 0.0f);
    std::vector<float> maxima(cell_count, 0.0f);
    for (const auto& seed : fixture.initial_max) {
        if (seed.first >= maxima.size()) {
            failure = "max-alpha seed out of range";
            return false;
        }
        maxima[seed.first] = seed.second;
    }

    const olm::radialblur::ScatterTailContext context{
        fixture.direction == 0 ? fixture.mode : 0,
        fixture.direction == 1 ? fixture.mode : 0,
        fixture.direction == 0 ? fixture.base_length : 0,
        fixture.direction == 1 ? fixture.base_length : 0,
        outer.data(), inner.data()};
    const olm::radialblur::ScatterTailInput input{
        fixture.direction, fixture.caller_distance, fixture.angular, fixture.radius,
        fixture.angular_count, fixture.source_alpha, fixture.source_r, fixture.source_g,
        fixture.source_b, fixture.span_gate};
    olm::radialblur::scatter_tail(context, input, {scatter.data(), maxima.data(), cell_count});

    for (std::size_t i = 0; i < scatter.size(); ++i) {
        if (bits(scatter[i]) != fixture.expected_scatter[i]) {
            failure = "scatter word " + std::to_string(i) + " expected 0x" +
                      std::to_string(fixture.expected_scatter[i]) + " got 0x" +
                      std::to_string(bits(scatter[i]));
            return false;
        }
    }
    for (std::size_t i = 0; i < maxima.size(); ++i) {
        if (bits(maxima[i]) != fixture.expected_max[i]) {
            failure = "max-alpha word " + std::to_string(i);
            return false;
        }
    }
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: radialblur_scatter_tail_probe <fixture-vector>\n";
        return 2;
    }
    std::ifstream input(argv[1], std::ios::binary);
    if (!input) {
        std::cerr << "cannot open fixture vector\n";
        return 2;
    }
    try {
        const std::uint32_t magic = read_u32(input);
        const std::uint32_t version = read_u32(input);
        if (magic != 0x31544252 || version != 1) throw std::runtime_error("bad fixture vector header");
        const std::uint32_t count = read_u32(input);
        for (std::uint32_t i = 0; i < count; ++i) {
            const Fixture fixture = read_fixture(input);
            std::string failure;
            const bool ok = run_fixture(fixture, failure);
            std::cout << fixture.name << "\t" << (ok ? "PASS" : "FAIL") << "\n";
            if (!ok) {
                std::cerr << fixture.name << ": " << failure << "\n";
                return 1;
            }
        }
        std::cout << "ALL_EXACT\t" << count << "\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        return 2;
    }
    return 0;
}
