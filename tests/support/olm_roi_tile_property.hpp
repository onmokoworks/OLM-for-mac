#ifndef OLM_ROI_TILE_PROPERTY_HPP
#define OLM_ROI_TILE_PROPERTY_HPP

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace olm::roi_property {

struct Rect { int left, top, right, bottom; };

inline int width(Rect r) { return r.right - r.left; }
inline int height(Rect r) { return r.bottom - r.top; }

struct Plane {
    int width = 0, height = 0, origin_x = 0, origin_y = 0;
    std::size_t rowbytes = 0;
    std::vector<std::uint8_t> storage;
    std::uint8_t *row(int y) { return storage.data() + std::size_t(y) * rowbytes; }
    const std::uint8_t *row(int y) const { return storage.data() + std::size_t(y) * rowbytes; }
};

inline Plane make_plane(int w, int h, std::size_t padding, std::uint8_t sentinel = 0xa5) {
    if (w <= 0 || h <= 0) throw std::invalid_argument("non-positive plane");
    Plane p; p.width = w; p.height = h; p.rowbytes = std::size_t(w) * 4 + padding;
    p.storage.assign(p.rowbytes * std::size_t(h), sentinel); return p;
}

inline Plane deterministic_source(int w, int h, std::size_t padding) {
    Plane p = make_plane(w, h, padding);
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) {
        auto *q = p.row(y) + x * 4;
        q[0] = std::uint8_t((x * 17 + y * 29 + 3) & 255);
        q[1] = std::uint8_t((x * 43 + y * 7 + 19) & 255);
        q[2] = std::uint8_t((x * 5 + y * 61 + 101) & 255);
        q[3] = std::uint8_t((x * 13 + y * 11 + 127) & 255);
    }
    return p;
}

inline Plane extract_with_halo(const Plane &src, Rect output, int halo,
                               std::size_t padding, std::uint8_t sentinel = 0xa5) {
    if (halo < 0 || output.left < 0 || output.top < 0 ||
        output.right > src.width || output.bottom > src.height ||
        width(output) <= 0 || height(output) <= 0) throw std::invalid_argument("invalid tile");
    Rect in{std::max(0, output.left - halo), std::max(0, output.top - halo),
            std::min(src.width, output.right + halo), std::min(src.height, output.bottom + halo)};
    Plane tile = make_plane(width(in), height(in), padding, sentinel);
    tile.origin_x = in.left; tile.origin_y = in.top;
    for (int y = 0; y < tile.height; ++y)
        std::copy_n(src.row(in.top + y) + in.left * 4, tile.width * 4, tile.row(y));
    return tile;
}

inline bool padding_is(const Plane &p, std::uint8_t sentinel = 0xa5) {
    const std::size_t active = std::size_t(p.width) * 4;
    for (int y = 0; y < p.height; ++y)
        for (std::size_t x = active; x < p.rowbytes; ++x)
            if (p.row(y)[x] != sentinel) return false;
    return true;
}

inline void compose(Plane &full, const Plane &tile, Rect output) {
    if (tile.width != width(output) || tile.height != height(output))
        throw std::invalid_argument("tile/output shape mismatch");
    for (int y = 0; y < tile.height; ++y)
        std::copy_n(tile.row(y), tile.width * 4, full.row(output.top + y) + output.left * 4);
}

// Test oracle: a radius-one box filter. Plugin harnesses can reuse all geometry
// helpers above and substitute their own full-frame and tile worker callbacks.
inline Plane box3(const Plane &input, Rect output, int frame_width, int frame_height,
                  std::size_t output_padding) {
    if (output.left < input.origin_x || output.top < input.origin_y ||
        output.right > input.origin_x + input.width ||
        output.bottom > input.origin_y + input.height) throw std::invalid_argument("output outside input");
    Plane out = make_plane(width(output), height(output), output_padding);
    out.origin_x = output.left; out.origin_y = output.top;
    for (int gy = output.top; gy < output.bottom; ++gy) for (int gx = output.left; gx < output.right; ++gx) {
        for (int c = 0; c < 4; ++c) {
            int sum = 0, count = 0;
            for (int dy = -1; dy <= 1; ++dy) for (int dx = -1; dx <= 1; ++dx) {
                const int x = gx + dx, y = gy + dy;
                if (x < 0 || y < 0 || x >= frame_width || y >= frame_height) continue;
                if (x < input.origin_x || y < input.origin_y ||
                    x >= input.origin_x + input.width || y >= input.origin_y + input.height)
                    throw std::runtime_error("insufficient halo");
                sum += input.row(y - input.origin_y)[(x - input.origin_x) * 4 + c]; ++count;
            }
            out.row(gy - output.top)[(gx - output.left) * 4 + c] = std::uint8_t(sum / count);
        }
    }
    return out;
}

inline std::vector<Rect> representative_tiles() {
    return {{0,0,9,7}, {9,0,24,7}, {24,0,37,7},
            {0,7,9,18}, {9,7,24,18}, {24,7,37,18},
            {0,18,9,29}, {9,18,24,29}, {24,18,37,29}};
}

} // namespace olm::roi_property
#endif
