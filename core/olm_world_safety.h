#ifndef OLM_WORLD_SAFETY_H
#define OLM_WORLD_SAFETY_H

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <new>
#include <vector>

namespace olm {
namespace world_safety {

enum class Status {
    ok,
    null_data,
    empty_geometry,
    arithmetic_overflow,
    stride_too_small,
    geometry_mismatch,
    overlapping_payloads,
    out_of_memory
};

inline bool checked_multiply(std::size_t a, std::size_t b, std::size_t *result) noexcept
{
    if (!result) return false;
    if (a != 0 && b > std::numeric_limits<std::size_t>::max() / a) return false;
    *result = a * b;
    return true;
}

struct ConstWorld {
    const void *data;
    std::size_t width;
    std::size_t height;
    std::size_t row_bytes;
    std::size_t pixel_bytes;
};

struct MutableWorld {
    void *data;
    std::size_t width;
    std::size_t height;
    std::size_t row_bytes;
    std::size_t pixel_bytes;
};

struct Layout {
    std::size_t active_row_bytes;
    std::size_t addressable_bytes;
    std::size_t tight_bytes;
};

inline Status validate_layout(const ConstWorld &world, Layout *layout = nullptr) noexcept
{
    if (!world.data) return Status::null_data;
    if (world.width == 0 || world.height == 0 || world.pixel_bytes == 0)
        return Status::empty_geometry;

    Layout value = {};
    if (!checked_multiply(world.width, world.pixel_bytes, &value.active_row_bytes) ||
        !checked_multiply(value.active_row_bytes, world.height, &value.tight_bytes))
        return Status::arithmetic_overflow;
    if (world.row_bytes < value.active_row_bytes) return Status::stride_too_small;

    std::size_t preceding_rows = 0;
    if (!checked_multiply(world.height - 1, world.row_bytes, &preceding_rows) ||
        preceding_rows > std::numeric_limits<std::size_t>::max() - value.active_row_bytes)
        return Status::arithmetic_overflow;
    value.addressable_bytes = preceding_rows + value.active_row_bytes;
    if (layout) *layout = value;
    return Status::ok;
}

inline Status validate_layout(const MutableWorld &world, Layout *layout = nullptr) noexcept
{
    return validate_layout(ConstWorld{world.data, world.width, world.height,
                                      world.row_bytes, world.pixel_bytes}, layout);
}

struct AddressRange {
    std::uintptr_t begin;
    std::uintptr_t end; // one past the last addressable byte
};

inline Status address_range(const ConstWorld &world, AddressRange *range) noexcept
{
    if (!range) return Status::arithmetic_overflow;
    Layout layout = {};
    const Status status = validate_layout(world, &layout);
    if (status != Status::ok) return status;
    const std::uintptr_t begin = reinterpret_cast<std::uintptr_t>(world.data);
    if (layout.addressable_bytes > std::numeric_limits<std::uintptr_t>::max() - begin)
        return Status::arithmetic_overflow;
    range->begin = begin;
    range->end = begin + layout.addressable_bytes;
    return Status::ok;
}

inline bool ranges_overlap(const AddressRange &a, const AddressRange &b) noexcept
{
    return a.begin < b.end && b.begin < a.end;
}

inline Status require_disjoint(const ConstWorld &a, const ConstWorld &b) noexcept
{
    AddressRange ar = {}, br = {};
    Status status = address_range(a, &ar);
    if (status != Status::ok) return status;
    status = address_range(b, &br);
    if (status != Status::ok) return status;
    return ranges_overlap(ar, br) ? Status::overlapping_payloads : Status::ok;
}

class TightStaging {
public:
    Status prepare(const ConstWorld &input, const MutableWorld &output,
                   bool require_independent_payloads = true) noexcept
    {
        prepared_ = false;
        Layout input_layout = {}, output_layout = {};
        Status status = validate_layout(input, &input_layout);
        if (status != Status::ok) return status;
        status = validate_layout(output, &output_layout);
        if (status != Status::ok) return status;
        if (input.width != output.width || input.height != output.height ||
            input.pixel_bytes != output.pixel_bytes)
            return Status::geometry_mismatch;
        if (require_independent_payloads) {
            status = require_disjoint(input, ConstWorld{output.data, output.width, output.height,
                                                       output.row_bytes, output.pixel_bytes});
            if (status != Status::ok) return status;
        }

        try {
            input_.resize(input_layout.tight_bytes);
            output_.resize(output_layout.tight_bytes);
        } catch (const std::bad_alloc &) {
            input_.clear();
            output_.clear();
            return Status::out_of_memory;
        }
        const auto *source = static_cast<const std::uint8_t *>(input.data);
        const auto *old_output = static_cast<const std::uint8_t *>(output.data);
        for (std::size_t y = 0; y < input.height; ++y) {
            std::memcpy(input_.data() + y * input_layout.active_row_bytes,
                        source + y * input.row_bytes, input_layout.active_row_bytes);
            std::memcpy(output_.data() + y * output_layout.active_row_bytes,
                        old_output + y * output.row_bytes, output_layout.active_row_bytes);
        }
        destination_ = output;
        active_row_bytes_ = input_layout.active_row_bytes;
        prepared_ = true;
        return Status::ok;
    }

    const std::uint8_t *input_data() const noexcept { return input_.data(); }
    std::uint8_t *output_data() noexcept { return output_.data(); }
    std::size_t row_bytes() const noexcept { return active_row_bytes_; }
    std::size_t width() const noexcept { return destination_.width; }
    std::size_t height() const noexcept { return destination_.height; }

    Status commit() noexcept
    {
        if (!prepared_) return Status::empty_geometry;
        auto *destination = static_cast<std::uint8_t *>(destination_.data);
        for (std::size_t y = 0; y < destination_.height; ++y)
            std::memcpy(destination + y * destination_.row_bytes,
                        output_.data() + y * active_row_bytes_, active_row_bytes_);
        return Status::ok;
    }

private:
    MutableWorld destination_ = {};
    std::size_t active_row_bytes_ = 0;
    std::vector<std::uint8_t> input_;
    std::vector<std::uint8_t> output_;
    bool prepared_ = false;
};

} // namespace world_safety
} // namespace olm

#endif
