"""Opt-in Windows/OpenCV runtime pieces for isolated AEX emulation.

This module deliberately does not change :class:`AexLoader`.  A caller opts in
by constructing ``WindowsOpenCVRuntime(loader)`` and calling ``install()``.
The layout and callback behavior mirror the small scaffold used by the Mode 3
actual-AEX probe, without implementing any plugin or OpenCV algorithm. This is
a bounded single-thread storage contract, not a complete Windows FLS runtime.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any

try:
    from .aex_loader import TEB_BASE
except ImportError:  # Direct execution/import from tools/emulation.
    from aex_loader import TEB_BASE


GS_TLS_OFFSET = 0x58
TLS_EPOCH_OFFSET = 0x04
TLS_BLOCK_SIZE = 0x100
TLS_TABLE_SIZE = 0x100
UNINITIALIZED_THREAD_EPOCH = -1
NULL = 0


@dataclass(frozen=True)
class WindowsOpenCVRuntimeState:
    """Guest addresses and stable semantic values installed by the scaffold."""

    gs_address: int
    tls_table: int
    tls_slot: int
    tls_index: int = 0
    epoch: int = UNINITIALIZED_THREAD_EPOCH
    fls_slot: int = 0
    aligned_allocations: dict[int, dict[str, int]] = field(default_factory=dict)


class WindowsOpenCVRuntime:
    """Install the minimum single-thread TLS/FLS storage contract."""

    def __init__(self, loader: Any, *, teb_base: int = TEB_BASE) -> None:
        self.loader = loader
        self.teb_base = teb_base
        self.state: WindowsOpenCVRuntimeState | None = None
        self._fls_values: dict[int, int] = {}
        self._allocated_fls: set[int] = set()
        self._next_fls_slot = 0
        self._aligned_allocations: dict[int, dict[str, int]] = {}

    def install(self) -> WindowsOpenCVRuntimeState:
        """Install guest memory and import callbacks, returning its state."""
        if self.state is not None:
            return self.state

        tls_table = self.loader.host_alloc(TLS_TABLE_SIZE, align=16)
        tls_slot = self.loader.host_alloc(TLS_BLOCK_SIZE, align=16)
        self.loader.write_bytes(tls_table, b"\x00" * TLS_TABLE_SIZE)
        self.loader.write_bytes(tls_slot, b"\x00" * TLS_BLOCK_SIZE)
        self.loader.write_bytes(tls_table, struct.pack("<Q", tls_slot))
        self.loader.write_bytes(tls_slot + TLS_EPOCH_OFFSET, struct.pack("<i", UNINITIALIZED_THREAD_EPOCH))
        gs_address = self.teb_base + GS_TLS_OFFSET
        self.loader.write_bytes(gs_address, struct.pack("<Q", tls_table))

        self.loader.register_import_impl("FlsAlloc", self.fls_alloc)
        self.loader.register_import_impl("FlsGetValue", self.fls_get)
        self.loader.register_import_impl("FlsSetValue", self.fls_set)
        self.loader.register_import_impl("FlsFree", self.fls_free)
        self.loader.register_import_impl("_aligned_malloc", self.aligned_malloc)
        self.loader.register_import_impl("_aligned_free", self.aligned_free)

        self.state = WindowsOpenCVRuntimeState(
            gs_address=gs_address,
            tls_table=tls_table,
            tls_slot=tls_slot,
            aligned_allocations=self._aligned_allocations,
        )
        return self.state

    def fls_alloc(self, _uc: Any, _args: list[int]) -> int:
        slot = self._next_fls_slot
        self._next_fls_slot += 1
        self._allocated_fls.add(slot)
        return slot

    def fls_get(self, _uc: Any, args: list[int]) -> int:
        slot = int(args[0])
        return self._fls_values.get(slot, NULL)

    def fls_set(self, _uc: Any, args: list[int]) -> int:
        slot, value = int(args[0]), int(args[1])
        if slot not in self._allocated_fls:
            return 0
        self._fls_values[slot] = value
        return 1

    def fls_free(self, _uc: Any, args: list[int]) -> int:
        slot = int(args[0])
        if slot not in self._allocated_fls:
            return 0
        self._allocated_fls.remove(slot)
        self._fls_values.pop(slot, None)
        return 1

    def aligned_malloc(self, _uc: Any, args: list[int]) -> int:
        size, alignment = int(args[0]), int(args[1])
        if size <= 0 or alignment <= 0 or alignment & (alignment - 1):
            return NULL
        pointer = self.loader.host_alloc(size, align=alignment)
        self.loader.write_bytes(pointer, b"\x00" * size)
        self._aligned_allocations[pointer] = {"size": size, "alignment": alignment}
        return pointer

    def aligned_free(self, _uc: Any, args: list[int]) -> int:
        self._aligned_allocations.pop(int(args[0]), None)
        return 0

    def report(self) -> dict[str, Any]:
        """Return stable metadata plus the current allocation bookkeeping."""
        return {
            "schema": "windows-opencv-runtime/1",
            "mode": "opt-in-loader-scaffold",
            "teb": {"gs_tls_offset": hex(GS_TLS_OFFSET), "tls_index": 0},
            "tls": {"epoch_offset": hex(TLS_EPOCH_OFFSET), "initial_epoch": UNINITIALIZED_THREAD_EPOCH},
            "fls": {"unset_value": NULL, "primary_slot": 0},
            "aligned_allocator": "monotonic host_alloc",
            "state": self.state,
            "aligned_allocations": dict(self._aligned_allocations),
        }
