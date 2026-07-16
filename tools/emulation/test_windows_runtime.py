import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from windows_runtime import (  # noqa: E402
    GS_TLS_OFFSET,
    TLS_EPOCH_OFFSET,
    WindowsOpenCVRuntime,
)
from aex_loader import TEB_BASE  # noqa: E402


class FakeLoader:
    def __init__(self):
        self.cursor = 0x40000000
        self.memory = {}
        self.import_impls = {}

    def host_alloc(self, size, align=16):
        self.cursor = (self.cursor + align - 1) & ~(align - 1)
        address = self.cursor
        self.cursor += size
        return address

    def write_bytes(self, address, data):
        self.memory[address] = bytes(data)

    def register_import_impl(self, name, implementation):
        self.import_impls[name] = implementation


class WindowsRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.loader = FakeLoader()
        self.runtime = WindowsOpenCVRuntime(self.loader)
        self.state = self.runtime.install()

    def test_tls_epoch_is_uninitialized(self):
        self.assertEqual(self.state.epoch, -1)
        self.assertEqual(
            struct.unpack("<i", self.loader.memory[self.state.tls_slot + TLS_EPOCH_OFFSET])[0], -1
        )
        self.assertEqual(
            struct.unpack("<Q", self.loader.memory[self.state.gs_address])[0], self.state.tls_table
        )
        self.assertEqual(self.state.gs_address, TEB_BASE + GS_TLS_OFFSET)

    def test_fls_unset_then_set_and_get(self):
        alloc = self.loader.import_impls["FlsAlloc"]
        get = self.loader.import_impls["FlsGetValue"]
        set_value = self.loader.import_impls["FlsSetValue"]
        slot = alloc(None, [0])
        self.assertEqual(slot, self.state.fls_slot)
        self.assertEqual(get(None, [slot]), 0)
        self.assertEqual(set_value(None, [slot, 0x1234]), 1)
        self.assertEqual(get(None, [slot]), 0x1234)

    def test_fls_free_and_invalid_slots_fail_closed(self):
        alloc = self.loader.import_impls["FlsAlloc"]
        get = self.loader.import_impls["FlsGetValue"]
        set_value = self.loader.import_impls["FlsSetValue"]
        free = self.loader.import_impls["FlsFree"]
        slot = alloc(None, [0xDEADBEEF])
        self.assertEqual(set_value(None, [slot, 0x1234]), 1)
        self.assertEqual(free(None, [slot]), 1)
        self.assertEqual(get(None, [slot]), 0)
        self.assertEqual(set_value(None, [slot, 0x5678]), 0)
        self.assertEqual(free(None, [slot]), 0)
        self.assertEqual(set_value(None, [999, 1]), 0)

    def test_aligned_malloc_tracks_monotonic_host_allocation(self):
        malloc = self.loader.import_impls["_aligned_malloc"]
        first = malloc(None, [33, 64])
        second = malloc(None, [8, 256])
        self.assertEqual(first % 64, 0)
        self.assertEqual(second % 256, 0)
        self.assertGreater(second, first)
        self.assertEqual(self.state.aligned_allocations[first], {"size": 33, "alignment": 64})
        self.assertEqual(malloc(None, [8, 3]), 0)

    def test_report_metadata_is_deterministic_and_algorithm_free(self):
        report = self.runtime.report()
        self.assertEqual(
            {key: report[key] for key in ("schema", "mode", "teb", "tls", "fls", "aligned_allocator")},
            {
                "schema": "windows-opencv-runtime/1",
                "mode": "opt-in-loader-scaffold",
                "teb": {"gs_tls_offset": "0x58", "tls_index": 0},
                "tls": {"epoch_offset": "0x4", "initial_epoch": -1},
                "fls": {"unset_value": 0, "primary_slot": 0},
                "aligned_allocator": "monotonic host_alloc",
            },
        )
        self.assertNotIn("GaussianBlur", repr(report))


if __name__ == "__main__":
    unittest.main()
