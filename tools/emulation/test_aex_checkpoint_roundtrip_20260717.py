"""AexLoader state-checkpoint roundtrip and fail-closed contract tests."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_EFLAGS,
    UC_X86_REG_MXCSR,
    UC_X86_REG_R12,
    UC_X86_REG_RAX,
    UC_X86_REG_RDI,
    UC_X86_REG_RDX,
    UC_X86_REG_RIP,
    UC_X86_REG_RSI,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM0,
    UC_X86_REG_XMM1,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import (  # noqa: E402
    AexLoader,
    CHECKPOINT_MAGIC,
    HOST_STRUCT_BASE,
    RETURN_TRAMPOLINE,
    STACK_BASE,
    STACK_SIZE,
    TEB_BASE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"
CODE_ADDR = RETURN_TRAMPOLINE + 0x100
CHECKPOINT_OFFSET = 10
CODE = bytes.fromhex(
    "49ffc4"       # inc r12
    "4883c007"     # add rax, 7 (sets carry for the selected initial RAX)
    "0f58c1"       # addps xmm0, xmm1
    "4883d000"     # adc rax, 0 (consumes restored carry)
    "483307"       # xor rax, [rdi]
    "480306"       # add rax, [rsi]
    "488902"       # mov [rdx], rax
    "0f58c1"       # addps xmm0, xmm1
    "c3"           # ret to AexLoader's return trampoline
)


def _new_loader(test_case: unittest.TestCase) -> AexLoader:
    if not DEFAULT_AEX.exists():
        test_case.skipTest(f"fixture AEX is unavailable: {DEFAULT_AEX}")
    loader = AexLoader(str(DEFAULT_AEX), verbose=False, fast=True)
    loader.write_bytes(CODE_ADDR, CODE)
    return loader


def _writable_pe_address(loader: AexLoader) -> int:
    ranges = loader._writable_image_ranges()
    assert ranges
    return ranges[0][0] + 0x80


def _seed(loader: AexLoader) -> dict[str, int]:
    heap = loader.bump_alloc(0x321, align=64)
    host = loader.host_alloc(0x287, align=32)
    pe_data = _writable_pe_address(loader)
    rsp = STACK_BASE + STACK_SIZE - 0x208
    loader.write_bytes(heap, struct.pack("<Q", 0x1122334455667788) + b"heap-state")
    loader.write_bytes(host, struct.pack("<Q", 0x0102030405060708) + b"host-state")
    loader.write_bytes(pe_data, b"PE-MUTABLE-STATE" + b"\x00" * 16)
    loader.write_bytes(TEB_BASE + 0x100, b"TEB-MUTABLE-STATE")
    loader.write_bytes(rsp, struct.pack("<Q", RETURN_TRAMPOLINE) + b"stack-state")

    loader.uc.reg_write(UC_X86_REG_RAX, 0xFFFFFFFFFFFFFFFC)
    loader.uc.reg_write(UC_X86_REG_R12, 0x123456789ABCDEF0)
    loader.uc.reg_write(UC_X86_REG_RDI, heap)
    loader.uc.reg_write(UC_X86_REG_RSI, host)
    loader.uc.reg_write(UC_X86_REG_RDX, pe_data)
    loader.uc.reg_write(UC_X86_REG_RSP, rsp)
    loader.uc.reg_write(UC_X86_REG_EFLAGS, 0x202)
    loader.uc.reg_write(UC_X86_REG_MXCSR, 0x1F80)
    loader.uc.reg_write(
        UC_X86_REG_XMM0,
        int.from_bytes(struct.pack("<4f", 1.0, 2.0, 3.0, 4.0), "little"),
    )
    loader.uc.reg_write(
        UC_X86_REG_XMM1,
        int.from_bytes(struct.pack("<4f", 0.25, 0.5, 0.75, 1.0), "little"),
    )
    loader.uc.reg_write(UC_X86_REG_RIP, CODE_ADDR)
    return {"heap": heap, "host": host, "pe_data": pe_data, "rsp": rsp}


def _finish(loader: AexLoader, pointers: dict[str, int]) -> dict:
    loader.resume_execution(max_instructions=100)
    return {
        "registers": loader._checkpoint_registers(),
        "pe": loader.read_bytes(pointers["pe_data"], 32),
        "heap": loader.read_bytes(pointers["heap"], 32),
        "host": loader.read_bytes(pointers["host"], 32),
        "stack": loader.read_bytes(pointers["rsp"], 32),
        "teb": loader.read_bytes(TEB_BASE + 0x100, 32),
        "heap_cursor": loader._heap_cursor,
        "host_cursor": loader._host_cursor,
    }


class CheckpointRoundtripTest(unittest.TestCase):
    def test_checkpoint_roundtrip_matches_uninterrupted_execution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aex-checkpoint-test-", dir="/tmp") as temp_dir:
            checkpoint_path = Path(temp_dir) / "roundtrip.aexcp"
            uninterrupted = _new_loader(self)
            uninterrupted_pointers = _seed(uninterrupted)
            uninterrupted_result = _finish(uninterrupted, uninterrupted_pointers)

            checkpointed = _new_loader(self)
            checkpointed_pointers = _seed(checkpointed)
            saved = {}

            def save_at_boundary(uc, address, size, user_data) -> None:
                saved["registers"] = checkpointed._checkpoint_registers()
                saved["header"] = checkpointed.save_checkpoint(
                    checkpoint_path, metadata={"test": "synthetic-roundtrip"},
                )
                uc.emu_stop()

            checkpointed.uc.hook_add(
                UC_HOOK_CODE, save_at_boundary,
                begin=CODE_ADDR + CHECKPOINT_OFFSET, end=CODE_ADDR + CHECKPOINT_OFFSET,
            )
            checkpointed.resume_execution(max_instructions=100)
            self.assertTrue(checkpoint_path.read_bytes().startswith(CHECKPOINT_MAGIC))

            resumed = _new_loader(self)
            resumed_header = resumed.load_checkpoint(checkpoint_path)
            self.assertEqual(resumed_header, saved["header"])
            self.assertEqual(resumed_header["metadata"], {"test": "synthetic-roundtrip"})
            self.assertEqual(resumed._checkpoint_registers(), saved["registers"])
            self.assertEqual(resumed._heap_cursor, checkpointed._heap_cursor)
            self.assertEqual(resumed._host_cursor, checkpointed._host_cursor)
            self.assertEqual(
                resumed.read_bytes(checkpointed_pointers["heap"], 32),
                checkpointed.read_bytes(checkpointed_pointers["heap"], 32),
            )
            self.assertEqual(
                resumed.read_bytes(checkpointed_pointers["host"], 32),
                checkpointed.read_bytes(checkpointed_pointers["host"], 32),
            )
            self.assertEqual(
                resumed.read_bytes(TEB_BASE + 0x100, 32),
                checkpointed.read_bytes(TEB_BASE + 0x100, 32),
            )
            resumed_result = _finish(resumed, checkpointed_pointers)
            self.assertEqual(resumed_result, uninterrupted_result)

    def test_public_pe_code_patch_is_restored(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aex-checkpoint-test-", dir="/tmp") as temp_dir:
            checkpoint_path = Path(temp_dir) / "pe-code-patch.aexcp"
            source = _new_loader(self)
            patch_addr = source.load_base + int(source.pe.OPTIONAL_HEADER.AddressOfEntryPoint)
            original = source.read_bytes(patch_addr, 16)
            patch = bytes(byte ^ 0x5A for byte in original)
            source.write_bytes(patch_addr, patch)
            source.save_checkpoint(checkpoint_path)

            resumed = _new_loader(self)
            resumed.write_bytes(patch_addr, patch)
            resumed.uc.mem_write(patch_addr, original)
            self.assertEqual(resumed.read_bytes(patch_addr, 16), original)
            resumed.load_checkpoint(checkpoint_path)
            self.assertEqual(resumed.read_bytes(patch_addr, 16), patch)

    def test_case0009_runner_saves_and_resumes_in_fresh_process(self) -> None:
        if not DEFAULT_AEX.exists():
            self.skipTest(f"fixture AEX is unavailable: {DEFAULT_AEX}")
        runner = REPO_ROOT / "tools" / "emulation" / "test_zoom_case0009.py"
        with tempfile.TemporaryDirectory(prefix="aex-checkpoint-case0009-", dir="/tmp") as temp_dir:
            root = Path(temp_dir)
            checkpoint = root / "case0009.aexcp"
            common = [
                sys.executable, str(runner), "--direct-zoom-core",
                "--direct-debug-size", "8x8", "--direct-debug-quality-step", "1",
                "--max-instructions", "500000",
            ]
            saved = subprocess.run(
                common + [
                    "--save-checkpoint-at-rip", str(checkpoint), "0x1800056f0",
                    "--output-json", str(root / "save.json"),
                    "--output-md", str(root / "save.md"),
                ],
                cwd=REPO_ROOT, check=True, capture_output=True, text=True,
            )
            self.assertIn("checkpoint_saved=", saved.stdout)
            self.assertTrue(checkpoint.is_file())
            resumed = subprocess.run(
                common + [
                    "--resume-checkpoint", str(checkpoint),
                    "--output-json", str(root / "resume.json"),
                    "--output-md", str(root / "resume.md"),
                ],
                cwd=REPO_ROOT, check=True, capture_output=True, text=True,
            )
            self.assertIn("classification=direct-debug-core-hooks-reached-nonsemantic", resumed.stdout)

    def test_checkpoint_corruption_and_aex_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aex-checkpoint-test-", dir="/tmp") as temp_dir:
            temp_path = Path(temp_dir)
            source = _new_loader(self)
            _seed(source)
            checkpoint_path = temp_path / "valid.aexcp"
            source.save_checkpoint(checkpoint_path)

            corrupt_path = temp_path / "corrupt.aexcp"
            corrupt = bytearray(checkpoint_path.read_bytes())
            corrupt[-1] ^= 0x80
            corrupt_path.write_bytes(corrupt)
            target = _new_loader(self)
            before = target._checkpoint_registers()
            with self.assertRaisesRegex(ValueError, "corrupt|checksum"):
                target.load_checkpoint(corrupt_path)
            self.assertEqual(target._checkpoint_registers(), before)

            changed_aex = temp_path / "changed.aex"
            shutil.copyfile(DEFAULT_AEX, changed_aex)
            with changed_aex.open("ab") as handle:
                handle.write(b"checkpoint-mismatch")
            mismatched = AexLoader(str(changed_aex), verbose=False, fast=True)
            with self.assertRaisesRegex(ValueError, "AEX identity"):
                mismatched.load_checkpoint(checkpoint_path)


if __name__ == "__main__":
    unittest.main()
