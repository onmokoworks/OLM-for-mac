from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_checked_allocation_header_contract() -> None:
    source = r'''
#include "core/olm_checked_allocation.h"
#include <cassert>
#include <cstddef>
#include <limits>

using namespace olm::allocation;

static_assert([] { std::size_t n = 0; return checked_mul(3840, 2160, &n) && n == 8294400; }());
static_assert([] { std::size_t n = 0; return image_bytes(3840, 2160, 4, 4, &n) && n == 132710400; }());
static_assert([] { std::size_t n = 0; return row_bytes(3840, 4, 4, &n) && n == 61440; }());

int main() {
    std::size_t value = 123;
    assert(!checked_add(std::numeric_limits<std::size_t>::max(), 1, &value));
    assert(value == 123);
    assert(!checked_mul(std::numeric_limits<std::size_t>::max(), 2, &value));
    assert(value == 123);
    assert(!image_bytes(0, 2160, 4, 4, &value));
    assert(!image_bytes(std::numeric_limits<std::size_t>::max(), 2, 4, 4, &value));

    // Three live 4K RGBA float planes fit under 500 MiB.
    RenderBudget normal(mib(500));
    assert(normal.reserve_image(3840, 2160, 4, sizeof(float), 3));
    assert(normal.used_bytes() == 398131200);

    // A fourth plane is rejected without changing the committed estimate.
    const std::size_t before = normal.used_bytes();
    assert(!normal.reserve_image(3840, 2160, 4, sizeof(float)));
    assert(normal.used_bytes() == before);

    // The DirectionalBlur-style 4406-square triple RGBA workspace exceeds 1 GiB
    // after its two scalar planes are included, and must fail closed.
    RenderBudget directional(mib(1024));
    assert(directional.reserve_image(4406, 4406, 4, sizeof(float), 3));
    assert(!directional.reserve_image(4406, 4406, 1, sizeof(float), 2));

    RenderBudget overflow(std::numeric_limits<std::size_t>::max());
    assert(!overflow.reserve_image(std::numeric_limits<std::size_t>::max(), 2, 4, 4));
}
'''
    with tempfile.TemporaryDirectory(prefix="olm-allocation-") as raw:
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
