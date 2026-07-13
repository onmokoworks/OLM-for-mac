"""
aex_loader.py -- Milestone 1 PE loader / Unicorn harness for OLM .aex plugins (x86-64).

Loads a Windows PE64 .aex DLL into a Unicorn CPU_X86_64 emulator, maps its
sections at (or relocated from) the PE's preferred ImageBase, resolves the
import table with Python hook stubs, and exposes a Windows x64 calling
convention `call_function()` helper so individual internal functions
(FUN_XXXXXXXX per the Ghidra decomp/disasm) can be invoked directly without
needing to boot a full After Effects host process.

Scope (Milestone 1): enough to call leaf/near-leaf functions that mostly do
arithmetic on caller-supplied buffers. Not a general Win32 loader -- there is
no TLS callback support, no SEH unwinding, no real heap, and only a handful
of imports have real implementations (the rest log + return 0).

See tools/emulation/README.md for usage and current limitations.
"""

from __future__ import annotations

import ctypes
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import pefile
from unicorn import (
    Uc,
    UC_ARCH_X86,
    UC_MODE_64,
    UC_HOOK_CODE,
    UC_HOOK_MEM_UNMAPPED,
    UC_HOOK_MEM_INVALID,
    UC_HOOK_MEM_READ,
    UC_PROT_ALL,
    UC_PROT_READ,
    UC_PROT_WRITE,
    UC_PROT_EXEC,
    UcError,
)
from unicorn.x86_const import (
    UC_X86_REG_RAX,
    UC_X86_REG_RBX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RSI,
    UC_X86_REG_RDI,
    UC_X86_REG_RBP,
    UC_X86_REG_RSP,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_R10,
    UC_X86_REG_R11,
    UC_X86_REG_R12,
    UC_X86_REG_R13,
    UC_X86_REG_R14,
    UC_X86_REG_R15,
    UC_X86_REG_RIP,
    UC_X86_REG_XMM0,
    UC_X86_REG_XMM1,
    UC_X86_REG_XMM2,
    UC_X86_REG_XMM3,
)

PAGE_SIZE = 0x1000

_XMM_REGS = [UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3]


def align_up(value: int, align: int = PAGE_SIZE) -> int:
    return (value + align - 1) & ~(align - 1)


# ---------------------------------------------------------------------------
# Memory map layout (all addresses are guest/emulated addresses)
# ---------------------------------------------------------------------------
#
#   0x180000000 .. +SizeOfImage      the mapped PE image (code/data/rdata/...)
#   0x0f000000 .. +STACK_SIZE        the emulated stack (grows down from top)
#   0x20000000 .. +HEAP_SIZE         bump-allocator heap for malloc()/scratch
#   0x30000000                       "return trampoline" -- a single HLT-like
#                                     RET instruction call_function() uses as
#                                     a fake return address so we know when
#                                     the called function has finished.
#
# These regions are placed well away from the image base and from each other
# to keep pointer-vs-pointer confusion unlikely during debugging.

STACK_BASE = 0x0F000000
STACK_SIZE = 0x00100000  # 1 MiB
HEAP_BASE = 0x20000000
HEAP_SIZE = 0x01000000  # 16 MiB initial; grows on demand
RETURN_TRAMPOLINE = 0x90000000
IMPORT_STUB_BASE = 0x71000000  # each imported function gets a small stub here
IMPORT_STUB_STRIDE = 0x10
CALLBACK_STUB_BASE = 0x82000000  # host-callback (emulated suite) stubs live here
CALLBACK_STUB_SIZE = 0x00100000
CALLBACK_STUB_STRIDE = 0x10
HOST_STRUCT_BASE = 0x40000000  # scratch region for emulated AE host structs
HOST_STRUCT_SIZE = 0x00400000  # 4 MiB initial; grows on demand
# Windows Thread Environment Block. Large-frame functions in the .aex call
# __chkstk (e.g. 0x18001d000), which reads GS:[0x10] (StackLimit) and GS:[0x8]
# (StackBase) to probe the guard page. GS base must point here and the TEB
# stack-bound fields must bracket the emulated stack, or the probe faults with
# UC_ERR_READ_UNMAPPED. This did not surface in M1-M3 because those small leaf
# functions had frames below the __chkstk threshold.
TEB_BASE = 0x50000000
TEB_SIZE = 0x00010000  # 64 KiB
IA32_GS_BASE_MSR = 0xC0000101


@dataclass
class ImportCallLog:
    name: str
    dll: str
    args: List[int] = field(default_factory=list)
    ret: int = 0


class AexLoader:
    """Loads one .aex PE64 image into a fresh Unicorn instance."""

    def __init__(self, aex_path: str, verbose: bool = True, fast: bool = False):
        self.path = Path(aex_path)
        if not self.path.exists():
            raise FileNotFoundError(f".aex not found: {aex_path}")

        self.verbose = verbose
        # fast mode: register the code hook ONLY over the stub/callback/
        # trampoline address window (0x30000000-0x33000000) so it never fires
        # on normal .text execution. This removes the per-instruction Python
        # callback -- the dominant Unicorn slowdown -- at the cost of losing
        # the exact instruction counter (only stub/callback hits are counted).
        # Needed to run real-scale (1920x1080) renders in bounded wall clock.
        self.fast = fast
        self.pe = pefile.PE(str(self.path), fast_load=True)
        self.pe.parse_data_directories(directories=[
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_BASERELOC"],
        ])

        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.size_of_image = align_up(self.pe.OPTIONAL_HEADER.SizeOfImage)
        self.load_base = self.image_base  # we load at preferred base (no clash expected)

        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)

        # import_addr (guest VA of the IAT slot) -> (dll, name)
        self.import_slots: Dict[int, tuple] = {}
        # stub_addr -> (dll, name) ; the actual code address each IAT slot points to
        self.import_stubs: Dict[int, tuple] = {}
        self.import_log: List[ImportCallLog] = []
        self.instructions_executed = 0

        # name -> python callable(uc, args:list[int]) -> int   (real implementations)
        self.import_impls: Dict[str, Callable[[Uc, List[int]], int]] = {}
        self._register_default_impls()

        # Generalized host callbacks (emulated AE suite functions, sampler
        # trampolines, etc). addr -> (label, handler(loader, args)->int|None)
        self.callbacks: Dict[int, tuple] = {}
        self._callback_cursor = CALLBACK_STUB_BASE
        self.callback_log: List[tuple] = []
        self._code_hooks: List[object] = []

        # Optional read-access tracing (used to enumerate context-struct
        # offsets). List of (lo, hi) ranges; when non-empty a MEM_READ hook
        # records every read that lands inside one of them.
        self.read_trace_ranges: List[tuple] = []
        self.read_trace: List[tuple] = []  # (base_label, offset, size, rip)
        self._read_hook_installed = False

        self._map_image()
        self._map_stack()
        self._map_heap()
        self._map_return_trampoline()
        self._map_callback_region()
        self._map_host_region()
        self._map_teb()
        self._resolve_imports()

        if self.fast:
            # Only hook the region containing trampoline (0x30000000),
            # import stubs (0x31000000) and callback stubs (0x32000000).
            self.uc.hook_add(UC_HOOK_CODE, self._on_code,
                             begin=RETURN_TRAMPOLINE, end=CALLBACK_STUB_BASE + CALLBACK_STUB_SIZE)
        else:
            self.uc.hook_add(UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(UC_HOOK_MEM_UNMAPPED | UC_HOOK_MEM_INVALID, self._on_bad_mem)

        self._heap_cursor = HEAP_BASE
        self._host_cursor = HOST_STRUCT_BASE
        self._heap_mapped_size = HEAP_SIZE
        self._host_mapped_size = HOST_STRUCT_SIZE

    # -- logging -----------------------------------------------------------
    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[aex_loader] {msg}")

    # -- image mapping -------------------------------------------------------
    def _map_image(self) -> None:
        self.uc.mem_map(self.load_base, self.size_of_image, UC_PROT_ALL)

        # Header + all sections are copied in verbatim at their virtual offsets;
        # gaps (e.g. bss-like padding) are left zero (mem_map zero-fills).
        header_data = self.pe.header
        self.uc.mem_write(self.load_base, bytes(header_data))

        for section in self.pe.sections:
            va = self.load_base + section.VirtualAddress
            raw = section.get_data()
            self.uc.mem_write(va, raw)

        delta = self.load_base - self.image_base
        if delta != 0:
            self._apply_relocations(delta)

        self._log(
            f"mapped {self.path.name} at 0x{self.load_base:x} "
            f"(size 0x{self.size_of_image:x}, delta 0x{delta:x})"
        )

    def _apply_relocations(self, delta: int) -> None:
        """Apply base relocations if load_base != preferred ImageBase."""
        if not hasattr(self.pe, "DIRECTORY_ENTRY_BASERELOC"):
            return
        count = 0
        for entry in self.pe.DIRECTORY_ENTRY_BASERELOC:
            for reloc in entry.entries:
                if reloc.type == 0:  # IMAGE_REL_BASED_ABSOLUTE
                    continue
                if reloc.type == 10:  # IMAGE_REL_BASED_DIR64
                    va = self.load_base + reloc.rva
                    orig = struct.unpack("<Q", self.uc.mem_read(va, 8))[0]
                    self.uc.mem_write(va, struct.pack("<Q", orig + delta))
                    count += 1
                else:
                    raise NotImplementedError(
                        f"Unsupported relocation type {reloc.type} at rva 0x{reloc.rva:x}"
                    )
        self._log(f"applied {count} relocations (delta 0x{delta:x})")

    # -- stack / heap ----------------------------------------------------
    def _map_stack(self) -> None:
        self.uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)

    def _map_heap(self) -> None:
        self.uc.mem_map(HEAP_BASE, HEAP_SIZE, UC_PROT_READ | UC_PROT_WRITE)

    def _map_return_trampoline(self) -> None:
        # 0xC3 = RET. call_function() pushes this address as the return
        # address before jumping into the target function; when the target
        # RETs, execution lands here and emu_stop() is called from the code
        # hook so we can inspect final register state.
        self.uc.mem_map(RETURN_TRAMPOLINE, PAGE_SIZE, UC_PROT_ALL)
        self.uc.mem_write(RETURN_TRAMPOLINE, b"\xc3")

    def _map_callback_region(self) -> None:
        self.uc.mem_map(CALLBACK_STUB_BASE, CALLBACK_STUB_SIZE, UC_PROT_ALL)

    def _map_host_region(self) -> None:
        self.uc.mem_map(HOST_STRUCT_BASE, HOST_STRUCT_SIZE, UC_PROT_READ | UC_PROT_WRITE)

    def _map_teb(self) -> None:
        # Map a minimal TEB and point GS at it so __chkstk's GS:[0x8]/GS:[0x10]
        # stack-bound probe reads valid values instead of faulting.
        self.uc.mem_map(TEB_BASE, TEB_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        # NT_TIB: StackBase at +0x08 (top of stack), StackLimit at +0x10
        # (lowest committed address). Bracket the whole emulated stack so the
        # probe loop (0x18001d020..) treats the frame as already committed.
        self.uc.mem_write(TEB_BASE + 0x08, struct.pack("<Q", STACK_BASE + STACK_SIZE))
        self.uc.mem_write(TEB_BASE + 0x10, struct.pack("<Q", STACK_BASE))
        # Self pointer (NT_TIB.Self at +0x18) points at the TEB itself.
        self.uc.mem_write(TEB_BASE + 0x18, struct.pack("<Q", TEB_BASE))
        self.uc.msr_write(IA32_GS_BASE_MSR, TEB_BASE)
        self._log(f"mapped TEB at 0x{TEB_BASE:x}, GS base set")

    def bump_alloc(self, size: int, align: int = 16) -> int:
        """Simple bump allocator inside the heap region. Never frees."""
        addr = align_up(self._heap_cursor, align)
        self._ensure_heap_mapped(addr + size)
        self._heap_cursor = addr + size
        return addr

    def host_alloc(self, size: int, align: int = 16) -> int:
        """Bump allocator for emulated host structures (separate region)."""
        addr = align_up(self._host_cursor, align)
        self._ensure_host_mapped(addr + size)
        self._host_cursor = addr + size
        return addr

    def _ensure_heap_mapped(self, end_addr: int) -> None:
        mapped_end = HEAP_BASE + self._heap_mapped_size
        if end_addr <= mapped_end:
            return
        grow = align_up(end_addr - mapped_end)
        self.uc.mem_map(mapped_end, grow, UC_PROT_READ | UC_PROT_WRITE)
        self._heap_mapped_size += grow

    def _ensure_host_mapped(self, end_addr: int) -> None:
        mapped_end = HOST_STRUCT_BASE + self._host_mapped_size
        if end_addr <= mapped_end:
            return
        grow = align_up(end_addr - mapped_end)
        self.uc.mem_map(mapped_end, grow, UC_PROT_READ | UC_PROT_WRITE)
        self._host_mapped_size += grow

    # -- generalized host callbacks -----------------------------------------
    def install_callback(self, label: str, handler: Callable[["AexLoader", List[int]], int]) -> int:
        """
        Install a Python-backed callable at a fresh guest address (a single
        RET instruction). When emulated code CALLs that address, the code
        hook invokes `handler(self, args)` (args = RCX/RDX/R8/R9), stores its
        integer return in RAX, and lets the RET return to the caller. The
        handler may also read/write XMM registers directly for float returns.
        Returns the guest address to store into a function-pointer table.
        """
        addr = self._callback_cursor
        self._callback_cursor += CALLBACK_STUB_STRIDE
        if self._callback_cursor > CALLBACK_STUB_BASE + CALLBACK_STUB_SIZE:
            raise MemoryError("aex_loader callback region exhausted")
        self.uc.mem_write(addr, b"\xc3")  # RET
        self.callbacks[addr] = (label, handler)
        return addr

    def detour_function(self, guest_addr: int, label: str,
                        handler: Callable[["AexLoader", List[int]], int]) -> int:
        """
        Patch an already-mapped guest function so execution jumps to a Python
        callback stub instead of the original body.

        This is intentionally minimal: it overwrites the first 12 bytes with
        `mov rax, imm64; jmp rax`. Use only on functions whose original body
        we are deliberately replacing for the duration of the run.
        """
        cb_addr = self.install_callback(label, handler)
        patch = b"\x48\xb8" + struct.pack("<Q", cb_addr) + b"\xff\xe0"
        self.uc.mem_write(guest_addr, patch)
        return cb_addr

    def add_code_hook(self, guest_addr: int,
                      handler: Callable[["AexLoader", int, int], None]) -> None:
        """
        Run `handler(loader, address, size)` whenever RIP reaches `guest_addr`.
        This uses a dedicated exact-address Unicorn code hook, so it remains
        efficient in fast mode.
        """
        def _wrapped(uc: Uc, address: int, size: int, user_data) -> None:
            handler(self, address, size)
        hook = self.uc.hook_add(UC_HOOK_CODE, _wrapped, begin=guest_addr, end=guest_addr)
        self._code_hooks.append(hook)

    # -- XMM helpers --------------------------------------------------------
    def read_xmm_f64(self, idx: int) -> float:
        raw = self.uc.reg_read(_XMM_REGS[idx])
        return struct.unpack("<d", raw.to_bytes(16, "little")[:8])[0]

    def read_xmm_f32(self, idx: int) -> float:
        raw = self.uc.reg_read(_XMM_REGS[idx])
        return struct.unpack("<f", raw.to_bytes(16, "little")[:4])[0]

    def write_xmm_f64(self, idx: int, value: float) -> None:
        packed = struct.pack("<d", value) + b"\x00" * 8
        self.uc.reg_write(_XMM_REGS[idx], int.from_bytes(packed, "little"))

    def write_xmm_f32(self, idx: int, value: float) -> None:
        packed = struct.pack("<f", value) + b"\x00" * 12
        self.uc.reg_write(_XMM_REGS[idx], int.from_bytes(packed, "little"))

    # -- read-access tracing ------------------------------------------------
    def add_read_trace_range(self, lo: int, hi: int, label: str) -> None:
        """Record reads landing in [lo, hi). Enables the MEM_READ hook lazily."""
        self.read_trace_ranges.append((lo, hi, label))
        if not self._read_hook_installed:
            self.uc.hook_add(UC_HOOK_MEM_READ, self._on_mem_read)
            self._read_hook_installed = True

    def _on_mem_read(self, uc: Uc, access, address, size, value, user_data) -> None:
        for lo, hi, label in self.read_trace_ranges:
            if lo <= address < hi:
                rip = uc.reg_read(UC_X86_REG_RIP)
                self.read_trace.append((label, address - lo, size, rip))
                break

    # -- libm / OpenMP import implementations -------------------------------
    def register_libm_impls(self, max_threads: int = 1) -> None:
        """
        Register real implementations for the math + OpenMP imports used by
        FUN_180004640 and its callees. Must be called explicitly (M1 default
        behavior of "unimplemented import -> RAX=0" is preserved otherwise).

        ABI notes (Windows x64):
          - cos/sin take a double in XMM0 and return a double in XMM0.
          - expf/log2f take a float in XMM0 and return a float in XMM0.
          - atan2f takes float y in XMM0, float x in XMM1, returns float XMM0.
          - omp_get_max_threads returns an int in EAX/RAX.
        """
        def _d1(fn):
            def impl(uc, args):
                self.write_xmm_f64(0, fn(self.read_xmm_f64(0)))
                return 0
            return impl

        def _f1(fn):
            def impl(uc, args):
                self.write_xmm_f32(0, fn(self.read_xmm_f32(0)))
                return 0
            return impl

        def _d2(fn):
            def impl(uc, args):
                self.write_xmm_f64(0, fn(self.read_xmm_f64(0), self.read_xmm_f64(1)))
                return 0
            return impl

        def _atan2f(uc, args):
            y = self.read_xmm_f32(0)
            x = self.read_xmm_f32(1)
            self.write_xmm_f32(0, math.atan2(y, x))
            return 0

        self.import_impls.update({
            "cos": _d1(math.cos),
            "sin": _d1(math.sin),
            "pow": _d2(math.pow),
            "expf": _f1(math.exp),
            "log2f": _f1(math.log2),
            "atan2f": _atan2f,
            "omp_get_max_threads": lambda uc, args: max_threads,
        })

    # -- imports -----------------------------------------------------------
    def _resolve_imports(self) -> None:
        if not hasattr(self.pe, "DIRECTORY_ENTRY_IMPORT"):
            return

        stub_addr = IMPORT_STUB_BASE
        total = sum(len(e.imports) for e in self.pe.DIRECTORY_ENTRY_IMPORT)
        stub_region_size = align_up(total * IMPORT_STUB_STRIDE)
        self.uc.mem_map(IMPORT_STUB_BASE, stub_region_size, UC_PROT_ALL)

        for entry in self.pe.DIRECTORY_ENTRY_IMPORT:
            dll = entry.dll.decode("ascii", "replace")
            for imp in entry.imports:
                name = (
                    imp.name.decode("ascii", "replace")
                    if imp.name
                    else f"ordinal_{imp.ordinal}"
                )
                iat_va = self.load_base + (imp.address - self.image_base)

                # Each import gets a unique tiny stub: RET. We point the
                # IAT slot at this stub; a code hook at that address detects
                # "we entered an import" and dispatches to the Python
                # implementation/log-and-stub-return logic, then executes the
                # RET to return to the caller (mimicking `call [iat_slot]`
                # jumping straight to a function that immediately returns,
                # after we've already fixed up registers/memory).
                self.uc.mem_write(stub_addr, b"\xc3")  # RET
                self.uc.mem_write(iat_va, struct.pack("<Q", stub_addr))

                self.import_slots[iat_va] = (dll, name)
                self.import_stubs[stub_addr] = (dll, name)
                stub_addr += IMPORT_STUB_STRIDE

        self._log(f"resolved {total} imports into stub table at 0x{IMPORT_STUB_BASE:x}")

    def register_import_impl(self, name: str, fn: Callable[[Uc, List[int]], int]) -> None:
        """Register/override a Python implementation for an imported symbol."""
        self.import_impls[name] = fn

    def _register_default_impls(self) -> None:
        def _read_cstring_or_bytes(uc: Uc, addr: int, n: int) -> bytes:
            return bytes(uc.mem_read(addr, n))

        def impl_memset(uc: Uc, args: List[int]) -> int:
            dst, val, n = args[0], args[1] & 0xFF, args[2]
            if n:
                uc.mem_write(dst, bytes([val]) * n)
            return dst

        def impl_memcpy(uc: Uc, args: List[int]) -> int:
            dst, src, n = args[0], args[1], args[2]
            if n:
                uc.mem_write(dst, bytes(uc.mem_read(src, n)))
            return dst

        def impl_memmove(uc: Uc, args: List[int]) -> int:
            # bytes() copy already snapshots src before writing dst, so this
            # is safe even for overlapping regions.
            return impl_memcpy(uc, args)

        def impl_malloc(uc: Uc, args: List[int]) -> int:
            size = args[0]
            if size <= 0:
                size = 1
            return self.bump_alloc(size)

        def impl_free(uc: Uc, args: List[int]) -> int:
            return 0  # bump allocator never frees; no-op is safe for M1

        self.import_impls.update(
            {
                "memset": impl_memset,
                "memcpy": impl_memcpy,
                "memmove": impl_memmove,
                "malloc": impl_malloc,
                "free": impl_free,
            }
        )

    # -- hooks ---------------------------------------------------------------
    def _on_code(self, uc: Uc, address: int, size: int, user_data) -> None:
        self.instructions_executed += 1

        if address in self.import_stubs:
            dll, name = self.import_stubs[address]
            args = self._read_int_args(uc, 4)
            ret = 0
            impl = self.import_impls.get(name)
            if impl is not None:
                try:
                    ret = impl(uc, args) or 0
                except Exception as exc:  # pragma: no cover - debug aid
                    self._log(f"import impl {name} raised {exc!r}; returning 0")
                    ret = 0
            else:
                self._log(f"import stub (unimplemented): {dll}!{name} args={args!r} -> RAX=0")
            uc.reg_write(UC_X86_REG_RAX, ret & 0xFFFFFFFFFFFFFFFF)
            self.import_log.append(ImportCallLog(name=name, dll=dll, args=args, ret=ret))
            return

        if address in self.callbacks:
            label, handler = self.callbacks[address]
            args = self._read_int_args(uc, 4)
            ret = handler(self, args)
            if ret is not None:
                uc.reg_write(UC_X86_REG_RAX, ret & 0xFFFFFFFFFFFFFFFF)
            self.callback_log.append((label, args, ret))
            return

        if address == RETURN_TRAMPOLINE:
            uc.emu_stop()

    def _on_bad_mem(self, uc: Uc, access, address, size, value, user_data) -> bool:
        rip = uc.reg_read(UC_X86_REG_RIP)
        self._log(
            f"UNMAPPED/INVALID mem access={access} addr=0x{address:x} "
            f"size={size} value=0x{value:x} at RIP=0x{rip:x}"
        )
        return False  # let Unicorn raise UcError

    def _read_int_args(self, uc: Uc, count: int) -> List[int]:
        regs = [UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9]
        return [uc.reg_read(r) for r in regs[:count]]

    # -- calling convention --------------------------------------------------
    def call_function(
        self,
        addr: int,
        int_args: Optional[List[int]] = None,
        float_args: Optional[Dict[int, float]] = None,
        max_instructions: int = 20_000_000,
    ) -> Dict[str, int]:
        """
        Call a function at `addr` using the Windows x64 calling convention.

        int_args: values for RCX, RDX, R8, R9, then pushed to the stack for
                  any beyond the 4th (shadow space + stack args), in order.
        float_args: {arg_index: float_value} for arguments that are actually
                  floats/doubles and must go in XMM0-XMM3 instead of the GP
                  registers at that position (per Windows x64 ABI, the slot
                  in the *other* register bank is left unused, not packed).
                  arg_index is 0-based position in the overall argument list.

        Returns a dict with RAX/RBX/... final register values and XMM0 (as
        raw bits) so callers can reinterpret as float/double as needed, plus
        'instructions' = instruction count executed during this call.
        """
        int_args = int_args or []
        float_args = float_args or {}

        sp = STACK_BASE + STACK_SIZE - 0x1000  # leave headroom below top
        sp &= ~0xF  # 16-byte align

        # Windows x64: caller must reserve 32 bytes shadow space, plus stack
        # args beyond the 4th, then the return address, and the whole frame
        # (after the call/push of return addr) must leave RSP % 16 == 8 at
        # function entry (i.e. RSP+8 aligned to 16 at the first instruction).
        stack_args = int_args[4:]
        n_stack_args = len(stack_args)
        shadow_and_args = 0x20 + n_stack_args * 8
        frame_size = align_up(shadow_and_args + 8, 16)  # +8 for return addr slot
        sp -= frame_size

        # write stack args (5th arg onward) just above shadow space
        for i, val in enumerate(stack_args):
            self.uc.mem_write(sp + 0x20 + i * 8, struct.pack("<Q", val & 0xFFFFFFFFFFFFFFFF))

        # push return address (our trampoline)
        sp -= 8
        self.uc.mem_write(sp, struct.pack("<Q", RETURN_TRAMPOLINE))

        self.uc.reg_write(UC_X86_REG_RSP, sp)

        gp_regs = [UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9]
        for i in range(min(4, len(int_args))):
            self.uc.reg_write(gp_regs[i], int_args[i] & 0xFFFFFFFFFFFFFFFF)

        # float_args values may be:
        #   - raw bytes (already packed, e.g. via f32_to_xmm_bytes) -- used as-is
        #   - a (float, 'f') or (float, 'd') tuple -- packed as single/double
        #   - a bare float -- packed as single-precision (float) by default,
        #     since all M1 target functions take `float`, not `double`.
        xmm_regs = [UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3]
        for idx, fval in float_args.items():
            if idx > 3:
                raise NotImplementedError("float args beyond position 3 need stack packing (not needed for M1 targets)")
            if isinstance(fval, bytes):
                packed = fval
            elif isinstance(fval, tuple):
                value, kind = fval
                packed = struct.pack("<f" if kind == "f" else "<d", value)
            else:
                packed = struct.pack("<f", fval)
            packed = packed + b"\x00" * (16 - len(packed))
            self.uc.reg_write(xmm_regs[idx], int.from_bytes(packed, "little"))

        self.uc.reg_write(UC_X86_REG_RIP, addr)

        self.import_log.clear()
        start_instr = self.instructions_executed
        try:
            self.uc.emu_start(addr, RETURN_TRAMPOLINE, count=max_instructions)
        except UcError as exc:
            rip = self.uc.reg_read(UC_X86_REG_RIP)
            raise RuntimeError(f"emulation faulted at RIP=0x{rip:x}: {exc}") from exc

        xmm0_raw = self.uc.reg_read(UC_X86_REG_XMM0)
        xmm0_bytes = xmm0_raw.to_bytes(16, "little") if isinstance(xmm0_raw, int) else bytes(xmm0_raw)
        result = {
            "rax": self.uc.reg_read(UC_X86_REG_RAX),
            "rbx": self.uc.reg_read(UC_X86_REG_RBX),
            "xmm0": xmm0_bytes,
            "xmm0_f32": struct.unpack("<f", xmm0_bytes[:4])[0],
            "xmm0_f64": struct.unpack("<d", xmm0_bytes[:8])[0],
            "instructions": self.instructions_executed - start_instr,
        }
        return result

    # -- convenience for float args as raw 32-bit packing -------------------
    @staticmethod
    def f32_to_xmm_bytes(value: float) -> bytes:
        return struct.pack("<f", value) + b"\x00" * 12

    @staticmethod
    def f64_to_xmm_bytes(value: float) -> bytes:
        return struct.pack("<d", value) + b"\x00" * 8

    def write_bytes(self, addr: int, data: bytes) -> None:
        self.uc.mem_write(addr, data)

    def read_bytes(self, addr: int, size: int) -> bytes:
        return bytes(self.uc.mem_read(addr, size))

    def read_f32_array(self, addr: int, count: int) -> List[float]:
        raw = self.read_bytes(addr, count * 4)
        return list(struct.unpack(f"<{count}f", raw))

    def write_f32_array(self, addr: int, values: List[float]) -> None:
        self.write_bytes(addr, struct.pack(f"<{len(values)}f", *values))
