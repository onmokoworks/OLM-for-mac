from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_checked_rect_halo_and_tile_budget() -> None:
    source = r'''
#include "core/olm_checked_rect.h"
#include <cassert>
#include <cstdint>
#include <limits>
using namespace olm::allocation;
using namespace olm::geometry;

int main() {
    std::size_t w = 0, h = 0;
    assert(dimensions(Rect64{-100, -50, 100, 50}, &w, &h));
    assert(w == 200 && h == 100);
    assert(!dimensions(Rect64{0, 0, 0, 1}, &w, &h));

    Rect64 expanded{};
    assert(expand(Rect64{0, 0, 1920, 1080}, 64, 32, &expanded));
    assert(expanded.left == -64 && expanded.top == -32);
    assert(expanded.right == 1984 && expanded.bottom == 1112);
    assert(!expand(Rect64{std::numeric_limits<std::int64_t>::min(), 0, 1, 1},
                   1, 0, &expanded));
    assert(!expand(Rect64{0, 0, std::numeric_limits<std::int64_t>::max(), 1},
                   1, 0, &expanded));

    const OverscanPolicy normal{256, 256, 4, 3840u * 2160u * 4u};
    std::size_t pixels = 0;
    assert(admit_overscan(Rect64{0, 0, 1920, 1080}, 64, 64,
                          normal, &expanded, &pixels));
    assert(pixels == 2048u * 1208u);
    assert(!admit_overscan(Rect64{0, 0, 1, 1}, 256, 256,
                           normal, &expanded, &pixels));
    assert(!admit_overscan(Rect64{0, 0, 1920, 1080}, 257, 0,
                           normal, &expanded, &pixels));

    // Three 512x512 RGBA float planes fit in 16 MiB; four do not.
    RenderBudget three(mib(16));
    const Rect64 tile{0, 0, 512, 512};
    assert(reserve_tile_planes(&three, tile, 4, 4, 3));
    RenderBudget four(mib(16));
    assert(!reserve_tile_planes(&four, tile, 4, 4, 5));

    // Geometry multiplication overflow must fail without consuming budget.
    RenderBudget overflow(std::numeric_limits<std::size_t>::max());
    const Rect64 huge{std::numeric_limits<std::int64_t>::min(), 0,
                      std::numeric_limits<std::int64_t>::max(), 2};
    assert(!reserve_tile_planes(&overflow, huge, 4, 4, 1));
    assert(overflow.used_bytes() == 0);
}
'''
    with tempfile.TemporaryDirectory(prefix="olm-rect-") as raw:
        temp = Path(raw)
        cpp = temp / "probe.cpp"
        exe = temp / "probe"
        cpp.write_text(source)
        built = subprocess.run(
            ["clang++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(ROOT), str(cpp), "-o", str(exe)],
            cwd=ROOT, text=True, capture_output=True,
        )
        assert built.returncode == 0, built.stderr
        ran = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        assert ran.returncode == 0, ran.stderr
