#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace olm::allocation {

// Arithmetic used to validate image geometry before constructing a vector.
// These helpers deliberately return false instead of saturating: a saturated
// byte count is not a safe allocation size.
constexpr bool checked_add(std::size_t left, std::size_t right,
                           std::size_t* result) noexcept {
    if (!result || right > std::numeric_limits<std::size_t>::max() - left) {
        return false;
    }
    *result = left + right;
    return true;
}

constexpr bool checked_mul(std::size_t left, std::size_t right,
                           std::size_t* result) noexcept {
    if (!result || (left != 0 && right > std::numeric_limits<std::size_t>::max() / left)) {
        return false;
    }
    *result = left * right;
    return true;
}

constexpr bool image_bytes(std::size_t width, std::size_t height,
                           std::size_t channels, std::size_t bytes_per_channel,
                           std::size_t* result) noexcept {
    std::size_t pixels = 0;
    std::size_t samples = 0;
    return width != 0 && height != 0 && channels != 0 && bytes_per_channel != 0 &&
           checked_mul(width, height, &pixels) &&
           checked_mul(pixels, channels, &samples) &&
           checked_mul(samples, bytes_per_channel, result);
}

constexpr bool row_bytes(std::size_t width, std::size_t channels,
                         std::size_t bytes_per_channel,
                         std::size_t* result) noexcept {
    std::size_t samples = 0;
    return width != 0 && channels != 0 && bytes_per_channel != 0 &&
           checked_mul(width, channels, &samples) &&
           checked_mul(samples, bytes_per_channel, result);
}

// A lightweight, per-render estimator. It does not own memory; callers reserve
// every simultaneously-live plane before allocating it. Failed reservations do
// not mutate the accumulated total, allowing a clean fail-closed render path.
class RenderBudget {
public:
    explicit constexpr RenderBudget(std::size_t limit_bytes) noexcept
        : limit_bytes_(limit_bytes), used_bytes_(0) {}

    constexpr bool reserve_bytes(std::size_t bytes) noexcept {
        std::size_t next = 0;
        if (!checked_add(used_bytes_, bytes, &next) || next > limit_bytes_) {
            return false;
        }
        used_bytes_ = next;
        return true;
    }

    constexpr bool reserve_image(std::size_t width, std::size_t height,
                                 std::size_t channels,
                                 std::size_t bytes_per_channel,
                                 std::size_t copies = 1) noexcept {
        std::size_t one = 0;
        std::size_t all = 0;
        return image_bytes(width, height, channels, bytes_per_channel, &one) &&
               checked_mul(one, copies, &all) && reserve_bytes(all);
    }

    constexpr std::size_t used_bytes() const noexcept { return used_bytes_; }
    constexpr std::size_t limit_bytes() const noexcept { return limit_bytes_; }
    constexpr std::size_t remaining_bytes() const noexcept {
        return limit_bytes_ - used_bytes_;
    }

private:
    std::size_t limit_bytes_;
    std::size_t used_bytes_;
};

constexpr std::size_t mib(std::size_t count) noexcept {
    return count <= std::numeric_limits<std::size_t>::max() / (1024u * 1024u)
               ? count * 1024u * 1024u
               : std::numeric_limits<std::size_t>::max();
}

}  // namespace olm::allocation
