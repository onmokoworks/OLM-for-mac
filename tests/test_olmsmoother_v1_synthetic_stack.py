"""Exercise synthetic-address translation with fatal ASan/UBSan, including edges."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / 'orchestra/state/F22-smoother-classifier-stack-ub'

HARNESS = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

template<class T, class M, class Read, class Write>
void accesses(M &m, Read read, Write write) {
    const T value = T(0x123456789abcdef0ull);
    for (size_t offset = 0; offset + sizeof(T) <= sizeof(m.stack); ++offset) {
        memset(m.stack, 0xa5, sizeof(m.stack));
        write(M::kStack + offset, value);
        assert(read(M::kStack + offset) == value);
        uint8_t expected[sizeof(m.stack)];
        memset(expected, 0xa5, sizeof(expected));
        memcpy(expected + offset, &value, sizeof(value));
        assert(memcmp(m.stack, expected, sizeof(expected)) == 0);
    }
    // Native pointers still bypass synthetic translation; deliberately unaligned.
    uint8_t native[sizeof(T) + 2];
    memset(native, 0xa5, sizeof(native));
    const uint64_t address = (uintptr_t)(native + 1);
    assert(!m.is_stack(address, sizeof(T)));
    write(address, value);
    assert(read(address) == value);
    assert(memcmp(native + 1, &value, sizeof(value)) == 0);
    assert(native[0] == 0xa5 && native[sizeof(native)-1] == 0xa5);
}

template<class M> void common(M &m) {
    accesses<uint8_t>(m, [&](auto a){return m.read8(a);},
                        [&](auto a, auto v){m.write8(a,v);});
    accesses<uint32_t>(m, [&](auto a){return m.read32(a);},
                         [&](auto a, auto v){m.write32(a,v);});
    accesses<uint64_t>(m, [&](auto a){return m.read64(a);},
                         [&](auto a, auto v){m.write64(a,v);});
    for (size_t width : {size_t(1), size_t(2), size_t(4), size_t(8)}) {
        assert(m.is_stack(M::kStack, width));
        assert(m.is_stack(M::kStack + sizeof(m.stack) - width, width));
        assert(!m.is_stack(M::kStack - 1, width));
        assert(!m.is_stack(M::kStack + sizeof(m.stack) - width + 1, width));
        assert(!m.is_stack(UINT64_MAX, width));
        assert(!m.is_stack(UINT64_MAX - width + 1, width));
    }
    assert(m.is_stack(M::kStack, sizeof(m.stack)));
    assert(!m.is_stack(M::kStack, sizeof(m.stack) + 1));
    assert(!m.is_stack(M::kStack, SIZE_MAX));
}

int main() {
    Classifier8TailMemory classifier;
    SubHandler8Memory subhandler;
    common(classifier);
    common(subhandler);
    accesses<uint16_t>(subhandler, [&](auto a){return subhandler.read16(a);},
                                  [&](auto a, auto v){subhandler.write16(a,v);});
    for (size_t offset = 0; offset < sizeof(subhandler.stack); ++offset)
        assert(subhandler.ptr(SubHandler8Memory::kStack + offset) == subhandler.stack + offset);
    uint8_t native = 0;
    assert(subhandler.ptr((uintptr_t)&native) == &native);
}
'''


class SyntheticStack(unittest.TestCase):
    def test_all_offsets_widths_and_native_fallback_sanitized(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            directory = Path(directory)
            env = dict(os.environ, TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory),
                       ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                       UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            source, binary = directory / 'probe.cpp', directory / 'probe'
            source.write_text(HARNESS)
            build = subprocess.run(
                ['clang++', '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
                 '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-g', '-I', str(ROOT),
                 '-I', str(ROOT / 'cli/OLMSmoother/shim'), str(source), '-o', str(binary)],
                env=env, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(binary)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
